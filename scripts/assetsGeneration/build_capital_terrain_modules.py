#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Closed, metre-scale modules for the capital terrain laboratories.

Run with Blender --background --python this_file. Scripted geometry, no sourcebook
images, no downloaded masters edited. Imported/dressed by build_capital_terrain_labs.py.
"""

from pathlib import Path
import json
import math
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena_geometry as g

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Source/Elements/Assets/Built/capital-terrain-labs"


def paving(variant):
    # Shared 6m boundaries, fixed flat walking surface; genuine recessed joints.
    g.block(0, 0, 0, 6, 6, 0.14)
    for row in range(8):
        for col in range(8):
            x, y = -2.625 + col * 0.75, -2.625 + row * 0.75
            if variant == 1:
                width, depth = 0.71, 0.71
            elif variant == 2:
                width, depth = 0.715, 0.695
            else:
                width, depth = 0.695, 0.715
            g.dressed_block(x, y, 0.14, width, depth, 0.13, walkable=True)


def curb(corner=False):
    if not corner:
        for i in range(4):
            g.dressed_block(-1.125 + i * 0.75, 0, 0, 0.745, 0.45, 0.30, walkable=True)
    else:
        # An L with a single shared corner block, no intersecting full bars.
        for x, y in [(0, 0), (0.75, 0), (1.5, 0), (0, 0.75), (0, 1.5)]:
            g.dressed_block(x, y, 0, 0.745, 0.745, 0.30, walkable=True)


def retaining():
    g.block(0, 0, 0, 3, 1.5, 0.2)
    for row in range(6):
        for col in range(4):
            g.dressed_block(-1.125 + col * 0.75, 0, 0.2 + row * 0.45, 0.735, 1.2, 0.435)
    g.block(0, 0, 2.9, 3, 1.5, 0.1)


def ramp():
    g.solid(
        [
            (-3, -3, 0),
            (3, -3, 0),
            (3, 3, 0),
            (-3, 3, 0),
            (-3, -3, 0.3),
            (3, -3, 0.3),
            (3, 3, 1.8),
            (-3, 3, 1.8),
        ],
        [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)],
        bevel=0.015,
    )


def stairs():
    for i in range(10):
        g.block(0, -2.025 + 0.45 * i, 0, 3, 0.45, 0.15 * (i + 1))


def rock(variant):
    # An original harmonic rock volume, not texture-derived displacement.
    rings, sectors = 64, 128
    points, faces = [(0, 0, 0)], []
    for j in range(1, rings):
        phi = math.pi * j / rings
        for i in range(sectors):
            theta = math.tau * i / sectors
            scale = (
                1
                + 0.12 * math.sin(5 * theta + variant) * math.sin(phi) ** 2
                + 0.075 * math.cos(11 * theta + 7 * phi + variant)
            )
            points.append(
                (
                    1.5 * math.sin(phi) * math.cos(theta) * scale,
                    1.5 * math.sin(phi) * math.sin(theta) * scale,
                    1.2 * (1 - math.cos(phi)) * (1 + 0.08 * math.sin(3 * theta) * math.sin(phi)),
                )
            )
    points.append((0, 0, 2.4))
    top = len(points) - 1
    for i in range(sectors):
        ni = (i + 1) % sectors
        faces.append((0, 1 + ni, 1 + i))
        for j in range(rings - 2):
            a = 1 + j * sectors + i
            b = 1 + j * sectors + ni
            faces.append((a, b, b + sectors, a + sectors))
        a = 1 + (rings - 2) * sectors + i
        b = 1 + (rings - 2) * sectors + ni
        faces.append((a, b, top))
    g.solid(points, faces, bevel=0)
    g.FACE_SMOOTH[:] = [True] * len(g.FACES)


def soil_module(bank=False):
    nx, ny = 64, 128
    points = []
    faces = []
    for j in range(ny + 1):
        y = -6 + 12 * j / ny
        for i in range(nx + 1):
            x = -3 + 6 * i / nx
            envelope = math.sin(math.pi * i / nx) ** 2 * math.sin(math.pi * j / ny) ** 2
            h = 0.10 + (
                1.0 * (1 + math.sin(y / 6 * math.pi / 2)) / 2
                if bank
                else 0.08 * (1 + math.cos(x * math.tau / 0.75)) * envelope
            )
            points.append((x, y, h))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    boundary = (
        list(range(nx + 1))
        + [j * (nx + 1) + nx for j in range(1, ny + 1)]
        + [ny * (nx + 1) + i for i in range(nx - 1, -1, -1)]
        + [j * (nx + 1) for j in range(ny - 1, 0, -1)]
    )
    bottom = []
    for p in boundary:
        bottom.append(len(points))
        points.append((points[p][0], points[p][1], 0))
    for i, a in enumerate(boundary):
        ni = (i + 1) % len(boundary)
        faces.append((a, bottom[i], bottom[ni], boundary[ni]))
    faces.append(tuple(bottom[::-1]))
    g.solid(points, faces, bevel=0)
    g.FACE_SMOOTH[: nx * ny] = [True] * (nx * ny)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mats = g.build_materials()
    definitions = []
    for v in range(3):
        definitions.append((f"paves-{v}", lambda v=v: paving(v), "paving", [6, 6, 0.27]))
    for v in range(3):
        definitions.append((f"roche-{v}", lambda v=v: rock(v), "rock", [3.6, 3.6, 2.4]))
    definitions += [
        ("bordure", curb, "stone", [3, 0.45, 0.3]),
        ("bordure-angle", lambda: curb(True), "stone", [2.25, 2.25, 0.3]),
        ("soutenement", retaining, "stone", [3, 1.5, 3]),
        ("rampe", ramp, "stone", [6, 6, 1.8]),
        ("escalier", stairs, "stone", [3, 4.5, 1.5]),
        ("berge", lambda: soil_module(True), "sand", [6, 12, 1.1]),
        ("sillons", soil_module, "soil", [6, 12, 0.26]),
    ]
    for name, build, family, extent in definitions:
        g.export_piece(name, build, OUT, mats, clean_degenerate=True)
        g.PIECES[-1].update(
            surfaceFamily=family, designEnvelopeMetres=extent, pivot="ground", generator=__file__
        )
    (OUT / "manifest.json").write_text(
        json.dumps(
            {
                "generator": "scripts/assetsGeneration/build_capital_terrain_modules.py",
                "status": "prototype de terrain, non validé artistiquement",
                "pieces": g.PIECES,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf8",
    )


if __name__ == "__main__":
    main()
