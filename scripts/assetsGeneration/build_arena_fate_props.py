#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Headless Blender prop kit for the approved painted Arena of Fate.

Simple closed pieces compose each reusable logical mesh; no heraldry or characters.
Reuses witness primitives, with material-preserving bevels, smooth curved normals,
COLOR_0 and the same metre-projected UV convention.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena_geometry as w
import arena_sculpted_geometry as sculpt
from arena_fate_nameplates import entries as nameplate_entries

# Share actual geometry buffers with the approved witness's sculpting helpers.
sculpt.g = w

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/arena-fate-props"


def transform(build, position=(0, 0, 0), axis="z", angle=0):
    start = len(w.VERTS)
    build()
    a, b = {"x": (1, 2), "y": (2, 0), "z": (0, 1)}[axis]
    for i in range(start, len(w.VERTS)):
        x, y, z = w.VERTS[i]
        p = [x, -y, z]
        u, v = p[a], p[b]
        p[a] = u * math.cos(angle) - v * math.sin(angle)
        p[b] = u * math.sin(angle) + v * math.cos(angle)
        p = [p[k] + position[k] for k in range(3)]
        w.VERTS[i] = (p[0], -p[1], p[2])


def block(x, y, z, width, depth, height, material="wood"):
    w.block(x, y, z, width, depth, height, material)


def rod(a, b, radius=0.018, material="dark_metal", sides=24):
    w.rod(a, b, radius, material, sides)


def lathe(profile, material="bronze", sides=64, position=(0, 0, 0)):
    # Ring profiles close around their section, preserving the open centre.
    if len(profile) == 4 and abs(profile[0][0] - profile[-1][0]) < 1e-8:
        points = [
            (
                position[0] + r * math.cos(j * math.tau / sides),
                position[1] + r * math.sin(j * math.tau / sides),
                position[2] + z,
            )
            for r, z in profile
            for j in range(sides)
        ]
        faces = [
            (
                i * sides + j,
                i * sides + (j + 1) % sides,
                ((i + 1) % len(profile)) * sides + (j + 1) % sides,
                ((i + 1) % len(profile)) * sides + j,
            )
            for i in range(len(profile))
            for j in range(sides)
        ]
        w.solid(points, faces, material, bevel=0.003)
        w.FACE_SMOOTH[-len(faces) :] = [True] * len(faces)
        return
    w.turned(*position, profile, material, sides)


def sweep(path, radius, material="wood", sides=12):
    """A continuous closed tube along a polyline, including real end caps."""
    from mathutils import Vector

    closed = sum((path[0][k] - path[-1][k]) ** 2 for k in range(3)) < 1e-12
    if closed:
        path = path[:-1]
    points, faces = [], []
    for i, value in enumerate(path):
        p = Vector(value)
        direction = Vector(
            path[(i + 1) % len(path)] if closed else path[min(i + 1, len(path) - 1)]
        ) - Vector(path[(i - 1) % len(path)] if closed else path[max(0, i - 1)])
        direction.normalize()
        axis = direction.cross(Vector((0, 0, 1)))
        if axis.length < 0.01:
            axis = direction.cross(Vector((1, 0, 0)))
        axis.normalize()
        other = direction.cross(axis)
        for j in range(sides):
            angle = math.tau * j / sides
            points.append(tuple(p + radius * (axis * math.cos(angle) + other * math.sin(angle))))
    for i in range(len(path) if closed else len(path) - 1):
        for j in range(sides):
            a, b = i * sides + j, i * sides + (j + 1) % sides
            faces.append((a, b, (b + sides) % len(points), (a + sides) % len(points)))
    if not closed:
        faces += [
            tuple(range(sides - 1, -1, -1)),
            tuple((len(path) - 1) * sides + j for j in range(sides)),
        ]
    w.solid(points, faces, material, bevel=0.001)
    if closed:
        w.FACE_SMOOTH[-len(faces) :] = [True] * len(faces)
    else:
        w.FACE_SMOOTH[-len(faces) : -2] = [True] * (len(faces) - 2)


def ring(x, y, z, rx, ry, tube=0.012, material="bronze", axis="z"):
    def build():
        sweep(
            [
                (rx * math.cos(j * math.tau / 64), ry * math.sin(j * math.tau / 64), 0)
                for j in range(65)
            ],
            tube,
            material,
        )

    transform(build, (x, y, z), "x" if axis == "y" else "y", math.pi / 2 if axis != "z" else 0)


def plank_panel(x, y, z, width, depth, height, count=6, material="wood"):
    for i in range(count):
        block(
            x - width / 2 + (i + 0.5) * width / count,
            y,
            z,
            width / count - 0.009,
            depth,
            height,
            material,
        )


def rivets(x0, x1, y, z, count=6):
    for i in range(count):
        x = x0 + i * (x1 - x0) / max(1, count - 1)
        transform(
            lambda: lathe([(0.014, 0), (0.016, 0.007), (0.010, 0.014)], sides=16),
            (x, y, z),
            "x",
            math.pi / 2,
        )


def sword(x, y, z, height=1.05):
    rod((x, y, z), (x, y, z + 0.19), 0.024, "wood")
    lathe([(0.035, 0), (0.047, 0.025), (0.027, 0.055)], position=(x, y, z - 0.015))
    block(x, y, z + 0.20, 0.29, 0.045, 0.045, "bronze")
    # Closed diamond-section blade: the two broad planes catch distinct light.
    points = [
        (x - 0.042, y, z + 0.25),
        (x, y - 0.016, z + 0.25),
        (x + 0.042, y, z + 0.25),
        (x, y + 0.016, z + 0.25),
        (x - 0.032, y, z + height - 0.14),
        (x, y - 0.010, z + height - 0.14),
        (x + 0.032, y, z + height - 0.14),
        (x, y + 0.010, z + height - 0.14),
        (x, y, z + height),
    ]
    w.solid(
        points,
        [
            (3, 2, 1, 0),
            (0, 1, 5, 4),
            (1, 2, 6, 5),
            (2, 3, 7, 6),
            (3, 0, 4, 7),
            (4, 5, 8),
            (5, 6, 8),
            (6, 7, 8),
            (7, 4, 8),
        ],
        "dark_metal",
        bevel=0.002,
    )


def shield(x=0, y=0, z=0, radius=0.38):
    def build():
        lathe(
            [(radius * 0.88, 0), (radius, 0.018), (radius, 0.075), (radius * 0.90, 0.085)], "wood"
        )
        lathe(
            [
                (radius * 0.93, 0.035),
                (radius + 0.015, 0.045),
                (radius + 0.015, 0.075),
                (radius * 0.93, 0.085),
            ],
            "bronze",
        )
        lathe(
            [(0.11, 0.08), (0.12, 0.105), (0.10, 0.14), (0.06, 0.17), (0.025, 0.18)], "dark_metal"
        )
        rod((-0.14, 0, -0.07), (0.14, 0, -0.07), 0.025, "wood")
        for j in range(12):
            angle = j * math.tau / 12
            lathe(
                [(0.009, 0), (0.012, 0.008), (0.007, 0.015)],
                position=(radius * 0.94 * math.cos(angle), radius * 0.94 * math.sin(angle), 0.081),
                sides=16,
            )

    transform(build, (x, y, z + radius), "x", math.pi / 2 - 0.16)


def weapon_rack():
    for x in [-0.78, 0.78]:
        block(x, 0, 0, 0.42, 0.62, 0.10)
        block(x, 0.13, 0.10, 0.12, 0.12, 1.58)
        rod((x, -0.26, 0.10), (x, 0.13, 0.56), 0.035, "wood")
    block(0, 0.13, 0.28, 1.67, 0.10, 0.13)
    block(0, 0.13, 1.35, 1.68, 0.10, 0.12)
    for i, x in enumerate([-0.54, -0.27, 0, 0.27]):
        sword(x, -0.055, 0.34, 0.96 + i * 0.035)
        ring(x, -0.03, 1.35, 0.055, 0.055, 0.007, axis="y")
    rod((0.55, -0.04, 0.17), (0.55, -0.04, 1.92), 0.022, "wood")
    w.prism([(0.49, 1.9), (0.55, 2.14), (0.61, 1.9)], -0.06, -0.02, "dark_metal")
    rivets(-0.78, 0.78, 0.065, 1.42, 7)


def shields():
    shield(-0.4, 0, 0, 0.39)
    shield(0.4, 0.10, 0, 0.34)
    block(0, 0.22, 0, 1.0, 0.30, 0.10)


def bench():
    for x in [-0.78, 0.78]:
        for y in [-0.22, 0.22]:
            lathe([(0.06, 0), (0.08, 0.04), (0.05, 0.30), (0.08, 0.36)], "wood", position=(x, y, 0))
        block(x, 0, 0.25, 0.08, 0.52, 0.09)
    block(0, 0, 0.18, 1.62, 0.09, 0.10)
    for y in [-0.18, 0, 0.18]:
        block(0, y, 0.40, 1.95, 0.17, 0.075)
    for x in [-0.8, 0.8]:
        block(x, 0.27, 0.42, 0.08, 0.09, 0.45)
    block(0, 0.27, 0.68, 1.92, 0.065, 0.18)
    rivets(-0.8, 0.8, 0.225, 0.78)


def chest():
    plank_panel(0, 0, 0.09, 1.15, 0.68, 0.52)
    for x in [-0.52, 0.52]:
        for y in [-0.28, 0.28]:
            block(x, y, 0, 0.12, 0.12, 0.13)
    # Arched lid made of longitudinal staves, including full end pieces.
    lid_start = len(w.VERTS)
    for i in range(9):
        a, b = math.pi * i / 9, math.pi * (i + 1) / 9
        w.prism(
            [
                (-0.33 * math.cos(a), 0.60 + 0.20 * math.sin(a)),
                (-0.33 * math.cos(b), 0.60 + 0.20 * math.sin(b)),
                (-0.31 * math.cos(b), 0.585 + 0.20 * math.sin(b)),
                (-0.31 * math.cos(a), 0.585 + 0.20 * math.sin(a)),
            ],
            -0.57,
            0.57,
            "wood",
        )
    for i in range(lid_start, len(w.VERTS)):
        x, y, z = w.VERTS[i]
        w.VERTS[i] = (y, -x, z)
    # Closed fitted ends under the curved lid, instead of a hollow open end.
    for x in [-0.558, 0.558]:
        transform(
            lambda: w.prism(
                [(-0.32, 0.60), (0.32, 0.60)]
                + [
                    (0.32 * math.cos(j * math.pi / 12), 0.60 + 0.19 * math.sin(j * math.pi / 12))
                    for j in range(1, 12)
                ],
                -0.013,
                0.013,
                "wood",
            ),
            (x, 0, 0),
            angle=math.pi / 2,
        )
    for x in [-0.43, 0.43]:
        block(x, -0.346, 0.11, 0.055, 0.019, 0.48, "dark_metal")
        block(x, 0.346, 0.11, 0.055, 0.019, 0.48, "dark_metal")
        ring(x, -0.37, 0.33, 0.054, 0.044, 0.011, axis="y")
    block(0, -0.36, 0.40, 0.13, 0.025, 0.17, "bronze")
    ring(0, -0.386, 0.45, 0.019, 0.027, 0.006, "dark_metal", "y")


def amphora(x, y, scale=1):
    def build():
        # Hollow mouth and inner vessel wall, not a flat sealed jar silhouette.
        profile = [
            (0.11, 0),
            (0.16, 0.07),
            (0.25, 0.22),
            (0.30, 0.46),
            (0.27, 0.64),
            (0.15, 0.78),
            (0.12, 0.90),
            (0.17, 0.93),
            (0.17, 0.97),
            (0.115, 0.97),
            (0.09, 0.89),
            (0.125, 0.76),
            (0.235, 0.61),
            (0.25, 0.44),
            (0.19, 0.20),
            (0.08, 0.09),
        ]
        lathe(profile, "stone_cream")
        for side in [-1, 1]:
            sweep(
                [
                    (side * (0.135 + 0.13 * math.sin(math.pi * t / 24)), 0, 0.87 - 0.30 * t / 24)
                    for t in range(25)
                ],
                0.032,
                "bronze",
                16,
            )
        ring(0, 0, 0.72, 0.204, 0.204, 0.012)
        for i in range(12):
            a = math.tau * i / 12
            rod(
                (0.267 * math.cos(a), 0.267 * math.sin(a), 0.34),
                (0.275 * math.cos(a), 0.275 * math.sin(a), 0.56),
                0.007,
                "bronze",
                12,
            )

    start = len(w.VERTS)
    build()
    for i in range(start, len(w.VERTS)):
        a, b, c = w.VERTS[i]
        w.VERTS[i] = (x + a * scale, -y + b * scale, c * scale)


def amphoras():
    amphora(-0.36, 0, 1.10)
    amphora(0.32, 0.12, 0.77)


def barrel():
    for i in range(18):
        a, b = math.tau * (i + 0.02) / 18, math.tau * (i + 0.98) / 18
        levels = [(0.32, 0.02), (0.36, 0.18), (0.395, 0.48), (0.36, 0.80), (0.32, 0.98)]
        points = []
        for r, z in levels:
            points += [
                (r * math.cos(a), r * math.sin(a), z),
                (r * math.cos(b), r * math.sin(b), z),
                ((r - 0.045) * math.cos(b), (r - 0.045) * math.sin(b), z),
                ((r - 0.045) * math.cos(a), (r - 0.045) * math.sin(a), z),
            ]
        faces = [(3, 2, 1, 0), (16, 17, 18, 19)]
        for k in range(4):
            for j in range(4):
                faces.append(
                    (4 * k + j, 4 * k + (j + 1) % 4, 4 * (k + 1) + (j + 1) % 4, 4 * (k + 1) + j)
                )
        w.solid(points, faces, "wood", bevel=0.004)
    for z, r in [(0.11, 0.351), (0.29, 0.384), (0.70, 0.384), (0.89, 0.351)]:
        lathe(
            [(r - 0.013, 0), (r + 0.014, 0), (r + 0.014, 0.055), (r - 0.013, 0.055)],
            "dark_metal",
            position=(0, 0, z),
        )
        for i in range(9):
            a = math.tau * i / 9
            rod(
                (r * math.cos(a), r * math.sin(a), z + 0.025),
                ((r + 0.021) * math.cos(a), (r + 0.021) * math.sin(a), z + 0.025),
                0.010,
                "bronze",
                12,
            )
    lathe([(0.305, 0), (0.305, 0.04)], "wood", position=(0, 0, 0.02))
    lathe([(0.305, 0), (0.305, 0.04)], "wood", position=(0, 0, 0.94))
    lathe([(0.04, 0), (0.04, 0.014)], "bronze", position=(0.14, 0.06, 0.98))


def crate(x, y, z, width=0.78, height=0.70):
    depth = width * 0.80
    for side in [-1, 1]:
        plank_panel(x, y + side * depth / 2, z + 0.03, width, 0.055, height, 5)
        transform(
            lambda: plank_panel(0, 0, 0, depth, 0.055, height, 4),
            (x + side * width / 2, y, z + 0.03),
            angle=math.pi / 2,
        )
        for h in [0.06, height - 0.11]:
            block(x, y + side * (depth / 2 + 0.035), z + h, width + 0.09, 0.055, 0.07)
        rod(
            (x - width * 0.44, y + side * (depth / 2 + 0.065), z + 0.14),
            (x + width * 0.44, y + side * (depth / 2 + 0.065), z + height - 0.05),
            0.025,
            "wood",
        )
    plank_panel(x, y, z + height, width, depth, 0.045, 5)
    plank_panel(x, y, z, width, depth, 0.04, 5)
    for xx in [-width / 2, width / 2]:
        for yy in [-depth / 2, depth / 2]:
            block(x + xx, y + yy, z, 0.055, 0.055, height + 0.05, "dark_metal")


def crates():
    crate(-0.40, 0, 0)
    crate(0.45, 0.11, 0, 0.60, 0.51)
    crate(-0.40, 0, 0.75, 0.56, 0.47)


def ropes():
    for layer in range(3):
        for turn in range(3):
            radius = 0.20 + turn * 0.045
            sweep(
                [
                    (
                        radius * math.cos(j * math.tau / 96),
                        radius * math.sin(j * math.tau / 96),
                        0.035 + layer * 0.048 + 0.006 * math.sin(j * math.tau * 3 / 96),
                    )
                    for j in range(97)
                ],
                0.023,
                "wood",
                12,
            )
    sweep([(0.30 + i * 0.013, 0.06 * math.sin(i * 0.11), 0.024) for i in range(50)], 0.021, "wood")
    for i in range(10):
        ring(0.32 + i * 0.045, 0, 0.025, 0.027, 0.023, 0.002, "bronze", "x")


def wheel(x, y, z):
    def build():
        lathe([(0.26, 0), (0.31, 0), (0.31, 0.095), (0.26, 0.095)], "wood")
        lathe([(0.306, -0.004), (0.325, 0), (0.325, 0.095), (0.306, 0.10)], "dark_metal")
        lathe([(0.073, -0.025), (0.073, 0.14)], "wood")
        for i in range(10):
            a = math.tau * i / 10
            rod(
                (0.05 * math.cos(a), 0.05 * math.sin(a), 0.048),
                (0.275 * math.cos(a), 0.275 * math.sin(a), 0.048),
                0.018,
                "wood",
            )
        lathe([(0.050, 0.14), (0.05, 0.16)], "bronze")

    transform(build, (x, y, z), "y", math.pi / 2)


def cart():
    for x in [-0.56, 0.56]:
        for y in [-0.43, 0.43]:
            wheel(x, y, 0.325)
    for y in [-0.43, 0.43]:
        rod((-0.62, y, 0.325), (0.62, y, 0.325), 0.032)
    plank_panel(0, 0, 0.41, 1.05, 1.28, 0.08, 7)
    for x in [-0.49, 0.49]:
        for y in [-0.59, 0.59]:
            block(x, y, 0.43, 0.06, 0.06, 0.57)
        for z in [0.61, 0.80]:
            block(x, 0, z, 0.055, 1.26, 0.12)
    for y in [-0.59, 0.59]:
        for z in [0.61, 0.80]:
            block(0, y, z, 1.04, 0.055, 0.12)
    for x in [-0.37, 0.37]:
        rod((x, 0.60, 0.55), (x, 1.40, 0.88), 0.036, "wood")
    rod((-0.37, 1.4, 0.88), (0.37, 1.4, 0.88), 0.034, "wood")
    transform(barrel, (-0.20, -0.17, 0.49))
    rod((0.34, -0.40, 0.51), (0.34, 0.32, 1.53), 0.018, "wood")
    for i in range(9):
        rod(
            (0.34 + (i - 4) * 0.017, 0.32, 1.48),
            (0.34 + (i - 4) * 0.022, 0.38, 1.62),
            0.007,
            "wood",
        )


def brazier():
    lathe([(0.35, 0), (0.36, 0.07), (0.27, 0.12), (0.19, 0.18)], "stone_cream")
    lathe([(0.15, 0.18), (0.11, 0.28), (0.085, 0.84), (0.14, 0.92), (0.18, 0.96)])
    lathe(
        [
            (0.16, 0.91),
            (0.29, 1.01),
            (0.37, 1.18),
            (0.39, 1.26),
            (0.355, 1.26),
            (0.325, 1.18),
            (0.25, 1.04),
            (0.13, 0.96),
        ],
        "dark_metal",
    )
    ring(0, 0, 1.25, 0.39, 0.39, 0.025)
    for i in range(12):
        a = math.tau * i / 12
        sweep(
            [
                (r * math.cos(a), r * math.sin(a), z)
                for r, z in [(0.18, 0.94), (0.26, 1.03), (0.365, 1.20)]
            ],
            0.012,
            "bronze",
        )
    for i in range(5):
        transform(lambda: rod((-0.18, 0, 1.09), (0.18, 0, 1.09), 0.027, "wood"), angle=i * 0.8)


def wall_lamp():
    block(0, -0.11, 0, 0.22, 0.06, 0.78, "bronze")
    for z in [0.12, 0.68]:
        ring(0, -0.145, z, 0.065, 0.065, 0.014, axis="y")
    sweep([(0, -0.08, 0.22), (0, 0.10, 0.20), (0, 0.32, 0.32), (0, 0.34, 0.63)], 0.033, "bronze")
    lathe([(0.17, 0), (0.19, 0.055), (0.14, 0.08)], position=(0, 0.34, 0.53))
    for i in range(6):
        a = math.tau * i / 6
        rod(
            (0.16 * math.cos(a), 0.34 + 0.16 * math.sin(a), 0.60),
            (0.14 * math.cos(a), 0.34 + 0.14 * math.sin(a), 0.97),
            0.012,
            "bronze",
        )
    lathe(
        [(0.19, 0), (0.19, 0.04), (0.13, 0.09), (0.025, 0.19)], "bronze", position=(0, 0.34, 0.97)
    )
    lathe([(0.045, 0), (0.045, 0.23)], "stone_cream", position=(0, 0.34, 0.61))


def armchair():
    for x in [-0.29, 0.29]:
        for y in [-0.24, 0.24]:
            lathe(
                [(0.052, 0), (0.06, 0.035), (0.038, 0.32), (0.065, 0.39)],
                "wood",
                position=(x, y, 0),
            )
            ring(x, y, 0.11, 0.045, 0.045, 0.010)
    block(0, 0, 0.38, 0.67, 0.63, 0.08)
    block(0, 0, 0.46, 0.58, 0.55, 0.11, "burgundy")
    block(0, 0.27, 0.51, 0.58, 0.085, 0.66, "burgundy")
    for x in [-0.31, 0.31]:
        lathe([(0.036, 0), (0.041, 0.10), (0.025, 0.30)], "wood", position=(x, -0.22, 0.48))
        block(x, 0, 0.79, 0.085, 0.61, 0.055)
        block(x, 0.30, 0.46, 0.075, 0.075, 0.80)
        lathe([(0.049, 0), (0.065, 0.022), (0.035, 0.065)], position=(x, 0.30, 1.26))
    block(0, 0.29, 1.18, 0.68, 0.10, 0.08, "bronze")
    for x in [-0.18, 0, 0.18]:
        rivets(x, x, 0.219, 0.77, 1)
        rivets(x, x, 0.219, 1.01, 1)


def table():
    for x in [-0.59, 0.59]:
        for y in [-0.30, 0.30]:
            lathe(
                [(0.06, 0), (0.065, 0.08), (0.04, 0.58), (0.08, 0.69)], "wood", position=(x, y, 0)
            )
    block(0, 0, 0.14, 1.25, 0.065, 0.095)
    plank_panel(0, 0, 0.70, 1.5, 0.83, 0.095, 8)
    block(0.04, 0, 0.796, 0.38, 0.86, 0.013, "burgundy")
    for x in [-0.39, 0.39]:
        lathe(
            [(0.12, 0), (0.145, 0.012), (0.15, 0.035), (0.13, 0.045)],
            "marble_white",
            position=(x, 0, 0.80),
        )
        lathe(
            [
                (0.053, 0),
                (0.06, 0.015),
                (0.02, 0.085),
                (0.06, 0.13),
                (0.067, 0.19),
                (0.055, 0.19),
                (0.047, 0.14),
                (0.012, 0.10),
            ],
            position=(x, -0.25, 0.80),
            sides=48,
        )
    lathe(
        [
            (0.075, 0),
            (0.11, 0.09),
            (0.08, 0.23),
            (0.042, 0.28),
            (0.065, 0.31),
            (0.045, 0.31),
            (0.028, 0.27),
            (0.06, 0.20),
            (0.08, 0.08),
        ],
        "bronze",
        position=(0.08, 0.16, 0.815),
    )
    sweep(
        [(0.15, 0.16, 1.07), (0.26, 0.16, 1.04), (0.26, 0.16, 0.93), (0.17, 0.16, 0.89)],
        0.012,
        "bronze",
    )


def lectern():
    lathe([(0.28, 0), (0.29, 0.06), (0.20, 0.13), (0.10, 0.19)], "stone_cream")
    lathe([(0.12, 0.19), (0.09, 0.29), (0.065, 0.91), (0.11, 0.99)], "wood")
    transform(lambda: block(0, 0, 0, 0.65, 0.50, 0.055), (0, 0, 1.0), "x", 0.27)
    rod((-0.31, 0.24, 1.12), (0.31, 0.24, 1.12), 0.019, "bronze")
    block(-0.10, 0, 1.05, 0.24, 0.31, 0.028, "burgundy")
    block(0.14, 0, 1.05, 0.24, 0.31, 0.026, "stone_cream")
    ring(0, 0, 0.37, 0.085, 0.085, 0.012)


def pallet():
    for x in [-0.78, 0.78]:
        for y in [-0.31, 0.31]:
            block(x, y, 0, 0.10, 0.10, 0.20)
    for y in [-0.31, 0.31]:
        block(0, y, 0.13, 1.84, 0.10, 0.10)
    for i in range(8):
        block(-0.80 + i * 0.23, 0, 0.19, 0.21, 0.65, 0.065)
    block(0, 0, 0.25, 1.83, 0.65, 0.09, "wood")
    block(-0.61, 0, 0.34, 0.34, 0.54, 0.11, "burgundy")
    for i in range(14):
        y = -0.31 + i * 0.045
        sweep(
            [(-0.80, y, 0.345), (-0.25, y, 0.36 + 0.008 * math.sin(i)), (0.75, y, 0.35)],
            0.005,
            "wood",
            8,
        )
    block(0.50, 0, 0.35, 0.45, 0.67, 0.026, "burgundy")


def chain_run(x, y, z, count, hanging=True):
    for i in range(count):
        ring(
            x if hanging else x + i * 0.075,
            y,
            z - i * 0.075 if hanging else z,
            0.047,
            0.031,
            0.008,
            "dark_metal",
            "y" if i % 2 == 0 else "x",
        )


def chains():
    block(0, 0, 0.025, 0.60, 0.17, 0.09, "dark_metal")
    for x in [-0.22, 0.22]:
        ring(x, 0, 0.14, 0.065, 0.065, 0.016, "dark_metal", "y")
        # Chain coiled on ground: independent solid links with open interiors.
        for i in range(28):
            a = i * math.tau / 28
            ring(
                x + 0.19 * math.cos(a),
                0.24 + 0.17 * math.sin(a),
                0.022 + 0.012 * (i % 2),
                0.044,
                0.023,
                0.006,
                "dark_metal",
                "z" if i % 2 else "y",
            )
        ring(x, 0.56, 0.08, 0.084, 0.062, 0.018, "dark_metal", "y")


def sarcophagus():
    # Neutral architectural moulding, no religious/imperial emblem.
    for z, width, depth, height in [
        (0, 2.28, 0.98, 0.12),
        (0.12, 2.16, 0.88, 0.13),
        (0.25, 2.05, 0.77, 0.49),
        (0.74, 2.20, 0.91, 0.10),
        (0.84, 2.28, 0.98, 0.08),
    ]:
        block(0, 0, z, width, depth, height, "stone_cream")
    w.prism([(-1.10, 0.91), (1.10, 0.91), (0.95, 1.08), (-0.95, 1.08)], -0.45, 0.45, "stone_cream")
    for side in [-1, 1]:
        block(0, side * 0.40, 0.35, 1.53, 0.035, 0.25, "marble_white")
        for x in [-0.74, 0.74]:
            ring(x, side * 0.443, 0.50, 0.065, 0.045, 0.012, "bronze", "y")
    for x in [-1.04, 1.04]:
        block(x, 0, 0.35, 0.028, 0.53, 0.25, "marble_white")


def practice_stand():
    for a in [0, math.pi / 2]:
        transform(lambda: block(0, 0, 0, 0.95, 0.12, 0.11), angle=a)
    lathe([(0.085, 0.10), (0.07, 1.45)], "wood")
    rod((-0.47, 0, 1.08), (0.47, 0, 1.08), 0.045, "wood")
    for i in range(36):
        ring(0, 0, 0.54 + i * 0.019, 0.18 + 0.025 * math.sin(i * math.pi / 36), 0.14, 0.016, "wood")
    lathe([(0.105, 0), (0.14, 0.04), (0.14, 0.20), (0.095, 0.24)], "wood", position=(0, 0, 1.28))


def training_staves():
    for j, x in enumerate((-0.25, 0, 0.25)):
        rod((x, 0, 0.045), (x + 0.075, 0.10, 2.03 - j * 0.09), 0.043, "wood", 20)
        rod(
            (x + 0.058, 0.074, 1.52 - j * 0.09),
            (x + 0.068, 0.089, 1.82 - j * 0.09),
            0.051,
            "mortar",
            20,
        )


def folded_linen():
    for layer in range(4):
        block(0.015 * layer, 0, 0.068 * layer, 0.61 - 0.016 * layer, 0.38, 0.060, "mortar")
        # Each folded edge is a continuous physical round hem.
        rod(
            (-0.28 + 0.014 * layer, 0.182, 0.026 + 0.068 * layer),
            (0.29 + 0.002 * layer, 0.182, 0.026 + 0.068 * layer),
            0.009,
            "mortar",
            12,
        )


def service_amphoras():
    start = len(w.FACE_MATERIALS)
    amphoras()
    # Exact original jar envelopes and placement; all vessel parts become clay.
    for i in range(start, len(w.FACE_MATERIALS)):
        w.FACE_MATERIALS[i] = w.NAMES.index("burgundy")
        w.FACE_COLORS[i] = (1, 1, 1, 1)
        w.FACE_SEEDS[i] = 1


def sculpted_armchair():
    start = len(w.VERTS)
    sculpt.chair(0, 0, 0, False)
    for i in range(start, len(w.VERTS)):
        x, north, z = w.VERTS[i]
        # Inside the existing chair footprint; authored cloth and real back frame.
        w.VERTS[i] = (x * 0.79, north * 0.86, z * 0.92)


def sculpted_table():
    table()
    # Broad turned edge below the same tabletop, and a carved front apron.
    for x in (-0.59, 0.59):
        lathe(
            [(0.065, 0), (0.079, 0.027), (0.079, 0.065), (0.065, 0.092)],
            "wood",
            position=(x, 0, 0.57),
        )
    for x in (-0.41, 0, 0.41):
        # Geometric carving, no emblem or glyph.
        w.prism([(x - 0.07, 0.55), (x, 0.62), (x + 0.07, 0.55), (x, 0.48)], -0.37, -0.33, "wood")


def loge_lantern():
    start = len(w.VERTS)
    sculpt.lamp(0, 0, 0, grand=True)
    for i in range(start, len(w.VERTS)):
        x, north, z = w.VERTS[i]
        w.VERTS[i] = (x * 0.48, north * 0.48, z)


def velum_winch():
    """Low terrace winding gear; the highest point stays below local Z1.10."""
    block(0, 0, 0, 0.92, 0.65, 0.14, "wood")
    for x in (-0.39, 0.39):
        block(x, 0, 0.14, 0.12, 0.52, 0.60, "wood")
        block(x, 0, 0.73, 0.17, 0.56, 0.075, "dark_metal")
    transform(
        lambda: lathe([(0.16, -0.35), (0.19, -0.32), (0.19, 0.32), (0.16, 0.35)], "wood"),
        (0, 0, 0.56),
        "y",
        math.pi / 2,
    )
    rod((-0.49, 0, 0.56), (0.49, 0, 0.56), 0.052, "dark_metal", 24)
    for x in (-0.30, 0.30):
        transform(
            lambda: lathe([(0.17, 0), (0.23, 0.02), (0.23, 0.06), (0.17, 0.08)], "dark_metal"),
            (x, 0, 0.56),
            "y",
            math.pi / 2,
        )
    for x in (-0.23, -0.17, -0.11, -0.05, 0.01, 0.07, 0.13, 0.19):
        ring(x, 0, 0.56, 0.193, 0.193, 0.021, "wood", "x")
    rod((0.48, 0, 0.56), (0.48, 0.24, 0.78), 0.034, "dark_metal")
    rod((0.48, 0.24, 0.78), (0.48, 0.38, 0.78), 0.047, "wood")
    for x in (-0.34, 0.34):
        for y in (-0.22, 0.22):
            lathe([(0.033, 0), (0.043, 0.024)], "dark_metal", 24, (x, y, 0.14))


def velum_anchor():
    block(0, 0, 0, 0.62, 0.57, 0.14, "stone_cream")
    block(0, 0, 0.14, 0.43, 0.40, 0.19, "marble_white")
    block(0, 0, 0.33, 0.28, 0.18, 0.055, "dark_metal")
    ring(0, 0, 0.53, 0.17, 0.19, 0.033, "dark_metal", "y")
    for x in (-0.20, 0.20):
        lathe([(0.030, 0), (0.038, 0.02)], "dark_metal", 24, (x, 0, 0.335))


def forged_grille_bar(x, z, height):
    start = len(w.FACES)
    lathe(
        [(0.019, 0), (0.016, 0.055), (0.016, height - 0.055), (0.019, height)],
        "dark_metal",
        sides=8,
        position=(x, 0, z),
    )
    w.FACE_SMOOTH[start:] = [False] * (len(w.FACES) - start)


def grille_panel(width, height=2.60, centre=0):
    """Closed forged members assembled into one repeatable grille module."""
    half = width / 2
    for x in (centre - half + 0.035, centre + half - 0.035):
        block(x, 0, 0, 0.070, 0.085, height, "dark_metal")
        for z in (0.14, 0.65, 1.78, height - 0.14):
            transform(
                lambda: lathe([(0.012, 0), (0.016, 0.009), (0.012, 0.016)], "dark_metal", sides=12),
                (x, 0.044, z),
                "x",
                -math.pi / 2,
            )
    for z in (0, 0.62, 1.75, height - 0.07):
        block(centre, 0, z, width, 0.085, 0.070, "dark_metal")
    count = max(2, math.ceil((width - 0.14) / 0.14))
    for j in range(1, count):
        x = centre - half + 0.070 + j * (width - 0.14) / count
        forged_grille_bar(x, 0.070, height - 0.14)
        for z in (0.62, 1.75):
            block(x, 0, z - 0.018, 0.047, 0.065, 0.104, "dark_metal")


def prison_cell_front():
    # Clear 1.10m door aperture, without a raised sill across that aperture.
    grille_panel(0.95, centre=-1.025)
    grille_panel(0.95, centre=1.025)
    block(0, 0, 2.50, 1.10, 0.085, 0.10, "dark_metal")


def prison_cell_return():
    # Standard centred straight panel: X[-1.2,1.2], Y0, no placement assumed.
    grille_panel(2.40)


def prison_cell_door_open():
    # Local origin is the left hinge; 105 degrees opens outward into +Y.
    def leaf():
        grille_panel(1.04, height=2.42, centre=0.52)
        for z in (0.30, 1.19, 2.10):
            lathe(
                [(0.026, 0), (0.032, 0.020), (0.032, 0.095), (0.026, 0.115)],
                "dark_metal",
                sides=16,
                position=(0.018, 0, z),
            )
        block(0.87, 0.059, 1.06, 0.13, 0.044, 0.25, "dark_metal")
        rod((0.90, 0.090, 1.18), (0.90, 0.090, 1.30), 0.017, "dark_metal", 12)

    transform(leaf, angle=math.radians(105))


def wash_fountain():
    # Wall datum Y0, basin into +Y; neutral service stone, no heraldic mask.
    block(0, 0.27, 0, 1.26, 0.54, 0.13, "stone_cream")
    block(0, 0.045, 0.13, 1.30, 0.090, 0.98, "stone_cream")
    block(0, 0.060, 1.11, 1.34, 0.120, 0.09, "stone_cream")
    for x in (-0.58, 0.58):
        block(x, 0.096, 0.19, 0.065, 0.030, 0.84, "stone_cream")
    start = len(w.VERTS)
    lathe(
        [
            (0.22, 0.13),
            (0.25, 0.24),
            (0.34, 0.37),
            (0.38, 0.54),
            (0.38, 0.61),
            (0.35, 0.63),
            (0.32, 0.63),
            (0.31, 0.45),
            (0.24, 0.31),
        ],
        "stone_cream",
        sides=64,
    )
    for i in range(start, len(w.VERTS)):
        x, north, z = w.VERTS[i]
        w.VERTS[i] = (x * 1.60, north * 0.73 - 0.30, z)
    start = len(w.VERTS)
    lathe([(0.313, 0.532), (0.313, 0.540)], "mortar", sides=64)
    for i in range(start, len(w.VERTS)):
        x, north, z = w.VERTS[i]
        w.VERTS[i] = (x * 1.60, north * 0.73 - 0.30, z)
    transform(
        lambda: lathe([(0.082, 0), (0.089, 0.022), (0.073, 0.031)], "dark_metal", sides=32),
        (0, 0.092, 0.95),
        "x",
        -math.pi / 2,
    )
    rod((0, 0.122, 0.95), (0, 0.31, 0.95), 0.032, "dark_metal", 20)
    rod((0, 0.31, 0.95), (0, 0.31, 0.86), 0.032, "dark_metal", 20)


KIT = [
    (
        "afp-weapon-rack",
        weapon_rack,
        ["vestiaires", "armurerie"],
        "Râtelier avec quatre épées et une lance, fers losangés, fixations bronze.",
    ),
    (
        "afp-shield-pair",
        shields,
        ["vestiaires", "armurerie", "entraînement"],
        "Deux boucliers sans emblème, bosses, bordures et poignées arrière.",
    ),
    (
        "afp-bench",
        bench,
        ["galerie", "vestiaires", "public"],
        "Banc à trois lames, pieds tournés, dossier et rivets.",
    ),
    (
        "afp-chest",
        chest,
        ["vestiaires", "loges", "stockage"],
        "Coffre cerclé avec couvercle cintré, serrures et poignées.",
    ),
    (
        "afp-amphora-pair",
        amphoras,
        ["galerie", "loges", "stockage"],
        "Deux amphores creuses, anses épaisses et bandes géométriques sobres.",
    ),
    (
        "afp-barrel",
        barrel,
        ["stockage", "entretien"],
        "Tonneau en dix-huit douelles galbées, quatre cercles rivetés.",
    ),
    (
        "afp-crate-stack",
        crates,
        ["stockage", "entretien"],
        "Trois caisses fermées, planches séparées et renforts obliques.",
    ),
    (
        "afp-rope-coil",
        ropes,
        ["entretien", "stockage"],
        "Cordage continu en neuf tours et extrémité ferrée.",
    ),
    (
        "afp-maintenance-cart",
        cart,
        ["entretien", "services"],
        "Chariot à quatre roues à rayons, ridelles, tonneau et balai.",
    ),
    (
        "afp-brazier",
        brazier,
        ["galerie", "arène", "sous-sol"],
        "Brasero à vasque intérieure, nervures bronze et bûches; feu géré par moteur.",
    ),
    (
        "afp-wall-lamp",
        wall_lamp,
        ["galerie", "loges", "sous-sol"],
        "Applique ajourée, support courbe, coupe et capot; lumière gérée par moteur.",
    ),
    (
        "afp-loge-chair",
        armchair,
        ["loges", "administration"],
        "Fauteuil bourgogne capitonné, bois tourné et bronze.",
    ),
    (
        "afp-loge-table",
        table,
        ["loges", "administration"],
        "Table avec chemin bourgogne, deux coupes, vaisselle et carafe creuse.",
    ),
    (
        "afp-lectern",
        lectern,
        ["administration", "galerie"],
        "Pupitre autonome, pied mouluré et registre sans texte ni emblème.",
    ),
    (
        "afp-pallet",
        pallet,
        ["prison", "services"],
        "Paillasse sur châssis de bois, coussin et couverture bourgogne.",
    ),
    (
        "afp-chain-set",
        chains,
        ["prison", "stockage"],
        "Deux chaînes à maillons ouverts, anneaux et menottes neutres au sol.",
    ),
    (
        "afp-neutral-sarcophagus",
        sarcophagus,
        ["catacombes"],
        "Sarcophage neutre, moulures, panneaux marbre et anneaux bronze.",
    ),
    (
        "afp-practice-stand",
        practice_stand,
        ["entraînement", "vestiaires"],
        "Poteau d'entraînement habillé de cordage, sans personnage.",
    ),
    (
        "afp-training-staves",
        training_staves,
        ["vestiaires", "entraînement"],
        "Trois bâtons d'entraînement à bouts émoussés, poignées de linge ; groupe de rangement.",
    ),
    (
        "afp-folded-linen",
        folded_linen,
        ["vestiaires", "services"],
        "Quatre linges pliés avec ourlets en vrai volume, à poser sur un banc existant.",
    ),
    (
        "afp-service-amphora-pair",
        service_amphoras,
        ["vestiaires", "catacombes", "stockage"],
        "Amphores utilitaires en terre cuite ; emprise exacte de la paire existante.",
    ),
    (
        "afp-loge-chair-sculpted",
        sculpted_armchair,
        ["loges"],
        "Fauteuil sculpté au gabarit existant, bois, velours à vrais plis et garnitures.",
    ),
    (
        "afp-loge-table-sculpted",
        sculpted_table,
        ["loges"],
        "Table existante enrichie de pieds tournés et d'une jupe gravée, coupes conservées.",
    ),
    (
        "afp-loge-lantern",
        loge_lantern,
        ["loges"],
        "Lanternon à socle de pierre, coupe et cage ; foyer défini dans sa fiche.",
    ),
    (
        "afp-velum-winch",
        velum_winch,
        ["terrasse", "entretien"],
        "Treuil bas de velum, tambour cordé, manivelle et platines ; aucune haute perche.",
    ),
    (
        "afp-velum-anchor",
        velum_anchor,
        ["terrasse"],
        "Ancrage bas de velum, socle mouluré et anneau fermé ; sommet sous un mètre.",
    ),
    (
        "afp-prison-cell-front",
        prison_cell_front,
        ["prison"],
        "Grille forgée de trois mètres, rivets, colliers et ouverture sans seuil de 1,10m.",
    ),
    (
        "afp-prison-cell-return",
        prison_cell_return,
        ["prison"],
        "Retour de cellule droit de 2,40m, cadre et barreaux forgés, raccords alignés.",
    ),
    (
        "afp-prison-cell-door-open",
        prison_cell_door_open,
        ["prison"],
        "Battant de 1,04m sur 2,42m, ouvert à 105 degrés vers +Y, origine à la charnière gauche.",
    ),
    (
        "afp-wash-fountain",
        wash_fountain,
        ["vestiaires"],
        "Fontaine de service neutre, bassin creux, dosseret sans masque, bec de fer et eau sombre.",
    ),
]

KIT.extend(nameplate_entries(w))


def export_prop(name, build, out, materials):
    """Export with material-preserving bevels, including wood/metal edge faces."""
    import bpy
    import bmesh

    for values in [
        w.VERTS,
        w.FACES,
        w.FACE_MATERIALS,
        w.FACE_SMOOTH,
        w.FACE_COLORS,
        w.FACE_SEEDS,
        w.FACE_BEVELS,
    ]:
        values.clear()
    before = w.SIMPLE_PARTS
    build()
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(w.VERTS, [], w.FACES)
    for material in materials:
        mesh.materials.append(material)
    for polygon, mi, smooth in zip(mesh.polygons, w.FACE_MATERIALS, w.FACE_SMOOTH):
        polygon.material_index = mi
        polygon.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    colors = [bm.faces.layers.float.new("tint_" + ch) for ch in "rgb"]
    seeds = bm.faces.layers.float.new("seedAlpha")
    widths = bm.faces.layers.float.new("bevelWidth")
    for face in bm.faces:
        for k, layer in enumerate(colors):
            face[layer] = w.FACE_COLORS[face.index][k]
        face[seeds] = w.FACE_SEEDS[face.index]
        face[widths] = w.FACE_BEVELS[face.index]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    groups = {}
    for edge in bm.edges:
        if edge.is_manifold and edge.calc_face_angle(0) > 0.42:
            key = (round(edge.link_faces[0][widths], 5), edge.link_faces[0].material_index)
            groups.setdefault(key, []).append(edge)
    for (width, mi), edges in sorted(groups.items()):
        result = bmesh.ops.bevel(
            bm,
            geom=edges,
            offset=width,
            segments=3,
            affect="EDGES",
            profile=0.5,
            clamp_overlap=True,
            material=mi,
        )
        for face in result["faces"]:
            face.material_index = mi
            if w.NAMES[mi] in ("stone_cream", "marble_white"):
                for layer in colors:
                    face[layer] = min(1, max(0.92, face[layer] * 1.07))
    remaining = set(bm.faces)
    while remaining:
        first = remaining.pop()
        component = [first]
        for face in component:
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.append(neighbor)
        stone = [
            f for f in component if w.NAMES[f.material_index] in ("stone_cream", "marble_white")
        ]
        if stone:
            counts = {}
            for face in stone:
                value = round(face[seeds], 7)
                counts[value] = counts.get(value, 0) + 1
            seed = max(counts, key=counts.get)
            for face in stone:
                face[seeds] = seed
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    for edge in bm.edges:
        edge.smooth = edge.is_manifold and edge.calc_face_angle(0) < math.radians(30)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    # Bevel clamps can leave zero-area triangles when cast to glTF float32.
    # Remove only these collapsed faces; meaningful surface geometry is retained.
    collapsed = []
    for face in bm.faces:
        a, b, c = [
            tuple(struct.unpack("<f", struct.pack("<f", coordinate))[0] for coordinate in vertex.co)
            for vertex in face.verts
        ]
        u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
        cross = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
        if sum(value * value for value in cross) < 1e-24:
            collapsed.append(face)
    bmesh.ops.delete(bm, geom=collapsed, context="FACES_ONLY")
    vertex_color = bm.loops.layers.float_color.new("COLOR_0")
    for face in bm.faces:
        stone = w.NAMES[face.material_index] in ("stone_cream", "marble_white")
        tint = tuple(face[layer] for layer in colors) + (face[seeds],) if stone else (1, 1, 1, 1)
        for loop in face.loops:
            loop[vertex_color] = tint
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    uv = mesh.uv_layers.new(name="UV0")
    for polygon in mesh.polygons:
        axis = max(range(3), key=lambda k: abs(polygon.normal[k]))
        axes = [k for k in range(3) if k != axis]
        for index in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[index].vertex_index].co
            uv.data[index].uv = (co[axes[0]] / 2, co[axes[1]] / 2)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(out / (name + ".glb")),
        export_format="GLB",
        use_selection=True,
        export_texcoords=True,
        export_normals=True,
        export_vertex_color="NAME",
        export_vertex_color_name="COLOR_0",
        export_materials="EXPORT",
        export_yup=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )
    mesh.calc_loop_triangles()
    w.PIECES.append(
        {
            "id": name,
            "file": name + ".glb",
            "materials": sorted({w.NAMES[p.material_index] for p in mesh.polygons}),
            "triangles": len(mesh.loop_triangles),
            "boundsBlender": [
                [round(min(v.co[k] for v in mesh.vertices), 4) for k in range(3)],
                [round(max(v.co[k] for v in mesh.vertices), 4) for k in range(3)],
            ],
            "assembledSimpleParts": w.SIMPLE_PARTS - before,
            "removedCollapsedBevelTriangles": len(collapsed),
        }
    )
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    print(f"PRODUCED {name} {w.PIECES[-1]['triangles']} triangles", flush=True)


def blender_main(out, preview=False, only=None):
    out.mkdir(parents=True, exist_ok=True)
    w.PIECES.clear()
    w.OBJECTS.clear()
    materials = w.build_materials()
    previous = {}
    if only and (out / "manifest.json").is_file():
        previous = {
            item["id"]: item
            for item in json.loads((out / "manifest.json").read_text(encoding="utf-8"))["meshes"]
        }
    for name, build, zones, description in KIT:
        if only and name not in only and name in previous:
            w.PIECES.append(previous[name])
            continue

        def grounded_build(build=build, name=name):
            start = len(w.VERTS)
            build()
            ground = min(p[2] for p in w.VERTS[start:])
            turn_to_south = name in {
                "afp-weapon-rack",
                "afp-shield-pair",
                "afp-bench",
                "afp-chest",
                "afp-loge-chair",
                "afp-loge-table",
                "afp-loge-table-sculpted",
                "afp-lectern",
            }
            for k in range(start, len(w.VERTS)):
                x, y, z = w.VERTS[k]
                w.VERTS[k] = (-x if turn_to_south else x, -y if turn_to_south else y, z - ground)

        export_prop(name, grounded_build, out, materials)
        item = w.PIECES[-1]
        low, high = item.pop("boundsBlender")
        item["bounds"] = [[low[0], -high[1], low[2]], [high[0], -low[1], high[2]]]
        item["dimensions"] = [round(high[k] - low[k], 4) for k in range(3)]
        item["origin"] = [0, 0, 0]
        item["suggestedZones"] = zones
        item["description"] = description
        item["placementHints"] = {
            "keepOutOfWalkingRoute": True,
            "front": "+Y south",
            "groundOffset": round(-low[2], 4),
        }
        if name == "afp-prison-cell-front":
            item["placementHints"].update(
                doorOpeningX=[-0.55, 0.55], doorClearHeight=2.50, hingeLocalPosition=[-0.55, 0, 0]
            )
        elif name == "afp-prison-cell-return":
            item["placementHints"].update(nominalEndpoints=[[-1.20, 0, 0], [1.20, 0, 0]])
        elif name == "afp-prison-cell-door-open":
            item["placementHints"].update(
                originRole="left hinge",
                leafWidth=1.04,
                leafHeight=2.42,
                openAngleDegrees=105,
                opensToward="+Y exterior",
            )
        elif name == "afp-wash-fountain":
            item["placementHints"].update(
                wallDatumY=0, projectsToward="+Y", noHeraldicMask=True, decorativeOnly=True
            )
        item["sha256"] = hashlib.sha256((out / item["file"]).read_bytes()).hexdigest()
        if name in ["afp-brazier", "afp-wall-lamp", "afp-loge-lantern"]:
            item["light"] = {
                "color": "#ffc47d",
                "radius": 4.0 if name in ("afp-brazier", "afp-loge-lantern") else 3.0,
                "position": [
                    0,
                    0 if name in ("afp-brazier", "afp-loge-lantern") else 0.34,
                    1.70
                    if name == "afp-loge-lantern"
                    else (1.28 if name == "afp-brazier" else 0.85),
                ],
                "flicker": name == "afp-brazier",
                "always": name == "afp-loge-lantern",
                **(
                    {"candelas": 40, "flamePosition": [0, 0, 1.40], "flameScale": 0.52}
                    if name == "afp-loge-lantern"
                    else {}
                ),
            }
    manifest = {
        "format": "jadg-arena-fate-props",
        "version": 1,
        "generator": "scripts/assetsGeneration/build_arena_fate_props.py",
        "helperDependency": "scripts/assetsGeneration/arena_geometry.py",
        "coordinates": "metres; manifest X east, Y south, Z up; GLB X east, Y up, Z south",
        "dimensionsAxisOrder": ["width X", "depth Y", "height Z"],
        "uvMetersPerRepeat": 2.0,
        "materials": w.NAMES,
        "materialSource": "../arena-witness-materials/manifest.json",
        "materialOverrides": {
            "afp-service-amphora-pair": {"burgundy": "pottery"},
            "afp-folded-linen": {"mortar": "linen"},
            "afp-training-staves": {"mortar": "linen"},
            "afp-wash-fountain": {"stone_cream": "chamber_stone", "mortar": "wash_water"},
        },
        "sculptedWitness": "arena-wicked-witness, approved 2026-10-10",
        "meshes": w.PIECES,
        "previews": ["kit-overview.png"] if preview or (out / "kit-overview.png").is_file() else [],
        "qaReport": "generation-report.json",
        "notes": [
            "Approved painted material kit reused; no texture edits.",
            "All faces finished; props do not replace traversable architecture.",
            "No invented heraldry, religious symbol or imperial symbol; no characters.",
            "One logical mesh per GLB; material factors are fallback only, UE parent binds validated painted maps.",
            "Lamps expose source metadata; no emissive flame or baked lighting.",
        ],
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if preview:
        render_preview(out)


def render_preview(out):
    """Geometry QA sheet, with fallback materials, not an Unreal style approval."""
    import bpy
    from mathutils import Vector

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for i, (name, *_rest) in enumerate(KIT):
        bpy.ops.import_scene.gltf(filepath=str(out / (name + ".glb")))
        for obj in bpy.context.selected_objects:
            obj.location.x += (i % 5 - 2) * 3.0
            obj.location.y += (i // 5 - 1.5) * 3.0
    bpy.ops.object.camera_add(location=(13, -17, 17))
    camera = bpy.context.object
    camera.rotation_euler = (
        (Vector((0, 0, 0.4)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 20
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (0.14, 0.16, 0.19)
    scene.render.resolution_x = 1800
    scene.render.resolution_y = 1400
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out / "kit-overview.png")
    bpy.ops.render.render(write_still=True)


def read_glb(path):
    raw = path.read_bytes()
    assert raw[:4] == b"glTF" and struct.unpack_from("<I", raw, 4)[0] == 2
    size, kind = struct.unpack_from("<II", raw, 12)
    assert kind == 0x4E4F534A
    return json.loads(raw[20 : 20 + size]), raw


def accessor_values(doc, raw, index):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    offset = (
        28
        + struct.unpack_from("<I", raw, 12)[0]
        + view.get("byteOffset", 0)
        + accessor.get("byteOffset", 0)
    )
    code, width = {5126: ("f", 4), 5125: ("I", 4), 5123: ("H", 2), 5121: ("B", 1)}[
        accessor["componentType"]
    ]
    channels = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[accessor["type"]]
    stride = view.get("byteStride", channels * width)
    values = [
        struct.unpack_from("<" + code * channels, raw, offset + i * stride)
        for i in range(accessor["count"])
    ]
    if accessor.get("normalized"):
        denominator = {5123: 65535, 5121: 255}[accessor["componentType"]]
        values = [tuple(v / denominator for v in value) for value in values]
    assert all(math.isfinite(v) for value in values for v in value)
    return values


def verify(out):
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    results = []
    for item in manifest["meshes"]:
        doc, raw = read_glb(out / item["file"])
        assert len(doc["meshes"]) == 1, item["id"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        triangles = 0
        attributes = []
        max_normal_error, degenerate_triangles = 0.0, 0
        actual_materials = sorted(
            {doc["materials"][p["material"]]["name"] for p in doc["meshes"][0]["primitives"]}
        )
        assert actual_materials == item["materials"]
        for primitive in doc["meshes"][0]["primitives"]:
            assert primitive.get("mode", 4) == 4
            assert all(
                k in primitive["attributes"]
                for k in ["POSITION", "NORMAL", "TEXCOORD_0", "COLOR_0"]
            )
            triangles += doc["accessors"][primitive["indices"]]["count"] // 3
            attributes.append(sorted(primitive["attributes"]))
            data = {
                name: accessor_values(doc, raw, index)
                for name, index in primitive["attributes"].items()
            }
            assert all(0 <= v <= 1 for value in data["COLOR_0"] for v in value)
            max_normal_error = max(
                max_normal_error,
                max(abs(math.sqrt(sum(v * v for v in n)) - 1) for n in data["NORMAL"]),
            )
            indices = [value[0] for value in accessor_values(doc, raw, primitive["indices"])]
            assert max(indices) < len(data["POSITION"])
            for i in range(0, len(indices), 3):
                a, b, c = [data["POSITION"][indices[i + k]] for k in range(3)]
                u, v = [b[k] - a[k] for k in range(3)], [c[k] - a[k] for k in range(3)]
                cross = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0],
                ]
                degenerate_triangles += sum(x * x for x in cross) < 1e-24
        assert max_normal_error < 1e-5
        assert degenerate_triangles == 0, item["id"]
        assert triangles == item["triangles"]
        assert all(value > 0 for value in item["dimensions"])
        assert all(name in w.NAMES for name in item["materials"])
        results.append(
            {
                "id": item["id"],
                "triangles": triangles,
                "bytes": len(raw),
                "sha256": item["sha256"],
                "dimensions": item["dimensions"],
                "primitives": len(attributes),
                "requiredAttributesPresent": True,
                "normalLengthMaxError": max_normal_error,
                "colorRangeVerified": True,
                "degenerateTrianglesAt1eMinus12SquareMetres": degenerate_triangles,
                "exportedMaterialNames": actual_materials,
            }
        )
    report = {
        "generator": manifest["generator"],
        "status": "passed",
        "meshCount": len(results),
        "triangles": sum(x["triangles"] for x in results),
        "bytes": sum(x["bytes"] for x in results),
        "assembledSimpleParts": sum(x["assembledSimpleParts"] for x in manifest["meshes"]),
        "checks": [
            "One logical mesh per GLB",
            "Indexed triangles and POSITION/NORMAL/TEXCOORD_0/COLOR_0",
            "SHA256 exact",
            "Positive measured dimensions",
            "Eight approved semantic material names only",
        ],
        "meshes": results,
        "limits": [
            "Geometry QA only; full arena placement and gameplay clearance reviewed by level builder.",
            "Material factors in Blender preview are not the Unreal painted parent materials.",
        ],
    }
    (out / "generation-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"VERIFIED {len(results)} meshes; {report['triangles']} triangles; {report['assembledSimpleParts']} simple parts",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument(
        "--only", nargs="+", help="Regenerate selected/new meshes and retain other verified outputs"
    )
    parser.add_argument("--blender", type=Path, default=w.BLENDER)
    argv = sys.argv[sys.argv.index("--") + 1 :] if w.bpy and "--" in sys.argv else None
    args = parser.parse_args(argv)
    if args.verify:
        verify(args.output)
        return 0
    if w.bpy:
        blender_main(args.output, args.preview, args.only)
        verify(args.output)
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
    if args.only:
        command.extend(["--only", *args.only])
    return subprocess.run(command).returncode


if __name__ == "__main__":
    raise SystemExit(main())
