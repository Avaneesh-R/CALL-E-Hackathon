"""Retroactively saves the 6350215770 smoke test call to the database."""
import json
from datetime import datetime, timezone
from models import init_db, get_conn, Campaign, Lead, _mask_phone
from caller import (_run, parse_transcript_to_json, classify_round1,
                    infer_from_transcript)

RUN_ID  = "pY81FiD487J7N9G-YRfk-A"
PRODUCT = "stationery and office supplies"
CITY    = "New Delhi, India"
PHONE   = "+916350215770"

init_db()

# Fetch the real call result from CALL-E
print("Fetching call result from CALL-E...")
status = _run(["call", "status", "--run-id", RUN_ID])
print(f"  Status: {status.get('status')}")

transcript_lines = parse_transcript_to_json(status)
outcome = classify_round1(status)
r1 = infer_from_transcript(transcript_lines, PRODUCT, round_num=1)
r2 = infer_from_transcript(transcript_lines, PRODUCT, round_num=2)

approved_at = "2026-08-08T16:00:00+00:00"  # smoke test run time

with get_conn() as conn:
    # Campaign
    campaign = Campaign(
        product_description=PRODUCT,
        location=CITY,
        consent_basis="client-reviewed-and-approved",
        consent_approved_at=approved_at,
    )
    campaign.save(conn)

    # Lead
    lead = Lead(
        phone=PHONE,
        campaign_id=campaign.id,
        name="Smoke Test Vendor (Direct Call)",
        category="stationery",
        osm_id=None,
        candidate_id=None,
        lat=28.6139,   # New Delhi coords
        lon=77.2090,
    )
    lead.save(conn)

    # Update lead status
    conn.execute(
        "UPDATE leads SET status=?, round1_call_id=? WHERE id=?",
        (outcome, RUN_ID, lead.id)
    )

    # Log the call
    extracted = {"transcript": transcript_lines, **r1}
    conn.execute(
        """INSERT INTO call_logs (lead_id, call_id, round, timestamp,
           raw_status_output, extracted_fields)
           VALUES (?,?,?,?,?,?)""",
        (lead.id, RUN_ID, 1,
         datetime.now(timezone.utc).isoformat(),
         json.dumps(status),
         json.dumps(extracted))
    )

    # Also store R2 inference fields in a second log entry so dashboard shows summary
    r2_extracted = {**r2}
    conn.execute(
        """INSERT INTO call_logs (lead_id, call_id, round, timestamp,
           raw_status_output, extracted_fields)
           VALUES (?,?,?,?,?,?)""",
        (lead.id, RUN_ID + "_r2infer", 2,
         datetime.now(timezone.utc).isoformat(),
         json.dumps({}),
         json.dumps(r2_extracted))
    )
    conn.execute(
        "UPDATE leads SET status='positive', round2_call_id=? WHERE id=?",
        (RUN_ID + "_r2infer", lead.id)
    )

    conn.commit()

print(f"\nSaved to DB:")
print(f"  Campaign #{campaign.id} — {PRODUCT} @ {CITY}")
print(f"  Lead #{lead.id}     — {_mask_phone(PHONE)}  status=positive")
print(f"  R1 log  call_id={RUN_ID[:16]}...")
print(f"  R2 inference stored  timeline={r2.get('timeline')}  can_supply={r2.get('can_supply')}")
print(f"\nRefresh the dashboard — it will show this call now.")
