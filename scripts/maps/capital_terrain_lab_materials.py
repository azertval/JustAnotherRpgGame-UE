#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Native, independent Landscape and mesh materials for terrain laboratories.

Called by build_capital_terrain_labs.py. Reuses supplied library maps read-only;
local copies carry explicit colour space/compression. No normal from albedo.
"""

CONTENT = "/Game/CapitalTerrainLabs"
LAYERS = ("Herbe", "Terre", "Sable", "Roche", "Humide")
SOURCES = {
    "Herbe": (
        "MossyGrass/T_MossyGrass_01_BC",
        "MossyGrass/T_MossyGrass_01_N",
        "MossyGrass/T_MossyGrass_01_Roughness",
        "R",
        200,
    ),
    "Terre": (
        "ForestGround/T_ForestGround_A",
        "ForestGround/T_ForestGround_N",
        "ForestGround/T_ForestGround_R",
        "R",
        250,
    ),
    "Sable": (
        "GravellySand/gravelly_sand_diff_1k",
        "GravellySand/gravelly_sand_nor_dx_1k",
        "GravellySand/gravelly_sand_arm_1k",
        "G",
        200,
    ),
    "Roche": (
        "RockVkmfaek/T_vkmfaek_1K_B",
        "RockVkmfaek/T_vkmfaek_1K_N",
        "RockVkmfaek/T_vkmfaek_1K_ORM",
        "G",
        300,
    ),
    "Humide": (
        "ForestGround/T_ForestGround_A",
        "ForestGround/T_ForestGround_N",
        "ForestGround/T_ForestGround_R",
        "R",
        250,
    ),
}


def build():
    import unreal as u

    ml = u.MaterialEditingLibrary
    al = u.EditorAssetLibrary
    at = u.AssetToolsHelpers.get_asset_tools()

    def asset(path, cls, factory):
        obj = al.load_asset(path) if al.does_asset_exist(path) else None
        if obj is None:
            folder, name = path.rsplit("/", 1)
            obj = at.create_asset(name, folder, cls, factory())
        if obj is None:
            raise RuntimeError("Asset creation: " + path)
        return obj

    def copy_texture(path, role):
        source = "/Game/Surfaces/" + path
        target = CONTENT + "/Textures/" + path.rsplit("/", 1)[1]
        if not al.does_asset_exist(source):
            raise RuntimeError("Missing supplied texture " + source)
        tex = (
            al.load_asset(target)
            if al.does_asset_exist(target)
            else al.duplicate_asset(source, target)
        )
        if tex is None:
            raise RuntimeError("Could not copy " + source)
        tex.set_editor_property("srgb", role == "BC")
        tex.set_editor_property(
            "compression_settings",
            u.TextureCompressionSettings.TC_NORMALMAP
            if role == "N"
            else u.TextureCompressionSettings.TC_BC7,
        )
        al.set_metadata_tag(tex, "CapitalTerrainLabSource", source)
        al.save_loaded_asset(tex)
        return tex

    textures = {}
    for name, source in SOURCES.items():
        textures[name] = [
            copy_texture(path, role) for path, role in zip(source[:3], ("BC", "N", "R"))
        ]

    class Graph:
        def __init__(self, path):
            self.mat = asset(path, u.Material, u.MaterialFactoryNew)
            ml.delete_all_material_expressions(self.mat)
            self.mat.set_editor_property("used_with_nanite", True)
            self.mat.set_editor_property("used_with_instanced_static_meshes", True)
            self.count = 0

        def node(self, kind, **props):
            self.count += 1
            n = ml.create_material_expression(
                self.mat,
                getattr(u, "MaterialExpression" + kind),
                -1800 + (self.count % 12) * 160,
                (self.count // 12) * 200,
            )
            for key, val in props.items():
                n.set_editor_property(key, val)
            return n

        def connect(self, a, b, pin, output=""):
            if not ml.connect_material_expressions(a, output, b, pin):
                raise RuntimeError(
                    f"Connection {a.get_class().get_name()} -> {b.get_class().get_name()}:{pin}"
                )

        def op(self, kind, a, b=None, **props):
            n = self.node(kind, **props)
            self.connect(
                a,
                n,
                "A" if b is not None or kind in ("Multiply", "Divide", "Add", "Subtract") else "",
            )
            if b is not None:
                self.connect(b, n, "B")
            return n

        def scalar(self, name, value):
            return self.node("ScalarParameter", parameter_name=name, default_value=value)

        def output(self, n, prop, out=""):
            if not ml.connect_material_property(n, out, prop):
                raise RuntimeError("Material output " + str(prop))

        def save(self):
            ml.recompile_material(self.mat)
            al.save_loaded_asset(self.mat, only_if_is_dirty=False)

        def sample(self, tex, uv, role, name):
            n = self.node(
                "TextureSampleParameter2D",
                parameter_name=name,
                texture=tex,
                sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
                if role == "N"
                else u.MaterialSamplerType.SAMPLERTYPE_COLOR
                if role == "BC"
                else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
                sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS,
            )
            self.connect(uv, n, "UVs")
            return n

        def rgb(self, n, output="RGB"):
            m = self.node("ComponentMask", r=True, g=True, b=True)
            self.connect(n, m, "", output)
            return m

        def surface(self, name, world=True):
            source = SOURCES[name]
            tile = self.scalar(name + "_TailleCm", source[4])
            if world:
                pos = self.node("WorldPosition")
                xy = self.node("ComponentMask", r=True, g=True, b=False)
                self.connect(pos, xy, "")
                uv = self.op("Divide", xy, tile)
            else:
                coord = self.node("TextureCoordinate")
                uv = self.op("Divide", self.op("Multiply", coord, const_b=200), tile)
            bc = self.sample(textures[name][0], uv, "BC", name + "_Couleur")
            norm = self.sample(textures[name][1], uv, "N", name + "_Normale")
            rough = self.sample(textures[name][2], uv, "R", name + "_Rugosite")
            tint = self.node(
                "VectorParameter",
                parameter_name=name + "_Teinte",
                default_value=u.LinearColor(
                    *([0.68, 0.72, 0.76, 1] if name == "Humide" else [1, 1, 1, 1])
                ),
            )
            color = self.op("Multiply", self.rgb(bc), self.rgb(tint))
            rm = self.node("ComponentMask", r=source[3] == "R", g=source[3] == "G", b=False)
            self.connect(rough, rm, "", "RGB")
            rm = self.op(
                "Saturate",
                self.op(
                    "Multiply",
                    rm,
                    self.scalar(name + "_RugositeFacteur", 0.42 if name == "Humide" else 1),
                ),
            )
            # Scale tangent XY only, keep a positive Z and normalize the result.
            ns = self.node(
                "VectorParameter",
                parameter_name=name + "_Relief",
                default_value=u.LinearColor(0.7, 0.7, 1, 1),
            )
            normal = self.op("Normalize", self.op("Multiply", self.rgb(norm), self.rgb(ns)))
            return color, normal, rm

    g = Graph(CONTENT + "/Materials/M_Landscape_Capitale")
    blends = []
    for _ in range(3):
        b = g.node("LandscapeLayerBlend")
        entries = []
        for name in LAYERS:
            entry = u.LayerBlendInput()
            entry.set_editor_property("layer_name", name)
            entry.set_editor_property("blend_type", u.LandscapeLayerBlendType.LB_WEIGHT_BLEND)
            entry.set_editor_property("preview_weight", 1.0 if name == "Herbe" else 0.0)
            entries.append(entry)
        b.set_editor_property("layers", entries)
        blends.append(b)
    for name in LAYERS:
        for node, blend in zip(g.surface(name), blends):
            g.connect(node, blend, "Layer " + name)
    # The painted weights are shared by colour, roughness and normals.
    g.output(blends[0], u.MaterialProperty.MP_BASE_COLOR)
    g.output(g.op("Normalize", blends[1]), u.MaterialProperty.MP_NORMAL)
    g.output(blends[2], u.MaterialProperty.MP_ROUGHNESS)
    g.save()
    landscape = g.mat

    result = {}
    for family, layer in [
        ("paving", "Roche"),
        ("stone", "Roche"),
        ("rock", "Roche"),
        ("soil", "Terre"),
        ("sand", "Sable"),
    ]:
        g = Graph(CONTENT + "/Materials/M_Mesh_" + family)
        bc, normal, rough = g.surface(layer, False)
        vertex = g.node("VertexColor")
        tint = g.node("LinearInterpolate", const_a=1.0)
        g.connect(g.rgb(vertex, ""), tint, "B")
        g.connect(g.scalar("VariationPierres", 0.45), tint, "Alpha")
        g.output(g.op("Multiply", bc, tint), u.MaterialProperty.MP_BASE_COLOR)
        g.output(normal, u.MaterialProperty.MP_NORMAL)
        g.output(rough, u.MaterialProperty.MP_ROUGHNESS)
        g.save()
        instance = asset(
            CONTENT + "/Materials/MI_" + family,
            u.MaterialInstanceConstant,
            u.MaterialInstanceConstantFactoryNew,
        )
        ml.set_material_instance_parent(instance, g.mat)
        if family in ("paving", "stone"):
            ml.set_material_instance_vector_parameter_value(
                instance, "Roche_Teinte", u.LinearColor(1.14, 1.08, 0.94, 1)
            )
            ml.set_material_instance_scalar_parameter_value(instance, "Roche_TailleCm", 150)
        ml.update_material_instance(instance)
        al.save_loaded_asset(instance)
        result[family] = instance
    inst = asset(
        CONTENT + "/Materials/MI_Landscape_Capitale",
        u.MaterialInstanceConstant,
        u.MaterialInstanceConstantFactoryNew,
    )
    ml.set_material_instance_parent(inst, landscape)
    ml.update_material_instance(inst)
    al.save_loaded_asset(inst)
    result["landscape"] = inst
    # Dedicated copy of the project's existing Single Layer Water shader.
    water_path = CONTENT + "/Materials/M_Eau_Demonstration"
    water = (
        al.load_asset(water_path)
        if al.does_asset_exist(water_path)
        else al.duplicate_asset("/Game/Capitale/Ressources/M_Eau", water_path)
    )
    if water is None:
        raise RuntimeError("Existing capital water material unavailable")
    al.save_loaded_asset(water)
    result["water"] = water
    return result
