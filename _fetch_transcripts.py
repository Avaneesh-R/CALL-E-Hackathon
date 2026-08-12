import sys, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')
from models import get_conn
import sqlite3

PHONE = '6350215770'

with get_conn() as conn:
    conn.row_factory = sqlite3.Row
    leads = conn.execute("SELECT * FROM leads WHERE phone LIKE ?", (f'%{PHONE}%',)).fetchall()
    print(f"Leads found for {PHONE}: {len(leads)}")
    for l in leads:
        print(f"  Lead #{l['id']} | campaign={l['campaign_id']} | status={l['status']} | name={l['name']}")

    lead_ids = [l['id'] for l in leads]
    if not lead_ids:
        # Also check call_logs directly by call_id in raw JSON
        print("\nChecking call_logs for any raw output mentioning this number...")
        all_logs = conn.execute("SELECT * FROM call_logs ORDER BY id").fetchall()
        matched = []
        for log in all_logs:
            raw = log['raw_status_output'] or ''
            if PHONE in raw:
                matched.append(log)
        print(f"call_logs with {PHONE} in raw JSON: {len(matched)}")
        lead_ids_from_logs = list(set(log['lead_id'] for log in matched))
        lead_ids = lead_ids_from_logs

    for lid in lead_ids:
        logs = conn.execute("SELECT * FROM call_logs WHERE lead_id=? ORDER BY id", (lid,)).fetchall()
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lid,)).fetchone()
        print(f"\n{'='*60}")
        print(f"Lead #{lid} — {lead['name'] if lead else 'unknown'} | phone={lead['phone'] if lead else '?'}")
        print(f"Campaign #{lead['campaign_id'] if lead else '?'} | Status: {lead['status'] if lead else '?'}")
        print(f"Call logs: {len(logs)}")
        print('='*60)

        for log in logs:
            raw = json.loads(log['raw_status_output']) if log['raw_status_output'] else {}
            extracted = json.loads(log['extracted_fields']) if log['extracted_fields'] else {}

            print(f"\n  --- Round {log['round']} | Call ID: {log['call_id']} ---")
            print(f"  API Status: {raw.get('status', '?')}")

            # Summary from API
            summary = raw.get('result', {}).get('summary', '') or raw.get('summary', '')
            if summary:
                print(f"  API Summary: {summary}")

            # Transcript
            tr = raw.get('result', {}).get('transcript', '') or raw.get('transcript', '')
            if isinstance(tr, list) and tr:
                print(f"\n  TRANSCRIPT ({len(tr)} lines):")
                for line in tr:
                    t = line.get('time', '')
                    spk = line.get('speaker', '')
                    txt = line.get('text', '')
                    print(f"    [{t}] {spk}: {txt}")
            elif isinstance(tr, str) and tr.strip():
                print(f"\n  TRANSCRIPT:\n    {tr}")
            else:
                print("  TRANSCRIPT: (none recorded)")

            # Inference output
            inf = {k: v for k, v in extracted.items() if k != 'transcript'}
            if inf:
                print(f"\n  AI INFERENCE:")
                for k, v in inf.items():
                    print(f"    {k}: {v}")

print("\nDone.")
