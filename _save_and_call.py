"""
Save the orphaned VkQva2nxsA transcript to DB and fire the overdue 10-min callback now.
"""
import json, time
from datetime import datetime, timezone
from models import get_conn, init_db
from caller import (_run, poll_until_done, extract_round2_fields,
                    parse_transcript_to_json, infer_from_transcript)
from scheduler import _update_status

PHONE   = "+916350215770"
LEAD_ID = 47
PRODUCT = "office supplies and stationery"

TRANSCRIPT = (
    "[00:00:00] BOT: Hi.\n"
    "[00:00:04] USER: Hello. Hi.\n"
    "[00:00:07] BOT: I'm calling for the requester to follow up on your interest in supplying office supplies and stationery;\n"
    "[00:00:09] USER: It hasn't been 5.\n"
    "[00:00:12] BOT: I'm calling for the requester to follow up on your interest in supplying office supplies and stationery;\n"
    "[00:00:25] USER: I told you to call me in 5 minutes. I told you to call in 5 minutes and you called in like 20 seconds. Call me 10 minutes later, exactly 10 minutes later.\n"
    "[00:00:27] BOT: I'm sorry about that.\n"
    "[00:00:28] BOT: I'll note you want the call back in 10 minutes,\n"
    "[00:00:30] BOT: exactly then.\n"
    "[00:00:32] USER: Yes.\n"
    "[00:00:34] BOT: Thank you for your time,\n"
    "[00:00:35] USER: Thank you.\n"
    "[00:00:35] BOT: bye."
)

init_db()

# Save orphaned transcript to call_logs
with get_conn() as conn:
    existing = conn.execute(
        "SELECT id FROM call_logs WHERE call_id='VkQva2nxsA-rO-YuQclIrw'"
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields) VALUES (?,?,?,?,?)",
            (LEAD_ID, "VkQva2nxsA-rO-YuQclIrw", 2,
             json.dumps({"status": "COMPLETED", "result": {"transcript": TRANSCRIPT,
                 "summary": "User asked to be called back exactly 10 minutes later."}}),
             json.dumps({"transcript": TRANSCRIPT,
                         "next_callback": "10 minutes later",
                         "summary": "User answered but asked for callback exactly 10 minutes later. No supply details collected."}))
        )
        conn.commit()
        print("Saved orphaned transcript to call_logs.")
    else:
        print("Already saved.")

    # Reset lead to positive so R2 can fire again
    conn.execute("UPDATE leads SET status='positive' WHERE id=?", (LEAD_ID,))
    conn.commit()

# Fire the overdue callback now
GOAL = (
    "You are following up with a business owner who expressed interest in supplying "
    "office supplies and stationery. They asked to be called back exactly 10 minutes ago. "
    "Apologise briefly for any timing issues, then confirm their interest and collect: "
    "what products they can supply, approximate quantities, price range per unit, "
    "and best timeline. Keep it under 4 minutes. Be friendly and professional."
)

print("\nPlanning overdue 10-min callback...")
plan = _run(["call", "plan", "--to-phone", PHONE, "--goal", GOAL,
             "--region", "IN", "--language", "English"])
print(f"  plan_id={plan['plan_id']}  ready={plan['ready_to_run']}")
if not plan.get("confirm_token"):
    print("No confirm_token:", plan.get("clarifying_questions"))
    exit(1)

print("Running call...")
run_result = _run(["call", "run",
                   "--plan-id", plan["plan_id"],
                   "--confirm-token", plan["confirm_token"]])
run_id = run_result.get("run_id") or run_result.get("id")
print(f"  run_id={run_id}  status={run_result.get('status')}")

print("Polling for completion...")
status = poll_until_done(run_id)
final = (status.get("status") or "").upper().replace(" ", "_")
print(f"  Final: {final}")

extracted = extract_round2_fields(status)
lines     = parse_transcript_to_json(status)
inference = {}
if lines:
    print(f"  Running inference on {len(lines)}-line transcript...")
    inference = infer_from_transcript(lines, PRODUCT, round_num=2)
    print("  Inference:", json.dumps(inference, indent=2))

combined = {**extracted, **inference}
with get_conn() as conn:
    conn.execute("UPDATE leads SET status='completed', round2_call_id=? WHERE id=?",
                 (run_id, LEAD_ID))
    conn.execute(
        "INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields) VALUES (?,?,?,?,?)",
        (LEAD_ID, run_id, 2, json.dumps(status), json.dumps(combined) if combined else None)
    )
    conn.commit()

print("Done. Lead 47 updated. Dashboard will show full transcript in expandable row.")
