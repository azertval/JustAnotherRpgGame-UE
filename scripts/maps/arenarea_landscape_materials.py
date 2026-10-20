#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Phase 2: native, editable Landscape layers using the supplied Fab PBR maps.

Produces owned Arenarea or Metropole materials. /Game/Fab and /Game/Surfaces
are supplied library inputs; their meshes and textures are never rewritten.
"""

CONTENT = "/Game/Capitale/Ressources/Arenarea"
LAYERS = ("Pelouse", "Prairie", "HerbeSauvage", "Terre", "Sable", "Roche", "Pavage")


def sources():
    rows = {}
    for name, folder, code, tile in [
        ("Pelouse", "Lawn_Grass", "tkynejer", 200),
        ("Prairie", "Uncut_Grass", "oilpt20", 200),
        ("HerbeSauvage", "Wild_Grass", "sfknaeoa", 200),
    ]:
        base = (
            f"/Game/Bibliotheque/Scans/Megascans/Surfaces/{folder}_{code}/Raw/{code}_tier_0/Textures/T_{code}_8K_"
        )
        rows[name] = ([base + s for s in ("B", "N", "ORM")], "G", tile)
    rows["Terre"] = (
        ["/Game/Surfaces/ForestGround/T_ForestGround_" + s for s in ("A", "N", "R")],
        "R",
        250,
    )
    rows["Sable"] = (
        [
            "/Game/Surfaces/GravellySand/gravelly_sand_" + s
            for s in ("diff_1k", "nor_dx_1k", "arm_1k")
        ],
        "G",
        200,
    )
    rows["Roche"] = (
        ["/Game/Surfaces/RockVkmfaek/T_vkmfaek_1K_" + s for s in ("B", "N", "ORM")],
        "G",
        300,
    )
    rows["Pavage"] = (rows["Roche"][0], "G", 150)
    return rows


def build(relief=False, metropole=False):
    import unreal as u

    ml, al = u.MaterialEditingLibrary, u.EditorAssetLibrary
    at = u.AssetToolsHelpers.get_asset_tools()

    def asset(path, cls, factory):
        if al.does_asset_exist(path):
            return al.load_asset(path)
        folder, name = path.rsplit("/", 1)
        obj = at.create_asset(name, folder, cls, factory())
        if obj is None:
            raise RuntimeError("Could not create " + path)
        return obj

    suffix = "Relief" if relief else "Surfaces"
    output_content = "/Game/Capitale/Ressources/Metropole" if metropole else CONTENT
    material = asset(output_content + "/Materials/M_" + suffix, u.Material, u.MaterialFactoryNew)
    ml.delete_all_material_expressions(material)
    material.set_editor_property("used_with_nanite", True)
    count = 0

    def node(kind, **props):
        nonlocal count
        count += 1
        n = ml.create_material_expression(
            material,
            getattr(u, "MaterialExpression" + kind),
            -2000 + (count % 12) * 160,
            (count // 12) * 200,
        )
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def link(a, b, pin, out=""):
        if not ml.connect_material_expressions(a, out, b, pin):
            raise RuntimeError(
                f"Material link {a.get_class().get_name()} -> {b.get_class().get_name()} {pin}"
            )

    def scalar(name, value):
        return node("ScalarParameter", parameter_name=name, default_value=value)

    def op(kind, a, b=None, **kw):
        n = node(kind, **kw)
        link(a, n, "A" if kind in ("Add", "Multiply", "Divide", "Subtract") else "")
        if b is not None:
            link(b, n, "B")
        return n

    def rgb(a, out=""):
        n = node("ComponentMask", r=True, g=True, b=True)
        link(a, n, "", out)
        return n

    def scattered_uvs(uv):
        # Three translated samples on a triangular lattice. The original PBR
        # maps keep the same scale and orientation; all channels share offsets.
        # Explicit original UV gradients avoid mip seams at lattice boundaries.
        common = """
float2 p = float2(UV.x - UV.y * 0.577350269, UV.y * 1.154700538);
float2 cell = floor(p), f = frac(p);
float2 a, b, c; float3 w;
if (f.x + f.y < 1.0) {
    a=cell; b=cell+float2(1,0); c=cell+float2(0,1);
    w=float3(1-f.x-f.y,f.x,f.y);
} else {
    a=cell+float2(1,1); b=cell+float2(0,1); c=cell+float2(1,0);
    w=float3(f.x+f.y-1,1-f.x,1-f.y);
}
"""
        def custom(code, size):
            uv_input = u.CustomInput()
            uv_input.set_editor_property("input_name", "UV")
            n = node("Custom", code=common+code,
                output_type=getattr(u.CustomMaterialOutputType, "CMOT_FLOAT"+str(size)),
                inputs=[uv_input])
            link(uv, n, "UV")
            return n
        coords = [custom("float2 id="+key+"; return UV + frac(sin(float2(dot(id,float2(127.1,311.7)),dot(id,float2(269.5,183.3))))*43758.5453)*7;", 2)
                  for key in ("a", "b", "c")]
        weights = custom("w=pow(max(w,0),2); return w/max(dot(w,float3(1,1,1)),0.00001);", 3)
        channels = []
        for i in range(3):
            n = node("ComponentMask", r=i == 0, g=i == 1, b=i == 2)
            link(weights, n, "")
            channels.append(n)
        return coords, channels, op("DDX", uv), op("DDY", uv)

    # Read native paint weights explicitly. Their sum is normalized in the shader,
    # so independent UE 5.8 target layers also remain well-defined after painting.
    paint = {name: node("LandscapeLayerSample", parameter_name=name, preview_weight=1/7)
             for name in LAYERS}
    total = None
    for weight in paint.values():
        total = weight if total is None else op("Add", total, weight)
    total = op("Add", total, const_b=0.00001)
    blends = [None, None, None]
    for name, (paths, channel, tile) in sources().items():
        if relief:
            colors = {
                "Pelouse": (0.32, 0.34, 0.30),
                "Prairie": (0.32, 0.34, 0.30),
                "HerbeSauvage": (0.32, 0.34, 0.30),
                "Terre": (0.34, 0.32, 0.28),
                "Sable": (0.50, 0.46, 0.36),
                "Roche": (0.28, 0.29, 0.29),
                "Pavage": (0.58, 0.55, 0.48),
            }
            outputs = [
                node("Constant3Vector", constant=u.LinearColor(*colors[name], 1)),
                node("Constant3Vector", constant=u.LinearColor(0, 0, 1, 1)),
                node("Constant", r=0.85),
            ]
        else:
            wp = node("WorldPosition")
            xy = node("ComponentMask", r=True, g=True, b=False)
            link(wp, xy, "")
            uv = op("Divide", xy, scalar(name + "_TailleCm", tile))
            scatter = scattered_uvs(uv) if metropole else None
            samples = []
            for path, role in zip(paths, ("BC", "N", "ORM")):
                target = CONTENT + "/Textures/" + path.rsplit("/", 1)[1]
                tex = (
                    al.load_asset(target)
                    if al.does_asset_exist(target)
                    else al.duplicate_asset(path, target)
                )
                if tex is None:
                    raise RuntimeError("Missing supplied PBR texture " + path)
                tex.set_editor_property("srgb", role == "BC")
                tex.set_editor_property(
                    "compression_settings",
                    u.TextureCompressionSettings.TC_NORMALMAP
                    if role == "N"
                    else u.TextureCompressionSettings.TC_BC7,
                )
                al.set_metadata_tag(tex, "ArenareaSource", path)
                al.save_loaded_asset(tex)
                combined = None
                for i, coord in enumerate(scatter[0] if scatter else [uv]):
                    sample = node(
                        "TextureSampleParameter2D", parameter_name=name + "_" + role,
                        texture=tex,
                        sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == "N"
                        else u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == "BC"
                        else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
                        sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS,
                    )
                    if scatter:
                        sample.set_editor_property("mip_value_mode", u.TextureMipValueMode.TMVM_DERIVATIVE)
                        link(scatter[2], sample, "DDX(UVs)")
                        link(scatter[3], sample, "DDY(UVs)")
                    link(coord, sample, "UVs")
                    contribution = op("Multiply", rgb(sample), scatter[1][i]) if scatter else rgb(sample)
                    combined = contribution if combined is None else op("Add", combined, contribution)
                samples.append(combined)
            tint = node(
                "VectorParameter",
                parameter_name=name + "_Teinte",
                default_value=u.LinearColor(
                    *((1.12, 1.07, 0.94, 1) if name == "Pavage" else (1, 1, 1, 1))
                ),
            )
            color = op("Multiply", rgb(samples[0]), rgb(tint))
            # A broad world-space tone modulation breaks repetition without fake normals.
            axis = node("ComponentMask", r=True, g=False, b=False)
            link(wp, axis, "")
            wave = op("Sine", op("Divide", axis, scalar(name + "_VariationMetresCm", 6500)))
            macro = op("Add", op("Multiply", wave, const_b=0.04), const_b=0.96)
            color = op("Multiply", color, macro)
            normal = op("Normalize", rgb(samples[1]))
            rough = node("ComponentMask", r=channel == "R", g=channel == "G", b=False)
            link(samples[2], rough, "")
            rough = op("Saturate", op("Multiply", rough, scalar(name + "_Rugosite", 1)))
            outputs = [color, normal, rough]
        weight = op("Divide", paint[name], total)
        for i, output in enumerate(outputs):
            contribution = op("Multiply", output, weight)
            blends[i] = contribution if blends[i] is None else op("Add", blends[i], contribution)
    for n, p in zip(
        [blends[0], op("Normalize", blends[1]), blends[2]],
        [
            u.MaterialProperty.MP_BASE_COLOR,
            u.MaterialProperty.MP_NORMAL,
            u.MaterialProperty.MP_ROUGHNESS,
        ],
    ):
        if not ml.connect_material_property(n, "", p):
            raise RuntimeError("Material output")
    ml.recompile_material(material)
    al.save_loaded_asset(material, only_if_is_dirty=False)
    inst = asset(
        output_content + "/Materials/MI_" + suffix,
        u.MaterialInstanceConstant,
        u.MaterialInstanceConstantFactoryNew,
    )
    ml.set_material_instance_parent(inst, material)
    ml.update_material_instance(inst)
    al.save_loaded_asset(inst)
    return inst
