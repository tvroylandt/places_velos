import json

with open('/Users/thomasvroylandt/Documents/places_velos/scratchpad/osm_raw_wide.json', encoding='utf-8') as f:
    raw = json.load(f)

elements = raw['elements']

def get_latlon(el):
    if 'lat' in el and 'lon' in el:
        return el['lon'], el['lat']
    c = el.get('center')
    if c:
        return c['lon'], c['lat']
    return None, None

def classify(tags):
    amenity = tags.get('amenity')
    cargo = tags.get('cargo_bike') in ('yes', 'designated')
    network = (tags.get('network') or '') + ' ' + (tags.get('brand') or '')
    is_velib = amenity == 'bicycle_rental' and 'lib' in network.lower()
    if cargo:
        return 'cargo'
    if amenity == 'bicycle_rental':
        return 'velib' if is_velib else None
    if amenity == 'bicycle_parking':
        return 'velo'
    return None

def capacity(tags, kind):
    cap = tags.get('capacity')
    if cap is not None:
        try:
            return max(0, int(float(cap)))
        except ValueError:
            pass
    return 15 if kind == 'velib' else 2

type_codes = {'velo': 0, 'velib': 1, 'cargo': 2}

def loc_label(tags, kind):
    if kind == 'velib':
        return "Station Vélib'"
    if kind == 'cargo':
        return 'Vélo-cargo'
    bp = tags.get('bicycle_parking')
    mapping = {
        'stands': 'Arceaux', 'wall_loops': 'Arceaux', 'rack': 'Support',
        'shed': 'Abri', 'building': 'Bâtiment', 'lockers': 'Consignes',
        'ground_slots': 'Fentes au sol', 'two-tier': 'Deux niveaux',
        'floor': 'Sol',
    }
    return mapping.get(bp, 'Autre')

rows = []
locs_set = set()
skipped_no_geo = 0
skipped_unclassified = 0

for el in elements:
    tags = el.get('tags', {})
    kind = classify(tags)
    if kind is None:
        skipped_unclassified += 1
        continue
    lon, lat = get_latlon(el)
    if lon is None:
        skipped_no_geo += 1
        continue
    cap = capacity(tags, kind)
    if cap <= 0:
        continue
    loc = loc_label(tags, kind)
    locs_set.add(loc)
    rows.append((kind, loc, cap, lon, lat))

locs = sorted(locs_set)
loc_idx = {l: i for i, l in enumerate(locs)}

out_rows = []
for kind, loc, cap, lon, lat in rows:
    out_rows.append([
        type_codes[kind],
        cap,
        cap,
        loc_idx[loc],
        round(lon, 5),
        round(lat, 5),
    ])

data = {
    'locs': locs,
    'rows': out_rows,
    'meta': {
        'source': 'OpenStreetMap (Overpass API) — Paris + Seine-Saint-Denis',
        'note': "Capacité issue du tag OSM capacity=* (estimation par défaut sinon).",
    }
}

out_path = '/Users/thomasvroylandt/Documents/places_velos/scratchpad/data_osm.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

import os
from collections import Counter
print('rows', len(out_rows), 'skipped_unclassified', skipped_unclassified, 'skipped_no_geo', skipped_no_geo)
print(Counter(r[0] for r in out_rows))
print('capacity total', sum(r[1] for r in out_rows))
print('file size', os.path.getsize(out_path))

lons = [r[4] for r in out_rows]
lats = [r[5] for r in out_rows]
print('bbox', min(lons), max(lons), min(lats), max(lats))
