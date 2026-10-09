#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit la carte de la porte (LOT-1012, LOT-1018) : le parvis d'Arenarea devant le Colisée, et le
Colisée en préfabriqué.

Le Colisée n'est pas une coque d'un seul tenant : `build_colosseum.py` en produit les pièces
(travées des trois ordres, attique, porte, quart de gradins, loge, sable, socle) à l'échelle du
Colisée de Rome, et ce script les **pose** — 80 travées par ordre sur l'ellipse, la porte plein
sud, les gradins quatre fois par symétrie — puis y ajoute ce qui vient d'ailleurs :

- les quatorze dieux **au maître** (`Master/Statues/`), dans les arcs du deuxième ordre de part et
  d'autre de la porte, chacun sur son socle, à 5,2 m de haut ; les deux lions gardiens sur les
  tours de la porte ;
- les bannières du kit de l'Arena of Fate, pendues à l'attique au-dessus des statues, l'empire
  au-dessus de la porte ; le culte des Sans-Dieux n'y flotte pas ;
- les feux : deux vasques à la porte, et sur le podium tout autour de l'arène, pour la nuit.

Deux sorties, au format de carte v5 (`jadg_map.py`) :

- le **préfabriqué** du Colisée, `Source/Elements/Editor/Prefabs/central-empire/capital/arenarea/colisee.json`
  (format `jadg-prefab`), origine au centre de l'arène, au niveau du sable ;
- la **carte** de la porte, `Source/Elements/Levels/porte-1012.json` : le parvis, ses six façades
  (la famille témoin du LOT-1019 : six exemplaires de la façade au maître, quatre au sud et deux qui
  bordent la ruelle), sa fontaine, ses arbres, ses lampes, son dallage, le Colisée posé, le lion
  qui fait sa ronde, les cadrages — et **la grille que Core joue** (la dette du LOT-1016) : tirée
  de la même géométrie, l'ellipse du Colisée et l'emprise des façades sont des murs, la ruelle hors
  du dallage aussi ; le groupe entre au milieu du parvis. `build_level.py` construit le niveau.

Repère de la carte : x vers l'est, y vers le sud, z vers le haut, en mètres ; `yaw` tourne le sud
vers l'est. Le repère de Blender des pièces (x est, y nord, z haut) s'y ramène par y = −y_blender.

Usage :
    python scripts/maps/build_gate_scene.py            # écrit le préfabriqué et la carte
    python scripts/maps/build_gate_scene.py --check    # code non nul si un fichier suivi diffère
"""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "assetsGeneration"))
sys.path.insert(0, str(ROOT / "scripts" / "maps"))
import build_colosseum as colosseum  # noqa: E402
import jadg_map  # noqa: E402

ELEMENTS = ROOT / "Source" / "Elements"
ASSETS = ELEMENTS / "Assets"
BUILT = "Built/colisee"
KIT = "Regions/central-empire/capital/arenarea/arena-of-fate/Scene"
MASTER_MANIFEST = ASSETS / "Master" / "manifest.json"
PREFAB_ID = "central-empire/capital/arenarea/colisee"
OUTPUT = ELEMENTS / "Editor" / "Prefabs" / f"{PREFAB_ID}.json"
MAP_OUTPUT = ELEMENTS / "Levels" / "porte-1012.json"
PALAZZO = "Master/Scenery/arenarea-palazzo-terracotta.glb"

# Les dieux, dans l'ordre où ils se posent de part et d'autre de la porte (du plus proche au plus
# loin, à l'est puis à l'ouest) : les quatorze statues du kit de l'Arena of Fate, au maître.
GODS = ["statue-bauron", "statue-tamera", "statue-lumina", "statue-bas", "statue-duality", "statue-oigridh",
        "statue-dorsi", "statue-ba-ka", "statue-fruitful", "statue-aibidh", "statue-fumetsu",
        "statue-nature-spirits", "statue-glorious-one", "statue-breith"]
# Les bannières, de la porte vers les flancs ; l'empire au-dessus de la porte.
BANNERS = ["banner-empire", "banner-tanarean-empire", "banner-allied-forces", "banner-arcanum", "banner-darkall",
           "banner-freelands", "banner-bennet", "banner-kolbjorn", "banner-mage-tower", "banner-seashores",
           "banner-sindile", "banner-stravian", "banner-storm-islands", "banner-taii-maku", "banner-kepesh",
           "banner-tsvetan", "banner-yama"]
STATUE_HEIGHT = 5.2      # la hauteur d'un dieu dans son arc, en mètres
LION_HEIGHT = 5.0        # celle d'un lion sur sa tour
BANNER_SCALE = 2.1       # une bannière du kit fait 3,1 × 4 m ; pendue à l'attique, 6,6 × 8,4 m
PODIUM_FIRES = 10        # un feu sur le podium toutes les N travées
FIRE = {"color": "#ffb866", "radius": 13.0, "height": 2.2, "flicker": True, "always": True}


class GateSceneError(RuntimeError):
    """Une donnée d'entrée manque ou ne se relie pas."""


def glb_bounds(path: Path) -> tuple[list[float], list[float]]:
    """La boîte englobante d'un .glb, lue dans ses accesseurs."""
    with path.open("rb") as stream:
        stream.read(12)
        length, _ = struct.unpack("<II", stream.read(8))
        document = json.loads(stream.read(length))
    low, high = [math.inf] * 3, [-math.inf] * 3
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            accessor = document["accessors"][primitive["attributes"]["POSITION"]]
            low = [min(low[k], accessor["min"][k]) for k in range(3)]
            high = [max(high[k], accessor["max"][k]) for k in range(3)]
    return low, high


def scene_point(x: float, y: float, z: float) -> list[float]:
    """Un point de Blender (x est, y nord, z haut) dans le repère de la carte (x est, y sud, z haut)."""
    return [round(x, 4), round(-y, 4), round(z, 4)]


def piece(name: str) -> str:
    return f"{BUILT}/{name}.glb"


def placed(identifier: str, mesh: str, x: float, y: float, z: float, yaw: float = 0.0, scale: float = 1.0,
           **extra) -> dict:
    item = {"id": identifier, "mesh": mesh, "position": scene_point(x, y, z), "yaw": round(yaw % 360.0, 4),
            "scale": round(scale, 5)}
    item.update(extra)
    return item


def build(assets: Path = ASSETS) -> dict:
    spec = colosseum.SPEC
    bays = colosseum.ring_bays(spec)
    width = colosseum.bay_width(spec)
    n = spec["bays"]
    master = {p["id"]: p for p in json.loads((assets / "Master" / "manifest.json").read_text(encoding="utf-8"))["pieces"]}
    gate_bays = {k % n for k in range(-(spec["gateBays"] // 2), spec["gateBays"] // 2 + 1)}
    objects: list[dict] = []

    # Les travées : trois ordres puis l'attique, la porte à la place des travées du sud.
    floors = [0.0]
    for height in spec["orders"]:
        floors.append(floors[-1] + height)
    for bay in bays:
        k = bay["index"]
        cx, cy = bay["centre"]
        for order in range(3):
            if k in gate_bays:
                continue
            objects.append(placed(f"ordre-{order + 1}/travee-{k:02d}", piece(f"col-arcade-{order + 1}"),
                                  cx, cy, floors[order], bay["yaw"]))
        objects.append(placed(f"attique/travee-{k:02d}", piece("col-attic"), cx, cy, floors[3], bay["yaw"]))
    objects.append(placed("porte/porte", piece("col-gate"), 0.0, -spec["b"], 0.0, 0.0))

    # Les gradins, quatre fois par symétrie ; la loge au nord ; le sable.
    for identifier, yaw, mirrored in (("nord-est", 0.0, False), ("nord-ouest", 0.0, True),
                                      ("sud-ouest", 180.0, False), ("sud-est", 180.0, True)):
        item = placed(f"gradins/{identifier}", piece("col-cavea"), 0.0, 0.0, 0.0, yaw)
        if mirrored:
            item["mirrored"] = True
        objects.append(item)
    objects.append(placed("loge/loge", piece("col-loge"), 0.0, spec["innerB"], 0.0, 0.0))
    objects.append(placed("sol/sable", piece("col-sand"), 0.0, 0.0, 0.0, 0.0))

    # Les dieux dans les arcs du deuxième ordre, de part et d'autre de la porte.
    inward = spec["depth"] / 2 + 0.9
    half = len(GODS) // 2
    slots = [k for pair in zip(range(2, 2 + half), range(n - 2, n - 2 - half, -1)) for k in pair]
    for god, k in zip(GODS, slots):
        reference = master.get(f"Statues/{god}")
        if reference is None:
            raise GateSceneError(f"{god} : absent du manifeste du maître")
        low, high = glb_bounds(assets / reference["file"])
        scale = STATUE_HEIGHT / (high[1] - low[1])
        bay = bays[k]
        nx, ny = bay["normal"]
        x, y = bay["centre"][0] - nx * inward, bay["centre"][1] - ny * inward
        floor = floors[1]
        objects.append(placed(f"dieux/socle-{god}", piece("col-plinth"), x, y, floor, bay["yaw"]))
        objects.append(placed(f"dieux/{god}", reference["file"], x, y, floor + 0.94 - low[1] * scale, bay["yaw"], scale,
                              master=reference["id"], meshy=f"{reference['meshy_name']}_{reference['meshy_id']}"))

    # Les lions gardiens sur les tours de la porte.
    lion = master.get("Statues/portal-guardian-lion")
    if lion is None:
        raise GateSceneError("Statues/portal-guardian-lion : absent du manifeste du maître")
    low, high = glb_bounds(assets / lion["file"])
    scale = LION_HEIGHT / (high[1] - low[1])
    gate_width = width * spec["gateBays"]
    tower = (gate_width - spec["tunnelWidth"]) / 2
    tower_top = sum(spec["orders"]) + 1.42
    tower_y = -spec["b"] + (spec["depth"] - spec["gateProtrusion"]) / 2
    for side, sign in (("ouest", -1), ("est", 1)):
        objects.append(placed(f"gardiens/lion-{side}", lion["file"], sign * (gate_width - tower) / 2, tower_y,
                              tower_top - low[1] * scale, 0.0, scale, master=lion["id"],
                              meshy=f"{lion['meshy_name']}_{lion['meshy_id']}"))

    # Les bannières à l'attique : l'empire au-dessus de la porte, les autres de part et d'autre.
    slots = [0] + [k for pair in zip(range(1, 1 + len(BANNERS) // 2), range(n - 1, n - 1 - len(BANNERS) // 2, -1))
                   for k in pair]
    for banner, k in zip(BANNERS, slots):
        bay = bays[k]
        nx, ny = bay["normal"]
        x, y = bay["centre"][0] + nx * 0.55, bay["centre"][1] + ny * 0.55
        objects.append(placed(f"bannieres/{banner}", f"{KIT}/{banner}.glb", x, y, floors[3] + 3.4, bay["yaw"],
                              BANNER_SCALE))

    # Les feux : deux vasques devant la porte, et sur le podium tout autour.
    for side, sign in (("ouest", -1), ("est", 1)):
        objects.append(placed(f"feux/porte-{side}", f"{KIT}/af-pyre.glb", sign * (gate_width / 2 + 1.6),
                              -spec["b"] - spec["gateProtrusion"] - 1.2, 0.0, 0.0, 2.2, light=FIRE))
    for k in range(0, n, PODIUM_FIRES):
        angle = math.radians(270.0 + k * 360.0 / n)
        if k % n in gate_bays or (k + n // 2) % n in gate_bays:
            continue
        objects.append(placed(f"feux/podium-{k:02d}", f"{KIT}/af-pyre.glb",
                              (spec["innerA"] + 2.0) * math.cos(angle), (spec["innerB"] + 2.0) * math.sin(angle),
                              spec["podium"] + spec["rise"], 0.0, 1.5, light=FIRE))
    return {
        "format": jadg_map.PREFAB_FORMAT,
        "version": 1,
        "name": "colisee",
        "comment": "Sortie de scripts/maps/build_gate_scene.py (LOT-1012, LOT-1018) : ne pas modifier à la main. "
                   "Repère : x est, y sud, z haut, en mètres ; yaw tourne le sud vers l'est ; origine au centre "
                   "de l'arène, au niveau du sable. Le Colisée de Rome : 189 × 156 m, 48 m, 80 travées ; ses "
                   "pièces : Assets/Built/colisee/manifest.json.",
        "place": "central-empire/capital/arenarea",
        "bayWidth": round(width, 4),
        "spec": spec,
        "objects": objects,
    }


# --- La carte de la porte ----------------------------------------------------------------------

# Le parvis, tel que le LOT-1012 l'a composé (repère de la carte). Les façades sont mises à leur
# hauteur ; leur emprise au sol, mesurée sur le maillage, devient des murs de la grille de Core.
PARVIS_OBJECTS = [
    {"id": "facade-sud-1", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [-18.6, 52.0, 0.0], "yaw": 0.0, "height": 12.0, "provisional": "hauteur non mesurée : aucune cote de la commande ; la famille témoin du LOT-1019, six exemplaires de la seule façade au maître, en attendant les six variantes commandées"},
    {"id": "facade-sud-2", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [-7.6, 52.0, 0.0], "yaw": 0.0, "height": 12.0},
    {"id": "facade-sud-3", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [7.6, 52.0, 0.0], "yaw": 0.0, "height": 12.0},
    {"id": "facade-sud-4", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [18.6, 52.0, 0.0], "yaw": 0.0, "height": 12.0},
    {"id": "facade-ruelle", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [-7.6, 66.0, 0.0], "yaw": 90.0, "height": 12.0},
    {"id": "facade-ruelle-est", "mesh": "Master/Scenery/arenarea-palazzo-terracotta.glb", "position": [7.6, 66.0, 0.0], "yaw": 270.0, "height": 12.0},
    {"id": "fontaine", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-fountain.glb", "position": [0.0, 34.5, 0.0], "yaw": 0.0, "scale": 1.0},
    {"id": "champion", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-champion-anonyme.glb", "position": [-12.0, 27.0, 0.0], "yaw": 0.0, "scale": 1.0},
    {"id": "char", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-char-de-course.glb", "position": [13.5, 30.0, 0.0], "yaw": 30.0, "scale": 1.0},
    {"id": "enseigne", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-enseigne-brasseur.glb", "position": [2.6, 58.5, 0.0], "yaw": 90.0, "scale": 1.0},
    {"id": "cypres-o-1", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [-28.5, 22.5, 0.0], "yaw": 0.0, "scale": 1.0},
    {"id": "cypres-o-2", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [-28.5, 31.5, 0.0], "yaw": 70.0, "scale": 1.0},
    {"id": "cypres-o-3", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [-28.5, 40.5, 0.0], "yaw": 140.0, "scale": 1.0},
    {"id": "cypres-e-1", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [28.5, 22.5, 0.0], "yaw": 200.0, "scale": 1.0},
    {"id": "cypres-e-2", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [28.5, 31.5, 0.0], "yaw": 270.0, "scale": 1.0},
    {"id": "cypres-e-3", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-cypres.glb", "position": [28.5, 40.5, 0.0], "yaw": 330.0, "scale": 1.0},
    {"id": "arbre-o", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-arbre-ombrage.glb", "position": [-21.0, 43.5, 0.0], "yaw": 20.0, "scale": 1.0},
    {"id": "arbre-e", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-meshy-arbre-ombrage.glb", "position": [21.0, 43.5, 0.0], "yaw": 110.0, "scale": 1.0},
    {"id": "lampe-1", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [-6.0, 21.0, 0.0], "yaw": 0.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-2", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [6.0, 21.0, 0.0], "yaw": 0.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-3", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [-18.0, 30.0, 0.0], "yaw": 90.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-4", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [18.0, 30.0, 0.0], "yaw": 90.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-5", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [-9.0, 43.5, 0.0], "yaw": 0.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-6", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [9.0, 43.5, 0.0], "yaw": 0.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-ruelle-1", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [-2.4, 60.0, 0.0], "yaw": 90.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
    {"id": "lampe-ruelle-2", "mesh": "Regions/central-empire/capital/arenarea/Scene/ar-lamp.glb", "position": [2.4, 70.5, 0.0], "yaw": 90.0, "scale": 1.0, "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}},
]
# Le lion de la porte garde son maillage lié du kit et sa ronde jusqu'au LOT-1025.
LION = {"id": "lion", "mesh": "Regions/central-empire/capital/arenarea/arena-of-fate/Characters/lion/lion.glb", "position": [7.5, 39.0, 0.0], "heading": 270.0, "idle": "idle", "walk": "walk", "walkSpeed": 3.0, "patrol": [[7.5, 39.0, 0.0], [-7.5, 39.0, 0.0], [-7.5, 24.0, 0.0], [7.5, 24.0, 0.0]]}
SHOTS = [
    {"id": "parvis", "target": [0.0, 24.0, 14.0], "heading": 0.0, "pitch": 9.0, "distance": 118.0, "comment": "Depuis le sud, au-dessus des toits du quartier : le parvis entier et la façade du Colisée d'un bord à l'autre, les maisons donnant l'échelle."},
    {"id": "porte", "target": [0.0, 19.0, 13.0], "heading": 0.0, "pitch": 3.0, "distance": 34.0, "comment": "Depuis le parvis, à hauteur d'homme ou presque : la porte, ses lions, les dieux dans les arcs."},
    {"id": "ruelle", "target": [0.0, 62.0, 2.5], "heading": 180.0, "pitch": 8.0, "distance": 11.0},
    {"id": "facades", "target": [0.0, 50.0, 3.0], "heading": 180.0, "pitch": 35.0, "distance": 30.0, "comment": "La famille témoin (LOT-1019) au cadrage du joueur : depuis le parvis, dans les bornes de la caméra (inclinaison de 25 à 70°, 4 à 120 m), les façades du sud vues du côté du parvis."},
]
LIGHTING = {"comment": "Réglages provisoires de la porte, à juger sur les captures. lampCandelas, fireCandelas : intensité d'une lampe et d'un feu, pour une exposition fixe de 1. sunScale, ambientScale : ce par quoi le soleil et la lumière du ciel de la table du jour sont multipliés (la table est écrite pour un rendu sans lumière indirecte). skyLuminance : éclaircissement du ciel visible. fog : brume de hauteur. post : réglages de post-traitement du moteur, par leur nom.", "lampCandelas": 60.0, "fireCandelas": 30.0, "sunScale": 1.8, "ambientScale": 0.45, "skyLuminance": 3.0, "exposureBias": 0.0, "fog": {"density": 0.004, "falloff": 0.05, "volumetric": True}, "post": {"bloom_intensity": 0.6, "vignette_intensity": 0.3}}
GROUND = {"comment": "Le sol lointain, sous le dallage : un plan uni. Couleur provisoire.", "colour": "#8f7d62", "size": 4000.0, "height": -0.02}
FILL = {"id": "dallage", "comment": "Le dallage du parvis : les trois dalles du kit d'Arenarea, tirées par case, jusqu'au pied du Colisée (l'ellipse exclue est la sienne, plus 1 m).", "meshes": ["Regions/central-empire/capital/arenarea/Scene/ar-paving-1.glb", "Regions/central-empire/capital/arenarea/Scene/ar-paving-2.glb", "Regions/central-empire/capital/arenarea/Scene/ar-paving-3.glb"], "cell": 1.5, "areas": [[-78.0, -10.5, 78.0, 57.0], [-15.0, 57.0, 15.0, 78.0]], "excludeEllipses": [[0.0, -60.5, 95.5, 79.0]]}
COLISEE_CENTRE = [0.0, -60.5, 0.0]
# Le parvis que Core joue : du pied du Colisée à la ruelle, d'un bord du dallage à l'autre.
GRID_ORIGIN = [-78.0, -10.5]
GRID_SIZE = (104, 59)          # 156 m sur 88,5 m, des cases de 1,5 m
ENTRY = (0.0, 27.0)            # là où le groupe se tenait : au milieu du parvis, devant la fontaine


def footprint_box(item: dict, low: list[float], high: list[float]) -> tuple[float, float, float, float]:
    """L'emprise au sol d'un objet mis à sa hauteur, tourné d'un quart de tour au plus."""
    scale = item["height"] / (high[1] - low[1])
    half_x, half_y = (high[0] - low[0]) * scale / 2, (high[2] - low[2]) * scale / 2
    cx = item["position"][0] + (high[0] + low[0]) * scale / 2
    cy = item["position"][1] + (high[2] + low[2]) * scale / 2
    if round(item.get("yaw", 0.0)) % 180 == 90:
        half_x, half_y = half_y, half_x
    return cx - half_x, cy - half_y, cx + half_x, cy + half_y


def gate_map(assets: Path = ASSETS) -> dict:
    """La carte de la porte : ce que le moteur construit et la grille que Core joue, d'un plan."""
    palazzo = assets / PALAZZO
    if not palazzo.is_file():
        raise GateSceneError(f"{PALAZZO} : absent (le maître des façades)")
    low, high = glb_bounds(palazzo)
    boxes = [footprint_box(item, low, high) for item in PARVIS_OBJECTS if item["mesh"] == PALAZZO]
    ellipse = FILL["excludeEllipses"][0]
    tiles = []
    columns, rows = GRID_SIZE
    entry = (int((ENTRY[0] - GRID_ORIGIN[0]) // jadg_map.CELL), int((ENTRY[1] - GRID_ORIGIN[1]) // jadg_map.CELL))
    for row in range(rows):
        for column in range(columns):
            x, y = jadg_map.cell_centre(column, row, GRID_ORIGIN)[:2]
            colosseum_side = ((x - ellipse[0]) / ellipse[2]) ** 2 + ((y - ellipse[1]) / ellipse[3]) ** 2 < 1.0
            lane = y > 57.0 and abs(x) > 15.0
            facade = any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in boxes)
            if (column, row) == entry:
                tiles.append({"x": column, "y": row, "type": "entry"})
            elif colosseum_side or lane or facade:
                tiles.append({"x": column, "y": row, "type": "wall"})
    return {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": "Porte1012",
        "comment": "La carte de la porte (LOT-1012, LOT-1018) : le parvis d'Arenarea devant le Colisée. Sortie de "
                   "scripts/maps/build_gate_scene.py, jamais à la main : ce que build_level.py construit et la grille "
                   "que Core joue viennent de la même géométrie (l'ellipse du Colisée, l'emprise des façades).",
        "place": "central-empire/capital/arenarea",
        "width": columns,
        "height": rows,
        "origin": GRID_ORIGIN,
        "nextEntityId": 1,
        "tiles": tiles,
        "entities": [],
        "objects": PARVIS_OBJECTS,
        "fills": [FILL],
        "prefabs": [{"id": "colisee", "prefab": PREFAB_ID, "position": COLISEE_CENTRE, "yaw": 0.0, "scale": 1.0,
                     "comment": "Le Colisée en pièces modulaires, aux dimensions de celui de Rome (189 × 156 m, 48 m ; "
                                "décision de l'auteur, 8 octobre 2026). Son centre est à y = -60,5 : sa façade sud à "
                                "y = 17,5, sa porte à 19."}],
        "characters": [LION],
        "party": {"appearances": list(jadg_map.HEROES), "walkSpeed": 3.0, "heading": 180.0},
        "lighting": LIGHTING,
        "daylight": jadg_map.DAYLIGHT,
        "ground": GROUND,
        "navigation": {"area": [-78.0, -84.0, 78.0, 78.0], "height": 6.0},
        "shots": SHOTS,
        "hours": ["12:00", "22:00"],
    }


def render(scene: dict) -> str:
    return jadg_map.dumps(scene)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="comparer au fichier suivi sans l'écrire")
    args = parser.parse_args(argv)
    try:
        outputs = {OUTPUT: render(build()), MAP_OUTPUT: render(gate_map())}
    except (GateSceneError, OSError, KeyError) as error:
        print(f"build_gate_scene : {error}", file=sys.stderr)
        return 1
    stale = False
    for path, text in outputs.items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                print(f"build_gate_scene : {path.relative_to(ROOT)} n'est pas à jour", file=sys.stderr)
                stale = True
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"{path.relative_to(ROOT)} : {len(json.loads(text)['objects'])} objets")
    return 1 if stale else 0


if __name__ == "__main__":
    raise SystemExit(main())
