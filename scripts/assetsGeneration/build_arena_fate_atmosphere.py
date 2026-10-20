#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Original closed flame geometry and sample-free, seamless ambient PCM loops.

Blender builds three curved tongues; NumPy synthesises original noise and crackles.
No external sample, voice, texture, sourcebook image or previously approved asset is edited.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/arena-fate-atmosphere"
BLENDER = Path(r"D:\Blender Foundation\Blender 5.2\blender.exe")
RATE = 48000
try:
    import bpy
except ImportError:
    bpy = None


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def flame(out):
    vertices, faces = [], []
    for height, radius, offset, lean, phase in [
        (0.68, 0.125, (-0.03, 0), (0.10, 0.025), 0),
        (0.44, 0.092, (-0.10, 0.055), (-0.09, 0.015), 1.7),
        (0.52, 0.085, (0.075, -0.045), (0.06, -0.045), 3.3),
    ]:
        base = len(vertices)
        sides, rings = 40, 14
        for ring in range(rings):
            t = ring / rings
            width = radius * (0.36 + 1.9 * t) * (1 - t) ** 1.2
            cx = offset[0] + lean[0] * t * t + 0.024 * math.sin(t * math.pi * 2 + phase) * t
            cy = offset[1] + lean[1] * t * t
            for j in range(sides):
                a = j * math.tau / sides
                r = width * (1 + 0.07 * math.sin(3 * a + t * 5 + phase))
                vertices.append((cx + r * math.cos(a), -(cy + r * 0.72 * math.sin(a)), height * t))
        for ring in range(rings - 1):
            for j in range(sides):
                a, b = base + ring * sides + j, base + ring * sides + (j + 1) % sides
                faces.append((a, b, b + sides, a + sides))
        tip = len(vertices)
        vertices.append((offset[0] + lean[0], -(offset[1] + lean[1]), height))
        for j in range(sides):
            faces.append(
                (base + (rings - 1) * sides + j, base + (rings - 1) * sides + (j + 1) % sides, tip)
            )
        faces.append(tuple(base + j for j in range(sides - 1, -1, -1)))
    mesh = bpy.data.meshes.new("afa-flame")
    mesh.from_pydata(vertices, [], faces)
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(edge.is_manifold for edge in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    colors = mesh.color_attributes.new(name="COLOR_0", type="FLOAT_COLOR", domain="CORNER")
    uv = mesh.uv_layers.new(name="UV0")
    for poly in mesh.polygons:
        poly.use_smooth = len(poly.vertices) <= 4
        for index in poly.loop_indices:
            co = mesh.vertices[mesh.loops[index].vertex_index].co
            t = max(0, min(1, co.z / 0.68))
            colors.data[index].color = (1.0, 0.17 + 0.70 * t**0.7, 0.015 + 0.16 * t**1.8, t)
            uv.data[index].uv = (co.x / 2, co.z / 2)
    material = bpy.data.materials.new("flame_emissive")
    material.diffuse_color = (1, 0.36, 0.03, 1)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1, 0.36, 0.03, 1)
    mesh.materials.append(material)
    obj = bpy.data.objects.new("afa-flame", mesh)
    bpy.context.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(out / "afa-flame.glb"),
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
    bounds = [
        [min(p[k] for p in vertices) for k in range(3)],
        [max(p[k] for p in vertices) for k in range(3)],
    ]
    from mathutils import Vector

    bpy.ops.object.camera_add(location=(1.5, -2, 1.3))
    camera = bpy.context.object
    camera.rotation_euler = (
        (Vector((0, 0, 0.30)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    )
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.95
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "VERTEX"
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (0.035, 0.04, 0.055)
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(out / "flame-geometry.png")
    bpy.ops.render.render(write_still=True)
    return {
        "id": "afa-flame",
        "file": "afa-flame.glb",
        "materials": ["flame_emissive"],
        "triangles": len(mesh.loop_triangles),
        "sha256": sha(out / "afa-flame.glb"),
        "dimensions": [bounds[1][k] - bounds[0][k] for k in range(3)],
        "origin": [0, 0, 0],
        "closedTongues": 3,
        "vertexAlpha": "normalised height; zero motion at root",
        "collision": "none",
    }


def loop_crossfade(values, count):
    import numpy as np

    # Both splice boundaries remain consecutive samples of their original waveform.
    t = np.linspace(0, 1, count, endpoint=True)
    weight = t * t * (3 - 2 * t)
    blend = values[-count:] * (1 - weight) + values[:count] * weight
    return np.concatenate((blend, values[count:-count]))


def sound(out, name, seconds, seed):
    import numpy as np

    rng = np.random.default_rng(seed)
    count = int((seconds + 0.75) * RATE)
    frequencies = np.fft.rfftfreq(count, 1 / RATE)
    white = rng.normal(size=count)
    spectrum = np.fft.rfft(white)
    if name == "exterior-breeze":
        response = (frequencies / (frequencies + 45)) ** 2 / (1 + (frequencies / 900) ** 2)
        response[0] = 0
        values = np.fft.irfft(spectrum * response, n=count)
        t = np.arange(count) / count
        values *= (
            0.70 + 0.20 * np.sin(math.tau * 2 * t + 0.3) + 0.08 * np.sin(math.tau * 7 * t + 1.2)
        )
        target_rms = 0.044
    else:
        response = (frequencies / (frequencies + 260)) / (1 + (frequencies / 6300) ** 3)
        response[0] = 0
        values = np.fft.irfft(spectrum * response, n=count) * 0.05
        for _ in range(110):
            duration = int(RATE * rng.uniform(0.009, 0.115))
            start = int(rng.integers(0, count - duration))
            t = np.arange(duration) / duration
            envelope = np.sin(math.pi * t) ** 2 * np.exp(-7 * t)
            burst = rng.normal(size=duration)
            burst -= np.roll(burst, 1) * 0.6
            values[start : start + duration] += envelope * burst * rng.uniform(0.15, 0.75)
        target_rms = 0.050
    values = loop_crossfade(values, int(0.75 * RATE))
    values -= values.mean()
    values *= target_rms / math.sqrt(float(np.mean(values**2)))
    # Extremely short, smooth zero seam guarantees no single-sample loop click.
    width = int(0.012 * RATE)
    envelope = np.sin(np.linspace(0, math.pi / 2, width)) ** 2
    values[:width] *= envelope
    values[-width:] *= envelope[::-1]
    values *= min(1, 0.82 / float(np.max(np.abs(values))))
    pcm = np.round(values * 32767).astype("<i2")
    path = out / (name + ".wav")
    with wave.open(str(path), "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(RATE)
        stream.writeframes(pcm.tobytes())
    differences = np.abs(np.diff(pcm.astype(np.int32)))
    return {
        "id": name,
        "file": path.name,
        "sha256": sha(path),
        "sampleRate": RATE,
        "channels": 1,
        "bits": 16,
        "seconds": len(pcm) / RATE,
        "loop": True,
        "peakDbFS": round(20 * math.log10(float(np.max(np.abs(values)))), 3),
        "rmsDbFS": round(20 * math.log10(math.sqrt(float(np.mean(values**2)))), 3),
        "loopBoundaryStepPcm": int(abs(int(pcm[-1]) - int(pcm[0]))),
        "boundarySamples": [int(pcm[0]), int(pcm[-1])],
        "maxAdjacentStepPcm": int(differences.max()),
        "provenance": "Original deterministic noise/filter/event synthesis; no external samples or voices",
        "seed": seed,
    }


def generate(out):
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mesh = flame(out)
    audio = [sound(out, "exterior-breeze", 24, 8673), sound(out, "local-crackle", 16, 9151)]
    doc = {
        "format": "jadg-arena-fate-atmosphere",
        "version": 1,
        "generator": "scripts/assetsGeneration/build_arena_fate_atmosphere.py",
        "installer": "scripts/maps/arena_fate_atmosphere.py",
        "coordinates": "metres; manifest X east Y south Z up; GLB X east Y up Z south",
        "meshes": [mesh],
        "audio": audio,
        "qaReport": "generation-report.json",
        "previews": ["flame-geometry.png"],
        "placements": {
            "afp-brazier": {
                "flameScale": 0.82,
                "audio": "local-crackle",
                "volume": 0.32,
                "audioRadiusMetres": 5,
            },
            "afp-wall-lamp": {"flameScale": 0.16, "audio": None},
        },
        "globalAudio": {
            "id": "exterior-breeze",
            "position": [0, 0, 8],
            "volume": 0.14,
            "audioRadiusMetres": 125,
            "occlusion": True,
        },
        "notes": [
            "Three closed tongues; emissive/WPO shader animates tips only.",
            "Fire remains a separate non-colliding mesh; point lights stay owned by scene builder.",
            "One exterior loop in persistent map; only braziers add attenuated crackles.",
            "No crowd recording, voice, external sample or sourcebook imagery.",
        ],
    }
    (out / "manifest.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    verify(out)


def verify(out):
    import numpy as np

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_arena_fate_props import accessor_values, read_glb

    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    item = manifest["meshes"][0]
    doc, raw = read_glb(out / item["file"])
    assert sha(out / item["file"]) == item["sha256"]
    assert len(doc["meshes"]) == 1
    p = doc["meshes"][0]["primitives"][0]
    assert all(k in p["attributes"] for k in ["POSITION", "NORMAL", "TEXCOORD_0", "COLOR_0"])
    vertices = accessor_values(doc, raw, p["attributes"]["POSITION"])
    colors = accessor_values(doc, raw, p["attributes"]["COLOR_0"])
    assert all(0 <= v <= 1 for c in colors for v in c)
    assert all(abs(c[3] - v[1] / 0.68) < 0.00005 for c, v in zip(colors, vertices))
    indices = [x[0] for x in accessor_values(doc, raw, p["indices"])]
    edges = {}
    for i in range(0, len(indices), 3):
        triangle = [tuple(round(v, 6) for v in vertices[indices[i + j]]) for j in range(3)]
        for j in range(3):
            edge = tuple(sorted((triangle[j], triangle[(j + 1) % 3])))
            edges[edge] = edges.get(edge, 0) + 1
    assert all(count == 2 for count in edges.values())
    for entry in manifest["audio"]:
        path = out / entry["file"]
        assert sha(path) == entry["sha256"]
        with wave.open(str(path), "rb") as stream:
            assert (
                stream.getnchannels() == 1
                and stream.getsampwidth() == 2
                and stream.getframerate() == RATE
            )
            pcm = np.frombuffer(stream.readframes(stream.getnframes()), dtype="<i2")
        assert pcm[0] == pcm[-1] == 0
        assert abs(int(pcm[1])) <= 1 and abs(int(pcm[-2])) <= 1
        assert np.max(np.abs(pcm.astype(np.int32))) < 32767
    report = {
        "generator": manifest["generator"],
        "status": "passed",
        "triangles": len(indices) // 3,
        "closedTongues": 3,
        "closedEdgesAfterPositionWeld": True,
        "requiredAttributesPresent": True,
        "vertexColorAlphaHeightVerified": True,
        "audio": manifest["audio"],
        "limits": [
            "Shader compilation, visibility and audio spatialisation must be checked by the Unreal builder.",
            "Audio describes air and burning wood only, not crowd activity.",
        ],
    }
    (out / "generation-report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"VERIFIED atmosphere: {len(indices) // 3} closed-flame triangles and 2 original PCM loops",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--verify", action="store_true")
    argv = (sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []) if bpy else None
    args = parser.parse_args(argv)
    if args.verify:
        verify(args.output)
        return 0
    if bpy:
        generate(args.output)
        return 0
    return subprocess.run(
        [
            str(BLENDER),
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
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
