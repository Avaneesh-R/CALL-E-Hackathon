"""
Campaign summary report generation and email delivery.
Requires env vars:
  SEND_REPORT_EMAIL=1
  REPORT_EMAIL_FROM=you@gmail.com
  REPORT_EMAIL_PASS=your_app_password
  REPORT_EMAIL_TO=client@example.com
"""
import json, os, smtplib
from email.message import EmailMessage
from pathlib import Path
from models import get_conn


def _gather_rows(campaign_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            """SELECT l.name, l.masked_phone, l.category, l.status,
                      c.product_description, c.location,
                      r1.extracted_fields AS r1_fields,
                      r2.extracted_fields AS r2_fields
               FROM leads l
               JOIN campaigns c ON c.id = l.campaign_id
               LEFT JOIN (
                   SELECT lead_id, extracted_fields FROM call_logs
                   WHERE id IN (SELECT MAX(id) FROM call_logs WHERE round=1 GROUP BY lead_id)
               ) r1 ON r1.lead_id = l.id
               LEFT JOIN (
                   SELECT lead_id, extracted_fields FROM call_logs
                   WHERE id IN (SELECT MAX(id) FROM call_logs WHERE round=2 GROUP BY lead_id)
               ) r2 ON r2.lead_id = l.id
               WHERE l.campaign_id = ?
               ORDER BY l.id""",
            (campaign_id,)
        ).fetchall()


def generate_summary_bullets(campaign_id: int) -> list[str]:
    rows = _gather_rows(campaign_id)
    if not rows:
        return ["No leads found for this campaign."]

    product = rows[0]["product_description"]
    location = rows[0]["location"]
    statuses = [r["status"] for r in rows]
    positives = statuses.count("positive") + statuses.count("completed")
    total = len(rows)

    prices = []
    for r in rows:
        ef = json.loads(r["r2_fields"]) if r["r2_fields"] else {}
        pr = ef.get("price_range") or ef.get("price_numeric")
        if pr:
            prices.append(str(pr))

    summaries = []
    for r in rows:
        ef = json.loads(r["r1_fields"]) if r["r1_fields"] else {}
        s = ef.get("summary")
        if s:
            summaries.append(s[:120])

    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        try:
            from groq import Groq
            import concurrent.futures as _cf
            client = Groq(api_key=api_key)
            table_text = "\n".join(
                f"- {r['name'] or r['masked_phone']} ({r['category']}): status={r['status']}"
                + (f", prices: {json.loads(r['r2_fields']).get('price_range','?')}" if r['r2_fields'] else "")
                for r in rows
            )
            prompt = (
                f"Product sourced: {product}\nLocation: {location}\n"
                f"Total vendors contacted: {total}, Positive responses: {positives}\n\n"
                f"Vendor details:\n{table_text}\n\n"
                f"Write exactly 5 concise procurement summary bullet points for a business client. "
                f"Cover: overall response rate, best pricing found, recommended next steps, "
                f"any vendors to follow up with, and risks or gaps. Return as a JSON array of 5 strings."
            )
            def _call():
                return client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=400, temperature=0.3,
                )
            with _cf.ThreadPoolExecutor(max_workers=1) as ex:
                resp = ex.submit(_call).result(timeout=20)
            raw = resp.choices[0].message.content.strip().strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
            bullets = json.loads(raw)
            if isinstance(bullets, list) and bullets:
                return [str(b) for b in bullets[:5]]
        except Exception:
            pass

    # Deterministic fallback
    return [
        f"Sourcing campaign for '{product}' in {location} completed.",
        f"{positives} of {total} vendors responded positively.",
        f"Price data collected: {', '.join(prices) if prices else 'None yet'}.",
        f"Vendor summaries: {'; '.join(summaries[:2]) if summaries else 'No AI inference available'}.",
        "Recommended next step: follow up with positive responders for R2 data capture.",
    ]


def send_report_email(campaign_id: int, excel_path: str = None) -> bool:
    if os.environ.get("SEND_REPORT_EMAIL", "").lower() not in ("1", "true", "yes"):
        return False
    from_addr = os.environ.get("REPORT_EMAIL_FROM")
    password   = os.environ.get("REPORT_EMAIL_PASS")
    to_addr    = os.environ.get("REPORT_EMAIL_TO")
    if not all([from_addr, password, to_addr]):
        print("[Report] Email env vars not configured (REPORT_EMAIL_FROM/PASS/TO). Skipping.")
        return False

    rows = _gather_rows(campaign_id)
    product = rows[0]["product_description"] if rows else "Unknown product"

    bullets = generate_summary_bullets(campaign_id)
    body = f"Campaign Summary — {product}\n\n" + "\n".join(f"• {b}" for b in bullets)
    body += "\n\nData © OpenStreetMap contributors (ODbL)"

    msg = EmailMessage()
    msg["Subject"] = f"Vendor Discovery Report: {product}"
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.set_content(body)

    if excel_path and Path(excel_path).exists():
        with open(excel_path, "rb") as f:
            msg.add_attachment(f.read(), maintype="application",
                               subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               filename=Path(excel_path).name)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(from_addr, password)
            smtp.send_message(msg)
        print(f"[Report] Email sent to {to_addr}")
        return True
    except Exception as e:
        print(f"[Report] Email failed: {e}")
        return False
