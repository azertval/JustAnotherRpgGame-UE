# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""L'aller-retour d'une carte entre son texte et l'éditeur (LOT-1018) : le critère de la fiche,
prouvé par un script d'éditeur, sans fenêtre.

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
        -script="<dépôt>/scripts/maps/check_level_roundtrip.py" -unattended -nosplash -nullrhi

(`powershell scripts/build.ps1 -Unreal` le lance.) Sur la carte d'essai à deux étages
(`essai/etages`), dans un niveau à part (`/Game/Maps/Levels/essai/aller-retour`) :

  1. **de rien** : le niveau et les maillages d'essai qu'il cite sont effacés, puis construits
     (`build_level.py`) — empreinte A ;
  2. reconstruit tel quel — la même empreinte A : la construction est régénérable ;
  3. **retouché comme à la souris**, par l'API de l'éditeur : un mur déplacé de 37 cm vers l'est
     et 21 cm vers le sud et tourné de 15°, la rampe allongée d'un dixième, le panneau de l'étage
     porté d'une case vers l'est, un cadrage incliné de 5° de plus ; sauvé — empreinte M ;
  4. **relu** (`read_level.py`) : la description réécrite (sous `Saved/Jadg/levels/`, jamais sur
     celle du dépôt) porte ces quatre gestes et rien d'autre ;
  5. **reconstruite** depuis la description réécrite — l'empreinte M : ce que l'éditeur a fait,
     le texte le refait.

Le niveau d'essai est effacé à la fin. Code non nul à la première différence.
"""

from __future__ import annotations

import sys
from pathlib import Path

import unreal

PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0, str(PROJECT_DIR / "scripts" / "maps"))
import build_level  # noqa: E402
import jadg_map  # noqa: E402
import read_level  # noqa: E402

MAP = "essai/etages"
PACKAGE = f"{jadg_map.MAP_PACKAGES}/essai/aller-retour"
WALL = "mur/5,0"
RAMP = "rampe"
SIGN = "e4"
SHOT = "palier"
OUTPUT = PROJECT_DIR / "Saved" / "Jadg" / "levels" / "aller-retour.json"


def log(message: str) -> None:
    unreal.log(f"[AllerRetour] {message}")


def check(condition: bool, message: str, failures: list[str]) -> None:
    log(("ok : " if condition else "ÉCHEC : ") + message)
    if not condition:
        failures.append(message)


def tagged(world: unreal.World, tag: str) -> unreal.Actor:
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if tag in [str(t) for t in actor.tags]:
            return actor
    build_level.fail(f"aucun acteur « {tag} »")


def main() -> None:
    failures: list[str] = []
    path = jadg_map.find(MAP)
    doc = jadg_map.read(path)

    # 1. De rien : le niveau et les maillages d'essai qu'il cite.
    for folder in (PACKAGE, f"{build_level.FIXTURE_ROOT}/ilot"):
        if unreal.EditorAssetLibrary.does_asset_exist(folder):
            unreal.EditorAssetLibrary.delete_asset(folder)
        if unreal.EditorAssetLibrary.does_directory_exist(folder):
            unreal.EditorAssetLibrary.delete_directory(folder)
    first = build_level.build(MAP, doc, path, PACKAGE)
    log(f"construit de rien : {first['digest'][:16]} ({first['seconds']} s, {first['imports']} import(s))")
    check(first["imports"] >= 2, "les maillages d'essai se sont réimportés", failures)

    # 2. Reconstruit tel quel.
    second = build_level.build(MAP, doc, path, PACKAGE)
    check(second["digest"] == first["digest"], f"reconstruit, la même empreinte ({second['digest'][:16]})", failures)

    # 3. Retouché comme à la souris : des gestes dans le repère du moteur, que le repère mesuré dit.
    fixtures = build_level.Library(build_level.FIXTURE_ASSETS.relative_to(PROJECT_DIR).as_posix())
    frame = build_level.Frame(build_level.FIXTURE_ASSETS / build_level.FRAME_REFERENCE,
                              fixtures.static_mesh(build_level.FRAME_REFERENCE))
    world = unreal.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    wall = tagged(world, f"{build_level.OBJECT_TAG}{WALL}")
    wall.set_actor_location(wall.get_actor_location() + frame.map_point([0.37, 0.21, 0.0]), False, False)
    turned = wall.get_actor_rotation()
    wall.set_actor_rotation(unreal.Rotator(turned.roll, turned.pitch, turned.yaw + 15.0), False)
    ramp = tagged(world, f"{build_level.OBJECT_TAG}{RAMP}")
    scale = ramp.get_actor_scale3d()
    along = [frame.local_map_axis(k) for k in range(3)].index(0)
    grown = [scale.x, scale.y, scale.z]
    grown[along] *= 1.1
    ramp.set_actor_scale3d(unreal.Vector(*grown))
    marker = tagged(world, f"{build_level.MARKER_TAG}{SIGN}")
    marker.set_actor_location(marker.get_actor_location() + frame.map_point([jadg_map.CELL, 0.0, 0.0]), False, False)
    shot = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(world, build_level.game_class("JadgShot"))
                if a.get_editor_property("shot_id") == SHOT)
    turned = shot.get_actor_rotation()
    shot.set_actor_rotation(unreal.Rotator(turned.roll, turned.pitch - 5.0, turned.yaw), False)
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        build_level.fail(f"{PACKAGE} : le niveau retouché ne se sauve pas")
    moved, _ = build_level.footprint(world)
    log(f"retouché : {moved[:16]}")

    # 4. Relu.
    reread, changes = read_level.read(world, doc)
    jadg_map.write(OUTPUT, reread)
    log("relu : " + ", ".join(changes))
    check(sorted(changes) == sorted([f"objet {WALL}", f"objet {RAMP}", f"entité {SIGN}", f"cadrage {SHOT}"]),
          f"quatre gestes relus, et eux seuls ({len(changes)})", failures)
    before = {o["id"]: o for o in doc["objects"]}
    after = {o["id"]: o for o in reread["objects"]}
    dx = after[WALL]["position"][0] - before[WALL]["position"][0]
    dy = after[WALL]["position"][1] - before[WALL]["position"][1]
    check(abs(dx - 0.37) < 1e-3 and abs(dy - 0.21) < 1e-3, f"le mur s'est déplacé de ({dx:.4f} ; {dy:.4f}) m", failures)
    check(abs(abs(after[WALL].get("yaw", 0.0) - before[WALL].get("yaw", 0.0)) - 15.0) < 1e-2,
          f"le mur a tourné de 15° (lacet {after[WALL].get('yaw')})", failures)
    check(abs(after[RAMP]["scale"][0] / before[RAMP]["scale"][0] - 1.1) < 1e-4, "la rampe s'est allongée d'un dixième", failures)
    check(abs(after[RAMP]["pitch"] - before[RAMP]["pitch"]) < 1e-2, "la rampe garde sa pente", failures)
    entities = {e["id"]: e for e in reread["entities"]}
    old = {e["id"]: e for e in doc["entities"]}
    check(entities[SIGN]["x"] == old[SIGN]["x"] + 1 and entities[SIGN].get("storey") == 1,
          "le panneau est une case plus à l'est, toujours à l'étage", failures)
    shots = {s["id"]: s for s in reread["shots"]}
    check(abs(shots[SHOT]["pitch"] - ({s["id"]: s for s in doc["shots"]}[SHOT]["pitch"] + 5.0)) < 1e-2,
          "le cadrage s'est incliné de 5° de plus", failures)

    # 5. Reconstruit depuis la description relue.
    rebuilt = build_level.build(MAP, reread, path, PACKAGE)
    check(rebuilt["digest"] == moved, f"reconstruit depuis le texte relu, l'empreinte du niveau retouché ({rebuilt['digest'][:16]})",
          failures)

    unreal.EditorAssetLibrary.delete_asset(PACKAGE)
    if failures:
        build_level.fail(f"aller-retour : {len(failures)} échec(s)")
    log("aller-retour réussi")


if __name__ == "__main__":
    main()
