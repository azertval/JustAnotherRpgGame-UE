#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Phase 1: metric Arenarea relief, reservations, paint masks and water geometry.

Only Q07 is authored. The rectangular margin provides a future neighbourhood seam.
Source: Source/Elements/Terrain/arenarea/definition.json. No image tracing.
"""

from pathlib import Path
import json
import math
import hashlib
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved/Jadg/arenarea-landscape"
DEFINITION = ROOT / "Source/Elements/Terrain/arenarea/definition.json"
LAYERS = ("Pelouse", "Prairie", "HerbeSauvage", "Terre", "Sable", "Roche", "Pavage")
sys.path.insert(0, str(ROOT / "scripts/maps"))
import jadg_map  # noqa: E402


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def uv(p):
    return [(p[1] - 680) * 6.75, -(p[0] - 1000) * 6.75, *p[2:]]


def segment(x, y, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    t = np.clip(((x - a[0]) * vx + (y - a[1]) * vy) / max(vx * vx + vy * vy, 1e-6), 0, 1)
    return np.hypot(x - a[0] - t * vx, y - a[1] - t * vy), t


def box_distance(x, y, bounds):
    x0, y0, x1, y1 = bounds
    return np.hypot(
        np.maximum(np.maximum(x0 - x, x - x1), 0), np.maximum(np.maximum(y0 - y, y - y1), 0)
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = json.loads(DEFINITION.read_text(encoding="utf8"))
    ox, oy = d["origin_m"]
    qx, qy = d["quads"]
    step = d["spacing_m"]
    y, x = np.mgrid[0 : qy + 1, 0 : qx + 1].astype(np.float32)
    x = x * step + ox
    y = y * step + oy
    shape = x.shape

    def polygon(points):
        image = Image.new("L", (qx + 1, qy + 1))
        ImageDraw.Draw(image).polygon(
            [((p[0] - ox) / step, (p[1] - oy) / step) for p in points], fill=255
        )
        return np.asarray(image) > 0

    district = polygon([[e, -n] for e, n in d["district"]["polygon_m"]])
    # Patrician terrace, 14..28m. Large forms precede the engineered platforms.
    h = 19 + 9 * smooth(-2700, -700, x) + 0.7 * np.sin(y / 380) * np.sin(x / 270)
    h = np.clip(h, 14, 28)
    w = d["water"]
    bay_poly = [uv(p) for p in w["bay_outline_uv"]]
    bay = polygon(bay_poly)
    coast_distance = np.full(shape, np.inf, dtype=np.float32)
    for a, b in zip(bay_poly, bay_poly[1:] + bay_poly[:1]):
        dist, _ = segment(x, y, a, b)
        coast_distance = np.minimum(coast_distance, dist)
    h = np.where(bay, -2 - np.minimum(coast_distance * 0.02, 8), h * smooth(0, 180, coast_distance))
    water_z = np.zeros(shape, dtype=np.float32)
    water_mask = bay.copy()
    bank_distance = coast_distance.copy()

    def channel(points, widths, levels, depth, bank_blend):
        nonlocal h, water_z, water_mask, bank_distance
        pts = [uv(p) for p in points]
        closest = np.full(shape, np.inf, dtype=np.float32)
        radius = np.zeros(shape, dtype=np.float32)
        surface = np.zeros(shape, dtype=np.float32)
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            dist, t = segment(x, y, a, b)
            take = dist < closest
            closest = np.minimum(closest, dist)
            radius = np.where(take, (widths[i] * (1 - t) + widths[i + 1] * t) / 2, radius)
            surface = np.where(take, levels[i] * (1 - t) + levels[i + 1] * t, surface)
        edge = closest - radius
        bed = surface - depth + (depth + 0.3) * smooth(-radius * 0.65, 0, edge)
        target = np.where(
            edge < 0, bed, surface + 0.3 + (h - surface - 0.3) * smooth(0, bank_blend, edge)
        )
        h = np.minimum(h, target)
        wet = edge < 1
        water_z = np.where(wet, np.maximum(surface, water_z), water_z)
        water_mask |= wet
        bank_distance = np.minimum(bank_distance, np.abs(edge))

    channel(w["river_center_uv"], w["river_width_m"], w["river_water_z_m"], 6, 170)
    # Atlas endpoint stops ~100m before its bay polygon: continue the channel
    # into the bay, rather than leave an isolated decorative water trench.
    channel(
        w["pool_connection_uv"] + [[780, 330]],
        [24] * 5,
        w["pool_connection_water_z_m"] + [0],
        3,
        85,
    )
    # Natural Pool is the explicit low coastal exception to the 14..28m urban band.
    pool = next(s for s in d["sites"] if s["id"] == "L07-06")
    px, py = pool["xy_m"][0], -pool["xy_m"][1]
    radius = np.hypot((x - px) / 30, (y - py) / 60)
    pool_h = -3 + 3.2 * smooth(0.3, 1, radius)
    h = np.minimum(h, np.where(radius <= 1, pool_h, 0.2 + (h - 0.2) * smooth(1, 4.5, radius)))
    water_z = np.where(radius <= 1, 0.2, water_z)
    water_mask |= radius <= 1
    bank_distance = np.minimum(bank_distance, abs(radius - 1) * 30)
    reserved = np.zeros(shape, dtype=np.float32)
    paving = np.zeros(shape, dtype=np.float32)
    gardens = np.zeros(shape, dtype=np.float32)
    for site in d["sites"]:
        if site["geometry_type"] == "water":
            continue
        cx, cy = site["xy_m"][0], -site["xy_m"][1]
        sx, sy = site["parcel_m"]
        dist = box_distance(x, y, [cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2])
        alpha = 1 - smooth(0, 120, dist)
        h = h * (1 - alpha) + site["ground_z_m"] * alpha
        reserved = np.maximum(reserved, dist == 0)
        paving = np.maximum(paving, 1 - smooth(0, 4, dist))
    for g in d["gardens"]:
        dist = box_distance(x, y, g["bounds"])
        alpha = 1 - smooth(0, 65, dist)
        h = h * (1 - alpha) + g["z"] * alpha
        gardens = np.maximum(gardens, 1 - smooth(0, 4, dist))

    routes = [r for r in d["roads"] if r["id"] == "R01"]
    routes = [{**r, "points": [uv(p) for p in r["nodes"]]} for r in routes]
    # The atlas' straight R01 segment intersects the bazaar's +24m platform
    # while still climbing from +8m. Turn east before it and hold +24m through
    # the public block; this also leaves room for the pool's natural slope.
    routes[0]["points"] = [
        routes[0]["points"][0],
        [-1552.5, 1350, 24],
        [-1552.5, 1230, 24],
        [-1552.5, 930, 24],
        *routes[0]["points"][1:],
    ]
    routes[0]["localRevision"] = (
        "Eastern approach to bazaar +24m; original nodes retained in definition.json"
    )
    # New local connections are explicitly design, not claims about the book.
    local = [
        (
            "acces-arena",
            24,
            [[-2463.75, -135, 20], [-2220, -135, 20], [-2100, -135, 20], [-1653.75, -202.5, 23]],
        ),
        ("acces-casino", 15, [[-1653.75, -202.5, 23], [-1417.5, -202.5, 23]]),
        ("acces-hippodrome", 15, [[-1890, -877.5, 22], [-1530, -1100, 23], [-1215, -1417.5, 23]]),
        (
            "acces-bazaar",
            15,
            [[-1552.5, 1080, 24], [-1410, 1080, 24], [-1410, 500, 24], [-1653.75, -202.5, 23]],
        ),
        ("jardin-arena", 6, [[-2220, -135, 20], [-2210, -440, 23], [-2130, -440, 23]]),
        (
            "jardin-casino",
            6,
            [[-1417.5, -202.5, 23], [-1417.5, -308, 23], [-1417.5, -430, 26], [-1245, -430, 26]],
        ),
        ("jardin-bas", 6, [[-2220, -135, 20], [-2100, -110, 20], [-2040, -110, 17]]),
    ]
    routes += [
        {"id": name, "width": width, "points": pts, "status": "design-local"}
        for name, width, pts in local
    ]
    road_distance = np.full(shape, np.inf, dtype=np.float32)
    for r in routes:
        nearest = np.full(shape, np.inf, dtype=np.float32)
        target = h.copy()
        for a, b in zip(r["points"], r["points"][1:]):
            dist, t = segment(x, y, a, b)
            target = np.where(dist < nearest, a[2] * (1 - t) + b[2] * t, target)
            nearest = np.minimum(nearest, dist)
        edge = nearest - r["width"] / 2
        alpha = (1 - smooth(0, 45, edge)) * (~water_mask)
        h = h * (1 - alpha) + target * alpha
        road_distance = np.minimum(road_distance, edge)
        paving = np.maximum(paving, 1 - smooth(0, 2, edge))
    # Site platforms have priority over access grades, as prescribed by the atlas.
    for site in d["sites"]:
        if site["geometry_type"] == "water":
            continue
        cx, cy = site["xy_m"][0], -site["xy_m"][1]
        sx, sy = site["parcel_m"]
        dist = box_distance(x, y, [cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2])
        alpha = 1 - smooth(0, 40, dist)
        h = h * (1 - alpha) + site["ground_z_m"] * alpha
    encoded = np.rint(32768 + h * 128).astype("<u2")
    h = (encoded.astype(np.float32) - 32768) / 128
    route_profiles = []
    for route in routes:
        grades = []
        for a, b in zip(route["points"], route["points"][1:]):
            count = int(math.dist(a[:2], b[:2]) / 2) + 1
            t = np.linspace(0, 1, count)
            rx, ry = a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t
            fx, fy = (rx - ox) / step, (ry - oy) / step
            ix, iy = np.floor(fx).astype(int), np.floor(fy).astype(int)
            fx, fy = fx - ix, fy - iy
            rz = (h[iy, ix] * (1 - fx) + h[iy, ix + 1] * fx) * (1 - fy) + (
                h[iy + 1, ix] * (1 - fx) + h[iy + 1, ix + 1] * fx
            ) * fy
            grades.extend((abs(np.diff(rz)) / np.hypot(np.diff(rx), np.diff(ry)) * 100).tolist())
        route_profiles.append({"id": route["id"], "measuredMaxGradePercent": max(grades)})
    (OUT / "route-profiles.json").write_text(json.dumps(route_profiles, indent=2), encoding="utf8")
    if max(r["measuredMaxGradePercent"] for r in route_profiles) > 8:
        raise RuntimeError(
            "A local access exceeds the 8% production limit; see route-profiles.json"
        )
    gy, gx = np.gradient(h, step)
    slope = np.hypot(gx, gy)
    sand = (1 - smooth(5, 28, bank_distance)) * (1 - paving)
    rock = smooth(0.20, 0.50, slope) * (1 - paving)
    prairie = 0.5 + 0.5 * np.sin(x / 110) * np.sin(y / 97)
    vals = np.stack(
        [
            gardens,
            (1 - gardens) * prairie * 0.7,
            (1 - gardens) * (1 - prairie * 0.7),
            np.full(shape, 0.08),
            sand,
            rock,
            paving * 10,
        ]
    )
    vals[1:4] *= (1 - sand) * (1 - rock) * (1 - paving)
    vals[0] *= 1 - paving
    vals[4] = np.maximum(vals[4], water_mask.astype(np.float32))
    vals /= np.maximum(vals.sum(axis=0), 0.0001)
    weights = np.floor(vals * 255).astype(np.uint8)
    remainder = (255 - weights.sum(axis=0)).astype(np.uint8)
    winner = vals.argmax(axis=0)
    for i in range(len(LAYERS)):
        weights[i] += remainder * (winner == i)
    assert np.all(weights.sum(axis=0) == 255)
    (OUT / "heights.r16").write_bytes(encoded.tobytes())
    (OUT / "weights.r8").write_bytes(weights.tobytes())
    np.savez_compressed(
        OUT / "placement.npz",
        height=h,
        district=district,
        gardens=gardens,
        water=water_mask,
        water_z=water_z,
        slope=slope,
        reserved=reserved,
        road_distance=road_distance,
        bank_distance=bank_distance,
    )
    # Water follows real variable river levels. A 4m skin extends under its banks.
    np.savez_compressed(
        OUT / "water.npz",
        x=x[::2, ::2],
        y=y[::2, ::2],
        z=water_z[::2, ::2],
        wet=water_mask[::2, ::2],
    )
    preview = np.zeros((*shape, 3), dtype=np.float32)
    palette = np.array(
        [
            [61, 105, 53],
            [103, 128, 66],
            [78, 109, 52],
            [130, 109, 79],
            [190, 177, 139],
            [115, 115, 105],
            [174, 163, 141],
        ]
    )
    for i in range(7):
        preview += vals[i, :, :, None] * palette[i]
    shade = np.clip(0.85 - gx * 0.8 - gy * 0.7, 0.5, 1.2)
    preview *= shade[:, :, None]
    preview[water_mask] = [45, 115, 133]
    preview[~district] *= 0.57
    im = Image.fromarray(np.uint8(np.clip(preview, 0, 255)))
    draw = ImageDraw.Draw(im)
    draw.line(
        [((p[0] - ox) / step, (-p[1] - oy) / step) for p in d["district"]["polygon_m"]]
        + [
            (
                (d["district"]["polygon_m"][0][0] - ox) / step,
                (-d["district"]["polygon_m"][0][1] - oy) / step,
            )
        ],
        fill=(245, 228, 177),
        width=3,
    )
    for s in d["sites"]:
        draw.text(
            ((s["xy_m"][0] - ox) / step, (-s["xy_m"][1] - oy) / step),
            s["name"],
            fill=(255, 255, 255),
        )
    im.thumbnail((1100, 1400))
    im.save(OUT / "plan-relief.png")
    report = {
        "phase": "01-relief",
        "districtAreaKm2": d["district"]["area_km2"],
        "extentMetres": [qx * step, qy * step],
        "quads": [qx, qy],
        "components": qx * qy // (63 * 63),
        "sampleSpacingMetres": step,
        "altitudes": [float(h.min()), float(h.max())],
        "layers": list(LAYERS),
        "routes": routes,
        "sourceSha256": hashlib.sha256(DEFINITION.read_bytes()).hexdigest(),
        "heightSha256": hashlib.sha256(encoded.tobytes()).hexdigest(),
        "platforms": [{"id": s["id"], "z": s["ground_z_m"]} for s in d["sites"]],
        "roadMaxGradePercent": max(
            abs(b[2] - a[2]) / math.dist(a[:2], b[:2]) * 100
            for r in routes
            for a, b in zip(r["points"], r["points"][1:])
        ),
    }
    (OUT / "relief.json").write_text(json.dumps(report, indent=2), encoding="utf8")
    # Limited playable inspection patch; the complete district is editable in UE.
    cx, cy = -2220, -135
    ix, iy = int((cx - 100 - ox) / step), int((cy - 100 - oy) / step)
    field = h[iy : iy + 101, ix : ix + 101]
    shots = [
        ("parvis", [-2250, -140, 22], 70, 30, 110),
        ("jardins", [-2130, -440, 24], 35, 30, 95),
        ("natural-pool", [-1755, 945, 3.5], 310, 32, 110),
        ("rive", [-2430, -1150, 8], 35, 32, 110),
        ("prairie", [-1850, -640, 24], 20, 30, 45),
    ]
    doc = {
        "format": jadg_map.FORMAT,
        "version": jadg_map.VERSION,
        "name": "Arenarea — Landscape du quartier",
        "comment": "Q07 atlas 15 octobre. Relief, matieres et foliage par phases. Quartier non meuble; inspection jouable locale uniquement.",
        "width": 120,
        "height": 120,
        "origin": [cx - 90, cy - 90],
        "storeys": [{"name": "sol", "z": 0}],
        "groundHeightfield": {
            "width": 101,
            "height": 101,
            "origin": [ox + ix * step, oy + iy * step],
            "spacing": [step, step],
            "heights": field.ravel().tolist(),
        },
        "nextEntityId": 1,
        "tiles": [{"x": 60, "y": 60, "type": "entry"}],
        "entities": [],
        "party": {"appearances": ["heros-brawler"], "walkSpeed": 3, "heading": 0},
        "lighting": {
            "sunScale": 1.65,
            "ambientScale": 0.38,
            "skyLuminance": 1.8,
            "exposureBias": 0,
            "fog": {"density": 0.0015, "falloff": 0.08, "volumetric": False},
            "post": {"bloom_intensity": 0.15, "vignette_intensity": 0.1},
        },
        "daylight": jadg_map.DAYLIGHT,
        "navigation": {"area": [cx - 90, cy - 90, cx + 90, cy + 90], "floor": 15, "height": 20},
        "shots": [
            {"id": n, "target": t, "heading": hd, "pitch": p, "distance": dst}
            for n, t, hd, p, dst in shots
        ],
        "hours": ["12:00", "22:00"],
    }
    path = jadg_map.TRIAL_LEVELS / "capital-landscape/arenarea.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(jadg_map.dumps(doc), encoding="utf8")
    print("ARENAREA_PREPARED", report["components"], "components", report["altitudes"])


if __name__ == "__main__":
    main()
