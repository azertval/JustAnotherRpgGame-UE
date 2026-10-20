#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Build the atlas-aligned water skin used by build_arenarea_landscape.py."""

from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Source/Elements/Assets/Built/arenarea-landscape"
OUT.mkdir(parents=True, exist_ok=True)
d = np.load(ROOT / "Saved/Jadg/arenarea-landscape/water.npz")
x, y, z, wet = (d[k] for k in ("x", "y", "z", "wet"))
ny, nx = x.shape
mask = wet[:-1, :-1] | wet[1:, :-1] | wet[:-1, 1:] | wet[1:, 1:]
row, col = np.nonzero(mask)
a = row * nx + col
faces = np.stack([a, a + nx, a + nx + 1, a + 1], axis=1)
used, mapped = np.unique(faces, return_inverse=True)
verts = np.stack([x.ravel()[used], -y.ravel()[used], z.ravel()[used]], axis=1)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
mesh = bpy.data.meshes.new("arenarea-eaux")
mesh.from_pydata(verts.tolist(), [], mapped.reshape(-1, 4).tolist())
mesh.update()
mat = bpy.data.materials.new("water-placeholder")
mat.diffuse_color = (0.04, 0.20, 0.24, 1)
mesh.materials.append(mat)
uv = mesh.uv_layers.new(name="UV0")
for p in mesh.polygons:
    p.use_smooth = True
    for li in p.loop_indices:
        co = mesh.vertices[mesh.loops[li].vertex_index].co
        uv.data[li].uv = (co.x / 10, co.y / 10)
obj = bpy.data.objects.new("arenarea-eaux", mesh)
bpy.context.collection.objects.link(obj)
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
path = OUT / "arenarea-eaux.glb"
bpy.ops.export_scene.gltf(
    filepath=str(path),
    export_format="GLB",
    use_selection=True,
    export_yup=True,
    export_animations=False,
    export_normals=True,
)
report = {
    "generator": "scripts/assetsGeneration/build_arenarea_water.py",
    "meshes": [
        {
            "id": "arenarea-eaux",
            "file": path.name,
            "triangles": len(faces) * 2,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    ],
}
(OUT / "manifest.json").write_text(json.dumps(report, indent=2), encoding="utf8")
print("ARENAREA_WATER_OK", len(faces) * 2)
