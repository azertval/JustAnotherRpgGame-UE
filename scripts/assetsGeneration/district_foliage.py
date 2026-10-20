#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Sculpted imperial garden vegetation, assembled from curved closed pieces.

Pass the witness geometry module as ``g``. Geometry uses metres, X east/Y south/
Z up, and appends to its existing buffers; no scene, export or material state is
changed. The caller supplies an existing foliage material and exports normally.
Large irregular leaf masses establish the silhouette; curved leaf sprays break
their outlines. Vertex colours provide restrained pigment variation, without
baked directional lighting or fine noise. Every surface is finished all around.
"""

import math
import random


def _add(a, b):
    return tuple(a[i] + b[i] for i in range(3))


def _mul(v, scale):
    return tuple(q * scale for q in v)


def _unit(v):
    return _mul(v, 1 / math.sqrt(sum(q * q for q in v)))


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _pigment(rng):
    value = rng.uniform(0.68, 1.0)
    return (value * rng.uniform(0.92, 1.00), value, value * rng.uniform(0.85, 0.99), 1)


def _solid(g, points, faces, material, tint):
    g.solid(points, faces, material, bevel=0, color=tint)
    g.FACE_SMOOTH[-len(faces) :] = [True] * len(faces)


def _branch(g, path, radius, material="wood"):
    """Curved taper with small longitudinal cambium ridges, closed at both ends."""
    points, faces = [], []
    sides = 16
    for j, centre in enumerate(path):
        tangent = _unit(
            tuple(path[min(j + 1, len(path) - 1)][k] - path[max(0, j - 1)][k] for k in range(3))
        )
        axis = (0, 1, 0) if abs(tangent[1]) < 0.85 else (1, 0, 0)
        u = _unit(_cross(tangent, axis))
        v = _cross(tangent, u)
        r = radius * (1 - 0.83 * j / (len(path) - 1))
        for k in range(sides):
            a = math.tau * k / sides
            rr = r * (1 + 0.07 * math.sin(a * 5 + j * 0.16))
            points.append(_add(centre, _add(_mul(u, rr * math.cos(a)), _mul(v, rr * math.sin(a)))))
    for j in range(len(path) - 1):
        for k in range(sides):
            a, b = j * sides + k, j * sides + (k + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces += [
        tuple(range(sides - 1, -1, -1)),
        tuple((len(path) - 1) * sides + k for k in range(sides)),
    ]
    _solid(g, points, faces, material, (0.83, 0.88, 0.81, 1))


def _leaf(g, centre, direction, length, width, material, tint, roll=0, outward=None):
    """A pointed, folded leaf with a curved midrib and a closed thin underside."""
    if outward is not None:
        normal = _unit(outward)
        projection = sum(direction[k] * normal[k] for k in range(3))
        d = _unit(tuple(direction[k] - projection * normal[k] for k in range(3)))
        side = _unit(_cross(d, normal))
    else:
        d = _unit(direction)
        side = _unit(_cross(d, (0, 0, 1) if abs(d[2]) < 0.92 else (0, 1, 0)))
        normal = _cross(side, d)
    side, normal = (
        _add(_mul(side, math.cos(roll)), _mul(normal, math.sin(roll))),
        _add(_mul(normal, math.cos(roll)), _mul(side, -math.sin(roll))),
    )
    points, faces = [], []
    # A narrow tip/base avoids duplicated pole vertices and degenerate triangles.
    for bottom in [False, True]:
        for j in range(7):
            t = j / 6
            breadth = width * max(0.015, math.sin(math.pi * t) ** 0.8)
            arc = length * 0.08 * math.sin(t * math.pi * 0.85)
            for k in [-1, 0, 1]:
                ridge = (1 - abs(k)) * breadth * 0.26
                offset = arc + ridge - (length * 0.025 if bottom else 0)
                points.append(
                    _add(
                        centre,
                        _add(
                            _mul(d, (t - 0.5) * length),
                            _add(_mul(side, k * breadth), _mul(normal, offset)),
                        ),
                    )
                )
    for j in range(6):
        for k in range(2):
            a = j * 3 + k
            faces.append((a, a + 1, a + 4, a + 3))
            faces.append((a + 21, a + 24, a + 25, a + 22))
    perimeter = [0, 1, 2, 5, 8, 11, 14, 17, 20, 19, 18, 15, 12, 9, 6, 3]
    for j, a in enumerate(perimeter):
        b = perimeter[(j + 1) % len(perimeter)]
        faces.append((a, a + 21, b + 21, b))
    _solid(g, points, faces, material, tint)


def _cluster(g, centre, radii, rng, material, upright=False):
    """An asymmetric lobed foliage mass with broad, overlapping leaf sprays."""
    phase = rng.uniform(0, math.tau)
    slices, rings = 28, 16
    rx, ry, rz = radii

    def surface(theta, phi, outward=1):
        ripple = (
            1
            + 0.10 * math.sin(3 * theta + phase + 2 * phi)
            + 0.075 * math.sin(5 * theta - phi + phase)
        )
        return (
            centre[0]
            + outward * rx * math.sin(phi) * math.cos(theta) * ripple
            + rx * 0.10 * math.cos(phi),
            centre[1] + outward * ry * math.sin(phi) * math.sin(theta) * ripple,
            centre[2]
            + outward * rz * math.cos(phi) * (1 + 0.055 * math.sin(theta * 3 + phase))
            + rz * 0.035 * math.sin(phi * 3),
        )

    points = [surface(0, 0, 0.67)]
    for j in range(1, rings):
        for k in range(slices):
            points.append(surface(math.tau * k / slices, math.pi * j / rings, 0.67))
    points.append(surface(0, math.pi, 0.67))
    faces = [(0, 1 + k, 1 + (k + 1) % slices) for k in range(slices)]
    for j in range(rings - 2):
        for k in range(slices):
            a, b = 1 + j * slices + k, 1 + j * slices + (k + 1) % slices
            faces.append((a, a + slices, b + slices, b))
    for k in range(slices):
        faces.append(
            (
                len(points) - 1,
                1 + (rings - 2) * slices + (k + 1) % slices,
                1 + (rings - 2) * slices + k,
            )
        )
    _solid(g, points, faces, material, _pigment(rng))
    # Ordered phyllotaxis gives readable sprays, rather than surface noise.
    for j in range(128):
        theta = phase + j * 2.3999632297
        phi = math.acos(1 - 2 * (j + 0.5) / 128)
        p = surface(theta, phi, rng.uniform(0.91, 1.015))
        normal = (
            math.sin(phi) * math.cos(theta) / rx,
            math.sin(phi) * math.sin(theta) / ry,
            math.cos(phi) / rz,
        )
        direction = (
            0.30 * math.cos(theta + 0.7),
            0.30 * math.sin(theta + 0.7),
            1 if upright else -0.8,
        )
        size = min(rx, ry, rz) * rng.uniform(0.58, 0.82)
        _leaf(
            g,
            p,
            direction,
            size * 1.5,
            size * 0.42,
            material,
            _pigment(rng),
            rng.uniform(-0.18, 0.18),
            outward=normal,
        )


def cypress(g, x=0, y=0, z=0, height=7, radius=1, material="foliage", seed=17):
    """Upright imperial cypress: curved trunk, ascending branches, feathered crown."""
    rng = random.Random(seed)
    _branch(
        g,
        [(x + 0.06 * radius * math.sin(j * 0.8), y, z + height * j / 10) for j in range(10)],
        radius * 0.18,
    )
    for tier in range(10):
        t = tier / 9
        envelope = radius * (0.35 + 0.72 * math.sin(math.pi * (0.12 + t * 0.85))) * (1 - t * 0.50)
        for k in range(5):
            a = math.tau * k / 5 + tier * 1.17
            rr = envelope * rng.uniform(0.34, 0.61)
            centre = (x + rr * math.cos(a), y + rr * math.sin(a), z + height * (0.17 + t * 0.72))
            _cluster(
                g,
                centre,
                (envelope * 0.57, envelope * 0.54, height * (0.10 - t * 0.035)),
                rng,
                material,
                upright=True,
            )
            if tier < 6:
                _branch(
                    g,
                    [
                        (x, y, centre[2] - height * 0.12),
                        (
                            centre[0] * 0.5 + x * 0.5,
                            centre[1] * 0.5 + y * 0.5,
                            centre[2] - height * 0.04,
                        ),
                        centre,
                    ],
                    radius * 0.055,
                )
    _cluster(
        g,
        (x + radius * 0.06, y, z + height * 0.94),
        (radius * 0.22, radius * 0.21, height * 0.07),
        rng,
        material,
        upright=True,
    )


def hedge(g, x=0, y=0, z=0, length=6, depth=1.5, height=1.6, material="foliage", seed=31):
    """A continuous clipped box hedge with scalloped, individually leafed margins."""
    rng = random.Random(seed)
    count = max(2, math.ceil(length / (depth * 0.56)))
    for j in range(count):
        xx = x - length / 2 + (j + 0.5) * length / count
        for side in [-1, 1]:
            centre = (
                xx + rng.uniform(-0.08, 0.08),
                y + side * depth * 0.20,
                z + height * (0.54 + rng.uniform(-0.04, 0.04)),
            )
            _branch(
                g,
                [(xx, y, z), (xx + side * 0.05, y + side * depth * 0.1, z + height * 0.4), centre],
                height * 0.05,
            )
            _cluster(g, centre, (length / count * 0.77, depth * 0.38, height * 0.52), rng, material)


def noble_tree(g, x=0, y=0, z=0, height=5, crown_radius=2, material="foliage", seed=47):
    """Small broadleaf tree with a legible trunk, branching forks and layered crown."""
    rng = random.Random(seed)
    _branch(
        g,
        [
            (x + 0.11 * crown_radius * math.sin(j * 0.56), y + 0.03 * j, z + height * j * 0.085)
            for j in range(9)
        ],
        height * 0.052,
    )
    for k in range(7):
        a = k * 2.3999632297
        rr = crown_radius * rng.uniform(0.52, 0.77)
        cz = z + height * (0.65 + 0.09 * math.sin(k * 1.1))
        centre = (x + rr * math.cos(a), y + rr * math.sin(a), cz)
        _branch(
            g,
            [
                (x, y, z + height * 0.32),
                (
                    x + rr * 0.3 * math.cos(a - 0.25),
                    y + rr * 0.3 * math.sin(a - 0.25),
                    z + height * 0.49,
                ),
                (x + rr * 0.75 * math.cos(a), y + rr * 0.75 * math.sin(a), cz - height * 0.08),
                centre,
            ],
            height * 0.024,
        )
        for j in range(3):
            az = a + (j - 1) * 0.62
            p = _add(
                centre,
                (
                    crown_radius * 0.21 * math.cos(az),
                    crown_radius * 0.21 * math.sin(az),
                    j * height * 0.055,
                ),
            )
            _cluster(g, p, (crown_radius * 0.42, crown_radius * 0.37, height * 0.17), rng, material)
    _cluster(
        g,
        (x + 0.12 * crown_radius, y, z + height * 0.85),
        (crown_radius * 0.50, crown_radius * 0.45, height * 0.16),
        rng,
        material,
    )
