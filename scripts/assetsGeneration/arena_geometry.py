#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Shared geometry primitives used by the current Arena and capital districts."""

from __future__ import annotations

import math
from pathlib import Path

try:
    import bpy
    import bmesh
except ImportError:
    bpy = None

ROOT = Path(__file__).resolve().parents[2]
BLENDER = Path(r"D:\Blender Foundation\Blender 5.2\blender.exe")
MATERIALS = {
    "stone_cream": ((0.67, 0.55, 0.38, 1), 0.78, 0),
    "marble_white": ((0.86, 0.82, 0.69, 1), 0.30, 0),
    "bronze": ((0.43, 0.27, 0.09, 1), 0.32, 1),
    "dark_metal": ((0.075, 0.065, 0.055, 1), 0.43, 1),
    "burgundy": ((0.29, 0.022, 0.048, 1), 0.88, 0),
    "sand": ((0.68, 0.52, 0.29, 1), 0.96, 0),
    "wood": ((0.24, 0.11, 0.04, 1), 0.65, 0),
    "mortar": ((0.22, 0.19, 0.16, 1), 0.95, 0),
}
NAMES = list(MATERIALS)
VERTS, FACES, FACE_MATERIALS = [], [], []
FACE_SMOOTH = []
FACE_COLORS, FACE_SEEDS, FACE_BEVELS = [], [], []
PIECES, OBJECTS, ROOFS = [], [], []
SIMPLE_PARTS = 0
DETAIL_COUNTS = {
    "dressedBlocks": 0,
    "floorSlabs": 0,
    "selectedChips": 0,
    "flutedDrums": 0,
    "coherentStairFlights": 0,
}


def stone_variation(points):
    centre = [sum(p[k] for p in points) / len(points) for k in range(3)]
    phase = math.sin(centre[0] * 17.13 + centre[1] * 7.97 + centre[2] * 31.71) * 43758.5453
    seed = phase - math.floor(phase)
    value = 0.86 + 0.12 * seed
    warmth = 0.025 * math.sin(seed * 17.0)
    return (min(1, value + warmth), value, min(1, value - warmth), 1), seed


def solid(points, faces, material="stone_cream", bevel=0.012, color=None, seed_alpha=None):
    global SIMPLE_PARTS
    base = len(VERTS)
    VERTS.extend((x, -y, z) for x, y, z in points)
    FACES.extend(tuple(base + k for k in face) for face in faces)
    FACE_MATERIALS.extend([NAMES.index(material)] * len(faces))
    FACE_SMOOTH.extend([False] * len(faces))
    if material in ("stone_cream", "marble_white"):
        if color is None or seed_alpha is None:
            generated_tint, generated_seed = stone_variation(points)
        tint = color if color is not None else generated_tint
        alpha = generated_seed if seed_alpha is None else seed_alpha
    else:
        tint = color or (1, 1, 1, 1)
        alpha = 1.0
    FACE_COLORS.extend([tint] * len(faces))
    FACE_SEEDS.extend([alpha] * len(faces))
    FACE_BEVELS.extend([bevel] * len(faces))
    SIMPLE_PARTS += 1


def block(x, y, z, width, depth, height, material="stone_cream"):
    """A simple block, bottom at z; bevels are applied before export."""
    a, b, c, d = x - width / 2, x + width / 2, y - depth / 2, y + depth / 2
    solid(
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
        material,
    )


def dressed_block(x, y, z, width, depth, height, material="stone_cream", walkable=False):
    """A closed, dressed stone with a broad sculpted face, not surface noise.

    Walkable slabs keep their nominal top flat; only their edges are chamfered.
    Wall faces have a 2.5-4.5 cm shallow convex dress and selected 18 mm corner chips.
    """
    tint, seed = stone_variation([(x, y, z + height / 2)])
    bevel = round(((0.018 + seed * 0.008) if walkable else (0.025 + seed * 0.020)) / 0.005) * 0.005
    relief = 0 if walkable else (0.025 + seed * 0.020)
    chip = seed < 0.17 and not walkable
    corner = (1 if seed < 0.085 else -1, 1, 1)
    points, faces, shared = [], [], {}
    centre, half = (x, y, z + height / 2), (width / 2, depth / 2, height / 2)
    n = 4
    for axis in range(3):
        others = [k for k in range(3) if k != axis]
        for side in [-1, 1]:
            grid = []
            for i in range(n + 1):
                row = []
                for j in range(n + 1):
                    q = list(centre)
                    q[axis] += side * half[axis]
                    q[others[0]] += (2 * i / n - 1) * half[others[0]]
                    q[others[1]] += (2 * j / n - 1) * half[others[1]]
                    key = tuple(round(v, 9) for v in q)
                    if key not in shared:
                        p = list(q)
                        if axis == 1:
                            envelope = math.sin(math.pi * i / n) * math.sin(math.pi * j / n)
                            p[1] += side * relief * max(0, envelope) ** 0.75
                        if chip:
                            target = [centre[k] + corner[k] * half[k] for k in range(3)]
                            distance = math.sqrt(sum((q[k] - target[k]) ** 2 for k in range(3)))
                            amount = 0.018 * max(0, 1 - distance / 0.12)
                            p = [p[k] - corner[k] * amount for k in range(3)]
                        shared[key] = len(points)
                        points.append(tuple(p))
                    row.append(shared[key])
                grid.append(row)
            for i in range(n):
                for j in range(n):
                    faces.append((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    solid(points, faces, material, bevel=bevel, color=tint, seed_alpha=seed)
    FACE_SMOOTH[-len(faces) :] = [not walkable] * len(faces)
    DETAIL_COUNTS["floorSlabs" if walkable else "dressedBlocks"] += 1
    DETAIL_COUNTS["selectedChips"] += int(chip)


def prism(profile, y0, y1, material="stone_cream"):
    n = len(profile)
    points = [(x, y0, z) for x, z in profile] + [(x, y1, z) for x, z in profile]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(k, (k + 1) % n, (k + 1) % n + n, k + n) for k in range(n)]
    solid(points, faces, material)


def turned(x, y, z, profile, material="marble_white", sides=64, flutes=0):
    points = []
    for radius, height in profile:
        for j in range(sides):
            angle = math.tau * j / sides
            rr = radius - flutes * (0.5 + 0.5 * math.cos(16 * angle))
            points.append((x + rr * math.cos(angle), y + rr * math.sin(angle), z + height))
    faces = []
    for ring in range(len(profile) - 1):
        for j in range(sides):
            a, b = ring * sides + j, ring * sides + (j + 1) % sides
            faces.append((a, b, b + sides, a + sides))
    faces += [
        tuple(range(sides - 1, -1, -1)),
        tuple((len(profile) - 1) * sides + j for j in range(sides)),
    ]
    solid(points, faces, material)
    FACE_SMOOTH[-len(faces) : -2] = [True] * (len(faces) - 2)


def rod(a, b, radius=0.045, material="bronze", sides=16):
    from mathutils import Vector

    first, last = Vector(a), Vector(b)
    direction = (last - first).normalized()
    axis = direction.cross(Vector((0, 0, 1)))
    if axis.length < 0.01:
        axis = direction.cross(Vector((1, 0, 0)))
    axis.normalize()
    other = direction.cross(axis)
    points = []
    for centre in [first, last]:
        for j in range(sides):
            angle = math.tau * j / sides
            co = centre + radius * (axis * math.cos(angle) + other * math.sin(angle))
            points.append(tuple(co))
    solid(
        points,
        [(j, (j + 1) % sides, (j + 1) % sides + sides, j + sides) for j in range(sides)]
        + [tuple(range(sides - 1, -1, -1)), tuple(range(sides, 2 * sides))],
        material,
    )
    FACE_SMOOTH[-(sides + 2) : -2] = [True] * sides


def masonry(x0, x1, y, z0, z1, depth=0.6, course=0.4, brick=0.95):
    # Bury the support behind the finished returns as well as the front/back faces.
    # Otherwise its full-width end face sits 13 mm beyond the stone and masks jambs.
    end_inset = min(0.05, (x1 - x0) * 0.25)
    height_inset = min(0.03, (z1 - z0) * 0.25)
    block(
        (x0 + x1) / 2,
        y,
        z0 + height_inset,
        x1 - x0 - 2 * end_inset,
        depth - 0.06,
        z1 - z0 - 2 * height_inset,
        "mortar",
    )
    rows = max(1, round((z1 - z0) / course))
    actual = (z1 - z0) / rows
    for row in range(rows):
        at = x0
        first = brick / 2 if row % 2 else brick
        while at < x1 - 0.001:
            width = min(first if at == x0 else brick, x1 - at)
            dressed_block(
                at + width / 2, y, z0 + row * actual + 0.013, width - 0.026, depth, actual - 0.026
            )
            at += width


def arc(x, y, spring, ri=2.1, thick=0.40, depth=0.75, segments=31, axis="x"):
    """Individual wedge stones, with real intrados and recessed joints."""
    for j in range(segments):
        a, b = math.pi * j / segments + 0.0018, math.pi * (j + 1) / segments - 0.0018
        polygon = [
            (x + ri * math.cos(a), spring + ri * math.sin(a)),
            (x + (ri + thick) * math.cos(a), spring + (ri + thick) * math.sin(a)),
            (x + (ri + thick) * math.cos(b), spring + (ri + thick) * math.sin(b)),
            (x + ri * math.cos(b), spring + ri * math.sin(b)),
        ]
        if axis == "x":
            prism(polygon, y - depth / 2, y + depth / 2)
        else:
            points = [(y - depth / 2, px, pz) for px, pz in polygon] + [
                (y + depth / 2, px, pz) for px, pz in polygon
            ]
            solid(
                points,
                [
                    (0, 3, 2, 1),
                    (4, 5, 6, 7),
                    (0, 1, 5, 4),
                    (1, 2, 6, 5),
                    (2, 3, 7, 6),
                    (3, 0, 4, 7),
                ],
            )


def column(x, y, z, height=4.12, radius=0.30):
    block(x, y, z, 0.9, 0.9, 0.17, "marble_white")
    turned(x, y, z + 0.17, [(0.42, 0), (0.42, 0.12), (0.35, 0.19), (0.31, 0.28)])
    shaft = height - 0.9
    for n in range(6):
        low = n * shaft / 6
        r = radius * (1 - 0.10 * n / 6)
        turned(x, y, z + 0.45 + low, [(r, 0), (r, shaft / 6 - 0.008)], sides=96, flutes=0.027)
        DETAIL_COUNTS["flutedDrums"] += 1
        if n in [0, 5]:
            turned(
                x,
                y,
                z + 0.45 + low,
                [(r + 0.004, 0), (r + 0.016, 0.008), (r + 0.016, 0.035), (r + 0.004, 0.043)],
                "bronze",
                sides=64,
            )
    turned(
        x, y, z + height - 0.45, [(0.28, 0), (0.32, 0.07), (0.36, 0.13), (0.43, 0.27), (0.43, 0.34)]
    )
    block(x, y, z + height - 0.11, 0.90, 0.90, 0.11, "marble_white")


def cornice(x, y, z, width, depth=0.9):
    for dz, h, extension in [
        (0, 0.13, 0),
        (0.13, 0.09, 0.07),
        (0.22, 0.15, 0.16),
        (0.37, 0.09, 0.23),
    ]:
        block(x, y, z + dz, width, depth + extension, h, "marble_white")
    # A restrained, continuous gilded fillet; no invented heraldic symbol.
    block(x, y + depth / 2 + 0.085, z + 0.31, width - 0.06, 0.045, 0.045, "bronze")
    for j in range(round(width / 0.32)):
        block(
            x - width / 2 + (j + 0.5) * width / round(width / 0.32),
            y + depth / 2 + 0.055,
            z + 0.12,
            0.12,
            0.19,
            0.12,
        )


def rail(x, y, z, width, axis="x"):
    """Complete sculpted balusters; endpoints are deliberate stone piers."""

    def box_at(u, base, w, d, h):
        if axis == "x":
            block(x + u, y, z + base, w, d, h, "marble_white")
        else:
            block(x, y + u, z + base, d, w, h, "marble_white")

    box_at(0, 0, width, 0.36, 0.12)
    box_at(0, 1.02, width, 0.43, 0.13)
    for j in range(max(2, round(width / 0.40))):
        u = -width / 2 + (j + 0.5) * width / max(2, round(width / 0.4))
        px, py = (x + u, y) if axis == "x" else (x, y + u)
        turned(
            px,
            py,
            z + 0.12,
            [
                (0.105, 0),
                (0.105, 0.09),
                (0.06, 0.17),
                (0.12, 0.36),
                (0.12, 0.45),
                (0.07, 0.60),
                (0.06, 0.73),
                (0.105, 0.83),
                (0.105, 0.9),
            ],
            sides=16,
        )
    for u in [-width / 2, width / 2]:
        box_at(u, 0, 0.42, 0.42, 1.13)
        box_at(u, 1.13, 0.5, 0.5, 0.10)


def floor(x0, x1, y0, y1, z, material="marble_white", tiles=True):
    block(
        (x0 + x1) / 2,
        (y0 + y1) / 2,
        z - 0.25,
        x1 - x0,
        y1 - y0,
        0.22,
        "mortar" if tiles else "stone_cream",
    )
    if not tiles:
        block((x0 + x1) / 2, (y0 + y1) / 2, z - 0.03, x1 - x0, y1 - y0, 0.03, material)
        return
    nx, ny = max(1, round((x1 - x0) / 0.75)), max(1, round((y1 - y0) / 0.75))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            dressed_block(
                x0 + (i + 0.5) * dx,
                y0 + (j + 0.5) * dy,
                z - 0.14,
                dx - 0.018,
                dy - 0.018,
                0.14,
                material,
                walkable=True,
            )


def stair_flight(cx, start_y, width, tread, first_top, delta_z, count, base_z, direction=1):
    """One closed flight, extruded from its stair profile: no internal tread faces or thin nosings."""
    profile = [(start_y, base_z), (start_y, first_top)]
    for j in range(count):
        end = start_y + direction * (j + 1) * tread
        top = first_top + j * delta_z
        profile.append((end, top))
        if j < count - 1:
            profile.append((end, first_top + (j + 1) * delta_z))
    profile.append((start_y + direction * count * tread, base_z))
    n = len(profile)
    points = [(cx - width / 2, y, z) for y, z in profile] + [
        (cx + width / 2, y, z) for y, z in profile
    ]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(j, (j + 1) % n, (j + 1) % n + n, j + n) for j in range(n)]
    solid(points, faces)
    first_face = len(FACES) - len(faces)
    for j in range(n):
        p, q = profile[j], profile[(j + 1) % n]
        if abs(p[1] - q[1]) < 1e-8 and p[1] > base_z + 0.02:
            FACE_MATERIALS[first_face + 2 + j] = NAMES.index("marble_white")
            FACE_COLORS[first_face + 2 + j] = stone_variation([points[k] for k in faces[2 + j]])[0]
    DETAIL_COUNTS["coherentStairFlights"] += 1


def vault(x0, x1, y, spring, radius, thickness=0.24, rise=None):
    """A barrel vault tiled along X, crossing the gallery width in Y."""
    rings = max(1, round((x1 - x0) / 0.65))
    segments = 30
    for k in range(rings):
        lo = x0 + k * (x1 - x0) / rings + 0.005
        hi = x0 + (k + 1) * (x1 - x0) / rings - 0.005
        for j in range(segments):
            a, b = math.pi * j / segments + 0.001, math.pi * (j + 1) / segments - 0.001
            height = rise or radius
            profile = [
                (y + radius * math.cos(a), spring + height * math.sin(a)),
                (
                    y + (radius + thickness) * math.cos(a),
                    spring + (height + thickness) * math.sin(a),
                ),
                (
                    y + (radius + thickness) * math.cos(b),
                    spring + (height + thickness) * math.sin(b),
                ),
                (y + radius * math.cos(b), spring + height * math.sin(b)),
            ]
            points = [(lo, py, pz) for py, pz in profile] + [(hi, py, pz) for py, pz in profile]
            solid(
                points,
                [
                    (0, 3, 2, 1),
                    (4, 5, 6, 7),
                    (0, 1, 5, 4),
                    (1, 2, 6, 5),
                    (2, 3, 7, 6),
                    (3, 0, 4, 7),
                ],
            )


def build_materials():
    result = []
    for name, (color, roughness, metallic) in MATERIALS.items():
        material = bpy.data.materials.new(name)
        material.diffuse_color = color
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        result.append(material)
    return result


def export_piece(
    name,
    build,
    out,
    materials,
    pivot=(0, 0, 0),
    role="architecture",
    roof=False,
    clean_degenerate=False,
    horizontal_surface_up=False,
    heightfield_surface_up=False,
    vertex_color=None,
):
    VERTS.clear()
    FACES.clear()
    FACE_MATERIALS.clear()
    FACE_SMOOTH.clear()
    FACE_COLORS.clear()
    FACE_SEEDS.clear()
    FACE_BEVELS.clear()
    before = SIMPLE_PARTS
    build()
    verts = [(x - pivot[0], y + pivot[1], z - pivot[2]) for x, y, z in VERTS]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], FACES)
    for material in materials:
        mesh.materials.append(material)
    for polygon, mi, smooth in zip(mesh.polygons, FACE_MATERIALS, FACE_SMOOTH):
        polygon.material_index = mi
        polygon.use_smooth = smooth
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    color_layers = [bm.faces.layers.float.new("tint_" + channel) for channel in "rgb"]
    seed_layer = bm.faces.layers.float.new("seedAlpha")
    width_layer = bm.faces.layers.float.new("dress_bevel")
    for face in bm.faces:
        for k, layer in enumerate(color_layers):
            face[layer] = FACE_COLORS[face.index][k]
        face[seed_layer] = FACE_SEEDS[face.index]
        face[width_layer] = FACE_BEVELS[face.index]
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    edges = [e for e in bm.edges if e.is_manifold and e.calc_face_angle(0) > 0.42]
    groups = {}
    for edge in edges:
        width = round(edge.link_faces[0][width_layer], 5)
        groups.setdefault(width, []).append(edge)
    for width, group in sorted(groups.items()):
        result = bmesh.ops.bevel(
            bm,
            geom=group,
            offset=width,
            segments=3,
            affect="EDGES",
            profile=0.5,
            clamp_overlap=True,
        )
        for face in result["faces"]:
            if NAMES[face.material_index] in ("stone_cream", "marble_white"):
                for layer in color_layers:
                    face[layer] = min(1, max(0.92, face[layer] * 1.07))
    # Bevel creates faces but must not turn the piece seed into a lighting/tint value.
    # Each `solid()` starts with independent vertices, so connected face islands are pieces.
    remaining = set(bm.faces)
    while remaining:
        seed_face = remaining.pop()
        component = [seed_face]
        for face in component:
            for edge in face.edges:
                for neighbor in edge.link_faces:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.append(neighbor)
        stone_faces = [
            face
            for face in component
            if NAMES[face.material_index] in ("stone_cream", "marble_white")
        ]
        if stone_faces:
            counts = {}
            for face in stone_faces:
                value = round(face[seed_layer], 7)
                counts[value] = counts.get(value, 0) + 1
            piece_seed = max(counts, key=counts.get)
            for face in stone_faces:
                face[seed_layer] = piece_seed
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # Smooth only the authored revolution/cylinder faces; sharp profile changes,
    # end caps and disconnected masonry joints preserve their real edges.
    for edge in bm.edges:
        edge.smooth = edge.is_manifold and edge.calc_face_angle(0) < math.radians(30)
    color_layer = bm.loops.layers.float_color.new("COLOR_0")
    for face in bm.faces:
        tint = tuple(face[layer] for layer in color_layers)
        if NAMES[face.material_index] not in ("stone_cream", "marble_white"):
            tint += (1,)
        else:
            tint += (face[seed_layer],)
        for loop in face.loops:
            loop[color_layer] = tint
    if clean_degenerate:
        # Triangulate before cleanup: concave stair profiles can otherwise create
        # zero-area triangles only later, in the glTF triangulator.
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.dissolve_degenerate(bm, dist=1e-7, edges=list(bm.edges))
        collapsed = [f for f in bm.faces if f.calc_area() < 1e-10]
        if collapsed:
            bmesh.ops.delete(bm, geom=collapsed, context="FACES_ONLY")
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if horizontal_surface_up or heightfield_surface_up:
        if heightfield_surface_up:
            bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
            for face in bm.faces:face.smooth=True
            for edge in bm.edges:edge.smooth=True
        # Recalculation cannot choose an outside for disconnected open sheets.
        # Water exports explicitly request upward, horizontal surface normals.
        bm.normal_update()
        for face in bm.faces:
            if horizontal_surface_up and abs(face.normal.z) < .9999:
                raise ValueError(f"{name}: non-horizontal face in water surface")
            if face.normal.z < 0:
                face.normal_flip()
        bm.normal_update()
    if vertex_color:
        for face in bm.faces:
            for loop in face.loops:
                co=loop.vert.co
                loop[color_layer]=vertex_color(co.x+pivot[0],-co.y+pivot[1],co.z+pivot[2])
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    uv = mesh.uv_layers.new(name="UV0")
    for polygon in mesh.polygons:
        axis = 2 if heightfield_surface_up else max(range(3), key=lambda k: abs(polygon.normal[k]))
        axes = [k for k in range(3) if k != axis]
        for li in polygon.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            # Reintroduce the world pivot so neighboring coplanar UVs share a phase.
            world = (co.x + pivot[0], co.y - pivot[1], co.z + pivot[2])
            uv.data[li].uv = (world[axes[0]] / 2, world[axes[1]] / 2)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(out / f"{name}.glb"),
        export_format="GLB",
        use_selection=True,
        export_texcoords=True,
        export_normals=True,
        export_tangents=clean_degenerate,
        export_vertex_color="NAME",
        export_vertex_color_name="COLOR_0",
        export_materials="EXPORT",
        export_yup=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )
    mesh.calc_loop_triangles()
    bounds = [
        [round(min(v.co[k] for v in mesh.vertices), 4) for k in range(3)],
        [round(max(v.co[k] for v in mesh.vertices), 4) for k in range(3)],
    ]
    PIECES.append(
        {
            "id": name,
            "file": name + ".glb",
            "materials": sorted({NAMES[p.material_index] for p in mesh.polygons}),
            "triangles": len(mesh.loop_triangles),
            "boundsBlender": bounds,
            "assembledSimpleParts": SIMPLE_PARTS - before,
        }
    )
    OBJECTS.append({"id": name, "meshId": name, "position": list(pivot), "yaw": 0, "role": role})
    if roof:
        ROOFS.append(name)
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    print(f"PRODUCED {name} {PIECES[-1]['triangles']} triangles", flush=True)
