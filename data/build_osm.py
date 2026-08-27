"""Génère data/data_osm.json depuis OpenStreetMap (Overpass API) pour Paris + Seine-Saint-Denis.

Interroge amenity=bicycle_parking et amenity=bicycle_rental, classe chaque élément en
vélo / Vélib' (réseau "Vélib' Métropole") / vélo-cargo (tag cargo_bike=yes|designated),
et écrit des lignes compactes [type, places, locIdx, lon, lat] au même format que
build_officiel.py, pour être embarquées telles quelles dans index.html.
"""
import json
import time
import urllib.parse
import urllib.request
from collections import Counter

OUT = '/Users/thomasvroylandt/Documents/places_velos/data/data_osm.json'

QUERY = """
[out:json][timeout:180];
area["name"="Paris"]["boundary"="administrative"]["admin_level"="8"]->.paris;
area["name"="Seine-Saint-Denis"]["boundary"="administrative"]["admin_level"="6"]->.ssd;
(
  node["amenity"="bicycle_parking"](area.paris);
  way["amenity"="bicycle_parking"](area.paris);
  node["amenity"="bicycle_rental"](area.paris);
  way["amenity"="bicycle_rental"](area.paris);
  node["amenity"="bicycle_parking"](area.ssd);
  way["amenity"="bicycle_parking"](area.ssd);
  node["amenity"="bicycle_rental"](area.ssd);
  way["amenity"="bicycle_rental"](area.ssd);
);
out center tags;
""".strip()

HEADERS = {'User-Agent': 'PlacesVeloParisTool/1.0 (contact: thomas@kantiles.com)'}


def fetch_overpass(retries=3):
    data = urllib.parse.urlencode({'data': QUERY}).encode('utf-8')
    req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=200) as resp:
                return json.loads(resp.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5)


def get_latlon(el):
    if 'lat' in el and 'lon' in el:
        return el['lon'], el['lat']
    c = el.get('center')
    return (c['lon'], c['lat']) if c else (None, None)


def classify(tags):
    amenity = tags.get('amenity')
    if tags.get('cargo_bike') in ('yes', 'designated'):
        return 'cargo'
    if amenity == 'bicycle_rental':
        network = (tags.get('network') or '') + ' ' + (tags.get('brand') or '')
        return 'velib' if 'lib' in network.lower() else None
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


LOC_MAP = {
    'stands': 'Arceaux', 'wall_loops': 'Arceaux', 'rack': 'Support',
    'shed': 'Abri', 'building': 'Bâtiment', 'lockers': 'Consignes',
    'ground_slots': 'Fentes au sol', 'two-tier': 'Deux niveaux', 'floor': 'Sol',
}


def loc_label(tags, kind):
    if kind == 'velib':
        return "Station Vélib'"
    if kind == 'cargo':
        return 'Vélo-cargo'
    return LOC_MAP.get(tags.get('bicycle_parking'), 'Autre')


def main():
    raw = fetch_overpass()
    elements = raw['elements']

    type_codes = {'velo': 0, 'velib': 1, 'cargo': 2}
    rows_raw = []
    locs_set = set()
    skipped = 0
    for el in elements:
        tags = el.get('tags', {})
        kind = classify(tags)
        if kind is None:
            skipped += 1
            continue
        lon, lat = get_latlon(el)
        if lon is None:
            continue
        cap = capacity(tags, kind)
        if cap <= 0:
            continue
        loc = loc_label(tags, kind)
        locs_set.add(loc)
        rows_raw.append((kind, loc, cap, lon, lat))

    locs = sorted(locs_set)
    loc_idx = {l: i for i, l in enumerate(locs)}
    rows = [
        [type_codes[kind], cap, loc_idx[loc], round(lon, 5), round(lat, 5)]
        for kind, loc, cap, lon, lat in rows_raw
    ]

    data = {
        'locs': locs,
        'rows': rows,
        'meta': {
            'source': 'OpenStreetMap (Overpass API) — Paris + Seine-Saint-Denis',
            'note': "Capacité issue du tag OSM capacity=* (estimation par défaut sinon).",
        },
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

    print('rows', len(rows), 'skipped_unclassified', skipped)
    print(Counter(r[0] for r in rows))
    print('capacity total', sum(r[1] for r in rows))


if __name__ == '__main__':
    main()
