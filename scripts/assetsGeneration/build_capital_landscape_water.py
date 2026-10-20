#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Water skins for the district Landscape tiles, no architecture or embankment meshes."""

from pathlib import Path
import json
import hashlib
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Saved/Jadg/capital-landscape-districts"
OUT = ROOT / "Source/Elements/Assets/Built/capital-landscape-districts"
OUT.mkdir(parents=True, exist_ok=True)
manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf8"))
rows = []
for tile in manifest["tiles"]:
    if tile["wetFraction"] == 0:
        continue
    with np.load(DATA / "tiles" / tile["id"] / "fields.npz") as f:
        wet, z = f["water"], f["water_z"]
    ny, nx = wet.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    x, y = xx*tile["spacing_m"]+tile["origin_m"][0], yy*tile["spacing_m"]+tile["origin_m"][1]
    cells = wet[:-1, :-1] | wet[1:, :-1] | wet[:-1, 1:] | wet[1:, 1:]
    row, col = np.nonzero(cells)
    a = row*nx + col
    faces = np.stack([a, a+nx, a+nx+1, a+1], axis=1)
    used, mapped = np.unique(faces, return_inverse=True)
    verts = np.stack([x.ravel()[used], -y.ravel()[used], z.ravel()[used]], axis=1)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    name = "eau-"+tile["id"]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts.tolist(), [], mapped.reshape(-1, 4).tolist())
    mesh.update()
    mat = bpy.data.materials.new("water-placeholder")
    mat.diffuse_color = (.04, .20, .24, 1)
    mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name="UV0")
    for p in mesh.polygons:
        p.use_smooth = True
        for li in p.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv = (co.x/10, co.y/10)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = OUT / (name+".glb")
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True,
                             export_yup=True, export_animations=False, export_normals=True)
    rows.append(dict(id=name, file=path.name, triangles=len(faces)*2,
                     sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    bpy.data.materials.remove(mat)
    print("CAPITAL_WATER", name, len(faces)*2, flush=True)
(OUT / "manifest.json").write_text(json.dumps(dict(generator=__file__, meshes=rows), indent=2), encoding="utf8")
# A revised shoreline can leave a formerly wet tile dry. Remove only this producer's
# obsolete meshes after every replacement and its manifest have been written.
current = {row["file"] for row in rows}
for obsolete in OUT.glob("eau-t??_??.glb"):
    if obsolete.name not in current:
        obsolete.unlink()
print("CAPITAL_WATER_OK", len(rows))
