from datetime import datetime, timezone, timedelta
from models import get_conn, init_db
from script_gen import generate_goal

init_db()
fire_at = datetime.now(timezone.utc) + timedelta(minutes=2)
goal = generate_goal("general vendor follow-up", round_num=2)

with get_conn() as conn:
    conn.execute(
        """INSERT INTO scheduled_calls
           (lead_id, campaign_id, scheduled_at, timezone, status, round, goal_script)
           VALUES (?,?,?,?,?,?,?)""",
        (47, 9, fire_at.isoformat(), "Asia/Kolkata", "pending", 2, goal)
    )
    conn.commit()
    row = conn.execute("SELECT * FROM scheduled_calls ORDER BY id DESC LIMIT 1").fetchone()
    print("Scheduled:", dict(row))
    local = fire_at.astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata"))
    print("Fires at (IST):", local.strftime("%H:%M:%S"))
