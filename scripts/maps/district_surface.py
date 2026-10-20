# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Shared map-space ground sampling for urban relief, in metres.

The same row-major field is persisted on AJadgMapFrame in centimetres. Terrain
altitude never selects a building storey: upper floors have explicit local bounds.
"""
from __future__ import annotations

import math


def validate_surface(data: dict) -> list[str]:
    errors = []
    field = data.get("groundHeightfield")
    if field is not None:
        try:
            width, height = field["width"], field["height"]
            if not isinstance(width, int) or not isinstance(height, int) or min(width, height) < 2:
                raise ValueError("dimensions must be integers >= 2")
            if len(field["heights"]) != width * height:
                raise ValueError("height count does not match dimensions")
            if len(field["origin"]) != 2 or len(field["spacing"]) != 2:
                raise ValueError("origin and spacing must be XY pairs")
            if any(not math.isfinite(v) for v in (*field["origin"], *field["spacing"], *field["heights"])):
                raise ValueError("all samples and coordinates must be finite")
            if min(field["spacing"]) <= 0:
                raise ValueError("spacing must be positive")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"groundHeightfield: {error}")
    levels = data.get("storeys", data.get("levels", [{"name": "street", "z": 0}]))
    for index, region in enumerate(data.get("storeyRegions", [])):
        try:
            if not isinstance(region["storey"], int) or not 0 <= region["storey"] < len(levels):
                raise ValueError("region must identify an existing storey")
            low, high = region["minimum"], region["maximum"]
            if len(low) != 3 or len(high) != 3 or any(not math.isfinite(v) for v in (*low, *high)):
                raise ValueError("bounds must contain finite XYZ coordinates")
            if any(low[k] >= high[k] for k in range(3)):
                raise ValueError("bounds must have positive volume")
        except (KeyError, TypeError, ValueError) as error:
            errors.append(f"storeyRegions[{index}]: {error}")
    return errors


def terrain_height(data: dict, x: float, y: float) -> float | None:
    """Bilinear height; None outside the sampled field, never clamp to its edge."""
    field = data.get("groundHeightfield")
    if not field:
        return None
    width, height = field["width"], field["height"]
    gx = (x - field["origin"][0]) / field["spacing"][0]
    gy = (y - field["origin"][1]) / field["spacing"][1]
    if not 0 <= gx <= width - 1 or not 0 <= gy <= height - 1:
        return None
    ix, iy = min(int(gx), width - 2), min(int(gy), height - 2)
    fx, fy = gx - ix, gy - iy
    values = field["heights"]
    first = values[iy * width + ix] * (1 - fx) + values[iy * width + ix + 1] * fx
    second = values[(iy + 1) * width + ix] * (1 - fx) + values[(iy + 1) * width + ix + 1] * fx
    return first * (1 - fy) + second * fy


def ground_height(data: dict, x: float, y: float, storey: int = 0) -> float:
    levels = data.get("storeys", data.get("levels", [{"name": "street", "z": 0}]))
    for region in data.get("storeyRegions", []):
        low, high = region["minimum"], region["maximum"]
        if region["storey"] == storey and low[0] <= x <= high[0] and low[1] <= y <= high[1]:
            return low[2]
    if storey != 0:
        return levels[storey]["z"]
    sampled = terrain_height(data, x, y)
    return sampled if sampled is not None else levels[0]["z"]


def storey_at(data: dict, point: list[float]) -> int:
    """Resolve authored points on floors, with the same 50 cm tolerance as runtime."""
    if data.get("groundHeightfield") or data.get("storeyRegions"):
        candidates = []
        for region in data.get("storeyRegions", []):
            low, high = region["minimum"], region["maximum"]
            if (low[0] <= point[0] <= high[0] and low[1] <= point[1] <= high[1]
                    and low[2] - .5 <= point[2] <= high[2] + .5):
                candidates.append(region)
        return max(candidates, key=lambda r: r["minimum"][2])["storey"] if candidates else 0
    levels = data.get("storeys", data.get("levels", [{"name": "street", "z": 0}]))
    return min(range(len(levels)), key=lambda i: abs(levels[i]["z"] - point[2]))
