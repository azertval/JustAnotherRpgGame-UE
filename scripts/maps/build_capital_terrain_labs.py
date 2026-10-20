#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Prepare and build three isolated capital terrain laboratories, never the city.

python scripts/maps/build_capital_terrain_labs.py --prepare
UnrealEditor-Cmd project -run=pythonscript -script=<this absolute path> -nullrhi
Maps: /Game/Maps/Levels/essai/capitale-sols-urbains,
      /Game/Maps/Levels/essai/capitale-rives,
      /Game/Maps/Levels/essai/capitale-terres-roches.
See Documentation/Guide/guide-essais-terrains-capitale.md for the replay command.
"""

from pathlib import Path
from array import array
import hashlib
import json
import math
import sys

# Archived generator: the current construction world must not be overwritten.
if __name__ == "__main__":
    raise RuntimeError("Generateur historique archive apres nettoyage. Ouvrir /Game/Capitale/Cartes/Capitale ; restauration explicite requise pour regenerer les anciens essais.")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import jadg_map  # noqa: E402
from capital_terrain_lab_materials import CONTENT, LAYERS  # noqa: E402

REPORT = ROOT / "Saved/Jadg/capital-terrain-labs"
ASSETS = ROOT / "Source/Elements/Assets/Built/capital-terrain-labs"
N = 127
MAPS = {
    "capitale-sols-urbains": {
        "name": "Terrasses et rues de la capitale",
        "base": 20,
        "entry": [42, 52],
        "shots": [
            {"id": "ensemble", "target": [0, 4, 21], "heading": 320, "pitch": 42, "distance": 68},
            {"id": "pavage", "target": [0, 0, 20.27], "heading": 300, "pitch": 32, "distance": 12},
            {
                "id": "raccord",
                "target": [-14, 10, 20.3],
                "heading": 310,
                "pitch": 35,
                "distance": 18,
            },
        ],
    },
    "capitale-rives": {
        "name": "Quais et berges de Tourmaline",
        "base": 0,
        "entry": [55, 50],
        "shots": [
            {"id": "ensemble", "target": [8, 2, 3.5], "heading": 300, "pitch": 38, "distance": 78},
            {"id": "quai", "target": [13, 0, 3.5], "heading": 295, "pitch": 32, "distance": 23},
            {"id": "berge", "target": [0, 30, 0.5], "heading": 300, "pitch": 30, "distance": 20},
        ],
    },
    "capitale-terres-roches": {
        "name": "Terres agricoles et affleurements",
        "base": 30,
        "entry": [43, 57],
        "shots": [
            {"id": "ensemble", "target": [0, 0, 31], "heading": 315, "pitch": 42, "distance": 78},
            {
                "id": "sillons",
                "target": [-15, 0, 30.2],
                "heading": 320,
                "pitch": 35,
                "distance": 20,
            },
            {"id": "rochers", "target": [23, -10, 34], "heading": 300, "pitch": 35, "distance": 25},
        ],
    },
}


def smooth(a, b, x):
    import numpy as np

    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def terrain(kind):
    import numpy as np

    y, x = np.mgrid[-63:64, -63:64].astype(float)
    if kind == "capitale-sols-urbains":
        h = 20 + 1.5 * smooth(17, 42, y) + 1.2 * np.exp(-((x + 37) ** 2 + (y + 30) ** 2) / 420)
        plaza = (1 - smooth(15, 22, np.abs(x))) * (1 - smooth(12, 18, np.abs(y)))
        h = h * (1 - plaza) + 20 * plaza
        grass = 0.85 * (1 - plaza)
        soil = 0.8 * plaza + 0.18
        sand = 0.05 + 0 * x
        wet = 0.03 + 0 * x
    elif kind == "capitale-rives":
        shore = x + 2 * np.sin(y / 15)
        h = -1.5 + 7 * smooth(-18, 30, shore) + 0.18 * np.sin(y / 12)
        quay = smooth(12, 17, x) * (1 - smooth(32, 37, x)) * (1 - smooth(18, 24, np.abs(y)))
        h = h * (1 - quay) + 3.5 * quay
        front = (1 - smooth(14, 15, x)) * (1 - smooth(18, 24, np.abs(y)))
        h = h * (1 - front) + np.minimum(h, -0.35 + 0.02 * (x - 14)) * front
        # The pavement is an actual 27cm mesh above its prepared foundation.
        h = np.where((x >= 15) & (x <= 33) & (np.abs(y) <= 18), 3.20, h)
        grass = smooth(3.5, 5.5, h)
        sand = 0.8 * (1 - grass)
        soil = 0.13 + quay
        wet = 0.9 * np.exp(-(((h - 0.2) / 0.65) ** 2))
    else:
        h = (
            30
            + 0.025 * y
            + 3.2 * np.exp(-((x - 25) ** 2 + (y + 12) ** 2) / 230)
            + 0.35 * np.sin(y / 14) * np.sin(x / 17)
        )
        field = (1 - smooth(8, 12, np.abs(x + 17))) * (1 - smooth(16, 23, np.abs(y)))
        h = h * (1 - field) + 30 * field
        road = np.exp(-(((x - 4 - 2 * np.sin(y / 18)) / 2.4) ** 4))
        grass = 0.8 * (1 - field) * (1 - road)
        soil = 0.2 + field + road
        sand = 0.06 + 0 * x
        wet = 0.01 + 0 * x
    dy, dx = np.gradient(h)
    rock = 0.02 + 0.9 * smooth(0.18, 0.6, np.sqrt(dx * dx + dy * dy))
    values = np.stack([grass, soil, sand, rock, wet])
    values /= values.sum(axis=0)
    weights = np.floor(values * 255).astype("uint8")
    # Largest remainder goes to the strongest layer, sum EXACTLY 255.
    rest = (255 - weights.sum(axis=0)).astype("uint8")
    dominant = np.argmax(values, axis=0)
    for i in range(5):
        weights[i] += rest * (dominant == i)
    return h, weights


def prepare():
    import numpy as np

    REPORT.mkdir(parents=True, exist_ok=True)
    for kind, spec in MAPS.items():
        h, weights = terrain(kind)
        encoded = np.rint(32768 + h * 128).astype("<u2")
        (REPORT / (kind + ".r16")).write_bytes(encoded.tobytes())
        (REPORT / (kind + ".r8")).write_bytes(weights.tobytes())
        # Core and Landscape share the same quantized samples, not an unrelated plane.
        quantized = (encoded.astype(float) - 32768) / 128
        doc = {
            "format": jadg_map.FORMAT,
            "version": jadg_map.VERSION,
            "name": spec["name"],
            "comment": "Prototype autonome de matières et modules ; atlas 15 octobre 2026. Pas une portion géoréférencée de la ville.",
            "width": 84,
            "height": 84,
            "origin": [-63, -63],
            "storeys": [{"name": "sol", "z": 0}],
            "groundHeightfield": {
                "width": N,
                "height": N,
                "origin": [-63, -63],
                "spacing": [1, 1],
                "heights": quantized.ravel().tolist(),
            },
            "nextEntityId": 1,
            "tiles": [{"x": spec["entry"][0], "y": spec["entry"][1], "type": "entry"}],
            "entities": [],
            "party": {"appearances": ["heros-brawler"], "walkSpeed": 3.0, "heading": 0},
            "lighting": {
                "sunScale": 1.65,
                "ambientScale": 0.38,
                "skyLuminance": 1.8,
                "exposureBias": 0,
                "fog": {"density": 0.0015, "falloff": 0.08, "volumetric": False},
                "post": {"bloom_intensity": 0.25, "vignette_intensity": 0.12},
            },
            "daylight": jadg_map.DAYLIGHT,
            "navigation": {"area": [-60, -60, 60, 60], "floor": -4, "height": 50},
            "shots": spec["shots"],
            "hours": ["12:00", "22:00"],
        }
        if kind == "capitale-rives":
            doc["tiles"] += [
                {"x": i, "y": j, "type": "deepWater"}
                for j in range(84)
                for i in range(84)
                if quantized[min(126, int((j + 0.5) * 1.5)), min(126, int((i + 0.5) * 1.5))] < 0.2
            ]
        path = jadg_map.TRIAL_LEVELS / "essai" / (kind + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(jadg_map.dumps(doc), encoding="utf8")
        assert (weights.sum(axis=0) == 255).all()
        print(kind, "altitude", round(float(h.min()), 3), round(float(h.max()), 3), "weights255 OK")


def build():
    import unreal as u
    import build_level as scene
    import import_scenery_unreal as scenery
    import capital_terrain_lab_materials as materials

    REPORT.mkdir(parents=True, exist_ok=True)
    reuse = "-JadgLabsReuseAssets" in u.SystemLibrary.get_command_line()
    if reuse:
        mats = {
            name: u.EditorAssetLibrary.load_asset(CONTENT + "/Materials/MI_" + name)
            for name in ("paving", "stone", "rock", "soil", "sand")
        }
        mats["landscape"] = u.EditorAssetLibrary.load_asset(
            CONTENT + "/Materials/MI_Landscape_Capitale"
        )
        mats["water"] = u.EditorAssetLibrary.load_asset(CONTENT + "/Materials/M_Eau_Demonstration")
        if not all(mats.values()):
            raise RuntimeError("Build materials before using JadgLabsReuseAssets")
    else:
        mats = materials.build()
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf8"))
    meshes = {}
    mesh_report = []
    for p in manifest["pieces"]:
        name = p["id"]
        folder = CONTENT + "/Meshes/" + name
        path = folder + "/StaticMeshes/SM_" + name
        source = ASSETS / p["file"]
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        mesh = (
            u.EditorAssetLibrary.load_asset(path)
            if u.EditorAssetLibrary.does_asset_exist(path)
            else None
        )
        if (
            mesh is None
            or u.EditorAssetLibrary.get_metadata_tag(mesh, "CapitalLabSource") != digest
        ):
            mesh = scenery.import_glb(source, CONTENT + "/Meshes", folder, path)
        scenery.finish(mesh)
        for slot in range(len(mesh.static_materials)):
            mesh.set_material(slot, mats[p["surfaceFamily"]])
        u.EditorAssetLibrary.set_metadata_tag(mesh, "CapitalLabSource", digest)
        u.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
        tri = mesh.get_num_nanite_triangles()
        if tri <= 0:
            raise RuntimeError("No built Nanite triangles: " + name)
        meshes[name] = mesh
        mesh_report.append(
            {
                "name": name,
                "asset": path,
                "naniteTriangles": tri,
                "sourceTriangles": p["triangles"],
                "collision": "complex-as-simple, fallback",
                "surface": p["surfaceFamily"],
                "sha256": digest,
            }
        )
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(
        scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE)
    )
    library = scene.Library()
    reports = []
    for kind, spec in MAPS.items():
        path = jadg_map.TRIAL_LEVELS / "essai" / (kind + ".json")
        doc = jadg_map.read(path)
        world = u.EditorLoadingAndSavingUtils.new_blank_map(False)
        level = scene.Level(world)
        heights = array("H")
        heights.frombytes((REPORT / (kind + ".r16")).read_bytes())
        weights = list((REPORT / (kind + ".r8")).read_bytes())
        landscape = u.JadgSceneBuild.spawn_landscape(
            world,
            frame.map_point([-63, -63, 0]),
            u.Vector(100, 100, 100),
            126,
            126,
            heights.tolist(),
            list(LAYERS),
            weights,
            mats["landscape"],
            CONTENT + "/Layers/" + kind,
            True,
        )
        if landscape is None:
            raise RuntimeError("Landscape failed " + kind)
        scene.Level.name(landscape, "Landscape_" + kind, "Terrain")
        landscape.set_editor_property("enable_nanite", True)
        # Built after all heights/weights are imported, never a flag-only result.
        if not u.JadgSceneBuild.build_landscape_nanite(landscape):
            raise RuntimeError("Nanite Landscape build failed")
        u.EditorAssetLibrary.save_directory(
            CONTENT + "/Layers", only_if_is_dirty=False, recursive=True
        )
        placed = []

        def ground(x, y, doc=doc):
            import district_surface

            return district_surface.ground_height(doc, x, y)

        def put(
            mesh,
            x,
            y,
            z=None,
            yaw=0,
            scale=(1, 1, 1),
            label=None,
            level=level,
            placed=placed,
            ground=ground,
        ):
            z = ground(x, y) if z is None else z
            actor = level.spawn(
                meshes[mesh],
                frame.map_point([x, y, z]),
                frame.rotation(yaw),
                label or mesh + "-" + str(len(placed)),
                "Modules/" + mesh,
                u.Vector(*scale),
            )
            placed.append({"mesh": mesh, "position": [x, y, z], "yaw": yaw, "scale": list(scale)})
            return actor

        if kind == "capitale-sols-urbains":
            for row in range(4):
                for col in range(5):
                    put("paves-" + str((col + row) % 3), -12 + col * 6, -9 + row * 6, 19.995)
            for i in range(10):
                put("bordure", -13.5 + 3 * i, -12.3, 20)
            for i in range(7):
                put("bordure", -15.3, -9 + 3 * i, 20, 90)
            put("bordure-angle", -15.4, -12.4, 20)
            for i in range(7):
                put("soutenement", -9 + i * 3, 25, 20)
            put("escalier", -13, 21.5, 20)
            put("rampe", 15, 20, 20)
            for x, y, v in [(-26, 12, 0), (-31, 18, 1), (26, -22, 2)]:
                put("roche-" + str(v), x, y, ground(x, y) - 0.25)
        elif kind == "capitale-rives":
            for row in range(6):
                for col in range(3):
                    put("paves-" + str((row + col) % 3), 18 + col * 6, -15 + row * 6, 3.23)
            for i in range(12):
                put("soutenement", 14.5, -16.5 + 3 * i, -0.1, 90, scale=(1, 1, 1.2))
            for i in range(6):
                put("bordure", 15.2, -13.5 + i * 6, 3.5, 90)
            for i in range(3):
                put("berge", -1, 24 + i * 12, -0.05, yaw=90)
            for i in range(9):
                x = -4 + 2 * math.sin(i)
                y = -30 + i * 4
                put("roche-" + str(i % 3), x, y, ground(x, y) - 0.4, 35 * i, scale=(1.1, 0.9, 0.7))
            plane = u.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
            water = level.spawn(
                plane,
                frame.map_point([-24, 0, 0]),
                u.Rotator(),
                "Eau_Tourmaline",
                "Eau",
                u.Vector(78, 126, 1),
            )
            water.static_mesh_component.set_material(0, mats["water"])
            water.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            water.static_mesh_component.set_editor_property("cast_shadow", False)
        else:
            for row in range(3):
                for col in range(2):
                    put("sillons", -20 + col * 6, -12 + row * 12, 29.99)
            for i in range(13):
                x = 23 + 7 * math.sin(i * 2.1)
                y = -10 + 7 * math.cos(i * 1.7)
                put(
                    "roche-" + str(i % 3),
                    x,
                    y,
                    ground(x, y) - 0.4,
                    yaw=i * 29,
                    scale=(1 + (i % 3) * 0.3, 1, 1 + (i % 2) * 0.4),
                )
            for i in range(4):
                put("berge", -30, 25 + i * 6, ground(-30, 25 + i * 6) - 0.6, yaw=90)
        # Shared physical ruler/lighting objects are ordinary 3D meshes, not image cards.
        cube = u.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
        sx, sy = spec["shots"][1]["target"][:2]
        for i in range(3):
            x, y = sx + 7 + i * 1.5, sy + 7
            z = ground(x, y)
            post = level.spawn(
                cube,
                frame.map_point([x, y, z + 1]),
                u.Rotator(),
                f"Repere_2m_{i}",
                "Reperes",
                u.Vector(0.12, 0.12, 2),
            )
            post.static_mesh_component.set_material(0, mats["stone"])
            light = level.spawn(
                u.PointLight,
                frame.map_point([x, y, z + 2.4]),
                u.Rotator(),
                f"Lanterne_{i}",
                "Lumieres",
            )
            light.light_component.set_mobility(u.ComponentMobility.MOVABLE)
            light.light_component.set_editor_property("intensity_units", u.LightUnits.CANDELAS)
            light.light_component.set_editor_property("intensity", 160.0)
            light.light_component.set_editor_property("attenuation_radius", 1600.0)
            light.light_component.set_editor_property("light_color", u.Color(255, 211, 157, 255))
        scene.place_sky(level, doc, frame)
        scene.place_navigation(level, doc, frame)
        scene.place_characters(level, doc, frame, library)
        scene.place_frame(level, doc, frame, "essai/" + kind, path)
        scene.place_shots(level, doc, frame)
        world.get_world_settings().set_editor_property(
            "default_game_mode", scene.game_class("JadgGameMode")
        )
        package = "/Game/Maps/Levels/essai/" + kind
        if not u.EditorLoadingAndSavingUtils.save_map(world, package):
            raise RuntimeError("Map save failed " + package)
        components = landscape.get_components_by_class(u.LandscapeNaniteComponent)
        ntris = [
            c.get_editor_property("static_mesh").get_num_nanite_triangles() for c in components
        ]
        if not ntris or min(ntris) <= 0:
            raise RuntimeError("Landscape lacks real Nanite geometry")
        report = {
            "package": package,
            "extentMetres": [126, 126],
            "quads": [126, 126],
            "landscapeComponents": 4,
            "landscapeNaniteTriangles": ntris,
            "layers": list(LAYERS),
            "placements": placed,
            "shots": doc["shots"],
            "heightSha256": hashlib.sha256((REPORT / (kind + ".r16")).read_bytes()).hexdigest(),
            "material": mats["landscape"].get_path_name(),
            "tessellation": False,
            "rvt": False,
        }
        reports.append(report)
        (REPORT / (kind + "-build.json")).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8"
        )
    u.EditorAssetLibrary.save_directory(CONTENT, only_if_is_dirty=False, recursive=True)
    (REPORT / "build.json").write_text(
        json.dumps(
            {
                "engine": "5.8.3",
                "meshes": mesh_report,
                "maps": reports,
                "artisticApproval": "pending",
                "generator": "scripts/maps/build_capital_terrain_labs.py",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf8",
    )
    print("CAPITAL_TERRAIN_LABS_OK", len(reports), "maps", len(meshes), "Nanite meshes")


if __name__ == "__main__":
    if "--prepare" in sys.argv:
        prepare()
    else:
        build()
