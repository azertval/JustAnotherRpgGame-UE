# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Reproducible district water, wind, fire/smoke, original local audio and residents.

Call build_environment(level, frame, doc, library, metadata) once in the persistent
world after static placement/navigation. Positions are authored world-map metres.
Then decorate_components(placed_objects, metadata) adds gentle wind to copied
material parents, keeping the source material/mesh untouched. Each placed object
is a dictionary with an `actor` and optional `motion` ('cloth' or 'foliage').
No import side effects; PCM synthesis and metadata validation run outside Unreal.
Runtime reports are emitted by JadgDistrictLife and do not imply audio audition.
"""

from __future__ import annotations

import array
import hashlib
import json
import math
import random
import sys
import wave
from pathlib import Path

try:
    import unreal
except ModuleNotFoundError:
    unreal = None

VERSION = 4
RATE = 22050
CONTENT = "/Game/Districts/Environment"
SOUNDS = ("breeze", "water", "market", "birds", "fire")
# World-space wavelengths in centimetres; the same ripples fit a fountain and a
# canal without stretching with the dimensions or UVs of their surface planes.
WATER_WAVES = (
    {"direction": (0.91, 0.4146), "wavelength": 137.0, "amplitude": 0.48, "frequency": 0.107, "phase": 0.0},
    {"direction": (-0.461, 0.8874), "wavelength": 91.0, "amplitude": 0.32, "frequency": -0.073, "phase": 0.37},
    {"direction": (0.305, -0.95235), "wavelength": 43.0, "amplitude": 0.055, "frequency": 0.163, "phase": 0.71},
)


def pcm_samples(kind: str, seconds: float = 12.0, rate: int = RATE) -> bytes:
    """Deterministic original mono PCM; loop edges fade to zero, no speech samples."""
    if kind not in SOUNDS or seconds <= 0 or rate < 1000:
        raise ValueError("Unsupported ambience or invalid PCM length/rate")
    rng = random.Random(int.from_bytes(hashlib.sha256(kind.encode()).digest()[:8], "big"))
    count = round(seconds * rate)
    samples = array.array("h")
    slow = medium = 0.0
    events = [(rng.uniform(0.6, seconds - 0.6), rng.uniform(0.12, 0.5), rng.uniform(1700, 3600))
              for _ in range(max(1, round(seconds / 2)))]
    for index in range(count):
        t = index / rate
        noise = rng.uniform(-1, 1)
        slow += 0.008 * (noise - slow)
        medium += 0.11 * (noise - medium)
        if kind == "breeze":
            value = slow * 1.9 * (0.64 + 0.25 * math.sin(t * 0.7)) + medium * 0.035
        elif kind == "water":
            value = medium * 0.65 + slow * 0.4 + noise * 0.055
            value += 0.045 * math.sin(t * 340 + 1.8 * math.sin(t * 6.1)) * (0.5 + 0.5 * math.sin(t * 4))
        elif kind == "fire":
            pop = rng.random() < 0.0012
            value = medium * 0.45 + slow * 0.5 + noise * (0.7 if pop else 0.012)
        elif kind == "market":
            # Quiet vowel-like resonances with independent syllable envelopes;
            # no recorded voices, words, names, music or external source material.
            value = slow * 0.5
            for voice in range(4):
                frequency = 91 + voice * 31
                envelope = max(0, math.sin(t * (2.3 + voice * 0.41) + voice)) ** 3
                value += envelope * (0.024 * math.sin(2 * math.pi * frequency * t)
                                     + 0.012 * math.sin(2 * math.pi * frequency * 3 * t))
        else:
            value = 0.0
            for start, length, pitch in events:
                dt = t - start
                if 0 <= dt < length:
                    envelope = math.sin(math.pi * dt / length) ** 2
                    phase = 2 * math.pi * (pitch * dt + 700 * dt * dt)
                    value += 0.12 * envelope * math.sin(phase)
        fade = min(1.0, index / (rate * 0.15), (count - 1 - index) / (rate * 0.15))
        samples.append(round(max(-0.95, min(0.95, value * fade)) * 32767))
    if sys.byteorder != "little":
        samples.byteswap()
    return samples.tobytes()


def generate_audio(folder: Path, seconds: float = 12.0) -> list[dict]:
    """PCM sources remain outside Git under Saved; this text script regenerates them."""
    folder.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind in SOUNDS:
        path = folder / f"district-{kind}-v{VERSION}.wav"
        if not path.exists():
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(RATE)
                output.writeframes(pcm_samples(kind, seconds))
        entries.append({"id": kind, "file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return entries


def validated_routes(metadata: dict) -> list[list[list[float]]]:
    routes = []
    for route in metadata.get("crowdRoutes", []):
        if len(route) < 2:
            raise ValueError("A district resident route requires at least two ground points")
        points = []
        for point in route:
            if len(point) != 3 or not all(math.isfinite(float(value)) for value in point):
                raise ValueError("District crowd points must be finite XYZ ground metres")
            points.append([float(value) for value in point])
        if all(point == points[0] for point in points):
            raise ValueError("A district resident route must contain distinct ground points")
        routes.append(points)
    return routes


def _required_engine():
    if unreal is None:
        raise RuntimeError("Environment installation runs in Unreal's editor Python")


def _asset_if_exists(path):
    """A missing generated asset is normal: do not emit an Unreal LoadAsset error."""
    library = unreal.EditorAssetLibrary
    return library.load_asset(path) if library.does_asset_exist(path) else None


def single_layer_water_api():
    """Resolve generated Python enum spelling, including CamelCase word splitting."""
    class_name = "MaterialExpressionSingleLayerWaterMaterialOutput"
    water_class = getattr(unreal, class_name, None)
    enum_type = getattr(unreal, "MaterialShadingModel", None)
    spellings = ("MSM_SINGLE_LAYER_WATER", "MSM_SINGLELAYERWATER", "MSM_SingleLayerWater")
    matching = [name for name in dir(enum_type) if
                "".join(char.lower() for char in name if char.isalnum()) == "msmsinglelayerwater"]
    selected, model = None, None
    for name in dict.fromkeys((*spellings, *matching)):
        value = getattr(enum_type, name, None) if enum_type is not None else None
        if value is not None:
            selected, model = name, value
            break
    diagnostic = {
        "className": class_name, "classAvailable": water_class is not None,
        "enumType": "MaterialShadingModel", "enumMember": selected,
        "enumCandidates": list(spellings), "matchingEnumMembers": matching,
    }
    return water_class, model, diagnostic


def _optional(obj, name, value, warnings):
    try:
        obj.set_editor_property(name, value)
    except Exception as error:
        warnings.append(f"{obj.get_name()}.{name}: {error}")


def _material(name: str, mode: str):
    """Small original animated graphs: opaque water, volumetric mesh fire, soft smoke."""
    editing = unreal.MaterialEditingLibrary
    path = CONTENT + "/Materials/" + name
    material = _asset_if_exists(path)
    if material and unreal.EditorAssetLibrary.get_metadata_tag(material, "DistrictVersion") == str(VERSION):
        return material
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, CONTENT + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"Unable to create district material {name}")
    editing.delete_all_material_expressions(material)

    def node(cls):
        return editing.create_material_expression(material, cls)

    def scalar(value):
        result = node(unreal.MaterialExpressionConstant)
        result.set_editor_property("r", value)
        return result

    def vector(x, y, z):
        result = node(unreal.MaterialExpressionConstant3Vector)
        result.set_editor_property("constant", unreal.LinearColor(x, y, z, 1))
        return result

    def op(cls, left, right, left_pin="", right_pin=""):
        result = node(cls)
        if not editing.connect_material_expressions(left, left_pin, result, "A"):
            raise RuntimeError("District material left input failed")
        if not editing.connect_material_expressions(right, right_pin, result, "B"):
            raise RuntimeError("District material right input failed")
        return result

    def output(source, prop):
        if not editing.connect_material_property(source, "", prop):
            raise RuntimeError(f"District material output failed: {prop}")

    time = node(unreal.MaterialExpressionTime)
    position = node(unreal.MaterialExpressionObjectPositionWS)
    mask = node(unreal.MaterialExpressionComponentMask)
    mask.set_editor_property("r", True)
    mask.set_editor_property("g", False)
    mask.set_editor_property("b", False)
    editing.connect_material_expressions(position, "", mask, "")
    phase = op(unreal.MaterialExpressionMultiply, mask, scalar(0.0037))
    clock = op(unreal.MaterialExpressionAdd, time, phase)

    def sine(frequency):
        result = node(unreal.MaterialExpressionSine)
        result.set_editor_property("period", 1.0)
        editing.connect_material_expressions(
            op(unreal.MaterialExpressionMultiply, clock, scalar(frequency)), "", result, "")
        return result

    if mode == "water":
        material.set_editor_property("two_sided", True)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
        material.set_editor_property("tangent_space_normal", False)
        world = node(unreal.MaterialExpressionWorldPosition)
        offsets = getattr(unreal, "WorldPositionIncludedOffsets", None)
        offset_mode = getattr(offsets, "WPT_EXCLUDE_ALL_SHADER_OFFSETS", None) if offsets else None
        if offset_mode is not None:
            world.set_editor_property("world_position_shader_offset", offset_mode)

        def coordinate(red, green):
            channel = node(unreal.MaterialExpressionComponentMask)
            for name, value in (("r", red), ("g", green), ("b", False), ("a", False)):
                channel.set_editor_property(name, value)
            if not editing.connect_material_expressions(world, "", channel, ""):
                raise RuntimeError("District water world coordinate input failed")
            return channel

        x, y = coordinate(True, False), coordinate(False, True)

        def oscillation(phase_node, cosine=False):
            result = node(unreal.MaterialExpressionSine)
            result.set_editor_property("period", 1.0)
            if cosine:
                phase_node = op(unreal.MaterialExpressionAdd, phase_node, scalar(0.25))
            if not editing.connect_material_expressions(phase_node, "", result, ""):
                raise RuntimeError("District water wave input failed")
            return result

        # Slow wave-group modulation breaks repeated specular stripes. Its space
        # scale is several metres, and its time scale several dozen seconds.
        broad_phase = op(unreal.MaterialExpressionAdd,
                         op(unreal.MaterialExpressionAdd,
                            op(unreal.MaterialExpressionMultiply, x, scalar(0.00061)),
                            op(unreal.MaterialExpressionMultiply, y, scalar(0.00043))),
                         op(unreal.MaterialExpressionMultiply, time, scalar(0.027)))
        broad = oscillation(broad_phase)
        strength = op(unreal.MaterialExpressionAdd, scalar(0.82),
                      op(unreal.MaterialExpressionMultiply, broad, scalar(0.18)))
        phase_warp = op(unreal.MaterialExpressionMultiply, oscillation(
            op(unreal.MaterialExpressionAdd, broad_phase, scalar(0.29))), scalar(0.10))
        normal_x, normal_y, height = scalar(0.0), scalar(0.0), scalar(0.0)
        for wave_spec in WATER_WAVES:
            dx, dy = wave_spec["direction"]
            wavelength, amplitude = wave_spec["wavelength"], wave_spec["amplitude"]
            phase_space = op(unreal.MaterialExpressionAdd,
                             op(unreal.MaterialExpressionMultiply, x, scalar(dx / wavelength)),
                             op(unreal.MaterialExpressionMultiply, y, scalar(dy / wavelength)))
            wave_phase = op(unreal.MaterialExpressionAdd,
                            op(unreal.MaterialExpressionAdd, phase_space, phase_warp),
                            op(unreal.MaterialExpressionAdd,
                               op(unreal.MaterialExpressionMultiply, time, scalar(wave_spec["frequency"])),
                               scalar(wave_spec["phase"])))
            ripple = oscillation(wave_phase)
            derivative = op(unreal.MaterialExpressionMultiply, oscillation(wave_phase, cosine=True), strength)
            slope = -2.0 * math.pi * amplitude / wavelength
            normal_x = op(unreal.MaterialExpressionAdd, normal_x,
                          op(unreal.MaterialExpressionMultiply, derivative, scalar(dx * slope)))
            normal_y = op(unreal.MaterialExpressionAdd, normal_y,
                          op(unreal.MaterialExpressionMultiply, derivative, scalar(dy * slope)))
            height = op(unreal.MaterialExpressionAdd, height,
                        op(unreal.MaterialExpressionMultiply,
                           op(unreal.MaterialExpressionMultiply, ripple, strength), scalar(amplitude)))
        normal_xy = op(unreal.MaterialExpressionAppendVector, normal_x, normal_y)
        normal_xyz = op(unreal.MaterialExpressionAppendVector, normal_xy, scalar(1))
        normal = node(unreal.MaterialExpressionNormalize)
        if not editing.connect_material_expressions(normal_xyz, "", normal, ""):
            raise RuntimeError("District water normal input failed")
        output(normal, unreal.MaterialProperty.MP_NORMAL)
        # Water is dielectric: no metal tint or baked light. A modestly rough
        # surface keeps broad, plausible moving reflections in the painted world.
        output(op(unreal.MaterialExpressionAdd, scalar(0.19),
                  op(unreal.MaterialExpressionMultiply, broad, scalar(0.025))), unreal.MaterialProperty.MP_ROUGHNESS)
        output(scalar(0.0), unreal.MaterialProperty.MP_METALLIC)
        output(scalar(0.25), unreal.MaterialProperty.MP_SPECULAR)
        movement = op(unreal.MaterialExpressionMultiply, vector(0, 0, 1), height)
        water_class, water_model, water_api = single_layer_water_api()
        logger = getattr(unreal, "log" if water_class is not None and water_model is not None else "log_warning", None)
        if callable(logger):
            logger("District water native API: " + json.dumps(water_api, sort_keys=True))
        unreal.EditorAssetLibrary.set_metadata_tag(material, "DistrictWaterApi", json.dumps(water_api, sort_keys=True))
        if water_class is not None and water_model is not None:
            material.set_editor_property("shading_model", water_model)
            water_output = node(water_class)
            names = editing.get_material_expression_input_names(water_output)
            inputs = {str(name).replace(" ", "").lower(): str(name) for name in names}
            for name, value in (
                ("ScatteringCoefficients", vector(0.00022, 0.00065, 0.00056)),
                ("AbsorptionCoefficients", vector(0.011, 0.0045, 0.0031)),
                ("PhaseG", scalar(0.18)),
                ("ColorScaleBehindWater", vector(1, 1, 1)),
            ):
                pin = inputs.get(name.lower())
                if pin is None or not editing.connect_material_expressions(value, "", water_output, pin):
                    raise RuntimeError(f"Native Single Layer Water input unavailable: {name}")
            output(vector(0.007, 0.022, 0.025), unreal.MaterialProperty.MP_BASE_COLOR)
            output(scalar(0.12), unreal.MaterialProperty.MP_OPACITY)
            output(scalar(1.333), unreal.MaterialProperty.MP_REFRACTION)
            backend = "SingleLayerWater"
        else:
            material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
            output(vector(0.028, 0.135, 0.145), unreal.MaterialProperty.MP_BASE_COLOR)
            backend = ("DefaultLit; SingleLayerWater unavailable: "
                       f"class={water_api['classAvailable']}, enumMember={water_api['enumMember']}")
        unreal.EditorAssetLibrary.set_metadata_tag(material, "DistrictWaterBackend", backend)
    elif mode == "fire":
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        vertex = node(unreal.MaterialExpressionVertexColor)
        brightness = op(unreal.MaterialExpressionAdd, scalar(5.0), sine(3.9))
        glow = op(unreal.MaterialExpressionMultiply, vertex, brightness)
        output(glow, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        weight = op(unreal.MaterialExpressionMultiply, vertex, vertex, "A", "A")
        movement = op(unreal.MaterialExpressionMultiply,
                      op(unreal.MaterialExpressionMultiply, vector(2.5, 1.5, 0.5), sine(1.31)), weight)
    else:
        material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
        output(vector(0.12, 0.10, 0.09), unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        fraction = node(unreal.MaterialExpressionFrac)
        editing.connect_material_expressions(
            op(unreal.MaterialExpressionMultiply, clock, scalar(0.2)), "", fraction, "")
        pulse = node(unreal.MaterialExpressionSine)
        pulse.set_editor_property("period", 2.0)
        editing.connect_material_expressions(fraction, "", pulse, "")
        fresnel = node(unreal.MaterialExpressionFresnel)
        fresnel.set_editor_property("exponent", 1.4)
        invert = node(unreal.MaterialExpressionOneMinus)
        if not editing.connect_material_expressions(fresnel, "", invert, ""):
            raise RuntimeError("District smoke opacity input failed")
        opacity = op(unreal.MaterialExpressionMultiply,
                     op(unreal.MaterialExpressionMultiply, invert, pulse), scalar(0.12))
        output(opacity, unreal.MaterialProperty.MP_OPACITY)
        movement = op(unreal.MaterialExpressionMultiply, vector(20, 5, 135), fraction)
    output(movement, unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    editing.recompile_material(material)
    unreal.EditorAssetLibrary.set_metadata_tag(material, "DistrictVersion", str(VERSION))
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def _audio(entry, warnings):
    folder = CONTENT + "/Audio"
    name = "SW_District_" + entry["id"]
    path = folder + "/" + name
    sound = _asset_if_exists(path)
    if sound is None or unreal.EditorAssetLibrary.get_metadata_tag(sound, "DistrictSource") != entry["sha256"]:
        factory = unreal.SoundFactory()
        # Wave.looping also works when cue generation is unavailable in a commandlet.
        _optional(factory, "auto_create_cue", False, warnings)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", entry["file"])
        task.set_editor_property("destination_path", folder)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        task.set_editor_property("factory", factory)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        sound = _asset_if_exists(path)
        if sound is None:
            raise RuntimeError(f"Cannot import original district sound: {entry['file']}")
        sound.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.set_metadata_tag(sound, "DistrictSource", entry["sha256"])
        unreal.EditorAssetLibrary.save_loaded_asset(sound)
    return sound


def _ambient(level, frame, sound, position, name, radius, volume, warnings):
    actor = level.spawn(unreal.AmbientSound, frame.map_point(position), unreal.Rotator(0, 0, 0),
                        name, "District/Ambience")
    component = actor.get_component_by_class(unreal.AudioComponent)
    if component is None:
        raise RuntimeError(f"AmbientSound has no audio component: {name}")
    settings = unreal.SoundAttenuationSettings()
    settings.set_editor_property("attenuate", True)
    settings.set_editor_property("spatialize", True)
    settings.set_editor_property("attenuation_shape", unreal.AttenuationShape.SPHERE)
    settings.set_editor_property("attenuation_shape_extents", unreal.Vector(100, 0, 0))
    settings.set_editor_property("falloff_distance", max(100, radius * 100 - 100))
    _optional(settings, "enable_occlusion", True, warnings)
    _optional(settings, "occlusion_low_pass_filter_frequency", 1400.0, warnings)
    _optional(settings, "occlusion_volume_attenuation", 0.35, warnings)
    component.set_editor_property("override_attenuation", True)
    component.set_editor_property("attenuation_overrides", settings)
    component.set_sound(sound)
    component.set_volume_multiplier(volume)
    component.set_editor_property("auto_activate", True)
    actor.tags = ["JadgDistrictAudio"]
    return {"id": name, "position": position, "radiusMetres": radius, "volume": volume,
            "asset": sound.get_path_name(), "auditioned": False}


def light_tags(item):
    """Interior fixtures stay lit at noon; only exterior lamps follow the day table."""
    fire = bool(item.get("fire", item.get("flame", False)))
    always = bool(item.get("always", False) or item.get("interior", False) or fire)
    tags = ["JadgDistrictLight"]
    if fire:
        tags.append("JadgDistrictFlicker")
    elif not always:
        tags.append("JadgLamp")
    if item.get("interior", False):
        tags.append("JadgDistrictInteriorLight")
    return tags, always


def build_environment(level, frame, doc, library, metadata) -> dict:
    _required_engine()
    warnings, waters, lights, fires, audio = [], [], [], [], []
    routes = validated_routes(metadata)
    root = Path(unreal.Paths.project_dir()).resolve()
    originals = generate_audio(root / "Saved/Jadg/district-environment/audio")
    sound_assets = {entry["id"]: _audio(entry, warnings) for entry in originals}
    water_material = _material("M_DistrictWater", "water")
    # Known engine packages need not be scanned into AssetRegistry by a commandlet.
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    sphere = unreal.load_asset("/Engine/BasicShapes/Sphere")
    if plane is None or sphere is None:
        raise RuntimeError("Required engine Plane/Sphere geometry is missing")
    for index, item in enumerate(metadata.get("waters", [])):
        position = item["position"]
        width, depth = item["size"]
        if width <= 0 or depth <= 0:
            raise ValueError("District water dimensions must be positive metres")
        actor = level.spawn(plane, frame.map_point(position), unreal.Rotator(0, 0, 0),
                            f"DistrictWater-{index:03}", "District/Water", unreal.Vector(width, depth, 1))
        component = actor.static_mesh_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_material(0, water_material)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("cast_shadow", False)
        component.set_editor_property("bounds_scale", 1.1)
        actor.tags = ["JadgDistrictWater"]
        waters.append({"position": position, "size": [width, depth], "animatedNormals": True,
                       "waveCoordinates": "absolute world centimetres; crossed waves with slow modulation",
                       "shading": unreal.EditorAssetLibrary.get_metadata_tag(water_material, "DistrictWaterBackend"),
                       "nativeApi": json.loads(unreal.EditorAssetLibrary.get_metadata_tag(water_material, "DistrictWaterApi") or "{}")})
        audio.append(_ambient(level, frame, sound_assets["water"], position,
                              f"DistrictWaterSound-{index:03}", 18, 0.35, warnings))

    flame_mesh = None
    for index, item in enumerate(metadata.get("lights", [])):
        position = item["position"]
        fire = bool(item.get("fire", item.get("flame", False)))
        light = level.spawn(unreal.PointLight, frame.map_point(position), unreal.Rotator(0, 0, 0),
                            f"DistrictLamp-{index:03}", "District/Lights")
        component = light.point_light_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        component.set_editor_property("intensity", float(item.get("candelas", 15)))
        component.set_editor_property("attenuation_radius", float(item.get("radius", 8)) * 100)
        component.set_editor_property("source_radius", 8.0)
        color = item.get("color", "#ffd49a").lstrip("#")
        component.set_editor_property("light_color", unreal.Color(
            r=int(color[:2], 16), g=int(color[2:4], 16), b=int(color[4:6], 16), a=255))
        component.set_editor_property("cast_shadows", bool(item.get("shadows", False)))
        tags, always = light_tags(item)
        light.tags = tags
        lights.append({"position": position, "radius": item.get("radius", 8),
                       "candelas": item.get("candelas", 15), "fire": fire,
                       "always": always, "interior": bool(item.get("interior", False))})
        if fire:
            if flame_mesh is None:
                source = root / "Source/Elements/Assets/Built/arena-fate-atmosphere/afa-flame.glb"
                if not source.exists():
                    raise RuntimeError("Original scripted 3D flame source missing; regenerate build_arena_fate_atmosphere.py")
                flame_mesh = library.static_mesh("Built/arena-fate-atmosphere/afa-flame.glb")
                # Preserve the library mesh; its original source/import remains regenerable.
                path = CONTENT + "/Meshes/SM_DistrictFlame"
                flame_mesh = (_asset_if_exists(path)
                              or unreal.EditorAssetLibrary.duplicate_asset(flame_mesh.get_path_name(), path))
                settings = flame_mesh.get_editor_property("nanite_settings")
                settings.enabled = False
                flame_mesh.set_editor_property("nanite_settings", settings)
                unreal.EditorAssetLibrary.save_loaded_asset(flame_mesh)
            scale = float(item.get("flameScale", 0.18))
            flame = level.spawn(flame_mesh, frame.map_point(position), unreal.Rotator(0, 0, 0),
                                f"DistrictFire-{index:03}", "District/Fire", unreal.Vector(scale, scale, scale))
            flame.static_mesh_component.set_material(0, _material("M_DistrictFire", "fire"))
            flame.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            flame.static_mesh_component.set_editor_property("cast_shadow", False)
            flame.static_mesh_component.set_editor_property("bounds_scale", 1.3)
            _optional(flame.static_mesh_component, "evaluate_world_position_offset", True, warnings)
            flame.tags = ["JadgDistrictFire"]
            smoke_position = [position[0], position[1], position[2] + 0.30]
            smoke = level.spawn(sphere, frame.map_point(smoke_position), unreal.Rotator(0, 0, 0),
                                f"DistrictSmoke-{index:03}", "District/Fire", unreal.Vector(0.28, 0.28, 0.55))
            smoke.static_mesh_component.set_material(0, _material("M_DistrictSmoke", "smoke"))
            smoke.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            smoke.static_mesh_component.set_editor_property("cast_shadow", False)
            smoke.static_mesh_component.set_editor_property("bounds_scale", 6.0)
            smoke.tags = ["JadgDistrictSmoke"]
            fires.append({"position": position, "scale": scale, "animatedVolume": True, "smoke": True})
            if len(fires) <= 8:
                audio.append(_ambient(level, frame, sound_assets["fire"], position,
                                      f"DistrictFireSound-{index:03}", 10, 0.16, warnings))

    xmin, ymin, xmax, ymax = metadata.get("area", [-30, -30, 30, 30])
    center = [(xmin + xmax) / 2, (ymin + ymax) / 2, 2]
    landmarks = metadata.get("landmarks", [])
    atmosphere_points = [item for item in landmarks if item.get("kind") in
                         ("market", "square", "plaza", "garden", "harbour", "harbor", "temple")]
    if not atmosphere_points:
        atmosphere_points = [{"id": "center", "kind": "square", "position": center}]
    for index, item in enumerate(atmosphere_points[:8]):
        position = list(item["position"])
        position[2] += 1.6
        market = item.get("kind") in ("market", "square", "plaza", "harbour", "harbor")
        audio.append(_ambient(level, frame, sound_assets["market" if market else "birds"], position,
                              f"DistrictLocalAmbience-{index:03}", 32 if market else 24,
                              0.22 if market else 0.16, warnings))
        audio.append(_ambient(level, frame, sound_assets["breeze"], position,
                              f"DistrictBreeze-{index:03}", 35, 0.2, warnings))
    life_class = unreal.load_class(None, "/Script/JustAnotherRpgGame.JadgDistrictLife")
    if life_class is None:
        raise RuntimeError("Compile JadgDistrictLife before installing district environment")
    life = level.spawn(life_class, frame.map_point(center), unreal.Rotator(0, 0, 0),
                       "DistrictLife", "District/Residents")
    count = int(metadata.get("crowdCount", 12))
    if not 0 <= count <= 32:
        raise ValueError("District population must be between 0 and 32")
    life.set_editor_property("crowd_count", count)
    life.set_editor_property("crowd_points", [frame.map_point(point) for route in routes for point in route])
    life.set_editor_property("crowd_route_lengths", [len(route) for route in routes])
    life.set_editor_property("crowd_appearances", metadata.get(
        "crowdAppearances", ["district-citizen-manny", "district-citizen-quinn"]))
    life.set_editor_property("resident_walk_speed", float(metadata.get("residentWalkSpeed", 1.5)) * 100)
    life.tags = ["JadgDistrictLife"]
    return {"version": VERSION, "waters": waters, "lights": lights, "fires": fires,
            "audio": audio, "audioSource": "Original deterministic PCM; five sources generated by this script",
            "audioAuditioned": False, "warnings": warnings,
            "population": {"requested": count, "routes": len(routes), "animated": True,
                           "navigation": "runtime complete paths, with rejected paths reported",
                           "appearances": list(life.get_editor_property("crowd_appearances")),
                           "visualLimitation": "Existing Mutable Manny/Quinn; civilian wardrobe unavailable",
                           "runtimeReport": "AJadgDistrictLife.GetLifeReportJson / [DistrictLifeReport] log"},
            "generatedAudio": originals}


def _wind_parent(parent, mode, warnings):
    """Duplicate the actual parent so all original pigment/PBR graph inputs survive."""
    if not isinstance(parent, unreal.Material):
        raise ValueError("Wind requires a resolved base Material")
    digest = hashlib.sha256(parent.get_path_name().encode()).hexdigest()[:12]
    folder = CONTENT + "/Wind"
    name = f"M_DistrictWind_{mode}_{digest}"
    path = folder + "/" + name
    copy = _asset_if_exists(path)
    if copy and unreal.EditorAssetLibrary.get_metadata_tag(copy, "DistrictVersion") == str(VERSION):
        return copy
    copy = copy or unreal.EditorAssetLibrary.duplicate_asset(parent.get_path_name(), path)
    if copy is None:
        raise RuntimeError(f"Cannot copy wind parent {parent.get_path_name()}")
    e = unreal.MaterialEditingLibrary

    def node(kind):
        return e.create_material_expression(copy, kind)

    def scalar(value):
        n = node(unreal.MaterialExpressionConstant)
        n.set_editor_property("r", value)
        return n

    def op(kind, a, b):
        n = node(kind)
        if not e.connect_material_expressions(a, "", n, "A") or not e.connect_material_expressions(b, "", n, "B"):
            raise RuntimeError("Wind graph input failed")
        return n

    def zmask(source):
        mask = node(unreal.MaterialExpressionComponentMask)
        mask.set_editor_property("r", False)
        mask.set_editor_property("g", False)
        mask.set_editor_property("b", True)
        e.connect_material_expressions(source, "", mask, "")
        return mask

    world = node(unreal.MaterialExpressionWorldPosition)
    origin = node(unreal.MaterialExpressionObjectPositionWS)
    bounds = node(unreal.MaterialExpressionObjectBounds)
    # ObjectBounds is the full size. Bottom weight=0, top weight=1; cloth inverts it.
    height = zmask(op(unreal.MaterialExpressionSubtract, world, origin))
    size = op(unreal.MaterialExpressionMax, zmask(bounds), scalar(1))
    weight = op(unreal.MaterialExpressionAdd,
                op(unreal.MaterialExpressionDivide, height, size), scalar(0.5))
    saturated = node(unreal.MaterialExpressionSaturate)
    if not e.connect_material_expressions(weight, "", saturated, ""):
        raise RuntimeError("Wind height anchor input failed")
    weight = saturated
    if mode == "cloth":
        inverse = node(unreal.MaterialExpressionOneMinus)
        if not e.connect_material_expressions(weight, "", inverse, ""):
            raise RuntimeError("Cloth wind anchor input failed")
        weight = inverse
    weight = op(unreal.MaterialExpressionMultiply, weight, weight)
    clock = node(unreal.MaterialExpressionTime)
    phase = op(unreal.MaterialExpressionAdd,
               op(unreal.MaterialExpressionMultiply, clock, scalar(0.47 if mode == "cloth" else 0.19)),
               op(unreal.MaterialExpressionMultiply, height, scalar(0.013)))
    sine = node(unreal.MaterialExpressionSine)
    sine.set_editor_property("period", 1.0)
    e.connect_material_expressions(phase, "", sine, "")
    direction = node(unreal.MaterialExpressionConstant3Vector)
    direction.set_editor_property("constant", unreal.LinearColor(3.2 if mode == "cloth" else 5.0, 1.1, 0, 1))
    movement = op(unreal.MaterialExpressionMultiply,
                  op(unreal.MaterialExpressionMultiply, sine, weight), direction)
    if not e.connect_material_property(movement, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET):
        raise RuntimeError("Wind WPO output failed")
    e.recompile_material(copy)
    unreal.EditorAssetLibrary.set_metadata_tag(copy, "DistrictVersion", str(VERSION))
    unreal.EditorAssetLibrary.save_loaded_asset(copy)
    return copy


_INSTANCE_PARAMETERS = (
    "scalar_parameter_values", "vector_parameter_values", "double_vector_parameter_values",
    "texture_parameter_values", "texture_collection_parameter_values", "parameter_collection_parameter_values",
    "runtime_virtual_texture_parameter_values", "sparse_volume_texture_parameter_values", "font_parameter_values",
    "base_property_overrides",
)


def _wind_interface(original, mode, warnings, cache=None, ancestry=None):
    """Clone every inherited instance, preserving local and inherited PBR/tint overrides.

    A leaf -> district tint -> approved textured instance -> master hierarchy keeps
    all four levels. Flattening the leaf onto a wind master would silently drop
    the district tint and the approved texture parameters inherited in the middle.
    Parameter arrays are copied again on regeneration to refresh already saved
    wind copies after an authored source instance changes.
    """
    cache = {} if cache is None else cache
    ancestry = set() if ancestry is None else ancestry
    key = (original.get_path_name(), mode)
    if key in cache:
        return cache[key]
    if key in ancestry:
        raise ValueError(f"Material parent cycle: {original.get_path_name()}")
    if isinstance(original, unreal.Material):
        animated = _wind_parent(original, mode, warnings)
        cache[key] = animated
        return animated
    if not isinstance(original, unreal.MaterialInstanceConstant):
        raise ValueError(f"Unsupported wind material interface: {original.get_path_name()}")
    parent = original.get_editor_property("parent")
    if parent is None:
        raise ValueError(f"Wind instance has no parent: {original.get_path_name()}")
    animated_parent = _wind_interface(parent, mode, warnings, cache, ancestry | {key})
    digest = hashlib.sha256((original.get_path_name() + mode).encode()).hexdigest()[:12]
    path = CONTENT + "/Wind/MI_DistrictWind_" + digest
    instance = (_asset_if_exists(path)
                or unreal.EditorAssetLibrary.duplicate_asset(original.get_path_name(), path))
    if instance is None:
        raise RuntimeError(f"Cannot clone wind instance {original.get_path_name()}")
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, animated_parent)
    for name in _INSTANCE_PARAMETERS:
        try:
            value = original.get_editor_property(name)
            # UE structs/arrays copy their value when assigned to the reflected property.
            instance.set_editor_property(name, value)
        except Exception as error:
            # The principal colour, physical and texture parameters must never be lost.
            if name in ("scalar_parameter_values", "vector_parameter_values", "texture_parameter_values"):
                raise RuntimeError(f"Could not preserve {original.get_path_name()}.{name}") from error
            warnings.append(f"{original.get_path_name()}.{name}: {error}")
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    unreal.EditorAssetLibrary.set_metadata_tag(instance, "DistrictVersion", str(VERSION))
    unreal.EditorAssetLibrary.save_loaded_asset(instance)
    cache[key] = instance
    return instance


def decorate_components(actors, metadata=None) -> dict:
    """Gentle wind on authored cloth/vegetation; geometry and source assets survive."""
    _required_engine()
    warnings, decorated, cache = [], [], {}
    for item in actors:
        actor = item.get("actor") if isinstance(item, dict) else item
        if actor is None:
            continue
        identifier = str(item.get("id", "") if isinstance(item, dict) else actor.get_actor_label())
        motion = item.get("motion") if isinstance(item, dict) else None
        label = (identifier + " " + str(item.get("mesh", "") if isinstance(item, dict) else "")).lower()
        if motion is None:
            if any(word in label for word in ("banner", "awning", "cloth", "drape", "banniere", "auvent")):
                motion = "cloth"
            elif any(word in label for word in ("cypress", "tree", "foliage", "hedge", "arbre", "cypres", "vegetal")):
                motion = "foliage"
        if motion not in ("cloth", "foliage"):
            continue
        component = actor.get_component_by_class(unreal.StaticMeshComponent)
        if component is None:
            continue
        slots = []
        for index in range(component.get_num_materials()):
            original = component.get_material(index)
            if original is None:
                continue
            animated = _wind_interface(original, motion, warnings, cache)
            component.set_material(index, animated)
            slots.append(animated.get_path_name())
        if slots:
            component.set_editor_property("bounds_scale", 1.1)
            _optional(component, "evaluate_world_position_offset", True, warnings)
            decorated.append({"id": identifier, "motion": motion, "materials": slots})
    return {"components": decorated, "warnings": warnings,
            "method": "Anchored shader wind on local copies; collision/static source geometry unchanged"}
