import sys, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')
from models import get_conn
import sqlite3

with get_conn() as conn:
    conn.row_factory = sqlite3.Row
    logs = conn.execute('''
        SELECT cl.*, l.name, l.phone, l.status
        FROM call_logs cl JOIN leads l ON cl.lead_id=l.id
        WHERE l.campaign_id=14
        ORDER BY cl.id
    ''').fetchall()
    print(f'Call logs for campaign #14: {len(logs)}')

    for log in logs:
        raw = json.loads(log['raw_status_output']) if log['raw_status_output'] else {}
        ext = json.loads(log['extracted_fields'])  if log['extracted_fields']  else {}

        api_status = raw.get('status', '?')
        name       = log['name'] or '?'
        print(f'\n{"="*60}')
        print(f'Vendor  : {name}')
        print(f'Round   : {log["round"]} | API Status: {api_status}')
        print(f'Call ID : {log["call_id"]}')

        summary = raw.get('result', {}).get('summary', '') or raw.get('summary', '')
        if summary:
            print(f'Summary : {summary}')

        tr = raw.get('result', {}).get('transcript', '') or raw.get('transcript', '')
        if isinstance(tr, list) and tr:
            print(f'\nTRANSCRIPT ({len(tr)} lines):')
            for line in tr:
                t   = line.get('time', '')
                spk = line.get('speaker', '')
                txt = line.get('text', '')
                print(f'  [{t}] {spk}: {txt}')
        elif isinstance(tr, str) and tr.strip():
            print(f'\nTRANSCRIPT:\n  {tr}')
        else:
            print('\nTRANSCRIPT: (none recorded)')

        inf = {k: v for k, v in ext.items() if k != 'transcript'}
        if inf:
            print(f'\nAI INFERENCE:')
            for k, v in inf.items():
                print(f'  {k}: {v}')

print('\nDone.')
