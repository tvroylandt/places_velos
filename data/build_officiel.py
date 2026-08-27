"""Génère data/data_officiel.json à partir du relevé de voirie de la Ville de Paris.

Source : stationnement-voie-publique-emplacements.parquet (open data Ville de Paris).
Sortie : lignes [type(0=velo,1=velib,2=cargo), places, locIdx, lon, lat] + vocabulaire des
localisations, compacts pour être embarqués tels quels dans index.html.
"""
import json
import struct

import pandas as pd

SRC = '/Users/thomasvroylandt/Documents/places_velos/stationnement-voie-publique-emplacements.parquet'
OUT = '/Users/thomasvroylandt/Documents/places_velos/data/data_officiel.json'


def decode_xy(b):
    x, y = struct.unpack('<dd', b[5:21])
    return x, y


def main():
    df = pd.read_parquet(SRC)
    xy = df['geo_point_2d'].apply(decode_xy)
    df['xlon'] = xy.apply(lambda t: t[0])
    df['ylat'] = xy.apply(lambda t: t[1])

    type_map = {'Vélos': 0, "Vélib'": 1, 'Vélo-cargo': 2}
    df['type'] = df['regpar'].map(type_map)
    df['loc'] = df['locsta'].fillna('Autre')

    locs = sorted(df['loc'].unique().tolist())
    loc_idx = {l: i for i, l in enumerate(locs)}

    rows = [
        [int(r.type), int(r.placal), loc_idx[r.loc], round(r.xlon, 5), round(r.ylat, 5)]
        for r in df.itertuples(index=False)
    ]

    data = {
        'locs': locs,
        'rows': rows,
        'meta': {
            'source': "Ville de Paris — open data (stationnement-voie-publique-emplacements)",
            'note': "Places calculées (placal) issues du relevé officiel de voirie. Paris intra-muros uniquement.",
        },
    }
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print('rows', len(rows), 'locs', len(locs), 'places total', df['placal'].sum())


if __name__ == '__main__':
    main()
