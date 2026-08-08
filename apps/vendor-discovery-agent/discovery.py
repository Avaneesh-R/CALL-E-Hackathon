"""
Module 1 — Vendor Discovery via OpenStreetMap Overpass API.
Finds businesses matching a product category within a location,
returning only those with a phone number.
Data is ODbL licensed — attribution required in any user-facing output.
"""
import re
import json
import time
import urllib.request
import urllib.parse
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
USER_AGENT = "VendorDiscoveryHackathon/1.0 (CALLE hackathon project)"

# Maps plain-English product keywords to OSM shop/amenity tags.
# Not exhaustive — the fallback does a free-text name search.
KEYWORD_TAG_MAP = {
    "grocery": [("shop", "supermarket"), ("shop", "grocery"), ("shop", "convenience")],
    "electronics": [("shop", "electronics"), ("shop", "computer")],
    "hardware": [("shop", "hardware"), ("shop", "doityourself")],
    "furniture": [("shop", "furniture")],
    "clothing": [("shop", "clothes"), ("shop", "fashion")],
    "bakery": [("shop", "bakery"), ("amenity", "cafe")],
    "restaurant": [("amenity", "restaurant"), ("amenity", "fast_food")],
    "pharmacy": [("amenity", "pharmacy"), ("shop", "chemist")],
    "stationery": [("shop", "stationery"), ("shop", "office_supplies")],
    "printing": [("shop", "copyshop"), ("craft", "printing")],
    "catering": [("amenity", "catering"), ("shop", "deli")],
    "florist": [("shop", "florist")],
    "automotive": [("shop", "car"), ("shop", "car_parts"), ("amenity", "car_repair")],
    "hotel": [("tourism", "hotel"), ("tourism", "hostel")],
    "gym": [("leisure", "fitness_centre"), ("amenity", "gym")],
    "bookstore": [("shop", "books")],
    "toys": [("shop", "toys")],
    "jewelry": [("shop", "jewelry"), ("shop", "jewellery")],
    "sports": [("shop", "sports")],
    "medical": [("amenity", "clinic"), ("amenity", "hospital"), ("amenity", "doctors")],
    "shoes": [("shop", "shoes")],
    "footwear": [("shop", "shoes")],
    "shoe": [("shop", "shoes")],
}


def _keyword_to_tags(product_description: str) -> list[tuple[str, str]]:
    desc = product_description.lower()
    for keyword, tags in KEYWORD_TAG_MAP.items():
        if keyword in desc:
            return tags
    # fallback: match against shop and amenity with name containing keywords
    return []


MIN_BBOX_DEGREES = 0.02  # ~2km; expand if Nominatim returns a point/tiny bbox


def geocode_location(location: str) -> tuple[float, float, float, float]:
    """Returns (south, west, north, east) bounding box for location string."""
    params = urllib.parse.urlencode({
        "q": location,
        "format": "json",
        "limit": 1,
    })
    req = urllib.request.Request(
        f"{NOMINATIM_URL}?{params}",
        headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    if not data:
        raise ValueError(f"Could not geocode location: {location!r}")
    result = data[0]
    bb = result["boundingbox"]  # [south, north, west, east]
    s, n, w, e = float(bb[0]), float(bb[1]), float(bb[2]), float(bb[3])
    # Expand tiny bboxes (points, small landmarks) to MIN_BBOX_DEGREES
    if (n - s) < MIN_BBOX_DEGREES or (e - w) < MIN_BBOX_DEGREES:
        lat = (s + n) / 2
        lon = (w + e) / 2
        half = MIN_BBOX_DEGREES / 2
        s, n, w, e = lat - half, lat + half, lon - half, lon + half
    return s, w, n, e


def _build_overpass_query(tags: list[tuple[str, str]], bbox: tuple, limit: int) -> str:
    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"
    union_parts = []
    for tag_key, tag_val in tags:
        for elem_type in ("node", "way"):
            union_parts.append(f'  {elem_type}["{tag_key}"="{tag_val}"]["phone"]({bbox_str});')
            union_parts.append(f'  {elem_type}["{tag_key}"="{tag_val}"]["contact:phone"]({bbox_str});')
    union_body = "\n".join(union_parts)
    return f'[out:json][timeout:60];\n(\n{union_body}\n);\nout body center qt {limit};'


def _build_name_fallback_query(product: str, bbox: tuple, limit: int) -> str:
    s, w, n, e = bbox
    bbox_str = f"{s},{w},{n},{e}"
    safe = re.sub(r'[^a-zA-Z0-9 ]', '', product)[:40]
    return (
        f'[out:json][timeout:30];\n'
        f'(\n'
        f'  node["name"~"{safe}",i]["phone"]({bbox_str});\n'
        f'  node["name"~"{safe}",i]["contact:phone"]({bbox_str});\n'
        f');\n'
        f'out body center qt {limit};'
    )


def _run_overpass(query: str) -> list[dict]:
    import urllib.error
    data = urllib.parse.urlencode({"data": query}).encode()
    last_err = None
    for server in OVERPASS_SERVERS:
        req = urllib.request.Request(
            server, data=data,
            headers={"User-Agent": USER_AGENT,
                     "Content-Type": "application/x-www-form-urlencoded"}
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                result = json.loads(resp.read())
            return result.get("elements", [])
        except urllib.error.HTTPError as e:
            if e.code == 504:
                last_err = e
                time.sleep(3)
                continue
            last_err = e
            continue
        except (urllib.error.URLError, OSError) as e:
            last_err = e
            continue
    raise RuntimeError(f"All Overpass servers failed. Last error: {last_err}")


def _normalize_phone(raw: str) -> Optional[str]:
    digits = re.sub(r'[^\d+]', '', raw)
    if not digits:
        return None
    if not digits.startswith('+'):
        digits = '+' + digits
    if len(digits) < 8:
        return None
    return digits


def discover_vendors(product_description: str, location: str, limit: int = 20) -> list[dict]:
    """
    Returns a list of vendor dicts with keys:
      name, phone (E.164 best-effort), category, lat, lon, osm_id
    Only vendors with a usable phone number are returned.
    Attribution: Data © OpenStreetMap contributors (ODbL)
    """
    bbox = geocode_location(location)
    tags = _keyword_to_tags(product_description)

    if tags:
        elements = _run_overpass(_build_overpass_query(tags, bbox, limit * 3))
    else:
        elements = []

    if not elements:
        elements = _run_overpass(_build_name_fallback_query(product_description, bbox, limit * 3))

    seen_phones = set()
    vendors = []
    for el in elements:
        t = el.get("tags", {})
        raw_phone = t.get("phone") or t.get("contact:phone") or ""
        phone = _normalize_phone(raw_phone)
        if not phone or phone in seen_phones:
            continue
        seen_phones.add(phone)
        # Build address from OSM addr:* tags
        addr_parts = []
        if t.get("addr:housenumber") and t.get("addr:street"):
            addr_parts.append(f"{t['addr:housenumber']} {t['addr:street']}")
        elif t.get("addr:street"):
            addr_parts.append(t["addr:street"])
        elif t.get("addr:full"):
            addr_parts.append(t["addr:full"])
        elif t.get("addr:place"):
            addr_parts.append(t["addr:place"])
        for key in ("addr:suburb", "addr:city", "addr:state", "addr:postcode"):
            if t.get(key):
                addr_parts.append(t[key])
        address = ", ".join(addr_parts) if addr_parts else None

        vendors.append({
            "name": t.get("name", "Unknown"),
            "phone": phone,
            "category": t.get("shop") or t.get("amenity") or t.get("craft") or "business",
            "lat": el.get("lat") or el.get("center", {}).get("lat"),
            "lon": el.get("lon") or el.get("center", {}).get("lon"),
            "osm_id": f"{el['type']}/{el['id']}",
            "address": address,
        })
        if len(vendors) >= limit:
            break

    return vendors
