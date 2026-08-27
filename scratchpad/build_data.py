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

type_map = {'Vélos': 'velo', "Vélib'": 'velib', 'Vélo-cargo': 'cargo'}
df['type'] = df['regpar'].map(type_map)

df['rue'] = (df['typevoie'].fillna('').str.strip() + ' ' + df['nomvoie'].fillna('').str.strip()).str.strip()
df['rue'] = df['rue'].str.replace(r'\s+', ' ', regex=True)

df['loc'] = df['locsta'].fillna('Autre')
df['zone'] = df['zoneres'].fillna('')

# dictionaries for repeated strings
rues = sorted(df['rue'].unique().tolist())
rue_idx = {r: i for i, r in enumerate(rues)}

locs = sorted(df['loc'].unique().tolist())
loc_idx = {l: i for i, l in enumerate(locs)}

zones = sorted(df['zone'].unique().tolist())
zone_idx = {z: i for i, z in enumerate(zones)}

type_codes = {'velo': 0, 'velib': 1, 'cargo': 2}

rows = []
for r in df.itertuples(index=False):
    rows.append([
        int(r.arrond),
        rue_idx[r.rue],
        type_codes[r.type],
        int(r.placal),
        int(r.plarel),
        loc_idx[r.loc],
        zone_idx[r.zone],
        round(r.xlon, 5),
        round(r.ylat, 5),
    ])

data = {
    'rues': rues,
    'locs': locs,
    'zones': zones,
    'arronds': sorted(df['arrond'].unique().tolist()),
    'rows': rows,  # [arrond, rue_idx, type_code(0=velo,1=velib,2=cargo), placal, plarel, loc_idx, zone_idx, lon, lat]
}

out_path = '/Users/thomasvroylandt/Documents/places_velos/scratchpad/data.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

import os
print('rows:', len(rows))
print('rues:', len(rues), 'locs:', len(locs), 'zones:', len(zones))
print('placal total:', df['placal'].sum(), 'plarel total:', df['plarel'].sum())
print('file size bytes:', os.path.getsize(out_path))
