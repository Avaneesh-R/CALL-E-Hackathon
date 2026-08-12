import json
from models import get_conn

def fix_encoding(s):
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s

def fix_dict(obj):
    if isinstance(obj, dict):
        return {k: fix_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [fix_dict(i) for i in obj]
    if isinstance(obj, str):
        return fix_encoding(obj)
    return obj

with get_conn() as conn:
    log = conn.execute("SELECT * FROM call_logs WHERE id=11").fetchone()
    ef = json.loads(log["extracted_fields"])
    fixed = fix_dict(ef)
    conn.execute("UPDATE call_logs SET extracted_fields=? WHERE id=11",
                 (json.dumps(fixed, ensure_ascii=False),))
    conn.commit()
    print("Fixed. price_range:", fixed.get("price_range"))
