#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Sequential phases for /Game/Maps/Levels/capital-landscape/arenarea.

Inputs: atlas definition, supplied /Game/Fab, previous terrain laboratory meshes.
Outputs: /Game/Capitale/Ressources/Arenarea and the one Arenarea map above.
Run by review_arenarea_landscape.ps1. No other district is rebuilt.
"""

from pathlib import Path
from array import array
import json
import sys
import time
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import build_level as scene  # noqa: E402
import jadg_map  # noqa: E402
import arenarea_landscape_materials as mats  # noqa: E402
import import_scenery_unreal as scenery  # noqa: E402

REPORT = ROOT / "Saved/Jadg/arenarea-landscape"
MAP_ID = "capital-landscape/arenarea"
PACKAGE = "/Game/Maps/Levels/capital-landscape/arenarea"
CONTENT = mats.CONTENT
DOC = jadg_map.TRIAL_LEVELS / (MAP_ID + ".json")


def save(world, phase, data):
    if not u.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        raise RuntimeError("Map save failed")
    u.EditorAssetLibrary.save_directory(CONTENT, only_if_is_dirty=False, recursive=True)
    data.update(
        phase=phase, package=PACKAGE, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    (REPORT / (phase + ".json")).write_text(json.dumps(data, indent=2), encoding="utf8")
    print("ARENAREA_PHASE_OK", phase)


def context():
    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    terrain = [a for a in actors if isinstance(a, u.Landscape)]
    if world is None or len(terrain) != 1:
        raise RuntimeError("Expected the saved Arenarea Landscape")
    return world, terrain[0], actors


def relief():
    definition = json.loads(
        (ROOT / "Source/Elements/Terrain/arenarea/definition.json").read_text(encoding="utf8")
    )
    material = mats.build(relief=True)
    doc = jadg_map.read(DOC)
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(
        scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE)
    )
    world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
    level = scene.Level(world)
    heights = array("H")
    heights.frombytes((REPORT / "heights.r16").read_bytes())
    weights = list((REPORT / "weights.r8").read_bytes())
    qx, qy = definition["quads"]
    ox, oy = definition["origin_m"]
    step = definition["spacing_m"] * 100
    land = u.JadgSceneBuild.spawn_landscape(
        world,
        u.Vector(ox * 100, oy * 100, 0),
        u.Vector(step, step, 100),
        qx,
        qy,
        heights.tolist(),
        list(mats.LAYERS),
        weights,
        material,
        CONTENT + "/Layers",
        True,
    )
    del weights, heights
    if land is None:
        raise RuntimeError("Landscape import failed")
    scene.Level.name(land, "Arenarea_Relief", "01_Relief")
    if not u.JadgSceneBuild.finalize_landscape_layers(land):
        raise RuntimeError("Landscape paint requires -AllowCommandletRendering")
    # Nanite is built during phase 2, after the final material is assigned.
    land.set_editor_property("enable_nanite", False)
    source = ROOT / "Source/Elements/Assets/Built/arenarea-landscape/arenarea-eaux.glb"
    folder = CONTENT + "/Meshes/arenarea-eaux"
    path = folder + "/StaticMeshes/SM_arenarea-eaux"
    mesh = scenery.import_glb(source, CONTENT + "/Meshes", folder, path)
    settings = mesh.get_editor_property("nanite_settings")
    settings.enabled = False
    mesh.set_editor_property("nanite_settings", settings)
    water_path = CONTENT + "/Materials/M_Eau"
    al = u.EditorAssetLibrary
    water = (
        al.load_asset(water_path)
        if al.does_asset_exist(water_path)
        else al.duplicate_asset("/Game/Capitale/Ressources/M_Eau", water_path)
    )
    if water is None:
        raise RuntimeError("Water shader source missing")
    mesh.set_material(0, water)
    al.save_loaded_asset(mesh, only_if_is_dirty=False)
    actor = level.spawn(mesh, u.Vector(), u.Rotator(), "Baie_Riviere_NaturalPool", "01_Relief/Eaux")
    actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("cast_shadow", False)
    for s in definition["sites"]:
        # Editor markers carry metric reservation names; no fake buildings.
        a = level.spawn(
            u.TargetPoint,
            u.Vector(s["xy_m"][0] * 100, -s["xy_m"][1] * 100, s["ground_z_m"] * 100),
            u.Rotator(),
            s["id"] + "_" + s["name"],
            "01_Relief/Reservations",
        )
        a.tags = ["ArenareaReservation", s["id"]]
    scene.place_sky(level, doc, frame)
    scene.place_navigation(level, doc, frame)
    scene.place_characters(level, doc, frame, scene.Library())
    scene.place_frame(level, doc, frame, MAP_ID, DOC)
    scene.place_shots(level, doc, frame)
    world.get_world_settings().set_editor_property(
        "default_game_mode", scene.game_class("JadgGameMode")
    )
    save(
        world,
        "01-relief-engine",
        {
            "quads": [qx, qy],
            "components": qx * qy // 3969,
            "material": material.get_path_name(),
            "north": "-Y",
            "water": "single layer, no collision",
            "buildings": "reservations only",
        },
    )


def materials():
    world, land, _ = context()
    material = mats.build()
    land.set_editor_property("landscape_material", material)
    if not u.JadgSceneBuild.finalize_landscape_layers(land):
        raise RuntimeError("Landscape paint requires -AllowCommandletRendering")
    land.set_editor_property("enable_nanite", True)
    if not u.JadgSceneBuild.build_landscape_nanite(land):
        raise RuntimeError("Nanite build failed")
    tris = [
        c.static_mesh.get_num_nanite_triangles()
        for c in land.get_components_by_class(u.LandscapeNaniteComponent)
    ]
    if not tris or min(tris) <= 0:
        raise RuntimeError("Nanite resources are empty")
    declared = [str(n) for n in u.JadgSceneBuild.landscape_layer_names(material)]
    if set(declared) != set(mats.LAYERS):
        raise RuntimeError("Layer mismatch")
    save(
        world,
        "02-materials",
        {
            "material": material.get_path_name(),
            "layers": declared,
            "naniteTriangles": tris,
            "sources": mats.sources(),
            "tessellation": False,
            "rvt": False,
        },
    )


def foliage():
    world, land, actors = context()
    if any(isinstance(a, u.InstancedFoliageActor) for a in actors):
        raise RuntimeError(
            "Foliage phase already present: rebuild relief/materials before replacing it"
        )
    plan = json.loads((REPORT / "foliage-plan.json").read_text(encoding="utf8"))
    rows = []
    al = u.EditorAssetLibrary
    for group in plan["groups"]:
        mesh = al.load_asset(group["mesh"])
        if mesh is None:
            raise RuntimeError("Missing foliage " + group["mesh"])
        tris = mesh.get_num_nanite_triangles()
        if tris <= 0:
            raise RuntimeError("Foliage Nanite data missing: " + group["mesh"])
        target = CONTENT + "/Foliage/FT_" + group["id"]
        ft = (
            al.load_asset(target)
            if al.does_asset_exist(target)
            else al.duplicate_asset(group["foliageType"], target)
        )
        if ft is None:
            raise RuntimeError("FoliageType copy failed")
        al.set_metadata_tag(ft, "ArenareaSource", group["foliageType"])
        al.save_loaded_asset(ft)
        transforms = [
            u.Transform(
                u.Vector(p[0] * 100, p[1] * 100, p[2] * 100),
                u.Rotator(0, p[3], 0),
                u.Vector(p[4], p[4], p[4]),
            )
            for p in group["instances"]
        ]
        planted = u.JadgFoliageBuild.plant_on_landscape(land, ft, transforms)
        if planted != len(transforms):
            raise RuntimeError("Could not attach foliage to Landscape: " + group["id"])
        rows.append(
            {
                "id": group["id"],
                "mesh": group["mesh"],
                "instances": len(transforms),
                "sourceNaniteTriangles": tris,
            }
        )
        print("ARENAREA_FOLIAGE", group["id"], len(transforms))
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if isinstance(a, u.InstancedFoliageActor):
            scene.Level.name(a, "Arenarea_Foliage", "03_Vegetation")
    save(
        world,
        "03-foliage",
        {
            "groups": rows,
            "instances": sum(r["instances"] for r in rows),
            "placement": "seeded; excludes roads, building parcels, submerged ground and steep banks",
            "sourceAssetsModified": False,
        },
    )


def audit():
    world, land, actors = context()
    report = {
        "naniteTriangles": [
            c.static_mesh.get_num_nanite_triangles()
            for c in land.get_components_by_class(u.LandscapeNaniteComponent)
        ],
        "foliageActors": sum(isinstance(a, u.InstancedFoliageActor) for a in actors),
        "probes": [],
        "errors": [],
    }
    report["foliageInstancesAfterReload"] = sum(
        c.get_instance_count()
        for a in actors
        if isinstance(a, u.InstancedFoliageActor)
        for c in a.get_components_by_class(u.InstancedStaticMeshComponent)
    )
    planted = json.loads((REPORT / "03-foliage.json").read_text(encoding="utf8"))["instances"]
    if report["foliageInstancesAfterReload"] != planted:
        report["errors"].append("Foliage count changed after reload")
    if not report["naniteTriangles"] or min(report["naniteTriangles"]) <= 0:
        report["errors"].append("Nanite empty after reload")
    heights = array("H")
    heights.frombytes((REPORT / "heights.r16").read_bytes())
    definition = json.loads(
        (ROOT / "Source/Elements/Terrain/arenarea/definition.json").read_text(encoding="utf8")
    )
    ox, oy = definition["origin_m"]
    nx = definition["quads"][0] + 1
    step = definition["spacing_m"]
    for x, y in [
        (-2464, -136),
        (-1418, -202),
        (-1216, -1418),
        (-2130, -440),
        (-1246, -430),
        (-1756, 944),
        (-1850, -640),
    ]:
        ix, iy = round((x - ox) / step), round((y - oy) / step)
        x, y = ox + ix * step, oy + iy * step
        expected = (heights[iy * nx + ix] - 32768) / 128
        hit = u.SystemLibrary.line_trace_single(
            world,
            u.Vector(x * 100, y * 100, 12000),
            u.Vector(x * 100, y * 100, -2000),
            u.TraceTypeQuery.ECC_VISIBILITY,
            True,
            [],
            u.DrawDebugTrace.NONE,
            True,
        )
        values = hit.to_tuple() if hit else None
        z = values[5].z / 100 if values and values[0] else None
        report["probes"].append({"xy": [x, y], "expected": expected, "collision": z})
        if z is None or abs(z - expected) > 0.04:
            report["errors"].append(f"Collision mismatch {x},{y}")
    (REPORT / "04-audit.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    if report["errors"]:
        raise RuntimeError("; ".join(report["errors"]))
    print("ARENAREA_AUDIT_OK")


def finalize():
    world, land, _ = context()
    point = u.Vector(-213000, -44000, 2300)
    before = list(u.JadgSceneBuild.landscape_weights_at(land, point, list(mats.LAYERS)))
    for name in mats.LAYERS:
        layer = u.EditorAssetLibrary.load_asset(CONTENT+"/Layers/LI_"+name)
        layer.set_editor_property("blend_method", u.LandscapeTargetLayerBlendMethod.FINAL_WEIGHT_BLENDING)
        u.EditorAssetLibrary.save_loaded_asset(layer)
    if not u.JadgSceneBuild.finalize_landscape_layers(land):
        raise RuntimeError("Final paint merge requires -AllowCommandletRendering")
    after = list(u.JadgSceneBuild.landscape_weights_at(land, point, list(mats.LAYERS)))
    if sum(after) < .9:
        raise RuntimeError("Empty native paint after merge: "+str(after))
    if not u.JadgSceneBuild.build_landscape_nanite(land):
        raise RuntimeError("Nanite refresh failed")
    save(world, "05-paint-finalized", {"before": before, "after": after})


if __name__ == "__main__":
    phase = scenery.command_line_option("JadgArenareaPhase") or "relief"
    {"relief": relief, "materials": materials, "foliage": foliage, "audit": audit,
     "finalize": finalize}[phase]()
