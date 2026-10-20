#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""La démo, simplifiée autour de l'Arena of Fate, sur la carte de la capitale (demande de l'auteur
du 19 octobre 2026 : « le colisée est suffisamment imposant », aucune autre zone).

La quête des pommes (`Source/Elements/World/quests/pommes.json`) s'y joue d'un bout à l'autre,
avec ses dialogues inchangés :

- **la mère** à l'entrée, devant la porte monumentale du sud, à son étal (`parvis_stall` de
  `build_arena_fate_modern_scene.py`) ; le groupe arrive sur le parvis, face à elle ;
- **le garde**, au niveau des vestiaires (-6 m), devant les cellules de la prison, et **l'enfant**
  dans la seconde cellule — tous deux jusqu'à ce que l'enfant soit libéré ou que le groupe
  endosse sa peine ; l'enfant libéré attend ensuite auprès de sa mère ;
- **le maître d'arène**, à la porte du triomphe, sur le bord du sable : il lance la série de
  combats (ses rencontres, sa zone de combat et les points d'entrée du groupe sont ceux de la carte
  de l'arène du LOT-1022, `arena-of-fate.json`, recopiés sur la grille de la capitale).

Deux usages :

    python scripts/maps/capitale_demo.py            # écrit Source/Elements/Levels/Capitale.json
    UnrealEditor-Cmd.exe … -run=pythonscript -script=<ce fichier>   # et le pose dans la carte

Dans l'éditeur, après `place_capitale_arena.py` (étape `demo` de `rebuild_capitale_relief.ps1`) :
le repère de la carte de Core (`AJadgMapFrame`) passe au coin de cette grille, au sol de l'arène,
avec ses sept étages ; le groupe, les personnages (`AJadgWalker`, un par entité qui a une
apparence), le départ, un volume de navigation autour de l'arène et le contrôleur qui y applique le
profil fin de navigation et la coupe de la caméra (`AJadgWitnessReview`) y sont posés, toujours
chargés. Les acteurs portent l'étiquette `JadgCapitaleDemo` : une relance retire les précédents.

Le combat ne quitte pas la capitale : sa carte d'arène (`ArenaMap`, `Config/DefaultGame.ini`) est
la capitale elle-même, rouverte le temps du combat, puis rouverte encore pour l'exploration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/maps"))
import jadg_map  # noqa: E402

MAP_ID = "Capitale"
PACKAGE = "/Game/Capitale/Cartes/Capitale"
ARENA = ROOT / "Source/Elements/Levels/central-empire/capital/arenarea/arena-of-fate.json"
TARGET = ROOT / "Source/Elements/Levels" / (MAP_ID + ".json")
PLACED = ROOT / "Saved/Jadg/capitale-arene.json"
TAG = "JadgCapitaleDemo"
FOLDER = "Demo"

# La grille : celle de l'arène (origine (-102 ; -84), cases de 1,5 m) prolongée de 8 cases de
# chaque côté, jusqu'au parvis sud où le groupe arrive. Les mètres sont ceux de l'arène : x à
# l'est, y au sud, l'origine au centre du sable.
ORIGIN = [-114.0, -96.0]
WIDTH, HEIGHT = 152, 128
# Ce que la démo garde de la carte de l'arène : le combat sur le sable, et le maître qui le lance.
KEPT = ("combatZone", "encounter", "arenaEntry")
# Les places, en mètres de l'arène, et leur étage (0 sable et parvis, 1 vestiaires et prison).
ENTRY = (0.75, 90.75)
MOTHER = (5.25, 86.25)
CHILD_FREED = (3.75, 86.25)
GUARD = (15.75, 14.25)
CHILD_CELL = (12.75, 14.25)
# La cellule de l'enfant est fermée (arena_undercroft.py) : on lui parle à travers la grille.
CHILD_THROUGH_BARS = (14.85, 14.9)
MASTER = (-36.75, -3.75)
POMMES = "quete.pommes"
# Le garde et l'enfant tiennent la prison tant que l'enfant n'est ni libéré ni racheté.
IN_CELL = "inconnue|acceptee|persuasion-echouee"
# Le parcours de la démo, que le contrôleur fait marcher au groupe dans le jeu lancé avec
# -JadgWitnessWalk=<rapport.json> : de l'arrivée à la mère, au garde de la prison (-6 m), au maître
# d'arène sur le sable. Des points au sol, en mètres de l'arène.
WALK = ((0.75, 90.75, 0.0), (3.75, 88.5, 0.0), (17.4, 14.25, -6.0), (-35.0, -3.75, 0.0))
AGENT_HEIGHT = 190.0  # cm (Config/DefaultEngine.ini, SupportedAgents)
# Navigation : l'emprise de la grille, des vestiaires (-6 m) à la terrasse (46,8 m). Les catacombes
# (-12 m) en restent dehors : elles s'ouvrent par un mur à interrupteur caché, fermé au repos.
NAVIGATION = {"area": [-114, -96, 114, 96], "floor": -7.0, "height": 58.0}
# Le profil fin de l'arène (verify_capitale_arena_access.py) : tuiles de 3 m, douze couches.
FINE_NAVIGATION = (("fine_navigation", True), ("navigation_cell_size", 10.0), ("navigation_cell_height", 5.0),
                   ("navigation_elevation_ratio", 1.0), ("navigation_tile_size", 300.0),
                   ("navigation_average_layers", 12.0), ("navigation_max_simplification_error", 1.3),
                   ("navigation_max_search_nodes", 32768))


def cell(point: tuple[float, float]) -> tuple[int, int]:
    return jadg_map.cell_of(point[0], point[1], ORIGIN)


def npc(identifier: str, point, storey: int, dialogue: str, figure: str, heading: float, presence=None) -> dict:
    x, y = cell(point)
    entity = {"id": identifier, "type": "npc", "x": x, "y": y, "storey": storey, "appearance": "pantin",
              "dialogue": dialogue, "figure": figure, "guards": "", "heading": heading}
    if presence is not None:
        entity.update(presenceFlag=POMMES, presenceTest="equals", presenceValue=presence)
    return entity


def reach_point(entity: dict, doc: dict) -> list[float]:
    """Où le groupe doit pouvoir se rendre pour solliciter un personnage : sa case, sauf l'enfant
    enfermé, sollicité devant sa grille."""
    x, y, _ = jadg_map.cell_centre(entity["x"], entity["y"], doc["origin"])
    if (entity["x"], entity["y"]) == cell(CHILD_CELL) and entity.get("storey") == 1:
        x, y = CHILD_THROUGH_BARS
    return [x, y, doc["storeys"][entity["storey"]]["z"]]


def document() -> dict:
    arena = json.loads(ARENA.read_text(encoding="utf-8"))
    shift = [round((arena["origin"][k] - ORIGIN[k]) / jadg_map.CELL) for k in (0, 1)]
    entities = []
    for entity in arena["entities"]:
        if entity["type"] in KEPT:
            entities.append(dict(entity, x=entity["x"] + shift[0], y=entity["y"] + shift[1]))
    master = next(e for e in arena["entities"] if e["type"] == "npc" and e.get("dialogue") == "maitre-arene")
    number = arena["nextEntityId"]
    entities += [
        npc(master["id"], MASTER, 0, "maitre-arene", master["figure"], 90.0, master["presenceValue"]),
        npc(f"e{number}", MOTHER, 0, "mere", "mother", 180.0),
        npc(f"e{number + 1}", GUARD, 1, "garde", "ironhand-soldier", 90.0, IN_CELL),
        npc(f"e{number + 2}", CHILD_CELL, 1, "enfant", "child", 90.0, IN_CELL + "|condamne"),
        npc(f"e{number + 3}", CHILD_FREED, 0, "enfant", "child", 180.0, "enfant-libere"),
    ]
    entry = cell(ENTRY)
    doc = {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": "Capitale",
        "place": "La capitale : l'Arena of Fate et son parvis",
        "comment": "Écrit par scripts/maps/capitale_demo.py : la démo autour de l'arène (quête des pommes), "
                   "les rencontres de la carte de l'arène recopiées sur cette grille.",
        "width": WIDTH,
        "height": HEIGHT,
        "origin": ORIGIN,
        "storeys": arena["storeys"],
        "nextEntityId": number + 4,
        "tiles": [{"x": entry[0], "y": entry[1], "type": "entry"}],
        "entities": entities,
        "objects": [],
        "party": dict(arena["party"], heading=0.0),
        "navigation": NAVIGATION,
    }
    errors = jadg_map.validate(doc)
    if errors:
        raise RuntimeError("; ".join(errors))
    return doc


def write() -> dict:
    doc = document()
    jadg_map.write(TARGET, doc)
    return doc


def place(doc: dict) -> dict:
    """Pose la démo dans la carte de la capitale (dans l'éditeur)."""
    import unreal as u

    import build_level as scene

    placed = json.loads(PLACED.read_text(encoding="utf-8"))
    (cx, cy), ground = placed["centre_m"], placed["ground_m"]
    offset = u.Vector(cx * 100.0, cy * 100.0, ground * 100.0)
    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if world is None:
        raise RuntimeError(PACKAGE)
    u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in u.WorldPartitionBlueprintLibrary.get_actor_descs()])
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    old = [a for a in actors.get_all_level_actors() if TAG in [str(t) for t in a.tags]]
    stale = [a.get_package().get_name() for a in old]
    for a in old:
        actors.destroy_actor(a)

    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE))
    level = scene.Level(world)

    def keep(actor: u.Actor, folder: str = FOLDER) -> u.Actor:
        actor.tags = list(actor.tags) + [TAG]
        actor.set_editor_property("is_spatially_loaded", False)
        actor.set_folder_path(folder)
        return actor

    # Le repère de la carte de Core : au coin de la grille, au sol de l'arène, ses sept étages.
    frames = [a for a in actors.get_all_level_actors() if a.get_class().get_name() == "JadgMapFrame"]
    if len(frames) != 1:
        raise RuntimeError(f"{len(frames)} repère(s) de carte dans la capitale, un seul attendu")
    mark = frames[0]
    mark.set_actor_location(offset + frame.map_point([ORIGIN[0], ORIGIN[1], 0.0]), False, False)
    mark.set_editor_property("level_id", MAP_ID)
    mark.set_editor_property("levels_root", jadg_map.levels_root(TARGET))
    mark.set_editor_property("cell_size", jadg_map.CELL * 100.0)
    mark.set_editor_property("east", frame.map_direction([1.0, 0.0, 0.0]))
    mark.set_editor_property("south", frame.map_direction([0.0, 1.0, 0.0]))
    mark.set_editor_property("storey_heights", [s["z"] * 100.0 for s in doc["storeys"]])
    # Les étages du monument font le sol : aucun champ de hauteurs (celui du relief entier n'y vaut rien).
    mark.set_editor_property("terrain_width", 0)
    mark.set_editor_property("terrain_height", 0)
    mark.set_editor_property("terrain_heights", [])

    def storey_z(storey: int) -> float:
        return doc["storeys"][storey]["z"]

    # Le groupe à l'entrée, par rang ; le départ du joueur sous le meneur.
    walker = scene.game_class("JadgWalker")
    entry = jadg_map.entry_of(doc)
    foot = jadg_map.cell_centre(*entry, doc["origin"])
    party = doc["party"]
    walkers = 0
    for rank, appearance in enumerate(party["appearances"]):
        actor = scene.place_walker(level, frame, walker, f"groupe-{rank + 1}", appearance, foot, party["heading"],
                                   party["walkSpeed"])
        actor.set_editor_property("party_rank", rank)
        actor.set_editor_property("entity_id", "")
        actor.set_actor_location(offset + actor.get_actor_location(), False, False)
        keep(actor, FOLDER + "/Groupe")
        walkers += 1
    starts = [a for a in actors.get_all_level_actors() if a.get_class().get_name() == "PlayerStart"]
    start_at = offset + frame.map_point([foot[0], foot[1], 1.0])
    if starts:
        for extra in starts[1:]:
            actors.destroy_actor(extra)
        starts[0].set_actor_location(start_at, False, False)
        starts[0].set_actor_rotation(frame.look(party["heading"]), False)
    else:
        keep(level.spawn(u.PlayerStart, start_at, frame.look(party["heading"]), "Depart", FOLDER))
    for entity in doc["entities"]:
        if entity["type"] != "npc" or "appearance" not in entity:
            continue
        foot = jadg_map.cell_centre(entity["x"], entity["y"], doc["origin"])
        foot[2] = storey_z(entity.get("storey", 0))
        actor = scene.place_walker(level, frame, walker, f"pnj-{entity['id']}-{entity['dialogue']}",
                                   entity["appearance"], foot, entity.get("heading", 0.0), 3.0)
        actor.set_editor_property("party_rank", -1)
        actor.set_editor_property("entity_id", entity["id"])
        actor.set_actor_location(offset + actor.get_actor_location(), False, False)
        keep(actor, FOLDER + "/Personnages")
        walkers += 1

    # La navigation de la démo : l'arène et son parvis, au profil fin, appliqué au lancement par le
    # contrôleur (les réglages de Recast se relisent de la configuration au chargement).
    x0, y0, x1, y1 = NAVIGATION["area"]
    low, high = NAVIGATION["floor"], NAVIGATION["floor"] + NAVIGATION["height"]
    centre = offset + frame.map_point([(x0 + x1) / 2, (y0 + y1) / 2, (low + high) / 2])
    size = u.Vector((x1 - x0) * 100.0, (y1 - y0) * 100.0, (high - low) * 100.0)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}
    u.JadgSceneBuild.spawn_box_volume(world, u.NavMeshBoundsVolume, centre, size)
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() not in before and actor.get_class().get_name() == "NavMeshBoundsVolume":
            actor.set_actor_label("Navigation_Arene")
            keep(actor)
    review = actors.spawn_actor_from_class(u.load_class(None, "/Script/JustAnotherRpgGame.JadgWitnessReview"),
                                          offset, u.Rotator())
    review.set_actor_label("Navigation_et_coupe")
    for name, value in FINE_NAVIGATION:
        review.set_editor_property(name, value)
    review.set_editor_property("route_points", [offset + frame.map_point(list(point)) for point in WALK])
    review.set_editor_property("walk_return", False)
    keep(review)
    # Le maillage de navigation se construit avec la carte, jamais dans le jeu : au profil fin
    # (appliqué ici, dans l'éditeur), puis découpé par WorldPartitionNavigationDataBuilder (étape
    # `navigation`) en morceaux chargés avec les cellules. Reconstruit dans le jeu, même en
    # arrière-plan, il prenait jusqu'à 270 ms d'une image au fil d'exécution du jeu (profil du
    # 20 octobre 2026).
    u.JadgSceneBuild.unreachable_points(world, offset + frame.map_point([ENTRY[0], ENTRY[1], 0.25]), [])
    # La hauteur des personnages (capsule de 1,96 m) : à 1,44 m, la hauteur par défaut, le maillage
    # passait sous le pignon de la voûte au pied de l'escalier sud, où le groupe restait coincé.
    for recast in [a for a in actors.get_all_level_actors() if a.get_class().get_name() == "RecastNavMesh"]:
        recast.set_editor_property("agent_height", AGENT_HEIGHT)
    if not review.prepare_fine_navigation():
        raise RuntimeError("Profil fin de navigation refusé")
    recasts = [a for a in actors.get_all_level_actors() if a.get_class().get_name() == "RecastNavMesh"]
    if len(recasts) != 1:
        raise RuntimeError(f"{len(recasts)} maillage(s) de navigation, un seul attendu")
    for recast in recasts:
        recast.set_editor_property("runtime_generation", u.RuntimeGenerationType.STATIC)
        recast.set_editor_property("is_world_partitioned", True)
        recast.set_editor_property("is_spatially_loaded", False)
    world.get_world_settings().set_editor_property("default_game_mode", scene.game_class("JadgGameMode"))

    if not u.EditorLevelLibrary.save_current_level() or not u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError("Sauvegarde de la carte et des acteurs de la démo")
    # Le paquet externe d'un acteur détruit ne s'efface pas toujours (place_capitale_arena.py).
    content = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_content_dir()))
    erased = 0
    for name in stale:
        path = content / (name[len("/Game/"):] + ".uasset")
        if path.is_file():
            path.unlink()
            erased += 1
    return dict(map=PACKAGE, core=str(TARGET.relative_to(ROOT)), walkers=walkers, removed=len(old), erased=erased,
                frame_cm=[round(v, 1) for v in (mark.get_actor_location().x, mark.get_actor_location().y,
                                                 mark.get_actor_location().z)])


def main() -> None:
    doc = write()
    try:
        import unreal  # noqa: F401
    except ImportError:
        print(f"{TARGET.relative_to(ROOT)} : {len(doc['entities'])} entité(s)")
        return
    report = place(doc)
    out = ROOT / "Saved/Jadg/capitale-demo.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("CAPITALE_DEMO_READY", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
