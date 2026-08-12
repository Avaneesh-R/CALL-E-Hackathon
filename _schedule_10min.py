from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from models import get_conn, init_db
from script_gen import generate_goal

init_db()
fire_at = datetime.now(timezone.utc) + timedelta(minutes=10)
tz = ZoneInfo("Asia/Kolkata")
local = fire_at.astimezone(tz)

goal = generate_goal("office supplies and stationery", round_num=2)

with get_conn() as conn:
    conn.execute(
        """INSERT INTO scheduled_calls
           (lead_id, campaign_id, scheduled_at, timezone, status, round, goal_script)
           VALUES (?,?,?,?,?,?,?)""",
        (47, 9, fire_at.isoformat(), "Asia/Kolkata", "pending", 2, goal)
    )
    conn.commit()
    row = conn.execute("SELECT id FROM scheduled_calls ORDER BY id DESC LIMIT 1").fetchone()

print(f"Scheduled (id={row['id']}) -> fires at {local.strftime('%H:%M:%S IST')} (10 min from now)")
print("Dashboard scheduler thread will auto-fire it. Keep dashboard running.")
