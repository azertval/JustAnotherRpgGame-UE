# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Independent Wicked-inspired painted witness materials, editor-only.

build_materials(style) returns eight saved MaterialInterface objects, keyed by
stone_cream, marble_white, bronze, dark_metal, burgundy, sand, wood and mortar. Supported
style: painted, plus optional chamber_stone and chamber_floor overrides.
UV0 must repeat every two metres.
Existing approved PNGs are read, hashed and imported into this witness's own
package namespace. Their colour, analytic physical normals and ORM stay separate.
No asset belonging to the approved Arena is changed. Copy this module into the
project's scripts/assetsGeneration folder before importing it from Unreal.
All output lives under /Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/.
This candidate is subject to image review; its parameters are not a new standard.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import unreal

SCRIPTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
import import_scenery_unreal as scenery  # noqa: E402 - the editor adds this local script directory

ROOT = Path(unreal.Paths.project_dir()).resolve()
TEXTURES = ROOT / "Source/Elements/Assets/Built/arena-witness-materials"
STYLES = ("painted",)
NAMES = ("stone_cream", "marble_white", "bronze", "dark_metal", "burgundy", "sand", "wood", "mortar")
VERSION = 5
GRAPH_VERSION = 3
# Texture maps remain full PBR inputs. Only source UV phase and the authored
# stone block pigment vary; metals, fabric and wood keep neutral COLOR_0.
# COLOR_0.A is the stable seed of each authored solid, including its bevels.
BLOCK_PARAMETERS = {
    "stone_cream": {"UVOffsetStrength": 1.0, "BlockValueStrength": 0.85, "BlockWarmthStrength": 0.55},
    "marble_white": {"UVOffsetStrength": 1.0, "BlockValueStrength": 0.38, "BlockWarmthStrength": 0.45},
}
# All sampled roughness detail is retained before clamping to an authored range.
# Marble is satin, not the glossy floor material used everywhere in the old proof.
# Physical normal amplitudes are tuned independently of colour and roughness.
FINISHES = {
    "stone_cream": {"RoughnessScale": 1.0, "RoughnessBias": 0.02, "RoughnessMin": 0.78, "RoughnessMax": 0.96, "NormalStrength": 0.50, "Specular": 0.32, "ColourGain": 1.06},
    "marble_white": {"RoughnessScale": 0.60, "RoughnessBias": 0.40, "RoughnessMin": 0.48, "RoughnessMax": 0.64, "NormalStrength": 0.24, "Specular": 0.38, "ColourGain": 1.02},
    "bronze": {"RoughnessScale": 1.0, "RoughnessBias": 0.06, "RoughnessMin": 0.36, "RoughnessMax": 0.76, "NormalStrength": 0.58, "Specular": 0.50, "ColourGain": 0.97},
    "dark_metal": {"RoughnessScale": 1.0, "RoughnessBias": 0.06, "RoughnessMin": 0.48, "RoughnessMax": 0.76, "NormalStrength": 0.64, "Specular": 0.50, "ColourGain": 0.96},
    "burgundy": {"RoughnessScale": 1.0, "RoughnessBias": 0.06, "RoughnessMin": 0.90, "RoughnessMax": 0.98, "NormalStrength": 0.48, "Specular": 0.22, "ColourGain": 0.94},
    "sand": {"RoughnessScale": 1.0, "RoughnessBias": 0.0, "RoughnessMin": 0.92, "RoughnessMax": 1.0, "NormalStrength": 0.55, "Specular": 0.20, "ColourGain": 1.02},
    "wood": {"RoughnessScale": 1.0, "RoughnessBias": 0.07, "RoughnessMin": 0.72, "RoughnessMax": 0.94, "NormalStrength": 0.72, "Specular": 0.28, "ColourGain": 0.96},
    "mortar": {"RoughnessScale": 1.0, "RoughnessBias": 0.04, "RoughnessMin": 0.90, "RoughnessMax": 1.0, "NormalStrength": 0.55, "Specular": 0.22, "ColourGain": 0.97},
}
# Optional placement overrides, sharing the independent stone maps and tangent
# convention. They supplement the eight GLB slots without changing those slots.
ALIASES = {"chamber_stone": "stone_cream", "chamber_floor": "stone_cream",
           "roof_terracotta": "stone_cream", "pottery": "stone_cream", "linen": "burgundy"}
FINISHES.update({
    "chamber_stone": {**FINISHES["stone_cream"], "RoughnessMin": 0.86, "RoughnessMax": 0.98, "NormalStrength": 0.42, "Specular": 0.25, "ColourGain": 0.90},
    "chamber_floor": {**FINISHES["stone_cream"], "RoughnessBias": 0.08, "RoughnessMin": 0.90, "RoughnessMax": 0.98, "NormalStrength": 0.34, "Specular": 0.23, "ColourGain": 0.83},
    "roof_terracotta": {**FINISHES["stone_cream"], "RoughnessMin": 0.83, "RoughnessMax": 0.95, "NormalStrength": 0.18, "ColourGain": 1.0, "ColourDetail": 0.035},
    "pottery": {**FINISHES["stone_cream"], "RoughnessMin": 0.89, "RoughnessMax": 0.98, "NormalStrength": 0.16, "ColourGain": 1.0, "ColourDetail": 0.10},
    "linen": {**FINISHES["burgundy"], "NormalStrength": 0.30, "ColourGain": 1.0, "ColourDetail": 0.0},
})
FINISHES["chamber_stone"]["ColourDetail"] = 0.45
# Planche validee de l'arene (arena-of-fate-planche-v1) : sable pale et uni (#d9c7a3), pierre
# ivoire et miel (#efe6d2) ; dans la lumiere de la capitale, le sable peint lisait orange et en damier.
FINISHES["sand"]["ColourDetail"] = 0.35
FINISHES["stone_cream"]["ColourGain"] = 1.0
FINISHES["wood"].update({"ColourDetail": 0.7, "ColourGain": 0.80, "NormalStrength": 0.38})
TINTS = {"chamber_stone": (0.92, 0.94, 1.0), "chamber_floor": (0.88, 0.90, 0.96),
         "wood": (0.88, 0.92, 1.0), "stone_cream": (1.04, 1.10, 1.22)}
QUIET_COLOURS = {"chamber_stone": (0.35, 0.28, 0.19), "wood": (0.12, 0.055, 0.025),
                 "roof_terracotta": (0.115, 0.018, 0.012), "pottery": (0.24, 0.085, 0.035),
                 "linen": (0.62, 0.56, 0.45), "sand": (0.62, 0.53, 0.38)}


def parent_material(folder, defaults):
    library = unreal.MaterialEditingLibrary
    path = f"{folder}/M_ArenaWickedWitness"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        material = unreal.EditorAssetLibrary.load_asset(path)
        if library.get_material_default_scalar_parameter_value(material, "WitnessVersion") == GRAPH_VERSION:
            return material
    else:
        material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "M_ArenaWickedWitness", folder, unreal.Material, unreal.MaterialFactoryNew())
    library.delete_all_material_expressions(material)

    def node(kind, x, y):
        return library.create_material_expression(material, kind, x, y)

    def connect(source, output, destination, pin):
        if not library.connect_material_expressions(source, output, destination, pin):
            raise RuntimeError(f"PBR graph connection failed: {source.get_name()}/{output} -> {destination.get_name()}/{pin}")

    def property_connection(source, output, prop):
        if not library.connect_material_property(source, output, prop):
            raise RuntimeError(f"PBR material output failed: {source.get_name()}/{output} -> {prop}")

    def scalar(name, default, x, y):
        result = node(unreal.MaterialExpressionScalarParameter, x, y)
        result.set_editor_property("parameter_name", name)
        result.set_editor_property("default_value", default)
        return result

    def constant(value, x, y):
        result = node(unreal.MaterialExpressionConstant, x, y)
        result.set_editor_property("r", value)
        return result

    def operation(kind, a, a_pin, b, b_pin, x, y):
        result = node(kind, x, y)
        connect(a, a_pin, result, "A")
        connect(b, b_pin, result, "B")
        return result

    vertices = node(unreal.MaterialExpressionVertexColor, -1800, -600)
    uv = node(unreal.MaterialExpressionTextureCoordinate, -1800, -200)
    uv.set_editor_property("coordinate_index", 0)
    # The source's alpha stores a stable per-solid seed. RGB stores the authored
    # block colour, with brighter bevels: never use RGB to drive UV offsets.
    # Use repeatable offsets only: no UV rotation/mirroring, which would require
    # rotating tangent normal components. Alpha is unused for opaque coverage.
    # Every role uses this EXACT same UV node, so physical details stay aligned.
    seeds = []
    for index, multiplier in enumerate((37.0, 53.0)):
        multiplied = operation(unreal.MaterialExpressionMultiply, vertices, "A",
                               constant(multiplier, -1800, index * 160), "", -1500, index * 160)
        fraction = node(unreal.MaterialExpressionFrac, -1300, index * 160)
        connect(multiplied, "", fraction, "")
        centred = operation(unreal.MaterialExpressionSubtract, fraction, "",
                            constant(0.5, -1500, 350), "", -1100, index * 160)
        seeds.append(centred)
    offset = operation(unreal.MaterialExpressionAppendVector, seeds[0], "", seeds[1], "", -950, 0)
    offset = operation(unreal.MaterialExpressionMultiply, offset, "",
                       scalar("UVOffsetStrength", 0.0, -1100, 400), "", -750, 0)
    shifted_uv = operation(unreal.MaterialExpressionAdd, uv, "", offset, "", -600, -200)
    samples = {}
    for i, (role, parameter, sampler) in enumerate((
        ("baseColor", "BaseColor", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),
        ("normal", "Normal", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL),
        ("orm", "ORM", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR),
    )):
        sample = library.create_material_expression(material, unreal.MaterialExpressionTextureSampleParameter2D, -500, i * 280)
        sample.set_editor_property("parameter_name", parameter)
        sample.set_editor_property("texture", defaults[role])
        sample.set_editor_property("sampler_type", sampler)
        connect(shifted_uv, "", sample, "UVs")
        samples[role] = sample
    # Colour per dressed block comes from the reproducible GLB, with neutral
    # white on metals/fabric. It is pigment variation, never baked illumination.
    value = node(unreal.MaterialExpressionLinearInterpolate, -900, -900)
    connect(constant(1.0, -1300, -950), "", value, "A")
    connect(vertices, "G", value, "B")
    connect(scalar("BlockValueStrength", 1.0, -1300, -1100), "", value, "Alpha")
    warmth = operation(unreal.MaterialExpressionSubtract, vertices, "R", vertices, "B", -1400, -700)
    warmth = operation(unreal.MaterialExpressionMultiply, warmth, "", constant(0.5, -1600, -800), "", -1200, -700)
    warmth = operation(unreal.MaterialExpressionMultiply, warmth, "",
                       scalar("BlockWarmthStrength", 1.0, -1400, -1200), "", -1000, -700)
    warm_red = operation(unreal.MaterialExpressionAdd, value, "", warmth, "", -700, -900)
    cool_blue = operation(unreal.MaterialExpressionSubtract, value, "", warmth, "", -700, -750)
    tint_rg = operation(unreal.MaterialExpressionAppendVector, warm_red, "", value, "", -500, -900)
    tint_rgb = operation(unreal.MaterialExpressionAppendVector, tint_rg, "", cool_blue, "", -300, -900)
    quiet = node(unreal.MaterialExpressionVectorParameter, -500, -1450)
    quiet.set_editor_property("parameter_name", "QuietColour")
    quiet.set_editor_property("default_value", unreal.LinearColor(0.3, 0.25, 0.18, 1.0))
    colour_detail = node(unreal.MaterialExpressionLinearInterpolate, -100, -1200)
    connect(quiet, "RGB", colour_detail, "A")
    connect(samples["baseColor"], "RGB", colour_detail, "B")
    connect(scalar("ColourDetail", 1.0, -500, -1600), "", colour_detail, "Alpha")
    coloured = library.create_material_expression(material, unreal.MaterialExpressionMultiply, -100, 0)
    connect(colour_detail, "", coloured, "A")
    connect(tint_rgb, "", coloured, "B")
    gained = operation(unreal.MaterialExpressionMultiply, coloured, "",
                       scalar("ColourGain", 1.0, -100, -160), "", 130, 0)
    tint = node(unreal.MaterialExpressionVectorParameter, 130, -160)
    tint.set_editor_property("parameter_name", "ColourTint")
    tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    tinted = operation(unreal.MaterialExpressionMultiply, gained, "", tint, "RGB", 360, 0)
    property_connection(tinted, "", unreal.MaterialProperty.MP_BASE_COLOR)
    flat_normal = node(unreal.MaterialExpressionConstant3Vector, -160, 200)
    flat_normal.set_editor_property("constant", unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
    normal = node(unreal.MaterialExpressionLinearInterpolate, 130, 260)
    connect(flat_normal, "", normal, "A")
    connect(samples["normal"], "RGB", normal, "B")
    connect(scalar("NormalStrength", 1.0, -160, 370), "", normal, "Alpha")
    normal_unit = node(unreal.MaterialExpressionNormalize, 330, 260)
    connect(normal, "", normal_unit, "")
    property_connection(normal_unit, "", unreal.MaterialProperty.MP_NORMAL)
    rough = operation(unreal.MaterialExpressionMultiply, samples["orm"], "G",
                      scalar("RoughnessScale", 1.0, -160, 600), "", 130, 550)
    rough = operation(unreal.MaterialExpressionAdd, rough, "",
                      scalar("RoughnessBias", 0.0, -160, 730), "", 330, 550)
    bounded_rough = node(unreal.MaterialExpressionClamp, 550, 550)
    connect(rough, "", bounded_rough, "")
    connect(scalar("RoughnessMin", 0.0, 130, 800), "", bounded_rough, "Min")
    connect(scalar("RoughnessMax", 1.0, 330, 800), "", bounded_rough, "Max")
    property_connection(bounded_rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    property_connection(scalar("Specular", 0.35, 550, 1000), "", unreal.MaterialProperty.MP_SPECULAR)
    for role, output, prop in (
        ("orm", "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION),
        ("orm", "B", unreal.MaterialProperty.MP_METALLIC),
    ):
        property_connection(samples[role], output, prop)
    version = library.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -500, 950)
    version.set_editor_property("parameter_name", "WitnessVersion")
    version.set_editor_property("default_value", float(GRAPH_VERSION))
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    material.set_editor_property("two_sided", False)
    material.set_editor_property("used_with_instanced_static_meshes", True)
    material.set_editor_property("used_with_nanite", True)
    library.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    return material


def build_materials(style):
    """Build/save the candidate and return {semantic_slot: MaterialInterface}."""
    if style not in STYLES:
        raise ValueError(f"Unknown Arena witness style: {style!r}; expected {STYLES}")
    manifest_file = TEXTURES / "manifest.json"
    if not manifest_file.is_file():
        raise RuntimeError("Generate Arena witness textures before running the editor material script")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if manifest.get("tileMetres") != 2.0 or manifest.get("version") != VERSION:
        raise RuntimeError("Arena texture manifest does not match the two-metre UV/version contract")
    folder = f"/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/{style}"
    unreal.EditorAssetLibrary.make_directory(folder)
    material_textures = {}
    for name in NAMES:
        textures = {}
        for role in ("baseColor", "normal", "orm"):
            entry = manifest["styles"][style][name][role]
            source = TEXTURES / entry["file"]
            content = source.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if digest != entry["sha256"]:
                raise RuntimeError(f"Arena witness texture changed without regeneration: {source}")
            # Content-addressed paths avoid stale imports when the source changes.
            path = f"{folder}/Textures/T_{name}_{role}_{digest[:12]}"
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                texture = unreal.EditorAssetLibrary.load_asset(path)
                if not isinstance(texture, unreal.Texture2D):
                    raise RuntimeError(f"Expected Texture2D at {path}")
            else:
                texture = scenery.import_image(content, "png", path, role)
            if entry.get("nativeProcessing"):
                # The source PNG remains byte-identical. The engine's derived
                # texture performs its own power-of-two processing for mips.
                texture.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
                texture.set_editor_property("max_texture_size", 2048)
                texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
                texture.set_editor_property("never_stream", False)
                unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
            expected_compression = (unreal.TextureCompressionSettings.TC_NORMALMAP if role == "normal"
                                    else unreal.TextureCompressionSettings.TC_BC7)
            expected_srgb = role == "baseColor"
            if (texture.get_editor_property("compression_settings") != expected_compression
                    or texture.get_editor_property("srgb") != expected_srgb
                    or texture.get_editor_property("flip_green_channel") != (role == "normal")):
                raise RuntimeError(f"Wrong PBR colour space/compression/normal convention: {path}")
            textures[role] = texture
        material_textures[name] = textures
    parent = parent_material(folder, material_textures["stone_cream"])
    for alias, source in ALIASES.items():
        material_textures[alias] = material_textures[source]
    result = {}
    library = unreal.MaterialEditingLibrary
    for name, textures in material_textures.items():
        path = f"{folder}/MI_{name}"
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            instance = unreal.EditorAssetLibrary.load_asset(path)
        else:
            instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                f"MI_{name}", folder, unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
        if not isinstance(instance, unreal.MaterialInstanceConstant):
            raise RuntimeError(f"Expected MaterialInstanceConstant at {path}")
        library.set_material_instance_parent(instance, parent)
        for role, parameter in (("baseColor", "BaseColor"), ("normal", "Normal"), ("orm", "ORM")):
            library.set_material_instance_texture_parameter_value(instance, parameter, textures[role])
            assigned = library.get_material_instance_texture_parameter_value(instance, parameter)
            if assigned is None or assigned.get_path_name() != textures[role].get_path_name():
                raise RuntimeError(f"PBR texture binding did not stick: {path}/{parameter}")
        # Keep grain/cloth direction. Stone receives coherent phase offsets on
        # ALL maps; no UV rotation that would turn tangent normals incorrectly.
        parameters = {"ColourDetail": 1.0, **BLOCK_PARAMETERS.get(ALIASES.get(name, name), {"UVOffsetStrength": 0.0, "BlockValueStrength": 0.0, "BlockWarmthStrength": 0.0}), **FINISHES[name]}
        for parameter, value in parameters.items():
            library.set_material_instance_scalar_parameter_value(instance, parameter, value)
        library.set_material_instance_vector_parameter_value(instance, "ColourTint", unreal.LinearColor(*TINTS.get(name, (1.0, 1.0, 1.0)), 1.0))
        library.set_material_instance_vector_parameter_value(instance, "QuietColour", unreal.LinearColor(*QUIET_COLOURS.get(name, (0.3, 0.25, 0.18)), 1.0))
        library.update_material_instance(instance)
        unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
        result[name] = instance
    unreal.log(f"ArenaWickedWitness {style}: {len(result)} independent PBR materials; texture manifest v{VERSION}, graph v{GRAPH_VERSION}; matte porous stone, satin marble, dark wood, velvet and aged metals; preserved physical maps; candidate awaiting review")
    return result
