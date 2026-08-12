from discovery import geocode_location, _run_overpass

# Try South Delhi — much larger area
bbox = geocode_location("South Delhi, India")
s, w, n, e = bbox
print(f"South Delhi bbox: {bbox}")

bbox_str = f"{s},{w},{n},{e}"

# Shoe shops without phone filter
q1 = f'[out:json][timeout:30];\n(\n  node["shop"="shoes"]({bbox_str});\n  way["shop"="shoes"]({bbox_str});\n);\nout tags qt 50;'
els = _run_overpass(q1)
print(f"\nShoe shops in South Delhi (no phone filter): {len(els)}")
with_phone = [e for e in els if e.get("tags", {}).get("phone") or e.get("tags", {}).get("contact:phone")]
print(f"Of those, with phone: {len(with_phone)}")
for el in with_phone:
    t = el.get("tags", {})
    print(f"  {t.get('name','?')} | {t.get('phone') or t.get('contact:phone')}")

# Any shop with phone at all in South Delhi
q2 = f'[out:json][timeout:30];\n(\n  node["shop"]["phone"]({bbox_str});\n  node["shop"]["contact:phone"]({bbox_str});\n);\nout tags qt 30;'
els2 = _run_overpass(q2)
print(f"\nAny shop with phone in South Delhi: {len(els2)}")
for el in els2[:10]:
    t = el.get("tags", {})
    print(f"  {t.get('name','?')} | {t.get('shop','?')} | {t.get('phone') or t.get('contact:phone')}")
