#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Martpart's approved atlas neighbourhoods and continuous urban relief.

Coordinates deliberately follow the district drawing: X right, Y down, Z up.
They are a scene convention, not the compass rose or a metric tracing of pixels.
The river is outside the upper/right boundary; streets continue into the city
at the left and bottom. Public halls keep level foundations on the hillside.
"""

import math
from functools import lru_cache

AREA = [-128.0, -104.0, 164.0, 148.0]
LAND = [(-128, -92), (-8, -104), (126, -64), (128, 148), (-128, 148)]
MARKET = [0.0, -43.0]
ILLU = [44.0, 59.0]
SHAFT = [-60.0, 37.0]
GATE = [120.0, -60.0]
BRIDGE = [140.0, -60.0]
# Recast found the narrow shared shop lane isolated by delivery stock. Its
# eastern mouth is a public passage; keep the goods in the adjacent delivery
# court and the planter beside that court, rather than across the carriageway.
ACCESS_DETAIL_POSITIONS = {
    "shop-reserve-9": [32.0, -63.0],
    "shop-reserve-18": [35.0, -63.0],
    "door-planter-8": [29.0, -58.0],
}
# The named visit is in the public passage beside the same commercial block,
# clear of the shop's side furniture and its 35cm navigation erosion margin.
UBEL_PARADISE = [-73.0, 96.0]
ROADS = [
    {
        "id": "stravian-avenue",
        "width": 9.0,
        "points": [(-124, -64), (-84, -38), (-40, -16), (0, -16), (59, -30), (120, -60)],
    },
    {
        "id": "reservoir-street",
        "width": 6.0,
        "points": [
            (-120, 12),
            (-97, 23),
            (-88, 37),
            (-77.5, 37),
            (-76.17, 43.7),
            (-72.37, 49.37),
            (-66.7, 53.17),
            (-60, 54.5),
            (-53.3, 53.17),
            (-47.63, 49.37),
            (-43.83, 43.7),
            (-42.5, 37),
            (-28, 37),
            (17, 28),
            (44, 30),
            (92, 27),
            (119, 12),
        ],
    },
    {
        "id": "saint-malrok",
        "width": 7.0,
        "points": [(-127, 112), (-94, 112), (-49, 119), (-5, 128), (51, 132), (123, 133)],
    },
    {
        "id": "tamera-path",
        "width": 6.0,
        "points": [(-104, -23), (-98, 6), (-96, 63), (-92, 112), (-92, 148)],
    },
    {
        "id": "witch-street",
        "width": 6.0,
        "points": [(85, -38), (90, -5), (91, 39), (89, 92), (89, 148)],
    },
    {"id": "monkling-alley", "width": 4.0, "points": [(-38, -92), (-37, -63), (-40, -16)]},
    {"id": "pauper-street", "width": 4.5, "points": [(-116, 50), (-116, 86), (-106, 116)]},
    {"id": "duckbunny-alley", "width": 4.5, "points": [(-23, 38), (-12, 70), (2, 101), (7, 126)]},
]


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


def base_height(x, y):
    # Eight metres of broad, cart-friendly relief down to the river. A slight
    # saddle breaks the mathematical plane without adding an invented hill.
    t = 0.57 * (128 - x) / 256 + 0.43 * (y + 100) / 248
    return 8.7 * max(0.0, min(1.0, t)) + 0.24 * math.sin(x / 42) * math.sin(y / 48)


def distance_to_segment(x, y, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - a[0] - dx * t, y - a[1] - dy * t)


def inside_land(x, y, margin=0):
    # The upper shore is oblique rather than an enclosing water rectangle.
    upper = -92 - (x + 128) * 0.1 if x < -8 else -104 + (x + 8) * 40 / 134
    return -128 + margin <= x <= 128 - margin and upper + margin <= y <= 148 - margin


def plot_candidates():
    plots = []
    for row in range(17):
        y = -85 + row * 13.8
        edge = -123 + (row % 3 - 1) * 1.4
        for col in range(20):
            width = [10.8, 13.2, 11.6, 12.4][(col + row) % 4]
            depth = [9.8, 11.2, 10.4][(col // 4 + row) % 3]
            x = edge + width / 2
            edge += width + 0.18 + (3.4 if col % 4 == 3 else 0)
            plot_y = round(y + ((col // 4 + row) % 3 - 1) * 0.65, 3)
            if not inside_land(x, plot_y, max(width, depth) / 2 + 1):
                continue
            if (
                abs(x - MARKET[0]) < 19 + width / 2 + 3
                and abs(plot_y - MARKET[1]) < 16 + depth / 2 + 3
            ):
                continue
            if math.hypot(x - ILLU[0], plot_y - ILLU[1]) < 27 + max(width, depth) / 2:
                continue
            if math.hypot(x - SHAFT[0], plot_y - SHAFT[1]) < 34 + max(width, depth) / 2:
                continue
            if abs(x + 29) < 18 + width / 2 and abs(plot_y - 100) < 18 + depth / 2:
                continue
            if any(
                distance_to_segment(x, plot_y, a, b)
                < road["width"] / 2 + max(width, depth) / 2 + 1.6
                for road in ROADS
                for a, b in zip(road["points"], road["points"][1:])
            ):
                continue
            plots.append(
                {
                    "id": f"merchant-{row}-{col}",
                    "position": [round(x, 3), plot_y],
                    "width": width,
                    "depth": depth,
                    "group": f"block-{row}-{col // 4}",
                    "style": (row + col * 2) % 3,
                    "floors": 4 if (row * 17 + col) % 13 == 0 else 2 + (row + col) % 2,
                    "yaw": 180 if row % 2 else 0,
                    "trade": (row * 3 + col) % 6,
                }
            )
    # Shared foundations make joined fronts genuinely continuous while the
    # neighbouring service lane changes level between commercial blocks.
    groups = {}
    for plot in plots:
        groups.setdefault(plot["group"], []).append(plot)
    for group in groups.values():
        gx = sum(p["position"][0] for p in group) / len(group)
        gy = sum(p["position"][1] for p in group) / len(group)
        for plot in group:
            plot["baseZ"] = base_height(gx, gy)
        # The ends of blocks address the oblique main avenue rather than
        # presenting every corner as another north/south square facade.
        for plot in [group[0], group[-1]]:
            x, y = plot["position"]
            nearest = None
            for a, b in zip(ROADS[0]["points"], ROADS[0]["points"][1:]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                t = max(0, min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy)))
                q = (a[0] + dx * t, a[1] + dy * t)
                distance = math.dist((x, y), q)
                if nearest is None or distance < nearest[0]:
                    nearest = (distance, q)
            if nearest[0] < 17:
                qx, qy = nearest[1]
                plot["yaw"] = math.degrees(math.atan2(x - qx, qy - y))
    # Eight tangential fronts enclose the planted annular Shaft Loop. Cardinal
    # openings preserve its radial streets instead of replacing it with a well.
    for i in range(12):
        if i in (0, 3, 6, 9):
            continue
        angle = i * math.tau / 12
        plots.append(
            {
                "id": f"shaft-front-{i}",
                "position": [SHAFT[0] + 25 * math.cos(angle), SHAFT[1] + 25 * math.sin(angle)],
                "width": 10,
                "depth": 10,
                "style": i % 3,
                "floors": 2 + i % 2,
                "yaw": math.degrees(angle) + 90,
                "trade": i % 6,
                "baseZ": base_height(*SHAFT),
                "group": "shaft-loop",
            }
        )
    # Corner houses follow oblique carriageways. Only genuinely vacant sites
    # receive these deeper ends; the assembly does not sprinkle villas in gaps.
    for n, (x, y, yaw) in enumerate(
        [(-103, -27, 33), (-59, -35, 27), (39, -11, -14), (73, -43, -26), (103, -30, -26)]
    ):
        if any(math.dist((x, y), p["position"]) < 16 for p in plots):
            continue
        plots.append(
            {
                "id": f"corner-trader-{n}",
                "position": [x, y],
                "width": 11.5,
                "depth": 13.5,
                "style": n % 3,
                "floors": 3,
                "yaw": yaw,
                "trade": n % 6,
                "baseZ": base_height(x, y),
                "group": f"corner-{n}",
            }
        )
    return plots


PLOTS = plot_candidates()
PLATFORMS = [
    {"id": "market-foundation", "position": MARKET, "halfSize": [19, 16], "blend": 7, "yaw": 0},
    {"id": "illu-foundation", "position": ILLU, "radius": 20, "blend": 7},
    {"id": "shaft-garden", "position": SHAFT, "radius": 18.5, "blend": 5},
    {
        "id": "gallery-court",
        "position": [-29, 100],
        "halfSize": [13, 13],
        "blend": 6,
        "yaw": 0,
        "raise": 1.2,
    },
    {"id": "gate-threshold", "position": GATE, "halfSize": [10, 7], "blend": 5, "yaw": 0},
] + [
    {
        "id": p["id"],
        "position": p["position"],
        "halfSize": [p["width"] / 2 + 0.22, p["depth"] / 2 + 1.1],
        "blend": 2.8,
        "yaw": p["yaw"],
        "baseZ": p["baseZ"],
    }
    for p in PLOTS
]


def platform_weight(platform, x, y):
    px, py = platform["position"]
    if "radius" in platform:
        distance = math.hypot(x - px, y - py) - platform["radius"]
    else:
        a = math.radians(platform.get("yaw", 0))
        dx, dy = x - px, y - py
        u, v = dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)
        distance = max(abs(u) - platform["halfSize"][0], abs(v) - platform["halfSize"][1])
    return 1 - smooth(distance / platform["blend"])


@lru_cache(maxsize=180000)
def ground_height(x, y):
    """The sole altitude contract for terrain, props, routes and gameplay."""
    z = base_height(x, y)
    # A foundation core is truly flat. Blending a neighbouring pad into that
    # core would tilt its doorway/floor, even when its own weight was one.
    for platform in PLATFORMS:
        if platform_weight(platform, x, y) >= 1:
            px, py = platform["position"]
            return round(platform.get("baseZ", base_height(px, py)) + platform.get("raise", 0), 6)
    neighbours = [(platform_weight(p, x, y), p) for p in PLATFORMS]
    for weight, platform in sorted(
        (pair for pair in neighbours if pair[0]), key=lambda pair: pair[0]
    ):
        px, py = platform["position"]
        target = platform.get("baseZ", base_height(px, py)) + platform.get("raise", 0)
        z += (target - z) * weight
    # The bridge and its gate form a level public route across the water.
    if x >= 120 and abs(y + 60) <= 4.5:
        z = base_height(*GATE)
    return round(z, 6)


def point(x, y, dz=0):
    return [round(x, 5), round(y, 5), round(ground_height(x, y) + dz, 6)]


def heightfield():
    origin, spacing = [-142.0, -120.0], [1.5, 1.5]
    width, height = 213, 197  # Includes city approaches and the whole bridge.
    return {
        "origin": origin,
        "spacing": spacing,
        "width": width,
        "height": height,
        "heights": [
            ground_height(origin[0] + col * spacing[0], origin[1] + row * spacing[1])
            for row in range(height)
            for col in range(width)
        ],
    }


def sampled_route(points, step=2.5, dz=0):
    result = []
    for a, b in zip(points, points[1:]):
        count = max(1, math.ceil(math.dist(a, b) / step))
        result += [
            point(a[0] + (b[0] - a[0]) * i / count, a[1] + (b[1] - a[1]) * i / count, dz)
            for i in range(count)
        ]
    return result + [point(*points[-1], dz)]
