#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Build the approved painted Arena as visitable modular architecture in Blender.

Source geometry: small closed stones, mouldings, arcades and stair profiles.
Outputs: Source/Elements/Assets/Built/arena-fate-modern/manifest.json and GLBs.
All positions are metres, X east / Y south / Z up, independently of logical storey.
The approved witness supplies geometry helpers and the engine supplies its materials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena_geometry as kit
import arena_fate_finishes as finishes
import arena_sculpted_geometry as sculpt
import arena_cavea as cavea
import arena_undercroft as undercroft

# The approved witness owns a separately loaded helper module on import. Bind
# its sculpting primitives to this generator's actual export buffers explicitly.
sculpt.g = kit

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/arena-fate-modern"
LEVELS = [
    {"name": name, "z": z}
    for name, z in [
        ("sable", 0),
        ("vestiaires-et-prison", -6),
        ("catacombes", -12),
        ("tribunes", 12),
        ("galerie-haute", 24),
        ("attique", 36),
        ("terrasse", 46.8),
    ]
]
DELEGATIONS = [
    "empire",
    "kolbjorn",
    "bennet",
    "seashores",
    "mage-tower",
    "kepesh",
    "storm-islands",
    "taii-maku",
    "tsvetan",
    "freelands",
    "sindile",
    "stravian",
    "yama",
]
OBJECTS = []


def polar(a, b, angle, z=0):
    return [a * math.cos(angle), b * math.sin(angle), z]


def wedge(ai, bi, ao, bo, lo, hi, bottom, top, material="stone_cream", segments=3):
    """Closed annular tile with real top, soffit and radial returns."""
    for i in range(segments):
        t0, t1 = lo + (hi - lo) * i / segments, lo + (hi - lo) * (i + 1) / segments
        corners = [polar(ai, bi, t0), polar(ao, bo, t0), polar(ao, bo, t1), polar(ai, bi, t1)]
        pts = [(p[0], p[1], z) for z in (bottom, top) for p in corners]
        kit.solid(
            pts,
            [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
            material,
            bevel=0.006,
        )


def ring(ai, bi, ao, bo, z, thickness=0.30, slots=False, material="marble_white", dressed=False):
    # 96 tiles share exact boundary coordinates; open south/north stair wells.
    for i in range(96):
        lo, hi = math.tau * i / 96, math.tau * (i + 1) / 96
        mid = (lo + hi) / 2
        if slots and abs(math.cos(mid)) < 0.115:
            continue
        if not dressed:
            wedge(ai, bi, ao, bo, lo, hi, z - thickness, z, material, 2)
            continue
        # Keep the exact original 192 straight boundary chords and shaft slots.
        wedge(ai, bi, ao, bo, lo, hi, z - thickness, z - 0.024, "mortar", 2)
        radial = max(1, math.ceil(max(ao - ai, bo - bi) / 0.78))
        for segment in range(2):
            a = lo + (hi - lo) * segment / 2
            b = lo + (hi - lo) * (segment + 1) / 2
            corners = [polar(ai, bi, a), polar(ao, bo, a), polar(ao, bo, b), polar(ai, bi, b)]

            def point(u, v, corners=corners):
                return tuple(
                    (1 - v) * ((1 - u) * corners[0][k] + u * corners[1][k])
                    + v * ((1 - u) * corners[3][k] + u * corners[2][k])
                    for k in (0, 1)
                )

            for r in range(radial):
                for t in range(4):
                    u0, u1 = r / radial, (r + 1) / radial
                    v0, v1 = t / 4, (t + 1) / 4
                    sculpt.slab(
                        [point(u0, v0), point(u1, v0), point(u1, v1), point(u0, v1)],
                        z,
                        thickness=0.11,
                        material=material,
                    )


def ring_collision(ai, bi, ao, bo, z=0, thickness=0.30, slots=False):
    """Closed architectural collision shell, authored from the exact ring chords.

    This is independent collision geometry, not a reduction of the visual mesh.
    Keep the same 96 slot decisions and the original 192 straight boundaries,
    flat walking top and actual floor soffit. Weld adjacent cells and omit their
    internal faces; expose radial caps only at the ends of real stair openings.
    Decorative stone bevels and joints remain in the untouched visual mesh.
    """
    active = set()
    for bay in range(96):
        mid = math.tau * (bay + 0.5) / 96
        if slots and abs(math.cos(mid)) < 0.115:
            continue
        active.update((2 * bay, 2 * bay + 1))
    points, faces, indices = [], [], {}

    def vertex(angle_index, outer, upper):
        key = (angle_index % 192, outer, upper)
        if key not in indices:
            angle = math.tau * key[0] / 192
            point = polar(
                ao if outer else ai, bo if outer else bi, angle, z if upper else z - thickness
            )
            indices[key] = len(points)
            points.append(tuple(point))
        return indices[key]

    for cell in sorted(active):
        ib0, ob0 = vertex(cell, False, False), vertex(cell, True, False)
        ib1, ob1 = vertex(cell + 1, False, False), vertex(cell + 1, True, False)
        it0, ot0 = vertex(cell, False, True), vertex(cell, True, True)
        it1, ot1 = vertex(cell + 1, False, True), vertex(cell + 1, True, True)
        faces.extend(
            ((ib0, ib1, ob1, ob0), (it0, ot0, ot1, it1), (ob0, ob1, ot1, ot0), (ib1, ib0, it0, it1))
        )
        if (cell - 1) % 192 not in active:
            faces.append((ib0, ob0, ot0, it0))
        if (cell + 1) % 192 not in active:
            faces.append((ob1, ib1, it1, ot1))
    kit.solid(points, faces, "mortar", bevel=0)


def tiled_rect(x0, x1, y0, y1, z, material="marble_white", tile=1.5):
    kit.block((x0 + x1) / 2, (y0 + y1) / 2, z - 0.32, x1 - x0, y1 - y0, 0.30, "mortar")
    nx, ny = max(1, math.ceil((x1 - x0) / tile)), max(1, math.ceil((y1 - y0) / tile))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            kit.block(
                x0 + (i + 0.5) * dx,
                y0 + (j + 0.5) * dy,
                z - 0.12,
                dx - 0.012,
                dy - 0.012,
                0.12,
                material,
            )


def transform_new(build, turn=0, dx=0, dy=0, dz=0):
    """Apply map rotation to newly authored vertices, before normals and bevels."""
    start = len(kit.VERTS)
    build()
    c, s = math.cos(math.radians(turn)), math.sin(math.radians(turn))
    for i in range(start, len(kit.VERTS)):
        x, north, z = kit.VERTS[i]
        y = -north
        kit.VERTS[i] = (c * x + s * y + dx, -(-s * x + c * y + dy), z + dz)


def attic():
    # Hollow windowed upper wall, using the 6 m bay convention of the arcade.
    for x0, x1 in [(-3, -1.05), (1.05, 3)]:
        kit.masonry(x0, x1, 0, 0, 9.6, 0.78, course=0.6, brick=1.05)
    kit.masonry(-1.05, 1.05, 0, 0, 2.8, 0.78, course=0.56)
    kit.masonry(-1.05, 1.05, 0, 6.1, 9.6, 0.78, course=0.7)
    for x in (-1.1, 1.1):
        kit.block(x, 0.03, 2.7, 0.16, 1.0, 3.6, "marble_white")
    kit.block(0, 0.03, 2.65, 2.4, 1.1, 0.18, "marble_white")
    kit.block(0, 0.03, 6.1, 2.4, 1.1, 0.22, "marble_white")
    kit.cornice(0, 0, 9.6, 6)
    kit.block(0, 0, 10.06, 6, 1.2, 0.74, "stone_cream")
    kit.block(0, 0, 10.8, 6, 0.66, 1.2, "marble_white")
    for x in (-2.6, 2.6):
        kit.block(x, 0.52, 0, 0.36, 0.25, 9.6, "marble_white")


def sand_disk():
    count = 192
    points = [
        tuple(polar(43, 27, math.tau * i / count, z)) for z in (-0.35, 0) for i in range(count)
    ]
    points.extend([(0, 0, -0.35), (0, 0, 0)])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.extend(
            [(2 * count, j, i), (2 * count + 1, count + i, count + j), (i, j, count + j, count + i)]
        )
    kit.solid(points, faces, "sand", bevel=0)


def vault_gable(radius, rise=1.5):
    # Close each curved end above the spring line with individually fitted blocks.
    steps = math.ceil(radius * 2 / 0.75)
    for i in range(steps):
        a, b = -radius + 2 * radius * i / steps, -radius + 2 * radius * (i + 1) / steps
        za, zb = (3.2 + rise * math.sqrt(max(0, 1 - (u / radius) ** 2)) for u in (a, b))
        kit.prism([(a, 3.19), (b, 3.19), (b, zb), (a, za)], -0.275, 0.275)


def room_walls(service=False):
    for a, b in [(-12, -1.8), (1.8, 12)]:
        kit.masonry(a, b, 9, 0, 3.2, 0.55, 0.53, 1.5)
    kit.arc(0, 9, 1.2, 1.8, 0.2, 0.62, segments=21)
    kit.masonry(-12, 12, -9, 0, 3.2, 0.55, 0.53, 1.5)

    def side(door=False):
        spans = [(-9, 5.8), (8.8, 9)] if door else [(-9, 9)]
        for a, b in spans:
            kit.masonry(a, b, 0, 0, 3.2, 0.55, 0.53, 1.5)
        if door:
            kit.arc(7.3, 0, 1.45, 1.5, 0.25, 0.6, segments=17)

    for x in (-12, 12):
        transform_new(lambda x=x: side(service and x > 0), 90, x, 0)
        transform_new(lambda: vault_gable(9), 90, x, 0)
    for x in (-8, 8):
        for y in (-7, 7):
            kit.column(x, y, 0, 3.2, 0.23)


def corridor_walls(catacomb=False):
    end, room_in, room_out, branch = (44, 10, 34, 25) if catacomb else (68, 12, 36, 28)
    for y in (-5, 5):
        spans = [(-end, -room_out), (-room_in, -6), (6, room_in), (room_out, end)]
        if catacomb and y < 0:
            spans[-1:] = [(room_out, 38), (42, end)]
        for a, b in spans:
            kit.masonry(a, b, y, 0, 3.2, 0.55, 0.53, 1.5)
    for x in (-end, end):
        transform_new(lambda: kit.masonry(-5, 5, 0, 0, 3.2, 0.55, 0.53, 1.5), 90, x)
        transform_new(lambda: vault_gable(5, 1.6), 90, x)
    for x in (-6, 6):
        for a, b in [(-branch, -5), (5, branch)]:
            transform_new(lambda a=a, b=b: kit.masonry(a, b, 0, 0, 3.2, 0.55, 0.53, 1.5), 90, x)
    kit.masonry(-6, 6, -branch, 0, 3.2, 0.55, 0.53, 1.5)
    for a, b in [(-6, 6)] if catacomb else [(-6, -2), (2, 6)]:
        kit.masonry(a, b, branch, 0, 3.2, 0.55, 0.53, 1.5)
    for y in (-branch, branch):
        transform_new(lambda: vault_gable(6), 0, 0, y)
    if catacomb:
        for x in (38, 42):
            transform_new(lambda: kit.masonry(5, 8, 0, 0, 3.2, 0.5, 0.53, 1.5), 90, x)


def branch_roofs(catacomb=False):
    end = 25 if catacomb else 28
    for a, b in [(-end, -5), (5, end)]:
        transform_new(lambda a=a, b=b: kit.vault(a, b, 0, 3.2, 6, rise=1.5), 90)
    # The descending flights retain open shafts; horizontal approaches have a real vault.
    spans = [(-44, -36), (36, 44)] if catacomb else [(-68, -61), (-49, -36), (36, 49), (61, 68)]
    for a, b in spans:
        kit.vault(a, b, 0, 3.2, 5, rise=1.6)


def loge():
    tiled_rect(-4, 4, -2.6, 2.6, 0)
    for x in (-3.5, 3.5):
        for y in (-2.0, 2.0):
            palace_column(x, y, 0, 4.1, 0.29)
        kit.rail(x, 0, 0, 4.0, axis="y")
    # Front balustrade; rear remains a real wide entrance from the promenade.
    kit.rail(0, -2.4, 0, 7)
    for x in (-2.8, 2.8):
        kit.rail(x, 2.4, 0, 1.4)


def loge_roof():
    kit.block(0, 0, 4.1, 8.4, 5.6, 0.25, "marble_white")
    # The existing 8.5 x 5.9 x 4.61 envelope is kept. A low pitched, overlapping
    # clay roof replaces the former textile-like flat burgundy block.
    for sign in (-1, 1):
        for row in range(8):
            near = row * 4.04 / 8
            far = min(4.04, near + 4.04 / 8 + 0.075)
            for column in range(11):
                y0 = -2.64 + column * 5.28 / 11
                y1 = min(2.64, y0 + 5.28 / 11 + 0.014)
                clay_tile(sign * near, sign * far, y0, y1, row)
    for column in range(11):
        y0 = -2.64 + column * 5.28 / 11
        y1 = -2.64 + (column + 1) * 5.28 / 11 - 0.009
        kit.rod((0, y0, 4.535), (0, y1, 4.535), 0.072, "dark_metal", 24)
    for y in (-2.7, 2.7):
        kit.cornice(0, y, 4.15, 8.5, 0.30)
    for x in (-4.07, 4.07):
        kit.block(x, 0, 4.35, 0.11, 5.35, 0.085, "dark_metal")


def fit_new_geometry(build, position=(0, 0, 0), scale=(1, 1, 1)):
    start = len(kit.VERTS)
    build()
    for i in range(start, len(kit.VERTS)):
        x, north, z = kit.VERTS[i]
        kit.VERTS[i] = (
            x * scale[0] + position[0],
            north * scale[1] - position[1],
            z * scale[2] + position[2],
        )


def palace_column(x, y, z, height=4.1, radius=0.29):
    # Same <=0.9 m square plinth as the original column: no aisle narrowing.
    fit_new_geometry(
        lambda: sculpt.sculpted_column(0, 0, 0, height, radius / 0.737),
        (x, y, z),
        (0.737, 0.737, 1),
    )


def palace_arcade():
    """One true 12m storey, at the original x=6 analytical bay pivot.

    The intrados keeps the validated stretched facade's opening (2.4/5.39*12
    spring and 2.1/5.39*12 rise), but stone courses, bases, shaft radii, capitals
    and cornice heights are authored at their real sizes, never stretched in Z.
    """
    spring = 2.4 * 12 / 5.39
    rise = 2.1 * 12 / 5.39
    for side in (-1, 1):
        x = 6 + side * 2.55
        kit.masonry(x - 0.45, x + 0.45, 0, 0, spring, 0.80, course=0.54, brick=0.95)
        palace_column(6 + side * 2.58, 0.55, 0, 10.64, 0.28)
        kit.block(x, 0, spring - 0.20, 1.0, 0.92, 0.20, "marble_white")
    for j in range(37):
        a = math.pi * j / 37 + 0.0014
        b = math.pi * (j + 1) / 37 - 0.0014
        profile = [
            (6 + 2.1 * math.cos(a), spring + rise * math.sin(a)),
            (6 + 2.5 * math.cos(a), spring + (rise + 0.42) * math.sin(a)),
            (6 + 2.5 * math.cos(b), spring + (rise + 0.42) * math.sin(b)),
            (6 + 2.1 * math.cos(b), spring + rise * math.sin(b)),
        ]
        kit.prism(profile, -0.41, 0.41)
    for side in (-1, 1):
        for j in range(15):
            a, b = j * 2.50 / 15, (j + 1) * 2.50 / 15
            profile = [
                (6 + side * a, spring + (rise + 0.42) * math.sqrt(max(0, 1 - (a / 2.5) ** 2))),
                (6 + side * b, spring + (rise + 0.42) * math.sqrt(max(0, 1 - (b / 2.5) ** 2))),
                (6 + side * b, 11.54),
                (6 + side * a, 11.54),
            ]
            kit.prism(profile, -0.37, 0.37)
    kit.block(6, 0.15, spring + rise - 0.21, 0.45, 1.02, 0.65, "marble_white")
    kit.cornice(6, 0, 11.54, 6.0)


def clay_tile(x0, x1, y0, y1, row):
    points = []
    nx, ny = 2, 6
    for layer in (0, 1):
        for i in range(nx + 1):
            u = i / nx
            x = x0 + (x1 - x0) * u
            for j in range(ny + 1):
                v = j / ny
                z = 4.36 + 0.135 * (1 - abs(x) / 4.04) + 0.004 * (8 - row)
                z += 0.019 * (2 * v - 1) ** 2 + 0.028 * layer
                points.append((x, y0 + (y1 - y0) * v, z))
    offset = (nx + 1) * (ny + 1)
    faces = []
    for layer in (0, 1):
        for i in range(nx):
            for j in range(ny):
                a = layer * offset + i * (ny + 1) + j
                faces.append((a, a + 1, a + ny + 2, a + ny + 1))
    for i in (0, nx):
        for j in range(ny):
            a = i * (ny + 1) + j
            faces.append((a, a + 1, a + 1 + offset, a + offset))
    for j in (0, ny):
        for i in range(nx):
            a = i * (ny + 1) + j
            faces.append((a, a + ny + 1, a + ny + 1 + offset, a + offset))
    kit.solid(points, faces, "dark_metal", bevel=0.003)
    kit.FACE_SMOOTH[-len(faces) :] = [True] * len(faces)


def loge_textiles():
    # Front faces inward (-Y); the original rear opening Y=+2.4 stays 4.2m clear.
    for y in (-2.0, 2.0):
        for a, b in ((-3.5, -1.15), (-1.15, 1.15), (1.15, 3.5)):
            sculpt.cloth((a + b) / 2, y, 3.99, b - a - 0.07, 0.37, 6, 0.16)
    for x in (-3.46, 3.46):
        sculpt.cloth(x, 1.98, 3.95, 0.42, 2.62, 4, 0.08)
    # Twelve delegations share a simpler, open colonnade.
    kit.block(0, -2.03, 3.90, 7.04, 0.23, 0.08, "marble_white")


def imperial_loge():
    loge()
    # Sculpted capitals/architrave carry the hierarchy without expanding the porch.
    sculpt.carved_frieze(0, -2.03, 3.27, 6.50)
    for x in (-3.5, 3.5):
        for y in (-2.0, 2.0):
            kit.turned(
                x, y, 3.02, [(0.29, 0), (0.34, 0.035), (0.34, 0.065), (0.29, 0.10)], "bronze", 48
            )


def imperial_loge_roof():
    kit.block(0, 0, 4.1, 8.4, 5.6, 0.25, "marble_white")
    kit.prism([(-4.04, 4.40), (4.04, 4.40), (0, 6.09)], -2.64, 2.64, "dark_metal")
    sx, sy, sz = 4.04 / 4.35, 5.28 / 6.73, 1.35
    for sign in (-1, 1):
        for row in range(8):
            near = row * 4.35 / 8
            far = min(4.35, near + 4.35 / 8 + 0.10)
            for column in range(11):
                y0 = -6.45 + column * 6.73 / 11
                y1 = min(0.28, y0 + 6.73 / 11 + 0.018)
                fit_new_geometry(
                    lambda near=near, far=far, y0=y0, y1=y1, row=row, sign=sign: sculpt.roof_tile(
                        -5 + sign * near, -5 + sign * far, y0, y1, 0.008 * (8 - row)
                    ),
                    (5 * sx, 3.085 * sy, 4.40 - 10 * sz),
                    (sx, sy, sz),
                )
    for column in range(11):
        y0 = -2.64 + column * 5.28 / 11
        y1 = -2.64 + (column + 1) * 5.28 / 11 - 0.010
        kit.rod((0, y0, 6.255), (0, y1, 6.255), 0.095, "dark_metal", 24)
    kit.prism([(-4.04, 4.47), (4.04, 4.47), (0, 6.27)], -2.64, -2.35, "stone_cream")
    for x in (-4.04, 4.04):
        kit.rod((x, -2.71, 4.47), (0, -2.71, 6.27), 0.075, "marble_white", 20)
        kit.block(x, 0, 4.40, 0.11, 5.35, 0.085, "dark_metal")
    for y in (-2.7, 2.7):
        kit.cornice(0, y, 4.15, 8.5, 0.30)
    # Additional white denticules remain under the original cornice envelope.
    for y in (-2.78, 2.78):
        for j in range(21):
            kit.block(-3.88 + j * 0.388, y, 4.18, 0.115, 0.22, 0.14, "marble_white")


def imperial_loge_textiles():
    loge_textiles()
    # Side panels reserve the same central rear entrance; no heraldry invented.
    for x in (-2.95, 2.95):
        sculpt.cloth(x, 2.36, 3.94, 0.68, 2.79, 6, 0.09)


def arcade_relief():
    for x in (3.45, 8.55):
        sculpt.lozenge(x, 0.69, 2.20, 0.31, 0.42, "marble_white", 0.09)
        sculpt.lozenge(x, 0.76, 2.20, 0.14, 0.18, "bronze", 0.045)
    for x in (4.30, 7.70):
        sculpt.lozenge(x, 0.43, 10.34, 0.32, 0.34, "marble_white", 0.10)
    sculpt.carved_frieze(6, 0.43, 10.75, 5.85)


def attic_relief():
    for x in (-2.02, 2.02):
        for z in (1.45, 4.45, 7.45):
            sculpt.lozenge(x, 0.59, z, 0.36, 0.48, "marble_white", 0.09)
    sculpt.carved_frieze(0, 0.38, 10.14, 5.84)


def statue_plinth():
    kit.block(0, 0, 0, 2.4, 2.4, 0.25, "marble_white")
    kit.block(0, 0, 0.25, 1.95, 1.95, 1.25, "marble_white")
    kit.block(0, 0, 1.5, 2.3, 2.3, 0.2, "marble_white")
    for yaw in (0, 90, 180, 270):

        def panel():
            kit.block(0, 1.0, 0.43, 1.43, 0.065, 0.73, "stone_cream")
            for x in (-0.75, 0.75):
                kit.block(x, 1.035, 0.39, 0.075, 0.07, 0.85, "marble_white")
            sculpt.lozenge(0, 1.061, 0.80, 0.35, 0.43, "bronze", 0.044)

        transform_new(panel, yaw)


def room_dado():
    for y in (-8.69, 8.69):
        for a, b in ((-11.65, -2.15), (2.15, 11.65)):
            kit.block((a + b) / 2, y, 0.08, b - a, 0.12, 0.26, "stone_cream")
            kit.block((a + b) / 2, y, 0.98, b - a, 0.10, 0.09, "stone_cream")
    # The +90 degree right return maps its doorway to local Y=-8.8..-5.8.
    # Keep the unchanged left dado and clear that negative-Y right-hand opening.
    for x in (-11.69, 11.69):
        kit.block(x, 1.60 if x > 0 else -1.60, 0.08, 0.12, 13.80, 0.26, "stone_cream")


def room_ribs():
    for x in (-9.2, -3.8, 3.8, 9.2):
        kit.vault(x - 0.10, x + 0.10, 0, 3.2, 8.74, thickness=0.15, rise=1.45)
        for y in (-8.73, 8.73):
            kit.block(x, y, 0.04, 0.43, 0.28, 3.09, "stone_cream")
            kit.block(x, y, 3.13, 0.56, 0.43, 0.10, "stone_cream")


def corridor_ribs(catacomb=False):
    # Original shaft/vault spans govern these placements. No rib crosses a hole.
    stations = (-43, -37, -8, 8, 37, 43) if catacomb else (-63.5, -42, -8, 8, 42, 63.5)
    for x in stations:
        kit.vault(x - 0.095, x + 0.095, 0, 3.2, 4.76, thickness=0.14, rise=1.56)
        for y in (-4.78, 4.78):
            kit.block(x, y, 0.02, 0.36, 0.20, 3.12, "stone_cream")
            kit.block(x, y, 3.14, 0.48, 0.34, 0.10, "stone_cream")


def room_backing(service=False):
    # Central masonry backing, continuous behind every dressed joint, never a door.
    for a, b in ((-12, -1.8), (1.8, 12)):
        kit.block((a + b) / 2, 9, 0, b - a, 0.035, 3.2, "mortar")
    kit.block(0, -9, 0, 24, 0.035, 3.2, "mortar")
    for x in (-12, 12):
        spans = ((-9, -8.8), (-5.8, 9)) if service and x > 0 else ((-9, 9),)
        for a, b in spans:
            kit.block(x, (a + b) / 2, 0, 0.035, b - a, 3.2, "mortar")
        continuous_gable(x, 9, 1.5)
    transform_new(lambda: continuous_vault(-0.016, 0.016, 0, 1.2, 1.885, 1.885), 90, 0, 9)
    if service:
        continuous_vault(11.984, 12.016, -7.3, 1.45, 1.605, 1.605)


def continuous_gable(x, radius, rise):
    profile = [(-radius, 3.2), (radius, 3.2)]
    profile += [
        (radius * math.cos(math.pi * j / 64), 3.2 + rise * math.sin(math.pi * j / 64))
        for j in range(1, 64)
    ]
    n = len(profile)
    points = [(px, y, z) for px in (x - 0.016, x + 0.016) for y, z in profile]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(j, (j + 1) % n, (j + 1) % n + n, j + n) for j in range(n)]
    kit.solid(points, faces, "mortar", bevel=0)


def continuous_vault(x0, x1, y, spring, radius, rise, thickness=0.030):
    count = 64
    profile = []
    for j in range(count + 1):
        a = math.pi * j / count
        profile.append((y + radius * math.cos(a), spring + rise * math.sin(a)))
    for j in range(count, -1, -1):
        a = math.pi * j / count
        profile.append(
            (y + (radius + thickness) * math.cos(a), spring + (rise + thickness) * math.sin(a))
        )
    n = len(profile)
    points = [(x, py, z) for x in (x0, x1) for py, z in profile]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(j, (j + 1) % n, (j + 1) % n + n, j + n) for j in range(n)]
    kit.solid(points, faces, "mortar", bevel=0)
    kit.FACE_SMOOTH[-len(faces) :] = [True] * len(faces)


def corridor_backing(catacomb=False):
    end, rin, rout, branch = (44, 10, 34, 25) if catacomb else (68, 12, 36, 28)
    for y in (-5, 5):
        spans = [(-end, -rout), (-rin, -6), (6, rin), (rout, end)]
        if catacomb and y < 0:
            spans[-1:] = [(rout, 38), (42, end)]
        for a, b in spans:
            kit.block((a + b) / 2, y, 0, b - a, 0.035, 3.2, "mortar")
    for x in (-end, end):
        kit.block(x, 0, 0, 0.035, 10, 3.2, "mortar")
        continuous_gable(x, 5, 1.6)
    for x in (-6, 6):
        for a, b in ((-branch, -5), (5, branch)):
            kit.block(x, (a + b) / 2, 0, 0.035, b - a, 3.2, "mortar")
    kit.block(0, -branch, 0, 12, 0.035, 3.2, "mortar")
    for a, b in ((-6, 6),) if catacomb else ((-6, -2), (2, 6)):
        kit.block((a + b) / 2, branch, 0, b - a, 0.035, 3.2, "mortar")
    for y in (-branch, branch):
        transform_new(lambda: continuous_gable(0, 6, 1.5), 90, 0, y)
    if catacomb:
        for x in (38, 42):
            kit.block(x, -6.5, 0, 0.035, 3, 3.2, "mortar")


def branch_vault_backing(catacomb=False):
    end = 25 if catacomb else 28
    for a, b in ((-end, -5), (5, end)):
        transform_new(lambda a=a, b=b: continuous_vault(a, b, 0, 3.2, 6.105, 1.605), 90)
    spans = ((-44, -36), (36, 44)) if catacomb else ((-68, -61), (-49, -36), (36, 49), (61, 68))
    for a, b in spans:
        continuous_vault(a, b, 0, 3.2, 5.105, 1.705)


def service_floor(crypt=False):
    # New joint rhythm; same exact [-12,12]x[-9,9] bounds and top Z=0.
    sculpt.paving(-12, 12, -9, 9, 0, "stone_cream" if crypt else "marble_white", 2 if crypt else 1)


def balustrade_relief():
    # Within the existing piers and 0.43m cap; walking side stays clear.
    for x in (-1.80, -0.90, 0, 0.90, 1.80):
        sculpt.lozenge(x, 0.16, 0.065, 0.19, 0.065, "bronze", 0.032)


def anchors():
    return {
        "e1": [-40, 0, 0],
        "e12": [40, 0, 0],
        "e4": [0, 0, 0],
        "e5": [-31, -5, 0],
        "e6": [25, 0, 0],
        "e7": [24, -12, 0],
        "e8": [24, -7, 0],
        "e9": [24, 6, 0],
        "e10": [24, 12, 0],
        "e11": [22, 0, 0],
        "e19": [-63, 0, -6],
        "e26": [63, 0, -6],
        "e21": [0, 21, -6],
        "e22": [0, 24, -6],
        "e23": [0, 25, -6],
        "e24": [40, -22, -6],
        "e32": [40, -7, -12],
        **{f"e{28 + k}": [-26 + 1.5 * k, -1, 0] for k in range(4)},
    }


def south_threshold_pylon():
    """A grounded side pilaster; no spanning member or additional walking deck."""
    kit.block(0, 0, 0, 1.14, 1.02, 0.18, "stone_cream")
    kit.block(0, -0.12, 0.18, 0.68, 0.45, 3.85, "stone_cream")
    palace_column(0, 0, 0, 4.1, 0.29)
    kit.cornice(0, 0, 4.1, 1.16, 0.76)
    for x in (-0.29, 0.29):
        kit.block(x, 0.30, 0.40, 0.07, 0.09, 2.82, "marble_white")


def south_threshold_side():
    # A short fitted return on each side. All its stones remain outside X+-9.6.
    kit.block(0, 0, 0, 2.60, 0.50, 0.16, "stone_cream")
    kit.masonry(-1.25, 1.25, 0, 0.16, 0.98, 0.36, course=0.41, brick=0.83)
    kit.cornice(0, 0, 0.98, 2.60, 0.35)
    for x in (-0.82, 0, 0.82):
        sculpt.lozenge(x, 0.26, 0.57, 0.25, 0.33, "marble_white", 0.065)


def south_threshold_textile():
    # Independent heavy cloth supported by the side pilaster, no invented emblem.
    sculpt.cloth(0, 0.41, 3.76, 0.68, 1.87, folds=6, swag=0.14)
    kit.rod((-0.38, 0.43, 3.81), (0.38, 0.43, 3.81), 0.034, "bronze", 16)


def ground_arcade_support():
    # Fitted lower piers occupy the existing jamb envelope, never the intrados.
    for x in (3.42, 8.58):
        kit.block(x, 0.48, 0, 0.94, 0.78, 0.24, "marble_white")
        for row in range(3):
            kit.dressed_block(x, 0.47, 0.24 + row * 0.39, 0.90, 0.69, 0.38)
        kit.block(x, 0.46, 1.41, 0.94, 0.75, 0.15, "marble_white")
        for row in range(7):
            kit.dressed_block(x, 0.44, 1.56 + row * 0.49, 0.85, 0.63, 0.475)


def metadata():
    # Les loges s'encastrent dans la media cavea (arena_cavea.LOGES), la loge imperiale sur le
    # grand axe, au-dessus de la porte de l'est.
    loges = [
        {"delegation": DELEGATIONS[i], "position": frame["position"], "yaw": frame["yaw"], "angle": frame["angle"]}
        for i, frame in enumerate(cavea.LOGES)
    ]
    route = [
        [-36, 0, 0],
        [-43, 0, 0],
        [-49, 0, 0],
        [-64, 0, -6],
        [-64, 3.5, -6],
        [-36, 3.5, -6],
        [-24, -2, -6],
        [-24, -12, -6],
        [-24, 0, -6],
        [-24, 12, -6],
        [0, 0, -6],
        [24, 12, -6],
        [24, 0, -6],
        [24, -14, -6],
        [34, -21.5, -6],
        [40, -22, -6],
        [40, -7.2, -12],
        [40, 0, -12],
        [22, 0, -12],
        [22, -14, -12],
        [22, 0, -12],
        [-22, 0, -12],
        [-22, -14, -12],
        [-22, 0, -12],
        [-22, 14, -12],
        [0, 0, -12],
        [22, 14, -12],
        [22, 0, -12],
        [40, 0, -12],
        [40, -7.2, -12],
        [40, -22, -6],
        [34, -21.5, -6],
        [24, 0, -6],
        [64, 3.5, -6],
        [64, 0, -6],
        [49, 0, 0],
        [43, 0, 0],
    ]
    # Le public quitte le passage de l'est par sa galerie laterale jusqu'au deambulatoire. Les
    # gradins se rejoignent par les vomitoires : aucun escalier ne se montre dans l'arene.
    route += [[49, 4.5, 0], [84, 4.5, 0], [89, 4.5, 0]]
    # Puis, par la premiere cage (diagonale sud-est), le tour des gradins : le deambulatoire du
    # sol, l'escalier en U, le vomitoire T1 jusqu'a la premiere praecinctio et sa loge, retour au
    # deambulatoire de 12 m, la volee de 12 a 24 m, le vomitoire de la seconde praecinctio.
    core = cavea.core_points()[0]
    loge = min(cavea.LOGES, key=lambda f: abs(f["angle"] - core["sector"] * math.tau / 16))
    route += [polar(88.5, 72.5, t, 0) for t in (0.15, 0.30)]
    route += [core[k] for k in ("ambulatory", "bottom_a", "landing", "top_b", "praecinctio_1")]
    route += [polar(65, 49, loge["angle"], 12), loge["position"], polar(65, 49, loge["angle"], 12)]
    route += [core["praecinctio_1"], core["top_b"], polar(88.5, 72.5, cavea.cores()[0]["t1"], 12)]
    route += [core[k] for k in ("ambulatory_12", "bottom_c", "top_c", "praecinctio_2", "ambulatory_24")]
    targets = [polar(89, 73, math.tau * i / 32, 0) for i in range(32) if i not in (8, 24)]
    # Les gradins desservis : les deux praecinctiones, les loges, les deambulatoires hauts.
    targets += [polar(65, 49, math.tau * (i + 0.5) / 16, 12) for i in range(16)]
    targets += [polar(82, 66, math.tau * (i + 0.5) / 16, 24) for i in range(16)]
    targets += [list(f["position"]) for f in cavea.LOGES]
    targets += [polar(90, 74, math.tau * (i + 0.5) / 16, z) for z in (12, 24) for i in range(16)]
    shots = [
        {"name": "ensemble", "target": [0, 0, 10], "yaw": 330, "pitch": 48, "distance": 220},
        {"name": "sable", "target": [-30, 0, 1.7], "yaw": 285, "pitch": 32, "distance": 18},
        {
            "name": "gradins",
            "target": polar(65, 49, 2.6, 12.5),
            "yaw": 335,
            "pitch": 40,
            "distance": 24,
        },
        {
            "name": "loge",
            "target": [*loges[0]["position"][:2], 13.5],
            "yaw": 110,
            "pitch": 35,
            "distance": 17,
        },
        {"name": "vestiaire", "target": [-24, -14, -4.3], "yaw": 10, "pitch": 35, "distance": 17},
        {"name": "prison", "target": [24, 14, -4.3], "yaw": 200, "pitch": 38, "distance": 18},
        {"name": "catacombes", "target": [22, -14, -10.3], "yaw": 20, "pitch": 38, "distance": 18},
        {"name": "facade", "target": [0, 69, 20], "yaw": 0, "pitch": 25, "distance": 80},
    ]
    return {
        "dimensions": {"width": 189, "depth": 156, "height": 48},
        "levels": LEVELS,
        "origin": [-102, -84],
        "width": 136,
        "height": 112,
        "entry": [-36, 0, 0],
        "entityPositions": anchors(),
        "loges": loges,
        "route": route,
        "navigationTargets": targets,
        "shots": shots,
        "lights": [],
        "approvedWitness": "Planning/versions/v0.1.0/v0.0.4-lieux-de-la-demo/annexes/LOT-106/wicked-approval-20261010.json",
        "zones": [
            {"id": "vestiaire-a", "position": [-24, -14, -6]},
            {"id": "vestiaire-b", "position": [-24, 14, -6]},
            {"id": "prison", "position": [24, 14, -6]},
            {"id": "salle-des-morts", "position": [24, -14, -6]},
            *[
                {"id": f"chapelle-{i}", "position": [x, y, -12]}
                for i, (x, y) in enumerate([(-22, -14), (22, -14), (-22, 14), (22, 14)])
            ],
        ],
    }


def build(out, only=None):
    out.mkdir(parents=True, exist_ok=True)
    kit.bpy.ops.object.select_all(action="SELECT")
    kit.bpy.ops.object.delete(use_global=False)
    kit.PIECES.clear()
    kit.OBJECTS.clear()
    OBJECTS.clear()
    materials = kit.build_materials()
    meta = metadata()
    previous = {}
    if only:
        previous = {
            m["id"]: m
            for m in json.loads((out / "manifest.json").read_text(encoding="utf8"))["meshes"]
        }

    def emit(name, fn, role="architecture"):
        if only and name not in only and name in previous:
            kit.PIECES.append(previous[name])
        else:
            kit.export_piece(name, fn, out, materials, role=role, clean_degenerate=True)

    def place(mesh, position=(0, 0, 0), yaw=0, role="architecture", scale=None, ident=None):
        item = {
            "id": ident or f"{mesh}-{len(OBJECTS):04d}",
            "meshId": mesh,
            "position": list(position),
            "yaw": yaw,
            "role": role,
            "occluder": role in ("roof", "wall", "arcade", "floor", "seating"),
        }
        if scale is not None:
            item["scale"] = scale
        OBJECTS.append(item)

    emit("afm-sand", sand_disk, "ground")
    place("afm-sand", role="floor")
    # La coursive des dieux couronne le podium (3 m) ; le sable reste en contrebas.
    emit("afm-statue-course", lambda: ring(43, 27, 49, 33, 0), "floor")
    place("afm-statue-course", (0, 0, cavea.PODIUM), role="floor")
    emit("afm-podium", cavea.podium, "wall")
    place("afm-podium", role="wall")
    emit("afm-podium-gate", cavea.podium_gate, "arcade")
    place("afm-podium-gate", role="arcade", ident="porte-des-morts")
    place("afm-podium-gate", yaw=180, role="arcade", ident="porte-du-triomphe")
    # Les deambulatoires commencent au dos de la cavea (84,6 m) : ni fente au pied du mur, ni
    # dalle noyee dans la cage des escaliers caches.
    emit("afm-ring-ground", lambda: ring(84.6, 68.6, 93.5, 77, 0, dressed=True), "floor")
    place("afm-ring-ground", role="floor")
    emit("afm-ring-upper", lambda: ring(84.6, 68.6, 93.5, 77, 0, dressed=True), "floor")
    place("afm-ring-upper", (0, 0, 12), role="floor")
    emit("afm-ring-gallery", lambda: ring(87, 71, 93.5, 77, 0, dressed=True), "floor")
    for z in (24, 36, 46.8):
        place("afm-ring-gallery", (0, 0, z), role="floor")
    # La cavea du Colisee : seize secteurs continus, sans breche ; les portes passent dessous.
    for i in range(16):
        name = f"afm-cavea-{i:02d}"
        emit(name, lambda i=i: cavea.sector(i), "seating")
        place(name, role="seating")
        name = f"afm-scalaria-{i:02d}"
        emit(name, lambda i=i: cavea.scalaria(i), "stairs")
        place(name, role="stairs")
    emit("afm-tunnel-floors", cavea.tunnel_floors, "floor")
    place("afm-tunnel-floors", role="floor")
    emit("afm-vomitorium", cavea.vomitorium, "arcade")
    for k, mouth in enumerate(cavea.vomitoria_positions()):
        place("afm-vomitorium", mouth["position"], mouth["yaw"], "arcade", ident=f"vomitoire-{k:02d}")
    # Les escaliers caches dans la masse : leurs garde-corps et le mur d'echiffre.
    emit("afm-escaliers", cavea.stair_dressing, "stairs")
    place("afm-escaliers", role="stairs", ident="escaliers-caches")
    # Le haut mur de la summa cavea et le portique couvert du sommet.
    emit("afm-summa-wall", cavea.summa_wall, "wall")
    emit("afm-summa-wall-door", lambda: cavea.summa_wall(door=True), "wall")
    emit("afm-porticus", cavea.porticus, "arcade")
    doors = cavea.door_bays()
    for name, radius, z in (("afm-summa-wall", cavea.WALL, 24), ("afm-porticus", cavea.PORTICUS, 36)):
        for i in range(80):
            lo, hi = math.tau * i / 80, math.tau * (i + 1) / 80
            p0, p1 = polar(radius, radius - 16, lo), polar(radius, radius - 16, hi)
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            place(
                name + ("-door" if name == "afm-summa-wall" and i in doors else ""),
                ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z),
                180 - math.degrees(math.atan2(dy, dx)),
                "wall" if name == "afm-summa-wall" else "arcade",
                [math.hypot(dx, dy) / 6, 1, 1],
            )
    emit("afm-tenture", cavea.tenture, "ornament")
    for k, (position, yaw) in enumerate(cavea.tenture_positions()):
        place("afm-tenture", position, yaw, "ornament", ident=f"tenture-{k:02d}")
    emit("afm-velum", cavea.velum, "ornament")
    place("afm-velum", role="ornament", ident="velum")
    # Gate wedges remain open: physical stairs and ground corridors pass through them.
    emit("afm-gate-path", lambda: tiled_rect(-5, 5, 38, 77, 0))
    place("afm-gate-path", role="floor")
    place("afm-gate-path", yaw=180, role="floor")
    # Leave the descending stair opening in its centre, with lateral public routes.
    # This replacement is authored as separate surfaces, never a hidden collision patch.
    emit(
        "afm-gate-sides",
        lambda: (
            tiled_rect(43, 94, -7, -2, 0),
            tiled_rect(43, 94, 2, 7, 0),
            tiled_rect(43, 49, -2, 2, 0),
            tiled_rect(62, 94, -2, 2, 0),
        ),
    )
    place("afm-gate-sides", role="floor")
    place("afm-gate-sides", yaw=180, role="floor")
    emit("afm-gate-rim", lambda: finishes.gate_rim(kit), "balustrade")
    place("afm-gate-rim", role="balustrade")
    place("afm-gate-rim", yaw=180, role="balustrade")
    emit("afm-descent", lambda: kit.stair_flight(0, 0, 3.4, 0.3, 0.15, 0.15, 40, -0.35))
    place("afm-descent", (61, 0, -6), yaw=270, role="stairs")
    place("afm-descent", (-61, 0, -6), yaw=90, role="stairs")
    place("afm-descent", (0, 26, -6), role="stairs")
    place("afm-descent", (40, -8, -12), yaw=180, role="stairs")
    emit("afm-arcade-sculpted", palace_arcade)
    # The reusable arcade is authored around x=6; placement shifts its pivot analytically.
    for i in range(80):
        t = math.tau * (i + 0.5) / 80
        lo, hi = math.tau * i / 80, math.tau * (i + 1) / 80
        p0, p1 = polar(93.5, 77, lo), polar(93.5, 77, hi)
        chord = math.dist(p0, p1)
        yaw = 90 - math.degrees(math.atan2(math.sin(t) / 77, math.cos(t) / 93.5))
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        px, py = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
        for z in (0, 12, 24):
            if z == 0 and i % 20 in (0, 19):
                continue
            place(
                "afm-arcade-sculpted",
                (px - c * chord, py + s * chord, z),
                yaw,
                "arcade",
                [chord / 6, 1, 1],
                ident=f"afm-arcade-{len(OBJECTS):04d}",
            )
    for i in range(4):
        t = math.pi * i / 2
        p0, p1 = polar(93.5, 77, t - math.tau / 80), polar(93.5, 77, t + math.tau / 80)
        chord = math.dist(p0, p1)
        yaw = 90 - math.degrees(t)
        c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        place(
            "afm-arcade-sculpted",
            ((p0[0] + p1[0]) / 2 - c * chord, (p0[1] + p1[1]) / 2 + s * chord, 0),
            yaw,
            "arcade",
            [chord / 6, 1, 1],
            ident=f"porte-monumentale-{i}",
        )
    emit("afm-attic", attic, "wall")
    for i in range(80):
        lo, hi = math.tau * i / 80, math.tau * (i + 1) / 80
        p0, p1 = polar(93.5, 77, lo), polar(93.5, 77, hi)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        yaw = 180 - math.degrees(math.atan2(dy, dx))
        place(
            "afm-attic",
            ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 36),
            yaw,
            "wall",
            [math.hypot(dx, dy) / 6, 1, 1],
        )
    emit("afm-balustrade", lambda: kit.rail(0, 0, 0, 5.5))
    # Garde-corps : le podium (au bord du sable), le portique et la terrasse du sommet.
    for z, a, b, count in [(cavea.PODIUM, 43.25, 27.25, 40), (36, 87, 71, 80), (46.8, 87, 71, 80)]:
        for i in range(count):
            p0, p1 = polar(a, b, math.tau * i / count), polar(a, b, math.tau * (i + 1) / count)
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            place(
                "afm-balustrade",
                ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, z),
                -math.degrees(math.atan2(dy, dx)),
                "rail",
                [math.hypot(dx, dy) / 5.5, 1, 1],
            )
    emit("afm-loge", loge, "architecture")
    emit("afm-loge-roof", loge_roof, "roof")
    emit("afm-loge-imperial", imperial_loge, "architecture")
    emit("afm-loge-imperial-roof", imperial_loge_roof, "roof")
    for log in meta["loges"]:
        imperial = log["delegation"] == "empire"
        place(
            "afm-loge-imperial" if imperial else "afm-loge",
            log["position"],
            log["yaw"],
            "loge",
            ident="loge-" + log["delegation"],
        )
        place(
            "afm-loge-imperial-roof" if imperial else "afm-loge-roof",
            log["position"],
            log["yaw"],
            "roof",
            ident="toit-loge-" + log["delegation"],
        )
    emit("afm-room-floor", lambda: tiled_rect(-12, 12, -9, 9, 0), "floor")
    emit("afm-room-floor-service", service_floor, "floor")
    emit("afm-room-floor-crypt", lambda: service_floor(True), "floor")
    emit("afm-room-walls", room_walls, "wall")
    emit("afm-room-walls-service", lambda: room_walls(True), "wall")
    emit("afm-room-vault", lambda: kit.vault(-12, 12, 0, 3.2, 9, rise=1.5), "roof")
    for z, xx in [(-6, 24), (-12, 22)]:
        for x in (-xx, xx):
            for y in (-14, 14):
                for name, role in [("floor", "floor"), ("walls", "wall"), ("vault", "roof")]:
                    mesh = "afm-room-" + name
                    if name == "walls" and z == -6 and x == 24 and y == -14:
                        mesh += "-service"
                    if name == "floor":
                        if z == -12:
                            mesh = "afm-room-floor-crypt"
                        elif x < 0:
                            mesh = "afm-room-floor-service"
                    place(
                        mesh,
                        (x, y, z),
                        yaw=180 if name == "walls" and y > 0 else 0,
                        role=role,
                        ident=f"afm-room-floor-{len(OBJECTS):04d}" if name == "floor" else None,
                    )
    # L'aménagement des vestiaires et de la prison (arena_undercroft.py), en mètres de l'arène.
    emit("afm-vestiaire-nord", lambda: undercroft.vestiaire(-1), "amenagement")
    emit("afm-vestiaire-sud", lambda: undercroft.vestiaire(1), "amenagement")
    emit("afm-prison", undercroft.prison, "amenagement")
    for mesh in ("afm-vestiaire-nord", "afm-vestiaire-sud", "afm-prison"):
        place(mesh, (0, 0, -6), role="amenagement", ident=mesh.replace("afm-", "amenagement-"))
    emit(
        "afm-under-cross",
        lambda: (
            tiled_rect(-68, 68, -5, 5, 0),
            tiled_rect(-6, 6, 5, 28, 0),
            tiled_rect(-6, 6, -28, -5, 0),
        ),
        "floor",
    )
    place("afm-under-cross", (0, 0, -6), role="floor")
    emit(
        "afm-cat-cross",
        lambda: (
            tiled_rect(-44, 44, -5, 5, 0),
            tiled_rect(-6, 6, 5, 25, 0),
            tiled_rect(-6, 6, -25, -5, 0),
            tiled_rect(36, 44, -10, -5, 0),
        ),
        "floor",
    )
    place("afm-cat-cross", (0, 0, -12), role="floor")
    for prefix, z, cat in [("under", -6, False), ("cat", -12, True)]:
        emit(f"afm-{prefix}-walls", lambda cat=cat: corridor_walls(cat), "wall")
        place(f"afm-{prefix}-walls", (0, 0, z), role="wall")
        emit(f"afm-{prefix}-branch-roofs", lambda cat=cat: branch_roofs(cat), "roof")
        place(f"afm-{prefix}-branch-roofs", (0, 0, z), role="roof")
    emit("afm-cat-landing", lambda: tiled_rect(34, 44, -23, -20, 0), "floor")
    place("afm-cat-landing", (0, 0, -6), role="floor")
    emit("afm-axial-vault", lambda: kit.vault(-12, 12, 0, 3.2, 5, rise=1.6), "roof")
    for z in (-6, -12):
        for x in (-24, 0, 24):
            place("afm-axial-vault", (x, 0, z), role="roof")
    emit(
        "afm-statue-plinth",
        statue_plinth,
    )
    meta["statues"] = []
    for i in range(14):
        t = math.tau * (i + 0.5) / 14
        p = polar(46, 30, t, cavea.PODIUM)
        place("afm-statue-plinth", p, 90 - math.degrees(t), "plinth")
        meta["statues"].append(
            {"position": [p[0], p[1], cavea.PODIUM + 1.7], "yaw": 270 - math.degrees(t), "height": 4.3}
        )
    for x, y in [(x, y) for x in (-24, 24) for y in (-14, 14)]:
        # Share the former centre light between the furnished sides of each room.
        # Total intensity and colour stay unchanged, without raising exposure.
        for offset in (-6, 6):
            meta["lights"].append({"position": [x + offset, y, -3.0], "candelas": 11, "radius": 11})
            meta["lights"].append(
                {"position": [x * 0.92 + offset, y, -9.0], "candelas": 8, "radius": 10}
            )
    for i in range(24):
        t = math.tau * i / 24
        meta["lights"].append({"position": polar(88, 72, t, 15), "candelas": 16, "radius": 8})
    for x in (-48, -24, 0, 24, 48):
        meta["lights"].append({"position": [x, 0, -2.8], "candelas": 18, "radius": 9})
    for x in (-30, 0, 30):
        meta["lights"].append({"position": [x, 0, -8.8], "candelas": 14, "radius": 9})
    # Add decoration after ALL existing placements so their stable IDs do not shift.
    emit("afm-loge-textiles", loge_textiles, "ornament")
    emit("afm-loge-imperial-textiles", imperial_loge_textiles, "ornament")
    emit("afm-arcade-relief", arcade_relief, "ornament")
    emit("afm-attic-relief", attic_relief, "ornament")
    emit("afm-room-dado", room_dado, "ornament")
    emit("afm-room-ribs", room_ribs, "ornament")
    emit("afm-under-ribs", corridor_ribs, "ornament")
    emit("afm-cat-ribs", lambda: corridor_ribs(True), "ornament")
    emit("afm-balustrade-relief", balustrade_relief, "ornament")
    emit("afm-room-backing", room_backing, "wall")
    emit("afm-room-service-backing", lambda: room_backing(True), "wall")
    emit("afm-room-vault-backing", lambda: continuous_vault(-12, 12, 0, 3.2, 9.105, 1.605), "roof")
    emit("afm-under-backing", corridor_backing, "wall")
    emit("afm-cat-backing", lambda: corridor_backing(True), "wall")
    emit("afm-under-vault-backing", branch_vault_backing, "roof")
    emit("afm-cat-vault-backing", lambda: branch_vault_backing(True), "roof")
    emit("afm-axial-vault-backing", lambda: continuous_vault(-12, 12, 0, 3.2, 5.105, 1.705), "roof")
    for source in list(OBJECTS):
        detail = {
            "afm-arcade-sculpted": "afm-arcade-relief",
            "afm-attic": "afm-attic-relief",
            "afm-balustrade": "afm-balustrade-relief",
        }.get(source["meshId"])
        if detail:
            place(
                detail,
                source["position"],
                source["yaw"],
                "ornament",
                source.get("scale"),
                "relief-" + source["id"],
            )
        if source["meshId"] in ("afm-room-walls", "afm-room-walls-service"):
            for name in ("afm-room-dado", "afm-room-ribs"):
                place(
                    name,
                    source["position"],
                    source["yaw"],
                    "ornament",
                    ident=name + "-" + source["id"],
                )
            backing = (
                "afm-room-service-backing"
                if source["meshId"].endswith("service")
                else "afm-room-backing"
            )
            place(backing, source["position"], source["yaw"], "wall", ident="fond-" + source["id"])
        if source["meshId"] in ("afm-room-vault", "afm-axial-vault"):
            backing = source["meshId"] + "-backing"
            place(backing, source["position"], source["yaw"], "roof", ident="fond-" + source["id"])
    for log in meta["loges"]:
        mesh = (
            "afm-loge-imperial-textiles" if log["delegation"] == "empire" else "afm-loge-textiles"
        )
        place(
            mesh,
            log["position"],
            log["yaw"],
            "ornament",
            ident="tentures-loge-" + log["delegation"],
        )
    place("afm-under-ribs", (0, 0, -6), role="ornament", ident="nervures-vestiaires")
    place("afm-cat-ribs", (0, 0, -12), role="ornament", ident="nervures-catacombes")
    for prefix, z in (("under", -6), ("cat", -12)):
        place(f"afm-{prefix}-backing", (0, 0, z), role="wall", ident=f"fond-murs-{prefix}")
        place(f"afm-{prefix}-vault-backing", (0, 0, z), role="roof", ident=f"fond-voutes-{prefix}")
    meta["materialOverrides"] = {
        "afm-velum": {"burgundy": "linen"},
        "afm-loge-roof": {"dark_metal": "roof_terracotta"},
        "afm-loge-imperial-roof": {"dark_metal": "roof_terracotta"},
        "afm-room-floor-service": {"marble_white": "chamber_floor", "mortar": "chamber_stone"},
        "afm-room-floor-crypt": {"stone_cream": "chamber_floor", "mortar": "chamber_stone"},
        **{
            name: {"stone_cream": "chamber_stone", "marble_white": "chamber_stone"}
            for name in ("afm-room-dado", "afm-room-ribs", "afm-under-ribs", "afm-cat-ribs")
        },
        **{
            name: {"mortar": "chamber_stone"}
            for name in (
                "afm-room-backing",
                "afm-room-service-backing",
                "afm-room-vault-backing",
                "afm-under-backing",
                "afm-cat-backing",
                "afm-under-vault-backing",
                "afm-cat-vault-backing",
                "afm-axial-vault-backing",
            )
        },
    }
    meta["shots"] += [
        {"name": "terrasse", "target": [24, 69, 47.3], "yaw": 100, "pitch": 42, "distance": 21},
        {"name": "parvis", "target": [0, 73, 1.7], "yaw": 0, "pitch": 38, "distance": 24},
        {
            "name": "galerie-haute",
            "target": polar(88.5, 72.5, math.pi / 4, 25.5),
            "yaw": 225,
            "pitch": 35,
            "distance": 18,
        },
    ]
    meta["sculptedWitness"] = "arena-wicked-witness, approved 2026-10-10"
    meta["supportOverrides"] = {}
    by_mesh = {}
    for item in OBJECTS:
        by_mesh.setdefault(item["meshId"], []).append(item)
    for item in OBJECTS:
        ident = item["id"]
        if ident.startswith("relief-"):
            meta["supportOverrides"][ident] = ident[len("relief-") :]
        elif ident.startswith("fond-"):
            source = ident[len("fond-") :]
            if any(obj["id"] == source for obj in OBJECTS):
                meta["supportOverrides"][ident] = source
        elif ident.startswith("tentures-loge-"):
            meta["supportOverrides"][ident] = "loge-" + ident[len("tentures-loge-") :]
        elif ident.startswith("toit-loge-"):
            meta["supportOverrides"][ident] = "loge-" + ident[len("toit-loge-") :]
        elif item["meshId"] in ("afm-room-dado", "afm-room-ribs"):
            meta["supportOverrides"][ident] = ident[len(item["meshId"]) + 1 :]
    for prefix in ("under", "cat"):
        floor = by_mesh[f"afm-{prefix}-cross"][0]["id"]
        for ident in (
            f"fond-murs-{prefix}",
            f"fond-voutes-{prefix}",
            "nervures-vestiaires" if prefix == "under" else "nervures-catacombes",
        ):
            meta["supportOverrides"][ident] = floor
    # Ground-level south threshold only. Existing actors, lions, routes and stair
    # surfaces are retained; these new IDs are appended after their placements.
    emit("afm-south-threshold-pylon", south_threshold_pylon, "ornament")
    emit("afm-south-threshold-side", south_threshold_side, "ornament")
    emit("afm-south-threshold-textile", south_threshold_textile, "ornament")
    ground = by_mesh["afm-ring-ground"][0]["id"]
    for sign, word in ((-1, "west"), (1, "east")):
        pylon = "seuil-sud-pylon-" + word
        side = "seuil-sud-side-" + word
        textile = "seuil-sud-textile-" + word
        place("afm-south-threshold-pylon", (sign * 12.5, 75.2, 0), role="ornament", ident=pylon)
        place("afm-south-threshold-side", (sign * 10.95, 75.45, 0), role="ornament", ident=side)
        place("afm-south-threshold-textile", (sign * 12.5, 75.2, 0), role="ornament", ident=textile)
        meta["supportOverrides"][pylon] = ground
        meta["supportOverrides"][side] = ground
        meta["supportOverrides"][textile] = pylon
    meta["southThreshold"] = {
        "position": [0, 74, 0],
        "clearCentralCorridor": {"x": [-5, 5]},
        "lionPositionsUnchanged": [[-6.5, 74.5, 0], [6.5, 74.5, 0]],
        "notes": [
            "Six lateral decorative actors on the existing ground ring only.",
            "No new floor, terrain, arch or lintel; no member crosses the stairs.",
            "All additions are beyond the flights and half landing X extent of 9m.",
            "Where the upper bypass overhangs, the decorations stay below Z4.56 while its soffit is above Z11.68.",
        ],
    }
    emit("afm-ground-arcade-support", ground_arcade_support, "ornament")
    for source in list(OBJECTS):
        if source["meshId"] == "afm-arcade-sculpted" and source["position"][2] == 0:
            ident = "ground-base-" + source["id"]
            place(
                "afm-ground-arcade-support",
                source["position"],
                source["yaw"],
                "ornament",
                source.get("scale"),
                ident,
            )
            meta["supportOverrides"][ident] = source["id"]
    # Vault-mounted ribs must follow their vault's cutaway, not the room's walls.
    for source in OBJECTS:
        if source["meshId"] == "afm-room-ribs":
            roof = next(
                item for item in by_mesh["afm-room-vault"] if item["position"] == source["position"]
            )
            meta["supportOverrides"][source["id"]] = roof["id"]
    for prefix, z, ident in (
        ("under", -6, "nervures-vestiaires"),
        ("cat", -12, "nervures-catacombes"),
    ):
        meta["supportOverrides"][ident] = [
            item["id"]
            for item in OBJECTS
            if item["position"][2] == z
            and item["meshId"] in ("afm-axial-vault", f"afm-{prefix}-branch-roofs")
        ]
    meta["geometryInvariants"] = [
        "LEVELS and gameplay anchors (sand, -6, -12) unchanged",
        "Roman cavea (19 October 2026): podium 3 m, ima/media/summa cavea, porticus; no visible stair tower",
        "Gates pass under the podium and the cavea; the cavea is continuous around the oval",
        "Arcade intrados preserved; real 12m authoring removes vertical stretching",
        "Loges sit in notches cut into the media cavea, above the first praecinctio (12 m)",
    ]
    # Referenced collision assets only: no extra actor, surface, material or render
    # placement is created. The scene importer binds these to ComplexCollisionMesh.
    emit("afm-ring-ground-collision", lambda: ring_collision(84.6, 68.6, 93.5, 77), "collision")
    emit(
        "afm-ring-upper-collision",
        lambda: ring_collision(84.6, 68.6, 93.5, 77),
        "collision",
    )
    emit(
        "afm-ring-gallery-collision",
        lambda: ring_collision(87, 71, 93.5, 77),
        "collision",
    )
    meta["complexCollisionMeshes"] = {
        "afm-ring-ground": "afm-ring-ground-collision",
        "afm-ring-upper": "afm-ring-upper-collision",
        "afm-ring-gallery": "afm-ring-gallery-collision",
    }
    meta["architecturalCollision"] = {
        "coordinates": "same metre-space and pivot as each visual ring",
        "angularChords": 192,
        "slotRule": "96 bays; omit abs(cos(bay_midpoint)) < 0.115 when slots=True",
        "localTopZ": 0,
        "localBottomZ": -0.30,
        "visualMeshUnchanged": True,
        "note": "Nominal architectural walking surfaces and real stair voids; decorative joints and bevels are visual only.",
    }
    meshes = []
    for m in kit.PIECES:
        path = out / m["file"]
        m["bytes"] = path.stat().st_size
        m["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        meshes.append(m)
    manifest = {
        "format": "jadg-arena-fate-modern",
        "version": 1,
        "generator": "scripts/assetsGeneration/build_arena_fate_modern.py",
        "coordinates": "metres X east / Y south / Z up; object positions absolute",
        "uvMetersPerRepeat": 2,
        "materials": kit.NAMES,
        "meshes": meshes,
        "objects": OBJECTS,
        "metadata": meta,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )
    print(
        json.dumps(
            {
                "meshes": len(meshes),
                "objects": len(OBJECTS),
                "triangles": sum(x["triangles"] for x in meshes),
                "loges": len(meta["loges"]),
                "statues": len(meta["statues"]),
            }
        ),
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--metadata-only", action="store_true")
    parser.add_argument(
        "--only", nargs="+", help="Regenerate selected meshes, retain other verified outputs"
    )
    argv = sys.argv[sys.argv.index("--") + 1 :] if kit.bpy and "--" in sys.argv else None
    args = parser.parse_args(argv)
    if args.metadata_only:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / "layout.json").write_text(
            json.dumps(metadata(), ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
        return 0
    if kit.bpy:
        build(args.output, args.only)
        return 0
    return subprocess.run(
        [
            str(kit.BLENDER),
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
            *(["--only", *args.only] if args.only else []),
        ]
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
