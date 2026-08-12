import json
from models import get_conn, init_db
init_db()
with get_conn() as conn:
    logs = conn.execute(
        "SELECT * FROM call_logs WHERE lead_id=47 ORDER BY id DESC"
    ).fetchall()
    for log in logs:
        print(f"\n=== call_log id={log['id']} round={log['round']} call_id={log['call_id']} ===")
        ef = json.loads(log['extracted_fields']) if log['extracted_fields'] else {}
        raw = json.loads(log['raw_status_output']) if log['raw_status_output'] else {}
        transcript = ef.get('transcript') or []
        print(f"Extracted fields (non-transcript): { {k:v for k,v in ef.items() if k!='transcript'} }")
        print(f"Transcript lines: {len(transcript)}")
        for line in transcript:
            print(f"  [{line.get('time','')}] {line.get('speaker','')}: {line.get('text','')}")
        if not transcript:
            # try raw
            result = raw.get('result') or {}
            t = result.get('transcript') or (result.get('extracted') or {}).get('transcript') or ''
            print(f"Raw transcript: {t}")
        print(f"Raw status: {raw.get('status')}")
        outcome = (raw.get('result') or {}).get('outcome') or {}
        print(f"Outcome: {outcome}")
        summary = (raw.get('result') or {}).get('summary') or ''
        print(f"Summary: {summary}")
