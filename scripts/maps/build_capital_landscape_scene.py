#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le paysage de la capitale impériale : son terrain, sa matière, son eau, sa carte d'ensemble.

En deux temps, comme les scènes témoins (D-52 : tout est texte, le binaire se régénère) :

    python scripts/maps/build_capital_landscape_scene.py --prepare
        hors du moteur : calcule le relief et les couches depuis le relevé
        (`capital_landscape_layout.py`, `capital_landscape.py`) et les écrit sous
        `Saved/Jadg/capital-landscape/` — hauteurs, une image par couche, les vagues de l'eau, un
        aperçu à relire —, puis la carte d'ensemble (`capital-landscape/ensemble`, format v5).

    UnrealEditor-Cmd.exe <projet> -run=pythonscript -script=<ce fichier, chemin absolu> -unattended -nullrhi
        dans l'éditeur, sans fenêtre : pose le niveau `/Game/Maps/Levels/capital-landscape/ensemble`.

Ce que le niveau porte :

  - un `Landscape` de 1512 × 1008 quads de 2 m (3 × 2 km), ses hauteurs et ses couches prises telles
    quelles sur les images préparées ; Nanite, pour que le déplacement de la matière se rende ;
  - sa matière, `/Game/Capitale/Ressources/MI_Capitale` : une instance de
    `/Game/Capitale/Ressources/M_SenseiTerrain_Landscape`, la copie de la matière du pack
    (`/Game/Bibliotheque/Materiaux/SenseiTerrain/Materials/M_SenseiTerrain`, posée par `install_terrain_packs.py`) portée au
    `Landscape` — ses cinq matières empilées, servies par les surfaces de `/Game/Surfaces` : mélange
    par hauteur, roche d'elle-même sur les pentes et en projection triplanaire, tuilage rompu de près
    et de loin, fondu au loin, variations de couleur et de relief ; déplacement nul dans la ville ;
  - l'eau de la baie, de la rivière, du ruisseau et du bassin : des surfaces séparées, d'une matière à
    une couche (`/Game/Capitale/Ressources/M_Eau`), ses vagues une texture calculée
    (`/Game/Capitale/Ressources/T_Vagues_N`) ;
  - le ciel, la table du jour, le groupe au seuil de l'arène, les cadrages — par `build_level.py`.

Sorties : `Saved/Jadg/capital-landscape/build.json`, l'empreinte du niveau à côté.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from array import array
from pathlib import Path

# Archived generator: the current construction world must not be overwritten.
if __name__ == "__main__":
    raise RuntimeError("Generateur historique archive apres nettoyage. Ouvrir /Game/Capitale/Cartes/Capitale ; restauration explicite requise pour regenerer les anciens essais.")

ROOT = Path(__file__).resolve().parents[2]
MAP_ID = "capital-landscape/ensemble"
LEVEL_PATH = ROOT / "Source/Test/Fixtures/Exploration/Levels/capital-landscape/ensemble.json"
REPORT_ROOT = ROOT / "Saved/Jadg/capital-landscape"
CONTENT = "/Game/CapitalLandscape"
Z_SCALE = 100.0  # 1/128 m (0,78125 cm) par pas : ± 256 m autour de l'acteur

sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import capital_landscape_layout as layout  # noqa: E402
import jadg_map  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- La préparation, hors du moteur --------------------------------------------------------------

def wave_normals(size: int = 512):
    """Une carte de normales de vagues, répétable : une somme de houles de fréquences entières."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(layout.SEED + 1)
    y, x = np.mgrid[0:size, 0:size] / size
    height = np.zeros((size, size))
    for _ in range(28):
        fx, fy = rng.integers(-9, 10, 2)
        if fx == 0 and fy == 0:
            continue
        height += np.sin(2 * np.pi * (fx * x + fy * y) + rng.uniform(0, 2 * np.pi)) / (fx * fx + fy * fy) ** 0.75
    gy, gx = np.gradient(height)
    # Une eau calme : la pente quadratique moyenne des vagues vaut 0,12.
    slope = 0.12 / np.sqrt(np.mean(gx * gx + gy * gy))
    normal = np.dstack([-gx * slope, -gy * slope, np.ones_like(height)])
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    return Image.fromarray(np.rint((normal * 0.5 + 0.5) * 255).astype(np.uint8), "RGB")


def level_doc(entry_height: float, heights) -> dict:
    """La carte d'ensemble : une clairière de marche au seuil de l'arène, les cadrages du paysage."""
    ex, ey = layout.metres(layout.ENTRY_UNITS)
    side = 20
    origin = [round(ex - side / 2 * jadg_map.CELL, 2), round(ey - side / 2 * jadg_map.CELL, 2)]
    shots = []
    comparison_path=ROOT/'scripts/maps/capital_comparison_shots.json'
    comparisons={s['id']:s for s in json.loads(comparison_path.read_text())} if comparison_path.exists() else {}
    for shot in layout.SHOTS:
        x, y = layout.metres(shot["target"])
        shots.append({"id": shot["id"], "target": [round(x, 1), round(y, 1), round(max(heights(x, y), layout.SEA_LEVEL)+shot.get('heightOffset',0), 1)],
                      "heading": shot["heading"], "pitch": shot["pitch"], "distance": shot["distance"]})
        if shot['id'] in comparisons:
            # Exact before/after camera poses. New close views follow revised streets.
            shots[-1]=dict(comparisons[shot['id']])
    return {
        "format": jadg_map.FORMAT, "version": jadg_map.VERSION,
        "name": "CapitalLandscape",
        "comment": "Le paysage de la capitale impériale, vue d'ensemble. Généré par "
                   "scripts/maps/build_capital_landscape_scene.py ; à juger par l'auteur.",
        "width": side, "height": side, "origin": origin,
        "storeys": [{"name": "seuil", "z": round(entry_height, 2)}],
        "nextEntityId": 1, "tiles": [{"x": side // 2, "y": side // 2, "type": "entry"}], "entities": [],
        "party": {"appearances": ["heros-brawler"], "walkSpeed": 3.0, "heading": 0.0},
        "lighting": {
            "comment": "Les réglages des quartiers ; une brume légère pour trois kilomètres de vue.",
            "sunScale": 1.65, "ambientScale": 0.34, "skyLuminance": 1.8, "exposureBias": 0.0,
            "fog": {"density": 0.0006, "falloff": 0.08, "volumetric": False},
            "post": {"bloom_intensity": 0.25, "vignette_intensity": 0.12,
                     "motion_blur_amount": 0.0, "film_grain_intensity": 0.0},
        },
        "daylight": jadg_map.DAYLIGHT,
        "ground": {"colour": "#0b0f08", "size": 40000.0, "height": layout.EDGE["floor"]},
        "navigation": {"area": list(layout.metres((100,120)))+list(layout.metres((1950,1440))),
                       "height": 140.0, "floor": -20.0},
        "shots": shots, "hours": ["12:00", "22:00"],
    }


def prepare() -> dict:
    import capital_landscape

    terrain = capital_landscape.generate()
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    files = {"hauteurs": REPORT_ROOT / "hauteurs.r16"}
    files["hauteurs"].write_bytes(terrain.height_units().tobytes())
    for name, mask in terrain.masks().items():
        files[name] = REPORT_ROOT / f"couche-{name}.r8"
        files[name].write_bytes(mask.tobytes())
    capital_landscape.preview(terrain).save(REPORT_ROOT / "apercu.png")
    wave_normals().save(REPORT_ROOT / "vagues.png")
    import capital_surface_materials
    capital_surface_materials.prepare()
    ex, ey = layout.metres(layout.ENTRY_UNITS)
    doc = level_doc(terrain.height_at(ex, ey), terrain.height_at)
    errors = jadg_map.validate(doc)
    if errors:
        raise RuntimeError("; ".join(errors))
    LEVEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    LEVEL_PATH.write_text(jadg_map.dumps(doc), encoding="utf-8", newline="\n")
    vertices = terrain.heights.size
    relief = {
        "quads": list(terrain.quads), "area": terrain.area, "resolution": layout.RESOLUTION,
        "seaLevel": layout.SEA_LEVEL, "lowest": float(terrain.heights.min()), "highest": float(terrain.heights.max()),
        "water": round(float(terrain.water.mean()), 4),
        "layers": {item["id"]: round(float(terrain.weights[item["id"]].sum()) / 255.0 / vertices, 4) for item in layout.LAYERS},
        "sha256": {name: sha256(path) for name, path in files.items()},
        "waves": sha256(REPORT_ROOT / "vagues.png"),
        "level": LEVEL_PATH.relative_to(ROOT).as_posix(), "levelSha256": sha256(LEVEL_PATH),
    }
    (REPORT_ROOT / "relief.json").write_text(json.dumps(relief, indent=1) + "\n", encoding="utf-8", newline="\n")
    import capital_urban_scene
    capital_urban_scene.prepare(terrain)
    return relief


# --- La construction, dans l'éditeur --------------------------------------------------------------

def read_relief() -> dict:
    path = REPORT_ROOT / "relief.json"
    if not path.is_file():
        raise RuntimeError("Lancer d'abord : python scripts/maps/build_capital_landscape_scene.py --prepare")
    relief = json.loads(path.read_text(encoding="utf-8"))
    for name, digest in relief["sha256"].items():
        file = REPORT_ROOT / ("hauteurs.r16" if name == "hauteurs" else f"couche-{name}.r8")
        if not file.is_file() or sha256(file) != digest:
            raise RuntimeError(f"{file.name} ne correspond plus à relief.json : relancer --prepare")
    if sha256(LEVEL_PATH) != relief["levelSha256"]:
        raise RuntimeError("La carte d'ensemble a changé depuis --prepare : la relancer")
    return relief


def ported_material(scene,for_horizon=False):
    """La copie de `M_SenseiTerrain` portée au `Landscape`, refaite à neuf depuis le pack : la matière
    et ses fonctions, sans plus aucun nœud du Mesh Terrain (ils ne se compilent pas dans le jeu lancé)."""
    import unreal

    spec = layout.MATERIAL
    assets = unreal.EditorAssetLibrary
    build = unreal.JadgSceneBuild
    if not assets.does_asset_exist(spec["source"]):
        scene.fail(f"{spec['source']} absente du poste : python scripts/assetsGeneration/install_terrain_packs.py")
    functions = f"{CONTENT}/HorizonFunctions" if for_horizon else f"{CONTENT}/Functions"
    destination=f"{CONTENT}/M_CapitalHorizon" if for_horizon else spec['ported']
    instance_path=f"{CONTENT}/MI_Horizon" if for_horizon else f"{CONTENT}/MI_Capitale"
    for stale in (destination,instance_path):
        if assets.does_asset_exist(stale) and not assets.delete_asset(stale):
            scene.fail(f"{stale} : l'ancien asset ne se supprime pas")
    if assets.does_directory_exist(functions) and not assets.delete_directory(functions):
        scene.fail(f"{functions} : les anciennes copies ne se suppriment pas")
    # Les fonctions du pack, copiées puis portées ; chaque copie appelle les copies.
    originals, copies = [], []
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for data in registry.get_assets_by_path(spec["functions"], recursive=False):
        original = data.get_asset()
        if not isinstance(original, unreal.MaterialFunction):
            continue
        copy = assets.duplicate_asset(str(data.package_name), f"{functions}/{data.asset_name}")
        if copy is None:
            scene.fail(f"{data.package_name} ne se copie pas")
        originals.append(original)
        copies.append(copy)
    material = assets.duplicate_asset(spec["source"], destination)
    if material is None:
        scene.fail(f"{spec['source']} ne se copie pas vers {spec['ported']}")
    ported: list[str] = []
    calls = 0
    for graph in [*copies, material]:
        ported += [str(name) for name in build.port_mesh_terrain_graph(graph,for_horizon) if str(name) not in ported]
        calls += build.retarget_function_calls(graph, originals, copies)
    missing = [item["channel"] for item in layout.LAYERS if item["channel"] and item["channel"] not in ported]
    if missing:
        scene.fail(f"{spec['source']} ne lit pas les canaux {missing} (elle lit {ported})")
    for copy in copies:
        unreal.MaterialEditingLibrary.update_material_function(copy, None)
    unreal.MaterialEditingLibrary.recompile_material(material)
    assets.save_directory(functions, only_if_is_dirty=False, recursive=True)
    assets.save_asset(destination, only_if_is_dirty=False)
    declared = [str(name) for name in build.landscape_layer_names(material)]
    scene.log(f"matière portée : {len(copies)} fonctions copiées, {calls} appels redirigés, couches {declared}")
    return material, ported, declared


def terrain_material(scene,for_horizon=False):
    """L'instance que le terrain porte : ses cinq matières servies par les surfaces, ses réglages du relevé."""
    import unreal

    library = unreal.MaterialEditingLibrary
    spec = layout.MATERIAL
    parent, ported, declared = ported_material(scene,for_horizon)
    name='MI_Horizon' if for_horizon else 'MI_Capitale'
    path = f"{CONTENT}/{name}"
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, CONTENT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    library.set_material_instance_parent(instance, parent)
    known = {
        "scalar": {str(n) for n in library.get_scalar_parameter_names(parent)},
        "vector": {str(n) for n in library.get_vector_parameter_names(parent)},
        "texture": {str(n) for n in library.get_texture_parameter_names(parent)},
        "switch": {str(n) for n in library.get_static_switch_parameter_names(parent)},
    }

    def check(kind: str, name: str) -> str:
        if name not in known[kind]:
            scene.fail(f"{spec['source']} n'a pas de paramètre « {name} » ({kind})")
        return name

    for item in layout.LAYERS:
        for role, texture_path in item["textures"].items():
            texture = unreal.EditorAssetLibrary.load_asset(texture_path)
            if texture is None:
                scene.fail(f"couche {item['id']} : surface absente du poste : {texture_path}")
            library.set_material_instance_texture_parameter_value(instance, check("texture", f"{role} {item['slot']}"), texture)
            if role == 'Height':
                library.set_material_instance_texture_parameter_value(instance, check('texture', f"Height Blend {item['slot']}"), texture)
    for name, slots in spec["layerScalars"].items():
        for slot, value in slots.items():
            library.set_material_instance_scalar_parameter_value(instance, check("scalar", f"{name} {slot}"), value)
    for name, slots in spec["layerVectors"].items():
        for slot, value in slots.items():
            library.set_material_instance_vector_parameter_value(instance, check("vector", f"{name} {slot}"), unreal.LinearColor(*value))
    for name, value in spec["scalars"].items():
        library.set_material_instance_scalar_parameter_value(instance, check("scalar", name), value)
    switches = dict(spec["switches"])
    for name, slots in spec["layerSwitches"].items():
        switches.update({f"{name} {slot}": value for slot, value in slots.items()})
    for name, value in switches.items():
        library.set_material_instance_static_switch_parameter_value(instance, check("switch", name), value)
    magnitude = spec["displacementMagnitude"]
    if magnitude is not None:
        overrides = instance.get_editor_property("base_property_overrides")
        scaling = unreal.DisplacementScaling()
        scaling.set_editor_property("magnitude", magnitude)
        scaling.set_editor_property("center", 0.5)
        overrides.set_editor_property("override_displacement_scaling", True)
        overrides.set_editor_property("displacement_scaling", scaling)
        instance.set_editor_property("base_property_overrides", overrides)
    displacement = "celle de la matière" if magnitude is None else f"{magnitude} cm"
    library.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return instance, declared, displacement


def wave_texture(scene):
    import unreal

    package = f"{CONTENT}/T_Vagues_N"
    task = unreal.AssetImportTask()
    task.filename = str(REPORT_ROOT / "vagues.png")
    task.destination_path, task.destination_name = package.rsplit("/", 1)
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(package)
    if not isinstance(texture, unreal.Texture2D):
        scene.fail("les vagues ne se sont pas importées en texture")
    texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    texture.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_asset(package, only_if_is_dirty=False)
    return texture


def water_material(scene, waves):
    """L'eau à une couche : le fond se voit sous les hauts-fonds, deux trains de vagues la rident."""
    import unreal

    library = unreal.MaterialEditingLibrary
    spec = layout.WATER_MATERIAL
    path = f"{CONTENT}/M_Eau"
    # Refaite à neuf : vider une matière n'ôte pas sa sortie d'eau, et elle n'en admet qu'une.
    if unreal.EditorAssetLibrary.does_asset_exist(path) and not unreal.EditorAssetLibrary.delete_asset(path):
        scene.fail(f"{path} : l'ancienne matière de l'eau ne se supprime pas")
    material = scene.new_material(path)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_SINGLE_LAYER_WATER)
    material.set_editor_property('two_sided',True)

    def node(kind, x: int, y: int):
        return library.create_material_expression(material, kind, x, y)

    def constant(value: float, x: int, y: int, name=None):
        expression = node(unreal.MaterialExpressionScalarParameter if name else unreal.MaterialExpressionConstant, x, y)
        if name: expression.set_editor_property('parameter_name', name)
        expression.set_editor_property("default_value" if name else "r", value)
        return expression

    def colour(values: list[float], x: int, y: int, name=None):
        expression = node(unreal.MaterialExpressionVectorParameter if name else unreal.MaterialExpressionConstant3Vector, x, y)
        if name: expression.set_editor_property('parameter_name', name)
        expression.set_editor_property("default_value" if name else "constant", unreal.LinearColor(values[0], values[1], values[2], 1.0))
        return expression

    def connect(source, output: str, target, name: str) -> None:
        if not library.connect_material_expressions(source, output, target, name):
            scene.fail(f"eau : l'entrée « {name} » ne se relie pas")

    position = node(unreal.MaterialExpressionWorldPosition, -1700, 0)
    flat = node(unreal.MaterialExpressionComponentMask, -1500, 0)
    for channel, value in (("r", True), ("g", True), ("b", False), ("a", False)):
        flat.set_editor_property(channel, value)
    connect(position, "", flat, "")
    samples = []
    for index, (period, speed) in enumerate(zip(spec["waveMetres"], spec["waveSpeed"])):
        scale = node(unreal.MaterialExpressionDivide, -1300, index * 320)
        connect(flat, "", scale, "A")
        connect(constant(period * 100.0, -1500, 140 + index * 320, f'WavePeriodCm{index}'), "", scale, "B")
        panner = node(unreal.MaterialExpressionPanner, -1100, index * 320)
        panner.set_editor_property("speed_x", speed)
        panner.set_editor_property("speed_y", speed * 0.6)
        velocity = node(unreal.MaterialExpressionComponentMask, -1200, 150+index*320)
        velocity.set_editor_property('r',True);velocity.set_editor_property('g',True)
        velocity.set_editor_property('b',False);velocity.set_editor_property('a',False)
        connect(colour([speed,speed*.6,0],-1400,120+index*320,f'WaveSpeed{index}'), 'RGB', velocity, '')
        connect(velocity, '', panner, 'Speed')
        connect(scale, "", panner, "Coordinate")
        sample = node(unreal.MaterialExpressionTextureSample, -900, index * 320)
        sample.set_editor_property("texture", waves)
        sample.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        connect(panner, "", sample, "UVs")
        samples.append(sample)
    summed = node(unreal.MaterialExpressionAdd, -600, 100)
    connect(samples[0], "RGB", summed, "A")
    connect(samples[1], "RGB", summed, "B")
    weighted = node(unreal.MaterialExpressionMultiply, -420, 100)
    connect(summed, "", weighted, "A")
    connect(colour([spec["waveStrength"], spec["waveStrength"], 0.5], -600, 300, 'WaveNormalScale'), "RGB", weighted, "B")
    normal = node(unreal.MaterialExpressionNormalize, -240, 100)
    connect(weighted, "", normal, "VectorInput")
    library.connect_material_property(normal, "", unreal.MaterialProperty.MP_NORMAL)
    library.connect_material_property(colour([0.0, 0.0, 0.0], -240, -300), "", unreal.MaterialProperty.MP_BASE_COLOR)
    library.connect_material_property(constant(spec["roughness"], -240, -150, 'Roughness'), "", unreal.MaterialProperty.MP_ROUGHNESS)
    library.connect_material_property(constant(0.225, -240, -60), "", unreal.MaterialProperty.MP_SPECULAR)
    # Opacité nulle : rien d'opaque à la surface, tout le rendu vient du volume d'eau et du fond.
    library.connect_material_property(constant(0.0, -240, 30), "", unreal.MaterialProperty.MP_OPACITY)
    output = node(unreal.MaterialExpressionSingleLayerWaterMaterialOutput, 0, 500)
    connect(colour(spec["scattering"], -240, 450, 'ScatteringPerCm'), "RGB", output, "ScatteringCoefficients")
    connect(colour(spec["absorption"], -240, 600, 'AbsorptionPerCm'), "RGB", output, "AbsorptionCoefficients")
    connect(constant(0.0, -240, 750), "", output, "PhaseG")
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def build_editor() -> None:
    import unreal

    import build_level as scene

    relief = read_relief()
    doc = jadg_map.read(LEVEL_PATH)
    library = scene.Library()
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE))
    east, south = frame.map_direction([1.0, 0.0, 0.0]), frame.map_direction([0.0, 1.0, 0.0])
    if (east.x, east.y, south.x, south.y) != (1.0, 0.0, 0.0, 1.0):
        scene.fail(f"le repère de la carte n'est pas celui du moteur (est {east}, sud {south})")

    import capital_surface_materials
    capital_surface_materials.build()
    material, declared, displacement = terrain_material(scene)
    water = water_material(scene, wave_texture(scene))

    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if world is None:
        scene.fail("le niveau vide n'a pas pu être créé")
    level = scene.Level(world)

    quads_x, quads_y = relief["quads"]
    heights = array("H")
    heights.frombytes((REPORT_ROOT / "hauteurs.r16").read_bytes())
    stacked = [item for item in layout.LAYERS if item["channel"]]
    weights: list[int] = []
    for item in stacked:
        weights += list((REPORT_ROOT / f"couche-{item['id']}.r8").read_bytes())
    x0, y0, x1, y1 = relief["area"]
    step = relief["resolution"] * 100.0
    folder = f"{CONTENT}/Couches"
    landscape = unreal.JadgSceneBuild.spawn_landscape(
        world, frame.map_point([x0, y0, 0.0]), unreal.Vector(step, step, Z_SCALE), quads_x, quads_y, heights.tolist(),
        [item["channel"] for item in stacked], weights, material, folder, False)
    if landscape is None:
        scene.fail("le Landscape n'a pas pu être créé")
    scene.Level.name(landscape, "Terrain", "terrain")
    unreal.EditorAssetLibrary.save_directory(folder, only_if_is_dirty=False, recursive=True)
    nanite = False
    if scene.scenery.command_line_option("JadgSansNanite") is None:
        landscape.set_editor_property("enable_nanite", True)
        nanite = bool(unreal.JadgSceneBuild.build_landscape_nanite(landscape))
        if not nanite:
            scene.log("terrain : la représentation Nanite ne s'est pas construite ; le déplacement ne se rendra pas")

    import capital_urban_scene
    urban_report = capital_urban_scene.build_editor(level, frame, library, water)

    # Offshore extension only; four non-overlapping water environments cover the terrain.
    plane = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
    offshore = 6000.0
    centre = [x0 - offshore/2, (y0 + y1) / 2, relief["seaLevel"]]
    sea = level.spawn(plane, frame.map_point(centre), unreal.Rotator(0, 0, 0), "Eau", "terrain",
                      unreal.Vector(offshore, y1 - y0, 1.0))
    sea.static_mesh_component.set_material(0, water)
    sea.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    sea.static_mesh_component.set_editor_property("cast_shadow", False)

    scene.place_sky(level, doc, frame)
    scene.place_navigation(level, doc, frame)
    characters = scene.place_characters(level, doc, frame, library)
    scene.place_frame(level, doc, frame, MAP_ID, LEVEL_PATH)
    scene.place_shots(level, doc, frame)
    import review_capital_navigation
    review_capital_navigation.build(level, frame, doc)
    world.get_world_settings().set_editor_property("default_game_mode", scene.game_class("JadgGameMode"))
    package = jadg_map.package(MAP_ID)
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, package):
        scene.fail(f"{package} : le niveau n'a pas pu être sauvé")
    digest, actors = scene.footprint(world)
    report = {
        "package": package, "digest": digest, "actors": len(actors), "characters": characters,
        "quads": [quads_x, quads_y], "components": [quads_x // 63, quads_y // 63],
        "vertices": (quads_x + 1) * (quads_y + 1), "resolutionMetres": relief["resolution"],
        "material": f"{CONTENT}/MI_Capitale", "parent": layout.MATERIAL["ported"], "source": layout.MATERIAL["source"],
        "declaredLayers": declared, "paintedLayers": {item["channel"]: item["id"] for item in stacked},
        "nanite": nanite, "displacement": displacement, "water": f"{CONTENT}/M_Eau",
        "reliefSha256": relief["sha256"], "levelSha256": relief["levelSha256"],
        "artisticApproval": "pending",
        "urban": urban_report,
    }
    (REPORT_ROOT / "build.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    scene.write_footprint(MAP_ID, digest, actors, {"terrainVertices": report["vertices"]})
    scene.log(f"paysage de la capitale : {quads_x} × {quads_y} quads, {len(layout.LAYERS)} couches, "
              f"Nanite {'oui' if nanite else 'non'}, empreinte {digest[:16]} ; {package}")
    import build_capital_material_witness
    build_capital_material_witness.build(frame, library)


def main() -> None:
    if "unreal" in sys.modules:
        build_editor()
        return
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prepare", action="store_true", required=True)
    parser.parse_args()
    relief = prepare()
    print(f"relief : {relief['quads'][0]} × {relief['quads'][1]} quads, de {relief['lowest']:.1f} à {relief['highest']:.1f} m ; "
          f"eau {relief['water']:.0%} ; couches {relief['layers']}")
    print((REPORT_ROOT / "apercu.png").relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
