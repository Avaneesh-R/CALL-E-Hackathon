"""
Follow-up call scheduler.
After R1 inference extracts a callback time, this module:
  1. Parses the natural-language time using Groq
  2. Saves a scheduled_calls record to SQLite
  3. Runs a background thread that fires R2 calls when due
"""
from __future__ import annotations
import json, os, re, threading, time as _time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from models import get_conn, _mask_phone

_lock = threading.Lock()
_scheduler_started = False


# ── Time parser (Groq-powered) ────────────────────────────────────────────────

def parse_callback_time(timeline_text: str, tz_name: str = "UTC") -> datetime | None:
    """
    Convert natural-language timeline (e.g. "5:05 PM tomorrow") into a UTC datetime.
    Uses Groq for reliability; falls back to simple regex.
    """
    if not timeline_text or timeline_text.lower() in ("null", "none", ""):
        return None

    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

    now_local = datetime.now(tz)
    now_iso   = now_local.isoformat()

    # Try Groq first
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            prompt = (
                f'Current local datetime ({tz_name}): {now_iso}\n'
                f'Vendor said: "{timeline_text}"\n\n'
                'Return ONLY a JSON object with one key: '
                '{"scheduled_at": "YYYY-MM-DDTHH:MM:SS"} in the vendor\'s local timezone. '
                'If the time cannot be determined, return {"scheduled_at": null}. '
                'No other text.'
            )
            client = Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=60, temperature=0,
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            parsed = json.loads(raw)
            dt_str = parsed.get("scheduled_at")
            if dt_str:
                dt_parsed = datetime.fromisoformat(dt_str)
                # Only attach tz if naive; if Groq returned an offset-aware string, convert directly
                if dt_parsed.tzinfo is None:
                    dt_parsed = dt_parsed.replace(tzinfo=tz)
                return dt_parsed.astimezone(timezone.utc)
        except Exception:
            pass

    # Regex fallback
    text = timeline_text.lower()
    time_m = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text)
    hour = minute = None
    if time_m:
        hour, minute = int(time_m.group(1)), int(time_m.group(2))
        if time_m.group(3) == "pm" and hour != 12:
            hour += 12
        elif time_m.group(3) == "am" and hour == 12:
            hour = 0
    else:
        hm = re.search(r'(\d{1,2})\s*(am|pm)', text)
        if hm:
            hour, minute = int(hm.group(1)), 0
            if hm.group(2) == "pm" and hour != 12:
                hour += 12

    if hour is None:
        return None

    offset = 1 if "tomorrow" in text else 0
    base = (now_local + timedelta(days=offset)).date()
    day_map = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,
               "friday":4,"saturday":5,"sunday":6}
    for name, wd in day_map.items():
        if name in text:
            days_ahead = (wd - now_local.weekday()) % 7 or 7
            base = (now_local + timedelta(days=days_ahead)).date()
            break

    try:
        dt_local = datetime(base.year, base.month, base.day, hour, minute, tzinfo=tz)
        return dt_local.astimezone(timezone.utc)
    except Exception:
        return None


# ── DB helpers ────────────────────────────────────────────────────────────────

def schedule_followup(lead_id: int, campaign_id: int, timeline_text: str,
                      product: str, lat: float = None, lon: float = None,
                      tz_hint: str = None, region: str = None,
                      language: str = None) -> bool:
    """
    Parse timeline_text, save a scheduled_calls row, return True if scheduled.
    tz_hint: pre-resolved timezone name (skips GPS lookup when already known).
    """
    from business_hours import get_timezone
    tz_name = tz_hint or (get_timezone(lat, lon) if lat and lon else None) or "UTC"
    scheduled_utc = parse_callback_time(timeline_text, tz_name)

    if not scheduled_utc:
        return False

    from script_gen import generate_goal
    r2_goal = generate_goal(product, round_num=2)

    with get_conn() as conn:
        # Prevent duplicate pending rows for the same lead
        existing = conn.execute(
            "SELECT id FROM scheduled_calls WHERE lead_id=? AND status IN ('pending','in_progress')",
            (lead_id,)
        ).fetchone()
        if existing:
            print(f"  [Scheduler] Skipping duplicate — lead {lead_id} already has a pending scheduled call.")
            return True  # Already scheduled, not an error

        conn.execute(
            """INSERT INTO scheduled_calls
               (lead_id, campaign_id, scheduled_at, timezone, status, round,
                goal_script, region, language)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (lead_id, campaign_id, scheduled_utc.isoformat(),
             tz_name, "pending", 2, r2_goal, region, language)
        )
        conn.commit()

    local_display = scheduled_utc.astimezone(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M %Z")
    print(f"  [Scheduler] R2 call scheduled for {local_display} (lead_id={lead_id})")
    return True


def get_pending_scheduled() -> list:
    with get_conn() as conn:
        return conn.execute(
            """SELECT sc.*, l.phone, l.lat, l.lon, l.masked_phone,
                      c.product_description, c.location
               FROM scheduled_calls sc
               JOIN leads l ON l.id = sc.lead_id
               JOIN campaigns c ON c.id = sc.campaign_id
               WHERE sc.status = 'pending'
               ORDER BY sc.scheduled_at"""
        ).fetchall()


# ── Call firing ───────────────────────────────────────────────────────────────

def _fire(row) -> None:
    lead_id     = row["lead_id"]
    sched_id    = row["id"]
    phone       = row["phone"]
    goal        = row["goal_script"]
    product     = row["product_description"]
    campaign_id = row["campaign_id"]
    tz_name     = row["timezone"] or "UTC"
    region      = row["region"]
    language    = row["language"]
    masked      = row["masked_phone"] or _mask_phone(phone)

    print(f"\n[Scheduler] Firing scheduled call -> {masked}  (scheduled_calls.id={sched_id})")

    from caller import (execute_call_pipeline, extract_round2_fields,
                        parse_transcript_to_json, infer_from_transcript)

    try:
        # Pass lat=None, lon=None — vendor explicitly requested this callback time,
        # so we always honour it regardless of business hours.
        status_output = execute_call_pipeline(
            phone=phone, goal=goal, dry_run=False,
            lat=None, lon=None, region=region, language=language
        )
        if status_output.get("status") == "SKIPPED":
            _update_status(sched_id, "skipped")
            return

        call_id   = status_output.get("run_id") or status_output.get("id") or "unknown"
        extracted = extract_round2_fields(status_output)
        lines     = parse_transcript_to_json(status_output)
        inference = {}
        if lines:
            try:
                inference = infer_from_transcript(lines, product, round_num=2)
            except Exception:
                pass

        combined = {**extracted, **inference}

        with get_conn() as conn:
            conn.execute(
                "UPDATE leads SET status='completed', round2_call_id=? WHERE id=?",
                (call_id, lead_id)
            )
            conn.execute(
                """INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields)
                   VALUES (?,?,?,?,?)""",
                (lead_id, call_id, 2,
                 json.dumps(status_output),
                 json.dumps(combined) if combined else None)
            )
            conn.commit()

        _update_status(sched_id, "fired")
        print(f"  [Scheduler] Call completed for lead {lead_id}. Status: {status_output.get('status')}")

        # If CALLE returned report_blocked OR inference found a new callback time, schedule next round
        new_timeline = ""
        if status_output.get("callback_requested"):
            # Extract from transcript directly — vendor said a time during the call
            if lines:
                raw_text = " ".join(l.get("text", "") for l in lines)
                m = re.search(r'(\d+)\s*minute', raw_text, re.IGNORECASE)
                if m:
                    new_timeline = f"in {m.group(1)} minutes"
        if not new_timeline and lines and inference:
            new_timeline = inference.get("timeline") or inference.get("next_steps") or ""

        if new_timeline and new_timeline not in ("null", "None", "", "-", "—"):
            print(f"  [Scheduler] Detected callback request: '{new_timeline[:80]}'")
            # Pass tz_name so relative times ("in 10 minutes") resolve in vendor's timezone
            scheduled = schedule_followup(
                lead_id=lead_id,
                campaign_id=campaign_id,
                timeline_text=new_timeline,
                product=product,
                lat=None, lon=None,
                tz_hint=tz_name,
                region=region,
                language=language,
            )
            if not scheduled:
                print(f"  [Scheduler] Could not parse time from: '{new_timeline[:60]}'")

    except Exception as e:
        print(f"  [Scheduler] Call failed for lead {lead_id}: {e}")
        _update_status(sched_id, "failed")


def _update_status(sched_id: int, status: str):
    with get_conn() as conn:
        conn.execute("UPDATE scheduled_calls SET status=? WHERE id=?", (status, sched_id))
        conn.commit()


# ── Background polling thread ─────────────────────────────────────────────────

def _poll_loop():
    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            rows = get_pending_scheduled()
            for row in rows:
                due = datetime.fromisoformat(row["scheduled_at"])
                if due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                if now_utc >= due:
                    # Claim the row atomically before spawning thread — prevents double-fire
                    with get_conn() as conn:
                        updated = conn.execute(
                            "UPDATE scheduled_calls SET status='in_progress' WHERE id=? AND status='pending'",
                            (row["id"],)
                        ).rowcount
                        conn.commit()
                    if updated:
                        threading.Thread(target=_fire, args=(row,), daemon=True).start()
        except Exception as e:
            print(f"[Scheduler] Poll error: {e}")
        _time.sleep(10)


def start_scheduler_thread():
    global _scheduler_started
    with _lock:
        if _scheduler_started:
            return
        t = threading.Thread(target=_poll_loop, daemon=True)
        t.start()
        _scheduler_started = True
        print("[Scheduler] Background thread started — polling every 10s")
