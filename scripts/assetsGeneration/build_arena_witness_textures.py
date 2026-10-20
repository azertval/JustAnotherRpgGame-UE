#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Original, periodic PBR textures for the Arena material comparison.

One UV repeat covers two metres. Geometry, illumination and palette remain common;
The current candidate is fantasy painting with constructed pigment strokes and
separate material identities; the two former candidates remain comparison states.
No image/reference is sampled. Base colour, physical height and roughness are
evaluated independently from seeded analytic fields. Normals are the derivative
of that physical height, never a derivative of the base colour. Metallic and
occlusion are material properties, not inferred image channels.

Run with the repository Python: arena_geometry_textures.py [--size 2048]
    [--styles painted]. Other styles are retained, or rebuilt at 1024 if missing.
Optional original base-colour input: inputs/stone_cream_painted_detail.png (preferred)
or inputs/stone_cream_painted.png. --apply-inputs
copies its exact PNG bytes and updates hashes/provenance without generating any
normal, ORM, resize, crop or image edit. Its seamless tiling remains unvalidated.
PNG files are regenerable local output, accompanied by a provenance manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/arena-witness-materials"
STYLES = ("painted", "stylized", "realistic")
NAMES = (
    "stone_cream",
    "marble_white",
    "bronze",
    "dark_metal",
    "burgundy",
    "sand",
    "wood",
    "mortar",
)
TILE_METRES = 2.0
VERSION = 5
PALETTES = {
    "stone_cream": (0.74, 0.68, 0.56),
    "marble_white": (0.87, 0.85, 0.79),
    "bronze": (0.53, 0.34, 0.13),
    "dark_metal": (0.19, 0.20, 0.21),
    "burgundy": (0.35, 0.042, 0.072),
    "sand": (0.70, 0.56, 0.36),
    "wood": (0.32, 0.16, 0.065),
    "mortar": (0.38, 0.35, 0.31),
}


def pigment_strokes(u, v, seed, count, long_range, short_range):
    """Construct tapered, angular brush deposits, with irregular staggered placement.

    These are pigment shapes, not light/shadow. Periodic shortest distances wrap
    strokes across the texture edges without mirroring or a regular stamp grid.
    """
    rng = np.random.default_rng(seed)
    strokes = np.zeros(u.shape + (3,), dtype=np.float32)
    for _ in range(count):
        cx, cy = rng.random(2)
        angle = rng.uniform(-0.45, 0.45) + rng.choice([0.0, math.pi / 2])
        length, width = rng.uniform(*long_range), rng.uniform(*short_range)
        dx = np.mod(u - cx + 0.5, 1.0) - 0.5
        dy = np.mod(v - cy + 0.5, 1.0) - 0.5
        along = dx * math.cos(angle) + dy * math.sin(angle)
        across = -dx * math.sin(angle) + dy * math.cos(angle)
        taper = width * (0.70 + 0.25 * np.sin(along / length * 2.0 + cy * 12))
        shape = np.clip((1 - np.abs(along) / length) * 9, 0, 1) * np.clip(
            (1 - np.abs(across) / taper) * 7, 0, 1
        )
        # Warm cream, subdued blue-violet and ochre pigments, never white highlights.
        pigments = (
            (0.045, 0.022, -0.018),
            (-0.027, -0.008, 0.025),
            (0.026, 0.027, 0.015),
            (-0.023, -0.018, -0.010),
        )
        strokes += shape[..., None] * np.asarray(
            pigments[rng.integers(0, len(pigments))], dtype=np.float32
        )
    return np.clip(strokes, -0.075, 0.075)


def cell_random(ix, iy, nx, ny, seed):
    """Seeded toroidal cell variation; no regular stamp or sampled image."""
    code = (
        np.mod(ix, nx).astype(np.uint64) * 374761393
        + np.mod(iy, ny).astype(np.uint64) * 668265263
        + seed * 1442695041
    ) & np.uint64(0xFFFFFFFF)
    code = ((code ^ (code >> np.uint64(13))) * 1274126177) & np.uint64(0xFFFFFFFF)
    return ((code ^ (code >> np.uint64(16))) & np.uint64(65535)).astype(np.float32) / 65535


def granules(u, v, seed, nx, ny, coverage=0.6):
    """Jittered elliptical pore/grain caps with varied radii, aspect and occurrence."""
    pu, pv = u * nx, v * ny
    ix, iy = np.floor(pu), np.floor(pv)
    result = np.zeros_like(u)
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            cx, cy = ix + dx, iy + dy
            a = cell_random(cx, cy, nx, ny, seed)
            b = cell_random(cx, cy, nx, ny, seed + 1)
            c = cell_random(cx, cy, nx, ny, seed + 2)
            radius = 0.19 + 0.22 * c
            x = (pu - cx - 0.5 - 0.60 * (a - 0.5)) / radius
            y = (pv - cy - 0.5 - 0.60 * (b - 0.5)) / (radius * (0.65 + 0.75 * a))
            cap = np.maximum(0, 1 - x * x - y * y) ** 3
            result += cap * (c < coverage) * (0.45 + 0.55 * b)
    return np.clip(result, 0, 1)


def physical_scratches(u, v, seed, count=20, width=0.0018):
    """Independent tapered tool cuts, 1-4 mm wide and 6-30 cm long."""
    rng = np.random.default_rng(seed)
    result = np.zeros_like(u)
    for _ in range(count):
        cx, cy = rng.random(2)
        angle = rng.uniform(-0.6, 0.6)
        length = rng.uniform(0.03, 0.15)
        du = np.mod(u - cx + 0.5, 1) - 0.5
        dv = np.mod(v - cy + 0.5, 1) - 0.5
        along = du * math.cos(angle) + dv * math.sin(angle)
        across = -du * math.sin(angle) + dv * math.cos(angle)
        taper = np.maximum(0, 1 - (along / length) ** 2) ** 2
        line = np.maximum(0, 1 - (across / (width * rng.uniform(0.6, 1.2))) ** 2) ** 2
        result += taper * line * rng.uniform(0.5, 1)
    return np.clip(result, 0, 1)


def wood_flow(u, v, seed):
    """Organic fibre deflection around a few knots; all distances wrap the tile."""
    flow = 0.10 * field(u, v, seed, 1, 5, count=7) + 0.045 * np.sin(math.tau * (2 * v + u))
    knots = np.zeros_like(u)
    rings = np.zeros_like(u)
    rng = np.random.default_rng(seed + 1)
    for _ in range(4):
        cx, cy = rng.random(2)
        rx, ry = rng.uniform(0.020, 0.055), rng.uniform(0.04, 0.09)
        x = (np.mod(u - cx + 0.5, 1) - 0.5) / rx
        y = (np.mod(v - cy + 0.5, 1) - 0.5) / ry
        radius = np.sqrt(x * x + y * y)
        envelope = np.maximum(0, 1 - radius / 3) ** 3
        flow += 0.22 * envelope * np.sin(np.arctan2(y, x))
        knots = np.maximum(knots, np.maximum(0, 1 - radius) ** 2)
        rings += envelope * np.sin(math.tau * (3.5 * radius + 0.13 * np.sin(np.arctan2(y, x) * 3)))
    return flow, knots, rings


def painted_material(name, u, v):
    """Fantasy portrait-inspired material identities, with simplified pigment forms.

    The rock, wood, metal and fabric use different constructive patterns. Their
    physical height is authored independently; brush colours never become normals.
    Large carved relief, joints and edges belong to the companion Blender meshes.
    """
    seed = 1801 + NAMES.index(name) * 173
    pigment = pigment_strokes(u, v, seed, 16, (0.08, 0.19), (0.025, 0.055))
    pigment += pigment_strokes(u, v, seed + 1, 28, (0.025, 0.080), (0.006, 0.015))
    physical = field(u, v, seed + 80, 12, 40, count=8)
    rough_field = field(u, v, seed + 90, 2, 8, count=8)
    bases = {
        "stone_cream": (0.67, 0.625, 0.525),
        "marble_white": (0.795, 0.785, 0.72),
        "bronze": (0.61, 0.385, 0.145),
        "dark_metal": (0.205, 0.195, 0.23),
        "burgundy": (0.425, 0.067, 0.113),
        "sand": (0.68, 0.545, 0.345),
        "wood": (0.36, 0.19, 0.095),
        "mortar": (0.345, 0.318, 0.30),
    }
    colour = np.broadcast_to(np.asarray(bases[name], dtype=np.float32), u.shape + (3,)).copy()
    colour += pigment * (1.0 if name in ("stone_cream", "marble_white", "sand") else 0.40)
    height = np.zeros_like(u)
    rough = np.full_like(u, 0.86)
    metal = np.zeros_like(u)
    ao = np.ones_like(u)
    if name == "stone_cream":
        # Broad worked waviness, sparse shallow pockets, fine pores and short chisel cuts.
        # None is derived from the original AI colour image, which may replace colour only.
        wear = field(u, v, seed + 81, 3, 12, count=9)
        pores = granules(u, v, seed + 82, 170, 139, 0.28)
        pockets = granules(u, v, seed + 86, 21, 17, 0.10)
        scratches = physical_scratches(u, v, seed + 83, 34, 0.0014)
        tool_phase = math.tau * (113 * u + 2 * v + 0.18 * field(u, v, seed + 84, 2, 8, count=6))
        tool = np.clip((np.sin(tool_phase) - 0.35) / 0.65, 0, 1) ** 2
        tool *= np.clip((wear + 0.30) / 1.30, 0, 1)
        height = (
            0.00038 * wear
            + 0.00010 * physical
            - 0.00055 * tool
            - 0.0011 * scratches
            - 0.0015 * pores
            - 0.0022 * pockets
        )
        rough = 0.80 + 0.095 * rough_field + 0.08 * pores + 0.045 * pockets - 0.085 * tool
        mineral = field(u, v, seed + 89, 3, 13, count=8)
        colour += mineral[..., None] * np.array([0.035, 0.027, 0.018])
        ao -= 0.18 * pores + 0.14 * pockets + 0.06 * scratches
    elif name == "marble_white":
        # Hierarchy of broad mineral ribbons and fine branching filaments, with
        # curves governed by separate periodic carriers, not one enlarged sine.
        warp = 0.80 * field(u, v, seed + 11, 1, 5, count=9) + 0.35 * np.sin(math.tau * (2 * v - u))
        phase = math.tau * (u + v) + warp
        trunk = np.sin(phase)
        main_vein = np.exp(-((trunk / (0.035 + 0.02 * (1 + rough_field))) ** 2))
        branch_phase = math.tau * (3 * u - 2 * v) + 1.25 * field(u, v, seed + 12, 2, 7, count=8)
        branches = np.exp(-((np.sin(branch_phase) / 0.055) ** 2)) * np.clip(0.5 + 0.7 * trunk, 0, 1)
        fine_veins = np.exp(
            -((np.sin(phase * 5 + 0.6 * field(u, v, seed + 13, 3, 11, count=7)) / 0.040) ** 2)
        )
        cloud = field(u, v, seed + 14, 1, 7, count=8)
        colour -= main_vein[..., None] * np.array([0.13, 0.105, 0.085])
        colour -= branches[..., None] * np.array([0.065, 0.054, 0.042])
        colour -= fine_veins[..., None] * np.array([0.025, 0.022, 0.018])
        colour += cloud[..., None] * np.array([0.035, 0.032, 0.022])
        polishing = field(u, v, seed + 110, 3, 14, count=9)
        scratches = physical_scratches(u, v, seed + 111, 14, 0.0009)
        height = 0.000035 * physical + 0.00011 * polishing - 0.00014 * scratches
        rough = (
            0.28 + 0.10 * rough_field + 0.12 * np.maximum(polishing - 0.15, 0) + 0.085 * scratches
        )
    elif name == "bronze":
        oxidation = np.clip((field(u, v, seed + 15, 2, 9, count=9) - 0.37) * 2.2, 0, 0.75)
        oxidation *= 0.65 + 0.35 * np.maximum(field(u, v, seed + 151, 12, 42, count=8), 0)
        scratches = physical_scratches(u, v, seed + 152, 42, 0.0012)
        colour = (
            colour * (1 - oxidation[..., None])
            + np.array([0.12, 0.265, 0.235]) * oxidation[..., None]
        )
        colour -= scratches[..., None] * np.array([0.04, 0.023, 0.008])
        hammer = field(u, v, seed + 153, 8, 27, count=8)
        height = 0.00020 * hammer + 0.00027 * oxidation - 0.00035 * scratches + 0.000035 * physical
        rough = 0.32 + 0.095 * rough_field + 0.44 * oxidation + 0.12 * scratches
        metal = 0.98 - 0.80 * oxidation
    elif name == "dark_metal":
        hammer = field(u, v, seed + 16, 12, 28, count=8)
        scratches = physical_scratches(u, v, seed + 161, 24, 0.0011)
        brushing = np.sin(math.tau * (211 * v + 0.13 * field(u, v, seed + 162, 2, 7, count=6)))
        height = 0.00028 * hammer - 0.00023 * scratches + 0.00003 * brushing
        rough = 0.47 + 0.105 * rough_field + 0.10 * scratches
        metal = np.full_like(u, 0.94)
    elif name == "burgundy":
        # Original repeating botanical brocade: paired slender leaves around a
        # flowing stem. It is ornament, never a borrowed heraldic emblem.
        x = np.mod(u * 5, 1) - 0.5
        y = np.mod(v * 6, 1) - 0.5
        stem = np.exp(-(((x - 0.10 * np.sin(y * math.tau)) / 0.018) ** 2))
        leaf_a = np.clip(1 - ((x - 0.12 - y * 0.5) / 0.11) ** 2 - ((y + 0.10) / 0.17) ** 2, 0, 1)
        leaf_b = np.clip(1 - ((x + 0.10 + y * 0.5) / 0.11) ** 2 - ((y - 0.13) / 0.15) ** 2, 0, 1)
        motif = np.maximum(stem * 0.50, np.maximum(leaf_a, leaf_b))
        colour = (
            colour * (1 - (motif * 0.32)[..., None])
            + np.array([0.63, 0.35, 0.125]) * (motif * 0.32)[..., None]
        )
        # Independent physical weave; ornamental colour is not converted to height.
        warp_phase = np.mod(360 * u, 1) - 0.5
        weft_phase = np.mod(320 * v, 1) - 0.5
        warp = np.maximum(0, 1 - (warp_phase / 0.47) ** 2) ** 0.7
        weft = np.maximum(0, 1 - (weft_phase / 0.47) ** 2) ** 0.7
        over = 0.5 + 0.5 * np.sin(math.pi * 360 * u) * np.sin(math.pi * 320 * v)
        weave = (0.25 + 0.55 * over) * warp + (0.80 - 0.55 * over) * weft
        nap = field(u, v, seed + 163, 18, 75, count=8)
        height = 0.00018 * weave + 0.000025 * nap - 0.000055 * (1 - warp) * (1 - weft)
        colour += (0.009 * (warp - weft))[..., None] * np.array([1, 0.35, 0.4])
        rough = 0.84 + 0.055 * rough_field + 0.055 * (1 - weave)
        ao -= 0.10 * (1 - warp) * (1 - weft)
    elif name == "sand":
        grains = granules(u, v, seed + 17, 380, 311, 0.88)
        grouped_grains = granules(u, v, seed + 18, 49, 41, 0.36)
        ripple = field(u, v, seed + 171, 3, 11, count=8)
        mineral = field(u, v, seed + 172, 36, 120, count=8)
        colour += (0.030 * mineral)[..., None] * np.array([1, 0.8, 0.55])
        colour -= grouped_grains[..., None] * np.array([0.045, 0.033, 0.017])
        height = 0.00070 * grains + 0.00135 * grouped_grains + 0.00065 * ripple
        rough = 0.94 + 0.028 * rough_field + 0.025 * (1 - grains)
        ao -= 0.06 * (1 - grains) * grouped_grains
    elif name == "wood":
        # Narrow, meandering wood fibres in long bands, with variable spacing.
        flow, knots, rings = wood_flow(u, v, seed + 19)
        phase = math.tau * (17 * u + flow)
        fibre = np.exp(-((np.sin(phase) / 0.18) ** 2))
        growth = np.sin(math.tau * (5 * u + 0.40 * flow))
        colour -= fibre[..., None] * np.array([0.072, 0.045, 0.022])
        colour += growth[..., None] * np.array([0.039, 0.027, 0.013])
        colour -= knots[..., None] * np.array([0.11, 0.065, 0.028])
        colour += rings[..., None] * np.array([0.034, 0.020, 0.008])
        # Physical capillary/tool structure uses a separate authored flow.
        physical_flow, physical_knots, _ = wood_flow(u, v, seed + 191)
        grooves = np.maximum(np.sin(math.tau * (61 * u + physical_flow)) - 0.20, 0) ** 2
        scratches = physical_scratches(u, v, seed + 192, 18, 0.0014)
        height = (
            0.00015 * physical - 0.00042 * grooves - 0.00065 * physical_knots - 0.00032 * scratches
        )
        rough = 0.61 + 0.10 * rough_field + 0.075 * grooves + 0.06 * physical_knots
        ao -= 0.06 * grooves + 0.10 * physical_knots
    elif name == "mortar":
        grains = granules(u, v, seed + 193, 120, 109, 0.65)
        height = 0.00034 * physical + 0.00027 * grains
        colour += pigment * 0.2
        rough = 0.95 + 0.02 * rough_field
    return np.clip(colour, 0, 1), height, np.clip(rough, 0.08, 1), metal, np.clip(ao, 0.6, 1)


def field(u, v, seed, low, high, count=18):
    """Integer Fourier modes give exact periodicity, including derivatives."""
    rng = np.random.default_rng(seed)
    result = np.zeros_like(u)
    for _ in range(count):
        a, b = rng.integers(-high, high + 1, 2)
        if abs(a) + abs(b) < low:
            a += low
        result += rng.uniform(0.4, 1.0) * np.sin(
            math.tau * (a * u + b * v) + rng.uniform(0, math.tau)
        )
    return np.tanh(result / np.sqrt(count))


def evaluate(name, style, u, v):
    """Return colour (sRGB), height (metres), roughness, metal, physical AO."""
    if style == "painted":
        return painted_material(name, u, v)
    seed = 1129 + NAMES.index(name) * 137
    level = STYLES.index(style)
    broad = field(u, v, seed, 1, 4)
    middle = field(u, v, seed + 1, 4, 16)
    fine = field(u, v, seed + 2, 24, 100)
    height_field = field(u, v, seed + 20, 2, (4, 18, 92)[level])
    rough_field = field(u, v, seed + 30, 1, (4, 20, 88)[level])
    detail = (0.0, 0.12, 0.78)[level]
    tint = (0.06, 0.025, 0.045)[level] * broad + detail * (0.020 * middle + 0.026 * fine)
    colour = np.asarray(PALETTES[name]) * (1.0 + tint[..., None])
    height = np.zeros_like(u)
    rough = np.zeros_like(u)
    metal = np.zeros_like(u)
    ao = np.ones_like(u)

    if name == "stone_cream":
        minerals = field(u, v, seed + 3, 1, 7)
        colour += ((0.008, 0.010, 0.020)[level] * minerals)[..., None] * np.array([1.0, 0.80, 0.46])
        pores = np.maximum(-height_field - 0.42, 0.0)
        # Millimetric pores in real limestone; the stylized surface stays quiet
        # so the dressed blocks, bevels and joints carry the large-scale relief.
        height = (0.000045, 0.00020, 0.00016)[level] * height_field - (0.0, 0.00004, 0.00065)[
            level
        ] * pores
        rough = (0.92, 0.82, 0.76)[level] + (0.015, 0.035, 0.13)[level] * rough_field
        if style == "realistic":
            mineral_spots = np.maximum(fine - 0.48, 0.0)
            colour -= mineral_spots[..., None] * np.array([0.095, 0.078, 0.052])
        ao -= (0.0, 0.025, 0.15)[level] * pores
    elif name == "marble_white":
        phase = math.tau * (2 * u + v) + 0.70 * np.sin(math.tau * (u - 2 * v)) + 0.28 * broad
        vein = np.exp(-((np.sin(phase) / (0.15, 0.075, 0.045)[level]) ** 2))
        secondary = np.exp(-((np.sin(phase * 3) / 0.065) ** 2))
        colour -= vein[..., None] * np.array([0.060, 0.055, 0.045]) * (0.8, 0.50, 1.0)[level]
        colour -= (detail * secondary)[..., None] * np.array([0.04, 0.045, 0.045])
        # Geological veins affect colour; polishing relief is a separate field.
        height = (0.000025, 0.000040, 0.000040)[level] * height_field
        rough = (0.49, 0.32, 0.23)[level] + (0.015, 0.025, 0.07)[level] * rough_field
    elif name == "bronze":
        oxidation = np.clip((broad + 0.20 * middle - 0.29) * (0.3, 0.6, 0.9)[level], 0, 0.65)
        colour = (
            colour * (1 - oxidation[..., None])
            + np.array([0.10, 0.22, 0.16]) * oxidation[..., None]
        )
        height = (0.00003, 0.00012, 0.00010)[level] * height_field
        rough = (
            (0.55, 0.40, 0.32)[level] + (0.015, 0.04, 0.12)[level] * rough_field + 0.35 * oxidation
        )
        metal = 1.0 - oxidation
    elif name == "dark_metal":
        brushed = np.sin(math.tau * (32, 72, 190)[level] * v + 0.35 * broad)
        colour += (detail * 0.014 * brushed)[..., None]
        height = (0.000008, 0.000018, 0.000025)[level] * brushed + 0.000012 * height_field
        rough = (0.63, 0.45, 0.38)[level] + (0.015, 0.025, 0.10)[level] * rough_field
        metal = np.full_like(u, 0.95)
    elif name == "burgundy":
        threads = (12, 64, 180)[level]
        weave = np.sin(math.tau * threads * u) * np.sin(math.tau * threads * v)
        colour += (detail * 0.014 * weave)[..., None] * np.array([1.0, 0.35, 0.40])
        height = (0.000012, 0.00009, 0.00010)[level] * weave + 0.000012 * height_field
        rough = (0.94, 0.88, 0.82)[level] + 0.055 * rough_field
        ao -= (0.0, 0.04, 0.07)[level] * np.maximum(-weave, 0)
    elif name == "sand":
        ripple = np.sin(math.tau * (5 * u + 2 * v) + 0.55 * np.sin(math.tau * v))
        grains = field(u, v, seed + 40, 60, 220, count=24)
        colour += ((0.0, 0.003, 0.008)[level] * ripple + (0.0, 0.003, 0.025)[level] * grains)[
            ..., None
        ]
        height = (0.00003, 0.00045, 0.00080)[level] * ripple + (0.0, 0.00007, 0.00018)[
            level
        ] * grains
        rough = (0.97, 0.94, 0.91)[level] + 0.035 * rough_field
        ao -= (0.0, 0.035, 0.065)[level] * np.maximum(-grains, 0)
    elif name == "wood":
        phase = math.tau * 7 * u + 0.85 * np.sin(math.tau * v) + 0.22 * broad
        grain = np.sin(phase) + detail * 0.38 * np.sin(phase * 6)
        colour += grain[..., None] * np.array([0.035, 0.025, 0.014])
        height = (0.000025, 0.00018, 0.00025)[level] * grain + (0.0, 0.00002, 0.00005)[
            level
        ] * height_field
        rough = (0.88, 0.72, 0.61)[level] + (0.015, 0.03, 0.10)[level] * rough_field
    elif name == "mortar":
        height = 0.00020 * height_field
        rough = 0.94 + 0.025 * rough_field
    return np.clip(colour, 0, 1), height, np.clip(rough, 0.08, 1), metal, np.clip(ao, 0.6, 1)


def images(name, style, size, measurements=None):
    axis = np.arange(size, dtype=np.float32) / size
    u, v = np.meshgrid(axis, axis)
    colour, height, rough, metal, ao = evaluate(name, style, u, v)
    spacing = TILE_METRES / size
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) / (2 * spacing)
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) / (2 * spacing)
    normal = np.stack((-dx, -dy, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    orm = np.stack((ao, rough, metal), axis=-1)
    if measurements is not None:
        decoded = np.rint((normal * 0.5 + 0.5) * 255) / 255 * 2 - 1
        measurements.update(
            {
                "size": [size, size],
                "heightMinMm": round(float(height.min()) * 1000, 5),
                "heightMaxMm": round(float(height.max()) * 1000, 5),
                "heightPeakToPeakMm": round(float(np.ptp(height)) * 1000, 5),
                "heightRmsMm": round(float(np.sqrt(np.mean(height**2))) * 1000, 5),
                "normalZRange": [
                    round(float(normal[..., 2].min()), 6),
                    round(float(normal[..., 2].max()), 6),
                ],
                "normalQuantizedLengthMaxError": round(
                    float(np.max(np.abs(np.linalg.norm(decoded, axis=-1) - 1))), 6
                ),
                "roughnessRange": [round(float(rough.min()), 5), round(float(rough.max()), 5)],
                "metalRange": [round(float(metal.min()), 5), round(float(metal.max()), 5)],
                "aoRange": [round(float(ao.min()), 5), round(float(ao.max()), 5)],
                "heightSource": "Independent authored periodic physical features, never baseColor pixels",
            }
        )
    return {"baseColor": colour, "normal": normal * 0.5 + 0.5, "orm": orm}


def periodicity_check(name):
    """Analytic opposite-edge values/height derivatives, not adjacent pixel equality."""
    axis = np.linspace(0, 1, 257, dtype=np.float64)
    zero, one = np.zeros_like(axis), np.ones_like(axis)
    errors = {key: 0.0 for key in ("baseColor", "height", "roughness", "metal", "ao")}
    for a, b in [
        (evaluate(name, "painted", zero, axis), evaluate(name, "painted", one, axis)),
        (evaluate(name, "painted", axis, zero), evaluate(name, "painted", axis, one)),
    ]:
        for key, left, right in zip(errors, a, b):
            errors[key] = max(errors[key], float(np.max(np.abs(left - right))))
    epsilon = 1 / 2048
    derivative_error = 0.0
    for transposed in [False, True]:

        def at(value, transposed=transposed):
            coord = np.full_like(axis, value)
            return (
                evaluate(name, "painted", axis, coord)[1]
                if transposed
                else evaluate(name, "painted", coord, axis)[1]
            )

        d0 = (at(epsilon) - at(-epsilon)) / (2 * epsilon)
        d1 = (at(1 + epsilon) - at(1 - epsilon)) / (2 * epsilon)
        derivative_error = max(derivative_error, float(np.max(np.abs(d0 - d1))))
    if (
        errors["height"] > 1e-8
        or max(errors[k] for k in errors if k != "height") > 1e-5
        or derivative_error > 1e-6
    ):
        raise ValueError(
            f"Procedural tile discontinuity {name}: {errors}, derivative {derivative_error}"
        )
    return {
        "status": "verified",
        "edgeValueMaxErrors": errors,
        "heightDerivativeMaxError": derivative_error,
        "scope": "Procedural colour/physical maps only; original AI colour input is excluded",
    }


def apply_original_inputs(output=OUTPUT, manifest=None):
    """Copy only approved original base-colour inputs, byte for byte.

    Reading dimensions is inspection only. No colour conversion, resampling or
    normal/roughness derivation occurs. The input is cited under a file key so the
    asset orphan checker sees both the source and generated texture references.
    """
    manifest_path = output / "manifest.json"
    if manifest is None:
        if not manifest_path.is_file():
            raise RuntimeError("Generate the procedural textures once before --apply-inputs")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("version") != VERSION:
        raise RuntimeError("Original input override requires the current texture manifest version")
    candidates = [
        output / "inputs/stone_cream_painted_detail.png",
        output / "inputs/stone_cream_painted.png",
    ]
    source = next((p for p in candidates if p.is_file()), candidates[-1])
    if not source.is_file():
        print("No original stone_cream painted input; procedural base colour retained", flush=True)
        return manifest
    content = source.read_bytes()
    with Image.open(source) as image:
        if image.format != "PNG":
            raise ValueError("Original painted input must be a PNG; it is never converted")
        size = list(image.size)
    entry = manifest["styles"]["painted"]["stone_cream"]["baseColor"]
    destination = output / entry["file"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    entry.update(
        {
            "sha256": digest,
            "size": size,
            "provenance": "Original AI-generated mineral painting, exact PNG bytes; no sourcebook image; no edit or resampling.",
            "periodicity": "not validated; inspect repetition in the engine",
            "normalRelation": "none: independent physical height and ORM remain unchanged",
            "nativeProcessing": {
                "powerOfTwo": "STRETCH_TO_POWER_OF_TWO",
                "maxTextureSize": 2048,
                "mips": "TMGS_FROM_TEXTURE_GROUP",
                "streaming": True,
            },
        }
    )
    manifest["provenance"] = (
        "Original procedural physical height/ORM and pigments; painted stone baseColor "
        "may use the exact original AI-painted PNG cited in inputs. No sourcebook image."
    )
    manifest["inputs"] = [
        {
            "file": source.relative_to(output).as_posix(),
            "sha256": digest,
            "size": size,
            "usage": "painted/stone_cream/baseColor only",
            "periodicity": "not validated",
        }
    ]
    provenance = source.with_suffix(".provenance.json")
    if provenance.is_file():
        manifest["inputs"].append(
            {
                "file": provenance.relative_to(output).as_posix(),
                "usage": "original generation provenance",
            }
        )
    for previous in candidates:
        if previous == source or not previous.is_file():
            continue
        with Image.open(previous) as previous_image:
            previous_size = list(previous_image.size)
        manifest["inputs"].append(
            {
                "file": previous.relative_to(output).as_posix(),
                "sha256": hashlib.sha256(previous.read_bytes()).hexdigest(),
                "size": previous_size,
                "usage": "previous source preserved",
            }
        )
        previous_provenance = previous.with_suffix(".provenance.json")
        if previous_provenance.is_file():
            manifest["inputs"].append(
                {
                    "file": previous_provenance.relative_to(output).as_posix(),
                    "usage": "previous generation provenance preserved",
                }
            )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Copied original stone painting {size[0]}×{size[1]} byte for byte; normal/ORM untouched",
        flush=True,
    )
    return manifest


def generate(output=OUTPUT, size=2048, styles=("painted",)):
    if size < 256 or size > 2048 or size & (size - 1):
        raise ValueError("size must be a power of two between 256 and 2048")
    existing = output / "manifest.json"
    previous = json.loads(existing.read_text(encoding="utf-8")) if existing.is_file() else {}
    manifest = {
        "generator": "scripts/assetsGeneration/arena_geometry_textures.py",
        "version": VERSION,
        "size": size,
        "styleSizes": previous.get("styleSizes", {}),
        "tileMetres": TILE_METRES,
        "styleRevisions": {"painted": VERSION, "stylized": 2, "realistic": 2},
        "provenance": "Original seeded periodic analytic material fields; normals from independent physical height, never baseColor; no corpus images.",
        "styles": {},
        "measurements": previous.get("measurements", {}),
        "periodicity": {},
    }
    for style in STYLES:
        materials = {}
        manifest["measurements"].setdefault(style, {})
        actual_size = size if style in styles else previous.get("styleSizes", {}).get(style, 1024)
        for name in NAMES:
            old = previous.get("styles", {}).get(style, {}).get(name)
            if (
                style not in styles
                and old
                and all((output / entry["file"]).is_file() for entry in old.values())
            ):
                materials[name] = old
                continue
            textures = {}
            measured = {}
            for role, values in images(name, style, actual_size, measured).items():
                path = output / style / f"{name}_{role}.png"
                path.parent.mkdir(parents=True, exist_ok=True)
                pixels = np.rint(np.clip(values, 0, 1) * 255).astype(np.uint8)
                Image.fromarray(pixels).save(path, compress_level=9)
                textures[role] = {
                    "file": path.relative_to(output).as_posix(),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            materials[name] = textures
            manifest["measurements"][style][name] = measured
            print(f"{style}/{name}: {actual_size}², baseColor + physical normal + ORM", flush=True)
        manifest["styles"][style] = materials
        manifest["styleSizes"][style] = actual_size
    output.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        manifest["periodicity"][name] = periodicity_check(name)
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return apply_original_inputs(output, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--styles", nargs="+", choices=STYLES, default=["painted"])
    parser.add_argument(
        "--apply-inputs",
        action="store_true",
        help="copy original base-colour inputs only, no texture generation",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.apply_inputs:
        apply_original_inputs(args.output)
        return
    manifest = generate(args.output, args.size, args.styles)
    print(
        f"{len(STYLES) * len(NAMES) * 3} original PNG textures; styles {manifest['styleSizes']} in {args.output}"
    )


if __name__ == "__main__":
    main()
