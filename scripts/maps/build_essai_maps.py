#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit les deux cartes d'essai de l'exploration (LOT-1016), chacune sous ses deux formes.

Le LOT-1016 fait jouer une carte de Core — ses portails, ses PNJ, ses lumières, posés sur des
cases — dans une carte du moteur. Tant que le format de carte du LOT-1018 n'existe pas, les deux
formes s'écrivent à part : la carte de Core (`Levels/<id>.json`, la grille et les entités) et la
description de scène que `build_scene_unreal.py` construit (`Scenes/<scène>.json`, les maillages).
Ce script les tire **du même plan**, pour qu'un mur de l'une soit un mur de l'autre.

Les deux cartes rejouent, en petit, le début de la quête « Des pommes pour l'arène » avec ses
dialogues et sa quête livrés (`Source/Elements/World`) :

- `essai/etals` : la mère à son étal, l'enfant qui n'y revient qu'une fois libéré, une lanterne
  devant un pan de mur (une lumière de nuit porte une ombre), le portail vers le parvis ;
- `essai/parvis` : le garde et l'enfant, que l'acceptation de la quête fait paraître, la zone qui
  déclenche le garde, un passage condamné, un passage que la libération de l'enfant ouvre.

Elles ne lisent aucun kit d'assets : sol, mur et pantin sont les données d'essai du dépôt
(`build_mesh_fixture.py`). Les cartes de Core vont sous `Source/Test/Fixtures/Exploration/Levels`,
hors des cartes du jeu ; la description de scène nomme ce dossier (`level.root`).

Usage :
    python scripts/maps/build_essai_maps.py           # écrit les quatre fichiers
    python scripts/maps/build_essai_maps.py --check   # vérifie qu'ils sont à jour
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEVELS = ROOT / "Source" / "Test" / "Fixtures" / "Exploration" / "Levels"
SCENES = ROOT / "Source" / "Elements" / "Scenes"
LEVELS_ROOT = "Source/Test/Fixtures/Exploration/Levels"

CELL = 1.5  # le côté d'une case, en mètres (`core::METERS_PER_TILE`)
WALL = "#"

FLOOR_MESH = "Scene/ilot/floor.glb"
WALL_MESH = "Scene/ilot/wall.glb"
PUPPET = "Npc/pantin/pantin.glb"

# Le plan d'une carte : `#` un mur, tout autre signe une case libre. Les lettres repèrent les
# entités, nommées dans `marks` ; une case libre sans entité est un point.
ETALS_PLAN = """
################
#..............#
#..M...........#
#..c.....L.....#
#........##....#
#............A.P
#..............#
#..............#
#..E...........#
#..............#
#..............#
################
"""

PARVIS_PLAN = """
#######S########
#..............#
#..............#
#.......Gc.....#
#..............#
P.A............#
#..............#
#.........L....#
#..............#
#..............R
#..............#
################
"""

LANTERN = {"color": "#ffbe7a", "radius": 4, "height": 22, "intensity": 100, "flicker": False, "always": False}
# La présence de l'enfant et du garde suit la quête, comme sur les cartes livrées.
WITH_GUARD = {"presenceFlag": "quete.pommes", "presenceTest": "equals", "presenceValue": "acceptee|persuasion-echouee"}

MAPS = {
    "essai/etals": {
        "scene": "essai-1016-etals",
        "name": "Essai1016Etals",
        "plan": ETALS_PLAN,
        "marks": {
            "E": {"entry": True},
            "M": {"type": "npc", "dialogue": "mere", "figure": "pantin", "heading": 180.0},
            "c": {"type": "npc", "dialogue": "enfant", "figure": "pantin", "heading": 180.0,
                  "presenceFlag": "quete.pommes", "presenceTest": "equals", "presenceValue": "enfant-libere"},
            "A": {"type": "spawnPoint", "name": "from-parvis"},
            "P": {"type": "portal", "arrival": "from-etals", "requiresFlag": "", "sealed": False,
                  "targetMap": "essai/parvis"},
            "L": {"type": "light", **LANTERN},
        },
        "zones": [],
        "shots": [
            {"id": "etals", "target": [12.0, 1.0, 9.0], "heading": 0.0, "pitch": 42.0, "distance": 24.0,
             "comment": "La carte entière depuis le sud, au cadrage du joueur : le groupe à l'entrée, la mère à son étal, le pan de mur et sa lanterne, le portail à l'est."},
            {"id": "lanterne", "target": [14.25, 1.0, 6.0], "heading": 205.0, "pitch": 28.0, "distance": 10.0,
             "comment": "La lanterne et le pan de mur, depuis le nord-est : à 22 h, la face du mur tournée vers elle est éclairée, le sol derrière lui est dans son ombre."},
        ],
    },
    "essai/parvis": {
        "scene": "essai-1016-parvis",
        "name": "Essai1016Parvis",
        "plan": PARVIS_PLAN,
        "marks": {
            "A": {"type": "spawnPoint", "name": "from-etals", "entry": True},
            "P": {"type": "portal", "arrival": "from-parvis", "requiresFlag": "", "sealed": False,
                  "targetMap": "essai/etals"},
            "G": {"type": "npc", "dialogue": "garde", "figure": "pantin", "heading": 270.0, **WITH_GUARD},
            "c": {"type": "npc", "dialogue": "enfant", "figure": "pantin", "heading": 270.0, **WITH_GUARD},
            "S": {"type": "portal", "arrival": "", "requiresFlag": "", "sealed": True, "targetMap": ""},
            "R": {"type": "portal", "arrival": "from-parvis", "sealed": False, "targetMap": "essai/etals",
                  "requiresFlag": "quest/pommes/step/enfant-libere"},
            "L": {"type": "light", **LANTERN},
        },
        # La zone du parvis : y entrer, la quête acceptée, fait parler le garde (LOT-126).
        "zones": [
            {"type": "zone", "x": 5, "y": 2, "width": 7, "height": 4, "name": "parvis",
             "presenceFlag": "quete.pommes", "presenceTest": "equals", "presenceValue": "acceptee",
             "triggerDialogue": "garde", "triggerOnce": False},
        ],
        "shots": [
            {"id": "parvis", "target": [12.0, 1.0, 9.0], "heading": 0.0, "pitch": 42.0, "distance": 24.0,
             "comment": "La carte entière depuis le sud : le point d'arrivée à l'ouest, le passage condamné au nord, celui que la quête ouvre à l'est."},
        ],
    },
}

LIGHTING = {
    "comment": "Les réglages de la porte (porte-1012.json), repris tels quels.",
    "lampCandelas": 60.0,
    "fireCandelas": 30.0,
    "sunScale": 1.8,
    "ambientScale": 0.45,
    "skyLuminance": 3.0,
    "exposureBias": 0.0,
    "fog": {"density": 0.004, "falloff": 0.05, "volumetric": True},
    "post": {"bloom_intensity": 0.6, "vignette_intensity": 0.3},
}


def rows_of(plan: str) -> list[str]:
    rows = plan.strip().splitlines()
    if len({len(row) for row in rows}) != 1:
        raise ValueError("plan : toutes les lignes n'ont pas la même longueur")
    return rows


def centre(column: int, row: int) -> list[float]:
    """Le centre d'une case dans le repère de la scène : X vers l'est, Z vers le sud, en mètres."""
    return [(column + 0.5) * CELL, 0.0, (row + 0.5) * CELL]


def entities_of(spec: dict) -> tuple[list[dict], tuple[int, int]]:
    """Les entités d'une carte, dans l'ordre du plan puis les zones, et la case d'entrée."""
    rows = rows_of(spec["plan"])
    entities: list[dict] = []
    entry = None
    for row, line in enumerate(rows):
        for column, sign in enumerate(line):
            mark = spec["marks"].get(sign)
            if mark is None:
                if sign not in (WALL, "."):
                    raise ValueError(f"plan : signe « {sign} » sans entité")
                continue
            if mark.get("entry"):
                entry = (column, row)
            if "type" not in mark:
                continue
            properties = {key: value for key, value in mark.items() if key not in ("type", "entry", "heading")}
            entities.append({"type": mark["type"], "x": column, "y": row, **properties, "heading": mark.get("heading")})
    for zone in spec["zones"]:
        entities.append({**zone, "heading": None})
    if entry is None:
        raise ValueError("plan : aucune entrée")
    for number, entity in enumerate(entities, start=1):
        entity["id"] = f"e{number}"
    return entities, entry


def level_text(identifier: str, spec: dict) -> str:
    """La carte de Core : la grille de collision, l'entrée, les entités (format v4)."""
    rows = rows_of(spec["plan"])
    entities, entry = entities_of(spec)
    tiles = [{"x": column, "y": row, "type": "wall"}
             for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == WALL]
    tiles.append({"x": entry[0], "y": entry[1], "type": "entry"})
    written = []
    for entity in entities:
        fields = {"id": entity["id"], "type": entity["type"], "x": entity["x"], "y": entity["y"]}
        fields |= {key: entity[key] for key in sorted(entity) if key not in ("id", "type", "x", "y", "heading")}
        # Une propriété par ligne : la forme canonique de l'éditeur de cartes.
        written.append("\n".join("    " + line for line in json.dumps(fields, indent=2, ensure_ascii=False).splitlines()))
    tile_lines = ",\n".join("    " + json.dumps(tile) for tile in tiles)
    return f"""{{
  "version": 4,
  "name": "{identifier}",
  "width": {len(rows[0])},
  "height": {len(rows)},
  "nextEntityId": {len(entities) + 1},
  "tiles": [
{tile_lines}
  ],
  "entities": [
{",\n".join(written)}
  ]
}}
"""


def scene_text(identifier: str, spec: dict) -> str:
    """La description de scène : le sol, les murs, les quatre du groupe, les PNJ, les cadrages."""
    rows = rows_of(spec["plan"])
    entities, entry = entities_of(spec)
    width, height = len(rows[0]) * CELL, len(rows) * CELL
    walls = [{"id": f"mur/{column},{row}", "folder": "murs", "mesh": WALL_MESH, "position": centre(column, row),
              "yaw": 0.0, "scale": 1.0}
             for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == WALL]
    puppet = {"mesh": PUPPET, "idle": "idle", "walk": "walk", "walkSpeed": 3.0}
    # Le groupe : sa place est celle que Core donne au lancement (l'entrée, ou le point d'arrivée
    # du portail) ; la scène le pose à l'entrée pour qu'il existe.
    characters = [{"id": f"groupe-{rank + 1}", **puppet, "position": centre(*entry), "heading": 90.0, "party": rank}
                  for rank in range(4)]
    characters += [{"id": f"pnj-{entity['id']}", **puppet, "position": centre(entity["x"], entity["y"]),
                    "heading": entity["heading"], "entity": entity["id"]}
                   for entity in entities if entity["type"] == "npc"]
    scene = {
        "version": 1,
        "name": spec["name"],
        "comment": (f"Carte d'essai de l'exploration (LOT-1016), écrite par scripts/maps/build_essai_maps.py, jamais à "
                    f"la main : la carte de Core « {identifier} » ({LEVELS_ROOT}) et cette scène viennent du même plan. "
                    f"Elle ne lit aucun kit d'assets. Même repère et mêmes champs que porte-1012.json."),
        "map": f"/Game/Maps/Levels/{identifier}",
        "assetsRoot": "Source/Test/Fixtures/Meshes/Assets",
        "level": {"id": identifier, "root": LEVELS_ROOT, "origin": [0.0, 0.0], "cell": CELL},
        "daylight": "Common/Lighting/daylight.json",
        "frameReference": "Scene/socle/repere.glb",
        "lighting": LIGHTING,
        "ground": {"colour": "#8f7d62", "size": 4000.0, "height": -0.02},
        "fills": [{"id": "sol", "meshes": [FLOOR_MESH], "cell": CELL, "areas": [[0.0, 0.0, width, height]]}],
        "objects": walls,
        "characters": characters,
        "navigation": {"area": [0.0, 0.0, width, height], "height": 4.0},
        "shots": spec["shots"],
        "hours": ["12:00", "22:00"],
    }
    head = json.dumps({key: value for key, value in scene.items() if key not in ("objects", "characters", "shots")},
                      indent=2, ensure_ascii=False)
    # Une ligne par objet, par personnage, par cadrage : le fichier se relit et se compare.
    lists = "".join(
        f',\n  "{key}": [\n' + ",\n".join("    " + json.dumps(item, ensure_ascii=False) for item in scene[key]) + "\n  ]"
        for key in ("objects", "characters", "shots"))
    return head[:-2] + lists + "\n}\n"


def files() -> dict[Path, str]:
    written: dict[Path, str] = {}
    for identifier, spec in MAPS.items():
        written[LEVELS / f"{identifier}.json"] = level_text(identifier, spec)
        written[SCENES / f"{spec['scene']}.json"] = scene_text(identifier, spec)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="vérifie que les fichiers sont à jour, sans rien écrire")
    arguments = parser.parse_args()

    stale = []
    for path, text in files().items():
        relative = path.relative_to(ROOT).as_posix()
        if arguments.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(relative)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        print(f"écrit {relative}")
    if stale:
        print("cartes d'essai périmées : " + ", ".join(stale), file=sys.stderr)
        print("relancer scripts/maps/build_essai_maps.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
