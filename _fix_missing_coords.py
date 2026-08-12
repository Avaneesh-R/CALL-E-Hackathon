"""
Geocode leads missing lat/lon using their business name + campaign location via Nominatim.
Updates the leads table in place.
"""
import sys, sqlite3, time, urllib.request, urllib.parse, json
sys.path.insert(0, r'C:\Users\rj02a\OneDrive\Desktop\calle')
from models import get_conn

MISSING_IDS = [42, 41, 33, 25]

def nominatim_search(name, location):
    q = f"{name}, {location}"
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": q, "format": "json", "limit": 1
    })
    req = urllib.request.Request(url, headers={"User-Agent": "calle-pipeline/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            results = json.loads(resp.read())
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        print(f"  Geocode failed for {q!r}: {e}")
    return None, None

with get_conn() as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT l.id, l.name, l.address, l.osm_id, l.candidate_id, l.campaign_id,
               c.location AS camp_location
        FROM leads l
        JOIN campaigns c ON c.id = l.campaign_id
        WHERE l.id IN ({})
    """.format(','.join('?' * len(MISSING_IDS))), MISSING_IDS).fetchall()

    for r in rows:
        name     = r["name"] or ""
        location = r["camp_location"] or ""
        address  = r["address"] or ""
        print(f"Lead #{r['id']} — {name} | campaign location: {location}")

        # Try address first, then name+location
        lat, lon = None, None
        if address:
            lat, lon = nominatim_search(address, location)
            if lat:
                print(f"  Found via address: {lat:.4f}, {lon:.4f}")
        if not lat:
            lat, lon = nominatim_search(name, location)
            if lat:
                print(f"  Found via name+location: {lat:.4f}, {lon:.4f}")

        if lat:
            conn.execute("UPDATE leads SET lat=?, lon=? WHERE id=?", (lat, lon, r["id"]))
            conn.commit()
            print(f"  Updated in DB.")
        else:
            print(f"  Could not geocode — will stay off map.")

        time.sleep(1.1)  # Nominatim rate limit: 1 req/sec

print("\nDone.")
