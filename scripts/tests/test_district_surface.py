# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Terrain heights must not turn a high street into an unrelated building floor."""
from copy import deepcopy

import pytest

import district_surface as surface
import build_capital_districts as districts
import jadg_map


@pytest.fixture
def district():
    return {
        "storeys": [{"name": "street", "z": 0}, {"name": "pub-upper", "z": 4}],
        "groundHeightfield": {
            "origin": [0, 0], "spacing": [10, 20], "width": 3, "height": 2,
            "heights": [0, 10, 20, 4, 14, 24],
        },
        "storeyRegions": [{"storey": 1, "minimum": [0, 0, 4], "maximum": [3, 3, 7]}],
    }


def test_height_interpolation_and_edges_preserve_metres(district):
    assert surface.ground_height(district, 5, 10) == pytest.approx(7)
    assert surface.ground_height(district, 20, 20) == 24
    assert surface.terrain_height(district, 20.01, 20) is None
    assert surface.ground_height(district, -1, 0) == 0


def test_high_road_and_local_upper_floor_are_distinct(district):
    assert surface.storey_at(district, [10, 10, 12]) == 0
    assert surface.storey_at(district, [1, 1, 4]) == 1
    assert surface.storey_at(district, [1, 1, .5]) == 0
    assert surface.ground_height(district, 1, 1, 1) == 4
    assert surface.ground_height(district, 1, 1) == pytest.approx(1.2)


@pytest.mark.parametrize("key,value", [("heights", [0]), ("spacing", [0, 1]),
                                     ("heights", [float("nan")] * 6), ("width", 1)])
def test_inconsistent_surface_is_refused_before_engine_import(district, key, value):
    district["groundHeightfield"][key] = value
    assert surface.validate_surface(district)


def test_storey_region_must_name_real_floor(district):
    district["storeyRegions"][0]["storey"] = 2
    assert surface.validate_surface(district)


def test_reconstruction_keeps_surface_and_ground_entity_storey(district):
    original = {"format": jadg_map.FORMAT, "version": 5, "name": "test", "place": "test",
                "width": 20, "height": 20, "nextEntityId": 2,
                "tiles": [{"x": 1, "y": 1, "type": "entry"}],
                "entities": [{"id": "e1", "type": "spawnPoint", "name": "arrival", "x": 1, "y": 1}],
                "party": {"appearances": []}}
    metadata = {**deepcopy(district), "area": [0, 0, 20, 20], "start": [5, 10, 7], "shots": [],
                "entityPositions": {"e1": [10, 10, 12]}, "levels": district["storeys"]}
    manifest = {"meshes": [], "objects": [], "metadata": metadata}
    result, _ = districts.make_document("arenarea", manifest, original)
    assert result["entities"][0]["storey"] == 0
    assert result["groundHeightfield"] == district["groundHeightfield"]
    assert result["storeyRegions"] == district["storeyRegions"]
    assert jadg_map.validate(result) == []
    again, _ = districts.make_document("arenarea", manifest, result)
    assert result == again
    assert districts.gameplay_contract(result) == districts.gameplay_contract(original)


def test_legacy_flat_cards_keep_storey_heights():
    legacy = {"storeys": [{"name": "street", "z": 0}, {"name": "basement", "z": -6}]}
    assert surface.ground_height(legacy, 100, 200, 1) == -6
    assert surface.storey_at(legacy, [100, 200, -6]) == 1
