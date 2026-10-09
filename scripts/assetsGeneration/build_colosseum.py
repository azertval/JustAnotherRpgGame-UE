#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Construit le Colisée d'Arenarea en **pièces modulaires**, à l'échelle du Colisée de Rome (LOT-1012).

La coque d'un seul tenant de l'ancien kit (`af-arena-shell.glb`, 51 × 36 m, trois images pour
toute sa surface) ne tient pas le gros plan une fois agrandie 2,7 fois : sa pierre est floue, ses
moulures sont des boîtes. Ce script la remplace par un **anneau de pièces** que la scène pose
une à une, chacune texturée au mètre (une image de pierre se répète tous les 3 m, le marbre tous
les 2 m) : la définition ne dépend plus de la taille du monument.

Les dimensions sont celles du Colisée de Rome, décision de l'auteur du 8 octobre 2026 (« pour la
taille rendue de l'arena base-toi sur le Colisée de Rome ») : 189 × 156 m au sol, 48 m de haut,
80 arcades par ordre, l'arène de 83 × 48 m. Les pièces (repère de Blender : X vers l'est, Y vers le
nord, Z vers le haut ; la façade d'une travée regarde −Y, sa face extérieure est en Y = 0) :

- `col-arcade-1`, `col-arcade-2`, `col-arcade-3` : une travée de chaque ordre (toscan, ionique,
  corinthien) — deux demi-piliers, l'arc, les écoinçons, l'entablement, la colonne engagée ; derrière,
  le sol, la voûte et le mur de fond de la galerie ; aux étages, un garde-corps de marbre dans l'arc ;
- `col-attic` : une travée de l'attique — pilastres, fenêtre, corbeaux et mât de velum ;
- `col-gate` : la porte axiale, sur trois travées, avec son tunnel jusqu'au sable et les socles des
  deux lions ;
- `col-cavea` : un quart des gradins avec le podium, depuis l'arène jusqu'à la galerie haute, ouvert
  sur l'axe pour le tunnel (posé quatre fois, par symétrie) ;
- `col-loge` : la loge impériale, au nord, dans l'ouverture symétrique du tunnel ;
- `col-sand` : le sable de l'arène ; `col-plinth` : le socle d'une statue dans un arc.

`ring_bays()` donne, à la scène comme à ce script, le centre et le lacet de chaque travée sur
l'ellipse, à longueur d'arc égale : c'est le seul endroit où l'anneau se calcule.

Les textures viennent de l'atelier de l'Arena of Fate (les cinq couleurs de base de D-46,
`Tools/…/V2/Textures/`, hors Git). Chaque matière porte sa **couleur de base** et sa rugosité et son
métal en **facteurs** glTF, les valeurs jugées sur captures au 4 octobre 2026 (D-46) ; elle ne porte
**plus de carte dérivée de sa couleur** : `material_maps.py` est retiré au LOT-1019 (« une pièce
livre ses vraies cartes, ou se recommande »), et le relief du Colisée est dans son maillage. Le
Colisée reste une pièce **construite** (famille 10, D-55 « composé ») jusqu'à sa reprise au
LOT-1021. Les pièces s'écrivent sous `Source/Elements/Assets/Built/colisee/` avec leur manifeste
(empreintes, triangles, dimensions), hors des kits verrouillés par `kits.lock.json`.

Usage (Python du poste ; Blender est lancé par le script) :
    python scripts/assetsGeneration/build_colosseum.py [--only col-gate,col-attic] [--blender CHEMIN]
        [--textures DOSSIER] [--output DOSSIER]

Dépendances : Blender 5.2, numpy (outil de production, pas de CI).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np

try:
    import bpy  # type: ignore
except ImportError:  # hors de Blender : seuls le pilote et `ring_bays` servent
    bpy = None

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source" / "Elements" / "Assets" / "Built" / "colisee"
TEXTURES = ROOT / "Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/V2/Textures"
BLENDER_DEFAULT = Path(r"D:\Blender Foundation\Blender 5.2\blender.exe")

# Le Colisée de Rome, en mètres (décision de l'auteur, 8 octobre 2026).
SPEC = {
    "a": 94.5, "b": 78.0,           # demi-axes de l'ellipse extérieure : 189 × 156 m
    "innerA": 41.5, "innerB": 24.0,  # l'arène : 83 × 48 m
    "bays": 80,                      # arcades par ordre
    "orders": [11.0, 11.5, 11.5],    # hauteur des trois ordres
    "attic": 14.0,                   # l'attique : 48 m en tout
    "pier": 2.4,                     # largeur d'un pilier
    "depth": 2.2,                    # épaisseur du mur de façade
    "entablature": 1.9,              # hauteur de l'entablement d'un ordre
    "gallery": 5.0,                  # profondeur de la galerie derrière chaque arc
    "gateBays": 3,                   # la porte axiale remplace trois travées
    "tunnelWidth": 10.0,             # l'ouverture du tunnel axial
    "tunnelHeight": 19.0,            # sa voûte : l'arc de la porte traverse les deux premiers ordres
    "gateProtrusion": 1.5,           # ce que la porte avance sur l'ellipse
    "tread": 0.8, "rise": 0.5,       # un gradin
    "podium": 5.0,                   # la hauteur du podium au-dessus du sable
}
# Les matières : l'indice d'une face, le nom de sa texture, la longueur d'une répétition en mètres,
# sa rugosité et son métal (D-46, jugés sur captures le 4 octobre 2026).
MATTERS_LIST = [("limestone", 3.0, 0.88, 0.0), ("marble", 2.0, 0.36, 0.0), ("sand", 3.0, 0.96, 0.0),
                ("velvet", 1.5, 0.92, 0.0), ("bronze", 1.0, 0.42, 1.0)]
LIME, MARBLE, SAND, VELVET, BRONZE = range(5)


# --- L'anneau ---------------------------------------------------------------------------------

def ellipse_arc(a: float, b: float, samples: int = 36_000) -> tuple[np.ndarray, np.ndarray]:
    """Le paramètre `t` et la longueur d'arc cumulée `s(t)` de l'ellipse, de 0 à 2π."""
    t = np.linspace(0.0, 2.0 * math.pi, samples + 1)
    x, y = a * np.cos(t), b * np.sin(t)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(x), np.diff(y)))])
    return t, s


def perimeter(a: float, b: float) -> float:
    return float(ellipse_arc(a, b)[1][-1])


def bay_width(spec: dict = SPEC) -> float:
    """La largeur d'une travée : le périmètre divisé par le nombre d'arcades (6,79 m à Rome)."""
    return perimeter(spec["a"], spec["b"]) / spec["bays"]


def ring_bays(spec: dict = SPEC) -> list[dict]:
    """Les travées de l'anneau, à longueur d'arc égale, la travée 0 centrée plein sud.

    Chaque travée est la corde entre deux points de l'ellipse ; `centre` est le milieu de la corde,
    `yaw` le lacet (degrés, sens direct vu du ciel) qui amène la façade d'une pièce (regardant −Y)
    sur la normale sortante, `normal` cette normale. Les cordes se suivent bout à bout : la façade
    est un polygone inscrit, sans trou ; le demi-pilier de chaque bout recouvre celui du voisin.
    """
    a, b, n = spec["a"], spec["b"], spec["bays"]
    t, s = ellipse_arc(a, b)
    length = float(s[-1])
    width = length / n
    south = float(np.interp(1.5 * math.pi, t, s))

    def point(arc: float) -> np.ndarray:
        angle = float(np.interp(arc % length, s, t))
        return np.array([a * math.cos(angle), b * math.sin(angle)])

    bays = []
    for k in range(n):
        p0, p1 = point(south + (k - 0.5) * width), point(south + (k + 0.5) * width)
        chord = p1 - p0
        normal = np.array([chord[1], -chord[0]]) / np.linalg.norm(chord)
        centre = (p0 + p1) / 2
        bays.append({
            "index": k,
            "centre": [round(float(centre[0]), 4), round(float(centre[1]), 4)],
            "normal": [round(float(normal[0]), 6), round(float(normal[1]), 6)],
            "yaw": round(math.degrees(math.atan2(normal[0], -normal[1])) % 360.0, 4),
            "chord": round(float(np.linalg.norm(chord)), 4),
        })
    return bays


def inside_ellipse(x: float, y: float, a: float, b: float) -> bool:
    return (x / a) ** 2 + (y / b) ** 2 < 1.0


# --- La géométrie (dans Blender) --------------------------------------------------------------

V: list[tuple[float, float, float]] = []
F: list[tuple[int, ...]] = []
M: list[int] = []
S: list[bool] = []


def reset() -> None:
    V.clear()
    F.clear()
    M.clear()
    S.clear()


def face(points, m: int, smooth: bool = False) -> None:
    n = len(V)
    V.extend(tuple(p) for p in points)
    F.append(tuple(range(n, n + len(points))))
    M.append(m)
    S.append(smooth)


def box(x: float, y: float, z: float, w: float, d: float, h: float, m: int = LIME) -> None:
    """Une boîte centrée en (x, y), posée en z, de largeur w (X), profondeur d (Y), hauteur h."""
    a, b, e, f = x - w / 2, x + w / 2, y - d / 2, y + d / 2
    p = [(a, e, z), (b, e, z), (b, f, z), (a, f, z), (a, e, z + h), (b, e, z + h), (b, f, z + h), (a, f, z + h)]
    for ids in [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)]:
        face([p[i] for i in ids], m)


def prism(polygon, y0: float, y1: float, m: int) -> None:
    """Un polygone du plan (x, z), en sens direct, extrudé de y0 à y1 ; sa face avant regarde −Y."""
    face([(x, y0, z) for x, z in polygon], m)
    face([(x, y1, z) for x, z in reversed(polygon)], m)
    count = len(polygon)
    for i in range(count):
        (x0, z0), (x1, z1) = polygon[i], polygon[(i + 1) % count]
        face([(x0, y0, z0), (x0, y1, z0), (x1, y1, z1), (x1, y0, z1)], m)


def lathe(x: float, y: float, z: float, profile, m: int, n: int = 24, smooth: bool = True,
          flutes: float = 0.0) -> None:
    """Un solide de révolution autour de la verticale, aux sommets partagés (lissage propre).

    `profile` : des (rayon, hauteur) du bas vers le haut ; `flutes` creuse un sommet sur deux."""
    rings = []
    for r, h in profile:
        base = len(V)
        for j in range(n):
            rr = r * (1.0 - flutes * (j % 2))
            angle = j * math.tau / n
            V.append((x + rr * math.cos(angle), y + rr * math.sin(angle), z + h))
        rings.append(base)
    for i in range(len(profile) - 1):
        for j in range(n):
            k = (j + 1) % n
            F.append((rings[i] + j, rings[i] + k, rings[i + 1] + k, rings[i + 1] + j))
            M.append(m)
            S.append(smooth and not flutes)
    for ring, reverse in ((rings[0], True), (rings[-1], False)):
        ids = [ring + j for j in range(n)]
        F.append(tuple(ids[::-1] if reverse else ids))
        M.append(m)
        S.append(False)


def rod(a, b, r: float, m: int = BRONZE, n: int = 10) -> None:
    """Un cylindre entre deux points."""
    a, b = np.array(a, dtype=float), np.array(b, dtype=float)
    t = b - a
    t /= np.linalg.norm(t)
    q = np.cross(t, [0.0, 0.0, 1.0])
    if np.linalg.norm(q) < 0.01:
        q = np.cross(t, [0.0, 1.0, 0.0])
    q /= np.linalg.norm(q)
    v = np.cross(t, q)
    for j in range(n):
        aa, bb = j * math.tau / n, (j + 1) * math.tau / n
        p = r * (q * math.cos(aa) + v * math.sin(aa))
        s = r * (q * math.cos(bb) + v * math.sin(bb))
        face([a + p, a + s, b + s, b + p], m)


def torus(x: float, y: float, z: float, r: float, t: float, m: int = MARBLE, vertical: bool = False) -> None:
    for i in range(20):
        for j in range(8):
            pts = []
            for u, w in [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]:
                a, b = u * math.tau / 20, w * math.tau / 8
                xx = (r + t * math.cos(b)) * math.cos(a)
                yy = (r + t * math.cos(b)) * math.sin(a)
                zz = t * math.sin(b)
                pts.append((x + xx, y + (zz if vertical else yy), z + (yy if vertical else zz)))
            face(pts, m)


def arch_ring(x: float, y: float, z: float, ri: float, ro: float, depth: float, m: int, n: int = 24) -> None:
    """L'arc en plein cintre : des claveaux de ri à ro, d'épaisseur `depth` centrée en y."""
    for i in range(n):
        a = i * math.pi / n + 0.004
        b = (i + 1) * math.pi / n - 0.004
        p = [(x + ri * math.cos(a), z + ri * math.sin(a)), (x + ro * math.cos(a), z + ro * math.sin(a)),
             (x + ro * math.cos(b), z + ro * math.sin(b)), (x + ri * math.cos(b), z + ri * math.sin(b))]
        face([(u, y - depth / 2, w) for u, w in p], m)
        face([(u, y + depth / 2, w) for u, w in p[::-1]], m)
        for k in range(4):
            (u, w), (s, t) = p[k], p[(k + 1) % 4]
            face([(u, y - depth / 2, w), (u, y + depth / 2, w), (s, y + depth / 2, t), (s, y - depth / 2, t)], m)


def extrados(ri: float, ro: float, impost: float, x_from: float, x_to: float, n: int = 12):
    """Les points de l'extrados d'un arc entre deux abscisses, du premier au second."""
    a0 = math.acos(max(-1.0, min(1.0, x_from / ro)))
    a1 = math.acos(max(-1.0, min(1.0, x_to / ro)))
    return [(ro * math.cos(a0 + (a1 - a0) * i / n), impost + ro * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def column(x: float, y: float, h: float, order: int, r: float = 0.5) -> None:
    """Une colonne engagée de l'ordre `order` (0 toscan, 1 ionique, 2 corinthien), de rayon r."""
    box(x, y, 0.0, 3.0 * r, 3.0 * r, 0.30 * r, MARBLE)
    box(x, y, 0.30 * r, 2.6 * r, 2.6 * r, 0.24 * r, MARBLE)
    lathe(x, y, 0.54 * r, [(1.22 * r, 0.0), (1.34 * r, 0.12 * r), (1.26 * r, 0.24 * r), (1.05 * r, 0.36 * r),
                           (1.0 * r, 0.5 * r)], MARBLE)
    shaft_top = h - 1.4 * r
    lathe(x, y, 1.0 * r, [(1.0 * r, 0.0), (0.98 * r, (shaft_top - 1.0 * r) * 0.4), (0.84 * r, shaft_top - 1.0 * r)],
          MARBLE, 48, False, 0.10)
    lathe(x, y, shaft_top, [(0.86 * r, 0.0), (1.02 * r, 0.1 * r), (1.08 * r, 0.2 * r), (1.04 * r, 0.36 * r),
                            (1.38 * r, 0.9 * r), (1.46 * r, 1.0 * r)], MARBLE)
    box(x, y, h - 0.44 * r, 2.9 * r, 2.9 * r, 0.22 * r, MARBLE)
    box(x, y, h - 0.22 * r, 3.1 * r, 3.1 * r, 0.22 * r, MARBLE)
    if order >= 1:
        for dx in (-1.0 * r, 1.0 * r):
            torus(x + dx, y - 1.1 * r, h - 0.7 * r, 0.42 * r, 0.11 * r, MARBLE, True)
    if order == 2:
        for j in range(8):
            a = j * math.tau / 8
            lathe(x + 0.9 * r * math.cos(a), y + 0.9 * r * math.sin(a), h - 1.3 * r,
                  [(0.14 * r, 0.0), (0.32 * r, 0.42 * r), (0.32 * r, 0.76 * r), (0.1 * r, 1.2 * r)], MARBLE, 8)


def entablature(x: float, z: float, w: float, y0: float, y1: float, height: float, m: int = LIME) -> None:
    """Architrave, frise et corniche : trois bandes, la corniche en saillie."""
    bands = [(0.0, 0.36, 0.10), (0.36, 0.34, 0.0), (0.70, 0.30, 0.45)]
    for start, part, out in bands:
        box(x, (y0 - out + y1) / 2, z + start * height, w, y1 - (y0 - out), part * height, m)
    # Les denticules sous la corniche.
    for j in range(int(w / 0.9)):
        box(x - w / 2 + (j + 0.5) * w / int(w / 0.9), y0 - 0.22, z + 0.66 * height, 0.34, 0.26, 0.26, MARBLE)


def balustrade(x: float, y: float, z: float, w: float, h: float = 1.15) -> None:
    """Un garde-corps de marbre : deux lisses et des balustres."""
    box(x, y, z, w, 0.5, 0.18, MARBLE)
    box(x, y, z + h - 0.16, w, 0.52, 0.16, MARBLE)
    count = max(1, round(w / 0.42))
    for i in range(count):
        xx = x - w / 2 + (i + 0.5) * w / count
        lathe(xx, y, z + 0.18, [(0.12, 0.0), (0.12, 0.06), (0.07, 0.14), (0.11, 0.26), (0.12, 0.4), (0.07, 0.55),
                                (0.08, 0.7), (0.12, 0.78), (0.12, h - 0.16)], MARBLE, 12)


def arcade(order: int, spec: dict = SPEC) -> None:
    """Une travée d'arcades de l'ordre donné : façade en Y = 0, galerie derrière."""
    height = spec["orders"][order]
    w, p, d, e = bay_width(spec), spec["pier"], spec["depth"], spec["entablature"]
    opening = w - p
    top = height - e
    ri, ro = opening / 2, opening / 2 + 0.6
    impost = top - ro - 0.5
    for sign in (-1, 1):
        box(sign * w / 2, d / 2, 0.0, p, d, top, LIME)
        # L'écoinçon, du pilier au sommet de l'arc.
        ze = impost + math.sqrt(ro * ro - ri * ri)
        arc = extrados(ri, ro, impost, sign * ri, 0.0)
        polygon = [(sign * ri, ze)] + arc[1:] + [(0.0, top), (sign * ri, top)]
        if sign > 0:
            polygon = polygon[::-1]
        prism(polygon, 0.0, d, LIME)
        column(sign * w / 2, 0.15, top, order)
    arch_ring(0.0, d / 2, impost, ri, ro, d, LIME)
    # La clé de l'arc.
    box(0.0, d / 2 - 0.18, impost + ri - 0.2, 0.7, d + 0.36, ro - ri + 0.5, MARBLE)
    entablature(0.0, top, w + p, 0.0, d, e)
    # La galerie : sol, voûte et mur de fond.
    gallery = spec["gallery"]
    box(0.0, d + gallery / 2, -0.4, w + p, gallery, 0.4, LIME)
    box(0.0, d + gallery / 2, impost + ri, w + p, gallery, top - impost - ri + e, LIME)
    if order == 0:
        # Au rez-de-chaussée, le mur de fond s'ouvre sur un passage sombre.
        door = 2.6
        for sign in (-1, 1):
            box(sign * (door / 2 + (w + p - door) / 4), d + gallery + 0.3, 0.0, (w + p - door) / 2, 0.6, impost + ri, LIME)
        box(0.0, d + gallery + 0.3, 4.2, door + 0.2, 0.6, impost + ri - 4.2, LIME)
        box(0.0, d + gallery + 2.0, 0.0, door + 2.0, 3.0, 0.1, LIME)
        box(0.0, d + gallery + 3.5, 0.0, door + 2.0, 0.4, impost + ri, LIME)
    else:
        box(0.0, d + gallery + 0.3, 0.0, w + p, 0.6, impost + ri, LIME)
        balustrade(0.0, d / 2, 0.0, opening - 0.1)


def attic(spec: dict = SPEC) -> None:
    """Une travée de l'attique : pilastres, fenêtre, corbeaux, corniche et mât de velum."""
    height = spec["attic"]
    w, p, d = bay_width(spec), spec["pier"], spec["depth"]
    wall_top = height - 1.9
    window = (-1.2, 1.2, 5.2, 7.6)
    x0, x1, z0, z1 = window
    half = (w + p) / 2
    box(-(half + x0) / 2 + x0, d / 2, 0.0, x0 + half, d, wall_top, LIME)
    box((half - x1) / 2 + x1, d / 2, 0.0, half - x1, d, wall_top, LIME)
    box(0.0, d / 2, 0.0, x1 - x0, d, z0, LIME)
    box(0.0, d / 2, z1, x1 - x0, d, wall_top - z1, LIME)
    # L'embrasure : un fond de pierre à 0,9 m, un encadrement de marbre.
    box(0.0, d / 2 + 0.45, z0, x1 - x0 + 0.2, d - 0.9, z1 - z0, LIME)
    for sign in (-1, 1):
        box(sign * (x1 + 0.18), -0.06, z0 - 0.3, 0.36, 0.12, z1 - z0 + 0.6, MARBLE)
    box(0.0, -0.06, z0 - 0.3, x1 - x0 + 0.72, 0.12, 0.3, MARBLE)
    box(0.0, -0.08, z1, x1 - x0 + 0.72, 0.16, 0.36, MARBLE)
    for sign in (-1, 1):
        box(sign * w / 2, -0.24, 0.0, 1.5, 0.48, wall_top, LIME)
        box(sign * w / 2, -0.28, wall_top - 0.5, 1.7, 0.56, 0.5, MARBLE)
        box(sign * w / 2, -0.26, 0.0, 1.7, 0.52, 0.6, MARBLE)
    for xx in (-w / 4, 0.0, w / 4):
        box(xx, -0.4, 9.4, 0.8, 0.8, 1.0, LIME)
        box(xx, -0.6, 10.1, 0.5, 0.4, 0.3, BRONZE)
    entablature(0.0, wall_top, w + p, 0.0, d, 1.9)
    rod((0.0, -0.62, 9.6), (0.0, -0.62, height + 5.0), 0.17, BRONZE, 12)
    lathe(0.0, -0.62, height + 5.0, [(0.2, 0.0), (0.32, 0.25), (0.08, 0.8), (0.0, 1.0)], BRONZE, 12)
    face([(0.0, -0.62, height + 4.7), (2.6, -0.62, height + 4.0), (0.0, -0.62, height + 3.3)], VELVET)
    face([(0.0, -0.62, height + 3.3), (2.6, -0.62, height + 4.0), (0.0, -0.62, height + 4.7)], VELVET)


def gate(spec: dict = SPEC) -> None:
    """La porte axiale : deux tours à colonnes jumelées, l'arc, le tunnel jusqu'à l'arène."""
    w = bay_width(spec) * spec["gateBays"]
    d, e = spec["depth"], spec["entablature"]
    h1, h2, h3 = spec["orders"]
    out = spec["gateProtrusion"]
    opening = spec["tunnelWidth"]
    tower = (w - opening) / 2
    tower_top = h1 + h2 + h3
    ri, ro = opening / 2, opening / 2 + 0.9
    impost = spec["tunnelHeight"] - ri
    top = h1 + h2 - e
    for sign in (-1, 1):
        tx = sign * (w / 2 - tower / 2)
        box(tx, (d - out) / 2, 0.0, tower, d + out, tower_top, LIME)
        for z, hh, order in ((0.0, h1, 0), (h1, h2, 1), (h1 + h2, h3, 2)):
            for dx in (-1.55, 1.55):
                box(tx + dx, -out + 0.1, z, 2.0, 1.4, 0.5, MARBLE)
                column(tx + dx, -out + 0.15, hh - 0.6, order, 0.5)
            entablature(tx, z + hh - 0.6, tower + 0.8, -out - 0.4, d, 0.6)
            # Une niche de marbre entre les colonnes jumelées.
            box(tx, -out - 0.05, z + 2.0, 1.6, 0.1, hh - 4.0, MARBLE)
        for z, ww, dd, hh in [(tower_top, tower + 0.6, d + out + 0.6, 0.32), (tower_top + 0.32, tower + 1.0, d + out + 1.0, 0.3),
                              (tower_top + 0.62, tower + 0.6, d + out + 0.6, 0.3)]:
            box(tx, (d - out) / 2, z, ww, dd, hh, LIME)
        box(tx, (d - out) / 2, tower_top + 0.92, 4.4, 4.4, 0.3, MARBLE)
        box(tx, (d - out) / 2, tower_top + 1.22, 3.8, 3.8, 0.2, MARBLE)
        # L'écoinçon, de la tour (qui sert de pile) au sommet de l'arc.
        ze = impost + math.sqrt(ro * ro - ri * ri)
        arc = extrados(ri, ro, impost, sign * ri, 0.0)
        polygon = [(sign * ri, ze)] + arc[1:] + [(0.0, top), (sign * ri, top)]
        if sign > 0:
            polygon = polygon[::-1]
        prism(polygon, -out, d, LIME)
    arch_ring(0.0, (d - out) / 2, impost, ri, ro, d + out, LIME)
    box(0.0, (d - out) / 2 - 0.2, impost + ri - 0.3, 1.2, d + out + 0.4, ro - ri + 0.7, MARBLE)
    inner = w / 2 - tower
    entablature(0.0, top, inner * 2 + 0.2, -out, d, e)
    # Le panneau d'attique au-dessus de l'arc, et la tenture de velours de l'empire.
    attic_top = top + e + 6.0
    box(0.0, (d - out) / 2, top + e, inner * 2 + 0.2, d + out, 6.0, LIME)
    box(0.0, -out - 0.08, top + e + 1.0, inner * 2 - 2.0, 0.16, 4.0, VELVET)
    for sign in (-1, 1):
        box(sign * (inner - 0.6), -out - 0.12, top + e + 0.7, 0.4, 0.24, 4.6, BRONZE)
    entablature(0.0, attic_top, inner * 2 + 0.2, -out, d, 1.5, MARBLE)
    # Le tunnel : sol, parois et voûte, de la façade au podium.
    length = spec["b"] - spec["innerB"]
    box(0.0, length / 2, -0.4, opening + 2.4, length, 0.4, LIME)
    for sign in (-1, 1):
        box(sign * (ri + 0.6), (d + length) / 2, 0.0, 1.2, length - d, spec["tunnelHeight"], LIME)
    box(0.0, (d + length) / 2, spec["tunnelHeight"] - 0.2, opening + 2.4, length - d, 1.4, LIME)
    # Les niches de torches le long du tunnel, un lampadaire de bronze tous les 9 m.
    for j in range(1, int(length / 9.0)):
        for sign in (-1, 1):
            rod((sign * ri, d + j * 9.0, 4.0), (sign * ri * 0.86, d + j * 9.0, 4.6), 0.07, BRONZE, 8)
            lathe(sign * ri * 0.86, d + j * 9.0, 4.6, [(0.12, 0.0), (0.22, 0.25), (0.2, 0.5), (0.0, 0.55)], BRONZE, 8)


def cavea(spec: dict = SPEC) -> None:
    """Un quart des gradins (X ≥ 0, Y ≥ 0) : le podium, les rangs, deux promenoirs, la galerie haute.

    Les rangs qui restent sous la voûte du tunnel s'arrêtent avant l'axe (Y) ; les autres le
    franchissent et couvrent le tunnel. Posé quatre fois par symétrie, le quart fait l'anneau."""
    ia, ib = spec["innerA"], spec["innerB"]
    tread, rise, podium = spec["tread"], spec["rise"], spec["podium"]
    gap = spec["tunnelWidth"] / 2 + 1.2
    segments = 44

    def band(rx: float, ry: float, width: float, z: float, h: float, m: int, cut: bool) -> None:
        t_end = math.acos(min(1.0, gap / rx)) if cut else math.pi / 2
        for i in range(segments):
            a = t_end * i / segments
            b = t_end * (i + 1) / segments
            p = [(rx * math.cos(a), ry * math.sin(a)), ((rx + width) * math.cos(a), (ry + width) * math.sin(a)),
                 ((rx + width) * math.cos(b), (ry + width) * math.sin(b)), (rx * math.cos(b), ry * math.sin(b))]
            face([(x, y, z + h) for x, y in p], m)
            for j in range(4):
                (x, y), (u, v) = p[j], p[(j + 1) % 4]
                face([(x, y, z), (u, v, z), (u, v, z + h), (x, y, z + h)], m)

    # Le podium, par assises, et son parapet de marbre.
    for k in range(int(podium / 0.5)):
        band(ia, ib, 1.4, k * 0.5, 0.5, LIME, True)
    band(ia + 0.3, ib + 0.3, 0.5, podium, 1.15, MARBLE, True)
    radius, z = 1.4, podium
    row = 0
    while ia + radius + tread < spec["a"] - spec["depth"] - spec["gallery"] - 1.0:
        over_tunnel = z >= spec["tunnelHeight"] + 1.0
        if row in (18, 36):
            # Un promenoir : une marche large et un mur de ceinture.
            band(ia + radius, ib + radius, 2.6, z, rise, LIME, not over_tunnel)
            band(ia + radius + 2.6, ib + radius + 2.6, 0.5, z + rise, 1.3, MARBLE, not over_tunnel)
            radius += 3.1
        else:
            band(ia + radius, ib + radius, tread, z, rise, LIME, not over_tunnel)
            # L'assise de marbre du gradin.
            band(ia + radius + 0.05, ib + radius + 0.05, tread - 0.1, z + rise, 0.08, MARBLE, not over_tunnel)
            radius += tread
        z += rise
        row += 1
    # La galerie haute : un mur de fond et sa corniche, sous l'attique.
    band(ia + radius, ib + radius, 1.0, z, 3.2, LIME, False)
    band(ia + radius - 0.3, ib + radius - 0.3, 1.6, z + 3.2, 0.4, MARBLE, False)


def loge(spec: dict = SPEC) -> None:
    """La loge impériale : un podium de pierre, un pavillon de marbre, le velours de l'empire."""
    depth = 8.0
    width = spec["tunnelWidth"] + 2.4 + 1.2
    podium = spec["podium"]
    box(0.0, depth / 2, 0.0, width, depth, podium, LIME)
    box(0.0, depth / 2, podium, width + 0.4, depth + 0.4, 0.3, MARBLE)
    box(0.0, depth / 2 + 0.5, podium + 0.3, width - 1.0, depth - 1.0, 0.06, VELVET)
    balustrade(0.0, 0.3, podium + 0.3, width - 0.6)
    pavilion = 9.0
    for xx in (-4.9, -1.7, 1.7, 4.9):
        for yy in (1.0, depth - 1.0):
            box(xx, yy, podium + 0.3, 1.5, 1.5, 0.3, MARBLE)
            column(xx, yy, pavilion - 0.6, 2, 0.42)
    entablature(0.0, podium + pavilion - 0.3, width - 0.4, 0.0, depth, 1.3, MARBLE)
    box(0.0, depth / 2, podium + pavilion + 1.0, width - 0.4, depth, 0.5, LIME)
    face([(-width / 2 + 0.2, -0.1, podium + pavilion + 1.0), (width / 2 - 0.2, -0.1, podium + pavilion + 1.0),
          (0.0, -0.1, podium + pavilion + 3.6)], MARBLE)
    face([(0.0, -0.1, podium + pavilion + 3.6), (width / 2 - 0.2, -0.1, podium + pavilion + 1.0),
          (-width / 2 + 0.2, -0.1, podium + pavilion + 1.0)], MARBLE)
    box(0.0, depth - 0.4, podium + 0.3, width - 0.8, 0.3, pavilion - 0.6, VELVET)
    box(0.0, depth / 2 + 1.5, podium + 0.36, 2.2, 1.6, 0.6, MARBLE)
    box(0.0, depth / 2 + 2.1, podium + 0.96, 2.0, 0.3, 1.8, VELVET)
    for sign in (-1, 1):
        rod((sign * 1.0, depth / 2 + 0.8, podium + 0.96), (sign * 1.0, depth / 2 + 0.8, podium + 1.6), 0.07, BRONZE, 8)


def sand(spec: dict = SPEC) -> None:
    """Le sable de l'arène : l'ellipse intérieure, légèrement au-dessus du sol."""
    n = 96
    face([(spec["innerA"] * math.cos(j * math.tau / n), spec["innerB"] * math.sin(j * math.tau / n), 0.02)
          for j in range(n)], SAND)


def plinth() -> None:
    """Le socle de marbre d'une statue, dans un arc d'étage."""
    box(0.0, 0.0, 0.0, 1.9, 1.9, 0.3, MARBLE)
    box(0.0, 0.0, 0.3, 1.6, 1.6, 0.5, MARBLE)
    box(0.0, 0.0, 0.8, 1.8, 1.8, 0.14, MARBLE)


PIECES = {
    "col-arcade-1": lambda: arcade(0),
    "col-arcade-2": lambda: arcade(1),
    "col-arcade-3": lambda: arcade(2),
    "col-attic": attic,
    "col-gate": gate,
    "col-cavea": cavea,
    "col-loge": loge,
    "col-sand": sand,
    "col-plinth": plinth,
}


# --- Blender : matières, UV, export -----------------------------------------------------------

def blender_materials(textures: Path) -> list:
    materials = []
    for name, _, roughness, metallic in MATTERS_LIST:
        image = bpy.data.images.load(str(textures / f"{name}-albedo.png"), check_existing=True)
        image.pack()
        material = bpy.data.materials.new(name)
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        node = material.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = image
        material.node_tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        materials.append(material)
    return materials


def export_piece(name: str, build, out: Path, materials: list) -> dict:
    """Construit la pièce, projette ses UV au mètre, l'exporte en .glb ; retourne sa mesure."""
    reset()
    build()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(V, [], F)
    mesh.update()
    for material in materials:
        mesh.materials.append(material)
    uv = mesh.uv_layers.new(name="metres")
    for index, polygon in enumerate(mesh.polygons):
        polygon.material_index = M[index]
        polygon.use_smooth = S[index]
        scale = MATTERS_LIST[M[index]][1]
        normal = polygon.normal
        axis = max(range(3), key=lambda j: abs(normal[j]))
        axes = [j for j in range(3) if j != axis]
        # Une projection plane par face, en coordonnées absolues : deux faces coplanaires se
        # suivent sans couture, et la texture se répète tous les `scale` mètres.
        for li in polygon.loop_indices:
            p = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (p[axes[0]] / scale, p[axes[1]] / scale)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = out / f"{name}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_texcoords=True,
                              export_normals=True, export_materials="EXPORT", export_yup=True, export_animations=False,
                              export_cameras=False, export_lights=False)
    bounds = [[round(min(p[j] for p in V), 4) for j in range(3)], [round(max(p[j] for p in V), 4) for j in range(3)]]
    bpy.data.objects.remove(obj, do_unlink=True)
    measure = {"id": name, "faces": len(F), "boundsBlender": bounds}
    print("PRODUCED " + json.dumps(measure), flush=True)
    return measure


def blender_main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="")
    parser.add_argument("--textures", type=Path, default=TEXTURES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    materials = blender_materials(args.textures)
    wanted = {n for n in args.only.split(",") if n}
    for name, build in PIECES.items():
        if wanted and name not in wanted:
            continue
        export_piece(name, build, args.output, materials)


# --- Le pilote : Blender, puis le manifeste ---------------------------------------------------

def measure_glb(path: Path) -> dict:
    """Triangles, poids, empreinte et matières d'une pièce exportée."""
    data = path.read_bytes()
    length = struct.unpack_from("<I", data, 12)[0]
    document = json.loads(data[20:20 + length])
    primitives = document["meshes"][0]["primitives"]
    triangles = sum(document["accessors"][p["indices"]]["count"] // 3 for p in primitives)
    return {"triangles": triangles, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "materials": [m["name"] for m in document.get("materials", [])]}


def find_blender(option: str | None) -> Path:
    for candidate in (option, os.environ.get("BLENDER"), str(BLENDER_DEFAULT)):
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise SystemExit("build_colosseum : Blender introuvable (--blender, ou la variable BLENDER)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--only", default="", help="ne produire que ces pièces (noms séparés par des virgules)")
    parser.add_argument("--blender", default=None)
    parser.add_argument("--textures", type=Path, default=TEXTURES)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    for name, *_ in MATTERS_LIST:
        if not (args.textures / f"{name}-albedo.png").is_file():
            print(f"build_colosseum : texture absente {args.textures / (name + '-albedo.png')}", file=sys.stderr)
            return 1
    args.output.mkdir(parents=True, exist_ok=True)
    command = [str(find_blender(args.blender)), "--background", "--threads", "2", "--python-exit-code", "1",
               "--python", str(Path(__file__).resolve()), "--", "--only", args.only,
               "--textures", str(args.textures), "--output", str(args.output)]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = [json.loads(line[len("PRODUCED "):]) for line in result.stdout.splitlines() if line.startswith("PRODUCED ")]
    if result.returncode != 0 or not produced:
        print(result.stdout[-4000:], file=sys.stderr)
        print(result.stderr[-4000:], file=sys.stderr)
        print(f"build_colosseum : Blender a échoué (code {result.returncode})", file=sys.stderr)
        return 1
    manifest_path = args.output / "manifest.json"
    pieces = {}
    if manifest_path.exists():
        pieces = {p["id"]: p for p in json.loads(manifest_path.read_text(encoding="utf-8"))["pieces"]}
    bays = ring_bays()
    for measure in produced:
        name = measure["id"]
        enriched = measure_glb(args.output / f"{name}.glb")
        pieces[name] = {"id": name, "file": f"{name}.glb", **enriched, "boundsBlender": measure["boundsBlender"]}
        print(f"{name} : {enriched['triangles']} triangles, {enriched['bytes'] // 1024} Kio, "
              f"{', '.join(enriched['materials'])}")
    manifest = {
        "version": 1,
        "note": "Pièces du Colisée construites par scripts/assetsGeneration/build_colosseum.py (LOT-1012, LOT-1019) : "
                "ne pas modifier à la main. Repère de Blender : X est, Y nord, Z haut ; la façade d'une "
                "travée regarde -Y. Exporté en .glb Y vers le haut.",
        "spec": SPEC,
        "bayWidth": round(bay_width(), 4),
        "perimeter": round(perimeter(SPEC["a"], SPEC["b"]), 3),
        "ringBays": len(bays),
        "pieces": [pieces[k] for k in sorted(pieces)],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{manifest_path.relative_to(ROOT)} : {len(pieces)} pièces")
    return 0


if __name__ == "__main__":
    if bpy is not None and "--" in sys.argv:
        blender_main(sys.argv[sys.argv.index("--") + 1:])
    else:
        raise SystemExit(main())
