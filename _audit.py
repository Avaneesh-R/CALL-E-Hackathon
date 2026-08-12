import json
from models import get_conn, init_db
init_db()
with get_conn() as conn:
    logs = conn.execute(
        "SELECT * FROM call_logs WHERE lead_id=47 ORDER BY id"
    ).fetchall()
    scheds = conn.execute(
        "SELECT * FROM scheduled_calls WHERE lead_id=47 ORDER BY id"
    ).fetchall()
    lead = conn.execute("SELECT * FROM leads WHERE id=47").fetchone()

print(f"Lead status: {lead['status']}  round1_call_id={lead['round1_call_id']}  round2_call_id={lead['round2_call_id']}\n")

for log in logs:
    ef = json.loads(log['extracted_fields']) if log['extracted_fields'] else {}
    raw = json.loads(log['raw_status_output']) if log['raw_status_output'] else {}
    result = raw.get('result') or {}
    transcript_raw = result.get('transcript') or ef.get('transcript') or []
    calling = (raw.get('result') or {}).get('extracted', {}).get('calling', {})
    start = calling.get('started_at', '')
    end   = calling.get('ended_at', '')
    dur   = calling.get('duration_seconds', '')
    print(f"=== log id={log['id']}  round={log['round']}  status={raw.get('status','?')} ===")
    print(f"    call_id : {log['call_id']}")
    print(f"    started : {start or 'N/A'}")
    print(f"    ended   : {end or 'N/A'}")
    print(f"    duration: {dur}s")
    if isinstance(transcript_raw, str):
        lines = [l for l in transcript_raw.strip().splitlines() if l.strip()]
        for l in lines:
            print(f"      {l}")
    elif isinstance(transcript_raw, list):
        for l in transcript_raw:
            if isinstance(l, dict):
                print(f"      [{l.get('time','')}] {l.get('speaker','')}: {l.get('text','')}")
    inf = {k:v for k,v in ef.items() if k not in ('transcript','raw_inference')}
    if inf:
        print(f"    inference: {json.dumps(inf)}")
    print()

print("=== Scheduled Calls ===")
for s in scheds:
    print(f"  id={s['id']}  status={s['status']}  scheduled_at={s['scheduled_at']}  tz={s['timezone']}")
