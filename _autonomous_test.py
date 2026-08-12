"""
Autonomous pipeline test — no human input needed.
Discovers vendors, calls up to 6, runs Groq inference, logs to DB.
Sunday-safe: passes lat=None to bypass Mon-Fri business hours gate.
"""
import os, sys, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')

# Load keys from registry if not already in env
if not os.environ.get('GROQ_API_KEY'):
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        os.environ['GROQ_API_KEY'] = winreg.QueryValueEx(key, "GROQ_API_KEY")[0]
    except Exception:
        pass

from datetime import datetime, timezone
from models import init_db, get_conn, Campaign, Lead, _mask_phone
from discovery import discover_vendors
from scoring import score_lead
from caller import execute_call_pipeline, classify_round1, parse_transcript_to_json, infer_from_transcript
from script_gen import generate_goal

PRODUCT  = "wholesale food and grocery supplies"
LOCATION = "New Delhi, India"
LIMIT    = 10  # fetch more to survive number filtering
REGION   = "IN"
LANGUAGE = "English"

print(f"\n{'='*62}")
print(f"AUTONOMOUS PIPELINE TEST — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"Product : {PRODUCT}")
print(f"Location: {LOCATION}")
print(f"{'='*62}\n")

# ── Step 1: Generate goal via Groq ──────────────────────────────
print("[1/5] Generating call script via Groq...")
try:
    goal = generate_goal(PRODUCT, round_num=1)
    print(f"  Script preview: {goal[:120]}...")
    GROQ_SCRIPT_OK = True
except Exception as e:
    print(f"  Groq script gen failed: {e} — using fallback")
    goal = (
        f"You are a procurement agent sourcing {PRODUCT}. "
        "Introduce yourself briefly. Ask if they supply these in bulk. "
        "If yes, ask about price range and minimum order. "
        "Keep the call under 90 seconds. Be polite and professional."
    )
    GROQ_SCRIPT_OK = False

# ── Step 2: Discover vendors ────────────────────────────────────
print(f"\n[2/5] Discovering vendors via OpenStreetMap...")
vendors = discover_vendors(PRODUCT, LOCATION, LIMIT)
if not vendors:
    print("  No vendors found. Exiting.")
    sys.exit(1)

print(f"  Found {len(vendors)} vendor(s). Scoring...")
for v in vendors:
    score, reasons = score_lead(v)
    v['_score'] = score
    v['_reasons'] = reasons

vendors.sort(key=lambda v: v.get('_score', 0), reverse=True)

# Filter: only valid Indian numbers (+91 10-digit) or known valid formats
def clean_phone(p):
    """Take first valid +91 number if multiple are concatenated."""
    import re
    # Split on known separators or +91 boundaries
    parts = re.split(r'(?=\+91)', p)
    parts = [x.strip() for x in parts if x.strip()]
    if not parts:
        parts = [p]
    return parts[0]  # take first number

def valid_phone(p):
    digits = ''.join(c for c in p if c.isdigit())
    if p.startswith('+91') and 11 <= len(digits) <= 12:
        return True
    if p.startswith('+') and not p.startswith('+91'):
        return False
    if len(digits) == 10:
        return True
    return False

# Clean concatenated numbers first
for v in vendors:
    v['phone'] = clean_phone(v['phone'])

before = len(vendors)
vendors = [v for v in vendors if valid_phone(v['phone'])]
vendors = vendors[:6]  # cap at 6 after filtering
print(f"  After phone validation: {len(vendors)}/{before} usable (capped at 6)")

for i, v in enumerate(vendors, 1):
    print(f"  {i}. [{v['_score']:3.0f}] {v.get('name','?')[:38]:<38} {_mask_phone(v['phone'])}")

# ── Step 3: Create campaign ─────────────────────────────────────
print(f"\n[3/5] Creating campaign in database...")
init_db()
with get_conn() as conn:
    campaign = Campaign(
        product_description=PRODUCT,
        location=LOCATION,
        goal_script=goal,
        consent_basis="autonomous-test-run",
        consent_approved_at=datetime.now(timezone.utc).isoformat(),
    )
    campaign.save(conn)
    campaign_id = campaign.id
    conn.commit()

    leads = []
    for v in vendors:
        lead = Lead(
            phone=v['phone'], campaign_id=campaign_id,
            name=v.get('name'), category=v.get('category'),
            lat=v.get('lat'), lon=v.get('lon'),
            osm_id=v.get('osm_id'),
            candidate_id=f"osm:{v['osm_id']}" if v.get('osm_id') else None,
            address=v.get('address'),
            lead_score=v.get('_score'),
        )
        lead.save(conn)
        leads.append(lead)
    conn.commit()

print(f"  Campaign #{campaign_id} created with {len(leads)} leads.")

# ── Step 4: Make calls ──────────────────────────────────────────
print(f"\n[4/5] Making calls (Sunday mode — hours gate bypassed)...")
print(f"-"*62)

outcomes = {'positive':0, 'negative':0, 'no_answer':0, 'unknown':0, 'failed':0, 'busy':0}

for lead in leads:
    label = (lead.name or _mask_phone(lead.phone))[:38]
    print(f"\n  Calling: {label}")
    try:
        status_output = execute_call_pipeline(
            phone=lead.phone,
            goal=goal,
            region=REGION,
            language=LANGUAGE,
            lat=None,   # bypass business hours gate
            lon=None,
        )

        call_status = status_output.get('status', '?')

        if call_status == 'SKIPPED':
            reason = status_output.get('skip_reason', '')
            print(f"    SKIPPED: {reason}")
            with get_conn() as conn:
                conn.execute("UPDATE leads SET status='skipped' WHERE id=?", (lead.id,))
                conn.commit()
            continue

        call_id = status_output.get('run_id') or 'unknown'
        outcome  = classify_round1(status_output)
        lines    = parse_transcript_to_json(status_output)
        inference = {}

        if lines:
            try:
                inference = infer_from_transcript(lines, PRODUCT, round_num=1)
                GROQ_INFERENCE_OK = True
            except Exception as e:
                print(f"    Inference error: {e}")
                GROQ_INFERENCE_OK = False
        else:
            GROQ_INFERENCE_OK = None

        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        print(f"    Status  : {call_status}")
        print(f"    Outcome : {outcome}")
        if inference:
            print(f"    Interest: {inference.get('interest_level','?')}")
            print(f"    Sentiment:{inference.get('sentiment','?')}")
            print(f"    Summary : {str(inference.get('summary',''))[:90]}")

        with get_conn() as conn:
            conn.execute("UPDATE leads SET status=?, round1_call_id=?, lead_score=? WHERE id=?",
                         (outcome, call_id, lead.lead_score, lead.id))
            conn.execute(
                "INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields) VALUES (?,?,?,?,?)",
                (lead.id, call_id, 1,
                 json.dumps(status_output),
                 json.dumps({'transcript': lines, **inference}))
            )
            conn.commit()

    except Exception as e:
        print(f"    ERROR: {e}")
        outcomes['failed'] += 1
        with get_conn() as conn:
            conn.execute("UPDATE leads SET status='failed' WHERE id=?", (lead.id,))
            conn.commit()

# ── Step 5: Summary ─────────────────────────────────────────────
print(f"\n{'='*62}")
print(f"[5/5] DONE — Campaign #{campaign_id}")
print(f"  Groq script gen : {'OK' if GROQ_SCRIPT_OK else 'FALLBACK'}")
print(f"  Outcomes: {outcomes}")
print(f"  Dashboard: http://127.0.0.1:5000")
print(f"{'='*62}\n")
