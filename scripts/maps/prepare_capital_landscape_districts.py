#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Atlas-scale capital: one deterministic field, disjoint tiles, district phases.

Produces Saved/Jadg/capital-landscape-districts and text review fixtures.
No building or bridge geometry is produced. All coordinates are world metres.
"""

from pathlib import Path
import argparse
import hashlib
import json
import math
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved/Jadg/capital-landscape-districts"
SOURCE = ROOT / "Source/Elements/Terrain/capital"
sys.path.insert(0, str(ROOT / "scripts/maps"))
from prepare_arenarea_landscape import smooth, uv, segment, box_distance  # noqa: E402
import jadg_map  # noqa: E402

LAYERS = ("Pelouse", "Prairie", "HerbeSauvage", "Terre", "Sable", "Roche", "Pavage")
PALETTE = np.array([[61, 105, 53], [103, 128, 66], [78, 109, 52], [130, 109, 79],
                    [190, 177, 139], [115, 115, 105], [174, 163, 141]], dtype=float)


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf8")


def polygon(x, y, points):
    """Analytic membership and distance: identical on both sides of every tile."""
    inside = np.zeros(x.shape, dtype=bool)
    distance = np.full(x.shape, np.inf)
    for a, b in zip(points, points[1:] + points[:1]):
        distance = np.minimum(distance, segment(x, y, a, b)[0])
        if a[1] != b[1]:
            inside ^= ((a[1] > y) != (b[1] > y)) & (
                x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            )
    return inside | (distance < 1e-6), distance


def sample(field, x, y, origin, spacing):
    fx, fy = (x - origin[0]) / spacing, (y - origin[1]) / spacing
    ix = np.clip(np.floor(fx).astype(int), 0, field.shape[1] - 2)
    iy = np.clip(np.floor(fy).astype(int), 0, field.shape[0] - 2)
    fx, fy = np.clip(fx - ix, 0, 1), np.clip(fy - iy, 0, 1)
    return ((field[iy, ix] * (1 - fx) + field[iy, ix + 1] * fx) * (1 - fy)
            + (field[iy + 1, ix] * (1 - fx) + field[iy + 1, ix + 1] * fx) * fy)


class Capital:
    def __init__(self):
        self.config = json.loads((SOURCE / "production.json").read_text(encoding="utf8"))
        self.atlas = json.loads((SOURCE / "atlas.json").read_text(encoding="utf8"))
        if hashlib.sha256((SOURCE / "atlas.json").read_bytes()).hexdigest() != self.config["atlasSha256"]:
            raise RuntimeError("Atlas changed without updating the production contract")
        self.districts = self.atlas["districts"]
        self.polygons = {q["id"]: [[p[0], -p[1]] for p in q["polygon_m"]] for q in self.districts}
        self.sites = [s for s in self.atlas["sites"] if s["xy_m"] and s["ground_z_m"] is not None
                      and s["geometry_type"] == "volume_or_site_type" and s["id"] != "X13"]
        # The botanical garden contains the palace; larger reservations are graded first.
        self.sites.sort(key=lambda s: -math.prod(s["parcel_m"]))
        self.routes = [{**r, "points": [uv(p) for p in r["nodes"]]} for r in self.atlas["roads"]]
        arena = ROOT / "Saved/Jadg/arenarea-landscape"
        self.arena_def = json.loads((ROOT / "Source/Elements/Terrain/arenarea/definition.json").read_text())
        with np.load(arena / "placement.npz") as archive:
            self.arena = {k: archive[k] for k in archive.files}
        self.arena_weights = np.fromfile(arena / "weights.r8", dtype=np.uint8).reshape(
            7, self.arena["height"].shape[0], self.arena["height"].shape[1])
        self.arena_routes = json.loads((arena / "relief.json").read_text())["routes"]
        self.routes = [r for r in self.routes if r["id"] != "R01"] + self.arena_routes
        self.inventory = json.loads((arena / "fab-inventory.json").read_text())

    def field(self, x, y):
        shape = x.shape
        # Smooth regional landforms from named height controls, before local engineering.
        numerator, denominator = np.zeros(shape), np.zeros(shape)
        for c in self.atlas["terrain_controls"]:
            if c["name"] == "Baie":
                continue
            cx, cy = c["xy_m"][0], -c["xy_m"][1]
            w = 1 / (250**2 + (x - cx)**2 + (y - cy)**2)**2
            numerator += w * c["z_m"]
            denominator += w
        h = numerator / denominator + 1.1 * np.sin(x / 310) * np.sin(y / 420)
        owner = np.full(shape, 14, dtype=np.uint8)
        garden = np.zeros(shape)
        for q in self.districts:
            inside, edge = polygon(x, y, self.polygons[q["id"]])
            owner[inside] = int(q["id"][1:])
            alpha = np.where(inside, 1, 1 - smooth(0, 160, edge))
            target = np.clip(h, q["z_min"], q["z_max"])
            cfg = self.config["districts"][q["id"]]
            step = cfg["terrace_step_m"]
            # Rounded earthen terraces; slope continuity is retained by a restrained amplitude.
            if step:
                target -= step * 0.10 * np.sin(2 * np.pi * target / step)
            h = h * (1 - alpha) + target * alpha
            patch = 0.5 + 0.25 * np.sin(x / 120) + 0.25 * np.cos(y / 145)
            garden = np.maximum(garden, inside * smooth(1 - cfg["garden_fraction"], 1, patch))
        water_z = np.zeros(shape)
        # The atlas frame cuts the open bay at u=0; extend that cut outside this level.
        bay_points = [[-150, p[1]] if p[0] == 0 else p for p in self.atlas["water"]["bay_outline_uv"]]
        bay, distance = polygon(x, y, [uv(p) for p in bay_points])
        h = np.where(bay, -2 - np.minimum(distance * 0.025, 14), h * smooth(0, 180, distance))
        wet, bank = bay.copy(), distance.copy()

        def channel(points, widths, levels, depth, blend):
            nonlocal h, water_z, wet, bank
            pts = [uv(p) for p in points]
            near = np.full(shape, np.inf)
            radius, z = np.zeros(shape), np.zeros(shape)
            for i, (a, b) in enumerate(zip(pts, pts[1:])):
                d, t = segment(x, y, a, b)
                take = d < near
                radius = np.where(take, (widths[i] * (1-t) + widths[i+1] * t) / 2, radius)
                z = np.where(take, levels[i] * (1-t) + levels[i+1] * t, z)
                near = np.minimum(near, d)
            edge = near - radius
            bed = z - depth + (depth - 0.25) * smooth(-radius * 0.7, 0, edge)
            target = np.where(edge < 0, bed, z + .25 + (h-z-.25)*smooth(0, blend, edge))
            h = np.minimum(h, target)
            take = edge < 0
            water_z = np.where(take, np.maximum(z, water_z), water_z)
            wet |= take
            bank = np.minimum(bank, abs(edge))

        water = self.atlas["water"]
        # Both rivers enter from the world beyond the level instead of ending in round pools.
        channel([[2000, 755]] + water["river_center_uv"], [180]+water["river_width_m"],
                [3.0]+water["river_water_z_m"], 6, 220)
        channel([[190, 1650]] + water["creek_center_uv"], [water["creek_width_m"]]*(len(water["creek_center_uv"])+1),
                [9.5]+water["creek_water_z_m"], 2.5, 190)
        channel(water["pool_connection_uv"] + [[780, 330]], [24]*5,
                water["pool_connection_water_z_m"] + [0], 3, 85)
        reserved, paving = np.zeros(shape), np.zeros(shape)
        # Gardens and agriculture are land uses, not giant fictitious building slabs.
        garden_site = next(s for s in self.sites if s["id"] == "L12-02")
        cx, cy = garden_site["xy_m"][0], -garden_site["xy_m"][1]
        sx, sy = garden_site["parcel_m"]
        gd = box_distance(x, y, [cx-sx/2, cy-sy/2, cx+sx/2, cy+sy/2])
        garden = np.maximum(garden, 1-smooth(0, 20, gd))
        roads = np.full(shape, np.inf)
        for route in self.routes:
            near, z = np.full(shape, np.inf), h.copy()
            for a, b in zip(route["points"], route["points"][1:]):
                dist, t = segment(x, y, a, b)
                z = np.where(dist < near, a[2]*(1-t)+b[2]*t, z)
                near = np.minimum(near, dist)
            edge = near - route["width"]/2
            # A route crosses water only as a future bridge; no land fill in its channel.
            alpha = (1-smooth(0, 120, edge)) * (~wet)
            h = h*(1-alpha) + z*alpha
            roads = np.minimum(roads, edge)
            paving = np.maximum(paving, (1-smooth(0, 3, edge))*(~wet))
        for site in self.sites:
            if site["id"] in ("L12-02", "L09-03") or site["district"] == "Q07":
                continue
            cx, cy = site["xy_m"][0], -site["xy_m"][1]
            sx, sy = site["parcel_m"]
            dist = box_distance(x, y, [cx-sx/2, cy-sy/2, cx+sx/2, cy+sy/2])
            # Broad cut/fill feathering protects the local ground around plateau reservations.
            alpha = (1-smooth(0, 220, dist)) * (~wet)
            h = h*(1-alpha) + site["ground_z_m"]*alpha
            reserved = np.maximum(reserved, dist == 0)
            paving = np.maximum(paving, (1-smooth(0, 3, dist))*(~wet))
        # Blend the completed Arenarea design into the shared field, preserving its core.
        inside, edge = polygon(x, y, self.polygons["Q07"])
        mix = np.where(inside, 1, 1-smooth(0, 160, edge))
        ao, astep = self.arena_def["origin_m"], self.arena_def["spacing_m"]
        ax, ay = self.arena_def["quads"]
        margin = np.minimum.reduce([x-ao[0], y-ao[1], ao[0]+ax*astep-x, ao[1]+ay*astep-y])
        mix *= smooth(0, 80, margin)
        h = h*(1-mix) + sample(self.arena["height"], x, y, ao, astep)*mix
        for key, value in (("gardens", garden), ("reserved", reserved)):
            value[:] = value*(1-mix) + sample(self.arena[key], x, y, ao, astep)*mix
        arwet = sample(self.arena["water"].astype(float), x, y, ao, astep) > .5
        wet = np.where(mix > .5, arwet, wet)
        water_z = np.where(mix > .5, sample(self.arena["water_z"], x, y, ao, astep), water_z)
        roads = np.minimum(roads, np.where(mix > .5, sample(self.arena["road_distance"], x, y, ao, astep), np.inf))
        bank = np.minimum(bank, np.where(mix > .5, sample(self.arena["bank_distance"], x, y, ao, astep), np.inf))
        # The stored height is the collision height; avoid hidden sub-centimetre discrepancies.
        encoded = np.rint(32768 + h*128)
        if encoded.min() < 0 or encoded.max() > 65535:
            raise RuntimeError("Height encoding overflow")
        h = (encoded-32768)/128
        return dict(height=h, owner=owner, gardens=garden, reserved=reserved, paving=paving,
                    road_distance=roads, water=wet, water_z=water_z, bank_distance=bank, arena_mix=mix)

    def tile(self, tx, ty):
        spacing = self.config["spacing_m"]
        size = self.config["tile_size_m"]
        q = size // spacing
        ox = self.config["origin_m"][0] + tx*size
        oy = self.config["origin_m"][1] + ty*size
        # One sample halo makes slope-dependent paint exactly equal at shared tile vertices.
        y, x = np.mgrid[-1:q+2, -1:q+2]
        x, y = x*spacing+ox, y*spacing+oy
        f = self.field(x, y)
        gy, gx = np.gradient(f["height"], spacing)
        f["slope"] = np.hypot(gx, gy)
        sand = (1-smooth(4, 28, f["bank_distance"]))*(1-f["paving"])
        rock = smooth(.18, .48, f["slope"])*(1-f["paving"])
        prairie = .5+.5*np.sin(x/110)*np.sin(y/97)
        agriculture = f["owner"] == 9
        # Long agricultural strips: 180 x 360 m fields separated by earthen headlands.
        headland = (np.mod(x+6000, 180) < 8) | (np.mod(y+6500, 360) < 10)
        prairie = np.where(agriculture, np.where(headland, .15, .95), prairie)
        g = f["gardens"]
        vals = np.stack([g, (1-g)*prairie*.7, (1-g)*(1-prairie*.7),
                         np.full(x.shape, .12), sand, rock, f["paving"]*10])
        vals[:4] *= (1-sand)*(1-rock)*(1-f["paving"])
        vals[4] = np.maximum(vals[4], f["water"])
        vals /= np.maximum(vals.sum(axis=0), .0001)
        for i in range(7):
            ar = sample(self.arena_weights[i], x, y, self.arena_def["origin_m"], 2)/255
            vals[i] = vals[i]*(1-f["arena_mix"]) + ar*f["arena_mix"]
        vals /= vals.sum(axis=0)
        weights = np.floor(vals*255).astype(np.uint8)
        remainder = (255-weights.sum(axis=0)).astype(np.uint8)
        winner = vals.argmax(axis=0)
        for i in range(7):
            weights[i] += remainder*(winner == i)
        assert np.all(weights.sum(axis=0) == 255)
        f = {k: v[1:-1, 1:-1] for k, v in f.items()}
        weights = weights[:, 1:-1, 1:-1]
        identifier = f"t{tx:02d}_{ty:02d}"
        folder = OUT / "tiles" / identifier
        folder.mkdir(parents=True, exist_ok=True)
        encoded = np.rint(32768+f["height"]*128).astype("<u2")
        (folder / "heights.r16").write_bytes(encoded.tobytes())
        (folder / "weights.r8").write_bytes(weights.tobytes())
        np.savez_compressed(folder / "fields.npz", **f)
        # Visual preview is derived from the actual weights and water mask.
        preview = np.einsum("ihw,ic->hwc", weights/255, PALETTE)
        preview *= np.clip(.88-gx[1:-1, 1:-1]*.8-gy[1:-1, 1:-1]*.6, .45, 1.2)[..., None]
        preview[f["water"]] = [45, 115, 133]
        Image.fromarray(np.uint8(np.clip(preview, 0, 255))).save(folder / "plan.png")
        counts = np.bincount(f["owner"].ravel(), minlength=15)
        # Prefer a represented urban district; unassigned peripheral tiles are Q14.
        owner = int(np.argmax(counts[1:14])+1) if counts[1:14].max() > q*q*.12 else 14
        report = dict(id=identifier, district=f"Q{owner:02d}", origin_m=[ox, oy], quads=q,
                      spacing_m=spacing, altitude_m=[float(f["height"].min()), float(f["height"].max())],
                      wetFraction=float(f["water"].mean()),
                      heightSha256=hashlib.sha256(encoded.tobytes()).hexdigest())
        dump(folder / "relief.json", report)
        return report

    def foliage(self, tile):
        folder = OUT / "tiles" / tile["id"]
        with np.load(folder / "fields.npz") as data:
            f = {k: data[k] for k in data.files}
        rng = np.random.default_rng(self.config["seed"] + int(tile["id"][1:3])*100 + int(tile["id"][4:]))
        groups = {}
        for row in self.inventory:
            if row["class"] != "StaticMesh" or "/Plants/" not in row["path"] or row["path"].endswith("tdcrdbur_VarF"):
                continue
            name = row["path"].rsplit("/", 1)[1]
            code = next(c for c in ("vlkhcbxia", "vczndjqja", "tbdpec3r", "tdcrdbur") if c in name)
            groups[name] = dict(id=name, code=code, mesh=row["path"],
                                foliageType="/Game/Capitale/Ressources/Arenarea/Foliage/FT_"+name, instances=[])
        trees = {
            "cypres": "/Game/Kit/Regions/central-empire/capital/arenarea/ar-meshy-cypres/StaticMeshes/SM_ar-meshy-cypres",
            "ombrage": "/Game/Kit/Regions/central-empire/capital/arenarea/ar-meshy-arbre-ombrage/StaticMeshes/SM_ar-meshy-arbre-ombrage",
        }
        for name, path in trees.items():
            groups[name] = dict(id=name, mesh=path, tree=True, desiredHeight_m=12 if name == "cypres" else 10, instances=[])
        ox, oy = tile["origin_m"]
        size = self.config["tile_size_m"]
        def seed(spacing, tree=False):
            yy, xx = np.mgrid[oy:oy+size:spacing, ox:ox+size:spacing]
            xx = xx.ravel() + rng.uniform(.1, spacing-.1, xx.size)
            yy = yy.ravel() + rng.uniform(.1, spacing-.1, yy.size)
            ix = np.clip(((xx-ox)/4).astype(int), 0, tile["quads"]-1)
            iy = np.clip(((yy-oy)/4).astype(int), 0, tile["quads"]-1)
            own = f["owner"][iy, ix]
            probs = np.array([self.config["districts"][f"Q{int(v):02d}"]["tree_density" if tree else "grass_density"] for v in own])
            if not tree:
                probs = np.maximum(probs, f["gardens"][iy, ix]*.75)
                probs = np.maximum(probs, (f["bank_distance"][iy, ix] < 25)*.7)
            allowed = (~f["water"][iy, ix]) & (f["height"][iy, ix] > .5)
            # 22 m tree cells do not divide a 1008 m tile: retain each root in its
            # own half-open tile, including the shorter last row and column.
            allowed &= (xx < ox+size) & (yy < oy+size)
            allowed &= (f["reserved"][iy, ix] < .01) & (f["road_distance"][iy, ix] > (12 if tree else 3))
            allowed &= (f["slope"][iy, ix] < (.4 if tree else .28)) & (rng.random(xx.size) < probs)
            # Farm trees mark plot edges; crop rows remain open and harvestable.
            if tree:
                allowed &= (own != 9) | (np.mod(xx+6000, 180) < 16)
            else:
                allowed &= (own != 9) | ((np.mod(xx+6000, 180) > 8) & (np.mod(yy+6500, 360) > 10))
            xs, ys = xx[allowed], yy[allowed]
            zs = sample(f["height"], xs, ys, [ox, oy], 4)
            for x, y, z, i, j in zip(xs, ys, zs, ix[allowed], iy[allowed]):
                if tree:
                    name = "cypres" if f["gardens"][j, i] > .4 or rng.random() < .24 else "ombrage"
                else:
                    code = ("tbdpec3r" if f["bank_distance"][j, i] < 25 else
                            "vlkhcbxia" if f["gardens"][j, i] > .4 else
                            "tdcrdbur" if f["owner"][j, i] == 9 else "vczndjqja")
                    name = rng.choice([k for k, g in groups.items() if g.get("code") == code])
                groups[name]["instances"].append([round(float(x), 3), round(float(y), 3),
                    round(float(z-.01), 4), round(float(rng.uniform(0, 360)), 2), round(float(rng.uniform(.8, 1.2)), 3)])
        seed(4)
        seed(22, tree=True)
        result = [g for g in groups.values() if g["instances"]]
        (folder / "foliage.json").write_text(json.dumps(result, separators=(",", ":")), encoding="utf8")
        self.ground_candidates(tile, result)
        return sum(len(g["instances"]) for g in result)

    @staticmethod
    def ground_candidates(tile, groups):
        """Flag curved quads for exact native collision projection after planting.

        Bilinear placement differs from a triangle on non-planar quads. Bounding
        both diagonals also covers the Landscape/Chaos axis conventions.
        """
        folder = OUT/'tiles'/tile['id']
        side = tile['quads']+1
        h = np.fromfile(folder/'heights.r16', dtype='<u2').reshape(side, side).astype(float)/128-256
        candidates = []
        for group in groups:
            p = np.asarray(group['instances'])
            x, y = (p[:, 0]-tile['origin_m'][0])/4, (p[:, 1]-tile['origin_m'][1])/4
            ix, iy = x.astype(int), y.astype(int)
            fx, fy = x-ix, y-iy
            a, b, c, d = h[iy, ix], h[iy, ix+1], h[iy+1, ix], h[iy+1, ix+1]
            base, twist = a+(b-a)*fx+(c-a)*fy, d-b-c+a
            z1, z2 = base+twist*np.minimum(fx, fy), base+twist*np.maximum(fx+fy-1, 0)
            error = np.maximum(abs(z1-p[:, 2]-.01), abs(z2-p[:, 2]-.01))
            candidates.extend(p[error > .005, :3].tolist())
        dump(folder/'ground-candidates.json', candidates)

    def manifest(self, tiles):
        rows = []
        for key in self.config["order"]:
            cfg = self.config["districts"][key]
            members = [t for t in tiles if t["district"] == key]
            q = next((q for q in self.districts if q["id"] == key), None)
            rows.append(dict(id=key, slug=cfg["slug"], name=q["name"] if q else "Abords et collines",
                             atlasAreaKm2=q["area_km2"] if q else None, tiles=[t["id"] for t in members]))
        result = dict(config=self.config, tiles=tiles, districts=rows, buildings=0)
        dump(OUT / "manifest.json", result)
        self.preview(tiles)
        self.fixtures(rows, tiles)
        self.streaming_route(rows)
        self.audit_seams(tiles)
        self.audit_sites()
        return result

    def streaming_route(self, rows):
        stops = []
        for row in rows:
            fixture = json.loads((jadg_map.TRIAL_LEVELS/("capital-landscape/paysage-"+row["slug"]+".json")).read_text())
            stops.append(dict(name=row['slug'], target=fixture['shots'][0]['target']))
        xx = np.arange(-2400, -1119, 40, dtype=float)
        yy = np.full(xx.shape, -440.)
        f = self.field(xx, yy)
        if np.any(f['water']):
            raise RuntimeError('Streaming travel must stay on dry landscape')
        travel = [[float(x), float(y), float(z+1)] for x, y, z in zip(xx, yy, f['height'])]
        dump(OUT/'world-partition/streaming-route.json', dict(stops=stops, travel=travel,
            travelSpeed_m_s=16, travelSampleSpacing_m=40, steadyMeasureSeconds=3))

    def audit_sites(self):
        rows = []
        for site in self.sites:
            if site["id"] in ("L12-02", "L09-03"):
                continue
            x, y = site["xy_m"][0], -site["xy_m"][1]
            f = self.field(np.array([x]), np.array([y]))
            z = float(f["height"][0])
            rows.append(dict(id=site["id"], name=site["name"], expected=site["ground_z_m"],
                             actual=z, delta=round(z-site["ground_z_m"], 4), wet=bool(f["water"][0])))
        dump(OUT/"site-grades.json", dict(sites=rows))
        if any(abs(r["delta"]) > .04 or r["wet"] for r in rows):
            raise RuntimeError("A reserved site lost its designed ground elevation")

    def preview(self, tiles):
        nx, ny = self.config["tiles_xy"]
        size = 126
        image = Image.new("RGB", (nx*size, ny*size))
        for tile in tiles:
            tx, ty = int(tile["id"][1:3]), int(tile["id"][4:])
            with Image.open(OUT / "tiles" / tile["id"] / "plan.png") as part:
                image.paste(part.resize((size, size)), (tx*size, ty*size))
        draw = ImageDraw.Draw(image)
        ox, oy = self.config["origin_m"]
        factor = size/self.config["tile_size_m"]
        for q in self.districts:
            points = [((p[0]-ox)*factor, (-p[1]-oy)*factor) for p in q["polygon_m"]]
            draw.line(points+[points[0]], fill=(240, 220, 175), width=2)
            x, y = q["center_m"]
            draw.text(((x-ox)*factor, (-y-oy)*factor), q["name"], fill="white")
        draw.text((20, 12), "NORD  ^   |   Terrain 11,088 x 13,104 km   |   Aucun batiment", fill="white")
        image.save(OUT / "plan-capitale.png")

    def fixtures(self, rows, tiles):
        base = json.loads((jadg_map.TRIAL_LEVELS / "capital-landscape/arenarea.json").read_text())
        for row in rows:
            # Two close views per district, in the actual authored land, with player camera bounds.
            points = []
            if row["id"] == "Q07":
                points = [(-2130, -440), (-1755, 945)]
            elif row["id"] == "Q14":
                points = [(-4150, -3150), (-3240, 4800)]
            else:
                q = next(q for q in self.districts if q["id"] == row["id"])
                cx, cy = q["center_m"][0], -q["center_m"][1]
                points = [(cx, cy), (cx+160, cy+100)]
            shots = []
            for i, (x, y) in enumerate(points):
                z = self.field(np.array([x]), np.array([y]))["height"][0]
                shots.append(dict(id=f"{row['slug']}-{i+1}", target=[x, y, float(z+1)], heading=35+i*110, pitch=35, distance=100))
            doc = {**base, "name": "Paysage — "+row["name"], "shots": shots, "entities": [],
                   "comment": "Paysage uniquement; aucun batiment. Sous-niveaux issus de l'atlas metropolitain."}
            # No character is created by the landscape district builder; the frame is for captures.
            path = jadg_map.TRIAL_LEVELS / ("capital-landscape/paysage-"+row["slug"]+".json")
            path.write_text(jadg_map.dumps(doc), encoding="utf8")

    @staticmethod
    def audit_seams(tiles):
        lookup = {t["id"]: t for t in tiles}
        checks = []
        for tile in tiles:
            tx, ty = int(tile["id"][1:3]), int(tile["id"][4:])
            q = tile["quads"]+1
            h = np.fromfile(OUT/"tiles"/tile["id"]/"heights.r16", dtype="<u2").reshape(q, q)
            w = np.fromfile(OUT/"tiles"/tile["id"]/"weights.r8", dtype=np.uint8).reshape(7, q, q)
            for other, axis in ((f"t{tx+1:02d}_{ty:02d}", 1), (f"t{tx:02d}_{ty+1:02d}", 0)):
                if other not in lookup:
                    continue
                hh = np.fromfile(OUT/"tiles"/other/"heights.r16", dtype="<u2").reshape(q, q)
                ww = np.fromfile(OUT/"tiles"/other/"weights.r8", dtype=np.uint8).reshape(7, q, q)
                equal_h = np.array_equal(h[:, -1], hh[:, 0]) if axis else np.array_equal(h[-1], hh[0])
                equal_w = np.array_equal(w[:, :, -1], ww[:, :, 0]) if axis else np.array_equal(w[:, -1], ww[:, 0])
                checks.append(dict(a=tile["id"], b=other, heights=equal_h, weights=equal_w))
        dump(OUT/"seams.json", dict(checks=checks, passed=all(c["heights"] and c["weights"] for c in checks)))
        if not all(c["heights"] and c["weights"] for c in checks):
            raise RuntimeError("Shared border differs: see seams.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    capital = Capital()
    tiles = []
    nx, ny = capital.config["tiles_xy"]
    for ty in range(ny):
        for tx in range(nx):
            path = OUT/"tiles"/f"t{tx:02d}_{ty:02d}"/"relief.json"
            if args.resume and path.exists():
                tile = json.loads(path.read_text())
            else:
                tile = capital.tile(tx, ty)
            tile["plantCount"] = capital.foliage(tile)
            tiles.append(tile)
            print("CAPITAL_PREPARED", tile["id"], tile["district"], tile["plantCount"], flush=True)
    manifest = capital.manifest(tiles)
    print("CAPITAL_FIELD_OK", len(tiles), "tiles", len(manifest["districts"]), "production sectors")


if __name__ == "__main__":
    main()
