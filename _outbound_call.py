import os, sys, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')
from caller import plan_call, run_call, poll_until_done

phone = '+916350215770'
goal = (
    'You are a wholesale supplier of Monster Energy drinks reaching out to a potential retail vendor. '
    'Introduce yourself briefly as a Monster Energy wholesale distributor. '
    'Ask the vendor if they currently sell energy drinks or beverages, '
    'and whether they would be interested in wholesale Monster drink deliveries to their location. '
    'Find out: 1) Do they need regular deliveries? 2) What quantities might they need? '
    'If the vendor says to call back later or mentions they are busy, ALWAYS ask them: '
    '"When would be a good time for me to call you back?" and wait for a specific time before ending the call. '
    'Do not hang up until you have a callback time or a clear rejection. '
    'Be friendly, professional and patient. Listen fully before responding.'
)

print('Planning call...')
plan = plan_call(phone, goal, region='IN', language='English')
print('Plan ID:', plan.get('plan_id'), '| ready:', plan.get('ready_to_run'))

plan_id = plan.get('plan_id')
confirm_token = plan.get('confirm_token')
if not plan_id or not confirm_token:
    print('ERROR:', plan); sys.exit(1)

print('Calling...')
run = run_call(plan_id, confirm_token)
run_id = run.get('run_id') or run.get('id')
print('Run ID:', run_id)

print('Polling...')
result = poll_until_done(run_id)
print('\nStatus:', result.get('status'))

tr = result.get('result', {}).get('transcript', '')
print('\n--- TRANSCRIPT ---')
if isinstance(tr, list):
    for line in tr:
        print(f"[{line.get('time','')}] {line.get('speaker','')}: {line.get('text','')}")
else:
    print(tr)

summary = result.get('result', {}).get('summary', '')
if summary:
    print('\n--- SUMMARY ---')
    print(summary)
