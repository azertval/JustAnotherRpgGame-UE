# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Offline contracts for original looping audio and authored navigation routes."""
import array
import copy
import math
from types import SimpleNamespace
import wave

import pytest

import district_atmosphere as atmosphere


@pytest.mark.parametrize("kind", atmosphere.SOUNDS)
def test_original_pcm_is_deterministic_bounded_and_has_silent_loop_edges(kind):
    pcm = atmosphere.pcm_samples(kind, seconds=1.5, rate=2000)
    assert pcm == atmosphere.pcm_samples(kind, seconds=1.5, rate=2000)
    samples = array.array("h", pcm)
    assert len(samples) == 3000
    assert samples[0] == samples[-1] == 0
    assert max(abs(sample) for sample in samples) <= 31129
    assert any(abs(sample) > 100 for sample in samples)


def test_generated_waves_are_reusable_mono_pcm_sources(tmp_path):
    first = atmosphere.generate_audio(tmp_path, seconds=1.5)
    second = atmosphere.generate_audio(tmp_path, seconds=1.5)
    assert first == second
    for source in first:
        with wave.open(source["file"], "rb") as sound:
            assert sound.getnchannels() == 1
            assert sound.getsampwidth() == 2
            assert sound.getframerate() == atmosphere.RATE
            assert sound.getnframes() == round(atmosphere.RATE * 1.5)


@pytest.mark.parametrize("route", [[], [[0, 0, 0]], [[0, 0, 0], [float("nan"), 1, 0]],
                                  [[0, 0, 0], [1, 1]], [[0, 0, 0], [0, 0, 0]]])
def test_rejects_routes_that_cannot_describe_a_real_patrol(route):
    with pytest.raises(ValueError):
        atmosphere.validated_routes({"crowdRoutes": [route]})


def test_routes_preserve_authored_xyz_ground_and_do_not_mutate_metadata():
    metadata = {"crowdRoutes": [[[1, 2, -6], [10, 2, 0], [10, 8, 0]]]}
    result = atmosphere.validated_routes(metadata)
    result[0][0][2] = 99
    assert metadata["crowdRoutes"][0][0] == [1, 2, -6]


@pytest.fixture
def material_interfaces(monkeypatch):
    class Material:
        def __init__(self, path):
            self.path = path

        def get_path_name(self):
            return self.path

    class Instance:
        def __init__(self, path, parent, **parameters):
            self.path = path
            self.properties = {name: [] for name in atmosphere._INSTANCE_PARAMETERS}
            self.properties.update(parameters, parent=parent)

        def get_path_name(self):
            return self.path

        def get_editor_property(self, name):
            return self.properties[name]

        def set_editor_property(self, name, value):
            self.properties[name] = value if name == "parent" else copy.deepcopy(value)

        def effective(self, name):
            inherited = self.properties["parent"]
            values = dict(inherited.effective(name)) if isinstance(inherited, Instance) else {}
            values.update(self.properties[name])
            return values

    assets = {}
    saved = []

    def duplicate(source, destination):
        source = assets[source]
        result = Instance(destination, source.properties["parent"])
        for key, value in source.properties.items():
            result.set_editor_property(key, value)
        assets[destination] = result
        return result

    editing = SimpleNamespace(
        set_material_instance_parent=lambda instance, parent: instance.set_editor_property("parent", parent),
        update_material_instance=lambda instance: None)
    library = SimpleNamespace(load_asset=assets.get, does_asset_exist=lambda path: path in assets, duplicate_asset=duplicate,
                              save_loaded_asset=lambda asset: saved.append(asset.path),
                              set_metadata_tag=lambda *args: None)
    monkeypatch.setattr(atmosphere, "unreal", SimpleNamespace(
        Material=Material, MaterialInstanceConstant=Instance,
        MaterialEditingLibrary=editing, EditorAssetLibrary=library))
    wind_master = Material("/Game/Wind/Master")
    monkeypatch.setattr(atmosphere, "_wind_parent", lambda *args: wind_master)
    master = Material("/Game/Approved/Master")
    painted = Instance("/Game/Approved/Painted", master,
                       scalar_parameter_values=[("Roughness", 0.8)],
                       texture_parameter_values=[("BaseColor", "/Game/Textures/Linen")])
    tinted = Instance("/Game/Martpart/Blue", painted,
                      vector_parameter_values=[("QuietColour", (0.03, 0.09, 0.2))])
    leaf = Instance("/Game/Martpart/Awning", tinted,
                    scalar_parameter_values=[("ColourDetail", 0.22)])
    for asset in (painted, tinted, leaf):
        assets[asset.path] = asset
    return SimpleNamespace(master=master, painted=painted, tinted=tinted, leaf=leaf,
                           wind_master=wind_master, assets=assets, saved=saved)


def test_wind_preserves_district_tint_and_approved_texture_inherited_through_instances(material_interfaces):
    source = material_interfaces
    result = atmosphere._wind_interface(source.leaf, "cloth", [])
    assert result.effective("scalar_parameter_values") == {"Roughness": 0.8, "ColourDetail": 0.22}
    assert result.effective("vector_parameter_values") == {"QuietColour": (0.03, 0.09, 0.2)}
    assert result.effective("texture_parameter_values") == {"BaseColor": "/Game/Textures/Linen"}
    assert result.get_editor_property("parent") is not source.tinted
    assert result.get_editor_property("parent").get_editor_property("parent").get_editor_property("parent") is source.wind_master
    assert source.leaf.get_editor_property("parent") is source.tinted
    assert source.painted.get_editor_property("parent") is source.master


def test_wind_regeneration_refreshes_saved_source_overrides_and_reuses_chain(material_interfaces):
    source = material_interfaces
    first = atmosphere._wind_interface(source.leaf, "cloth", [])
    source.tinted.set_editor_property("vector_parameter_values", [("QuietColour", (0.1, 0.2, 0.3))])
    second = atmosphere._wind_interface(source.leaf, "cloth", [])
    assert second is first
    assert second.effective("vector_parameter_values") == {"QuietColour": (0.1, 0.2, 0.3)}
    assert len(source.assets) == 6


def test_wind_rejects_cyclic_instance_hierarchy(material_interfaces):
    source = material_interfaces
    source.painted.set_editor_property("parent", source.leaf)
    with pytest.raises(ValueError, match="parent cycle"):
        atmosphere._wind_interface(source.leaf, "cloth", [])


@pytest.fixture
def water_graph_engine(monkeypatch):
    """Evaluate the generated shader graph offline, with documented UE pin contracts."""
    class Node:
        def __init__(self, kind):
            self.kind, self.properties, self.inputs = kind, {}, {}

        def set_editor_property(self, name, value):
            self.properties[name] = value

    class Material:
        def __init__(self):
            self.properties, self.outputs, self.nodes, self.metadata = {}, {}, [], {}

        def set_editor_property(self, name, value):
            self.properties[name] = value

    result = Material()

    def expression(material, kind, *args):
        value = Node(kind.__name__.replace("MaterialExpression", ""))
        material.nodes.append(value)
        return value

    def connect(source, pin, target, input_pin):
        # UE shortens the sole input named 'Input' to the empty string.
        if input_pin == "Input":
            return False
        target.inputs[input_pin] = source
        return True

    editing = SimpleNamespace(
        create_material_expression=expression, connect_material_expressions=connect,
        connect_material_property=lambda source, pin, property_name: result.outputs.__setitem__(property_name, source) or True,
        delete_all_material_expressions=lambda material: None, recompile_material=lambda material: None,
        get_material_expression_input_names=lambda node: ["Scattering Coefficients", "Absorption Coefficients", "Phase G", "Color Scale Behind Water"],
    )
    engine = SimpleNamespace(
        MaterialEditingLibrary=editing, Material=Material, MaterialFactoryNew=lambda: None,
        MaterialShadingModel=SimpleNamespace(MSM_SINGLELAYERWATER="water", MSM_DEFAULT_LIT="default"),
        BlendMode=SimpleNamespace(BLEND_OPAQUE="opaque"),
        LinearColor=lambda *values: values[:3],
        AssetToolsHelpers=SimpleNamespace(get_asset_tools=lambda: SimpleNamespace(create_asset=lambda *args: result)),
        EditorAssetLibrary=SimpleNamespace(load_asset=lambda *args: None, does_asset_exist=lambda *args: False,
            save_loaded_asset=lambda *args: None,
            set_metadata_tag=lambda material, key, value: material.metadata.__setitem__(key, value)),
    )
    for kind in ("Constant", "Constant3Vector", "Time", "ObjectPositionWS", "WorldPosition", "ComponentMask",
                 "Multiply", "Add", "Sine", "AppendVector", "Normalize", "SingleLayerWaterMaterialOutput"):
        setattr(engine, "MaterialExpression" + kind, type("MaterialExpression" + kind, (), {}))
    monkeypatch.setattr(atmosphere, "unreal", engine)

    def evaluate(node, world=(0, 0, 0), time=0):
        kind = node.kind
        if kind == "Constant":
            return node.properties["r"]
        if kind == "Constant3Vector":
            return node.properties["constant"]
        if kind == "Time":
            return time
        if kind == "WorldPosition":
            return world
        values = {key: evaluate(value, world, time) for key, value in node.inputs.items()}
        if kind == "ComponentMask":
            vector = values[""]
            channels = [vector[i] for i, key in enumerate(("r", "g", "b")) if node.properties.get(key, False)]
            return channels[0] if len(channels) == 1 else tuple(channels)
        if kind in ("Add", "Multiply"):
            left, right = values["A"], values["B"]
            operation = (lambda a, b: a + b) if kind == "Add" else (lambda a, b: a * b)
            if isinstance(left, tuple) or isinstance(right, tuple):
                left = left if isinstance(left, tuple) else (left,) * len(right)
                right = right if isinstance(right, tuple) else (right,) * len(left)
                return tuple(operation(a, b) for a, b in zip(left, right))
            return operation(left, right)
        if kind == "Sine":
            return math.sin(2 * math.pi * values[""] / node.properties["period"])
        if kind == "AppendVector":
            return tuple(v for key in ("A", "B") for v in (
                values[key] if isinstance(values[key], tuple) else (values[key],)))
        if kind == "Normalize":
            vector = values[""]
            length = math.sqrt(sum(v * v for v in vector))
            return tuple(v / length for v in vector)
        raise AssertionError(f"Unexpected water dependency {kind}")

    engine.MaterialProperty = SimpleNamespace(**{
        name: name for name in ("MP_NORMAL", "MP_ROUGHNESS", "MP_METALLIC", "MP_SPECULAR", "MP_BASE_COLOR",
                                "MP_OPACITY", "MP_REFRACTION", "MP_WORLD_POSITION_OFFSET")})
    return SimpleNamespace(engine=engine, material=result, evaluate=evaluate)


def test_native_water_has_dielectric_reflection_and_connected_volume_inputs(water_graph_engine):
    fixture = water_graph_engine
    material = atmosphere._material("TestWater", "water")
    assert material.properties["shading_model"] == "water"
    assert material.properties["blend_mode"] == "opaque"
    assert material.properties["tangent_space_normal"] is False
    assert material.metadata["DistrictWaterBackend"] == "SingleLayerWater"
    water = next(node for node in material.nodes if node.kind == "SingleLayerWaterMaterialOutput")
    assert len(water.inputs) == 4
    assert fixture.evaluate(material.outputs["MP_METALLIC"]) == 0.0
    assert fixture.evaluate(material.outputs["MP_SPECULAR"]) == 0.25
    assert fixture.evaluate(material.outputs["MP_REFRACTION"]) == 1.333


def test_water_normal_is_spatially_crossed_and_animation_stays_below_one_centimetre(water_graph_engine):
    fixture = water_graph_engine
    material = atmosphere._material("TestWater", "water")
    normal = material.outputs["MP_NORMAL"]
    origin = fixture.evaluate(normal, (0, 0, 0), 0)
    east = fixture.evaluate(normal, (53, 0, 0), 0)
    south = fixture.evaluate(normal, (0, 53, 0), 0)
    later = fixture.evaluate(normal, (0, 0, 0), 7)
    assert origin != east and origin != south and origin != later
    # The normal graph can evaluate from world coordinates alone, without UV,
    # plane size, object origin or object-scale dependencies.
    for point in ((0, 0, 0), (315, -423, 0), (40, 14000, 0)):
        for time in (0, 3.5, 14, 51):
            z = fixture.evaluate(material.outputs["MP_WORLD_POSITION_OFFSET"], point, time)[2]
            assert abs(z) < 1.0
            assert fixture.evaluate(normal, point, time)[2] > 0.995


def test_water_backend_unavailable_uses_explicit_lit_fallback(water_graph_engine):
    fixture = water_graph_engine
    del fixture.engine.MaterialExpressionSingleLayerWaterMaterialOutput
    material = atmosphere._material("TestWater", "water")
    assert material.properties["shading_model"] == "default"
    assert "unavailable" in material.metadata["DistrictWaterBackend"]
    assert fixture.evaluate(material.outputs["MP_METALLIC"]) == 0


def test_missing_generated_asset_is_not_loaded(monkeypatch):
    calls = []
    monkeypatch.setattr(atmosphere, "unreal", SimpleNamespace(EditorAssetLibrary=SimpleNamespace(
        does_asset_exist=lambda path: False,
        load_asset=lambda path: calls.append(path))))
    assert atmosphere._asset_if_exists("/Game/Districts/NewMaterial") is None
    assert calls == []


def test_existing_generated_asset_is_loaded(monkeypatch):
    asset = object()
    calls = []

    def load(path):
        calls.append(path)
        return asset

    monkeypatch.setattr(atmosphere, "unreal", SimpleNamespace(EditorAssetLibrary=SimpleNamespace(
        does_asset_exist=lambda path: True, load_asset=load)))
    assert atmosphere._asset_if_exists("/Game/Districts/ExistingMaterial") is asset
    assert calls == ["/Game/Districts/ExistingMaterial"]


@pytest.mark.parametrize("item", [{"interior": True}, {"always": True}, {"fire": True}])
def test_interior_and_permanent_fixtures_do_not_switch_off_with_daylight(item):
    tags, always = atmosphere.light_tags(item)
    assert always is True
    assert "JadgLamp" not in tags


def test_exterior_lamp_keeps_daylight_control():
    tags, always = atmosphere.light_tags({"candelas": 450})
    assert always is False
    assert "JadgLamp" in tags


@pytest.mark.parametrize("member", ["MSM_SINGLE_LAYER_WATER", "MSM_SINGLELAYERWATER", "MSM_SingleLayerWater"])
def test_water_resolves_generated_python_enum_spellings(monkeypatch, member):
    model, water_class = object(), object()
    monkeypatch.setattr(atmosphere, "unreal", SimpleNamespace(
        MaterialShadingModel=SimpleNamespace(**{member: model}),
        MaterialExpressionSingleLayerWaterMaterialOutput=water_class))
    resolved_class, resolved_model, diagnostic = atmosphere.single_layer_water_api()
    assert resolved_class is water_class
    assert resolved_model is model
    assert diagnostic["classAvailable"] is True
    assert diagnostic["enumMember"] == member


def test_water_diagnostic_distinguishes_missing_enum_from_missing_class(monkeypatch):
    monkeypatch.setattr(atmosphere, "unreal", SimpleNamespace(
        MaterialShadingModel=SimpleNamespace(MSM_DEFAULT_LIT=0),
        MaterialExpressionSingleLayerWaterMaterialOutput=object()))
    _, model, diagnostic = atmosphere.single_layer_water_api()
    assert model is None
    assert diagnostic["classAvailable"] is True
    assert diagnostic["enumMember"] is None
