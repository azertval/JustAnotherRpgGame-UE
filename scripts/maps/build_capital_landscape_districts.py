#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""District production: relief -> materials/Nanite -> vegetation -> reload audit.

Outputs /Game/Capitale/Ressources/Metropole and /Game/Maps/Levels/capital-landscape/
paysage-* plus districts/*. Each district is saved independently before assembly.
No buildings, walls, bridges, props, characters or invisible floors are spawned.
"""

from pathlib import Path
from array import array
import json
import sys
import time
import unreal as u

# Archived generator: the current construction world must not be overwritten.
if __name__ == "__main__":
    raise RuntimeError("Generateur historique archive apres nettoyage. Ouvrir /Game/Capitale/Cartes/Capitale ; restauration explicite requise pour regenerer les anciens essais.")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import build_level as scene  # noqa: E402
import jadg_map  # noqa: E402
import import_scenery_unreal as scenery  # noqa: E402
from arenarea_landscape_materials import LAYERS, build as build_surfaces  # noqa: E402

REPORT = ROOT / "Saved/Jadg/capital-landscape-districts"
CONTENT = "/Game/Capitale/Ressources/Metropole"
LEVELS = "/Game/Maps/Levels/capital-landscape"
ASSEMBLY = "/Game/Maps/Levels/capital-landscape/construction-capitale"
DISTRICT_PACKAGES = {
    'Q01': '/Game/Maps/Levels/capital-landscape/districts/sloghood',
    'Q02': '/Game/Maps/Levels/capital-landscape/districts/uptown',
    'Q03': '/Game/Maps/Levels/capital-landscape/districts/artisansquare',
    'Q04': '/Game/Maps/Levels/capital-landscape/districts/scholarnest',
    'Q05': '/Game/Maps/Levels/capital-landscape/districts/dweomer',
    'Q06': '/Game/Maps/Levels/capital-landscape/districts/martpart',
    'Q07': '/Game/Maps/Levels/capital-landscape/districts/arenarea',
    'Q08': '/Game/Maps/Levels/capital-landscape/districts/oldtown',
    'Q09': '/Game/Maps/Levels/capital-landscape/districts/neckoffoods',
    'Q10': '/Game/Maps/Levels/capital-landscape/districts/bloomburgs',
    'Q11': '/Game/Maps/Levels/capital-landscape/districts/downtown',
    'Q12': '/Game/Maps/Levels/capital-landscape/districts/palacedomain',
    'Q13': '/Game/Maps/Levels/capital-landscape/districts/docks',
    'Q14': '/Game/Maps/Levels/capital-landscape/districts/abords',
}
MANIFEST = json.loads((REPORT / "manifest.json").read_text(encoding="utf8"))
AL = u.EditorAssetLibrary


def report(name, data):
    data["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = REPORT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")
    print("CAPITAL_PHASE_OK", name, flush=True)


def district(key):
    return next(q for q in MANIFEST["districts"] if q["id"] == key)


def package(row):
    return DISTRICT_PACKAGES[row['id']]


def tiles(row):
    return [t for t in MANIFEST["tiles"] if t["id"] in row["tiles"]]


def actors():
    return u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()


def save(world, row, phase, data):
    if not u.EditorLoadingAndSavingUtils.save_map(world, package(row)):
        raise RuntimeError("Map save failed: " + row["slug"])
    AL.save_directory(CONTENT, only_if_is_dirty=True, recursive=True)
    report(row["id"] + "/" + phase + ".json", dict(package=package(row), **data))


def context(row):
    world = u.EditorLoadingAndSavingUtils.load_map(package(row))
    terrain = {a.get_actor_label().removeprefix("Relief_"): a for a in actors() if isinstance(a, u.Landscape)}
    if world is None or set(terrain) != set(row["tiles"]):
        raise RuntimeError("Saved district is incomplete: " + row["slug"])
    return world, terrain


def relief(row):
    world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
    level = scene.Level(world)
    material = AL.load_asset("/Game/Capitale/Ressources/Arenarea/Materials/MI_Relief")
    water = AL.load_asset("/Game/Capitale/Ressources/Arenarea/Materials/M_Eau")
    made = []
    for t in tiles(row):
        folder = REPORT / "tiles" / t["id"]
        heights = array("H")
        heights.frombytes((folder / "heights.r16").read_bytes())
        weights = list((folder / "weights.r8").read_bytes())
        ox, oy = t["origin_m"]
        land = u.JadgSceneBuild.spawn_landscape(world, u.Vector(ox*100, oy*100, 0),
            u.Vector(t["spacing_m"]*100, t["spacing_m"]*100, 100), t["quads"], t["quads"],
            heights.tolist(), list(LAYERS), weights, material, CONTENT+"/Layers", True)
        if land is None:
            raise RuntimeError("Landscape import failed " + t["id"])
        scene.Level.name(land, "Relief_"+t["id"], "01_Relief/"+row["name"])
        land.tags = ["CapitalLandscape", row["id"], t["id"]]
        land.set_editor_property("enable_nanite", False)
        if not u.JadgSceneBuild.finalize_landscape_layers(land):
            raise RuntimeError("Landscape paint needs an RHI-enabled commandlet")
        if t["wetFraction"] > 0:
            name = "eau-"+t["id"]
            source = ROOT / "Source/Elements/Assets/Built/capital-landscape-districts" / (name+".glb")
            target = CONTENT+"/Water/"+name
            mesh = scenery.import_glb(source, CONTENT+"/Water", target, target+"/StaticMeshes/SM_"+name)
            settings = mesh.get_editor_property("nanite_settings")
            settings.enabled = False
            mesh.set_editor_property("nanite_settings", settings)
            mesh.set_material(0, water)
            AL.save_loaded_asset(mesh, only_if_is_dirty=False)
            actor = level.spawn(mesh, u.Vector(), u.Rotator(), name, "02_Eaux")
            actor.set_actor_enable_collision(False)
            actor.static_mesh_component.set_collision_profile_name("NoCollision")
            actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            actor.static_mesh_component.set_editor_property("cast_shadow", False)
            actor.tags = ["CapitalWater"]
        made.append(t["id"])
        print("CAPITAL_RELIEF", row["id"], t["id"], flush=True)
    atlas = json.loads((ROOT/"Source/Elements/Terrain/capital/atlas.json").read_text(encoding="utf8"))
    for site in atlas["sites"]:
        if not site["xy_m"] or site["ground_z_m"] is None or site["id"] == "X13":
            continue
        if (site["district"] or "Q14") != row["id"]:
            continue
        x, north = site["xy_m"]
        marker = level.spawn(u.TargetPoint, u.Vector(x*100, -north*100, site["ground_z_m"]*100),
            u.Rotator(), site["id"]+"_"+site["name"], "04_Emprises_libres")
        marker.tags = ["CapitalReservation", site["id"], "Parcelle_m="+str(site["parcel_m"])]
        marker.set_editor_property("is_editor_only_actor", True)
    save(world, row, "01-relief", dict(tiles=made, buildings=0, north="-Y", spacing_m=4))


def materials(row):
    world, terrain = context(row)
    path = CONTENT+"/Materials/MI_Surfaces"
    material = AL.load_asset(path) if AL.does_asset_exist(path) else build_surfaces(metropole=True)
    built = {}
    for name, land in terrain.items():
        land.set_editor_property("landscape_material", material)
        if not u.JadgSceneBuild.finalize_landscape_layers(land):
            raise RuntimeError("Final Landscape paint merge failed " + name)
        land.set_editor_property("enable_nanite", True)
        # A small overlap hides Nanite's border simplification; source heights still match exactly.
        land.set_editor_property("nanite_skirt_enabled", True)
        land.set_editor_property("nanite_skirt_depth", 0.2)
        if not u.JadgSceneBuild.build_landscape_nanite(land):
            raise RuntimeError("Nanite failed: " + name)
        tris = [c.static_mesh.get_num_nanite_triangles() for c in land.get_components_by_class(u.LandscapeNaniteComponent)]
        if not tris or min(tris) <= 0:
            raise RuntimeError("Empty Nanite representation: " + name)
        built[name] = sum(tris)
        print("CAPITAL_NANITE", row["id"], name, sum(tris), flush=True)
    save(world, row, "02-materials", dict(tiles=built, layers=list(LAYERS), material=material.get_path_name()))


def tree_type(group):
    target = CONTENT+"/Vegetation/SM_"+group["id"]
    mesh = AL.load_asset(target) if AL.does_asset_exist(target) else AL.duplicate_asset(group["mesh"], target)
    if mesh is None:
        raise RuntimeError("Missing supplied tree " + group["mesh"])
    ns = mesh.get_editor_property("nanite_settings")
    if not ns.enabled:
        ns.enabled = True
        mesh.set_editor_property("nanite_settings", ns)
        AL.save_loaded_asset(mesh, only_if_is_dirty=False)
    tris = mesh.get_num_nanite_triangles()
    if tris <= 0:
        raise RuntimeError("Tree Nanite is empty " + target)
    ftpath = CONTENT+"/Vegetation/FT_"+group["id"]
    ft = AL.load_asset(ftpath) if AL.does_asset_exist(ftpath) else AL.duplicate_asset(
        "/Game/Capitale/Ressources/Arenarea/Foliage/FT_SM_vlkhcbxia_VarA", ftpath)
    ft.set_editor_property("mesh", mesh)
    ft.set_editor_property("override_materials", [])
    ft.set_editor_property("nanite_override_materials", [])
    ft.set_editor_property("cull_distance", u.Int32Interval(0, 0))
    ft.set_editor_property("collision_with_world", False)
    AL.set_metadata_tag(ft, "SourceAsset", group["mesh"])
    AL.save_loaded_asset(ft)
    box = mesh.get_bounding_box()
    scale = group["desiredHeight_m"]*100/(box.max.z-box.min.z)
    return ft, scale, box.min.z, tris


def foliage(row):
    world, terrain = context(row)
    if any(isinstance(a, u.InstancedFoliageActor) for a in actors()):
        raise RuntimeError("Vegetation already exists; restart this district at Relief")
    cache, counts = {}, {}
    for t in tiles(row):
        groups = json.loads((REPORT / "tiles" / t["id"] / "foliage.json").read_text())
        count = 0
        for g in groups:
            if g["id"] not in cache:
                if g.get("tree"):
                    cache[g["id"]] = tree_type(g)
                else:
                    ft = AL.load_asset(g["foliageType"])
                    mesh = AL.load_asset(g["mesh"])
                    tris = mesh.get_num_nanite_triangles()
                    if ft is None or tris <= 0:
                        raise RuntimeError("Foliage source missing " + g["id"])
                    cache[g["id"]] = ft, 1, 0, tris
            ft, base_scale, minimum, _ = cache[g["id"]]
            transforms = []
            for x, y, z, yaw, factor in g["instances"]:
                scale = factor*base_scale
                transforms.append(u.Transform(u.Vector(x*100, y*100, z*100-minimum*scale),
                                               u.Rotator(pitch=0, yaw=yaw, roll=0), u.Vector(scale, scale, scale)))
            planted = u.JadgFoliageBuild.plant_on_landscape(terrain[t["id"]], ft, transforms)
            if planted != len(transforms):
                raise RuntimeError("Planting failed " + t["id"] + "/" + g["id"])
            count += planted
        counts[t["id"]] = count
        print("CAPITAL_PLANTED", row["id"], t["id"], count, flush=True)
    root_report = project_roots(row)
    report(row['id']+'/06-grounding.json', dict(**root_report, remainingErrors=project_roots(row, apply=False)['changed']))
    save(world, row, "03-foliage", dict(instances=sum(counts.values()), tiles=counts,
                                       variants={k: v[3] for k, v in cache.items()}, buildings=0))


def project_roots(row, apply=True):
    candidates = []
    for tile in tiles(row):
        points = json.loads((REPORT/'tiles'/tile['id']/'ground-candidates.json').read_text())
        candidates.extend(u.Vector(*(v*100 for v in p)) for p in points)
    changed, checked = 0, 0
    for actor in actors():
        if isinstance(actor, u.InstancedFoliageActor):
            count, seen = u.JadgFoliageBuild.ground_foliage_roots(actor, candidates, apply)
            if count < 0:
                raise RuntimeError('Cannot project foliage onto its native Landscape base')
            changed += count
            checked += seen
    if checked != len(candidates):
        raise RuntimeError(f'Foliage ground candidates missing: {checked}/{len(candidates)}')
    return dict(candidates=len(candidates), checked=checked, changed=changed)


def grounding(row):
    world, _ = context(row)
    result = project_roots(row)
    save(world, row, '06-grounding', result)
    context(row)
    check = project_roots(row, apply=False)
    if check['changed']:
        raise RuntimeError('Foliage roots still differ from native terrain after reload')
    report(row['id']+'/06-grounding.json', dict(**result, remainingErrors=check['changed']))


def audit(row):
    world, terrain = context(row)
    checks, errors, triangle_count = [], [], 0
    for t in tiles(row):
        land = terrain[t["id"]]
        triangles = [c.static_mesh.get_num_nanite_triangles() for c in land.get_components_by_class(u.LandscapeNaniteComponent)]
        triangle_count += sum(triangles)
        if not triangles or min(triangles) <= 0:
            errors.append("Nanite empty " + t["id"])
        heights = array("H")
        heights.frombytes((REPORT / "tiles" / t["id"] / "heights.r16").read_bytes())
        source_weights = (REPORT / "tiles" / t["id"] / "weights.r8").read_bytes()
        side = t["quads"] + 1
        for ix, iy in ((32, 32), (126, 126), (220, 220)):
            x, y = t["origin_m"][0]+ix*4, t["origin_m"][1]+iy*4
            expected = (heights[iy*(t["quads"]+1)+ix]-32768)/128
            hit = u.SystemLibrary.line_trace_single(world, u.Vector(x*100, y*100, 30000),
                u.Vector(x*100, y*100, -5000), u.TraceTypeQuery.ECC_VISIBILITY, True,
                [a for a in actors() if isinstance(a, u.InstancedFoliageActor)], u.DrawDebugTrace.NONE, True)
            values = hit.to_tuple() if hit else None
            actual = values[5].z/100 if values and values[0] else None
            checks.append(dict(tile=t["id"], xy=[x, y], expected=expected, actual=actual))
            checks[-1]["traceDetails"] = [str(v) for v in values] if values else []
            if actual is None or abs(actual-expected) > .04:
                errors.append("Collision mismatch " + t["id"])
            weights = list(u.JadgSceneBuild.landscape_weights_at(land, u.Vector(x*100, y*100, expected*100), list(LAYERS)))
            expected_weights = [source_weights[layer*side*side+iy*side+ix]/255 for layer in range(7)]
            if len(weights) != 7 or abs(sum(weights)-1) > .04:
                errors.append("Native paint lost after reload " + t["id"])
            elif max(abs(a-b) for a, b in zip(weights, expected_weights)) > .025:
                errors.append("Native paint differs from authored layers " + t["id"])
            checks[-1]["paintWeights"] = weights
            checks[-1]["expectedPaintWeights"] = expected_weights
    all_actors = actors()
    count = sum(c.get_instance_count() for a in all_actors if isinstance(a, u.InstancedFoliageActor)
                for c in a.get_components_by_class(u.InstancedStaticMeshComponent))
    planned = json.loads((REPORT/row["id"]/"03-foliage.json").read_text())["instances"]
    if count != planned:
        errors.append("Foliage count changed after reload")
    unexpected = [a.get_actor_label() for a in all_actors if isinstance(a, u.StaticMeshActor) and "CapitalWater" not in [str(t) for t in a.tags]]
    if unexpected:
        errors.append("Unexpected static actors: " + str(unexpected))
    roots = project_roots(row, apply=False)
    if roots['changed']:
        errors.append('Foliage root height differs from native collision')
    report(row["id"]+"/04-audit.json", dict(probes=checks, instances=count, naniteTriangles=triangle_count,
                                            buildings=0, roots=roots, unexpectedStaticActors=unexpected, errors=errors))
    if errors:
        raise RuntimeError("; ".join(errors))


def review_map(row, all_districts=False):
    doc_path = jadg_map.TRIAL_LEVELS / ("capital-landscape/paysage-"+row["slug"]+".json")
    doc = jadg_map.read(doc_path)
    if all_districts:
        doc["shots"] = [json.loads((jadg_map.TRIAL_LEVELS/("capital-landscape/paysage-"+q["slug"]+".json")).read_text())["shots"][0]
                        for q in MANIFEST["districts"]]
        doc["name"] = "Paysage de la capitale — World Partition"
        doc_path = jadg_map.TRIAL_LEVELS/"capital-landscape/paysage-capitale.json"
        jadg_map.write(doc_path, doc)
    world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
    level = scene.Level(world)
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE))
    scene.place_sky(level, doc, frame)
    scene.place_frame(level, doc, frame, "capital-landscape/paysage-"+("capitale" if all_districts else row["slug"]), doc_path)
    scene.place_shots(level, doc, frame)
    if all_districts:
        level.spawn(u.PlayerStart, frame.map_point(doc['shots'][0]['target']),
                    u.Rotator(pitch=0, yaw=35, roll=0), 'DepartPaysage', '00_Inspection')
    world.get_world_settings().set_editor_property("default_game_mode", scene.game_class("JadgGameMode"))
    world.get_world_settings().set_editor_property("instanced_foliage_grid_size", 25200)
    paths = []
    for q in MANIFEST["districts"] if all_districts else [row]:
        streaming = u.EditorLevelUtils.add_level_to_world(world, package(q), u.LevelStreamingAlwaysLoaded)
        if streaming is None:
            raise RuntimeError("Sublevel assembly failed " + q["slug"])
        paths.append(package(q))
    target = ASSEMBLY if all_districts else LEVELS + "/paysage-"+row["slug"]
    if not u.EditorLoadingAndSavingUtils.save_map(world, target):
        raise RuntimeError("Review map save failed " + target)
    report("assembly.json" if all_districts else row["id"]+"/05-review-map.json", dict(package=target, levels=paths, buildings=0))


if __name__ == "__main__":
    key = scenery.command_line_option("CapitalDistrict") or "Q07"
    phase = scenery.command_line_option("CapitalPhase") or "all"
    row = district(key)
    if phase in ("all", "finish"):
        if phase == "all":
            relief(row)
        materials(row)
        foliage(row)
        audit(row)
        review_map(row)
    elif phase == "assemble":
        review_map(district("Q07"), all_districts=True)
    elif phase == "surfaces":
        material = build_surfaces(metropole=True)
        report("surface-material.json", dict(material=material.get_path_name(), buildings=0))
    elif phase == "grounding_all":
        for quarter in MANIFEST['districts']:
            grounding(quarter)
    else:
        {"relief": relief, "materials": materials, "foliage": foliage,
         "audit": audit, "review": review_map, "grounding": grounding}[phase](row)
