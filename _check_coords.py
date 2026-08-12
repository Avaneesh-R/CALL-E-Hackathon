import sys, sqlite3
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')
from models import get_conn

with get_conn() as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT l.id, l.name, l.phone, l.status, l.lat, l.lon, l.campaign_id,
               COUNT(cl.id) as call_count
        FROM leads l
        LEFT JOIN call_logs cl ON cl.lead_id=l.id
        WHERE l.status NOT IN ('not_called','skipped','failed')
        GROUP BY l.id
        ORDER BY l.id DESC
    """).fetchall()

    has_coords  = [r for r in rows if r["lat"] is not None and r["lat"] != ""]
    no_coords   = [r for r in rows if not (r["lat"] is not None and r["lat"] != "")]

    print(f"Answered/attempted leads: {len(rows)}")
    print(f"  With lat/lon : {len(has_coords)}")
    print(f"  Missing coords: {len(no_coords)}")
    print()
    print("Missing lat/lon (these won't appear on map):")
    for r in no_coords:
        print(f"  Lead #{r['id']:3d} | {(r['name'] or '?')[:32]:<32} | {r['status']:<12} | calls={r['call_count']} | campaign={r['campaign_id']}")
    print()
    print("Has lat/lon:")
    for r in has_coords:
        print(f"  Lead #{r['id']:3d} | {(r['name'] or '?')[:32]:<32} | {r['status']:<12} | lat={r['lat']:.4f}")
