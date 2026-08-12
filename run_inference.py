"""Re-fetch call result from CALL-E by run_id and run full R1+R2 inference."""
import json
from caller import (infer_from_transcript, parse_transcript_to_json,
                    classify_round1, _run)

RUN_ID  = "pY81FiD487J7N9G-YRfk-A"
PRODUCT = "stationery and office supplies"
PHONE   = "+91****770"

SEP = "=" * 60

print(f"\n{SEP}")
print("FETCHING CALL RESULT FROM CALL-E")
print(SEP)
status = _run(["call", "status", "--run-id", RUN_ID])
print(f"  Status : {status.get('status')}")

transcript_lines = parse_transcript_to_json(status)

if not transcript_lines:
    # Transcript already known from smoke test output — use it directly
    raw_transcript = (
        "[00:00:00] BOT: Hi.\n"
        "[00:00:04] USER: Hello.\n"
        "[00:00:07] BOT: I'm calling for a client who is looking to source stationery and office supplies for business needs;\n"
        "[00:00:12] BOT: can your company supply those?\n"
        "[00:00:16] USER: Hello. Yes.\n"
        "[00:00:19] BOT: Great, could you share your catalog or product details,\n"
        "[00:00:27] BOT: pricing, minimum order requirements, and how ordering or quotations work?\n"
        "[00:00:38] USER: Okay. Sure. Call me at 5:05 PM tomorrow.\n"
        "[00:00:40] BOT: Got it.\n"
        "[00:00:41] BOT: I'll pass that along.\n"
        "[00:00:47] USER: Okay.\n"
        "[00:00:49] BOT: Thank you, bye."
    )
    from caller import _TRANSCRIPT_LINE_RE
    for line in raw_transcript.strip().splitlines():
        m = _TRANSCRIPT_LINE_RE.match(line.strip())
        if m:
            transcript_lines.append({"time": m.group(1), "speaker": m.group(2), "text": m.group(3)})
    print("  (Transcript loaded from smoke test capture)")

print(f"\n{SEP}")
print(f"FULL TRANSCRIPT  ({len(transcript_lines)} lines)")
print(SEP)
for t in transcript_lines:
    print(f"  [{t['time']}] {t['speaker']:<6}: {t['text']}")

outcome = classify_round1(status)
print(f"\n  CALL-E R1 classification : {outcome.upper()}")

print(f"\n{SEP}")
print("ROUND 1 INFERENCE  -  Qualification Analysis")
print(SEP)
r1 = infer_from_transcript(transcript_lines, PRODUCT, round_num=1)
for label, key in [
    ("Interest Level",    "interest_level"),
    ("Sentiment",         "sentiment"),
    ("Key Signals",       "key_signals"),
    ("Recommend R2 Call", "recommend_round2"),
    ("Summary",           "summary"),
]:
    print(f"  {label:<22}: {r1.get(key, '-')}")

print(f"\n{SEP}")
print("ROUND 2 INFERENCE  -  Data Capture Analysis")
print(SEP)
r2 = infer_from_transcript(transcript_lines, PRODUCT, round_num=2)
for label, key in [
    ("Contact Name",       "contact_name"),
    ("Can Supply",         "can_supply"),
    ("Quantity Mentioned", "quantity_mentioned"),
    ("Price Range",        "price_range"),
    ("Timeline",           "timeline"),
    ("Next Steps",         "next_steps"),
    ("Summary",            "summary"),
]:
    print(f"  {label:<22}: {r2.get(key, '-')}")

print(f"\n{SEP}")
print("VERDICT")
print(SEP)
interest  = r1.get("interest_level", "unknown")
rec_r2    = r1.get("recommend_round2", False)
timeline  = r2.get("timeline") or r2.get("next_steps") or "not captured"
can_supply = r2.get("can_supply")
lead_grade = "HOT" if interest == "high" else "WARM" if interest == "medium" else "COLD"

print(f"  Lead Grade     : {lead_grade}  (interest_level={interest})")
print(f"  CALL-E outcome : {outcome.upper()}")
print(f"  Can Supply     : {can_supply}")
print(f"  Follow-up at   : {timeline}")
print(f"  Proceed to R2  : {'YES' if rec_r2 else 'NO'}")
print(f"  Action         : {'Schedule R2 call - vendor confirmed availability and gave a callback time' if rec_r2 else 'Mark negative and move on'}")
print(SEP)
