import json

with open('/Users/thomasvroylandt/Documents/places_velos/scratchpad/osm_raw.json', encoding='utf-8') as f:
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
        return 'velib' if is_velib else None  # ignore non-Velib rental systems
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
    # sensible defaults when capacity is missing
    return 15 if kind == 'velib' else 2

type_codes = {'velo': 0, 'velib': 1, 'cargo': 2}

# reuse same loc/zone vocab shape as the official dataset for a consistent schema
# loc: derive from bicycle_parking = surface/covered/shed/etc; velib/cargo -> 'Vélib' station' / 'Vélo-cargo'
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
rues_set = set()
zones_set = set()
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
    rue = tags.get('addr:street') or ''
    loc = loc_label(tags, kind)
    zone = tags.get('addr:postcode') or ''
    rues_set.add(rue)
    locs_set.add(loc)
    zones_set.add(zone)
    rows.append((kind, rue, loc, zone, cap, lon, lat))

rues = sorted(rues_set)
rue_idx = {r: i for i, r in enumerate(rues)}
locs = sorted(locs_set)
loc_idx = {l: i for i, l in enumerate(locs)}
zones = sorted(zones_set)
zone_idx = {z: i for i, z in enumerate(zones)}

# arrondissement not reliably available from OSM tags (postcode proxy: 750XX)
def arr_from_zone(z):
    if z and z.startswith('750') and len(z) == 5:
        try:
            n = int(z[3:])
            if n == 0:
                n = 1
            return n
        except ValueError:
            return 0
    return 0

out_rows = []
for kind, rue, loc, zone, cap, lon, lat in rows:
    arr = arr_from_zone(zone)
    out_rows.append([
        arr,
        rue_idx[rue],
        type_codes[kind],
        cap,
        cap,  # OSM has a single capacity figure -> use for both metrics
        loc_idx[loc],
        zone_idx[zone],
        round(lon, 5),
        round(lat, 5),
    ])

arronds = sorted(set(r[0] for r in out_rows))

data = {
    'rues': rues,
    'locs': locs,
    'zones': zones,
    'arronds': arronds,
    'rows': out_rows,
    'meta': {
        'source': 'OpenStreetMap (Overpass API)',
        'note': "Capacité issue du tag OSM capacity=* (à défaut, estimation par défaut). Arrondissement estimé depuis le code postal quand disponible.",
    }
}

out_path = '/Users/thomasvroylandt/Documents/places_velos/scratchpad/data_osm.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

import os
print('rows', len(out_rows), 'skipped_unclassified', skipped_unclassified, 'skipped_no_geo', skipped_no_geo)
from collections import Counter
print(Counter(r[2] for r in out_rows))
print('placal(=capacity) total', sum(r[3] for r in out_rows))
print('file size', os.path.getsize(out_path))
