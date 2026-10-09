#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit les cartes d'essai de l'exploration (LOT-1016) et l'arène du combat (LOT-1017) : trois
cartes de Core sous leurs deux formes.

Le LOT-1016 fait jouer une carte de Core — ses portails, ses PNJ, ses lumières, posés sur des
cases — dans une carte du moteur. Tant que le format de carte du LOT-1018 n'existe pas, les deux
formes s'écrivent à part : la carte de Core (`Levels/<id>.json`, la grille et les entités) et la
description de scène que `build_scene_unreal.py` construit (`Scenes/<scène>.json`, les maillages).
Ce script les tire **du même plan**, pour qu'un mur de l'une soit un mur de l'autre.

Les deux cartes rejouent, en petit, le début de la quête « Des pommes pour l'arène » avec ses
dialogues et sa quête livrés (`Source/Elements/World`) :

- `essai/etals` : la mère à son étal, l'enfant qui n'y revient qu'une fois libéré, une lanterne
  devant un pan de mur (une lumière de nuit porte une ombre), un coffre et un panneau, le portail
  vers le parvis ;
- `essai/parvis` : le garde et l'enfant, que l'acceptation de la quête fait paraître, la zone qui
  déclenche le garde, un passage condamné, un passage que la libération de l'enfant ouvre, et le
  maître d'arène, dont le dialogue engage une rencontre.

La troisième, `essai/arene` (scène `essai-1017-arene`), est le **sable** où la bascule vers le
combat mène (LOT-1017) : la carte de Core y porte ce que le combat lit — la zone de combat
(`combatZone`, la carte entière), les quatre points d'entrée du groupe (`arenaEntry`, camp allié,
rangs 0 à 3) et le marqueur de rencontre (`encounter`) autour duquel chaque rencontre de la série
se dresse —, et quatre piliers de deux cases sur deux, qui coupent la vue et se contournent.
L'exploration ne la joue pas : le groupe y entre par la rencontre, et en sort par son issue.

Un PNJ nomme sa figurine par son dossier depuis `Assets/` : le jeu y lit son portrait quand les
kits sont sur le poste. Son maillage, lui, reste le pantin des données d'essai.

Elles ne lisent aucun kit d'assets : sol, mur et pantin sont les données d'essai du dépôt
(`build_mesh_fixture.py`). Les cartes de Core vont sous `Source/Test/Fixtures/Exploration/Levels`,
hors des cartes du jeu ; la description de scène nomme ce dossier (`level.root`).

Usage :
    python scripts/maps/build_essai_maps.py           # écrit les cinq fichiers
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
# Les fiches d'apparence (Rpg/appearances/, LOT-1015) : les quatre héros dans l'ordre de D-28, et le
# pantin qui tient la place d'un PNJ sans fiche.
HEROES = ("heros-brawler", "heros-mage", "heros-priest", "heros-scoundrel")
PUPPET = "pantin"

# Le plan d'une carte : `#` un mur, tout autre signe une case libre. Les lettres repèrent les
# entités, nommées dans `marks` ; une case libre sans entité est un point.
ETALS_PLAN = """
################
#..............#
#..M...........#
#..c.....L.....#
#........##....#
#............A.P
#......K.......#
#..............#
#..E...........#
#...T..........#
#..............#
################
"""

# Le sable : 20 × 14 cases (30 × 21 m). `1` à `4`, le groupe par rang ; `X`, le marqueur de
# rencontre : les bandits s'y dressent à une case à l'ouest (contact) et à l'est (archers).
ARENE_PLAN = """
####################
#..................#
#..................#
#........##........#
#........##........#
#..1...............#
#..2...............#
#..3...........X...#
#..4...............#
#........##........#
#........##........#
#..................#
#..................#
####################
"""

PARVIS_PLAN = """
#######S########
#..............#
#..............#
#.......Gc.....#
#..............#
P.A............#
#..............#
#.........L.B..#
#..............#
#..............R
#..............#
################
"""

# Les figurines des PNJ, par leur dossier depuis `Assets/` (`core::figureDirectory`).
CAPITAL = "Regions/central-empire/capital"
MOTHER = f"{CAPITAL}/martpart/Characters/mother"
CHILD = f"{CAPITAL}/Common/Characters/child"
GUARD = "Regions/central-empire/Common/Characters/ironhand-soldier"
ARENA_MASTER = f"{CAPITAL}/arenarea/arena-of-fate/Characters/arena-master"

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
            "M": {"type": "npc", "dialogue": "mere", "figure": MOTHER, "heading": 180.0},
            "c": {"type": "npc", "dialogue": "enfant", "figure": CHILD, "heading": 180.0,
                  "presenceFlag": "quete.pommes", "presenceTest": "equals", "presenceValue": "enfant-libere"},
            "A": {"type": "spawnPoint", "name": "from-parvis"},
            "P": {"type": "portal", "arrival": "from-etals", "requiresFlag": "", "sealed": False,
                  "targetMap": "essai/parvis"},
            "L": {"type": "light", **LANTERN},
            # Un coffre ne s'ouvre qu'une fois, un panneau se relit : la scène leur donne un bloc.
            "K": {"type": "chest", "block": 0.7},
            "T": {"type": "sign", "block": 1.4},
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
            "G": {"type": "npc", "dialogue": "garde", "figure": GUARD, "heading": 270.0, **WITH_GUARD},
            "c": {"type": "npc", "dialogue": "enfant", "figure": CHILD, "heading": 270.0, **WITH_GUARD},
            # Le maître d'arène : « combattre » engage une rencontre, donc la bascule vers le combat.
            "B": {"type": "npc", "dialogue": "maitre-arene", "figure": ARENA_MASTER, "heading": 270.0},
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
    "essai/arene": {
        "scene": "essai-1017-arene",
        "name": "Essai1017Arene",
        "plan": ARENE_PLAN,
        "marks": {
            # Le groupe entre par ses points d'entrée, le meneur en tête (core::partyDeploymentOn).
            "1": {"type": "arenaEntry", "side": "allies", "rank": 0, "entry": True},
            "2": {"type": "arenaEntry", "side": "allies", "rank": 1},
            "3": {"type": "arenaEntry", "side": "allies", "rank": 2},
            "4": {"type": "arenaEntry", "side": "allies", "rank": 3},
            # Le marqueur de la première rencontre de la série ; les suivantes s'y dressent aussi
            # (core::encounterTriggerOn : le premier marqueur de la carte).
            "X": {"type": "encounter", "encounterId": "arene-bandits", "respawns": True},
        },
        # La zone de combat : la carte entière, le sable et son enceinte (core::cropLevelToZone).
        "zones": [
            {"type": "combatZone", "x": 0, "y": 0, "width": 20, "height": 14, "name": "sable"},
        ],
        "shots": [
            {"id": "arene", "target": [15.0, 1.0, 10.5], "heading": 0.0, "pitch": 48.0, "distance": 30.0,
             "comment": "Le sable entier depuis le sud, au cadrage du joueur : le groupe à l'ouest, les bandits autour de leur marqueur à l'est, les piliers entre eux."},
            {"id": "arene-melee", "target": [12.0, 1.0, 10.5], "heading": 20.0, "pitch": 38.0, "distance": 16.0,
             "comment": "Le centre du sable, plus près : les piliers et l'aperçu de travail (chemin, portée, cibles)."},
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


# Ce qu'une marque du plan dit à la scène seule : la carte de Core ne l'écrit pas.
SCENE_ONLY = ("entry", "heading", "block")


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
            properties = {key: value for key, value in mark.items() if key not in SCENE_ONLY}
            entities.append({"x": column, "y": row, **properties,
                             "heading": mark.get("heading"), "block": mark.get("block")})
    for zone in spec["zones"]:
        entities.append({**zone, "heading": None, "block": None})
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
        fields |= {key: entity[key] for key in sorted(entity) if key not in ("id", "type", "x", "y", *SCENE_ONLY)}
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
    """La description de scène : le sol, les murs, le mobilier, les quatre du groupe, les PNJ, les
    cadrages."""
    rows = rows_of(spec["plan"])
    entities, entry = entities_of(spec)
    width, height = len(rows[0]) * CELL, len(rows) * CELL
    walls = [{"id": f"mur/{column},{row}", "folder": "murs", "mesh": WALL_MESH, "position": centre(column, row),
              "yaw": 0.0, "scale": 1.0}
             for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == WALL]
    # Ce qu'on sollicite sans lui parler : un bloc de la hauteur dite, qui montre son entité.
    furniture = [{"id": f"{entity['type']}-{entity['id']}", "folder": "mobilier", "mesh": WALL_MESH,
                  "position": centre(entity["x"], entity["y"]), "yaw": 0.0, "height": entity["block"],
                  "entity": entity["id"]}
                 for entity in entities if entity["block"] is not None]
    # Le groupe : sa place est celle que Core donne au lancement (l'entrée, ou le point d'arrivée
    # du portail) ; la scène le pose à l'entrée pour qu'il existe. Les quatre héros de D-28 par
    # leur fiche d'apparence (LOT-1015) ; un PNJ, le pantin, en attendant sa fiche (LOT-1024).
    characters = [{"id": f"groupe-{rank + 1}", "appearance": HEROES[rank], "walkSpeed": 3.0,
                   "position": centre(*entry), "heading": 90.0, "party": rank}
                  for rank in range(4)]
    # Les adversaires d'une arène ne sont pas dans la scène : le combat les pose depuis la
    # rencontre (LOT-1017).
    characters += [{"id": f"pnj-{entity['id']}", "appearance": PUPPET, "walkSpeed": 3.0,
                    "position": centre(entity["x"], entity["y"]),
                    "heading": entity["heading"], "entity": entity["id"]}
                   for entity in entities if entity["type"] == "npc"]
    scene = {
        "version": 1,
        "name": spec["name"],
        "comment": (f"Carte d'essai de l'exploration (LOT-1016) ou du combat (LOT-1017), écrite par "
                    f"scripts/maps/build_essai_maps.py, jamais à la main : la carte de Core « {identifier} » "
                    f"({LEVELS_ROOT}) et cette scène viennent du même plan. Elle ne lit aucun kit d'assets. Même "
                    f"repère et mêmes champs que porte-1012.json."),
        "map": f"/Game/Maps/Levels/{identifier}",
        "assetsRoot": "Source/Test/Fixtures/Meshes/Assets",
        "level": {"id": identifier, "root": LEVELS_ROOT, "origin": [0.0, 0.0], "cell": CELL},
        "daylight": "Common/Lighting/daylight.json",
        "frameReference": "Scene/socle/repere.glb",
        "lighting": LIGHTING,
        "ground": {"colour": "#8f7d62", "size": 4000.0, "height": -0.02},
        "fills": [{"id": "sol", "meshes": [FLOOR_MESH], "cell": CELL, "areas": [[0.0, 0.0, width, height]]}],
        "objects": walls + furniture,
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
