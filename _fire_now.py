import json, time
from models import get_conn
from caller import (_run, poll_until_done, extract_round2_fields,
                    parse_transcript_to_json, infer_from_transcript)
from scheduler import _update_status

PHONE    = "+916350215770"
LEAD_ID  = 47
SCHED_ID = 1
PRODUCT  = "office supplies and stationery"

GOAL = (
    "You are following up with a business owner who previously expressed interest in "
    "supplying office supplies and stationery. They said they could call back. "
    "Confirm they are still interested, find out what products they can supply, "
    "approximate quantity, price range per unit, and best timeline to proceed. "
    "Keep it under 4 minutes. Be friendly and professional."
)

print("Planning call...")
plan = _run(["call", "plan", "--to-phone", PHONE, "--goal", GOAL, "--region", "IN", "--language", "English"])
print(f"  plan_id={plan['plan_id']}  ready={plan['ready_to_run']}")

confirm_token = plan.get("confirm_token")
plan_id       = plan.get("plan_id")
if not confirm_token:
    raise RuntimeError("No confirm_token — CALLE needs more info")

print("Running call...")
run_result = _run(["call", "run", "--plan-id", plan_id, "--confirm-token", confirm_token])
run_id = run_result.get("run_id") or run_result.get("call_run_id") or run_result.get("id")
print(f"  run_id={run_id}  status={run_result.get('status')}")
if not run_id:
    raise RuntimeError(f"No run_id: {run_result}")

print("Polling...")
status = poll_until_done(run_id)
final = (status.get("status") or "").upper().replace(" ", "_")
print(f"  Final status: {final}")

extracted = extract_round2_fields(status)
lines     = parse_transcript_to_json(status)
inference = {}
if lines:
    print(f"  Inference on {len(lines)}-line transcript...")
    inference = infer_from_transcript(lines, PRODUCT, round_num=2)
    print("  Inference:", json.dumps(inference, indent=2))

combined = {**extracted, **inference}
with get_conn() as conn:
    conn.execute("UPDATE leads SET status='completed', round2_call_id=? WHERE id=?", (run_id, LEAD_ID))
    conn.execute(
        "INSERT INTO call_logs (lead_id, call_id, round, raw_status_output, extracted_fields) VALUES (?,?,?,?,?)",
        (LEAD_ID, run_id, 2, json.dumps(status), json.dumps(combined) if combined else None)
    )
    conn.commit()

_update_status(SCHED_ID, "fired")
print("Done. Lead 47 -> completed. Check dashboard.")
