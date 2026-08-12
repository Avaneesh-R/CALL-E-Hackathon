from models import get_conn, init_db
init_db()
with get_conn() as conn:
    rows = conn.execute("SELECT id, name, phone, masked_phone, osm_id, status, campaign_id FROM leads").fetchall()
    for r in rows:
        if "6350" in (r["phone"] or ""):
            print(dict(r))
