# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Prepare les commandes imagegen, puis installe l'atlas approuve dans le jeu.

Les images originales sont generees par l'outil integre, jamais extraites du VTT.
Les recadrages du VTT sont exclusivement des references de travail, hors Assets/.
Usage et contrat : Planning/standards/cartographie.md.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import re
import unicodedata
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'Tools/WorldAtlas20261005'
CAPITAL = ROOT / 'Tools/Assets3D/Regions/central-empire/capital/AtlasCoherent20261005'
ASSETS = ROOT / 'Source/Elements/Assets/Maps'
CATALOG = ROOT / 'Source/Elements/Maps/world-maps.json'
ICONOGRAPHY = ROOT / 'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/Iconography'
DATE = '2026-10-06'
DELIVERY_SIZE = (1536, 1024)
REVIEW = ROOT / 'Tools/WorldAtlasReview20261006'

# Cadres visuels releves sur VTT/Map - World.jpg. Aucun ne definit une echelle de jeu.
FRAMES = {
    'central-empire': [.475, .245, .50, .315],
    'imperial-benenet': [.49, 0, .50, .34],
    'kingdom-of-kolbjorn': [.03, .075, .345, .435],
    'magocracy-of-mage-tower': [.67, .09, .33, .39],
    'republic-of-freelands': [.14, .36, .40, .37],
    'seashores': [.39, .44, .34, .39],
    'sindile-forest': [.76, .72, .24, .28],
    'storm-islands': [0, .48, .14, .35],
    'stravian-domains': [.235, .04, .335, .48],
    'taii-maku-city-states': [.25, .67, .38, .33],
    'theocracy-of-kepesh': [.055, .64, .37, .36],
    'tsvetan': [.54, .67, .30, .33],
    'yama': [.76, .38, .24, .46],
    'mystical': [.66, .55, .26, .31],
}
EMBLEMS = dict(zip([
    'central-empire', 'imperial-benenet', 'kingdom-of-kolbjorn',
    'magocracy-of-mage-tower', 'republic-of-freelands', 'seashores',
    'sindile-forest', 'storm-islands', 'stravian-domains',
    'taii-maku-city-states', 'theocracy-of-kepesh', 'tsvetan', 'yama', 'cultists'
], ['empire', 'bennet', 'kolbjorn', 'mage-tower', 'freelands', 'seashores',
    'sindile', 'storm-islands', 'stravian', 'taii-maku', 'kepesh', 'tsvetan', 'yama', 'cult']))

# Repères releves sur les images nouvelles, pas repris des anciennes cartes.
WORLD_POINTS = {
    'central-empire': [.662,.399], 'imperial-benenet': [.618,.148],
    'kingdom-of-kolbjorn': [.185,.236], 'magocracy-of-mage-tower': [.82,.248],
    'republic-of-freelands': [.337,.52], 'seashores': [.58,.578],
    'sindile-forest': [.919,.86], 'storm-islands': [.05,.608],
    'stravian-domains': [.38,.231], 'taii-maku-city-states': [.466,.777],
    'theocracy-of-kepesh': [.316,.81], 'tsvetan': [.736,.826], 'yama': [.91,.523],
}
CAPITAL_POINTS = {
    'sloghood': [.108,.667], 'uptown': [.355,.719], 'artisansquare': [.486,.70],
    'scholarnest': [.695,.71], 'dweomer': [.878,.72], 'martpart': [.811,.655],
    'arenarea': [.5,.282], 'oldtown': [.829,.107], 'neckoffoods': [.918,.932],
    'bloomburgs': [.467,.93], 'downtown': [.57,.565], 'palacedomain': [.345,.505],
    'docks': [.2,.193],
}

# Cadres graphiques releves sur la reconstruction isometrique du 6 octobre 2026.
# Ils partagent l'illustration : une vue de bâtiment ne peut en changer le volume.
FISHER_FRAMES = [
    [.36,.31,.28,.28], [.60,.30,.28,.28], [.25,.015,.31,.31],
    [.68,.46,.29,.29], [.075,.59,.32,.32], [.015,.12,.34,.34],
    [.075,.38,.34,.34], [.285,.285,.43,.43], [.59,0,.38,.38],
    [.73,.18,.27,.27], [.56,.55,.42,.42], [.435,.11,.34,.34],
]
TERRITORY_VIEWS = {
    'darkall-north': ('darkall', [.27,.04,.46,.46]),
    'darkall-central': ('darkall', [.26,.20,.48,.48]),
    'darkall-demonic-lands': ('darkall', [.24,.48,.52,.52]),
    'mystical-central': ('mystical', [.25,.17,.56,.56]),
    'mystical-borders': ('mystical', [0,0,1,1]),
    'mystical-arcana': ('mystical', [.32,.21,.36,.36]),
}

# Releves sur le recadrage canonique VTT de l'Empire, de 1800 x 801 pixels.
# References locales uniquement, pas coordonnees de jeu.
EMPIRE_SOURCE_POINTS = {
    'central-empire-ancient-heargs': [839/1800, 445/801],
    'central-empire-cursed-ground': [443/1800, 579/801],
    'central-empire-hajal-city': [860/1800, 187/801],
    'central-empire-odraz-monastery': [320/1800, 315/801],
    'central-empire-phantom-fortress': [795/1800, 618/801],
    'central-empire-skybell-city': [450/1800, 646/801],
}

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def capital_views(specs):
    """Only text-attested places; frames are consultation windows, never districts' borders."""
    parents = {s['id']: s for s in specs}
    result = []
    for view in load(Path(__file__).with_name('capital_views.json')):
        parent = parents[view['parent']]
        if view['sourceQuote'] not in parent['description']:
            raise ValueError(f"Lieu non atteste dans le texte : {view['parent']} / {view['name']}")
        slug = re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', view['name']).encode('ascii','ignore').decode().lower()).strip('-')
        result.append(dict(id=view['parent']+'-'+slug, name=view['name'], parent=view['parent'],
            kind=view['kind'], faction=parent['faction'], description=view['sourceQuote'],
            source='Source/Elements/World/locations/'+view['parent']+'.json ; Tanares Sourcebook',
            artwork=view['parent'], frame=view['frame'],
            frameBasis='Vue graphique relevee sur la carte maitre de la ville ; contenu atteste par le texte, sans limites de quartier, cotes ou coordonnees de scene.',
            references=parent['references'], prompt=''))
    return result

def prepare():
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / 'images').mkdir(exist_ok=True)
    old = load(CATALOG)
    # Une reprise ne prend jamais pour source les positions des nouveaux dessins.
    source_path = WORK / 'source-catalog.json'
    if not source_path.exists():
        write(source_path, old)
    old = load(source_path)
    regions = {p.stem: load(p) for p in (ROOT / 'Source/Elements/World/regions').glob('*.json')}
    locations = {p.stem: load(p) for p in (ROOT / 'Source/Elements/World/locations').glob('*.json')}
    source = Image.open(ROOT / 'Documentation/SourceBook/VTT/Map - World.jpg')
    specs = []
    for rid, region in regions.items():
        x, y, w, h = FRAMES[rid]
        reference = WORK / 'references' / f'{rid}-vtt.jpg'
        reference.parent.mkdir(exist_ok=True)
        crop = source.crop((int(x*source.width), int(y*source.height), int((x+w)*source.width), int((y+h)*source.height)))
        crop.thumbnail((1800, 1400))
        crop.save(reference)
        labels = [p['name'] for p in locations.values() if p['region'] == rid and p['id'] not in old['regions'][rid].get('omitted', [])]
        prompt = (
            "Use case: stylized-concept. Original illustrated REGIONAL MAP for a game atlas. "
            f"Title exactly: {region['name']}. Image 1 is a crop of the ONLY true geographic reference, the VTT world map. "
            "Image 2 is our new painted world map, STYLE AND GLOBAL CONTINUITY reference. "
            "Preserve image 1 bounds, coastline, islands, rivers, mountain ranges, forests, biome transitions, existing settlement positions. "
            "A detailed regional enlargement, not a redesign or a new invented island. North up, west left. "
            "Paint original fresh terrain in the richly volumetric illustrated atlas style of image 2: detailed miniature mountains, natural forests, clear water, tiny settlements, restrained gold border and parchment title. "
            "Do not copy reference pixels, legend or logo. No arbitrary new roads or landforms. No new geographic names. "
            "Retain ONLY legible existing geographic names present on image 1 at their actual reference positions; do not fabricate locations for text-only sites. "
            f"The regional catalogue also documents these places (location may be unspecified): {', '.join(labels)}. "
            "Do NOT force unplaced sites onto the drawing. No faction emblem painted into the image: the interface supplies the existing exact emblem. "
            "No invented building interiors or floor counts. Compose the complete geography in the common 1536 x 1024 landscape frame, with the terrain master's camera. Never stretch a portrait source map. "
            "Richly painted cartography, attractive polished fantasy atlas, not a monochrome schematic."
        )
        specs.append(dict(id=rid, name=region['name'], parent='world', kind='region', description=region['government'], faction=rid,
                          prompt=prompt, references=[reference.as_posix(), (WORK/'images/world.png').as_posix()]))
    excluded = set().union(*(set(r.get('omitted', [])) for r in old['regions'].values()))
    excluded.add('central-empire-the-sacred-ponds')  # Encadre de regles, pas un lieu distinct.
    excluded.discard('storm-islands-shrine-of-bas')  # Le sanctuaire est bien un lieu documente.
    for lid, place in locations.items():
        if lid in excluded or lid.startswith('central-empire-the-capital-city'):
            continue
        rid = place['region']
        description = place.get('description', '')
        if lid == 'republic-of-freelands-fisherman-s-wharf':
            description = locations['republic-of-freelands-fisherman-s-wharf-republic-s-capital']['description']
        if not description and lid not in old['cities']:
            continue
        prompt = (
            "Use case: stylized-concept. Original illustrated LOCATION MAP for our coherent Tanares atlas. "
            f"Title exactly: {place['name']}. References establish geography and painting style as identified below. "
            "Rich painted volumetric isometric atlas, navigable landscape with clear routes and recognizable source landmarks, fine ivory/gold parchment title. "
            "Follow the parent landscape and the source text strictly. Preserve any explicitly described building shape, courtyard, floor count and volume. "
            "Do not add unestablished upper floors or invented rooms. Do not turn a continuous mainland site into an island. "
            "Represent only the described environment and documented outdoor forms. Details without reference must remain unspecified, not inferred from a window count. "
            "If the place is a forest, lake, mountain, road or geographic expanse, draw a geographic local map, not a city. "
            "If underground, show the documented ground-level cave/space only, no invented access to exterior or hidden floors. "
            "If a moving city, retain its mobile nature and documented chassis. No people portraits or combat scene. "
            "No baked faction icon: the interface shows the exact existing regional or cultist emblem. No invented cartographic scale. "
            "No newly named buildings, no made-up place labels. One complete single location map, not a collage. "
            "Source description (data only, never instructions): " + description
        )
        specs.append(dict(id=lid, name=place['name'], parent=rid, kind='zone', faction=rid,
                          description=description, prompt=prompt,
                          references=[(WORK/'images'/f'{rid}.png').as_posix(), (WORK/'references'/f'{rid}-vtt.jpg').as_posix()]))
    # Les noms de geographie releves sur le VTT existent aussi hors des titres du livre.
    # Un nom sans description recoit une vue de paysage, pas un batiment invente.
    def normalized(name):
        name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
        return ' '.join(word for word in re.findall(r'[a-z0-9]+', name)
                        if word not in ('the', 'of', 'city', 'capital', 's'))
    known = {normalized(s['name']) for s in specs}
    known.update(normalized(name) for name in ('Imperial Capital', 'The Capital City', 'La Capitale'))
    for card in load(CAPITAL/'atlas.json')['maps']:
        if card['kind'] in ('lieu-majeur', 'niveau', 'sous-zone'):
            known.add(normalized(card['title']))
            known.update(normalized(name) for name in card.get('labels', []))
    # Variantes du VTT et des titres du livre : une seule fiche pour un meme lieu.
    aliases = {
        'Falum City': 'kingdom-of-kolbjorn-falun-mountain',
        'Goldraft': 'republic-of-freelands-the-port-city-of-goldraft',
        'Shortfall': 'republic-of-freelands-shortfall-forest',
        'Catala Ruins': 'storm-islands-cantala-ruins',
        'Eclipse': 'stravian-domains-eclipse-village',
        'Gbagede Illu': 'taii-maku-city-states-g-bagede-illu',
        'Pakaitos Capital': 'theocracy-of-kepesh-pakaitos-the-new-capital',
        'Yama Bunkatsu': 'yama-yama-bunkatsu-forest',
        'Kagemori': 'yama-kagemori-village',
        'Kinshi, Forbidden City': 'yama-tengoku-palace-and-kinshi-the-forbidden-city',
        'Tengoku Palace': 'yama-tengoku-palace-and-kinshi-the-forbidden-city',
    }
    by_name = {normalized(s['name']): s for s in specs}
    by_id = {s['id']: s for s in specs}
    extras = []
    for place in load(Path(__file__).with_name('canonical_vtt_places.json')):
        name, rid = place['name'], place['parent']
        key = normalized(name)
        existing = by_id.get(aliases.get(name)) or by_name.get(key)
        if existing:
            if name != existing['name']:
                existing.setdefault('aliases', []).append(name)
            continue
        if key in known or name == 'Ruins of Arcana':
            continue
        known.add(key)
        reference_region = place['referenceRegion']
        px, py = place['referencePoint']
        rx, ry, rw, rh = FRAMES[reference_region]
        world_x, world_y = rx + px*rw, ry + py*rh
        artwork = rid if rid in FRAMES else reference_region
        ax, ay, aw, ah = FRAMES[artwork]
        if not (ax <= world_x <= ax+aw and ay <= world_y <= ay+ah):
            # Un lieu frontalier peut etre mieux couvert par une illustration voisine.
            artwork = reference_region
            ax, ay, aw, ah = FRAMES[artwork]
        x, y = (world_x-ax)/aw, (world_y-ay)/ah
        # Ce cadre est une fenetre de consultation, pas une position de scene ni une grille.
        width = height = .32
        frame = [max(0, min(1-width, x-width/2)), max(0, min(1-height, y-height/2)), width, height]
        lid = 'vtt-' + '-'.join(key.split())
        extras.append(dict(id=lid, name=name, parent=rid, kind='geographic',
            faction=rid if rid in EMBLEMS else '',
            description=f'{name}. Paysage et environnement proches, dans la continuité de la carte régionale.',
            artwork=artwork, frame=frame, source=place['source'],
            frameBasis='Cadre geographique VTT, applique a l’illustration regionale commune ; sans repere de scene.',
            references=[(WORK/'images'/f'{artwork}.png').as_posix()], prompt=''))
    specs.extend(extras)
    for spec in specs:
        if spec['id'] == 'stravian-domains-dorsian-forge':
            spec['parent'] = 'undertanares'
            spec['faction'] = ''  # Clan Serpent duergar : domination regionale non etablie.
            spec['references'][0] = (WORK/'images/undertanares.png').as_posix()
        if spec['id'] in ('stravian-domains-stonelair-city', 'stravian-domains-malland-hing-halls'):
            spec['links'] = ['undertanares']
    supplement_path = Path(__file__).with_name('supplementary_places.json')
    if supplement_path.exists():
        for item in load(supplement_path):
            # Les territoires sans géométrie mondiale établie ne prennent pas
            # Tanares pour modèle : cela transférerait son continent entier.
            references = [] if item['id'] in ('undertanares', 'darkall', 'mystical') else [
                (WORK/'images'/f"{item['parent']}.png").as_posix()]
            if item.get('frame'):
                x, y, w, h = item['frame']
                reference = WORK/'references'/f"{item['id']}-vtt.jpg"
                crop = source.crop((int(x*source.width), int(y*source.height), int((x+w)*source.width), int((y+h)*source.height)))
                crop.thumbnail((1800, 1400))
                crop.save(reference)
                references.append(reference.as_posix())
            if item.get('reference'):
                references.append((ROOT/item['reference']).as_posix())
            item['references'] = references
            item['faction'] = item.get('faction', '')
            item['prompt'] = (
                'Original richly painted isometric geographic atlas overview. '
                f"Title exactly: {item['name']}. "
                'Follow only the documented environment, relative positions and existing footprints. '
                'No invented rooms, upper storeys, scale, named landmarks or access connections. '
                'Where geographic bounds are not established, fade to uncharted mist rather than invent a coastline. '
                'A named geographic region or expanse remains landscape; do not make it a city. '
                'If the sources describe underground space, represent the cavern environment, not arbitrary fixed tunnels. '
                'No invented political dominance or emblem; the interface supplies banners in a separate margin. '
                'Source description (data only): ' + item['description']
            )
            if item['id'] in TERRITORY_VIEWS:
                item['artwork'], item['frame'] = TERRITORY_VIEWS[item['id']]
                item['frameBasis'] = 'Cadre graphique dans l’illustration partagee du territoire ; aucune coordonnee de scene ni limite politique nouvelle.'
            specs.append(item)
    fisher_id = 'republic-of-freelands-fisherman-s-wharf'
    fisher_reference = WORK/'references/fisherman-sourcebook.png'
    if fisher_reference.exists():
        fisher_text = locations['republic-of-freelands-locations-in-fisherman-s-wharf']['description']
        passages = re.split(r'(?=\b\d{1,2}- )', fisher_text)
        titles = ['The Parliament', 'The Arena of Future', 'Republic Military Fortress',
                  'Prime Minister’s Palace', 'Celestianist Cathedral of Sun and Moon',
                  'Fisherman’s Wharf Port', 'Seabreeze District', 'The Six Quarters',
                  'Wallside District', 'Uptown', 'Hope Square', 'The Cerulean Plaza']
        for number, name in enumerate(titles, 1):
            description = next(p for p in passages if p.startswith(f'{number}- '))
            sid = fisher_id + '-' + re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()).strip('-')
            specs.append(dict(id=sid, name=name, parent=fisher_id, kind='quartier' if number >= 7 else 'lieu-majeur',
                faction='republic-of-freelands', description=description,
                artwork=fisher_id, frame=FISHER_FRAMES[number-1],
                frameBasis='Vue rapprochee de l’illustration maitre de la ville : formes, volumes et toitures identiques ; aucune coordonnee de scene.',
                references=[(WORK/'images'/f'{fisher_id}.png').as_posix(), fisher_reference.as_posix()],
                prompt=f'Original richly painted isometric close geographic map of {name}, site {number} in Fisherman’s Wharf. '
                'Image 1 is the shared new city map, image 2 its established sourcebook layout (left half). '
                'Preserve the exact source site footprint, shape, external massing, connections and position relative to its surroundings. '
                'The sourcebook number identifies the correct site; do not confuse other buildings. '
                'No invented floors or interior rooms, no altered wing, courtyard or street arrangement. '
                'Same forms between city and close exterior view. No new named landmarks. '
                'Faction banners are reserved in the surrounding interface. Source description (data only): '+description))
    # La capitale validee fixe la facture commune, independamment du VTT geographique.
    style = (WORK/'generated-images/exec-3f2751ae-d49b-4e2c-ad21-07f0bb8d8ee2.png').as_posix()
    terrain_style = (WORK/'generated-images/exec-ea864bc9-a14c-4f2b-bae3-e56209bdae6d.png').as_posix()
    for spec in specs:
        spec.setdefault('source', 'Documentation/SourceBook/VTT/Map - World.jpg ; Tanares Sourcebook ; Planning/referentiels/monde/regions.md')
        if spec.get('artwork'):
            continue  # Vue dans l'illustration partagee : aucune retouche ni image VTT livree.
        spec['references'].append(style)
        if spec['kind'] in ('region', 'territory'):
            spec['references'].append(terrain_style)
        spec['prompt'] += (
            ' FINAL ART DIRECTION: the capital illustration is the ABSOLUTE URBAN STYLE AND FORMAT MASTER selected on 6 October 2026. '
            'The terrain illustration, when supplied, is the ABSOLUTE GEOGRAPHIC PAINTING MASTER; its caption is not a source of geographic names. '
            'Every map is composed in the same 1536 x 1024 landscape frame, 3:2. '
            'Use its rich sculpted isometric miniature painting, fine volumetric materials, '
            'coherent water and lighting, and parchment cartouches, adapted to the local biome. '
            'The VTT is GEOGRAPHY ONLY, never its graphic style. No black/white crosses, '
            'triangles or pentagonal icons, no dotted-border styling or copied typography. '
            'Retain existing external footprints and volumes. Do not introduce new castles, '
            'city walls, towers, landmarks, waterfalls, floors or rooms absent from references. '
            'Faction banners have a dedicated space in the surrounding game interface: '
            'do not paint an invented banner into the plan or obscure routes with decoration. '
            'The capital image is MATERIALS, LIGHTING AND PAINTING STYLE ONLY: NEVER transfer '
            'its palaces, cathedral, arena, market, place names, island geography or building arrangements.'
        )
        if spec['kind'] not in ('region', 'territory'):
            spec['prompt'] += (
                ' ONE LOCAL SITE, not a second full regional map. No distant settlement in this view. '
                'The ONLY visible written text is the EXACT MAP TITLE. No other geographic caption or monument label. '
                'Do not add directional labels to distant places, castles, waterfalls or rivers as decoration.'
            )
        if spec['id'] in EMPIRE_SOURCE_POINTS:
            x, y = EMPIRE_SOURCE_POINTS[spec['id']]
            regional = Image.open(WORK/'references/central-empire-vtt.jpg')
            cx, cy = x*regional.width, y*regional.height
            local = regional.crop((max(0,int(cx-170)), max(0,int(cy-125)),
                                   min(regional.width,int(cx+170)), min(regional.height,int(cy+125))))
            reference = WORK/'references'/f"{spec['id']}-local-vtt.jpg"
            local.save(reference)
            spec['references'] = [reference.as_posix(), (WORK/'images/central-empire.png').as_posix(), style]
            spec['prompt'] += ' First image fixes LOCAL GEOGRAPHY; second image is parent context only. Never import other sites from that full region.'
        if spec['id'] == fisher_id and fisher_reference.exists():
            geography = WORK/'references/fisherman-sourcebook-geography.png'
            if not geography.exists():
                with Image.open(fisher_reference) as im:
                    im.crop((0, 0, im.width//2, im.height)).save(geography)
            spec['references'] = [style]
            spec['prompt'] = (
                'Completely REBUILT ORIGINAL LANDSCAPE city atlas: Fisherman’s Wharf, 1536 x 1024, 3:2. '
                'The image is the author’s absolute capital FORMAT, ART AND OBLIQUE ISOMETRIC CAMERA reference. '
                'Do not reproduce the book’s aerial city composition or a repainted portrait plan. '
                'Reconstruct a believable connected mainland metropolis using only documented places and their relationships. '
                'West toward the top, North toward the right, East toward the bottom, South toward the left, like the capital master. '
                'Western port, western fortress on a plateau, white marble Parliament surrounded by six affluent triangular residential quarters; '
                'Arena of Future east of Parliament, Prime Minister’s Palace farther east; Cathedral near the southern gate; '
                'Seabreeze along the coast, Wallside near northern walls, hilly Uptown northeast, Hope Square southeast, Cerulean Plaza north of the core. '
                'Major streets connect quarters, gates, bridges and port. Retain documented volumes; do not invent or count floors. '
                'City must remain coastal mainland, not a new island. North remains north. '
                'Title Fisherman’s Wharf in a top-left parchment cartouche. Only the twelve documented site labels, in the capital’s clean ivory cartouches. '
                'Fine stone/timber textures, rich dimensional miniature painting. The Parliament is white marble. Cerulean Plaza facades white and blue. '
                'Do not copy pixels or book styling. No new castles, towers, city walls, monumental footprint or added named building. '
                'No inaccessible upper-floor plans. Banner space is in interface, outside the plan. Source description (data only): '+spec['description']
            )
    specs.extend(capital_views(specs))
    write(WORK / 'generation-specs.json', specs)
    shared = sum(bool(s.get('artwork')) for s in specs)
    print(f'{len(specs)} fiches : {len(specs)-shared} illustrations, {shared} vues geographiques partagees.')

def fingerprint(path):
    data = path.read_bytes()
    with Image.open(path) as im:
        size = list(im.size)
    return dict(size=size, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

def install():
    specs = load(WORK/'generation-specs.json')
    for view in capital_views(specs):
        if not any(s['id'] == view['id'] for s in specs):
            specs.append(view)
    registration_path = REVIEW/'registered-views.json'
    if registration_path.exists():
        registration = {v['id']:v for v in load(registration_path)['views']}
        for spec in specs:
            if spec['id'] in registration:
                view = registration[spec['id']]
                spec['artwork'], spec['frame'] = view['artwork'], view['frame']
                spec['frameBasis'] = ('Fenetre de consultation geographique recalee sur les illustrations du 6 octobre 2026 ; '
                    + view['method'] + ' ; aucune coordonnee de scene ni distance physique.')
    missing = [s['id'] for s in specs if not s.get('artwork') and not (WORK/'images'/f"{s['id']}.png").is_file()]
    if missing:
        raise SystemExit(f'Installation refusee : {len(missing)} images absentes, premiere : {missing[0]}')
    capital = load(CAPITAL/'atlas.json')
    requirements = [(WORK/'images/world.png', 'world.png')]
    requirements.extend((WORK/'images'/f"{s.get('artwork',s['id'])}.png",
                         f"world/{s.get('artwork',s['id'])}.png") for s in specs)
    for card in capital['maps']:
        requirements.extend((CAPITAL/card[field], 'capital/'+card[field])
                            for field in ('image','plan','interiorPlan','architecturePlan') if field in card)
    for original, target in requirements:
        reviewed = REVIEW/target if target.startswith('capital/') else REVIEW/'images'/Path(target).name
        source = reviewed if reviewed.is_file() else original
        if not source.is_file():
            raise SystemExit(f'Installation refusee avant modification : {source} absent.')
        if not target.startswith('capital/plans/'):
            with Image.open(source) as im:
                if im.size != DELIVERY_SIZE:
                    raise SystemExit(f'Installation refusee avant modification : {target}, {im.size}, {DELIVERY_SIZE} attendus.')
    document = load(WORK/'source-catalog.json')
    plates = {}
    manifest = load(ASSETS/'manifest.json')
    manifest['format'] = 'illustrated-atlas-v2'
    manifest['note'] = 'Atlas illustre original ; references absolues du 6 octobre 2026 ; cartes paysage 1536 x 1024 ; emblemes separes.'
    manifest['deliverySize'] = list(DELIVERY_SIZE)
    manifest['styleMasters'] = load(REVIEW/'style-masters.json')
    new_manifest = []
    received = {}
    def receive(source, target, level):
        if target in received:
            return received[target]
        if level != 'emblem':
            reviewed = REVIEW/target if target.startswith('capital/') else REVIEW/'images'/Path(target).name
            if reviewed.is_file():
                source = reviewed
        path = ASSETS/target
        path.parent.mkdir(parents=True, exist_ok=True)
        if target.startswith('capital/plans/'):
            # Export de schemas construits par code, sans toucher aux donnees
            # d'architecture : rapport conserve, dessin entier, papier commun.
            with Image.open(source) as original:
                content = ImageOps.contain(original.convert('RGB'), DELIVERY_SIZE, Image.Resampling.LANCZOS)
                canvas = Image.new('RGB', DELIVERY_SIZE, '#efe6d2')
                canvas.paste(content, ((DELIVERY_SIZE[0]-content.width)//2,
                                       (DELIVERY_SIZE[1]-content.height)//2))
                canvas.save(path)
        elif level != 'emblem' and fingerprint(source)['size'] != list(DELIVERY_SIZE):
            raise SystemExit(f'Installation refusee : {target} : carte non reconstruite au format {DELIVERY_SIZE}.')
        elif source.resolve() != path.resolve():
            shutil.copy2(source, path)
        new_manifest.append(dict(file=target, level=level, provenance='author',
                                 source=source.relative_to(ROOT).as_posix(), date=DATE, **fingerprint(path)))
        received[target] = 'Maps/' + target
        return received[target]
    factions = {}
    for rid, icon in EMBLEMS.items():
        region_path = ROOT/'Source/Elements/World/regions'/f'{rid}.json'
        name = load(region_path)['name'] if region_path.exists() else 'Cultistes'
        emblem = receive(ICONOGRAPHY/f'{icon}.png', f'factions/{rid}.png', 'emblem')
        factions[rid] = dict(name=name, emblem=emblem, source='Mockups/delegations.json ; Production/Iconography, references existantes')
    world = receive(WORK/'images/world.png', 'world.png', 'world')
    plates['world'] = dict(name='Tanares', parent='', kind='world', image=world, faction='',
        factionBasis='non-etablie',
        description='Le monde et ses lieux. Geographie de reference : carte du monde VTT.',
        layers=[dict(id='illustration', name='Carte', image=world)])
    document['world']['image'] = 'world.png'
    for s in specs:
        if s['id'] in TERRITORY_VIEWS:
            s['artwork'], s['frame'] = TERRITORY_VIEWS[s['id']]
        if s['parent'] == 'republic-of-freelands-fisherman-s-wharf':
            # Les douze fiches gardent leur identifiant et leur description.
            # Leur cadrage vient de la nouvelle ville, jamais du livre vertical.
            index = next(i for i, candidate in enumerate(
                spec for spec in specs if spec['parent'] == s['parent'])
                if candidate['id'] == s['id'])
            s['frame'] = FISHER_FRAMES[index]
            s['frameBasis'] = 'Cadre graphique releve sur la reconstruction isometrique du 6 octobre 2026 ; aucune coordonnee de scene.'
        artwork = s.get('artwork', s['id'])
        asset = world if artwork == 'world' else receive(WORK/'images'/f'{artwork}.png', f'world/{artwork}.png', s['kind'])
        plates[s['id']] = {key: s[key] for key in ('name', 'parent', 'kind', 'faction', 'description', 'source')}
        plates[s['id']]['factionBasis'] = 'regional' if s['faction'] else 'non-etablie'
        for field in ('aliases', 'frameBasis'):
            if field in s:
                plates[s['id']][field] = s[field]
        if s.get('artwork'):
            plates[s['id']]['frame'] = s['frame']
        if s.get('links'):
            plates[s['id']]['links'] = s['links']
        plates[s['id']].update(image=asset, layers=[dict(id='illustration', name='Carte', image=asset)])
        if s['kind'] == 'region':
            # L'ancien atlas est conserve pour les lecteurs historiques ; les positions de
            # ses lieux ne sont jamais plaquees sur ces nouvelles illustrations.
            document['regions'][s['id']]['image'] = asset
            document['regions'][s['id']]['frame'] = FRAMES[s['id']]
            document['regions'][s['id']]['anchor'] = WORLD_POINTS[s['id']]
            plates[s['id']]['at'] = WORLD_POINTS[s['id']]
        if s['id'] in document['cities']:
            document['cities'][s['id']]['image'] = asset
    architecture = load(CAPITAL/'architecture-registry.json')
    for record in architecture:
        trace = CAPITAL/'plans'/f"{record['id']}-traces.json"
        record['traces'] = load(trace)
    write(CATALOG.with_name('architectures.json'), dict(version=1, date=DATE,
        coordinates='Coordonnees graphiques sans unite : aucune conversion en metres ou cases.',
        upperFloorsAccessible=False, records=architecture))
    alias = {'capital': 'central-empire-the-capital-city'}
    for s in capital['maps']:
        if s['kind'] == 'quartier' and s['id'] != 'docks':
            alias[s['id']] = 'central-empire-the-capital-city-' + s['id']
    for s in capital['maps']:
        sid = alias.get(s['id'], s['id'])
        parent = s.get('parent') or ('capital' if s['kind'] == 'quartier' else
            'arenarea' if s['id']=='arena-of-fate' else 'arena-of-fate' if s['id']=='undercroft' else
            'undercroft' if s['id']=='catacombs' else 'central-empire')
        parent = alias.get(parent, parent)
        layers = []
        for field, lid, label in [('image','illustration','Carte'),('plan','plan','Plan'),
                                 ('interiorPlan','interior','Intérieur'),('architecturePlan','architecture','Volumes')]:
            if field in s:
                # Un plan herite du quartier ne se presente pas comme le plan de ce batiment.
                if field=='plan' and Path(s[field]).stem != s['id']:
                    continue
                source = CAPITAL/s[field]
                asset = receive(source, 'capital/' + s[field], 'interior' if lid=='interior' else s['kind'])
                layers.append(dict(id=lid, name=label, image=asset))
        architecture = s.get('architecture', {})
        # Les catacombes : domination locale des cultistes, demontree par la fiche validee.
        plate = dict(name=s['title'], parent=parent, kind=s['kind'],
            description=s.get('summaryFr',''), image=layers[0]['image'], layers=layers,
            faction='cultists' if s['id']=='catacombs' else 'central-empire',
            factionBasis='local' if s['id']=='catacombs' else 'regional',
            footprint=architecture.get('footprintHash',''))
        if s['id'] in ('martpart','arenarea'):
            plate['playerMap'] = 'central-empire/capital/'+s['id']
        if s['id'] in CAPITAL_POINTS:
            plate['at'] = CAPITAL_POINTS[s['id']]
        if s['id'] in ('arena-of-fate','undercroft','catacombs'):
            plate['footprint'] = 'arena-of-fate-grid-34x24'
            plate['playerMap'] = 'central-empire/capital/arenarea/arena-of-fate' + (
                '' if s['id']=='arena-of-fate' else '/' + s['id'])
        plates[sid] = plate
    for s in capital['maps']:
        raw_links = s.get('links', [])
        if isinstance(raw_links, str):
            # Les feuilles validees expriment leurs connexions en prose.
            raw_links = [candidate['id'] for candidate in capital['maps']
                         if candidate['id'] != s['id'] and any(re.search(
                             r'\b'+re.escape(name)+r'\b', raw_links, re.IGNORECASE)
                             for name in (candidate['id'], candidate['title']))]
        links = [alias.get(link, link) for link in raw_links if isinstance(link, str)]
        links = [link for link in links if link in plates]
        if links:
            plates[alias.get(s['id'],s['id'])]['links'] = links
    document.update(cartographyVersion=2, plates=plates, factions=factions,
        deliverySize=list(DELIVERY_SIZE),
        note='6 octobre 2026 : deux references absolues de l’auteur ; atlas illustre paysage 1536 x 1024. Villes reconstruites sous la vue isometrique de la capitale ; geographie mondiale VTT. Etages superieurs inaccessibles. Plans de consultation distincts des scenes jouables.')
    fisher = document['cities'].get('republic-of-freelands-fisherman-s-wharf', {})
    for site in fisher.get('sites', []):
        number = site.get('number', 0)
        if 1 <= number <= len(FISHER_FRAMES):
            x, y, w, h = FISHER_FRAMES[number-1]
            site['at'] = [x+w/2, y+h/2]
    document['cities']['central-empire-the-capital-city']['image'] = plates[alias['capital']]['image']
    write(CATALOG, document)
    # Anciennes images monde/regions/villes remplacees dans le meme changement (D-32).
    used = {entry['file'] for entry in new_manifest}
    for old in manifest['maps']:
        path = ASSETS/old['file']
        if old['file'] not in used and path.is_file() and path.resolve().is_relative_to(ASSETS.resolve()):
            path.unlink()
    manifest['maps'] = new_manifest
    write(ASSETS/'manifest.json', manifest)
    write(REVIEW/'delivery.json', dict(date=DATE, plates=len(plates), factions=len(factions), images=len(new_manifest)))
    print(f'Atlas installe : {len(plates)} cartes, {len(factions)} factions, {len(new_manifest)} images.')
    # Replay later author corrections after the original atlas reconstruction.
    # Its own installation updates hashes and removes superseded interior images (D-32).
    audit = ROOT/'Tools/WorldAtlasAudit20261007'
    if (audit/'audit.json').is_file():
        import apply_atlas_audit
        apply_atlas_audit.plans()
        apply_atlas_audit.apply_data()
        if (audit/'approved-registration.json').is_file():
            apply_atlas_audit.register()
        apply_atlas_audit.install()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare','install'])
    args = parser.parse_args()
    {'prepare': prepare, 'install': install}[args.action]()
