# Places Vélo Paris

Outil web statique pour explorer les emplacements de stationnement vélo à Paris (et
Seine-Saint-Denis pour la source OpenStreetMap) : filtrez par type de place et par
localisation, tracez une zone au lasso sur la carte, et obtenez en direct la somme des
places par type (vélos / Vélib' / vélos-cargos).

**→ Ouvrir [`index.html`](index.html) dans un navigateur.** Aucun serveur applicatif
n'est nécessaire : c'est une page HTML autonome (données embarquées), qui charge juste
le fond de carte OpenStreetMap et la librairie Leaflet via CDN — une connexion internet
est donc requise pour afficher la carte.

## Sources de données

Deux jeux de données, sélectionnables via le bouton en haut de la page :

- **Ville de Paris** — relevé officiel de voirie
  (`stationnement-voie-publique-emplacements.parquet`, open data Ville de Paris).
  Paris intra-muros uniquement. Le nombre de places vient de la colonne `placal`
  (places calculées).
- **OpenStreetMap** — récupéré via l'API Overpass (`amenity=bicycle_parking`,
  `amenity=bicycle_rental` filtré sur le réseau Vélib' Métropole, et
  `cargo_bike=yes|designated` pour les vélos-cargos), sur Paris + Seine-Saint-Denis. Le
  nombre de places vient du tag `capacity=*` (valeur par défaut estimée quand absent).

## Régénérer les données

```bash
python3 data/build_officiel.py   # relit le .parquet -> data/data_officiel.json
python3 data/build_osm.py        # interroge Overpass -> data/data_osm.json
```

Puis reconstruire `index.html` à partir du gabarit et des deux JSON :

```bash
python3 -c "
tpl = open('data/template.html', encoding='utf-8').read()
data = open('data/data_officiel.json', encoding='utf-8').read()
data_osm = open('data/data_osm.json', encoding='utf-8').read()
out = tpl.replace('__DATA_JSON__', data).replace('__DATA_JSON_OSM__', data_osm)
open('index.html', 'w', encoding='utf-8').write(out)
"
```

## Structure

- `index.html` — l'outil, prêt à être servi tel quel (ex. GitHub Pages).
- `data/build_officiel.py`, `data/build_osm.py` — génèrent les JSON compacts embarqués.
- `data/template.html` — gabarit HTML avec les emplacements `__DATA_JSON__` /
  `__DATA_JSON_OSM__` à substituer.
- `stationnement-voie-publique-emplacements.parquet` — source brute Ville de Paris.
