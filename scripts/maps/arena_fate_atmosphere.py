# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Install original volumetric fires and discreet atmosphere without Blueprints.

Call per sub-level with its prop dictionaries plus transient `actor` entries.
Call once in persistent level with metadata.atmospherePersistent=True, props=[].
The returned report distinguishes installed actors and optional API warnings.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
ASSETS = ROOT / "Source/Elements/Assets/Built/arena-fate-atmosphere"
PROPS = ROOT / "Source/Elements/Assets/Built/arena-fate-props/manifest.json"
CONTENT = "/Game/ArenaFate/Atmosphere"
VERSION = 2


def optional(obj, name, value, warnings):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as error:
        warnings.append(
            f"{obj.get_name() if hasattr(obj, 'get_name') else type(obj).__name__}.{name}: {error}"
        )
        return False


def fire_material():
    editing = unreal.MaterialEditingLibrary
    path = CONTENT + "/M_ArenaFire"
    material = (
        unreal.EditorAssetLibrary.load_asset(path)
        if unreal.EditorAssetLibrary.does_asset_exist(path)
        else None
    )
    if (
        material
        and editing.get_material_default_scalar_parameter_value(material, "AtmosphereVersion")
        == VERSION
    ):
        return material
    if material is None:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_ArenaFire", CONTENT, unreal.Material, unreal.MaterialFactoryNew()
        )
    if material is None:
        raise RuntimeError("Cannot create Arena fire parent material")
    editing.delete_all_material_expressions(material)
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", False)

    def node(kind, x, y):
        return editing.create_material_expression(material, kind, x, y)

    def connect(a, pin, b, input_pin):
        if not editing.connect_material_expressions(a, pin, b, input_pin):
            raise RuntimeError(
                f"Arena fire graph failed {a.get_name()}.{pin} -> {b.get_name()}.{input_pin}"
            )

    def constant(value, x=-1100, y=500):
        n = node(unreal.MaterialExpressionConstant, x, y)
        n.set_editor_property("r", value)
        return n

    def op(kind, a, ap, b, bp, x, y):
        n = node(kind, x, y)
        connect(a, ap, n, "A")
        connect(b, bp, n, "B")
        return n

    vertices = node(unreal.MaterialExpressionVertexColor, -1600, -350)
    clock = node(unreal.MaterialExpressionTime, -1600, 250)
    position = node(unreal.MaterialExpressionObjectPositionWS, -1600, 650)
    seed = node(unreal.MaterialExpressionComponentMask, -1400, 650)
    seed.set_editor_property("r", True)
    seed.set_editor_property("g", False)
    seed.set_editor_property("b", False)
    seed.set_editor_property("a", False)
    connect(position, "", seed, "")
    phase = op(unreal.MaterialExpressionMultiply, seed, "", constant(0.00037), "", -1200, 650)
    tip_weight = op(unreal.MaterialExpressionMultiply, vertices, "A", vertices, "A", -1200, -150)

    def oscillation(frequency, amplitude, y):
        t = op(
            unreal.MaterialExpressionMultiply,
            clock,
            "",
            constant(frequency, -1500, y),
            "",
            -1100,
            y,
        )
        t = op(unreal.MaterialExpressionAdd, t, "", phase, "", -900, y)
        s = node(unreal.MaterialExpressionSine, -700, y)
        s.set_editor_property("period", 1.0)
        connect(t, "", s, "")
        return op(
            unreal.MaterialExpressionMultiply, s, "", constant(amplitude, -700, y + 75), "", -500, y
        )

    x = oscillation(1.3, 1.8, 200)
    y = oscillation(0.91, 1.2, 450)
    z = oscillation(2.17, 0.65, 700)
    xy = op(unreal.MaterialExpressionAppendVector, x, "", y, "", -300, 300)
    xyz = op(unreal.MaterialExpressionAppendVector, xy, "", z, "", -100, 300)
    movement = op(unreal.MaterialExpressionMultiply, xyz, "", tip_weight, "", 100, 300)
    if not editing.connect_material_property(
        movement, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET
    ):
        raise RuntimeError("Arena fire WPO output could not connect")
    flicker = oscillation(5.7, 0.60, -450)
    brightness = op(unreal.MaterialExpressionAdd, flicker, "", constant(6.0), "", -300, -300)
    # VertexColor's RGB output is unnamed; "A" is the explicitly masked alpha output.
    glow = op(unreal.MaterialExpressionMultiply, vertices, "", brightness, "", 100, -300)
    if not editing.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
        raise RuntimeError("Arena fire emissive output could not connect")
    version = node(unreal.MaterialExpressionScalarParameter, -1600, 1000)
    version.set_editor_property("parameter_name", "AtmosphereVersion")
    version.set_editor_property("default_value", VERSION)
    editing.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def import_sound(entry, warnings):
    folder = CONTENT + "/Audio"
    name = "SW_" + entry["id"].replace("-", "_")
    path = folder + "/" + name
    existing = (
        unreal.EditorAssetLibrary.load_asset(path)
        if unreal.EditorAssetLibrary.does_asset_exist(path)
        else None
    )
    digest = hashlib.sha256((ASSETS / entry["file"]).read_bytes()).hexdigest()
    if (
        existing is None
        or unreal.EditorAssetLibrary.get_metadata_tag(existing, "JadgAtmosphereSha256") != digest
    ):
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(ASSETS / entry["file"]))
        task.set_editor_property("destination_path", folder)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        factory = unreal.SoundFactory()
        cue_enabled = optional(factory, "auto_create_cue", True, warnings)
        if cue_enabled:
            optional(factory, "include_looping_node", True, warnings)
            optional(factory, "include_attenuation_node", False, warnings)
            optional(factory, "include_modulator_node", False, warnings)
            optional(factory, "cue_package_suffix", "_Cue", warnings)
            optional(factory, "cue_volume", 1.0, warnings)
        task.set_editor_property("factory", factory)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        existing = unreal.EditorAssetLibrary.load_asset(path)
        if existing is None:
            raise RuntimeError(f"Arena ambience import failed: {entry['file']}")
        existing.set_editor_property("looping", True)
        unreal.EditorAssetLibrary.set_metadata_tag(existing, "JadgAtmosphereSha256", digest)
        unreal.EditorAssetLibrary.save_loaded_asset(existing)
    cue = (
        unreal.EditorAssetLibrary.load_asset(path + "_Cue")
        if unreal.EditorAssetLibrary.does_asset_exist(path + "_Cue")
        else None
    )
    if cue:
        unreal.EditorAssetLibrary.save_loaded_asset(cue)
        return cue
    warnings.append(f"SoundCue unavailable for {entry['id']}; playing looping SoundWave directly")
    return existing


def ambient(level, location, sound, label, volume, radius, warnings, spatial=True):
    actor = level.spawn(
        unreal.AmbientSound, location, unreal.Rotator(0, 0, 0), label, "Arena/Ambience"
    )
    component = actor.get_component_by_class(unreal.AudioComponent)
    if component is None:
        raise RuntimeError(f"No AudioComponent on {label}")
    settings = unreal.SoundAttenuationSettings()
    settings.set_editor_property("attenuate", True)
    settings.set_editor_property("spatialize", spatial)
    settings.set_editor_property("attenuation_shape", unreal.AttenuationShape.SPHERE)
    settings.set_editor_property(
        "attenuation_shape_extents", unreal.Vector(75.0 if spatial else 6000.0, 0, 0)
    )
    settings.set_editor_property("falloff_distance", radius * 100 - (75.0 if spatial else 6000.0))
    optional(settings, "enable_occlusion", True, warnings)
    optional(settings, "use_complex_collision_for_occlusion", True, warnings)
    optional(settings, "occlusion_low_pass_filter_frequency", 1200.0, warnings)
    optional(settings, "occlusion_volume_attenuation", 0.25, warnings)
    component.set_editor_property("override_attenuation", True)
    component.set_editor_property("attenuation_overrides", settings)
    component.set_sound(sound)
    component.set_volume_multiplier(volume)
    component.set_editor_property("auto_activate", True)
    actor.tags = ["JadgArenaAtmosphere", "JadgArenaAudio"]
    return actor


def fire_location(frame, doc, item, source):
    actor = item.get("actor")
    if actor:
        local = frame.map_point(source)
        return unreal.MathLibrary.transform_location(actor.get_actor_transform(), local)
    # Position/yaw fallback uses the same clockwise map convention as Frame.rotation.
    scale = item.get("scale", 1.0)
    scale = scale if isinstance(scale, list) else [scale] * 3
    local = [source[k] * scale[k] for k in range(3)]
    a = math.radians(item.get("yaw", 0))
    position = list(item["position"])
    position[0] += local[0] * math.cos(a) + local[1] * math.sin(a)
    position[1] += -local[0] * math.sin(a) + local[1] * math.cos(a)
    position[2] += local[2] + doc["storeys"][item.get("storey", 0)]["z"]
    return frame.map_point(position)


def fixture_lighting(doc, item, prop):
    """Map text owns interior reach/intensity; other maps retain their defaults.

    Tune lighting.interiorProfiles by zone or lighting.fixtureOverrides by exact
    object ID. lightCandelas/lightRadius on an object have highest precedence.
    Exterior and honour loges use their previously approved prop values.
    """
    floor_z = float(doc["storeys"][item.get("storey", 0)]["z"])
    default = 40.0 if abs(floor_z - 12.0) < 0.01 else (12.0 if floor_z <= -11.0 else 18.0)
    profile = {}
    zone = item.get("lightingZone")
    if floor_z < 0:
        profiles = doc.get("lighting", {}).get("interiorProfiles", {})
        if zone is None:
            zone = next(
                (
                    name
                    for name in ("vestiaire", "prison", "salle-des-morts", "chapelle")
                    if name in item["id"]
                ),
                "corridor",
            )
        profile.update(profiles.get(zone, {}))
        profile.update(doc.get("lighting", {}).get("fixtureOverrides", {}).get(item["id"], {}))
    candelas = float(
        item.get("lightCandelas", profile.get("candelas", prop["light"].get("candelas", default)))
    )
    radius = float(item.get("lightRadius", profile.get("radius", prop["light"]["radius"])))
    if not math.isfinite(candelas) or candelas <= 0 or not math.isfinite(radius) or radius <= 0:
        raise RuntimeError(f"Invalid fixture intensity/radius on {item['id']}")
    return {"candelas": candelas, "radius": radius, "zone": zone}


def install(level, frame, doc, library, metadata, prop_objects):
    """Return a serialisable report; no global loop without explicit persistent flag."""
    manifest = json.loads((ASSETS / "manifest.json").read_text(encoding="utf-8"))
    props = {item["id"]: item for item in json.loads(PROPS.read_text(encoding="utf-8"))["meshes"]}
    audio = {item["id"]: item for item in manifest["audio"]}
    warnings, flames, local_audio, global_audio, paths, local_lights = [], [], [], [], [], []
    active = [
        (item, props.get(Path(item["mesh"]).stem))
        for item in prop_objects
        if props.get(Path(item["mesh"]).stem, {}).get("light")
    ]
    persistent = (
        metadata.get("atmospherePersistent", False)
        if isinstance(metadata, dict)
        else getattr(metadata, "atmospherePersistent", False)
    )
    if active:
        material = fire_material()
        paths.append(material.get_path_name())
        mesh = library.static_mesh("Built/arena-fate-atmosphere/afa-flame.glb")
        # These tiny dynamic fires deliberately use the ordinary WPO vertex path.
        # Architecture and all approved props retain their Nanite settings.
        nanite = mesh.get_editor_property("nanite_settings")
        if nanite.enabled:
            nanite.enabled = False
            mesh.set_editor_property("nanite_settings", nanite)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        # Fire is not architecture: no collision, no shadow, no navigation obstacle.
        for item, prop in active:
            identifier = Path(item["mesh"]).stem
            spec = manifest["placements"].get(
                identifier,
                {
                    "flameScale": prop["light"].get("flameScale", 0.16),
                    "audio": None,
                },
            )
            location = fire_location(frame, doc, item, prop["light"]["position"])
            flame_location = fire_location(
                frame, doc, item, prop["light"].get("flamePosition", prop["light"]["position"])
            )
            size = spec["flameScale"]
            flame_actor = level.spawn(
                mesh,
                flame_location,
                frame.rotation(item.get("yaw", 0)),
                "Fire:" + item["id"],
                "Arena/Fire",
                unreal.Vector(size, size, size),
            )
            component = flame_actor.static_mesh_component
            component.set_mobility(unreal.ComponentMobility.MOVABLE)
            component.set_material(0, material)
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_editor_property("cast_shadow", False)
            component.set_editor_property("bounds_scale", 1.25)
            optional(component, "evaluate_world_position_offset", True, warnings)
            flame_actor.tags = ["JadgArenaAtmosphere", "JadgArenaFire"] + [
                tag for tag in item["actor"].tags if str(tag).startswith("JadgWitnessSupport:")
            ]
            light = level.spawn(
                unreal.PointLight,
                location,
                unreal.Rotator(0, 0, 0),
                "FireLight:" + item["id"],
                "Arena/Fire",
            )
            lamp = light.point_light_component
            lamp.set_mobility(unreal.ComponentMobility.MOVABLE)
            lamp.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
            settings = fixture_lighting(doc, item, prop)
            candelas = settings["candelas"]
            lamp.set_editor_property("intensity", candelas)
            lamp.set_editor_property("attenuation_radius", settings["radius"] * 100)
            lamp.set_editor_property("source_radius", 8.0)
            lamp.set_editor_property("volumetric_scattering_intensity", 0.35)
            color = prop["light"]["color"].lstrip("#")
            lamp.set_editor_property(
                "light_color",
                unreal.Color(
                    r=int(color[0:2], 16), g=int(color[2:4], 16), b=int(color[4:6], 16), a=255
                ),
            )
            lamp.set_editor_property("cast_shadows", True)
            light.tags = ["JadgArenaAtmosphere", "JadgArenaFireLight"] + [
                tag for tag in item["actor"].tags if str(tag).startswith("JadgWitnessSupport:")
            ]
            local_lights.append(
                {
                    "actor": light.get_actor_label(),
                    "candelas": candelas,
                    "radiusMetres": settings["radius"],
                    "zone": settings["zone"],
                    "fixtureId": item["id"],
                    "always": True,
                }
            )
            flames.append(
                {
                    "prop": item["id"],
                    "actor": flame_actor.get_actor_label(),
                    "locationCm": [flame_location.x, flame_location.y, flame_location.z],
                    "scale": size,
                }
            )
            if spec.get("audio"):
                sound = import_sound(audio[spec["audio"]], warnings)
                sound_actor = ambient(
                    level,
                    location,
                    sound,
                    "Crackle:" + item["id"],
                    spec["volume"],
                    spec["audioRadiusMetres"],
                    warnings,
                )
                local_audio.append(sound_actor.get_actor_label())
                if sound.get_path_name() not in paths:
                    paths.append(sound.get_path_name())
    if persistent:
        spec = manifest["globalAudio"]
        sound = import_sound(audio[spec["id"]], warnings)
        actor = ambient(
            level,
            frame.map_point(spec["position"]),
            sound,
            "ArenaExteriorBreeze",
            spec["volume"],
            spec["audioRadiusMetres"],
            warnings,
            spatial=False,
        )
        global_audio.append(actor.get_actor_label())
        paths.append(sound.get_path_name())
    return {
        "version": manifest["version"],
        "flames": flames,
        "localAudio": local_audio,
        "globalAudio": global_audio,
        "localLights": local_lights,
        "assetPaths": paths,
        "warnings": warnings,
        "audioProvenance": "Original wind and wood crackles only; no crowd or voice",
    }
