"""
Full pipeline test run â€” 3 vendors, LA stationery shops, custom short goal.
"""
import os, sys, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')

from datetime import datetime, timezone
from models import init_db, get_conn, Campaign, Lead, _mask_phone
from discovery import discover_vendors
from caller import execute_call_pipeline, classify_round1, parse_transcript_to_json, infer_from_transcript
from scheduler import schedule_followup

PRODUCT  = "wholesale stationery and office supplies"
LOCATION = "Houston, Texas, USA"
LIMIT    = 3
REGION   = "US"
LANGUAGE = "English"
SKIP_HOURS = True   # Saturday — bypass Mon-Fri gate

GOAL = (
    "You are a procurement agent sourcing wholesale stationery and office supplies. "
    "Introduce yourself briefly. Ask: do they supply stationery or office goods in bulk? "
    "If yes, ask about price range and minimum order quantity. "
    "Keep the call under 90 seconds. Be polite and professional."
)

init_db()

print(f"\n{'='*60}")
print(f"Product : {PRODUCT}")
print(f"Location: {LOCATION}")
print(f"Time    : {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
print(f"{'='*60}\n")

print("Discovering vendors via OpenStreetMap...")
vendors = discover_vendors(PRODUCT, LOCATION, LIMIT)
if not vendors:
    print("No vendors found. Exiting.")
    sys.exit(1)

print(f"Found {len(vendors)} vendor(s):\n")
for i, v in enumerate(vendors, 1):
    print(f"  {i}. {v['name'][:40]:<40} {_mask_phone(v['phone'])}  ({v['category']})")

# Save campaign
with get_conn() as conn:
    campaign = Campaign(
        product_description=PRODUCT,
        location=LOCATION,
        goal_script=GOAL,
        consent_basis="client-reviewed-and-approved",
        consent_approved_at=datetime.now(timezone.utc).isoformat(),
    )
    campaign.save(conn)
    campaign_id = campaign.id
    conn.commit()
    print(f"\nCampaign #{campaign_id} created.\n")

    leads = []
    for v in vendors:
        lead = Lead(
            phone=v["phone"], campaign_id=campaign_id,
            name=v.get("name"), category=v.get("category"),
            lat=v.get("lat"), lon=v.get("lon"),
            osm_id=v.get("osm_id"),
            candidate_id=f"osm:{v['osm_id']}" if v.get("osm_id") else None,
            address=v.get("address"),
        )
        lead.save(conn)
        leads.append(lead)
    conn.commit()

print(f"{'â”€'*60}")
print("ROUND 1 â€” Qualification calls")
print(f"{'â”€'*60}\n")

for lead in leads:
    print(f"[{lead.name or lead.masked_phone}]")
    try:
        status_output = execute_call_pipeline(
            phone=lead.phone, goal=GOAL,
            region=REGION, language=LANGUAGE,
            lat=None if SKIP_HOURS else lead.lat,
            lon=None if SKIP_HOURS else lead.lon,
        )

        if status_output.get("status") == "SKIPPED":
            reason = status_output.get("skip_reason", "")
            print(f"  SKIPPED â€” {reason}\n")
            with get_conn() as conn:
                conn.execute("UPDATE leads SET status='skipped', skip_reason=? WHERE id=?",
                             (reason, lead.id)); conn.commit()
            continue

        call_id = status_output.get("run_id") or "unknown"
        outcome  = classify_round1(status_output)
        lines    = parse_transcript_to_json(status_output)
        inference = {}
        if lines:
            try:
                inference = infer_from_transcript(lines, PRODUCT, round_num=1)
            except Exception as e:
                print(f"  Inference error: {e}")

        print(f"  Outcome  : {outcome}")
        print(f"  Interest : {inference.get('interest_level','?')}")
        print(f"  Sentiment: {inference.get('sentiment','?')}")
        print(f"  Summary  : {inference.get('summary','')[:100]}")

        # Store in DB
        with get_conn() as conn:
            conn.execute("UPDATE leads SET status=?, round1_call_id=? WHERE id=?",
                         (outcome, call_id, lead.id))
            conn.execute(
                "INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields) VALUES (?,?,?,?,?)",
                (lead.id, call_id, 1,
                 json.dumps(status_output),
                 json.dumps({"transcript": lines, **inference}))
            )
            conn.commit()

        # Auto-schedule R2 if positive and gave a timeline
        if outcome == "positive" and lead.osm_id:
            timeline = inference.get("timeline") or inference.get("next_steps") or ""
            if timeline and timeline not in ("null","None","","-"):
                schedule_followup(
                    lead_id=lead.id, campaign_id=campaign_id,
                    timeline_text=timeline, product=PRODUCT,
                    lat=lead.lat, lon=lead.lon,
                    region=REGION, language=LANGUAGE,
                )

    except Exception as e:
        print(f"  ERROR: {e}")
        with get_conn() as conn:
            conn.execute("UPDATE leads SET status='failed' WHERE id=?", (lead.id,)); conn.commit()

    print()

print(f"{'='*60}")
print("Done. Open dashboard to see full transcripts and inference.")
print(f"Campaign #{campaign_id} â€” http://127.0.0.1:5000")
print(f"{'='*60}\n")
