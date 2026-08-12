import json
from models import get_conn, init_db
init_db()

with get_conn() as conn:
    # Delete synthetic R2-inference-only entry (not a real call)
    conn.execute("DELETE FROM call_logs WHERE call_id LIKE '%_r2infer%'")

    # Patch log id=10: inject real timestamps from CALLE data we fetched
    raw10 = json.loads(conn.execute("SELECT raw_status_output FROM call_logs WHERE id=10").fetchone()[0])
    raw10.setdefault("result", {})
    raw10["result"]["extracted"] = raw10["result"].get("extracted") or {}
    raw10["result"]["extracted"]["calling"] = {
        "started_at": "2026-08-08T22:38:46.000+05:30",
        "ended_at":   "2026-08-08T22:39:25.000+05:30",
        "duration_seconds": 39,
        "status": "finished"
    }
    conn.execute("UPDATE call_logs SET raw_status_output=? WHERE id=10",
                 (json.dumps(raw10),))
    conn.commit()

print("Deleted synthetic log. Patched log id=10 with real timestamps.")

# Re-run audit summary
logs = conn.execute("SELECT id, round, call_id FROM call_logs WHERE lead_id=47 ORDER BY id").fetchall()
for l in logs:
    print(f"  log id={l['id']}  round={l['round']}  call_id={l['call_id']}")
