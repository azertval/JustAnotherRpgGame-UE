#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le format de carte `jadg-map`, version 5 (LOT-1018) : lire, contrôler, écrire, migrer.

Une carte est **une** description texte qui dit à la fois ce que Core joue (la grille de
collision, les entités sur leurs cases, les étages) et ce que le moteur construit (le terrain, les
objets en mètres, les préfabriqués, les lumières, le ciel, la navigation, le groupe, les
cadrages). Spécification : `Documentation/Specification/niveaux.md` ; schéma :
`Documentation/Specification/level.schema.json`.

Ce module est la seule écriture d'une v5 : `build_essai_maps.py`, `build_gate_scene.py` et
`read_level.py` écrivent par lui, sous sa forme canonique (`dumps`) — relire puis réécrire une
carte intacte rend le même fichier, octet pour octet. Core lit la v5 (`core::LevelLoader`) ;
`build_level.py`, dans l'éditeur du moteur, la construit.

Le **repère** d'une carte : x vers l'est (les colonnes croissantes), y vers le sud (les lignes
croissantes), z vers le haut, en mètres ; le coin de la case (0, 0) tombe en `origin` ; une case
fait 1,5 m (`core::METERS_PER_TILE`). Un lacet (`yaw`, en degrés) tourne le sud vers l'est, comme
dans les descriptions de scène du LOT-1012.

Le **contrôle** (`--check`) relit toutes les cartes du jeu et des essais :

- chaque carte suit le schéma et se tient (identifiants uniques, entités dans la grille et à un
  étage qui existe, volumes non retournés) ;
- **portails appariés** : la carte et le point d'arrivée qu'un portail vise existent, et la carte
  visée a un passage qui revient ;
- **arrivées citées** : un point d'arrivée que ni portail ni zone ne cite est signalé ;
- **zones nommées** : une zone, une zone de combat ont un nom, unique dans la carte ;
- **cases inatteignables** : depuis l'entrée et les points d'arrivée, au rez, par les cases que
  la collision laisse passer ; une entité posée sur une case inatteignable est une erreur. Sur le
  maillage de navigation du niveau construit, le même contrôle est celui de `build_level.py`.

La **migration** (`--migrate`) écrit la v5 d'une carte v4 de l'ancien dépôt, telle quelle : la
grille, les couches et les entités ne changent pas (les identifiants non plus) ; l'étage de décor
d'une couche (`floor`) devient sa hauteur en mètres (`z`) ; les notes de l'éditeur
(`<carte>.editor.json`) entrent dans la description ; le groupe, le ciel, la navigation et un
cadrage s'ajoutent.

Usage :
    python scripts/maps/jadg_map.py --check                 # toutes les cartes, code non nul si faute
    python scripts/maps/jadg_map.py --check essai/etals     # une carte (et ce qu'elle vise)
    python scripts/maps/jadg_map.py --migrate carte.json    # écrit la v5 d'une v4 à sa place
    python scripts/maps/jadg_map.py --canonical             # réécrit chaque carte sous sa forme canonique
    python scripts/maps/jadg_map.py --info essai/etals      # fichier, niveau, cadrages, heures (build.ps1)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORMAT = "jadg-map"
VERSION = 5
CELL = 1.5  # le côté d'une case, en mètres (`core::METERS_PER_TILE`)
SCHEMA = ROOT / "Documentation" / "Specification" / "level.schema.json"
# Les dossiers de cartes, dans l'ordre où le jeu les cherche : les cartes d'essai d'abord.
GAME_LEVELS = ROOT / "Source" / "Elements" / "Levels"
TRIAL_LEVELS = ROOT / "Source" / "Test" / "Fixtures" / "Exploration" / "Levels"
LEVEL_ROOTS = (TRIAL_LEVELS, GAME_LEVELS)
# Le chemin du niveau du moteur d'une carte : `/Game/Maps/Levels/<identifiant>` (`AJadgMapFrame`).
MAP_PACKAGES = "/Game/Maps/Levels"

# L'ordre des clés racine d'une carte écrite ; une clé inconnue suit, dans l'ordre alphabétique.
ROOT_ORDER = ("format", "version", "name", "comment", "place", "width", "height", "origin", "storeys", "storeyLevels",
              "nextEntityId", "tiles", "forced", "layers", "entities", "terrain", "routes", "outlines",
              "objects", "fills", "prefabs", "characters", "party", "assetsRoot", "lighting", "daylight", "ground",
              "navigation", "shots", "hours", "notes")
# L'ordre des clés de tête d'un élément de liste ; les autres suivent par ordre alphabétique.
ITEM_ORDER = ("id", "type", "x", "y", "storey", "name", "kind", "scene", "z", "piece", "mesh", "prefab", "file",
              "position", "target", "heading", "yaw", "pitch", "roll", "distance", "scale", "height", "entity",
              "volume", "cells", "points", "tiles")
# Celui d'un élément sans identifiant : une case, une couche, une note.
CELL_ORDER = ("x", "y", "type", "piece", "name", "kind", "scene", "storey", "z", "text", "tiles")

# Les types de case que la collision arrête (`core::isSolid`).
SOLID = {"solid", "wall", "cliff", "deepWater", "tree", "rock", "fence", "stall", "crate", "column", "roof",
         "tiers", "pit", "lava"}
# Les familles d'entités qui ne sont pas un point où l'on se tient : leur case n'a pas à être atteinte.
AREAS = {"zone", "combatZone", "cityBlock", "route", "light"}

# Ce que la migration ajoute à une carte v4 : le groupe préformé (D-28) par ses fiches
# d'apparence (LOT-1015), le PNJ sans fiche par le pantin, et le ciel de la porte.
HEROES = ("heros-brawler", "heros-mage", "heros-priest", "heros-scoundrel")
PUPPET = "pantin"
STOREY_HEIGHT = 3.0  # la hauteur d'un étage de décor de la v4 (`floor`), en mètres : provisoire
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
DAYLIGHT = "Common/Lighting/daylight.json"


class MapError(ValueError):
    """Une carte qui ne se lit pas comme une v5."""


# --- Lire et écrire ---------------------------------------------------------------------------

def read(path: Path) -> dict:
    """La carte de `path`, telle qu'écrite ; refuse un fichier qui n'est pas une v5."""
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise MapError(f"{path} : JSON invalide ({error})") from error
    if not isinstance(doc, dict) or doc.get("format") != FORMAT or doc.get("version") != VERSION:
        raise MapError(f"{path} : pas une carte {FORMAT} version {VERSION}")
    return doc


def _ordered(item: dict, order: tuple[str, ...]) -> dict:
    head = [key for key in order if key in item]
    return {key: item[key] for key in head + sorted(key for key in item if key not in order)}


def _scalar_list(value: list) -> bool:
    """Une liste de scalaires, ou de listes de scalaires (des points) : elle s'écrit sur une ligne."""
    return all(not isinstance(v, (dict, list)) or (isinstance(v, list) and _scalar_list(v)) for v in value)


def _compact(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _format(value, indent: int) -> str:
    """La forme canonique d'une valeur : une ligne par élément d'une liste d'objets, un objet de
    liste sur une ligne sauf s'il porte lui-même une liste d'objets (une couche et ses cases)."""
    pad = " " * indent
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = [f'{pad}  {json.dumps(key, ensure_ascii=False)}: {_format(child, indent + 2)}'
                 for key, child in value.items()]
        return "{\n" + ",\n".join(lines) + f"\n{pad}}}"
    if isinstance(value, list):
        if not value or _scalar_list(value):
            return _compact(value)
        items = []
        for item in value:
            if isinstance(item, dict):
                item = _ordered(item, ITEM_ORDER if "id" in item else CELL_ORDER)
                nested = [key for key, child in item.items()
                          if isinstance(child, list) and child and not _scalar_list(child)]
                if nested:
                    head = ", ".join(f"{json.dumps(k, ensure_ascii=False)}: {_compact(v)}"
                                     for k, v in item.items() if k not in nested)
                    tail = ", ".join(f"{json.dumps(k, ensure_ascii=False)}: {_format(item[k], indent + 2)}"
                                     for k in nested)
                    items.append(f"{pad}  {{{head}, {tail}}}" if head else f"{pad}  {{{tail}}}")
                    continue
            items.append(f"{pad}  {_compact(item)}")
        return "[\n" + ",\n".join(items) + f"\n{pad}]"
    return _compact(value)


def dumps(doc: dict) -> str:
    """La forme canonique d'une carte : ce que Git relit et compare."""
    return _format(_ordered(doc, ROOT_ORDER), 0) + "\n"


def write(path: Path, doc: dict) -> bool:
    """Écrit la carte sous sa forme canonique ; faux si le fichier était déjà à jour."""
    text = dumps(doc)
    path = Path(path)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


# --- Où sont les cartes -----------------------------------------------------------------------

def all_maps() -> dict[str, Path]:
    """Les cartes v5 des dossiers de cartes, par identifiant (chemin sans extension). Une carte
    d'essai masque une carte du jeu du même identifiant, comme pour le jeu."""
    found: dict[str, Path] = {}
    for root in reversed(LEVEL_ROOTS):
        for path in sorted(root.rglob("*.json")):
            found[path.relative_to(root).with_suffix("").as_posix()] = path
    return found


def find(map_id: str) -> Path | None:
    for root in LEVEL_ROOTS:
        path = root / f"{map_id}.json"
        if path.is_file():
            return path
    return None


def levels_root(path: Path) -> str:
    """Le dossier où la carte se lit avant ceux du jeu (`AJadgMapFrame::LevelsRoot`) ; vide pour
    une carte du jeu."""
    path = Path(path).resolve()
    if path.is_relative_to(GAME_LEVELS):
        return ""
    for root in LEVEL_ROOTS:
        if path.is_relative_to(root):
            return root.relative_to(ROOT).as_posix()
    raise MapError(f"{path} : hors des dossiers de cartes")


def map_id_of(path: Path) -> str:
    path = Path(path).resolve()
    for root in LEVEL_ROOTS:
        if path.is_relative_to(root):
            return path.relative_to(root).with_suffix("").as_posix()
    raise MapError(f"{path} : hors des dossiers de cartes")


def package(map_id: str) -> str:
    return f"{MAP_PACKAGES}/{map_id}"


# --- Les pièces des kits et les préfabriqués ------------------------------------------------

ASSETS = ROOT / "Source" / "Elements" / "Assets"
PREFABS = ROOT / "Source" / "Elements" / "Editor" / "Prefabs"
PREFAB_FORMAT = "jadg-prefab"
_PIECES: dict[tuple[str, str], tuple[str, tuple[int, int]] | None] = {}
_FOOTPRINTS: dict[str, dict[str, tuple[int, int]]] = {}
_MESHES: dict[str, dict[str, str]] = {}
_INDEX: dict[str, list[Path]] = {}


def place_levels(place: str) -> list[str]:
    """Les niveaux de l'arborescence des lieux, du plus propre au plus commun (`EX-LVL-029`) :
    `central-empire/capital/arenarea` → la zone, la ville, la région, le monde."""
    parts = [p for p in place.split("/") if p]
    return ["/".join(parts[:i]) for i in range(len(parts), -1, -1)]


def _footprints(scene: Path) -> dict[str, tuple[int, int]]:
    """L'emprise des pièces d'un kit, en cases, lue dans son manifeste (`footprint`)."""
    key = scene.as_posix()
    if key not in _FOOTPRINTS:
        found: dict[str, tuple[int, int]] = {}
        meshes: dict[str, str] = {}
        manifest = scene / "manifest.json"
        if manifest.is_file():
            for name, entry in json.loads(manifest.read_text(encoding="utf-8")).get("textures", {}).items():
                footprint = entry.get("footprint") or [1, 1]
                found[name.rsplit("/", 1)[-1]] = (int(footprint[0]), int(footprint[1]))
                if entry.get("mesh"):
                    meshes[name.rsplit("/", 1)[-1]] = entry["mesh"]
        _FOOTPRINTS[key] = found
        _MESHES[key] = meshes
    return _FOOTPRINTS[key]


def _manifest_mesh(scene: Path, piece: str) -> Path | None:
    """Le maillage que le manifeste d'un kit donne à une pièce (`mesh`, relatif au kit), s'il existe :
    une pièce partagée qui ne porte pas son nom (`mp-cypress` → `../../arenarea/Scene/ar-meshy-cypres.glb`,
    `reused-af-bench` → `../arena-of-fate/Scene/af-bench.glb`, LOT-1022)."""
    _footprints(scene)
    mesh = _MESHES[scene.as_posix()].get(piece)
    if not mesh:
        return None
    path = (scene / mesh).resolve()
    return path if path.is_file() else None


def resolve_piece(place: str, piece: str, assets: Path = ASSETS) -> tuple[str, tuple[int, int]] | None:
    """Le maillage d'une pièce de couche (`ar-paving-2`) et son emprise en cases : le `.glb` du
    même nom dans le kit du lieu, du plus propre au plus commun (le lieu, sa ville, sa région, le
    monde ; leur `Common/`), puis, à défaut, le seul `.glb` de ce nom sous `Regions/`. `None` si
    aucun : la pièce reste dans le texte, et la construction la compte."""
    key = (place, piece)
    if key in _PIECES:
        return _PIECES[key]
    regions = Path(assets) / "Regions"
    found = None
    for level in place_levels(place):
        base = regions / level if level else regions
        for scene in (base / "Scene", base / "Common" / "Scene"):
            for candidate in [scene / f"{piece}.glb", *sorted(scene.glob(f"*/{piece}.glb"))]:
                if candidate.is_file():
                    found = (candidate, _footprints(scene).get(piece, (1, 1)))
                    break
            if found:
                break
        if found:
            break
    if found is None:
        if not _INDEX and regions.is_dir():
            for glb in sorted(regions.rglob("*.glb")):
                _INDEX.setdefault(glb.stem, []).append(glb)
        matches = _INDEX.get(piece, [])
        if len(matches) == 1:
            scene = matches[0].parent if matches[0].parent.name == "Scene" else matches[0].parent.parent
            found = (matches[0], _footprints(scene).get(piece, (1, 1)))
    if found is None:
        # Le dernier recours : le maillage que le manifeste du kit donne à la pièce, sous un autre nom.
        for level in place_levels(place):
            base = regions / level if level else regions
            for scene in (base / "Scene", base / "Common" / "Scene"):
                mesh = _manifest_mesh(scene, piece)
                if mesh is not None:
                    found = (mesh, _footprints(scene).get(piece, (1, 1)))
                    break
            if found:
                break
    result = None if found is None else (Path(found[0]).resolve().relative_to(Path(assets).resolve()).as_posix(), found[1])
    _PIECES[key] = result
    return result


def read_prefab(prefab_id: str) -> dict:
    """Un préfabriqué (`Editor/Prefabs/<chemin>.json`, format `jadg-prefab`) : des objets posés
    autour de son origine, par maillage (`mesh`) ou par pièce du kit de son lieu (`piece`)."""
    path = PREFABS / f"{prefab_id}.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("format") != PREFAB_FORMAT or doc.get("version") != 1:
        raise MapError(f"{path} : pas un préfabriqué {PREFAB_FORMAT} version 1")
    return doc


def migrate_prefab(old: dict, name: str) -> dict:
    """Le préfabriqué v1 d'un tampon de l'ancien éditeur (`jadg-editor-prefab`) : chaque pièce de
    ses couches devient un objet posé au centre de son emprise, à la hauteur de son étage ; les
    types de case et la collision forcée, que seul l'ancien tampon portait, tombent."""
    objects = []
    for layer in old.get("layers", ()):
        z = layer.get("floor", 0) * STOREY_HEIGHT
        for cell in layer.get("pieces", ()):
            x, y = cell["at"]
            item = {"id": f"{layer['name']}/{x},{y}", "piece": cell["piece"],
                    "position": [(x + 0.5) * CELL, (y + 0.5) * CELL, z]}
            objects.append(item)
    return {"format": PREFAB_FORMAT, "version": 1, "name": name,
            "comment": "Migré du tampon de l'ancien éditeur par scripts/maps/jadg_map.py --migrate (LOT-1018) : "
                       "une pièce par case, posée au centre de sa case, à la hauteur de son étage.",
            "place": old.get("place", ""), "objects": objects}


# --- La grille --------------------------------------------------------------------------------

def cell_centre(column: int, row: int, origin: list[float] | None = None) -> list[float]:
    """Le centre d'une case, en mètres dans le repère de la carte, au sol."""
    x0, y0 = origin or [0.0, 0.0]
    return [x0 + (column + 0.5) * CELL, y0 + (row + 0.5) * CELL, 0.0]


def cell_of(x: float, y: float, origin: list[float] | None = None) -> tuple[int, int]:
    import math
    x0, y0 = origin or [0.0, 0.0]
    return math.floor((x - x0) / CELL), math.floor((y - y0) / CELL)


def entry_of(doc: dict) -> tuple[int, int] | None:
    for tile in doc.get("tiles", ()):
        if tile.get("type") == "entry":
            return tile["x"], tile["y"]
    return None


def solid_cells(doc: dict) -> set[tuple[int, int]]:
    return {(t["x"], t["y"]) for t in doc.get("tiles", ()) if t.get("type") in SOLID}


def blocked_by_props(doc: dict) -> set[tuple[int, int]]:
    """Les cases qu'un décor posé comme entité arrête (`prop`, `blocks` vrai par défaut)."""
    cells = set()
    for entity in doc.get("entities", ()):
        if entity.get("type") == "prop" and entity.get("blocks", True) and not entity.get("presenceFlag"):
            for dx in range(int(entity.get("width", 1))):
                for dy in range(int(entity.get("height", 1))):
                    cells.add((entity["x"] + dx, entity["y"] + dy))
    return cells


def reachable(doc: dict, starts: list[tuple[int, int]]) -> set[tuple[int, int]]:
    """Les cases du rez qu'on atteint depuis `starts`, de case en case (côtés et diagonales libres)."""
    width, height = doc["width"], doc["height"]
    blocked = solid_cells(doc) | blocked_by_props(doc)
    seen = {start for start in starts if start not in blocked}
    queue = deque(seen)
    while queue:
        x, y = queue.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in seen or (nx, ny) in blocked:
                continue
            # En diagonale, les deux côtés libres : on ne coupe pas l'angle d'un mur.
            if dx and dy and ((x + dx, y) in blocked or (x, y + dy) in blocked):
                continue
            seen.add((nx, ny))
            queue.append((nx, ny))
    return seen


def zone_cells(entity: dict) -> list[tuple[int, int]]:
    if entity.get("cells"):
        return [(c["x"], c["y"]) for c in entity["cells"]]
    if "volume" in entity:
        return []
    return [(entity["x"] + dx, entity["y"] + dy)
            for dx in range(int(entity.get("width", 1))) for dy in range(int(entity.get("height", 1)))]


# --- Le contrôle ------------------------------------------------------------------------------

def schema_errors(doc: dict) -> list[str]:
    """Les écarts au schéma publié (`level.schema.json`), par jsonschema s'il est installé."""
    try:
        import jsonschema
    except ImportError:  # le poste sans .venv : le contrôle sémantique suffit
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [f"schéma : {'/'.join(str(p) for p in error.absolute_path) or '(racine)'} : {error.message}"
            for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))[:20]]


def validate(doc: dict) -> list[str]:
    """Ce qui empêche la carte d'être lue ou construite : schéma, identifiants, bornes, étages."""
    errors = schema_errors(doc)
    if errors:
        return errors
    width, height = doc["width"], doc["height"]
    storeys = doc.get("storeys") or [{"name": "rez", "z": 0.0}]
    entries = [t for t in doc["tiles"] if t["type"] == "entry"]
    if len(entries) != 1:
        errors.append(f"{len(entries)} entrée(s), une seule attendue")
    seen_tiles = set()
    for tile in doc["tiles"]:
        if not (0 <= tile["x"] < width and 0 <= tile["y"] < height):
            errors.append(f"case hors de la grille : ({tile['x']}, {tile['y']})")
        if (tile["x"], tile["y"]) in seen_tiles:
            errors.append(f"deux cases en ({tile['x']}, {tile['y']})")
        seen_tiles.add((tile["x"], tile["y"]))
    ids = set()
    numbers = []
    for entity in doc.get("entities", ()):
        identifier = entity.get("id", "")
        if identifier in ids:
            errors.append(f"deux entités « {identifier} »")
        ids.add(identifier)
        if identifier[:1] == "e" and identifier[1:].isdigit():
            numbers.append(int(identifier[1:]))
        if not (0 <= entity["x"] < width and 0 <= entity["y"] < height):
            errors.append(f"{identifier} : hors de la grille ({entity['x']}, {entity['y']})")
        if not 0 <= entity.get("storey", 0) < len(storeys):
            errors.append(f"{identifier} : à l'étage {entity['storey']}, que la carte n'a pas")
        volume = entity.get("volume")
        if volume and any(volume["max"][k] <= volume["min"][k] for k in range(3)):
            errors.append(f"{identifier} : volume retourné")
    if numbers and doc.get("nextEntityId", 1) <= max(numbers):
        errors.append(f"nextEntityId {doc.get('nextEntityId')} déjà donné (e{max(numbers)})")
    zs = [s["z"] for s in storeys]
    if zs[0] != 0.0 or len(set(zs)) != len(zs):
        errors.append("étages : le rez en tête à 0 m, puis chaque étage ou sous-sol à sa hauteur, jamais deux à la même")
    for item in doc.get("objects", ()):
        if not item.get("id"):
            errors.append(f"objet sans identifiant : {item.get('mesh')}")
    object_ids = [item["id"] for item in list(doc.get("objects", [])) + list(doc.get("prefabs", [])) if item.get("id")]
    for duplicate in sorted({i for i in object_ids if object_ids.count(i) > 1}):
        errors.append(f"deux objets « {duplicate} »")
    return errors


def _text(entity: dict, key: str) -> str:
    value = entity.get(key, "")
    return value if isinstance(value, str) else ""


def check_world(maps: dict[str, dict], only: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Le contrôle de contenu des cartes `maps` (identifiant → carte) : erreurs, avertissements."""
    errors: list[str] = []
    warnings: list[str] = []
    arrivals = {map_id: {_text(e, "name"): e for e in doc.get("entities", ()) if e.get("type") == "spawnPoint"}
                for map_id, doc in maps.items()}
    cited: dict[str, set[str]] = {map_id: set() for map_id in maps}
    links: dict[str, set[str]] = {map_id: set() for map_id in maps}
    for map_id, doc in maps.items():
        for entity in doc.get("entities", ()):
            target, arrival = "", ""
            if entity.get("type") == "portal" and not entity.get("sealed"):
                target, arrival = _text(entity, "targetMap"), _text(entity, "arrival")
            elif entity.get("type") == "zone" and _text(entity, "triggerMap"):
                target, arrival = _text(entity, "triggerMap"), _text(entity, "triggerArrival")
            else:
                continue
            links[map_id].add(target)
            if target in cited and arrival:
                cited[target].add(arrival)
            if only is not None and map_id not in only:
                continue
            where = f"{map_id}#{entity.get('id')}"
            if not target:
                errors.append(f"{where} : portail sans carte visée (condamné ? « sealed »)")
            elif target not in maps:
                errors.append(f"{where} : vise la carte « {target} », qui n'existe pas")
            elif arrival and arrival not in arrivals[target]:
                errors.append(f"{where} : vise le point d'arrivée « {arrival} », que « {target} » n'a pas")
    for map_id, doc in maps.items():
        if only is not None and map_id not in only:
            continue
        for error in validate(doc):
            errors.append(f"{map_id} : {error}")
        if any(e.startswith(f"{map_id} : schéma") for e in errors):
            continue
        # Portails appariés : la carte visée a un passage qui revient.
        for target in sorted(links[map_id]):
            if target in maps and target != map_id and map_id not in links[target]:
                warnings.append(f"{map_id} : « {target} » n'a aucun passage qui revient")
        # Arrivées citées.
        for name in sorted(arrivals[map_id]):
            if name not in cited[map_id]:
                warnings.append(f"{map_id} : le point d'arrivée « {name} » n'est cité par aucun portail")
        # Zones nommées.
        names: dict[str, int] = {}
        for entity in doc.get("entities", ()):
            if entity.get("type") in ("zone", "combatZone"):
                name = _text(entity, "name")
                if not name:
                    errors.append(f"{map_id}#{entity.get('id')} : {entity['type']} sans nom")
                else:
                    names[name] = names.get(name, 0) + 1
        for name, count in sorted(names.items()):
            if count > 1:
                errors.append(f"{map_id} : {count} zones nommées « {name} »")
        # Cases inatteignables, au rez.
        entry = entry_of(doc)
        if entry is None:
            continue
        starts = [entry] + [(e["x"], e["y"]) for e in arrivals[map_id].values() if e.get("storey", 0) == 0]
        reached = reachable(doc, starts)
        blocked = solid_cells(doc)
        for entity in doc.get("entities", ()):
            if entity.get("type") in AREAS or entity.get("storey", 0) != 0:
                continue
            cell = (entity["x"], entity["y"])
            # Une entité qu'on sollicite peut se tenir dans le plein (un portail dans un mur, un
            # PNJ derrière son étal) : il suffit qu'une case voisine soit atteinte.
            near = {(cell[0] + dx, cell[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
            if not near & reached:
                errors.append(f"{map_id}#{entity.get('id')} ({entity['type']}) : case ({cell[0]}, {cell[1]}) "
                              "inatteignable depuis l'entrée et les points d'arrivée")
        free = doc["width"] * doc["height"] - len(blocked)
        lost = free - len(reached)
        if lost > 0:
            warnings.append(f"{map_id} : {lost} case(s) libre(s) inatteignable(s) au rez sur {free}")
    return errors, warnings


# --- La migration -----------------------------------------------------------------------------

def migrate(v4: dict, notes: list[dict] | None = None, map_id: str = "") -> dict:
    """La v5 d'une carte v4 : ce que Core joue ne change pas ; ce que le moteur construit s'ajoute."""
    if v4.get("version") != 4:
        raise MapError(f"{map_id} : version {v4.get('version')}, la migration lit la v4")
    if "base" in v4:
        raise MapError(f"{map_id} : une variante ne se migre pas (une v5 porte ses propres objets)")
    width, height = v4["width"], v4["height"]
    layers = []
    place = ""
    for layer in v4.get("layers", ()):
        moved = {key: value for key, value in layer.items() if key != "floor"}
        if layer.get("floor"):
            moved["z"] = layer["floor"] * STOREY_HEIGHT
        for tile in layer.get("tiles", ()):
            if tile.get("elevation"):
                raise MapError(f"{map_id} : couche {layer.get('name')} : hauteur réservée en ({tile['x']}, {tile['y']})")
        place = place or layer.get("scene", "")
        layers.append(moved)
    entities = []
    for entity in v4.get("entities", ()):
        if entity.get("elevation"):
            raise MapError(f"{map_id}#{entity.get('id')} : hauteur réservée non nulle")
        moved = {key: value for key, value in entity.items() if key != "elevation"}
        if moved.get("type") == "npc" and "appearance" not in moved:
            moved["appearance"] = PUPPET
        entities.append(moved)
    known = {"version", "name", "width", "height", "nextEntityId", "tiles", "forced", "layers", "entities"}
    side_x, side_y = width * CELL, height * CELL
    doc = {
        "format": FORMAT,
        "version": VERSION,
        "name": v4["name"],
        "comment": "Migrée de la v4 telle quelle par scripts/maps/jadg_map.py --migrate (LOT-1018) : la grille, "
                   "les couches et les entités sont celles de la v4 ; le groupe, le ciel, la navigation et le "
                   "cadrage s'y sont ajoutés.",
        "place": place,
        "width": width,
        "height": height,
        "origin": [0.0, 0.0],
        "nextEntityId": v4.get("nextEntityId", 1),
        "tiles": v4["tiles"],
    }
    if v4.get("forced"):
        doc["forced"] = v4["forced"]
    doc["layers"] = layers
    doc["entities"] = entities
    for key, value in v4.items():
        if key not in known:
            doc[key] = value  # une propriété de carte (l'heure fixe d'un souterrain)
    doc["party"] = {"appearances": list(HEROES), "walkSpeed": 3.0}
    doc["lighting"] = LIGHTING
    doc["daylight"] = DAYLIGHT
    doc["navigation"] = {"area": [0.0, 0.0, side_x, side_y], "height": 12.0}
    doc["shots"] = [{"id": "ensemble", "target": [side_x / 2, side_y / 2, 1.0], "heading": 0.0, "pitch": 50.0,
                     "distance": round(max(side_x, side_y) * 0.9, 1),
                     "comment": "La carte entière depuis le sud : un cadrage de relecture, pas encore celui du joueur."}]
    doc["hours"] = ["12:00", "22:00"]
    if notes:
        doc["notes"] = [{"x": note["column"], "y": note["row"], "text": note["text"]} for note in notes]
    return doc


def migrate_file(path: Path) -> Path:
    """Remplace la v4 de `path` par sa v5, et retire ses notes d'éditeur, entrées dans la v5 ; un
    tampon de l'ancien éditeur devient un préfabriqué v1."""
    path = Path(path)
    v4 = json.loads(path.read_text(encoding="utf-8"))
    if v4.get("format") == "jadg-editor-prefab":
        write(path, migrate_prefab(v4, path.stem))
        return path
    sidecar = path.with_name(path.stem + ".editor.json")
    notes = json.loads(sidecar.read_text(encoding="utf-8")).get("notes") if sidecar.is_file() else None
    doc = migrate(v4, notes, path.stem)
    write(path, doc)
    if sidecar.is_file():
        sidecar.unlink()
    return path


# --- La ligne de commande ---------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", nargs="*", metavar="CARTE", help="contrôle les cartes (toutes sans argument)")
    parser.add_argument("--migrate", nargs="+", type=Path, metavar="FICHIER", help="migre des cartes v4 en v5")
    parser.add_argument("--canonical", action="store_true", help="réécrit chaque carte sous sa forme canonique")
    parser.add_argument("--strict", action="store_true", help="un avertissement fait échouer le contrôle")
    parser.add_argument("--info", metavar="CARTE", help="ce que build.ps1 lit d'une carte : fichier, niveau, cadrages, heures")
    arguments = parser.parse_args(argv)

    if arguments.info:
        path = find(arguments.info)
        if path is None:
            print(f"carte « {arguments.info} » introuvable", file=sys.stderr)
            return 1
        doc = read(path)
        print(json.dumps({"id": arguments.info, "path": path.relative_to(ROOT).as_posix(), "package": package(arguments.info),
                          "shots": [{"id": shot["id"], "storey": shot.get("storey", 0)} for shot in doc.get("shots", ())],
                          "hours": doc.get("hours", [])}, ensure_ascii=False))
        return 0

    if arguments.migrate:
        for path in arguments.migrate:
            print(f"migrée : {migrate_file(path).resolve().relative_to(ROOT).as_posix()}")
        return 0

    paths = all_maps()
    maps: dict[str, dict] = {}
    unreadable = []
    for map_id, path in paths.items():
        try:
            maps[map_id] = read(path)
        except MapError as error:
            unreadable.append(str(error))
    if arguments.canonical:
        for map_id, doc in maps.items():
            if write(paths[map_id], doc):
                print(f"réécrite : {map_id}")
        return 0
    if arguments.check is None:
        parser.print_help()
        return 2
    only = set(arguments.check) or None
    errors, warnings = check_world(maps, only)
    errors = unreadable + errors
    for map_id, doc in maps.items():
        if (only is None or map_id in only) and paths[map_id].read_text(encoding="utf-8") != dumps(doc):
            errors.append(f"{map_id} : pas sous sa forme canonique (python scripts/maps/jadg_map.py --canonical)")
    for warning in warnings:
        print(f"avertissement : {warning}")
    for error in errors:
        print(f"erreur : {error}", file=sys.stderr)
    count = len(maps) if only is None else len(only)
    print(f"{count} carte(s), {len(errors)} erreur(s), {len(warnings)} avertissement(s)")
    return 1 if errors or (arguments.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
