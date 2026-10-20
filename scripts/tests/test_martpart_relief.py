# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Physical terrain/threshold regressions independent of Blender and Unreal."""

import importlib.util
import math
from pathlib import Path

import pytest

import martpart_district_layout as layout


@pytest.fixture
def geometry():
    source = Path(__file__).resolve().parents[1] / "assetsGeneration/build_martpart_district.py"
    spec = importlib.util.spec_from_file_location("martpart_relief_geometry_test", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for values in [
        module.g.VERTS,
        module.g.FACES,
        module.g.FACE_MATERIALS,
        module.g.FACE_SMOOTH,
        module.g.FACE_COLORS,
        module.g.FACE_SEEDS,
        module.g.FACE_BEVELS,
    ]:
        values.clear()
    return module


def test_cart_routes_have_continuous_slope_and_do_not_cross_the_river():
    for road in layout.ROADS:
        points = layout.sampled_route(road["points"], step=0.5)
        for point in points:
            assert layout.inside_land(*point[:2])
        for a, b in zip(points, points[1:]):
            horizontal = math.dist(a[:2], b[:2])
            assert abs(a[2] - b[2]) / horizontal < 0.20, (road["id"], a, b)
    assert 5 <= layout.ground_height(-115, 135) - layout.ground_height(*layout.GATE) <= 10


def test_hall_arena_and_every_shop_have_level_foundations_and_thresholds():
    for platform in layout.PLATFORMS:
        x, y = platform["position"]
        z = layout.ground_height(x, y)
        if "radius" in platform:
            samples = [
                (
                    x + platform["radius"] * 0.85 * math.cos(i * math.pi / 4),
                    y + platform["radius"] * 0.85 * math.sin(i * math.pi / 4),
                )
                for i in range(8)
            ]
        else:
            angle = math.radians(platform.get("yaw", 0))
            samples = [
                (
                    x + dx * math.cos(angle) - dy * math.sin(angle),
                    y + dx * math.sin(angle) + dy * math.cos(angle),
                )
                for dx in [-4.9, 0, 4.9]
                for dy in [-4.9, 0, 4.9]
            ]
        for px, py in samples:
            assert layout.ground_height(px, py) == pytest.approx(z, abs=1e-5), platform["id"]


def test_collision_wall_has_real_open_doorway_at_all_building_heights(geometry):
    geometry.shop_physical(4)
    # Each authored solid contributes eight vertices. Test occupied volumes,
    # rather than trusting metadata or the source's declared doorway width.
    bounds = []
    for i in range(0, len(geometry.g.VERTS), 8):
        vertices = [(x, -y, z) for x, y, z in geometry.g.VERTS[i : i + 8]]
        bounds.append(
            [(min(v[k] for v in vertices), max(v[k] for v in vertices)) for k in range(3)]
        )

    def occupied(point):
        return any(
            all(lo - 1e-6 <= value <= hi + 1e-6 for value, (lo, hi) in zip(point, box))
            for box in bounds
        )

    assert not occupied((0, 4.86, 1.5))
    assert not occupied((1.30, 4.86, 2.5))
    assert occupied((3.25, 4.86, 1.5))
    assert occupied((0, 4.86, 3.6))
    assert max(v[2] for v in geometry.g.VERTS) == 14


def test_heightfield_covers_gameplay_and_includes_exact_ground_samples():
    field = layout.heightfield()
    assert field["spacing"] == [1.5, 1.5]
    assert len(field["heights"]) == field["width"] * field["height"]
    for col, row in [(0, 0), (80, 64), (174, 100), (212, 196)]:
        x, y = [field["origin"][i] + [col, row][i] * field["spacing"][i] for i in range(2)]
        assert field["heights"][row * field["width"] + col] == layout.ground_height(x, y)
    # The navigable bridge shares its gate's height even over water.
    assert layout.ground_height(140, -60) == layout.ground_height(*layout.GATE)


def test_public_gallery_stair_reaches_the_same_deck_without_a_lip(geometry):
    geometry.gallery(physical=True)
    vertices = [(x, -y, z) for x, y, z in geometry.g.VERTS]
    # Four-metre-wide final stair and 3.6m deck meet at local Y=0.
    boundary = [v for v in vertices if abs(v[1]) < 1e-7 and abs(v[0]) <= 2.01]
    assert max(v[2] for v in boundary) == pytest.approx(3.6)
    assert max(v[2] for v in vertices if abs(v[0]) <= 6 and 0 <= v[1] <= 6) >= 3.6


def test_joined_and_oblique_fronts_leave_every_door_approach_clear():
    # Check the placed, scaled foundations rather than the unscaled ten-metre
    # template; a wider end house must not seal the next merchant's doorway.
    for house in layout.PLOTS:
        angle = math.radians(house["yaw"])
        x, y = house["position"]
        forward = house["depth"] / 2 + 0.8
        door = (x - forward * math.sin(angle), y + forward * math.cos(angle))
        for neighbour in layout.PLOTS:
            if house is neighbour:
                continue
            other = math.radians(neighbour["yaw"])
            dx, dy = door[0] - neighbour["position"][0], door[1] - neighbour["position"][1]
            u, v = (
                dx * math.cos(other) + dy * math.sin(other),
                -dx * math.sin(other) + dy * math.cos(other),
            )
            assert not (
                abs(u) < neighbour["width"] / 2 + 0.35 and abs(v) < neighbour["depth"] / 2 + 0.35
            ), (house["id"], neighbour["id"])


def test_visit_walk_reaches_gallery_without_entering_filled_stairs_or_tables(geometry):
    geometry.gallery(physical=True)
    boxes = []
    for index in range(0, len(geometry.g.VERTS), 8):
        vertices = [(x, -y, z) for x, y, z in geometry.g.VERTS[index : index + 8]]
        boxes.append([(min(p[k] for p in vertices), max(p[k] for p in vertices)) for k in range(3)])
    base = layout.ground_height(-29, 100)
    for x, y, z in geometry.build_visit_route():
        # Check the actual solid architecture at three body heights. Matching
        # the terrain below a filled step is not evidence of a clear approach.
        for dz in [0.15, 0.9, 1.5]:
            point = (x + 29, y - 100, z - base + dz)
            assert not any(
                all(lo + 0.0001 < value < hi - 0.0001 for value, (lo, hi) in zip(point, box))
                for box in boxes
            ), (x, y, z, dz)
