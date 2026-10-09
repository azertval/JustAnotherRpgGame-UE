#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Écrit les cartes d'essai de l'exploration (LOT-1016), l'arène du combat (LOT-1017) et la carte à
deux étages (LOT-1018), au format de carte v5 (`jadg-map`, `jadg_map.py`).

Une carte d'essai est **une** description : la grille de collision et les entités que Core joue,
les murs, le sol, le mobilier, le groupe et les PNJ que `build_level.py` construit — tirés d'un
même plan, pour qu'un mur de l'un soit un mur de l'autre.

Les deux premières rejouent, en petit, le début de la quête « Des pommes pour l'arène » avec ses
dialogues et sa quête livrés (`Source/Elements/World`) :

- `essai/etals` : la mère à son étal, l'enfant qui n'y revient qu'une fois libéré, une lanterne
  devant un pan de mur (une lumière de nuit porte une ombre), un coffre et un panneau, le portail
  vers le parvis ;
- `essai/parvis` : le garde et l'enfant, que l'acceptation de la quête fait paraître, la zone qui
  déclenche le garde, un passage condamné, un passage que la libération de l'enfant ouvre, et le
  maître d'arène, dont le dialogue engage une rencontre.

La troisième, `essai/arene`, est le **sable** où la bascule vers le combat mène (LOT-1017) : la
zone de combat est un **volume** (le sable entier), le marqueur de rencontre aussi (`encounter`,
autour duquel chaque rencontre de la série se dresse), les quatre points d'entrée du groupe
(`arenaEntry`, camp allié, rangs 0 à 3) des points ; deux piliers de deux cases sur deux coupent
la vue et se contournent.

La quatrième, `essai/etages`, est la dette du LOT-1016 (D-51) : **deux étages l'un au-dessus de
l'autre** dans une seule carte. Un plancher à 3 m couvre la moitié est de la salle ; une rampe y
monte ; sous le plancher, un portail du rez mène au palier de l'étage ; à la verticale du portail,
sur le plancher, un panneau et une lanterne de l'étage. Autour de la salle, un **terrain** : un
tertre, un chemin pavé sur une rampe de terre, une mare.

Un PNJ nomme sa figurine par son dossier depuis `Assets/` : le jeu y lit son portrait quand les
kits sont sur le poste. Son personnage, lui, est le pantin (`appearance`), en attendant sa fiche
(LOT-1024).

Elles ne lisent aucun kit d'assets : sol et mur sont les données d'essai du dépôt
(`build_mesh_fixture.py`, `assetsRoot`). Elles vont sous `Source/Test/Fixtures/Exploration/Levels`,
hors des cartes du jeu.

Usage :
    python scripts/maps/build_essai_maps.py           # écrit les quatre cartes
    python scripts/maps/build_essai_maps.py --check   # vérifie qu'elles sont à jour
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jadg_map  # noqa: E402

ROOT = jadg_map.ROOT
LEVELS = jadg_map.TRIAL_LEVELS

CELL = jadg_map.CELL
WALL = "#"

FLOOR_MESH = "Scene/ilot/floor.glb"
WALL_MESH = "Scene/ilot/wall.glb"
WALL_HEIGHT = 2.3657290935516357  # la hauteur du bloc de mur des données d'essai, en mètres
# Les fiches d'apparence (Rpg/appearances/, LOT-1015) : les quatre héros dans l'ordre de D-28, et le
# pantin qui tient la place d'un PNJ sans fiche.
HEROES = jadg_map.HEROES
PUPPET = jadg_map.PUPPET

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

# Deux étages : 16 × 12 cases (24 × 18 m). Le plancher de l'étage couvre les colonnes 8 à 14 et
# les lignes 1 à 10 ; la rampe (`/`) monte vers l'est sur les colonnes 4 à 7, lignes 1 et 2.
# `O` : le portail du rez, sous le plancher ; les entités de l'étage sont dans `upstairs`.
ETAGES_PLAN = """
################
#...////.......#
#...////.......#
#..............#
#..............#
#..............#
#.E............#
#..........O...#
#..............#
#....L.........#
#..............#
################
"""
# Autour de la salle, un terrain (LOT-1018) : un tertre au nord-est, un chemin pavé qui monte de
# l'ouest par une rampe de terre, une mare au sud. Ses hauteurs et ses couches se régénèrent
# (`build_level.py`) ; sous la salle, il reste sous le dallage.
ETAGES_TERRAIN = {
    "area": [-24.0, -24.0, 48.0, 42.0],
    "resolution": 1.0,
    "base": -0.1,
    "shapes": [
        {"shape": "disc", "centre": [32.0, -12.0], "radius": 6.0, "height": 4.0, "falloff": 8.0},
        {"shape": "ramp", "from": [-20.0, 9.75], "to": [-4.0, 9.75], "width": 6.0, "heights": [1.5, 0.0]},
    ],
    "layers": [{"name": "herbe", "colour": "#4f6b33"}, {"name": "terre", "colour": "#7a5f3e"},
               {"name": "pave", "colour": "#8a8378"}],
}
ETAGES_ROUTES = [{"name": "chemin", "points": [[-20.0, 9.75], [-1.0, 9.75]], "width": 3.0, "layer": "pave"}]
ETAGES_OUTLINES = [{"name": "mare", "points": [[4.0, 24.0], [16.0, 24.0], [18.0, 32.0], [6.0, 34.0]],
                    "height": -1.2, "water": -0.3, "layer": "terre"}]
STOREY = 3.0                 # la hauteur du plancher de l'étage, en mètres
SLAB = 0.3                   # son épaisseur
SLAB_CELLS = (8, 1, 14, 10)  # colonnes et lignes qu'il couvre, bornes comprises
RAMP = (4, 7, 1, 2)          # la rampe : colonnes 4 à 7, lignes 1 et 2

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
            {"id": "etals", "target": [12.0, 9.0, 1.0], "heading": 0.0, "pitch": 42.0, "distance": 24.0,
             "comment": "La carte entière depuis le sud, au cadrage du joueur : le groupe à l'entrée, la mère à son étal, le pan de mur et sa lanterne, le portail à l'est."},
            {"id": "lanterne", "target": [14.25, 6.0, 1.0], "heading": 205.0, "pitch": 28.0, "distance": 10.0,
             "comment": "La lanterne et le pan de mur, depuis le nord-est : à 22 h, la face du mur tournée vers elle est éclairée, le sol derrière lui est dans son ombre."},
        ],
    },
    "essai/parvis": {
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
            {"id": "parvis", "target": [12.0, 9.0, 1.0], "heading": 0.0, "pitch": 42.0, "distance": 24.0,
             "comment": "La carte entière depuis le sud : le point d'arrivée à l'ouest, le passage condamné au nord, celui que la quête ouvre à l'est."},
        ],
    },
    "essai/arene": {
        "name": "Essai1017Arene",
        "plan": ARENE_PLAN,
        "marks": {
            # Le groupe entre par ses points d'entrée, le meneur en tête (core::partyDeploymentOn).
            "1": {"type": "arenaEntry", "side": "allies", "rank": 0, "entry": True},
            "2": {"type": "arenaEntry", "side": "allies", "rank": 1},
            "3": {"type": "arenaEntry", "side": "allies", "rank": 2},
            "4": {"type": "arenaEntry", "side": "allies", "rank": 3},
            # Le marqueur de la première rencontre de la série ; les suivantes s'y dressent aussi
            # (core::encounterTriggerOn : le premier marqueur de la carte). Un volume d'une case, haut
            # de 2 m, autour de sa case.
            "X": {"type": "encounter", "encounterId": "arene-bandits", "respawns": True, "volumeHeight": 2.0},
        },
        # La zone de combat : un volume, le sable entier et son enceinte (core::combatZoneOf).
        "zones": [
            {"type": "combatZone", "x": 0, "y": 0, "name": "sable",
             "volume": {"min": [0.0, 0.0, -0.5], "max": [30.0, 21.0, 4.0]}},
        ],
        "shots": [
            {"id": "arene", "target": [15.0, 10.5, 1.0], "heading": 0.0, "pitch": 48.0, "distance": 30.0,
             "comment": "Le sable entier depuis le sud, au cadrage du joueur : le groupe à l'ouest, les bandits autour de leur marqueur à l'est, les piliers entre eux."},
            {"id": "arene-melee", "target": [12.0, 10.5, 1.0], "heading": 20.0, "pitch": 38.0, "distance": 16.0,
             "comment": "Le centre du sable, plus près : les piliers et l'aperçu de travail (chemin, portée, cibles)."},
        ],
    },
    "essai/etages": {
        "name": "Essai1018Etages",
        "plan": ETAGES_PLAN,
        "storeys": [{"name": "rez", "z": 0.0}, {"name": "etage", "z": STOREY}],
        "marks": {
            "E": {"entry": True},
            # Sous le plancher : le portail du rez mène au palier de l'étage (même carte).
            "O": {"type": "portal", "arrival": "palier", "requiresFlag": "", "sealed": False,
                  "targetMap": "essai/etages"},
            "L": {"type": "light", **LANTERN},
        },
        # Les entités de l'étage : le palier en haut de la rampe, le panneau et la lanterne à la
        # verticale du portail du rez.
        "upstairs": [
            {"type": "spawnPoint", "x": 9, "y": 2, "name": "palier"},
            {"type": "sign", "x": 11, "y": 7, "block": 1.4},
            {"type": "light", "x": 12, "y": 9, **LANTERN},
        ],
        "zones": [],
        "shots": [
            {"id": "etages", "target": [12.0, 9.0, 1.5], "heading": 30.0, "pitch": 38.0, "distance": 26.0,
             "comment": "La salle depuis le sud-ouest, au cadrage du joueur : la rampe, le plancher de l'étage et ce qui est dessous."},
            {"id": "palier", "target": [15.0, 6.0, 2.0], "heading": 240.0, "pitch": 30.0, "distance": 14.0,
             "comment": "Le plancher depuis l'est : le panneau et la lanterne de l'étage, le portail du rez dessous."},
        ],
    },
}

LIGHTING = {
    "comment": "Les réglages de la porte (LOT-1012), repris tels quels.",
    "lampCandelas": 60.0,
    "fireCandelas": 30.0,
    "sunScale": 1.8,
    "ambientScale": 0.45,
    "skyLuminance": 3.0,
    "exposureBias": 0.0,
    "fog": {"density": 0.004, "falloff": 0.05, "volumetric": True},
    "post": {"bloom_intensity": 0.6, "vignette_intensity": 0.3},
}

# Ce qu'une marque du plan dit à la construction seule : la carte de Core ne le joue pas.
BUILD_ONLY = ("entry", "block", "volumeHeight")


def rows_of(plan: str) -> list[str]:
    rows = plan.strip().splitlines()
    if len({len(row) for row in rows}) != 1:
        raise ValueError("plan : toutes les lignes n'ont pas la même longueur")
    return rows


def centre(column: int, row: int, z: float = 0.0) -> list[float]:
    """Le centre d'une case dans le repère de la carte : x vers l'est, y vers le sud, en mètres."""
    return [(column + 0.5) * CELL, (row + 0.5) * CELL, z]


def entities_of(spec: dict) -> tuple[list[dict], tuple[int, int]]:
    """Les entités d'une carte, dans l'ordre du plan, puis celles de l'étage, puis les zones ; et la
    case d'entrée. Chaque entité garde ce que la construction lit d'elle (`block`)."""
    rows = rows_of(spec["plan"])
    entities: list[dict] = []
    entry = None
    for row, line in enumerate(rows):
        for column, sign in enumerate(line):
            mark = spec["marks"].get(sign)
            if mark is None:
                if sign not in (WALL, ".", "/"):
                    raise ValueError(f"plan : signe « {sign} » sans entité")
                continue
            if mark.get("entry"):
                entry = (column, row)
            if "type" not in mark:
                continue
            entities.append({"x": column, "y": row, **mark})
    for upstairs in spec.get("upstairs", ()):
        entities.append({**upstairs, "storey": 1})
    for zone in spec["zones"]:
        entities.append(dict(zone))
    if entry is None:
        raise ValueError("plan : aucune entrée")
    for number, entity in enumerate(entities, start=1):
        entity["id"] = f"e{number}"
    return entities, entry


def core_entity(entity: dict) -> dict:
    """L'entité telle que la carte l'écrit : ses propriétés, le PNJ avec son personnage."""
    written = {key: value for key, value in entity.items() if key not in BUILD_ONLY}
    if entity["type"] == "npc":
        written["appearance"] = PUPPET
    if "volumeHeight" in entity:
        x0, y0 = entity["x"] * CELL, entity["y"] * CELL
        written["volume"] = {"min": [x0, y0, 0.0], "max": [x0 + CELL, y0 + CELL, entity["volumeHeight"]]}
    return written


def objects_of(identifier: str, spec: dict, entities: list[dict]) -> list[dict]:
    """Les murs, le mobilier qui montre une entité, et — pour la carte à deux étages — le plancher et
    la rampe."""
    rows = rows_of(spec["plan"])
    objects = [{"id": f"mur/{column},{row}", "mesh": WALL_MESH, "position": centre(column, row), "folder": "murs"}
               for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == WALL]
    storeys = spec.get("storeys") or [{"z": 0.0}]
    for entity in entities:
        if "block" in entity:
            # Ce qu'on sollicite sans lui parler : un bloc de la hauteur dite, qui montre son entité.
            z = storeys[entity.get("storey", 0)]["z"]
            objects.append({"id": f"{entity['type']}-{entity['id']}", "mesh": WALL_MESH,
                            "position": centre(entity["x"], entity["y"], z), "height": entity["block"],
                            "entity": entity["id"], "folder": "mobilier"})
    if identifier == "essai/etages":
        c0, r0, c1, r1 = SLAB_CELLS
        thickness = SLAB / WALL_HEIGHT
        # Le plancher : le bloc de mur aplati, son dessus à la hauteur de l'étage.
        objects.append({"id": "plancher", "mesh": WALL_MESH,
                        "position": [(c0 + c1 + 1) / 2 * CELL, (r0 + r1 + 1) / 2 * CELL, STOREY - SLAB],
                        "scale": [c1 - c0 + 1, r1 - r0 + 1, round(thickness, 6)], "folder": "etage"})
        # La rampe : le même bloc aplati, incliné de la case 4 du rez au bord du plancher (colonne 8).
        a0, a1, b0, b1 = RAMP
        run = (a1 - a0 + 1) * CELL
        slope = math.atan2(STOREY, run)
        length = math.hypot(run, STOREY)
        mid = [(a0 * CELL + (a1 + 1) * CELL) / 2, (b0 + b1 + 1) / 2 * CELL, STOREY / 2]
        # Le bloc pivote sur le centre de sa base : la base se pose sous le milieu de la pente.
        pivot = [mid[0] + SLAB * math.sin(slope), mid[1], mid[2] - SLAB * math.cos(slope)]
        objects.append({"id": "rampe", "mesh": WALL_MESH, "position": [round(v, 6) for v in pivot],
                        "pitch": round(math.degrees(slope), 6),
                        "scale": [round(length / CELL, 6), b1 - b0 + 1, round(thickness, 6)], "folder": "etage"})
    return objects


def map_doc(identifier: str, spec: dict) -> dict:
    """La description v5 d'une carte d'essai."""
    rows = rows_of(spec["plan"])
    entities, entry = entities_of(spec)
    width, height = len(rows[0]) * CELL, len(rows) * CELL
    tiles = [{"x": column, "y": row, "type": "wall"}
             for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == WALL]
    # La rampe se monte : au rez, ses cases sont un passage (`stairs`).
    tiles += [{"x": column, "y": row, "type": "stairs"}
              for row, line in enumerate(rows) for column, sign in enumerate(line) if sign == "/"]
    tiles.append({"x": entry[0], "y": entry[1], "type": "entry"})
    tiles.sort(key=lambda tile: (tile["y"], tile["x"]))
    doc = {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": spec["name"],
        "comment": (f"Carte d'essai de l'exploration (LOT-1016), du combat (LOT-1017) ou des étages (LOT-1018), "
                    f"écrite par scripts/maps/build_essai_maps.py, jamais à la main : la grille que Core joue et ce "
                    f"que build_level.py construit viennent du même plan « {identifier} ». Elle ne lit aucun kit "
                    f"d'assets."),
        "width": len(rows[0]),
        "height": len(rows),
        "origin": [0.0, 0.0],
    }
    if "storeys" in spec:
        doc["storeys"] = spec["storeys"]
    doc |= {
        "nextEntityId": len(entities) + 1,
        "tiles": tiles,
        "entities": [core_entity(entity) for entity in entities],
        **({"terrain": ETAGES_TERRAIN, "routes": ETAGES_ROUTES, "outlines": ETAGES_OUTLINES}
           if identifier == "essai/etages" else {}),
        "objects": objects_of(identifier, spec, entities),
        "fills": [{"id": "sol", "meshes": [FLOOR_MESH], "cell": CELL, "areas": [[0.0, 0.0, width, height]]}],
        "party": {"appearances": list(HEROES), "walkSpeed": 3.0},
        "assetsRoot": "Source/Test/Fixtures/Meshes/Assets",
        "lighting": LIGHTING,
        "daylight": jadg_map.DAYLIGHT,
        # Le sol lointain, sous une carte sans terrain.
        **({} if identifier == "essai/etages" else {"ground": {"colour": "#8f7d62", "size": 4000.0, "height": -0.02}}),
        "navigation": {"area": [0.0, 0.0, width, height], "height": 4.0 + (STOREY if "storeys" in spec else 0.0)},
        "shots": spec["shots"],
        "hours": ["12:00", "22:00"],
    }
    return doc


def files() -> dict[Path, str]:
    return {LEVELS / f"{identifier}.json": jadg_map.dumps(map_doc(identifier, spec)) for identifier, spec in MAPS.items()}


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
