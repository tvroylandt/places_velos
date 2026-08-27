import pandas as pd
import json
import struct

df = pd.read_parquet('/Users/thomasvroylandt/Documents/places_velos/stationnement-voie-publique-emplacements.parquet')

def decode_xy(b):
    x, y = struct.unpack('<dd', b[5:21])
    return x, y

xy = df['geo_point_2d'].apply(decode_xy)
df['xlon'] = xy.apply(lambda t: t[0])
df['ylat'] = xy.apply(lambda t: t[1])

type_map = {'Vélos': 0, "Vélib'": 1, 'Vélo-cargo': 2}
df['type'] = df['regpar'].map(type_map)
df['loc'] = df['locsta'].fillna('Autre')

locs = sorted(df['loc'].unique().tolist())
loc_idx = {l: i for i, l in enumerate(locs)}

rows = []
for r in df.itertuples(index=False):
    rows.append([
        int(r.type),
        int(r.placal),
        int(r.plarel),
        loc_idx[r.loc],
        round(r.xlon, 5),
        round(r.ylat, 5),
    ])

data = {
    'locs': locs,
    'rows': rows,
    'meta': {
        'source': "Ville de Paris — open data (stationnement-voie-publique-emplacements)",
        'note': "Places calculées (placal) et relevées (plarel) issues du relevé officiel de voirie. Paris intra-muros uniquement.",
    }
}

out_path = '/Users/thomasvroylandt/Documents/places_velos/scratchpad/data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

import os
print('rows', len(rows), 'locs', len(locs))
print('placal total', df['placal'].sum(), 'plarel total', df['plarel'].sum())
print('file size', os.path.getsize(out_path))
lons = [r[4] for r in rows]
lats = [r[5] for r in rows]
print('bbox', min(lons), max(lons), min(lats), max(lats))
