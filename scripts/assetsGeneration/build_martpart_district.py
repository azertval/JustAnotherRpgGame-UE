#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Build the complete, modular Martpart district with headless Blender.

The sourcebook supplies identity; the atlas fixes landmark neighbourhoods.
X follows the drawing's right and Y its bottom, not the compass rose. Urban
relief, level foundations and carriageways share one altitude contract. No
Unreal assets or canonical map data are touched. Roofs are removable.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "maps"))
import martpart_district_layout as layout

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/martpart-district"
DIAGNOSTICS = ROOT / "Saved/Jadg/districts/martpart/geometry"
BLENDER = Path(r"D:\Blender Foundation\Blender 5.2\blender.exe")
spec = importlib.util.spec_from_file_location(
    "martpart_wicked_helpers", Path(__file__).with_name("arena_sculpted_geometry.py")
)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
g = w.g
foliage_spec = importlib.util.spec_from_file_location(
    "martpart_district_foliage", Path(__file__).with_name("district_foliage.py")
)
foliage = importlib.util.module_from_spec(foliage_spec)
foliage_spec.loader.exec_module(foliage)
EXTRA_MATERIALS = {
    "roof_terracotta": ((0.40, 0.13, 0.065, 1), 0.84, 0),
    "pottery": ((0.47, 0.24, 0.12, 1), 0.63, 0),
    "linen": ((0.82, 0.73, 0.52, 1), 0.91, 0),
    "roof_blue": ((0.20, 0.22, 0.36, 1), 0.79, 0),
    "plaster_ochre": ((0.61, 0.40, 0.20, 1), 0.87, 0),
    "plaster_sage": ((0.32, 0.40, 0.30, 1), 0.88, 0),
    "produce_red": ((0.50, 0.075, 0.035, 1), 0.64, 0),
    "produce_green": ((0.20, 0.34, 0.065, 1), 0.69, 0),
    "cobble": ((0.38, 0.34, 0.28, 1), 0.89, 0),
    "foliage": ((0.17, 0.29, 0.12, 1), 0.90, 0),
}
g.MATERIALS.update(EXTRA_MATERIALS)
g.NAMES[:] = list(g.MATERIALS)
OBJECTS, ROOFS, LIGHTS, LANDMARKS, TARGETS = [], [], [], [], []
BUILDINGS = []
REUSE = {}
PUBLIC_PAVING_AREAS = [
    (-116, 55, -76, 113),   # Tamera / Hen's Alley frontage and service courts.
    (-44, 84, -14, 116),   # Public gallery court.
    (-29, -74, 29, -19),   # Municipal market and its commercial parvis.
    (21, 35, 68, 82),      # Illu Die forecourt, outside the arena itself.
]
STREET_FINISHING_GROUPS = [
    (-112, 66), (-112, 84), (-112, 102), (-104, 72),
    (-88, 66), (-84, 84), (-80, 102), (-88, 108),
    (-22, -60), (-10, -60), (6, -26), (18, -26),
    (23, 37), (59, 37), (23, 49), (59, 73),
]


def block(*args):
    g.block(*args)


def old_bridge():
    """Three shallow stone vaults and cutwater piers support a level public deck."""
    block(0, 0, -0.55, 24, 8, 0.55, "stone_cream")
    for y in [-4, 4]:
        block(0, y, 0, 24, 0.35, 1, "stone_cream")
        block(0, y, 1, 24, 0.48, 0.15, "marble_white")
        for x in range(-11, 12, 2):
            block(x, y, 0, 0.30, 0.52, 1.08, "marble_white")
    for x in [-12, -4, 4, 12]:
        block(x, 0, -4.4, 1.3, 8.3, 3.85, "stone_cream")
        for y in [-4.1, 4.1]:
            g.turned(
                x, y, -4.4, [(0.95, 0), (0.95, 1.5), (0.68, 2.5), (0.50, 3.6)], "stone_cream", 4
            )
    for cx in [-8, 0, 8]:
        for j in range(20):
            a, b = j * math.pi / 20 + 0.002, (j + 1) * math.pi / 20 - 0.002
            inner = [(cx + 3.34 * math.cos(t), -3.50 + 2.42 * math.sin(t)) for t in [a, b]]
            outer = [(cx + 3.76 * math.cos(t), -3.50 + 2.82 * math.sin(t)) for t in [a, b]]
            g.prism([inner[0], outer[0], outer[1], inner[1]], -4.03, 4.03)
            # Masonry spandrel between the actual vault and the deck.
            g.prism([outer[0], (outer[0][0], -0.55), (outer[1][0], -0.55), outer[1]], -3.9, 3.9)


def opposite_bank():
    """Continuous distant Oldtown bank: background ground and masonry revetment."""
    block(40, 0, -4.4, 80, 360, 4.39, "cobble")
    block(0.35, 0, -4.4, 0.7, 360, 4.4, "stone_cream")
    for y in range(-176, 180, 8):
        if -10 < y < 6:
            continue
        block(0.4, y, 0, 1.1, 8, 0.18, "marble_white")


def table(x, y, z=0, width=2.4, depth=1.1):
    for i in range(5):
        block(
            x,
            y - depth / 2 + (i + 0.5) * depth / 5,
            z + 0.86,
            width,
            depth / 5 - 0.015,
            0.09,
            "wood",
        )
    for dx in [-width / 2 + 0.16, width / 2 - 0.16]:
        for dy in [-depth / 2 + 0.12, depth / 2 - 0.12]:
            block(x + dx, y + dy, z, 0.12, 0.12, 0.86, "wood")
    for dy in [-depth / 2 + 0.1, depth / 2 - 0.1]:
        block(x, y + dy, z + 0.58, width, 0.07, 0.16, "wood")


def barrel(x, y, z=0, scale=1):
    g.turned(
        x,
        y,
        z,
        [
            (0.29 * scale, 0),
            (0.37 * scale, 0.15 * scale),
            (0.42 * scale, 0.52 * scale),
            (0.37 * scale, 0.91 * scale),
            (0.29 * scale, scale),
        ],
        "wood",
        24,
    )
    for h, r in [(0.14, 0.375), (0.30, 0.405), (0.75, 0.398), (0.90, 0.375)]:
        g.turned(
            x, y, z + h * scale, [(r * scale, 0), (r * scale, 0.055 * scale)], "dark_metal", 24
        )
    for j in range(12):
        a = j * math.tau / 12
        g.rod(
            (x + 0.302 * scale * math.cos(a), y + 0.302 * scale * math.sin(a), z + 0.04 * scale),
            (x + 0.305 * scale * math.cos(a), y + 0.305 * scale * math.sin(a), z + 0.97 * scale),
            0.013 * scale,
            "bronze",
            6,
        )


def crate(x, y, z=0, width=0.85):
    for j in range(4):
        for sy in [-1, 1]:
            block(x, y + sy * width / 2, z + 0.08 + j * 0.17, width, 0.055, 0.14, "wood")
        for sx in [-1, 1]:
            block(x + sx * width / 2, y, z + 0.08 + j * 0.17, 0.055, width, 0.14, "wood")
    for dx in [-width / 2, width / 2]:
        for dy in [-width / 2, width / 2]:
            block(x + dx, y + dy, z, 0.065, 0.065, 0.80, "wood")
    block(x, y, z, width, width, 0.06, "wood")


def jar(x, y, z=0, scale=1):
    g.turned(
        x,
        y,
        z,
        [
            (0.20 * scale, 0),
            (0.36 * scale, 0.25 * scale),
            (0.40 * scale, 0.52 * scale),
            (0.22 * scale, 0.80 * scale),
            (0.17 * scale, 0.90 * scale),
            (0.21 * scale, 0.94 * scale),
            (0.17 * scale, 0.98 * scale),
            (0.135 * scale, 0.92 * scale),
            (0.14 * scale, 0.85 * scale),
        ],
        "pottery",
        32,
    )


def stock(kind=0):
    table(0, 0, width=2.8)
    if kind == 0:
        for x in [-0.88, 0, 0.88]:
            crate(x, 0, 0.94, 0.73)
            for j in range(12):
                px = x + ((j % 4) - 1.5) * 0.15
                py = ((j // 4) - 1) * 0.15
                g.turned(
                    px,
                    py,
                    1.29,
                    [(0.04, 0), (0.085, 0.055), (0.07, 0.125), (0.025, 0.15)],
                    "produce_red" if x < 0 else "produce_green",
                    10,
                )
    elif kind == 1:
        for j in range(5):
            x = -1.06 + j * 0.49
            g.turned(
                x,
                0,
                0.96,
                [(0.16, 0), (0.20, 0.05), (0.20, 0.33), (0.15, 0.39)],
                "linen" if j % 2 else "burgundy",
                16,
            )
        for j in range(3):
            block(0, 0.28, 1.02 + j * 0.07, 0.83, 0.38, 0.055, "linen")
    elif kind == 2:
        for j in range(5):
            jar(-1.08 + j * 0.52, 0, 0.97, 0.57 + 0.1 * (j % 2))
    else:
        for x in [-0.88, 0, 0.88]:
            g.turned(
                x,
                0,
                0.95,
                [(0.28, 0), (0.34, 0.10), (0.32, 0.36), (0.25, 0.38), (0.22, 0.26)],
                "linen",
                20,
            )
            g.turned(
                x,
                0,
                1.20,
                [(0.23, 0), (0.21, 0.06), (0.01, 0.19)],
                "sand" if x < 0 else "produce_red",
                20,
            )


def awning(width=3.6, depth=2.8, material="burgundy"):
    for x in [-width / 2 + 0.12, width / 2 - 0.12]:
        for y in [-depth / 2 + 0.12, depth / 2 - 0.12]:
            block(x, y, 0, 0.10, 0.10, 2.65, "wood")
    count = 10
    for j in range(count):
        x0 = -width / 2 + j * width / count
        x1 = x0 + width / count + 0.014
        points = []
        for side in [0, 1]:
            for k in range(9):
                y = -depth / 2 + k * depth / 8
                z = 2.68 + 0.24 * math.cos(y / depth * math.pi) - side * 0.045
                points.extend([(x0, y, z), (x1, y, z)])
        faces = []
        for side in [0, 18]:
            for k in range(8):
                a = side + 2 * k
                faces.append((a, a + 1, a + 3, a + 2))
        for k in range(8):
            for a in [2 * k, 2 * k + 1]:
                faces.append((a, a + 2, a + 20, a + 18))
        faces.extend([(0, 1, 19, 18), (16, 17, 35, 34)])
        g.solid(points, faces, material if j % 2 else "linen", 0.008)
        block((x0 + x1) / 2, depth / 2, 2.42, x1 - x0, 0.035, 0.28, material if j % 2 else "linen")
    g.rod((-width / 2, 0, 2.95), (width / 2, 0, 2.95), 0.045, "wood")


def lamp():
    g.turned(
        0,
        0,
        0,
        [(0.28, 0), (0.28, 0.17), (0.13, 0.35), (0.09, 2.85), (0.18, 2.97)],
        "dark_metal",
        24,
    )
    for dx in [-0.22, 0.22]:
        for dy in [-0.22, 0.22]:
            g.rod((dx, dy, 2.92), (dx * 0.8, dy * 0.8, 3.62), 0.025, "bronze", 8)
    block(0, 0, 3.00, 0.32, 0.32, 0.45, "linen")
    g.turned(0, 0, 3.61, [(0.36, 0), (0.25, 0.16), (0.02, 0.34)], "dark_metal", 24)


def window(x, y, z, style=0):
    block(x, y, z, 1.35, 0.12, 1.55, "dark_metal")
    for dx in [-0.70, 0.70]:
        block(x + dx, y + 0.09, z - 0.05, 0.11, 0.16, 1.69, "marble_white")
    for zz in [z - 0.08, z + 1.57]:
        block(x, y + 0.09, zz, 1.59, 0.22, 0.10, "marble_white")
    for dx in [-0.48, 0, 0.48]:
        block(x + dx, y + 0.16, z + 0.06, 0.09, 0.11, 1.40, "wood")
    block(x, y + 0.17, z + 0.71, 1.32, 0.1, 0.075, "bronze")
    for dx in [-1.03, 1.03]:
        block(x + dx, y + 0.17, z, 0.43, 0.10, 1.56, "wood" if style == 0 else "plaster_sage")
        for dz in [0.25, 0.65, 1.05, 1.40]:
            block(x + dx, y + 0.25, z + dz, 0.39, 0.05, 0.055, "bronze")


def rotated_geometry(fn, yaw):
    start = len(g.VERTS)
    fn()
    a = math.radians(-yaw)
    for i in range(start, len(g.VERTS)):
        x, y, z = g.VERTS[i]
        g.VERTS[i] = (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a), z)


def shop_shell(style=0, floors=2):
    width = 10
    height = floors * 3.5
    plaster = ["plaster_ochre", "linen", "plaster_sage"][style]
    # Real open south doorway, 2.8 m clear, with uninterrupted level floor.
    for x in [-3.25, 3.25]:
        g.masonry(x - 1.75, x + 1.75, 4.86, 0, 1.1, 0.32, 0.36, 0.84)
        block(x, 4.86, 1.10, 3.50, 0.32, height - 1.10, plaster)
    block(0, 4.86, 3.10, 3.02, 0.32, height - 3.10, plaster)
    block(0, -4.86, 1.10, width, 0.32, height - 1.10, plaster)
    g.masonry(-5, 5, -4.86, 0, 1.1, 0.32, 0.36, 0.84)
    for x in [-4.86, 4.86]:
        block(x, 0, 0, 0.32, 10, 1.1, "stone_cream")
        block(x, 0, 1.10, 0.32, 10, height - 1.10, plaster)
    for x in [-4.8, -1.48, 1.48, 4.8]:
        block(x, 4.99, 0, 0.25, 0.26, height, "marble_white" if style != 2 else "wood")
    for y in [-4.99, 4.99]:
        for z in [1.0, 3.58, height - 0.18]:
            material = "marble_white" if style != 2 else "wood"
            if y > 0 and z == 1.0:
                # The waist-height belt must never cross the real doorway.
                for x in [-3.36, 3.36]:
                    block(x, y, z, 3.53, 0.20, 0.16, material)
            else:
                block(0, y, z, 10.25, 0.20, 0.16, material)
    # Upper storey has a separate ceiling/roof object for camera occultation.
    for x in [-3.22, 3.22]:
        window(x, 5.07, 4.20, style)
        rotated_geometry(lambda x=x: window(x, 5.07, 4.20, style), 180)
        window(x, 5.07, 1.43, style)
    for x in [-1.55, 1.55]:
        block(x, 5.06, 0, 0.20, 0.22, 3.24, "marble_white")
    block(0, 5.1, 3.13, 3.37, 0.30, 0.26, "marble_white")
    if style != 2:
        g.arc(0, 5.19, 2.16, 1.39, 0.19, 0.21, segments=17)
        block(0, 5.42, 3.67, 3.75, 1.18, 0.20, "marble_white")
        for x in [-1.6, -1.2, -0.8, -0.4, 0, 0.4, 0.8, 1.2, 1.6]:
            g.turned(
                x,
                5.94,
                3.87,
                [(0.07, 0), (0.10, 0.09), (0.055, 0.25), (0.085, 0.50), (0.065, 0.61)],
                "marble_white",
                20,
            )
        block(0, 5.94, 4.48, 3.75, 0.25, 0.13, "marble_white")
    for x in [-4.86, 4.86]:
        for z in [0, 1.02, height - 0.28]:
            block(x, 0, z, 0.48, 10.3, 0.22, "stone_cream")
        for y in [-4.8, 0, 4.8]:
            block(x, y, 1.1, 0.30, 0.24, height - 1.1, "marble_white" if style != 2 else "wood")
        block(x, 0, 3.55, 0.34, 10.2, 0.17, "marble_white")
    for angle in [90, 270]:
        for x in [-2.8, 2.8]:
            for z in [1.43, 4.20]:
                rotated_geometry(lambda x=x, z=z: window(x, 5.07, z, style), angle)
    for x in [-3.3, 3.3]:
        block(x, 5.25, 3.69, 2.10, 0.70, 0.14, "wood")
    # A projecting trade sign, entirely geometric and not invented heraldry.
    g.rod((3.85, 5.15, 3.4), (3.85, 6.15, 3.4), 0.045, "dark_metal")
    block(3.85, 5.94, 2.71, 0.10, 0.76, 0.54, "wood")
    if style == 1:
        g.turned(3.92, 5.93, 2.78, [(0.15, 0), (0.20, 0.10), (0.17, 0.28)], "bronze", 20)
    # Full-height facades, with another carved belt and windows per storey.
    # The upper homes are exterior volumes; public galleries are separate.
    for floor in range(2, floors):
        for y in [-4.99, 4.99]:
            block(0, y, floor * 3.5, 10.25, 0.22, 0.18, "wood" if style == 2 else "marble_white")
        for angle in [0, 90, 180, 270]:
            for x in [-3.1, 3.1]:
                rotated_geometry(
                    lambda x=x, floor=floor: window(x, 5.07, floor * 3.5 + 1.35, style), angle
                )
    if style == 2:
        # Timber frame, diagonal braces and protruding upper sill distinguish
        # these narrow mercantile homes from imperial stone arcades.
        for y in [-5.06, 5.06]:
            for floor in range(floors):
                for x in [-4.6, 0, 4.6]:
                    block(x, y, floor * 3.5, 0.18, 0.15, 3.5, "wood")
                for side in [-1, 1]:
                    g.rod(
                        (side * 0.4, y, floor * 3.5 + 0.3),
                        (side * 4.3, y, (floor + 1) * 3.5 - 0.3),
                        0.09,
                        "wood",
                        8,
                    )


def curved_tile(x0, x1, y0, y1, height, material="roof_terracotta", along_x=True):
    """Closed barrel tile: curved width, stepped lap, substantial front lip."""
    points = []
    for side in [0, 1]:
        for row in range(2):
            for k in range(7):
                u = k / 6
                x = x0 + (x1 - x0) * (row if along_x else u)
                y = y0 + (y1 - y0) * (u if along_x else row)
                lift = 0.08 * math.sin(math.pi * u) + 0.025 + (0.04 if row == 1 else 0)
                points.append((x, y, height(x, y) + lift - side * 0.055))
    faces = []
    for offset in [0, 14]:
        for k in range(6):
            faces.append((offset + k, offset + k + 1, offset + k + 8, offset + k + 7))
    for row in [0, 7]:
        for k in range(6):
            a = row + k
            faces.append((a, a + 14, a + 15, a + 1))
    faces.extend([(0, 7, 21, 14), (6, 20, 27, 13)])
    g.solid(points, faces, material, 0.008)


def roof(width=11, depth=11, z=6.7, material="roof_terracotta", hip=False):
    block(0, 0, 3.62, 10, 10, 0.15, "wood")
    for side in [-1, 1]:
        for row in range(12):
            x0 = side * row * width / 24
            x1 = side * min(width / 2, (row + 1) * width / 24 + 0.07)
            for k in range(24):
                y0 = -depth / 2 + k * depth / 24
                curved_tile(
                    x0,
                    x1,
                    y0,
                    y0 + depth / 24 + 0.008,
                    lambda x, y: z + 2.8 * (1 - abs(x) / (width / 2)),
                    material,
                )
    for y in [-depth / 2, depth / 2]:
        g.prism(
            [(-width / 2, z), (0, z + 2.8), (width / 2, z)], y - 0.06, y + 0.06, "plaster_ochre"
        )
        for side in [-1, 1]:
            for j in range(12):
                x0 = side * j * width / 24
                x1 = side * (j + 1) * width / 24
                g.rod(
                    (x0, y, z + 2.8 * (1 - abs(x0) / (width / 2)) + 0.1),
                    (x1, y, z + 2.8 * (1 - abs(x1) / (width / 2)) + 0.1),
                    0.07,
                    material,
                    10,
                )
    for x in [-width / 2, width / 2]:
        block(x, 0, z - 0.17, 0.19, depth + 0.1, 0.25, "wood")
    for k in range(24):
        y = -depth / 2 + (k + 0.5) * depth / 24
        g.rod(
            (0, y - depth / 48, z + 2.9), (0, y + depth / 48 + 0.025, z + 2.9), 0.13, material, 16
        )
    block(3, -2, z + 0.3, 0.85, 0.9, 2.25, "stone_cream")
    block(3, -2, z + 2.5, 1.1, 1.15, 0.15, "marble_white")


def flat_roof(height=7):
    block(0, 0, 3.62, 10, 10, 0.15, "wood")
    first = len(g.VERTS)
    block(0, 0, 6.30, 10.55, 10.55, 0.20, "stone_cream")
    for x in [-5.1, 5.1]:
        block(x, 0, 6.50, 0.30, 10.5, 0.9, "stone_cream")
    for y in [-5.1, 5.1]:
        block(0, y, 6.50, 10.5, 0.30, 0.9, "stone_cream")
    for x in [-4, -2, 0, 2, 4]:
        for y in [-5.1, 5.1]:
            block(x, y, 7.40, 0.65, 0.60, 0.18, "marble_white")
    for x in [-5.1, 5.1]:
        for y in [-4, -2, 0, 2, 4]:
            block(x, y, 7.40, 0.60, 0.65, 0.18, "marble_white")
    for i in range(first, len(g.VERTS)):
        x, y, z = g.VERTS[i]
        g.VERTS[i] = (x, y, z + height - 6.3)


def interior_base():
    """Permanent interior floor and low walls remain legible during shell cutaway."""
    for i in range(40):
        x = -4.7 + (i + 0.5) * 9.4 / 40
        for j in range(4):
            block(x, -4.7 + (j + 0.5) * 2.35, 0.006, 9.4 / 40 - 0.008, 2.342, 0.024, "wood")
    # The open front maintains the exact 2.8 m clear entry, with no raised threshold.
    for x in [-4.56, 4.56]:
        block(x, 0, 0.03, 0.20, 9.32, 0.60, "stone_cream")
        block(x, 0, 0.63, 0.25, 9.32, 0.055, "wood")
    block(0, -4.56, 0.03, 9.32, 0.20, 0.60, "stone_cream")
    block(0, -4.56, 0.63, 9.32, 0.25, 0.055, "wood")
    for x in [-2.98, 2.98]:
        block(x, 4.56, 0.03, 3.16, 0.20, 0.60, "stone_cream")
        block(x, 4.56, 0.63, 3.16, 0.25, 0.055, "wood")


def city_fringe():
    """Continuous context ground joins the district to its surrounding city."""
    block(-104, 2, -0.30, 52, 220, 0.25, "cobble")
    block(-6, -87, -0.30, 144, 42, 0.25, "cobble")
    block(-6, 91, -0.30, 144, 42, 0.25, "cobble")


def furniture(kind=0):
    if kind == 1:
        for x in [-2.7, 2.7]:
            for y in [-1.7, 1.7]:
                table(x, y, width=2, depth=1.1)
                for yy in [y - 0.95, y + 0.95]:
                    w.bench(x, yy, 2.0)
                for dx in [-0.35, 0.35]:
                    g.turned(
                        x + dx, y, 0.97, [(0.09, 0), (0.11, 0.15), (0.08, 0.20)], "pottery", 16
                    )
        table(0, -3.95, width=4.8, depth=0.7)
        for x in [-3.7, -2.8, 2.8, 3.7]:
            barrel(x, -3.95)
    else:
        for y in [-2.7, 1.6]:
            table(-3.35, y, width=1.0, depth=2.2)
            for yy in [y - 0.7, y, y + 0.7]:
                jar(-3.35, yy, 0.96, 0.6)
        table(2.5, -3.3, width=3.0)
        for x in [1.5, 2.5, 3.5]:
            crate(x, -3.3, 0.96, 0.6)
        for yy in [-2, 0, 2.2]:
            barrel(3.75, yy)
        if kind == 2:
            for yy in [-2, 1]:
                g.turned(-2.3, yy, 1.05, [(0.55, 0), (0.55, 0.12)], "bronze", 32)
                for j in range(12):
                    a = j * math.tau / 12
                    block(
                        -2.3 + 0.57 * math.cos(a),
                        yy + 0.57 * math.sin(a),
                        1.02,
                        0.18,
                        0.18,
                        0.19,
                        "dark_metal",
                    )
            table(-2.3, -3.4, width=2.4)
    # Interior centre x=-1..1 remains unobstructed from the doorway to the rear.


def hall_body():
    # Thirty by twenty-four metres; crossed 4 m aisles run through all doors.
    for x in [-14.65, 14.65]:
        for y in [-10, -5, 0, 5, 10]:
            w.sculpted_column(x, y, 0, 6, 0.33)
    for x in [-10, -5, 5, 10]:
        for y in [-11.6, 11.6]:
            w.sculpted_column(x, y, 0, 6, 0.33)
    for y in [-11.8, 11.8]:
        for a, b in [(-15, -2.3), (2.3, 15)]:
            g.masonry(a, b, y, 0, 0.9, 0.38, 0.3, 1.0)
        block(0, y, 6, 30.6, 0.8, 0.48, "marble_white")
        w.carved_frieze(0, y + 0.4, 5.38, 29)
    for x in [-14.9, 14.9]:
        for cy in [-7.3, 7.3]:
            block(x, cy, 0, 0.38, 9.8, 0.9, "stone_cream")
        block(x, 0, 6, 0.8, 24, 0.48, "wood")
    for x in [-9, 9]:
        for y in [-6, 0, 6]:
            w.sculpted_column(x, y, 0, 6, 0.28)
    for x in [-14, -7, 0, 7, 14]:
        g.rod((x, -11.6, 6.4), (x, 0, 10.2), 0.14, "wood", 12)
        g.rod((x, 0, 10.2), (x, 11.6, 6.4), 0.14, "wood", 12)
    for x in [-14, 14]:
        for y in [-11, 11]:
            barrel(x, y, scale=0.9)


def hall_roof():
    # Fired blue-violet barrel tiles with actual relief at player distance.
    # Solid roof boards support the small closed tiles. Their continuous
    # underside also prevents thin, disconnected tile solids from producing
    # a perforated shadow representation. Clerestory ventilation stays open.
    def boards(y0, y1, height):
        points = [
            (x, y, height(x, y) - depth)
            for depth in [0.16, 0.04]
            for x, y in [(-15.65, y0), (15.65, y0), (15.65, y1), (-15.65, y1)]
        ]
        g.solid(
            points,
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
            "wood",
            bevel=0,
        )

    for side in [-1, 1]:
        boards(side * 1.5, side * 12.37, lambda x, y: 10 - abs(y) * 0.28)
        boards(0, side * 1.95, lambda x, y: 11.15 - abs(y) * 0.24)
        for row in range(18):
            y0 = side * (1.5 + row * 0.6)
            y1 = side * (1.5 + (row + 1) * 0.6 + 0.07)
            for k in range(65):
                x0 = -15.6 + k * 0.48
                curved_tile(
                    x0, x0 + 0.487, y0, y1, lambda x, y: 10 - abs(y) * 0.28, "roof_blue", False
                )
        block(0, side * 12.35, 6.39, 31.5, 0.22, 0.25, "wood")
    for y in [-1.5, 1.5]:
        block(0, y, 9.6, 31, 0.12, 1.10, "wood")
        for x in range(-15, 16):
            block(x, y, 9.66, 0.065, 0.17, 1, "bronze")
    for x in [-15.65, 15.65]:
        for side in [-1, 1]:
            g.rod((x, side * 1.5, 9.7), (x, side * 12.35, 6.66), 0.09, "roof_blue", 12)
    for k in range(65):
        x = -15.6 + k * 0.48
        for side in [-1, 1]:
            curved_tile(
                x, x + 0.49, 0, side * 1.95, lambda a, b: 11.15 - abs(b) * 0.24, "roof_blue", False
            )
        g.rod((x, 0, 11.26), (x + 0.51, 0, 11.26), 0.14, "roof_blue", 16)
    for x in [-15.6, 15.6]:
        for y in [-12.3, 12.3]:
            g.turned(x, y, 6.5, [(0.15, 0), (0.12, 0.45), (0.02, 0.9)], "bronze", 20)


def sector(r0, r1, a0, a1, z, h, material):
    steps = max(1, round(abs(a1 - a0) * 14))
    pts = []
    for zz in [z, z + h]:
        for r in [r0, r1]:
            pts += [
                (
                    r * math.cos(a0 + (a1 - a0) * j / steps),
                    r * math.sin(a0 + (a1 - a0) * j / steps),
                    zz,
                )
                for j in range(steps + 1)
            ]
    n = steps + 1
    faces = []
    for j in range(steps):
        faces += [
            (j, j + 1, n + j + 1, n + j),
            (2 * n + j, 3 * n + j, 3 * n + j + 1, 2 * n + j + 1),
            (j, 2 * n + j, 2 * n + j + 1, j + 1),
            (n + j, n + j + 1, 3 * n + j + 1, 3 * n + j),
        ]
    faces += [(0, n, 3 * n, 2 * n), (n - 1, 2 * n - 1, 4 * n - 1, 3 * n - 1)]
    g.solid(pts, faces, material, 0.025)


def illu_body():
    g.turned(0, 0, -0.16, [(16.8, 0), (16.8, 0.16)], "stone_cream", 96)
    g.turned(0, 0, 0.004, [(9.2, 0), (9.2, 0.025)], "sand", 96)
    # Four broad radial entrances remain clear; tier stairs are genuine .15 m rises.
    for quadrant in range(4):
        a0 = quadrant * math.pi / 2 + 0.20
        a1 = (quadrant + 1) * math.pi / 2 - 0.20
        for row in range(4):
            r = 10.2 + row * 1.36
            sector(r, r + 1.31, a0, a1, 0, 0.42 * (row + 1), "stone_cream")
            sector(r + 0.65, r + 1.02, a0, a1, 0.42 * (row + 1), 0.24, "wood")
            sector(r + 0.67, r + 1.03, a0, a1, 0.42 * (row + 1) + 0.24, 0.04, "burgundy")
        sector(16.2, 16.8, a0, a1, 0, 4.1, "stone_cream")
        sector(16.0, 17.0, a0, a1, 4.1, 0.30, "marble_white")
        for j in range(6):
            a = a0 + (a1 - a0) * j / 5
            x, y = 16.15 * math.cos(a), 16.15 * math.sin(a)
            block(x, y, 0, 0.50, 0.50, 4.4, "marble_white")
    for side in [-1, 1]:
        for j in range(12):
            block(
                side * (10.25 + (j + 0.5) * 0.42), 0, 0, 0.43, 3.05, (j + 1) * 0.14, "stone_cream"
            )
    for a in [math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4]:
        x, y = 13 * math.cos(a), 13 * math.sin(a)
        block(x, y, 1.7, 0.58, 0.58, 5.4, "dark_metal")
        g.turned(
            x,
            y,
            6.6,
            [(0.55, 0), (0.68, 0.12), (0.48, 0.55), (0.28, 0.9), (0.02, 1.16)],
            "bronze",
            32,
        )
        for j in range(8):
            ang = j * math.tau / 8
            g.rod(
                (x, y, 6.9),
                (x + 0.9 * math.cos(ang), y + 0.9 * math.sin(ang), 6.9),
                0.05,
                "bronze",
                10,
            )
    # Marked combat circles are bronze inlays, flat to the accessible sand.
    for r in [3, 7.8]:
        sector(r, r + 0.055, 0, math.tau, 0.035, 0.01, "bronze")


def illu_canopy():
    for q in range(4):
        a0 = q * math.pi / 2 + 0.27
        a1 = (q + 1) * math.pi / 2 - 0.27
        for row in range(6):
            r0 = 13.7 + row * 0.63
            r1 = r0 + 0.66
            for tile in range(20):
                aa = a0 + (a1 - a0) * tile / 20
                bb = a0 + (a1 - a0) * (tile + 1) / 20 - 0.003
                sector(r0, r1, aa, bb, 4.45 + (5 - row) * 0.085, 0.18, "burgundy")
        for j in range(9):
            a = a0 + (a1 - a0) * j / 8
            g.rod(
                (13.7 * math.cos(a), 13.7 * math.sin(a), 5.08),
                (17.5 * math.cos(a), 17.5 * math.sin(a), 4.65),
                0.065,
                "bronze",
                10,
            )


def gate():
    for x in [-5.25, 5.25]:
        for y in [-1.9, 1.9]:
            block(x, y, 0, 3.1, 3.2, 8.5, "stone_cream")
            block(x, y, 8.5, 3.6, 3.7, 0.35, "marble_white")
        for y in [-1.9, 1.9]:
            for dx in [-1, 0, 1]:
                block(x + dx, y, 8.85, 0.52, 3.7, 0.85, "stone_cream")
    block(0, 0, 6.0, 7.5, 3.4, 2.0, "stone_cream")
    g.arc(0, 0, 3.6, 3.5, 0.48, 3.6)
    w.carved_frieze(0, 1.85, 7.1, 7.4)
    for x in [-3.8, 3.8]:
        block(x, 0, 0, 0.52, 3.7, 6.0, "marble_white")


def fountain():
    g.turned(
        0,
        0,
        0,
        [(2.2, 0), (2.2, 0.18), (2.1, 0.30), (2.1, 0.54), (1.82, 0.54), (1.82, 0.22)],
        "stone_cream",
        64,
    )
    g.turned(
        0,
        0,
        0.20,
        [(0.60, 0), (0.50, 0.20), (0.32, 1.55), (0.60, 1.75), (0.55, 1.9)],
        "marble_white",
        48,
    )
    g.turned(0, 0, 2.05, [(0.10, 0), (0.24, 0.13), (0.18, 0.34), (0.03, 0.46)], "bronze", 32)


def shaft():
    g.turned(0, 0, 0, [(3.0, 0), (3.0, 0.45), (2.5, 0.45), (2.5, 0.05)], "stone_cream", 64)
    # Secured service shaft, visible mechanism instead of an unguarded hole.
    for x in [-2, -1, 0, 1, 2]:
        block(x, 0, 0.09, 0.10, 4.8, 0.12, "dark_metal")
    for y in [-2, -1, 0, 1, 2]:
        block(0, y, 0.09, 4.8, 0.10, 0.12, "dark_metal")
    for x in [-2.6, 2.6]:
        block(x, 0, 0.45, 0.28, 0.28, 4.2, "wood")
    block(0, 0, 4.35, 5.8, 0.35, 0.38, "wood")
    g.rod((-2.6, 0, 4.2), (0, 0, 2.9), 0.06, "dark_metal")
    g.rod((2.6, 0, 4.2), (0, 0, 2.9), 0.06, "dark_metal")
    g.turned(0, 0, 0.25, [(0.9, 0), (0.9, 0.1), (0.78, 0.9), (0.78, 1)], "wood", 24)


def cart():
    """A loaded handcart, with actual hubs, spokes, handles and planked sides."""
    for y in [-0.73, 0.73]:
        for j in range(10):
            a = j * math.tau / 10
            b = (j + 1) * math.tau / 10
            g.rod(
                (0.55 * math.cos(a), y, 0.58 + 0.55 * math.sin(a)),
                (0.55 * math.cos(b), y, 0.58 + 0.55 * math.sin(b)),
                0.065,
                "wood",
                10,
            )
            g.rod(
                (0, y, 0.58), (0.52 * math.cos(a), y, 0.58 + 0.52 * math.sin(a)), 0.035, "wood", 8
            )
        g.rod((0, y - 0.14, 0.58), (0, y + 0.14, 0.58), 0.12, "dark_metal", 20)
    g.rod((0, -0.9, 0.58), (0, 0.9, 0.58), 0.07, "dark_metal", 12)
    for j in range(8):
        block(-1.1 + (j + 0.5) * 0.275, 0, 0.85, 0.26, 1.4, 0.11, "wood")
    for z in [1.02, 1.24, 1.46]:
        for y in [-0.68, 0.68]:
            block(0, y, z, 2.3, 0.07, 0.17, "wood")
        block(1.09, 0, z, 0.07, 1.35, 0.17, "wood")
    for y in [-0.52, 0.52]:
        g.rod((-1.1, y, 0.88), (-2.8, y, 1.0), 0.065, "wood", 10)
    crate(0.45, 0, 0.98, 0.75)
    jar(-0.45, 0.22, 0.98, 0.65)
    barrel(-0.48, -0.33, 0.98, 0.55)


def planter():
    g.turned(
        0,
        0,
        0,
        [
            (0.75, 0),
            (0.92, 0.15),
            (0.84, 0.8),
            (1.00, 0.9),
            (1.00, 1.04),
            (0.77, 1.04),
            (0.70, 0.85),
        ],
        "pottery",
        48,
    )
    g.turned(0, 0, 0.83, [(0.73, 0), (0.73, 0.03)], "mortar", 32)
    foliage.noble_tree(g, z=0.86, height=4.1, crown_radius=1.15, material="foliage")


def trade_sign(kind=0):
    g.rod((0, 0, 2.9), (0, 1, 2.9), 0.043, "dark_metal", 10)
    for y in [0.35, 0.85]:
        g.rod((0, y, 2.9), (0, y, 2.55), 0.018, "bronze", 8)
    block(0, 0.60, 1.92, 0.10, 1.12, 0.70, "wood")
    # Sculpted trade motifs on both sides: potter's vessel, inn cup, textile roll.
    for side in [-1, 1]:
        x = side * 0.09
        if kind == 0:
            g.turned(
                x, 0.60, 2.00, [(0.13, 0), (0.22, 0.15), (0.12, 0.38), (0.10, 0.49)], "bronze", 24
            )
        elif kind == 1:
            g.turned(
                x,
                0.60,
                2.00,
                [(0.20, 0), (0.08, 0.11), (0.08, 0.25), (0.23, 0.35), (0.25, 0.50)],
                "bronze",
                24,
            )
        else:
            block(x, 0.60, 2.06, 0.05, 0.70, 0.37, "linen")
            for y in [0.25, 0.95]:
                g.rod((x, y, 2.03), (x, y, 2.47), 0.065, "bronze", 12)


def party_link():
    # Narrow sealed seam between terraced houses; no public route enters it.
    block(0, 0, 0, 1.10, 10.0, 1.1, "stone_cream")
    block(0, 0, 1.1, 1.10, 10.0, 5.2, "plaster_ochre")
    for y in [-5, 5]:
        block(0, y, 1.0, 1.12, 0.15, 0.17, "wood")
        block(0, y, 6.15, 1.20, 0.23, 0.22, "marble_white")
    block(0, 0, 6.30, 1.25, 10.4, 0.15, "roof_terracotta")


def porch():
    for x in [-2.5, 2.5]:
        block(x, 0, 0, 0.3, 0.3, 3.4, "wood")
        block(x, 0, 3.2, 0.52, 0.46, 0.18, "bronze")
    block(0, 0, 3.4, 5.5, 0.40, 0.25, "wood")
    g.rod((-2.5, 0, 2.55), (-1.6, 0, 3.4), 0.075, "wood", 12)
    g.rod((2.5, 0, 2.55), (1.6, 0, 3.4), 0.075, "wood", 12)


def market_bay(key, x, y, kind=0, yaw=0):
    a = math.radians(yaw)

    def point(dx, dy):
        return x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a)

    place(key + "-stock", "mp-stock-" + str(kind), x, y, yaw=yaw, role="furniture")
    place(key + "-canopy", "mp-awning-" + str(kind % 2), x, y, yaw=yaw, role="textile")
    px, py = point(-1, -2.05)
    place(
        key + "-reserve",
        "mp-crates" if kind % 2 == 0 else "mp-barrels",
        px,
        py,
        yaw=yaw,
        role="furniture",
    )


def delivery(key, x, y, yaw=0):
    place(key + "-cart", "mp-cart", x, y, yaw=yaw, role="furniture")
    place(key + "-barrels", "mp-barrels", x + 2.0, y + 1.8, yaw=25 + yaw, role="furniture")
    place(key + "-crates", "mp-crates", x + 2.2, y - 0.5, yaw=yaw, role="furniture")


PROXY_SPECS = {}


def physical_box(x, y, z, width, depth, height):
    # Architectural volumes are independent of the dressed visual geometry.
    a, b, c, d = x - width / 2, x + width / 2, y - depth / 2, y + depth / 2
    g.solid(
        [
            (a, c, z),
            (b, c, z),
            (b, d, z),
            (a, d, z),
            (a, c, z + height),
            (b, c, z + height),
            (b, d, z + height),
            (a, d, z + height),
        ],
        [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)],
        "stone_cream",
        bevel=0,
    )


def warp_surface(fn):
    first = len(g.VERTS)
    fn()
    for i in range(first, len(g.VERTS)):
        x, north, z = g.VERTS[i]
        g.VERTS[i] = (x, north, z + layout.ground_height(x, -north))


def district_ground():
    """A shared 1.5m lattice, exposed bottom and continuous perimeter returns."""
    field = layout.heightfield()
    ox, oy = field["origin"]
    sx, sy = field["spacing"]
    cols = field["width"]
    points = []
    faces = []
    shared = {}
    edges = {}

    def vertex(x, y, z):
        key = (round(x, 5), round(y, 5), round(z, 6))
        if key not in shared:
            shared[key] = len(points)
            points.append(key)
        return shared[key]

    for row in range(field["height"] - 1):
        for col in range(cols - 1):
            x, y = ox + col * sx, oy + row * sy
            # Extend urban land at the left/bottom; never cover the river.
            cx, cy = x + sx / 2, y + sy / 2
            upper = -92 - (cx + 128) * 0.1 if cx < -8 else -104 + (cx + 8) * 40 / 134
            if cx > 128 or cy < upper:
                continue
            xy = [(x, y), (x + sx, y), (x + sx, y + sy), (x, y + sy)]
            indices = [vertex(a, b, layout.ground_height(a, b)) for a, b in xy]
            faces.extend(
                [(indices[0], indices[1], indices[2]), (indices[0], indices[2], indices[3])]
            )
            for a, b in zip(indices, indices[1:] + indices[:1]):
                key = tuple(sorted((a, b)))
                edges[key] = None if key in edges else (a, b)
    bottom = -3.8
    for edge in edges.values():
        if edge is None:
            continue
        a, b = edge
        p, q = points[a], points[b]
        c, d = vertex(q[0], q[1], bottom), vertex(p[0], p[1], bottom)
        faces.append((a, d, c, b))
    # The terrain is a volume, not a floating top sheet. Its underside follows
    # the same triangulation with a fixed bottom beneath both shores.
    top_faces = list(faces[: sum(len(f) == 3 for f in faces)])
    for face in top_faces:
        faces.append(tuple(vertex(points[i][0], points[i][1], bottom) for i in reversed(face)))
    first_face = len(g.FACE_SMOOTH)
    g.solid(points, faces, "cobble", bevel=0)
    # Interpolated terrain normals suppress visible lattice facets. Collision
    # still uses the same authored top triangles and level foundation cores.
    for i, face in enumerate(faces):
        if len(face) == 3 and all(points[v][2] > bottom + 0.01 for v in face):
            g.FACE_SMOOTH[first_face + i] = True


def road_surface(road):
    for a, b in zip(road["points"], road["points"][1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        nx, ny = -dy / length, dx / length
        count = max(1, math.ceil(length / 0.9))
        width = road["width"]
        for row in range(count):
            for col in range(max(1, round(width / 0.85))):
                u = (row + 0.5) / count
                v = (col + 0.5) * width / max(1, round(width / 0.85)) - width / 2
                x, y = a[0] + dx * u + nx * v, a[1] + dy * u + ny * v
                h = 0.035 if col not in (0, round(width / 0.85) - 1) else 0.075
                # Substantial chamfered paving stones; the cart route remains
                # the continuous terrain beneath these shallow dressed tops.
                first = len(g.VERTS)
                block(
                    0,
                    0,
                    -0.03,
                    width / max(1, round(width / 0.85)) - 0.03,
                    length / count - 0.035,
                    h,
                    "stone_cream" if col in (0, round(width / 0.85) - 1) else "cobble",
                )
                angle = math.atan2(dy, dx) - math.pi / 2
                for i in range(first, len(g.VERTS)):
                    xx, north, z = g.VERTS[i]
                    yy = -north
                    px = x + xx * math.cos(angle) - yy * math.sin(angle)
                    py = y + xx * math.sin(angle) + yy * math.cos(angle)
                    g.VERTS[i] = (px, -py, z + layout.ground_height(px, py))


def public_paver_positions():
    """A shared stone phase over real public courts, clear of planted centres.

    Carriageways keep their existing dressed stones. The apron fills the
    remaining public ground without moving a building or flattening relief.
    """
    plots = [(p, math.cos(math.radians(p["yaw"])), math.sin(math.radians(p["yaw"])))
             for p in layout.PLOTS]
    for row in range(220):
        y = -80 + (row + 0.5) * 0.9
        offset = 0.45 if row % 2 else 0
        for col in range(210):
            x = -118 + (col + 0.5) * 0.9 + offset
            area = next((a for a in PUBLIC_PAVING_AREAS
                         if a[0] + 0.45 <= x <= a[2] - 0.45
                         and a[1] + 0.45 <= y <= a[3] - 0.45), None)
            if area is None:
                continue
            if math.dist((x, y), layout.ILLU) < 18.2 or math.dist((x, y), layout.SHAFT) < 18.7:
                continue
            if any(layout.distance_to_segment(x, y, a, b) < road["width"] / 2 + 0.55
                   for road in layout.ROADS for a, b in zip(road["points"], road["points"][1:])):
                continue
            occupied = False
            for p, cos, sin in plots:
                dx, dy = x - p["position"][0], y - p["position"][1]
                # Actual map yaw is negative, matching build_level.map_rotation.
                u, v = dx * cos - dy * sin, dx * sin + dy * cos
                if abs(u) < p["width"] / 2 + 0.8 and abs(v) < p["depth"] / 2 + 0.8:
                    occupied = True
                    break
            if not occupied:
                border = min(x - area[0], area[2] - x, y - area[1], area[3] - y) < 1.25
                yield x, y, border


def triangulated_ground_height(x, y):
    """Exact planes exported by district_ground's 1.5m cell diagonals."""
    spacing = 1.5
    x0 = -142 + math.floor((x + 142) / spacing) * spacing
    y0 = -120 + math.floor((y + 120) / spacing) * spacing
    u, v = (x - x0) / spacing, (y - y0) / spacing
    z00, z10 = layout.ground_height(x0, y0), layout.ground_height(x0 + spacing, y0)
    z11, z01 = layout.ground_height(x0 + spacing, y0 + spacing), layout.ground_height(x0, y0 + spacing)
    if v <= u:
        return z00 + u * (z10 - z00) + v * (z11 - z10)
    return z00 + u * (z11 - z01) + v * (z01 - z00)


def clip_surface_polygon(polygon, triangle):
    """Convex XY clipping; preserves every terrain and stone bevel boundary."""
    for a, b in zip(triangle, triangle[1:] + triangle[:1]):
        output = []
        if not polygon:
            break

        def side(p):
            return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])  # noqa: B023

        previous = polygon[-1]
        pd = side(previous)
        for point in polygon:
            distance = side(point)
            if (distance >= -1e-9) != (pd >= -1e-9):
                t = pd / (pd - distance)
                output.append(tuple(previous[k] + t * (point[k] - previous[k]) for k in (0, 1)))
            if distance >= -1e-9:
                output.append(point)
            previous, pd = point, distance
        polygon = output
    return polygon


def conforming_paving_stone(x, y):
    """One closed stone with a real chamfer and an exactly conforming top.

    Its planar top and bevel regions are intersected with every terrain cell
    triangle they cover. Both the grid lines and diagonals become real mesh
    edges, so no analytic-height chord can cut through the exported ground.
    """
    half, chamfer = 0.441, 0.015
    outline = [(x - half, y - half), (x + half, y - half),
               (x + half, y + half), (x - half, y + half)]
    inner = [(px + (chamfer if px < x else -chamfer),
              py + (chamfer if py < y else -chamfer)) for px, py in outline]
    regions = [inner[:3], [inner[0], inner[2], inner[3]]]
    for i in range(4):
        j = (i + 1) % 4
        regions += [[outline[i], outline[j], inner[j]], [outline[i], inner[j], inner[i]]]
    cells = []
    for row in range(math.floor((y - half + 120) / 1.5), math.floor((y + half + 120) / 1.5) + 1):
        for col in range(math.floor((x - half + 142) / 1.5), math.floor((x + half + 142) / 1.5) + 1):
            a, b = -142 + col * 1.5, -120 + row * 1.5
            cells += [[(a, b), (a + 1.5, b), (a + 1.5, b + 1.5)],
                      [(a, b), (a + 1.5, b + 1.5), (a, b + 1.5)]]
    xy, shared, top_faces = [], {}, []
    for region in regions:
        for cell in cells:
            polygon = clip_surface_polygon(list(region), cell)
            clean = []
            for point in polygon:
                point = tuple(round(value, 7) for value in point)
                if not clean or point != clean[-1]:
                    clean.append(point)
            if len(clean) > 1 and clean[0] == clean[-1]:
                clean.pop()
            if len(clean) < 3:
                continue
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(clean, clean[1:] + clean[:1]))
            if area < 1e-9:
                continue
            face = []
            for point in clean:
                if point not in shared:
                    shared[point] = len(xy)
                    xy.append(point)
                face.append(shared[point])
            top_faces.append(tuple(face))
    points = []
    for px, py in xy:
        lift = .012 * max(0, min(1, (half - abs(px - x)) / chamfer, (half - abs(py - y)) / chamfer))
        points.append((px, py, triangulated_ground_height(px, py) + lift))
    n = len(points)
    points += [(px, py, triangulated_ground_height(px, py) - .07) for px, py in xy]
    faces = list(top_faces) + [tuple(i + n for i in reversed(face)) for face in top_faces]
    edges = {}
    for face in top_faces:
        for a, b in zip(face, face[1:] + face[:1]):
            key = tuple(sorted((a, b)))
            edges[key] = None if key in edges else (a, b)
    for edge in edges.values():
        if edge is not None:
            a, b = edge
            faces.append((a, a + n, b + n, b))
    return points, faces, len(top_faces)


def public_paving():
    """Closed stones conform to the actual terrain, including every bevel."""
    for x, y, border in public_paver_positions():
        points, faces, _ = conforming_paving_stone(x, y)
        g.solid(points, faces, "stone_cream" if border else "cobble", bevel=0)


def street_finishing():
    """Sixteen planted market/seating groups on surveyed open side areas."""
    for i, (x, y) in enumerate(STREET_FINISHING_GROUPS):
        key = f"street-finishing-{i}"
        place_on_public_paving(key + "-tree", "mp-planter", x, y, role="foliage")["motion"] = "foliage"
        if i % 3 == 0:
            place_on_public_paving(key + "-seating", "mp-tavern-table", x + 3.2, y, role="furniture")
        else:
            place_on_public_paving(key + "-stock", f"mp-stock-{i % 4}", x + 3.2, y, role="furniture")
            place_on_public_paving(key + "-canopy", f"mp-awning-{i % 2}", x + 3.2, y, role="textile")


def shop_physical(floors):
    height = floors * 3.5
    for x in [-3.25, 3.25]:
        physical_box(x, 4.86, 0, 3.5, 0.32, height)
    physical_box(0, 4.86, 3.1, 3.02, 0.32, height - 3.1)
    physical_box(0, -4.86, 0, 10, 0.32, height)
    for x in [-4.86, 4.86]:
        physical_box(x, 0, 0, 0.32, 10, height)


def shop_roof(style, floors, physical=False):
    height = floors * 3.5
    if physical:
        physical_box(0, 0, 3.62, 10, 10, 0.15)
        if style == 2:
            physical_box(0, 0, height, 10.55, 10.55, 0.2)
            for x in [-5.1, 5.1]:
                physical_box(x, 0, height + 0.2, 0.3, 10.5, 0.9)
            for y in [-5.1, 5.1]:
                physical_box(0, y, height + 0.2, 10.5, 0.3, 0.9)
        else:
            pts = [
                (-5.5, -5.5, height),
                (5.5, -5.5, height),
                (0, -5.5, height + 2.8),
                (-5.5, 5.5, height),
                (5.5, 5.5, height),
                (0, 5.5, height + 2.8),
            ]
            g.solid(pts, [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (0, 3, 5, 2), (1, 2, 5, 4)], bevel=0)
    else:
        if style == 2:
            flat_roof(height)
        else:
            roof(z=height)
            block(0, 0, 3.62, 10, 10, 0.15, "wood")


def hall_physical():
    for x in [-14.65, 14.65]:
        for y in [-10, -5, 0, 5, 10]:
            physical_box(x, y, 0, 0.8, 0.8, 6.5)
    for x in [-10, -5, 5, 10]:
        for y in [-11.6, 11.6]:
            physical_box(x, y, 0, 0.8, 0.8, 6.5)
    for x in [-9, 9]:
        for y in [-6, 0, 6]:
            physical_box(x, y, 0, 0.7, 0.7, 6.5)
    for y in [-11.8, 11.8]:
        for x in [-8.65, 8.65]:
            physical_box(x, y, 0, 12.7, 0.38, 0.9)
        physical_box(0, y, 6, 30.6, 0.8, 0.48)
    for x in [-14.9, 14.9]:
        for y in [-7.3, 7.3]:
            physical_box(x, y, 0, 0.38, 9.8, 0.9)
    physical_box(0, 0, -0.08, 30, 24, 0.08)


def illu_physical():
    # Closed podium, real radial openings and the identical tread heights.
    g.turned(0, 0, -0.16, [(16.8, 0), (16.8, 0.16)], "stone_cream", 48)
    for q in range(4):
        a0 = q * math.pi / 2 + 0.2
        a1 = (q + 1) * math.pi / 2 - 0.2
        for row in range(4):
            r = 10.2 + row * 1.36
            sector(r, r + 1.31, a0, a1, 0, 0.42 * (row + 1), "stone_cream")
        sector(16.2, 16.8, a0, a1, 0, 4.4, "stone_cream")
    for side in [-1, 1]:
        for j in range(12):
            physical_box(side * (10.25 + (j + 0.5) * 0.42), 0, 0, 0.43, 3.05, (j + 1) * 0.14)


def gallery(physical=False):
    box = physical_box if physical else block
    # A public market gallery, reached by a broad 20-tread physical stair.
    box(0, 3, -0.15, 12, 6, 0.15)
    box(0, 3, 3.38, 12, 6, 0.22)
    for x in [-5.5, 5.5]:
        for y in [0.5, 5.5]:
            box(x, y, 0, 0.45, 0.45, 3.6)
    for j in range(20):
        box(0, -8 + (j + 0.5) * 0.4, 0, 4, 0.4, (j + 1) * 0.18)
    for x in [-5.8, 5.8]:
        box(x, 3, 3.6, 0.25, 6, 1.1)
    box(0, 5.8, 3.6, 12, 0.25, 1.1)
    if physical:
        physical_box(0, 4, 3.6, 2, 1.1, 1.1)
        for x in [-4, -2, 2, 4]:
            physical_box(x, 4.3, 3.6, 1.8, 0.55, 0.65)
    else:
        first = len(g.VERTS)
        for x in [-4, -2, 2, 4]:
            w.bench(x, 4.3, 1.8)
        # Furniture on the elevated balcony is raised along with its deck.
        table(0, 4, 0, width=2)
        for i in range(first, len(g.VERTS)):
            x, y, z = g.VERTS[i]
            g.VERTS[i] = (x, y, z + 3.6)


def gallery_canopy(physical=False):
    for x in [-5.5, 5.5]:
        for y in [0.5, 5.5]:
            if physical:
                physical_box(x, y, 3.6, 0.55, 0.55, 3)
            else:
                w.sculpted_column(x, y, 3.6, 3, 0.22)
    if physical:
        physical_box(0, 3, 6.6, 12.5, 6.5, 0.22)
    else:
        block(0, 3, 6.6, 12.5, 6.5, 0.22, "wood")
        for j in range(19):
            x = -6 + (j + 0.5) * 12 / 19
            curved_tile(
                x,
                x + 0.65,
                -0.4,
                6.4,
                lambda a, b: 6.86 + 0.45 * math.sin(math.pi * b / 6.4),
                "burgundy",
            )


def shaft_garden():
    # A ring of paths, planted quadrants and an ornamented central ouvrage.
    for q in range(4):
        a0 = q * math.pi / 2 + 0.19
        a1 = (q + 1) * math.pi / 2 - 0.19
        sector(8, 15.5, a0, a1, -0.12, 0.18, "foliage")
        for r in [8, 15.6]:
            sector(r, r + 0.35, a0, a1, 0, 0.18, "stone_cream")
        a = (a0 + a1) / 2
        foliage.cypress(
            g,
            x=12 * math.cos(a),
            y=12 * math.sin(a),
            height=6.0,
            radius=0.8,
            material="foliage",
            seed=70 + q,
        )
    g.turned(0, 0, 0, [(4.2, 0), (4.2, 0.22), (3.8, 0.22), (3.8, 0.45)], "stone_cream", 48)
    for x in [-2.6, 2.6]:
        for y in [-2.6, 2.6]:
            w.sculpted_column(x, y, 0.45, 5.7, 0.28)
    for y in [-2.8, 2.8]:
        w.carved_frieze(0, y, 5.45, 5.7)
    g.turned(0, 0, 5.95, [(3.5, 0), (3.5, 0.35), (2.7, 0.35), (2.7, 0.65)], "marble_white", 48)
    g.turned(
        0, 0, 6.6, [(2.45, 0), (2.3, 0.25), (2.3, 5.4), (2.6, 5.4), (2.6, 5.75)], "stone_cream", 48
    )
    for z in [8.2, 11.0]:
        for angle in range(0, 360, 60):
            a = math.radians(angle)
            x, y = 2.35 * math.cos(a), 2.35 * math.sin(a)
            block(x, y, z, 0.55, 0.45, 1.3, "dark_metal")
    g.turned(
        0,
        0,
        12.35,
        [(2.6, 0), (2.7, 0.3), (2.15, 0.7), (1.5, 1.6), (0.45, 2.6), (0.04, 3.2)],
        "bronze",
        48,
    )
    shaft()


def quay_wall():
    points = [(-128, -92), (-8, -104), (126, -64), (128, 148)]
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = max(1, math.ceil(math.hypot(dx, dy) / 3))
        for j in range(n):
            x, y = a[0] + dx * (j + 0.5) / n, a[1] + dy * (j + 0.5) / n
            if x > 115 and -68 < y < -52:
                continue
            z = layout.ground_height(x, y)
            first = len(g.VERTS)
            block(0, 0, -3.5, math.hypot(dx, dy) / n + 0.06, 0.85, z + 3.65, "stone_cream")
            block(0, 0, z + 0.15, math.hypot(dx, dy) / n + 0.16, 1.15, 0.18, "marble_white")
            angle = math.atan2(dy, dx)
            for i in range(first, len(g.VERTS)):
                xx, yy, zz = g.VERTS[i]
                yy = -yy
                g.VERTS[i] = (
                    x + xx * math.cos(angle) - yy * math.sin(angle),
                    -(y + xx * math.sin(angle) + yy * math.cos(angle)),
                    zz,
                )


def city_context_land():
    # Continuous ground beneath neighbouring city silhouettes. The river is
    # confined to the upper/right shore; no water surrounds Downtown/Arenarea.
    points = [(-650, -55), (-142, -106), (-142, 175), (128, 175), (128, 650), (-650, 650)]
    top = [(x, y, layout.ground_height(x, y) - 0.08) for x, y in points]
    bottom = [(x, y, -3.8) for x, y in points]
    n = len(points)
    g.solid(
        bottom + top,
        [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
        + [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)],
        "cobble",
        bevel=0,
    )


def emit(out, materials, name, fn, physical=None):
    if physical is not None:
        PROXY_SPECS[name] = physical
    if name in REUSE:
        g.PIECES.append(dict(REUSE[name]))
        return
    if name == "mp-furnishing-foot-supports":
        export_furnishing_support_piece(name, fn, out, materials)
    else:
        g.export_piece(name, fn, out, materials, clean_degenerate=True)


def place(
    name,
    mesh,
    x,
    y,
    z=0,
    yaw=0,
    role="architecture",
    roof=False,
    occluder=None,
    absolute=False,
    scale=None,
):
    position = [x, y, z] if absolute else layout.point(x, y, z)
    if name in layout.ACCESS_DETAIL_POSITIONS:
        position = layout.point(*layout.ACCESS_DETAIL_POSITIONS[name])
    obj = {
        "id": name,
        "meshId": mesh,
        "position": position,
        "yaw": yaw,
        "role": role,
        "collision": mesh in PROXY_SPECS,
    }
    if scale is not None:
        obj["scale"] = scale
    if occluder is not None:
        obj["occluder"] = occluder
    if role == "textile":
        obj["motion"] = "cloth"
    OBJECTS.append(obj)
    if roof:
        ROOFS.append(name)
    return obj


def place_on_public_paving(name, mesh, x, y, role):
    """Seat the new court furniture on the same exact surface as its stones."""
    return place(name, mesh, x, y, round(triangulated_ground_height(x, y) + .012, 6),
                 role=role, absolute=True, occluder=False)


def align_paved_furnishing():
    """Existing side stalls, pots and lamps use the same surveyed support.

    Only furniture touching the new stone footprint is affected. House
    foundations, gameplay positions and every walk point keep their contract.
    """
    stones = {(round(x, 4), round(y, 4)) for x, y, _ in public_paver_positions()}

    def covered(x, y):
        row = round((y + 80) / .9 - .5)
        for rr in [row - 1, row, row + 1]:
            py = -80 + (rr + .5) * .9
            offset = .45 if rr % 2 else 0
            col = round((x + 118 - offset) / .9 - .5)
            for cc in [col - 1, col, col + 1]:
                px = -118 + (cc + .5) * .9 + offset
                if (abs(x - px) <= .441 and abs(y - py) <= .441
                        and (round(px, 4), round(py, 4)) in stones):
                    return True
        return False

    moved = {}
    for obj in OBJECTS:
        if obj["role"] not in ["furniture", "foliage", "textile"]:
            continue
        x, y, z = obj["position"]
        if not any(covered(x + dx, y + dy)
                   for dx, dy in [(0, 0), (-.25, 0), (.25, 0), (0, -.25), (0, .25)]):
            continue
        support = round(triangulated_ground_height(x, y) + .012, 6)
        obj["position"][2] = support
        moved[obj["id"]] = support - z
    for light in LIGHTS:
        if light.get("supportId") in moved:
            light["position"][2] += moved[light["supportId"]]
    return moved


def fit_furnishing_feet():
    """Keep roofs/tables level and seat every original foot on surveyed floors.

    The survey is text source, not a runtime dependency on preceding exports.
    It records the upper envelope of actual floor triangles clipped to each
    original pole/leg/base footprint, including terrain and paver boundaries.
    """
    survey = json.loads(Path(__file__).with_name("martpart_furnishing_supports.json")
                        .read_text(encoding="utf-8"))
    for mesh_id, checksum in survey["unchangedFloorMeshes"].items():
        if mesh_id in REUSE:
            assert REUSE[mesh_id]["sha256"] == checksum, ("Resurvey changed furnishing floor", mesh_id)
    by_id = {obj["id"]: obj for obj in OBJECTS}
    moved = {}
    for row in survey["objects"]:
        obj = by_id[row["id"]]
        assert obj["meshId"] == row["meshId"]
        assert obj["position"][:2] == row["originalXY"] and obj.get("yaw", 0) == row["originalYaw"]
        moved[obj["id"]] = row["originZ"] - obj["position"][2]
        obj["position"] = row["xy"] + [row["originZ"]]
        obj["yaw"] = row["yaw"]
    for light in LIGHTS:
        if light.get("supportId") in moved:
            light["position"][2] += moved[light["supportId"]]
    return survey


def support_patch_geometry(row, foot, patch):
    """A closed, explicitly triangulated prism stable at GLB float32 precision.

    Floor patches are convex intersections of triangles. The hull removes
    only quantized near-duplicates/collinearity: every original boundary
    vertex must stay within the actual float32 rounding displacement.
    """
    def float32(value):
        return struct.unpack("<f", struct.pack("<f", value))[0]

    def cross(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

    original = [(p[0], p[1]) for p in patch]
    quantized = [(float32(x), float32(y)) for x, y in original]
    rounding = max(math.dist(p, q) for p, q in zip(original, quantized))
    ordered = sorted(set(quantized))
    lower, upper = [], []
    for target, sequence in [(lower, ordered), (upper, reversed(ordered))]:
        for p in sequence:
            while len(target) >= 2 and cross(target[-2], target[-1], p) <= 0:
                target.pop()
            target.append(p)
    hull = lower[:-1] + upper[:-1]
    if len(hull) < 3:
        return None
    area = abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(hull,hull[1:]+hull[:1])))/2
    if area < 1e-9:
        return None
    for p in original:
        distance = math.inf
        for a, b in zip(hull, hull[1:]+hull[:1]):
            dx, dy = b[0]-a[0], b[1]-a[1]
            u = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
            distance = min(distance, math.dist(p, (a[0]+u*dx, a[1]+u*dy)))
        assert distance <= rounding + 2e-8, ("Non-quantization concavity in foot patch", row["id"], distance, rounding)
    # Use the widest source triangle to recover its surveyed floor plane.
    a = patch[0]
    b, c = max(((b,c) for i,b in enumerate(patch[1:],1) for c in patch[i+1:]),
               key=lambda pair: abs(cross(a,pair[0],pair[1])))
    den = cross(a,b,c)
    zx = ((b[2]-a[2])*(c[1]-a[1])-(c[2]-a[2])*(b[1]-a[1]))/den
    zy = ((b[0]-a[0])*(c[2]-a[2])-(c[0]-a[0])*(b[2]-a[2]))/den
    bottom = [(x,y,float32(a[2]+zx*(x-a[0])+zy*(y-a[1]))) for x,y in hull]
    top = float32(row["originZ"] + foot["localBottomZ"] + .012)
    assert min(top-p[2] for p in bottom) >= .0129
    n = len(hull)
    vertices = bottom + [(x,y,top) for x,y in hull]
    faces = [(0,i+1,i) for i in range(1,n-1)] + [(n,n+i,n+i+1) for i in range(1,n-1)]
    for i in range(n):
        j = (i+1) % n
        faces.extend([(i,j,n+j),(i,n+j,n+i)])
    return vertices, faces


def furnishing_foot_supports(survey, physical=False):
    """Precisely cut timber pole extensions and stone bases; all faces closed."""
    for row in survey["objects"]:
        for foot in row["feet"]:
            for patch in foot["floorPatches"]:
                geometry = support_patch_geometry(row, foot, patch)
                if geometry:
                    g.solid(*geometry, "stone_cream" if physical else foot["material"], bevel=0)


def export_furnishing_support_piece(name, fn, out, materials, role="architecture"):
    """Only this new lot uses local-island normals and its authored triangles.

    No global helper behavior changes. Generic degenerate dissolution cannot
    open these already-quantized, explicitly triangulated closed volumes.
    """
    if not g.bpy:
        return g.export_piece(name, fn, out, materials, role=role, clean_degenerate=False)
    original = g.bmesh
    diagnostics = {"mesh": name, "normalPasses": 0, "normalUpdateCalls": 0,
                   "orientationMethod": "paired directed edges and positive local signed volume; one normal update per pass",
                   "closedIslandsChecked": 0,
                   "openIslands": 0, "minimumAbsoluteVolume": math.inf}

    class LocalOps:
        def __getattr__(self, key):
            return getattr(original.ops, key)

        def recalc_face_normals(self, bm, faces):
            remaining = set(faces)
            diagnostics["normalPasses"] += 1
            while remaining:
                component = [remaining.pop()]
                for face in component:
                    for edge in face.edges:
                        for neighbour in edge.link_faces:
                            if neighbour in remaining:
                                remaining.remove(neighbour)
                                component.append(neighbour)
                edges = {edge for face in component for edge in face.edges}
                if any(not edge.is_manifold for edge in edges):
                    diagnostics["openIslands"] += 1
                    raise RuntimeError(("Open fitted foot island", name))
                for edge in edges:
                    loops = list(edge.link_loops)
                    if (len(loops) != 2 or loops[0].vert != loops[1].link_loop_next.vert
                            or loops[1].vert != loops[0].link_loop_next.vert):
                        raise RuntimeError(("Inconsistent fitted foot winding", name))
                vertices = {vertex for face in component for vertex in face.verts}
                saved = [(v, tuple(v.co)) for v in vertices]
                centre = [sum(co[k] for _,co in saved)/len(saved) for k in range(3)]
                for vertex, co in saved:
                    vertex.co = tuple(co[k]-centre[k] for k in range(3))
                volume = 0
                for face in component:
                    pts = [v.co.copy() for v in face.verts]
                    volume += sum(pts[0].dot(pts[i].cross(pts[i+1]))/6 for i in range(1,len(pts)-1))
                assert abs(volume) > 1e-15, ("Degenerate fitted foot island", name, volume)
                if volume < 0:
                    for face in component:
                        face.normal_flip()
                diagnostics["minimumAbsoluteVolume"] = min(diagnostics["minimumAbsoluteVolume"], abs(volume))
                diagnostics["closedIslandsChecked"] += 1
                for vertex, co in saved:
                    vertex.co = co
            # Triangles already have coherent outward winding. Updating their
            # cached normals once avoids a full BMesh flag scan for every isle.
            bm.normal_update()
            diagnostics["normalUpdateCalls"] += 1

    class LocalBmesh:
        ops = LocalOps()

        def __getattr__(self, key):
            return getattr(original, key)

    g.bmesh = LocalBmesh()
    try:
        g.export_piece(name, fn, out, materials, role=role, clean_degenerate=False)
    finally:
        g.bmesh = original
        DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
        (DIAGNOSTICS / (name + "-normal-closure.json")).write_text(json.dumps(diagnostics,indent=2)+"\n")


def target(key, name, x, y, z=0, kind="place"):
    position = layout.point(x, y, z)
    TARGETS.append({"id": key, "position": position})
    LANDMARKS.append({"id": key, "name": name, "position": position, "kind": kind})


def building(plot):
    key = plot["id"]
    x, y = plot["position"]
    style = plot["style"]
    floors = plot["floors"]
    yaw = plot["yaw"]
    kind = plot["trade"] % 3
    base = layout.ground_height(x, y)
    angle = math.radians(yaw)
    size = [plot["width"] / 10, plot["depth"] / 10, 1]

    def relative(dx, dy):
        dx, dy = dx * size[0], dy * size[1]
        return x + dx * math.cos(angle) - dy * math.sin(angle), y + dx * math.sin(
            angle
        ) + dy * math.cos(angle)

    place(
        key + "-walls",
        f"mp-shop-{style}-{floors}",
        x,
        y,
        yaw=yaw,
        role="wall",
        occluder=True,
        scale=size,
    )
    place(
        key + "-roof",
        f"mp-roof-{style}-{floors}",
        x,
        y,
        yaw=yaw,
        role="roof",
        roof=True,
        occluder=True,
        scale=size,
    )
    place(key + "-interior", f"mp-furniture-{kind}", x, y, yaw=yaw, role="furniture", scale=size)
    place(key + "-floor", "mp-interior-base", x, y, yaw=yaw, role="floor", scale=size)
    ax, ay = relative(0, 6.7)
    place(
        key + "-awning",
        f"mp-awning-{style % 2}",
        ax,
        ay,
        base - layout.ground_height(ax, ay),
        yaw=yaw,
        role="textile",
    )
    sx, sy = relative(3.7, 5.2)
    place(
        key + "-sign",
        f"mp-trade-sign-{plot['trade'] % 3}",
        sx,
        sy,
        base - layout.ground_height(sx, sy),
        yaw=yaw,
        role="furniture",
    )
    door = relative(0, 5)
    BUILDINGS.append(
        {
            "id": key,
            "position": [x, y, base],
            "footprint": [plot["width"], plot["depth"]],
            "group": plot["group"],
            "door": [door[0], door[1], base],
            "yaw": yaw,
            "clearDoorWidth": 2.8 * size[0],
            "interior": [x, y, base],
            "floors": floors,
            "storeyHeight": 3.5,
            "trade": ["food", "tavern", "mechanics", "textiles", "pottery", "imports"][
                plot["trade"]
            ],
        }
    )
    # Only ordinary shops genuinely reached by the street network are targets.
    TARGETS.append({"id": key + "-interior", "position": [x, y, base]})
    return base


def append_proxies(out, materials):
    visuals = list(g.PIECES)
    active = {obj["meshId"] for obj in OBJECTS if obj.get("collision", True)}
    for piece in visuals:
        if piece["id"] not in active:
            continue
        name = piece["id"] + "-collision"
        if name in REUSE:
            g.PIECES.append(dict(REUSE[name]))
        else:
            if piece["id"] == "mp-furnishing-foot-supports":
                export_furnishing_support_piece(name, PROXY_SPECS[piece["id"]], out, materials,
                                               role="collision-proxy")
            else:
                g.export_piece(
                    name,
                    PROXY_SPECS[piece["id"]],
                    out,
                    materials,
                    role="collision-proxy",
                    clean_degenerate=True,
                )
        g.PIECES[-1]["role"] = "collision-proxy"
        piece["collisionMesh"] = name
    return {
        "policy": "authored architectural geometry; decorative dressing is nonblocking",
        "proxies": len(active),
        "distinctTriangles": sum(
            m["triangles"] for m in g.PIECES if m.get("role") == "collision-proxy"
        ),
        "coverage": "all colliding placed local meshes; floor openings and 2.8m doorways preserved",
    }


def build_visit_route():
    """Acceptance walk follows streets and reaches the stair from its toe.

    Direct diagonals through the mercantile blocks and the Shaft's tangent
    frontages are not walkable. The gallery approach stays west of the filled
    stair before crossing its twenty authored treads at their exact heights.
    The lower landing keeps a full capsule on the court, 0.8m before the first
    riser, rather than placing its centre in the stair's transition zone.
    """
    points = [
        (-119, -61),
        (-84, -38),
        (-40, -16),
        (0, -16),
        (0, -43),
        (0, -16),
        (59, -30),
        (85, -42.8),
        (85, -38),
        (90, -5),
        (91, 27),
        (44, 30),
        (44, 59),
        (44, 30),
        (17, 28),
        (-28, 37),
        (-42.5, 37),
        (-45.68, 42.93),
        (-50.1005, 46.8995),
        (-54.07, 51.32),
        (-60, 54.5),
        (-60, 55),
        (-60, 54.5),
        (-65.93, 51.32),
        (-69.8995, 46.8995),
        (-74.32, 42.93),
        (-77.5, 37),
        (-88, 37),
        (-96, 45),
        (-96, 63),
        (-94, 112),
        (-49, 119),
        (-44, 112),
        (-44, 90),
        (-36, 90),
        (-29, 90),
        (-29, 91.2),
    ]
    visits = layout.sampled_route(points)
    for i in range(20):
        visits.append(layout.point(-29, 92 + (i + 0.5) * 0.4, (i + 1) * 0.18))
    visits.append(layout.point(-29, 101.8, 3.6))
    for i in reversed(range(20)):
        visits.append(layout.point(-29, 92 + (i + 0.5) * 0.4, (i + 1) * 0.18))
    visits.append(layout.point(-29, 91.2))
    return visits


def build_crowd_routes(visits=None):
    """Public crowd loops reuse the accepted street walk, in both directions.

    The market/arena connection follows Stravian Avenue and Witch Street;
    the Shaft connection follows Reservoir Street's clear inner annulus.
    Direct chords across these neighbourhoods enter shops and delivery stock.
    """
    visits = build_visit_route() if visits is None else visits

    def return_walk(start, end):
        first = next(i for i, p in enumerate(visits) if p[:2] == list(start))
        last = next(i for i, p in enumerate(visits[first:], first) if p[:2] == list(end))
        outward = visits[first:last + 1]
        return outward + outward[-2::-1]

    return [
        layout.sampled_route(
            [(-84, -38), (-40, -16), (0, -16), (59, -30), (0, -16), (-40, -16), (-84, -38)]
        ),
        return_walk((0, -16), (44, 59)),
        return_walk((-28, 37), (-96, 63)),
    ]


def build(out):
    out.mkdir(parents=True, exist_ok=True)
    old_manifest = out / "manifest.json"
    previous_files = set()
    if old_manifest.is_file():
        previous_files = {
            mesh["file"] for mesh in json.loads(old_manifest.read_text(encoding="utf-8"))["meshes"]
        }
    for seq in [
        g.PIECES,
        g.OBJECTS,
        g.ROOFS,
        OBJECTS,
        ROOFS,
        LIGHTS,
        LANDMARKS,
        TARGETS,
        BUILDINGS,
    ]:
        seq.clear()
    PROXY_SPECS.clear()
    if not REUSE:
        g.bpy.ops.object.select_all(action="SELECT")
        g.bpy.ops.object.delete(use_global=False)
    materials = g.build_materials() if g.bpy else None
    emit(out, materials, "mp-relief-ground", district_ground, district_ground)
    for road in layout.ROADS:
        emit(out, materials, "mp-road-" + road["id"], lambda road=road: road_surface(road))
    emit(out, materials, "mp-public-paving", public_paving)
    for style in range(3):
        for floors in [2, 3, 4]:
            emit(
                out,
                materials,
                f"mp-shop-{style}-{floors}",
                lambda style=style, floors=floors: shop_shell(style, floors),
                lambda floors=floors: shop_physical(floors),
            )
            emit(
                out,
                materials,
                f"mp-roof-{style}-{floors}",
                lambda style=style, floors=floors: shop_roof(style, floors),
                lambda style=style, floors=floors: shop_roof(style, floors, True),
            )
        emit(
            out,
            materials,
            f"mp-furniture-{style}",
            lambda style=style: furniture(style),
            lambda: [
                physical_box(-3.35, -0.5, 0, 1.1, 5.8, 1.15),
                physical_box(3.2, -1, 0, 2.2, 5.5, 1.2),
            ],
        )
    for i in range(4):
        emit(
            out,
            materials,
            f"mp-stock-{i}",
            lambda i=i: stock(i),
            lambda: physical_box(0, 0, 0, 2.8, 1.1, 1.3),
        )
    for i, mat in enumerate(["burgundy", "roof_blue"]):
        emit(out, materials, f"mp-awning-{i}", lambda mat=mat: awning(material=mat))
    for name, fn, physical in [
        ("hall", hall_body, hall_physical),
        ("hall-roof", hall_roof, lambda: physical_box(0, 0, 6.5, 31.5, 25, 4.8)),
        ("illu-die", illu_body, illu_physical),
        (
            "illu-canopy",
            illu_canopy,
            lambda: [
                sector(
                    13.7,
                    17.5,
                    q * math.pi / 2 + 0.27,
                    (q + 1) * math.pi / 2 - 0.27,
                    4.45,
                    0.9,
                    "stone_cream",
                )
                for q in range(4)
            ],
        ),
        (
            "gate",
            gate,
            lambda: (
                [physical_box(x, 0, 0, 3.5, 6.5, 9.7) for x in [-5.25, 5.25]]
                + [physical_box(0, 0, 6, 7.5, 3.4, 2)]
            ),
        ),
        ("fountain", fountain, lambda: physical_box(0, 0, 0, 4.4, 4.4, 0.55)),
        ("shaft-garden", shaft_garden, lambda: physical_box(0, 0, 0, 6, 6, 15.6)),
        ("gallery", gallery, lambda: gallery(True)),
        ("gallery-canopy", gallery_canopy, lambda: gallery_canopy(True)),
        ("quay-wall", quay_wall, None),
        ("city-context-land", city_context_land, None),
        ("lamp", lamp, lambda: physical_box(0, 0, 0, 0.42, 0.42, 3.5)),
        ("cart", cart, lambda: physical_box(0, 0, 0.25, 2.5, 3.5, 1.6)),
        ("planter", planter, lambda: physical_box(0, 0, 0, 1.1, 1.1, 0.9)),
        ("interior-base", interior_base, lambda: physical_box(0, 0, -0.08, 9.4, 9.4, 0.1)),
        ("trade-sign-0", lambda: trade_sign(0), None),
        ("trade-sign-1", lambda: trade_sign(1), None),
        ("trade-sign-2", lambda: trade_sign(2), None),
        (
            "tavern-table",
            lambda: [
                table(0, 0, width=2),
                w.bench(0, -1.1, 2),
                w.bench(0, 1.1, 2),
                jar(0.4, 0, 0.96, 0.4),
            ],
            lambda: physical_box(0, 0, 0, 2, 2.8, 1.1),
        ),
        (
            "crates",
            lambda: [crate(-0.6, 0), crate(0.5, 0), crate(-0.6, 0, 0.8)],
            lambda: physical_box(0, 0, 0, 2, 1, 1.5),
        ),
        (
            "barrels",
            lambda: [barrel(0, 0), barrel(0.9, 0.15, scale=0.78)],
            lambda: physical_box(0.3, 0, 0, 1.6, 0.8, 1),
        ),
        ("linen-line", lambda: w.cloth(0, 0, 3.5, 4.5, 1.2, folds=9, material="linen"), None),
        (
            "closed-gate",
            lambda: [block(-3.8 + j * 0.38, 0, 0, 0.13, 0.22, 4, "dark_metal") for j in range(21)],
            lambda: physical_box(0, 0, 0, 8, 0.22, 4),
        ),
        (
            "bridge",
            old_bridge,
            lambda: (
                [physical_box(0, 0, -0.55, 24, 8, 0.55)]
                + [physical_box(0, y, 0, 24, 0.48, 1.15) for y in [-4, 4]]
            ),
        ),
        (
            "oldtown-bank",
            lambda: block(
                202, 20, -3.8, 100, 360, 3.8 + layout.ground_height(*layout.GATE), "cobble"
            ),
            None,
        ),
    ]:
        emit(out, materials, "mp-" + name, fn, physical)
    place("relief-ground", "mp-relief-ground", 0, 0, role="ground", absolute=True)
    for road in layout.ROADS:
        place(road["id"] + "-surface", "mp-road-" + road["id"], 0, 0, role="floor", absolute=True)
    place("public-court-paving", "mp-public-paving", 0, 0,
          role="floor", absolute=True, occluder=False)
    place("river-revetment", "mp-quay-wall", 0, 0, role="wall", absolute=True, occluder=True)
    place("surrounding-city-land", "mp-city-context-land", 0, 0, role="background", absolute=True)
    for row, y in enumerate([170, 185]):
        for col, x in enumerate(range(-127, 129, 16)):
            style = (row + col) % 3
            floors = 2 + (col % 2)
            for kind, role in [("shop", "background"), ("roof", "background")]:
                obj = place(
                    f"south-context-{kind}-{row}-{col}",
                    f"mp-{kind}-{style}-{floors}",
                    x,
                    y,
                    yaw=180,
                    role=role,
                    occluder=True,
                )
                obj["collision"] = False
    for col, x in enumerate([-158, -174]):
        for row, y in enumerate([-57, -29, 0, 29, 58, 87, 116, 146]):
            if -72 < y < -48:
                continue
            style = (row + col) % 3
            floors = 2 + (row % 2)
            for kind in ["shop", "roof"]:
                obj = place(
                    f"west-context-{kind}-{row}-{col}",
                    f"mp-{kind}-{style}-{floors}",
                    x,
                    y,
                    yaw=90,
                    role="background",
                    occluder=True,
                )
                obj["collision"] = False
    for plot in layout.PLOTS:
        building(plot)
    mx, my = layout.MARKET
    ax, ay = layout.ILLU
    sx, sy = layout.SHAFT
    gx, gy = layout.GATE
    place("municipal-market", "mp-hall", mx, my, role="wall", occluder=True)
    place("municipal-market-roof", "mp-hall-roof", mx, my, role="roof", roof=True, occluder=True)
    target("municipal-market", "Municipal Market", mx, my, kind="interior")
    # Free crossed aisles, distinct produce/textile/import bays and deliveries.
    for i, dx in enumerate([-11, -6, 6, 11]):
        for j, dy in enumerate([-7, 7]):
            market_bay(f"hall-bay-{i}-{j}", mx + dx, my + dy, (i + j) % 4, 180 if j == 0 else 0)
    for i, x in enumerate([-12, -6, 6, 12]):
        market_bay(f"food-front-{i}", x, -22, i % 4)
        market_bay(f"cloth-back-{i}", x, -65, 1 if i % 2 else 2, 180)
    delivery("market-delivery", -25, -48, 90)
    delivery("market-imports", 25, -50, 270)
    place("illu-die-arena", "mp-illu-die", ax, ay, role="architecture", occluder=True)
    place("illu-die-canopy", "mp-illu-canopy", ax, ay, role="roof", roof=True, occluder=True)
    target("illu-die-arena", "Illu Die Arena", ax, ay, kind="interior")
    target("ice-street", "Ice St", ax, ay - 22)
    for a in [math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4]:
        LIGHTS.append(
            {
                "position": [
                    ax + 13 * math.cos(a),
                    ay + 13 * math.sin(a),
                    layout.ground_height(ax, ay) + 7.5,
                ],
                "candelas": 180,
                "radius": 18,
                "color": "#9baaff",
                "always": True,
            }
        )
    place("shaft-loop-ensemble", "mp-shaft-garden", sx, sy, role="landscape", occluder=False)
    target("shaft-loop", "The Shaft Loop", sx, sy + 18)
    target("shaft-central-work", "Ouvrage du Shaft Loop", sx, sy + 5)
    for i in range(4):
        angle = math.pi / 4 + i * math.pi / 2
        x, y = sx + 17 * math.cos(angle), sy + 17 * math.sin(angle)
        place(f"shaft-ring-bench-{i}", "mp-tavern-table", x, y, role="furniture")
    place("public-gallery", "mp-gallery", -29, 100, role="architecture", occluder=True)
    place(
        "public-gallery-canopy",
        "mp-gallery-canopy",
        -29,
        100,
        role="roof",
        roof=True,
        occluder=True,
    )
    target("gallery-court", "Cour des étoffes", -29, 89)
    target("gallery-upper", "Galerie publique", -29, 101.8, 3.6, kind="upper-interior")
    # Small planted seating areas finish the court's edges; its central
    # 4m-wide staircase and accepted west approach remain completely clear.
    for i, (x, y) in enumerate([(-39, 96), (-19, 96), (-39, 109), (-19, 109)]):
        place_on_public_paving(f"gallery-court-planter-{i}", "mp-planter", x, y,
                               role="foliage")["motion"] = "foliage"
    for i, x in enumerate([-39, -19]):
        place_on_public_paving(f"gallery-court-seating-{i}", "mp-tavern-table", x, 102,
                               role="furniture")
    street_finishing()
    place("reservoir-fountain", "mp-fountain", -11, 27, role="furniture")
    target("reservoir-street", "Reservoir St", -11, 32)
    # The upper/right river exists only outside the wall and bridge approaches.
    place("market-gate", "mp-gate", gx, gy, yaw=90, role="wall", occluder=True)
    target("market-gate", "Market Gate", gx - 4, gy)
    bz = layout.ground_height(gx, gy)
    place("old-bridge", "mp-bridge", 140, -60, bz, yaw=0, role="floor", absolute=True)
    target("old-bridge", "Old Bridge", 140, -60)
    place("oldtown-closed", "mp-closed-gate", 152, -60, bz, yaw=90, role="wall", absolute=True)
    place("oldtown-bank", "mp-oldtown-bank", 0, 0, role="background", absolute=True)
    for row, x in enumerate([170, 184, 199]):
        for j, y in enumerate([-90, -74, -37, -20, 0, 20, 40, 60, 80, 100, 120]):
            style = (row + j) % 3
            floors = 2 + (row + j) % 2
            item = place(
                f"oldtown-house-{row}-{j}",
                f"mp-shop-{style}-{floors}",
                x,
                y,
                bz,
                yaw=90,
                role="background",
                absolute=True,
                occluder=True,
            )
            item["collision"] = False
            item = place(
                f"oldtown-roof-{row}-{j}",
                f"mp-roof-{style}-{floors}",
                x,
                y,
                bz,
                yaw=90,
                role="background",
                absolute=True,
                occluder=True,
            )
            item["collision"] = False
    target("oldtown-exit-closed", "Oldtown — passage fermé", 150, -60, kind="closed-exit")
    for key, x, y, yaw in [
        ("downtown", -128, 112, 90),
        ("scholarnest", -92, 148, 0),
        ("dweomer", 89, 148, 0),
    ]:
        place(key + "-closed", "mp-closed-gate", x, y, yaw=yaw, role="wall")
        target(
            key + "-exit",
            key.capitalize() + " — passage fermé",
            x + (3 if yaw else 0),
            y - (3 if not yaw else 0),
            kind="closed-exit",
        )
    target("arenarea-exit", "Arenarea", -124, -64, kind="open-exit")
    for road in layout.ROADS:
        x, y = road["points"][len(road["points"]) // 2]
        if road["id"] != "reservoir-street":
            target(road["id"], road["id"].replace("-", " ").title(), x, y)
    for key, name, x, y in [
        ("hens-alley", "Hen’s Alley", -96, 80),
        ("blinddagger-corner", "Blinddagger Corner", -108, 105),
        ("ubel-paradise", "Ubel Paradise", *layout.UBEL_PARADISE),
    ]:
        target(key, name, x, y)
    # Dense service courts tell different trades; do not fill circulation with
    # random boxes. Canopies, linens and stock stay beside real fronts.
    for i, plot in enumerate(layout.PLOTS):
        x, y = plot["position"]
        a = math.radians(plot["yaw"])
        base = layout.ground_height(x, y)

        def pt(dx, dy, x=x, y=y, a=a, plot=plot):
            dx, dy = dx * plot["width"] / 10, dy * plot["depth"] / 10
            return x + dx * math.cos(a) - dy * math.sin(a), y + dx * math.sin(a) + dy * math.cos(a)

        if i % 3 == 0:
            px, py = pt(-3.6, 6.4)
            place(
                f"shop-reserve-{i}",
                "mp-crates" if plot["trade"] in [0, 3, 5] else "mp-barrels",
                px,
                py,
                base - layout.ground_height(px, py),
                yaw=plot["yaw"],
                role="furniture",
            )
        if i % 7 == 0:
            px, py = pt(0, -5.9)
            place(
                f"back-laundry-{i}",
                "mp-linen-line",
                px,
                py,
                base - layout.ground_height(px, py),
                yaw=plot["yaw"],
                role="textile",
            )
        if i % 4 == 0:
            px, py = pt(4.3, 6.7)
            place(f"door-planter-{i}", "mp-planter", px, py, role="foliage")["motion"] = "foliage"
        px, py = pt(3.9, 5.4)
        LIGHTS.append(
            {
                "position": [px, py, base + 2.7],
                "candelas": 26,
                "radius": 5,
                "color": "#ffd19b",
                "always": True,
            }
        )
    for road in layout.ROADS[:5]:
        pts = layout.sampled_route(road["points"], step=18)
        for i, p in enumerate(pts):
            if i % 2:
                continue
            x, y, z = p
            x += road["width"] / 2 + 1
            # Street lamps must never be planted inside a shop front.
            if any(math.hypot(x - b["position"][0], y - b["position"][1]) < 8 for b in BUILDINGS):
                continue
            obj = place(f"lamp-{road['id']}-{i}", "mp-lamp", x, y, role="furniture")
            LIGHTS.append(
                {
                    "position": [x, y, obj["position"][2] + 3.3],
                    "supportId": obj["id"],
                    "candelas": 70,
                    "radius": 8,
                    "color": "#ffce94",
                }
            )
    align_paved_furnishing()
    foot_survey = fit_furnishing_feet()
    emit(out, materials, "mp-furnishing-foot-supports",
         lambda: furnishing_foot_supports(foot_survey),
         lambda: furnishing_foot_supports(foot_survey, True))
    place("furnishing-foot-supports", "mp-furnishing-foot-supports", 0, 0,
          role="furniture", absolute=True, occluder=False)
    # Original quest and arrival IDs survive; only scene placements change.
    entities = {
        "e1": layout.point(2, -23),
        "e2": layout.point(-2, -23),
        "e3": layout.point(-119, -61),
        "e4": layout.point(-125, -65),
        "e5": layout.point(116, -60),
        "e6": layout.point(150, -60),
        "e7": layout.point(-92, 145),
        "e8": layout.point(-125, 112),
        "e9": layout.point(89, 145),
    }
    route = layout.sampled_route(
        [(116, -60), (59, -30), (0, -16), (0, -23), (0, -16), (-40, -16), (-84, -38), (-119, -61)]
    )
    visits = build_visit_route()
    shots = [
        {
            "name": name,
            "target": layout.point(x, y, dz),
            "yaw": yaw,
            "pitch": pitch,
            "distance": distance,
        }
        for name, x, y, dz, yaw, pitch, distance in [
            ("ensemble", 0, 26, 6, 0, 57, 305),
            ("market-street", 0, -20, 1.6, 0, 34, 30),
            ("market-interior", 0, -43, 1.6, 0, 45, 21),
            ("illu-die", 44, 49, 2, 20, 42, 40),
            ("shaft-loop", -60, 37, 4, 0, 53, 65),
            ("urban-alley", -96, 80, 1.6, 30, 36, 26),
            ("public-gallery", -29, 103, 5.2, 0, 38, 31),
            ("old-bridge", 133, -60, 1.5, 90, 32, 46),
            ("old-bridge-diagonal", 133, -60, 1.5, 45, 32, 46),
        ]
    ]
    gallery_z = layout.ground_height(-29, 100) + 3.6
    metadata = {
        "area": layout.AREA,
        "levels": [
            {"name": "Rues et intérieurs", "z": 0},
            {"name": "Galerie publique", "z": gallery_z},
        ],
        "start": entities["e5"],
        "route": route,
        "visitRoute": visits,
        "navigationTargets": TARGETS,
        "landmarks": LANDMARKS,
        "entityPositions": entities,
        "lights": LIGHTS,
        "waters": [
            {"position": [0, -135, -2.6], "size": [410, 160]},
            {"position": [140, 36, -2.6], "size": [24, 380]},
            {"position": layout.point(-11, 27, 0.3), "size": [3.4, 3.4]},
        ],
        "crowdRoutes": build_crowd_routes(visits),
        "roofsIds": ROOFS,
        "roofObjectIds": ROOFS,
        "buildings": BUILDINGS,
        "shots": shots,
        "materialAliases": {
            "roof_blue": "burgundy",
            "plaster_ochre": "stone_cream",
            "plaster_sage": "stone_cream",
            "produce_red": "pottery",
            "produce_green": "pottery",
            "cobble": "stone_cream",
            "foliage": "linen",
        },
        "materialColors": {k: list(v[0]) for k, v in EXTRA_MATERIALS.items()},
        "minimumMainStreetWidth": 6,
        "doorClearWidth": 2.8,
        "heightFunction": {"module": "martpart_district_layout", "function": "ground_height"},
        "groundHeightfield": layout.heightfield(),
        "storeyRegions": [
            {"storey": 0, "minimum": [120, -63.8, bz], "maximum": [152, -56.2, bz + 0.2]},
            {"storey": 1, "minimum": [-35, 100, gallery_z], "maximum": [-23, 106, gallery_z + 3.2]},
        ]
        + [
            {
                "storey": 0,
                "minimum": [-31, 92 + j * 0.4, layout.ground_height(-29, 100) + (j + 1) * 0.18],
                "maximum": [
                    -27,
                    92 + (j + 1) * 0.4,
                    layout.ground_height(-29, 100) + (j + 1) * 0.18 + 3.2,
                ],
            }
            for j in range(20)
        ],
        "terrain": {
            "revision": "martpart-relief-20261011",
            "coordinates": "X drawing right, Y drawing bottom; not compass north",
            "rangeMeters": [
                min(layout.heightfield()["heights"]),
                max(layout.heightfield()["heights"]),
            ],
            "platforms": layout.PLATFORMS,
            "roads": layout.ROADS,
            "river": "upper/right only",
            "illuCanopy": "red burgundy",
            "shaftLoop": "annular built garden and central ouvrage; no new basement",
        },
        "source": "Tanares Sourcebook pp.98-99; delivered Martpart atlas and architectures.json; approval 11 October 2026",
        "visualDetails": {"counts": dict(g.DETAIL_COUNTS), "vertexColor": "COLOR_0"},
        "notes": [
            "Eight metres of continuous urban relief toward the river; flat public foundations and level shop thresholds.",
            "Two/three residential storeys, selected four; 3.5m each. Only the market gallery is an accessible upper floor.",
            "Municipal Market blue-violet roof; Illu Die red tribune roofs and magical taii’maku lamps.",
            "Shaft Loop remains a built and planted annular surface place, without an invented playable underground.",
        ],
    }
    metadata["collision"] = append_proxies(out, materials)
    manifest = {
        "format": "jadg-district",
        "version": 2,
        "generator": "scripts/assetsGeneration/build_martpart_district.py",
        "coordinates": "metres; X drawing right Y drawing bottom Z up; GLB X right Y up Z down",
        "uvMetersPerRepeat": 2,
        "materials": g.NAMES,
        "meshes": g.PIECES,
        "objects": OBJECTS,
        "metadata": metadata,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    verify(out)
    # Only files explicitly owned by the preceding manifest are replacements.
    # The source-before snapshot keeps recovery copies; stray/manual files are
    # never inferred to be disposable from a broad directory glob.
    retained = {mesh["file"] for mesh in manifest["meshes"]}
    for name in previous_files - retained:
        obsolete = out / name
        if obsolete.parent.resolve() != out.resolve():
            raise RuntimeError(f"Unexpected preceding mesh path: {name}")
        obsolete.unlink(missing_ok=True)


def verify(out):
    path = out / "manifest.json"
    m = json.loads(path.read_text(encoding="utf-8"))
    ids = set()
    for mesh in m["meshes"]:
        data = (out / mesh["file"]).read_bytes()
        magic, version, size = struct.unpack_from("<III", data)
        assert magic == 0x46546C67 and version == 2 and size == len(data), mesh["id"]
        length, kind = struct.unpack_from("<II", data, 12)
        assert kind == 0x4E4F534A
        doc = json.loads(data[20 : 20 + length])
        assert len(doc["meshes"]) == 1
        for primitive in doc["meshes"][0]["primitives"]:
            assert {"POSITION", "NORMAL", "TEXCOORD_0", "COLOR_0"}.issubset(primitive["attributes"])
        mesh["sha256"] = hashlib.sha256(data).hexdigest()
        mesh["bytes"] = len(data)
        assert mesh["id"] not in ids
        ids.add(mesh["id"])
    assert len({o["id"] for o in m["objects"]}) == len(m["objects"])
    assert all(o["meshId"] in ids for o in m["objects"])
    assert set(m["metadata"]["roofsIds"]).issubset({o["id"] for o in m["objects"]})
    assert all(b["clearDoorWidth"] >= 2 for b in m["metadata"]["buildings"])
    # Test the actual local shell's doorway and furnishing aisle analytically.
    assert all(
        abs(math.dist(b["door"][:2], b["position"][:2]) - b["footprint"][1] / 2) < 1e-6
        for b in m["metadata"]["buildings"]
    )
    meshes = {mesh["id"]: mesh for mesh in m["meshes"]}
    assert all(
        meshes[obj["meshId"]].get("collisionMesh") in meshes
        for obj in m["objects"]
        if obj.get("collision", True)
    )
    assert m["metadata"]["groundHeightfield"]["spacing"] == [1.5, 1.5]
    assert len(m["metadata"]["groundHeightfield"]["heights"]) == (
        m["metadata"]["groundHeightfield"]["width"] * m["metadata"]["groundHeightfield"]["height"]
    )
    assert all(2 <= b["floors"] <= 4 for b in m["metadata"]["buildings"])
    path.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "status": "verified",
        "meshes": len(ids),
        "objects": len(m["objects"]),
        "buildings": len(m["metadata"]["buildings"]),
        "landmarks": len(m["metadata"]["landmarks"]),
        "triangles": sum(p["triangles"] for p in m["meshes"]),
        "bytes": sum(p["bytes"] for p in m["meshes"]),
        "checks": [
            "GLB header/length and one mesh per file",
            "POSITION NORMAL UV0 COLOR_0 per primitive",
            "SHA256 per mesh",
            "unique object IDs and all mesh references",
            "independent roof IDs",
            "2.8 m shop doorways",
            "complete authored architectural collision coverage",
            "continuous 1.5m heightfield and two-to-four storey homes",
        ],
        "requiresEngineValidation": [
            "render noon and 22h",
            "navigation including bridge and arena stairs",
            "camera wall/roof occultation",
            "frame time",
        ],
    }
    (out / "generation-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report), flush=True)


def preview(out):
    """Inspect the exported assembly; this is geometry evidence, not Unreal approval."""
    from mathutils import Vector

    bpy = g.bpy
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    DIAGNOSTICS.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    templates = {}
    for mesh in m["meshes"]:
        if mesh.get("role") == "collision-proxy":
            continue
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.import_scene.gltf(filepath=str(out / mesh["file"]))
        obj = next(o for o in bpy.context.selected_objects if o.type == "MESH")
        templates[mesh["id"]] = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
    for material in bpy.data.materials:
        key = material.name.split(".")[0]
        if key in g.MATERIALS:
            material.diffuse_color = g.MATERIALS[key][0]
    for item in m["objects"]:
        obj = bpy.data.objects.new(item["id"], templates[item["meshId"]])
        bpy.context.collection.objects.link(obj)
        x, y, z = item["position"]
        obj.location = (x, -y, z)
        obj.rotation_euler.z = math.radians(-item["yaw"])
        obj.scale = item.get("scale", [1, 1, 1])
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    cam = bpy.data.cameras.new("martpart-geometry-review")
    camera = bpy.data.objects.new("martpart-geometry-review", cam)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    cam.type = "ORTHO"
    for name, position, aim, scale, cutaway in [
        ("geometry-district", (20, 310, 270), (0, 25, 5), 340, False),
        ("geometry-market", (30, 7, 38), (0, -43, 6), 76, False),
        ("geometry-market-cutaway", (30, 7, 38), (0, -43, 6), 76, True),
        ("geometry-illu-die", (84, 100, 44), (44, 59, 5), 72, False),
        ("geometry-shaft-loop", (-30, 90, 54), (-60, 37, 8), 95, False),
        ("geometry-gallery", (0, 140, 35), (-29, 100, 11), 70, False),
    ]:
        for obj in scene.objects:
            obj.hide_render = cutaway and obj.name in m["metadata"]["roofsIds"]
        camera.location = (position[0], -position[1], position[2])
        point = Vector((aim[0], -aim[1], aim[2]))
        camera.rotation_euler = (point - camera.location).to_track_quat("-Z", "Y").to_euler()
        cam.ortho_scale = scale
        scene.render.filepath = str(DIAGNOSTICS / (name + ".png"))
        bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--blender", type=Path, default=BLENDER)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument(
        "--refresh-mesh",
        action="append",
        default=[],
        help="Rebuild only named meshes and new meshes; retain verified existing GLBs",
    )
    parser.add_argument(
        "--layout-only",
        action="store_true",
        help="Recompose the manifest using previously verified, unchanged GLBs",
    )
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if g.bpy and "--" in sys.argv else None
    )
    if args.verify:
        verify(args.output)
        return 0
    if args.layout_only:
        previous = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
        REUSE.update({item["id"]: item for item in previous["meshes"]})
        build(args.output)
        return 0
    if g.bpy:
        if args.refresh_mesh:
            previous = json.loads((args.output / "manifest.json").read_text(encoding="utf-8"))
            REUSE.update(
                {
                    item["id"]: item
                    for item in previous["meshes"]
                    if item["id"] not in args.refresh_mesh
                    and item["id"]
                    not in {identifier + "-collision" for identifier in args.refresh_mesh}
                }
            )
        build(args.output)
        if args.preview:
            preview(args.output)
        return 0
    command = [
        str(args.blender),
        "--background",
        "--threads",
        "2",
        "--python-exit-code",
        "1",
        "--python",
        str(Path(__file__).resolve()),
        "--",
        "--output",
        str(args.output),
    ]
    if args.preview:
        command.append("--preview")
    for mesh in args.refresh_mesh:
        command.extend(["--refresh-mesh", mesh])
    return subprocess.run(command).returncode


if __name__ == "__main__":
    raise SystemExit(main())
