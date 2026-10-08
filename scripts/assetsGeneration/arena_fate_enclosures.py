#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Les pièces qui tiennent les trois niveaux de l'Arena of Fate dans la même emprise.

Le Colisée est un ovale de 34 × 24 cases (`arena_fate_architecture_v2.py`, `af-arena-shell`). Ses
deux sous-sols sont dessous : ils ont la même emprise, et leurs escaliers tombent aux mêmes cases
(décision de l'auteur du 4 octobre 2026). Ce script modèle ce qui manquait au kit pour l'écrire :

- `af-undercroft-shell` : l'enceinte ovale du niveau −1, la fondation des gradins — haute au nord
  et sur les flancs, basse au sud pour laisser voir les salles, percée de trois portes : le parvis
  (sud), l'escalier du triomphe (ouest), celui de la porte des morts (est) ;
- `af-catacomb-shell` : la même emprise, taillée dans la roche ;
- `af-stair-w`, `af-stair-e`, `af-stair-s` : l'escalier du kit (`af-stair`, qui monte au nord)
  tourné vers les trois autres côtés ;
- `af-stairwell` : une trémie, l'escalier qui **descend** vers le sud sous le niveau du sol ;
- `af-pyre` : un feu du pourtour de l'arène, entre deux statues de la coursive.

Blender --background --factory-startup --python scripts/assetsGeneration/arena_fate_enclosures.py
Écrit dans `Production/V4/Architecture/` de l'atelier, avec son fragment de manifeste ; n'installe
rien (`install_arena_fate.py`). Les matières sont celles de l'atlas des sous-sols.
"""
import argparse
import importlib.util
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROD = ROOT / 'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production'
OUT = PROD / 'V4/Architecture'
spec = importlib.util.spec_from_file_location(
    'arena_underground', Path(__file__).with_name('arena_fate_underground_v3.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
b = u.b
box, face, transform = b.box, b.face, b.transformed
STONE, MARBLE, CAT, JOINT = u.STONE, u.MARBLE, u.CAT, u.JOINT

# L'emprise commune, en mètres : le nu intérieur de l'enceinte, et son épaisseur. Une case fait
# 1,5 m ; la carte, 51 × 36 m. Le plan des cartes (`scripts/maps/arena_fate_levels.py`) tient pour
# praticable une case dont le centre est à 0,45 m au moins en deçà de ce nu.
INNER_X, INNER_Y = 23.4, 15.9
THICK = 1.45
SEGMENTS = 144
# La demi-largeur des trois portes, et l'angle où chacune s'ouvre (0 : est, 90 : nord).
GATE_HALF = 1.62
GATES = {'east': 0.0, 'south': 270.0, 'west': 180.0}


def tangent(angle, rx=INNER_X, ry=INNER_Y):
    return math.atan2(ry * math.cos(angle), -rx * math.sin(angle))


def in_gate(x, y):
    """Vrai si le point de l'enceinte est dans l'ouverture d'une des trois portes."""
    return (abs(y) < GATE_HALF and abs(x) > INNER_X - 1) or (abs(x) < GATE_HALF and y < -INNER_Y + 1)


def height_at(angle, tall, low):
    """La hauteur de l'enceinte à cet angle : haute au nord, basse au sud, d'une pente douce."""
    return low + (tall - low) * min(1.0, max(0.0, (math.sin(angle) + 0.22) / 0.30))


def band(rx, ry, width, z, h, slot, keep):
    """Une assise elliptique : un voussoir par segment, là où `keep(angle, x, y)` le garde."""
    for i in range(SEGMENTS):
        a0 = i * math.tau / SEGMENTS
        a1 = (i + 1) * math.tau / SEGMENTS
        mid = (a0 + a1) / 2
        if not keep(mid, rx * math.cos(mid), ry * math.sin(mid)):
            continue
        p = [(rx * math.cos(a0), ry * math.sin(a0)),
             ((rx + width) * math.cos(a0), (ry + width) * math.sin(a0)),
             ((rx + width) * math.cos(a1), (ry + width) * math.sin(a1)),
             (rx * math.cos(a1), ry * math.sin(a1))]
        face([(x, y, z + h) for x, y in p], slot)
        face([(x, y, z) for x, y in p[::-1]], slot)
        for j in range(4):
            x, y = p[j]
            s, t = p[(j + 1) % 4]
            face([(x, y, z), (s, t, z), (s, t, z + h), (x, y, z + h)], slot)


def apron(slot):
    """Le sol au pied de l'enceinte : le dallage en cases s'arrête avant la courbe, lui la rejoint."""
    for ring in range(4):
        inset = 4.4 - ring * 1.15
        band(INNER_X - inset, INNER_Y - inset, 1.2, 0, 0.1, slot, lambda a, x, y: True)


def gate_frame(angle_degrees, slot):
    """Les piédroits et l'arc d'une porte de l'enceinte, dans l'axe de son escalier."""
    a = math.radians(angle_degrees)
    x, y = (INNER_X + THICK / 2) * math.cos(a), (INNER_Y + THICK / 2) * math.sin(a)

    def frame():
        for side in (-1, 1):
            for course in range(8):
                box(side * (GATE_HALF + 0.38), 0, course * 0.375, 0.76, THICK + 0.3, 0.36, slot)
            box(side * (GATE_HALF + 0.38), 0, 3.0, 0.9, THICK + 0.44, 0.16, MARBLE)
        u.arch(0, 0, 3.16, GATE_HALF, GATE_HALF + 0.42, THICK + 0.16, slot, 20)
        box(0, 0, 3.16 + GATE_HALF + 0.42, 2 * GATE_HALF + 1.7, THICK + 0.36, 0.2, MARBLE)

    transform(frame, x, y, 0, tangent(a))


def undercroft_shell():
    """L'enceinte du niveau −1 : la fondation en grand appareil des gradins."""
    apron(STONE)
    courses = 8
    for course in range(courses):
        z = course * 0.375
        band(INNER_X, INNER_Y, THICK, z, 0.36, STONE,
             lambda a, x, y, z=z: not in_gate(x, y) and z + 0.36 <= height_at(a, 3.0, 1.2) + 0.01)
    # Le joint en retrait, le socle et le couronnement de marbre.
    band(INNER_X + 0.03, INNER_Y + 0.03, THICK - 0.06, 0, 1.15, JOINT,
         lambda a, x, y: not in_gate(x, y))
    band(INNER_X - 0.07, INNER_Y - 0.07, THICK + 0.14, 0, 0.16, STONE,
         lambda a, x, y: not in_gate(x, y))
    for top, keep in ((3.0, lambda a: math.sin(a) > 0.08), (1.2, lambda a: math.sin(a) < -0.22)):
        band(INNER_X - 0.09, INNER_Y - 0.09, THICK + 0.18, top, 0.17, MARBLE,
             lambda a, x, y, keep=keep: keep(a) and not in_gate(x, y))
    # Les arcs de décharge de la partie haute : l'ossature qui porte les gradins se voit.
    bays = 26
    for bay in range(bays):
        a = (bay + 0.5) * math.pi / bays
        if not 0.16 < a < math.pi - 0.16:
            continue
        x, y = (INNER_X - 0.02) * math.cos(a), (INNER_Y - 0.02) * math.sin(a)

        def relief():
            for side in (-1, 1):
                box(side * 0.98, 0, 0.16, 0.36, 0.22, 1.5, STONE)
                box(side * 0.98, 0, 1.66, 0.46, 0.28, 0.12, MARBLE)
            u.arch(0, 0, 1.78, 0.8, 1.14, 0.22, STONE, 14)

        transform(relief, x, y, 0, tangent(a) + math.pi)
    for degrees in GATES.values():
        gate_frame(degrees, STONE)


def catacomb_shell():
    """La même emprise, taillée dans la roche : des strates irrégulières, sans appareil."""
    apron(CAT)
    rng = random.Random(1570)
    strata = 5
    rough = [[rng.uniform(-0.28, 0.42) for _ in range(SEGMENTS)] for _ in range(strata)]
    for layer in range(strata):
        z = layer * 0.72
        for i in range(SEGMENTS):
            a0 = i * math.tau / SEGMENTS
            a1 = (i + 1) * math.tau / SEGMENTS
            mid = (a0 + a1) / 2
            top = height_at(mid, 3.6, 1.1) + rough[0][i] * 0.6
            if z >= top:
                continue
            h = min(0.72, top - z)
            inner = (rough[layer][i] + rough[layer][(i + 1) % SEGMENTS]) / 2 - layer * 0.05
            rx, ry = INNER_X + inner, INNER_Y + inner
            width = THICK + 0.5 - inner
            p = [(rx * math.cos(a0), ry * math.sin(a0)),
                 ((rx + width) * math.cos(a0), (ry + width) * math.sin(a0)),
                 ((rx + width) * math.cos(a1), (ry + width) * math.sin(a1)),
                 (rx * math.cos(a1), ry * math.sin(a1))]
            slot = CAT if (i + layer) % 3 else JOINT
            face([(x, y, z + h) for x, y in p], slot)
            for j in range(4):
                x, y = p[j]
                s, t = p[(j + 1) % 4]
                face([(x, y, z), (s, t, z), (s, t, z + h), (x, y, z + h)], slot)


def stair(angle):
    """L'escalier du kit, qui monte au nord, tourné de `angle`."""
    transform(lambda: u.legacy(b.stair), angle=angle)


def stairwell():
    """Une trémie : quinze marches qui descendent vers le sud, entre trois garde-corps."""
    for step in range(15):
        box(0, 2.25 - (step + 0.5) * 0.3, -(step + 1) * 0.2, 2.6, 0.3, 0.2, STONE)
    for side in (-1, 1):
        box(side * 1.34, 0, -3.1, 0.12, 4.4, 3.1, JOINT)
        box(side * 1.34, 0, 0, 0.24, 4.4, 0.86, STONE)
        box(side * 1.34, 0, 0.86, 0.3, 4.4, 0.12, MARBLE)
    box(0, -2.14, -3.1, 2.6, 0.12, 3.1, JOINT)
    box(0, -2.06, 0, 2.92, 0.24, 0.86, STONE)
    box(0, -2.06, 0.86, 2.92, 0.3, 0.12, MARBLE)
    box(0, 0, -3.12, 2.6, 4.4, 0.04, JOINT)


def pyre():
    """Un feu du pourtour de l'arène : une vasque de bronze sur son dé de marbre, à l'échelle du
    monument — le brasero du kit est celui d'une salle."""
    box(0, 0, 0, 1.0, 1.0, 0.18, MARBLE)
    box(0, 0, 0.18, 0.8, 0.8, 0.5, MARBLE)
    box(0, 0, 0.68, 0.96, 0.96, 0.12, MARBLE)
    b.lathe(0, 0, 0.8, [(0.22, 0), (0.14, 0.25), (0.2, 0.5), (0.55, 0.8), (0.62, 0.95), (0.5, 0.97)],
            u.BRONZE, 20)
    for tongue in range(9):
        a = tongue * math.tau / 9
        b.lathe(0.3 * math.cos(a), 0.3 * math.sin(a), 1.72,
                [(0.1, 0), (0.14, 0.16), (0.04, 0.42), (0, 0.6)], u.FIRE, 6)
    b.lathe(0, 0, 1.72, [(0.2, 0), (0.22, 0.2), (0.07, 0.6), (0, 0.9)], u.EMBER, 8)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default='')
    arguments = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    only = {name for name in arguments.only.split(',') if name}
    OUT.mkdir(parents=True, exist_ok=True)
    u.OUT = OUT
    u.bpy.ops.object.select_all(action='SELECT')
    u.bpy.ops.object.delete(use_global=False)
    material = u.mat_atlas()
    jobs = [
        ('af-undercroft-shell', [34, 24], undercroft_shell, 'wide', 0.012),
        ('af-catacomb-shell', [34, 24], catacomb_shell, 'wide', 0),
        ('af-stair-w', [3, 2], lambda: stair(math.pi / 2), 'tall', 0.008),
        ('af-stair-e', [3, 2], lambda: stair(-math.pi / 2), 'tall', 0.008),
        ('af-stair-s', [2, 3], lambda: stair(math.pi), 'tall', 0.008),
        ('af-stairwell', [2, 3], stairwell, 'tall', 0.008),
        ('af-pyre', [1, 1], pyre, 'tall', 0.008),
    ]
    textures, measures = {}, []
    if only and (OUT / 'architecture-manifest.json').exists():
        # Une reprise ciblée garde au fragment les pièces qu'elle ne refait pas.
        textures = json.loads((OUT / 'architecture-manifest.json').read_text(encoding='utf8'))['textures']
        measures = [measure for measure in json.loads(
            (OUT / 'architecture-measurements.json').read_text(encoding='utf8'))
            if measure['id'] not in only]
    for name, footprint, build, kind, bevel in jobs:
        if only and name not in only:
            continue
        entry, measure = u.export(name, footprint, build, material, kind, bevel)
        if kind == 'wide':
            # Une enceinte ne dit rien du praticable : la couche de collision de la carte le fait.
            entry['tactical'] = 'open'
        if name == 'af-pyre':
            # Jugé sur captures de l'arène à 22 h (D-46, par délégation) : il porte deux fois plus
            # loin que le brasero d'une salle.
            entry['light'] = {'color': '#ffb866', 'radius': 13.0, 'height': 2.2, 'flicker': True,
                              'always': True}
            entry['glow'] = 0.5
        textures['scene/arena-of-fate/' + name] = entry
        measures.append(measure)
    manifest = {'version': 1, 'tile': [256, 159], 'storey': 283.742841317, 'textures': textures}
    (OUT / 'architecture-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    (OUT / 'architecture-measurements.json').write_text(json.dumps(measures, indent=2),
                                                        encoding='utf8')
    print('FINISHED', len(measures), 'pieces', sum(m['triangles'] for m in measures), 'triangles',
          flush=True)


if __name__ == '__main__':
    main()
