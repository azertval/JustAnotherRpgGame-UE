# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Relit un niveau retouché dans l'éditeur et réécrit sa description v5 (LOT-1018, D-52).

Le texte est la source, le niveau une sortie (`build_level.py`) ; l'éditeur du moteur sert à
placer à la souris ce qu'un script place mal. Ce script ramène **ce geste-là** dans le texte, et
rien d'autre : la liste de ce qu'il relit est la **frontière** de l'éditeur, écrite dans
`Documentation/Specification/niveaux.md`. Ce qui ne se relit pas ne se fait pas dans l'éditeur.

Ce qu'il relit :

- un **objet** (`objects`, étiquette `JadgObject:<id>`) : sa position, son lacet, son tangage, son
  roulis, son échelle ; supprimé dans l'éditeur, il quitte la description. Un objet posé à une
  hauteur (`height`) ne relit que sa position et son lacet ;
- un **préfabriqué** posé (`AJadgPrefab`) : sa position, son lacet, son échelle — jamais ses objets,
  qui se retouchent dans son fichier ;
- une **entité** (son repère, `JadgMarker:<id>`) : sa case et son étage ; son **volume**
  (`JadgVolume:<id>`) : la boîte ;
- un **cadrage** (`AJadgShot`) : le point visé, le cap, l'inclinaison, la distance.

Tout le reste — un acteur ajouté à la main, un maillage changé, le terrain sculpté, une lumière,
un réglage de rendu — n'est pas relu : `build_level.py` le referait tel que le texte le dit.

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="<dépôt>/scripts/maps/read_level.py" -JadgMap=essai/etals -unattended -nosplash -nullrhi

Options : `-JadgMap=<carte>` ; `-JadgOut=<fichier>` pour écrire ailleurs que sur la description.
Une valeur relue qui ne diffère de l'écrite que par l'arrondi (0,1 mm, un millième de degré) garde
l'écrite : relire un niveau intact ne change pas un octet de la description.
"""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "maps"))
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "assetsGeneration"))
import build_level  # noqa: E402
import import_master_unreal as master_import  # noqa: E402
import jadg_map  # noqa: E402

POSITION_STEP = 1e-4   # en mètres
ANGLE_STEP = 1e-3      # en degrés
SCALE_STEP = 1e-5


def log(message: str) -> None:
    unreal.log(f"[Relecture] {message}")


def same(old, new, step: float) -> bool:
    if isinstance(old, list) and isinstance(new, list):
        return len(old) == len(new) and all(abs(a - b) <= step for a, b in zip(old, new))
    if isinstance(old, (int, float)) and isinstance(new, (int, float)):
        return abs(old - new) <= step
    return False


def clean(value: float, digits: int) -> float:
    rounded = round(value, digits)
    return 0.0 if rounded == 0 else rounded


def keep(item: dict, key: str, value, step: float, default=None) -> None:
    """Écrit `value` sous `key`, sauf si l'écrite (ou le défaut) ne diffère que par l'arrondi."""
    current = item.get(key, default)
    if current is not None and same(current, value, step):
        return
    if default is not None and same(default, value, step) and key not in item:
        return
    item[key] = value


def tagged(world: unreal.World, prefix: str) -> dict[str, unreal.Actor]:
    found = {}
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        for tag in actor.tags:
            text = str(tag)
            if text.startswith(prefix):
                found[text[len(prefix):]] = actor
    return found


def read_objects(world: unreal.World, doc: dict, frame: build_level.Frame, library: build_level.Library) -> list[str]:
    changes = []
    actors = tagged(world, build_level.OBJECT_TAG)
    kept = []
    for item in doc.get("objects", ()):
        actor = actors.get(item["id"])
        if actor is None or actor.get_attach_parent_actor() is not None:
            changes.append(f"objet {item['id']} supprimé")
            continue
        transform = actor.get_actor_transform()
        position = frame.map_of_point(transform.translation)
        position[2] -= build_level.storey_z(doc, item.get("storey", 0))
        rotation = transform.rotation.rotator()
        yaw, pitch, roll = frame.angles_of(rotation)
        before = copy.deepcopy(item)
        if "height" in item:
            mesh = library.static_mesh(item["mesh"])
            box = mesh.get_bounding_box()
            position[2] += box.min.z * transform.scale3d.z / 100.0
        else:
            scale = [abs(v) for v in frame.map_scale(transform.scale3d)]
            value = clean(scale[0], 6) if max(scale) - min(scale) < SCALE_STEP else [clean(v, 6) for v in scale]
            if not item.get("mirrored"):
                keep(item, "scale", value, SCALE_STEP, 1.0)
            keep(item, "pitch", clean(pitch, 3), ANGLE_STEP, 0.0)
            keep(item, "roll", clean(roll, 3), ANGLE_STEP, 0.0)
        keep(item, "position", [clean(v, 4) for v in position], POSITION_STEP)
        keep(item, "yaw", clean(yaw, 3), ANGLE_STEP, 0.0)
        if item != before:
            changes.append(f"objet {item['id']}")
        kept.append(item)
    if "objects" in doc:
        doc["objects"] = kept
    return changes


def read_prefabs(world: unreal.World, doc: dict, frame: build_level.Frame) -> list[str]:
    changes = []
    anchors = {a.get_editor_property("instance_id"): a
               for a in unreal.GameplayStatics.get_all_actors_of_class(world, build_level.game_class("JadgPrefab"))}
    for item in doc.get("prefabs", ()):
        actor = anchors.get(item["id"])
        if actor is None:
            continue
        before = copy.deepcopy(item)
        transform = actor.get_actor_transform()
        keep(item, "position", [clean(v, 4) for v in frame.map_of_point(transform.translation)], POSITION_STEP)
        keep(item, "yaw", clean(frame.angles_of(transform.rotation.rotator())[0], 3), ANGLE_STEP, 0.0)
        keep(item, "scale", clean(transform.scale3d.z, 6), SCALE_STEP, 1.0)
        if item != before:
            changes.append(f"préfabriqué {item['id']}")
    return changes


def read_entities(world: unreal.World, doc: dict, frame: build_level.Frame) -> list[str]:
    changes = []
    markers = tagged(world, build_level.MARKER_TAG)
    volumes = tagged(world, build_level.VOLUME_TAG)
    storeys = doc.get("storeys") or [{"z": 0.0}]
    for entity in doc.get("entities", ()):
        before = copy.deepcopy(entity)
        marker = markers.get(entity["id"])
        if marker is not None:
            point = frame.map_of_point(marker.get_actor_location())
            column, row = jadg_map.cell_of(point[0], point[1], doc.get("origin"))
            if 0 <= column < doc["width"] and 0 <= row < doc["height"]:
                entity["x"], entity["y"] = column, row
            storey = min(range(len(storeys)), key=lambda s: abs(storeys[s]["z"] - point[2]))
            if storey or "storey" in entity:
                entity["storey"] = storey
        box = volumes.get(entity["id"])
        if box is not None and "volume" in entity:
            centre = frame.map_of_point(box.get_actor_location())
            shape = box.get_component_by_class(unreal.BoxComponent)
            extent = shape.get_scaled_box_extent()
            half = [abs(v) for v in frame.map_of_direction(extent)]
            low = [clean(centre[k] - half[k] / 100.0, 4) for k in range(3)]
            high = [clean(centre[k] + half[k] / 100.0, 4) for k in range(3)]
            volume = entity["volume"]
            if not (same(volume["min"], low, POSITION_STEP) and same(volume["max"], high, POSITION_STEP)):
                entity["volume"] = {"min": low, "max": high}
        if entity != before:
            changes.append(f"entité {entity['id']}")
    return changes


def read_shots(world: unreal.World, doc: dict, frame: build_level.Frame) -> list[str]:
    changes = []
    shots = {a.get_editor_property("shot_id"): a
             for a in unreal.GameplayStatics.get_all_actors_of_class(world, build_level.game_class("JadgShot"))}
    for item in doc.get("shots", ()):
        actor = shots.get(item["id"])
        if actor is None:
            continue
        before = copy.deepcopy(item)
        look = frame.map_of_direction(unreal.MathLibrary.get_forward_vector(actor.get_actor_rotation()))
        heading = math.degrees(math.atan2(look[0], -look[1])) % 360.0
        pitch = -math.degrees(math.asin(max(-1.0, min(1.0, look[2]))))
        keep(item, "target", [clean(v, 4) for v in frame.map_of_point(actor.get_actor_location())], POSITION_STEP)
        keep(item, "heading", clean(heading, 3), ANGLE_STEP)
        keep(item, "pitch", clean(pitch, 3), ANGLE_STEP)
        keep(item, "distance", clean(actor.get_editor_property("distance") / 100.0, 4), POSITION_STEP)
        if item != before:
            changes.append(f"cadrage {item['id']}")
    return changes


def read(world: unreal.World, doc: dict) -> tuple[dict, list[str]]:
    """La description `doc`, mise à jour de ce que la frontière relit du niveau `world`."""
    doc = copy.deepcopy(doc)
    library = build_level.Library(doc.get("assetsRoot"))
    fixtures = build_level.Library(build_level.FIXTURE_ASSETS.relative_to(PROJECT_DIR).as_posix())
    frame = build_level.Frame(build_level.FIXTURE_ASSETS / build_level.FRAME_REFERENCE,
                              fixtures.static_mesh(build_level.FRAME_REFERENCE))
    changes = (read_objects(world, doc, frame, library) + read_prefabs(world, doc, frame)
               + read_entities(world, doc, frame) + read_shots(world, doc, frame))
    return doc, changes


def main() -> None:
    map_id = master_import.command_line_option("JadgMap")
    if not map_id:
        build_level.fail("-JadgMap=<carte> attendu")
    path = jadg_map.find(map_id)
    if path is None:
        build_level.fail(f"carte « {map_id} » introuvable")
    world = unreal.EditorLoadingAndSavingUtils.load_map(jadg_map.package(map_id))
    if world is None:
        build_level.fail(f"{jadg_map.package(map_id)} : le niveau ne s'ouvre pas (build_level.py d'abord)")
    doc, changes = read(world, jadg_map.read(path))
    out = master_import.command_line_option("JadgOut")
    target = Path(out) if out else path
    jadg_map.write(target, doc)
    log(f"{map_id} : {len(changes)} changement(s) relu(s) -> {target}" + ("".join(f"\n  {c}" for c in changes)))


if __name__ == "__main__":
    main()
