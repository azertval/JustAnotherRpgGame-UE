"""Small engraved additions to the existing Arena podium; Blender only at build time.

Use KIT.extend(entries(w)) in build_arena_fate_props.py. No master is modified.
Plaques: local engine X horizontal, +Y outward, Z upward; bottom origin.
Back Y=0, front Y=.135, width1.38, height.68 metres. At scale1 place
on its arena-facing side: local_position(plinth.position, plinth.yaw,
(0,-1.025,.455)), yaw=plinth.yaw+180 (same yaw as its statue).
The backing intentionally encloses the old lozenge; recess floor at Y=.110
remains outside it. No zero-depth decal or raised substitute lettering.
Fumetsu collar: centre on existing plinth, bottom Z=1.30; max width2.12m
stays inside its 2.40m foot. A double stone course distinguishes its support
without inventing heraldry or engraving an assertion about its divinity.
"""

from pathlib import Path

# Exact canonical forms in capitale.md:91-106; line breaks are layout only.
NAMES = (
    ("breith", "Breith"),
    ("bauron", "Bauron"),
    ("bas", "Bás"),
    ("dorsi", "Dorsi"),
    ("ba-ka", "Ba-Ka"),
    ("fruitful", "Fruitful"),
    ("aibidh", "Aibidh"),
    ("fumetsu", "Fumetsu\nTenshinkin"),
    ("nature-spirits", "Les Esprits\nde la Nature"),
    ("glorious-one", "Glorious One"),
    ("tamera", "Tamera"),
    ("lumina", "Lumina"),
    ("duality", "Tamera & Bauron"),
    ("oigridh", "Òigridh"),
)


def engraved(w, label):
    import bpy
    from mathutils import Vector

    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.0675))
    slab = bpy.context.object
    slab.dimensions = (1.38, 0.68, 0.135)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = slab.modifiers.new("Stone edge", "BEVEL")
    bevel.width, bevel.segments = 0.009, 3
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    curve = bpy.data.curves.new("Carving stencil", "FONT")
    curve.body, curve.size = label, 1.0
    font = Path("C:/Windows/Fonts/times.ttf")
    if not font.is_file():
        raise RuntimeError("The reproducible inscription font is missing: " + str(font))
    curve.font = bpy.data.fonts.load(str(font), check_existing=True)
    curve.align_x = "CENTER"
    curve.space_line = 0.95
    curve.resolution_u = 12
    cutter = bpy.data.objects.new("Carving stencil", curve)
    bpy.context.collection.objects.link(cutter)
    bpy.context.view_layer.update()
    bounds = [Vector(v) for v in cutter.bound_box]
    lo = [min(v[k] for v in bounds) for k in range(2)]
    hi = [max(v[k] for v in bounds) for k in range(2)]
    scale = min(1.18 / (hi[0] - lo[0]), 0.46 / (hi[1] - lo[1]), 0.29)
    curve.size *= scale
    # Scale typography only, keeping physical cut depth independent of name length.
    curve.extrude = 0.04
    cutter.location = (-(lo[0] + hi[0]) * 0.5 * scale, -(lo[1] + hi[1]) * 0.5 * scale, 0.110)
    bpy.ops.object.select_all(action="DESELECT")
    cutter.select_set(True)
    bpy.context.view_layer.objects.active = cutter
    bpy.ops.object.convert(target="MESH")
    cutter = bpy.context.object
    depth_min = min((cutter.matrix_world @ v.co).z for v in cutter.data.vertices)
    cutter.location.z += 0.110 - depth_min
    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = slab
    cut = slab.modifiers.new("Letters cut into stone", "BOOLEAN")
    cut.operation, cut.solver, cut.object = "DIFFERENCE", "EXACT", cutter
    bpy.ops.object.modifier_apply(modifier=cut.name)
    if len(slab.data.polygons) < 60:
        raise RuntimeError("Inscription boolean produced no readable recesses: " + label)
    # Transform authored slab XY/text-depth Z to kit X/depth Y/height Z.
    points = [slab.matrix_world @ v.co for v in slab.data.vertices]
    w.solid(
        [(p.x, p.z, p.y + 0.34) for p in points],
        [tuple(p.vertices) for p in slab.data.polygons],
        "stone_cream",
        bevel=0,
        color=(0.97, 0.96, 0.94, 1),
        seed_alpha=0.61,
    )
    for obj in (cutter, slab):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if not data.users:
            bpy.data.meshes.remove(data)
    # Conversion may already release its curve datablock.


def fumetsu_collar(w):
    # Two restrained stepped courses. Inner edge at .970 embeds in .975 plinth;
    # exterior1.06 stays well within1.20 foot. Entire ring rests against stone.
    for half, z, height in ((1.035, 0, 0.075), (1.06, 0.105, 0.075)):
        inner = 0.970
        thick = half - inner
        for sign in (-1, 1):
            w.block(0, sign * (inner + half) / 2, z, 2 * half, thick, height, "marble_white")
            w.block(sign * (inner + half) / 2, 0, z, thick, 2 * inner, height, "marble_white")


def entries(w):
    result = [
        (
            "afp-nameplate-" + slug,
            lambda label=label: engraved(w, label),
            ["coursive"],
            "Plaque de pierre, nom canonique réellement gravé : " + label.replace("\n", " "),
        )
        for slug, label in NAMES
    ]
    result.append(
        (
            "afp-fumetsu-plinth-collar",
            lambda: fumetsu_collar(w),
            ["coursive"],
            "Double assise sobre distinguant le socle de Fumetsu, sans emblème inventé.",
        )
    )
    return result
