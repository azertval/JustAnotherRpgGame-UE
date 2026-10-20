#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le relief et les couches du paysage de la capitale, calculés depuis son relevé (D-52).

Hors du moteur (numpy, Pillow) : `capital_landscape_layout.py` donne les rives, l'enceinte, les
quartiers, les bois, les buttes et les voies ; ce module en tire, à chaque sommet du terrain,

  - une **hauteur** en mètres (le seuil de l'Arena of Fate à zéro, l'eau à `SEA_LEVEL`) ;
  - le **poids** de chacune des cinq couches de matière, de 0 à 255, leur somme à 255.

Rien n'est peint ni sculpté à la main : deux calculs du même relevé donnent les mêmes octets
(`SEED`). `build_capital_landscape_scene.py --prepare` écrit ces images sous
`Saved/Jadg/capital-landscape/`, avec un aperçu qu'on relit avant de lancer le moteur.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

import capital_landscape_layout as layout

QUADS_PER_COMPONENT = 63


@dataclass
class Landscape:
    """Le terrain calculé : `heights` en mètres, `weights` par identifiant de couche, lignes y puis x."""
    quads: tuple[int, int]
    area: list[float]
    heights: np.ndarray
    weights: dict[str, np.ndarray]
    water: np.ndarray

    def height_at(self, x: float, y: float) -> float:
        """Bilinear metres; reject points outside the heightfield (no wrapped indices)."""
        u = (x - self.area[0]) / layout.RESOLUTION
        v = (y - self.area[1]) / layout.RESOLUTION
        if not 0 <= u <= self.quads[0] or not 0 <= v <= self.quads[1]:
            raise ValueError(f'Point outside capital heightfield: {(x, y)}')
        i, j = min(int(u), self.quads[0]-1), min(int(v), self.quads[1]-1)
        a, b = u-i, v-j
        return float((self.heights[j,i]*(1-a)+self.heights[j,i+1]*a)*(1-b)
                     +(self.heights[j+1,i]*(1-a)+self.heights[j+1,i+1]*a)*b)

    def masks(self) -> dict[str, np.ndarray]:
        """Les poids tels qu'une matière à couches empilées les lit : chaque couche couvre celles
        d'en dessous de son masque, de 0 à 255 ; le fond (la première couche) n'en a pas."""
        order = [item["id"] for item in layout.LAYERS]
        share = {name: self.weights[name].astype(np.float64) / 255.0 for name in order}
        below = sum(share.values())
        masks: dict[str, np.ndarray] = {}
        for name in reversed(order[1:]):
            masks[name] = np.rint(255.0 * np.divide(share[name], below, out=np.zeros_like(below),
                                                    where=below > 1e-6)).astype(np.uint8)
            below = below - share[name]
        return {name: masks[name] for name in order[1:]}

    def height_units(self) -> np.ndarray:
        """Les hauteurs du moteur : 32 768 au niveau de l'acteur, 1/128 m par pas (échelle Z de 100)."""
        if self.heights.min() < -256 or self.heights.max() > 255.9921875:
            raise ValueError('Heightfield exceeds the current Landscape Z range; do not silently clip it')
        return np.clip(np.rint(32768.0 + self.heights * 128.0), 0, 65535).astype("<u2")


def smooth(value: np.ndarray) -> np.ndarray:
    value = np.clip(value, 0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)


def blur(field: np.ndarray, sigma: float) -> np.ndarray:
    """Un flou gaussien approché par trois moyennes glissantes, bords prolongés."""
    if sigma <= 0:
        return field
    radius = max(1, int(round(math.sqrt(sigma * sigma * 12.0 / 3.0 + 1.0) / 2.0)))
    out = field.astype(np.float64)
    for axis in (0, 1):
        for _ in range(3):
            padded = np.concatenate([np.repeat(out.take([0], axis), radius + 1, axis), out,
                                     np.repeat(out.take([-1], axis), radius, axis)], axis)
            total = np.cumsum(padded, axis)
            width = 2 * radius + 1
            out = (total.take(range(width, total.shape[axis]), axis)
                   - total.take(range(0, total.shape[axis] - width), axis)) / width
    return out


def noise(shape: tuple[int, int], cell: float, rng: np.random.Generator) -> np.ndarray:
    """Un bruit de valeurs lissé, de -1 à 1, d'une maille de `cell` sommets."""
    rows, columns = shape
    lattice = rng.uniform(-1.0, 1.0, (int(rows / cell) + 3, int(columns / cell) + 3))
    y = np.arange(rows) / cell
    x = np.arange(columns) / cell
    y0, x0 = y.astype(int), x.astype(int)
    fy, fx = smooth(y - y0)[:, None], smooth(x - x0)[None, :]
    a = lattice[y0][:, x0]
    b = lattice[y0][:, x0 + 1]
    c = lattice[y0 + 1][:, x0]
    d = lattice[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


class Grid:
    """La grille des sommets, et le tracé du relevé dessus."""

    def __init__(self) -> None:
        self.area = layout.area_metres()
        x0, y0, x1, y1 = self.area
        self.quads = (round((x1 - x0) / layout.RESOLUTION), round((y1 - y0) / layout.RESOLUTION))
        if any(q % QUADS_PER_COMPONENT for q in self.quads):
            raise ValueError(f"terrain de {self.quads} quads : des multiples de {QUADS_PER_COMPONENT} attendus")
        self.shape = (self.quads[1] + 1, self.quads[0] + 1)
        # Un sommet par unité du plan : 1 / (mètres par quad / mètres par unité).
        self.per_unit = layout.METRES_PER_UNIT / layout.RESOLUTION
        u = layout.AREA_UNITS[0] + np.arange(self.shape[1]) / self.per_unit
        v = layout.AREA_UNITS[1] + np.arange(self.shape[0]) / self.per_unit
        self.u, self.v = np.meshgrid(u, v)

    def pixel(self, point: tuple[float, float]) -> tuple[float, float]:
        return ((point[0] - layout.AREA_UNITS[0]) * self.per_unit, (point[1] - layout.AREA_UNITS[1]) * self.per_unit)

    def polygons(self, polygons: list[list[tuple[float, float]]]) -> np.ndarray:
        image = Image.new("L", (self.shape[1], self.shape[0]), 0)
        draw = ImageDraw.Draw(image)
        for polygon in polygons:
            draw.polygon([self.pixel(p) for p in polygon], fill=255)
        return np.asarray(image, dtype=np.float64) / 255.0

    def lines(self, roads: list[dict]) -> np.ndarray:
        image = Image.new("L", (self.shape[1], self.shape[0]), 0)
        draw = ImageDraw.Draw(image)
        for road in roads:
            width = max(2, round(road["width"] / layout.RESOLUTION))
            draw.line([self.pixel(p) for p in road["points"]], fill=255, width=width, joint="curve")
        return np.asarray(image, dtype=np.float64) / 255.0

    def ellipse(self, centre: tuple[float, float], radii: tuple[float, float]) -> np.ndarray:
        """La distance à une ellipse, en unités du plan : négative dedans."""
        du, dv = (self.u - centre[0]) / radii[0], (self.v - centre[1]) / radii[1]
        return (np.sqrt(du * du + dv * dv) - 1.0) * min(radii)

    def vertex(self, point: tuple[float, float]) -> tuple[int, int]:
        x, y = self.pixel(point)
        return (min(self.shape[0] - 1, max(0, round(y))), min(self.shape[1] - 1, max(0, round(x))))


def generate() -> Landscape:
    grid = Grid()
    rng = np.random.default_rng(layout.SEED)
    shape = grid.shape
    units = grid.per_unit                      # sommets par unité du plan

    # --- L'eau et la terre ---------------------------------------------------------------------
    water = np.clip(grid.polygons([layout.WATER]) - grid.polygons(layout.ISLANDS) + grid.polygons(layout.POOLS), 0, 1)
    # Une rive organique : le contour relevé est déplacé par un bruit avant d'être seuillé.
    ragged = blur(water, 2.5) + 0.16 * noise(shape, 22, rng) + 0.08 * noise(shape, 7, rng)
    water = (ragged > 0.5).astype(np.float64)
    dry_access=grid.lines([{'width':18,'points':[(725,412),(810,427),(850,400),(836,449),(866,484)]}])
    water*=1-dry_access
    land = 1.0 - water
    shore = blur(land, 7.0)                    # 0,5 sur la rive ; 14 m de plage de part et d'autre
    inland = np.clip((blur(land, 120.0) - 0.5) * 2.0, 0.0, 1.0)
    open_water = np.clip(1.0 - blur(land, 45.0) * 1.6, 0.0, 1.0)

    # --- Ce qui est bâti, boisé, cultivé -------------------------------------------------------
    walled = grid.polygons([layout.CITY_WALL])
    palace = grid.polygons([layout.PALACE_WALL])
    greens = grid.polygons(layout.GREENS)
    suburbs = grid.polygons([layout.OLDTOWN, layout.SLOGHOOD, layout.BOOMBURBS, layout.HALFLING_BARROWS])
    village = grid.polygons([layout.NECKOFFOODS_VILLAGE])
    docks = grid.polygons([layout.DOCKS])
    built = np.clip(np.maximum.reduce([walled - palace - greens, suburbs * 0.85, village * 0.55, docks]), 0, 1) * land
    settled = blur(np.clip(walled + suburbs + village + docks, 0, 1), 10.0)
    fields = grid.polygons(layout.FIELDS) * land
    forest_bias = blur(grid.polygons(layout.FORESTS), 9.0)
    garden_bias = blur(grid.polygons(layout.GARDENS), 5.0)
    roads = grid.lines(layout.ROADS) * land

    # --- Le relief -----------------------------------------------------------------------------
    height = 1.2 + layout.INLAND_RISE * inland ** 1.2
    ridge = layout.RIDGE
    # Des crêtes et des cols : un bruit à arêtes module la chaîne.
    crests = 1.0 - np.abs(noise(shape, 110, rng) + 0.5 * noise(shape, 45, rng)) / 1.5
    height += (ridge["height"] * smooth((ridge["line"] - grid.v) / ridge["depth"])
               * (1.0 - layout.RIDGE_CRESTS + layout.RIDGE_CRESTS * 1.6 * crests))
    # Des collines, pas des cônes : le plan est froissé avant d'y mesurer la distance à chaque sommet.
    warp = layout.HILL_WARP
    wu = grid.u + warp["units"] * (noise(shape, warp["cell"], rng) + 0.4 * noise(shape, warp["cell"] / 3, rng))
    wv = grid.v + warp["units"] * (noise(shape, warp["cell"], rng) + 0.4 * noise(shape, warp["cell"] / 3, rng))
    envelope = np.zeros(shape)
    for hill in layout.HILLS:
        ax, ay = hill.get('axes', (1.0, 1.0))
        distance = np.hypot((wu - hill["centre"][0])/ax, (wv - hill["centre"][1])/ay) - hill["radius"]
        rise = hill["height"] * smooth(1.0 - distance / hill["falloff"])
        if "terraces" in hill:
            # Des paliers maçonnés : la pente garde un tiers de sa rampe, le reste se met en marches.
            step = hill["terraces"]
            rise = 0.3 * rise + 0.7 * step * (np.floor(rise / step) + smooth((rise / step % 1.0 - 0.75) / 0.25))
        # Neighbouring hills form one envelope; their heights must not accumulate.
        envelope = np.maximum(envelope, rise)
    height += envelope
    # Les mamelons et les creux semés : chaque quartier a ses accidents.
    knolls = layout.DISTRICT_RELIEF["knolls"]
    for _ in range(knolls["count"]):
        cu = rng.uniform(layout.AREA_UNITS[0], layout.AREA_UNITS[2])
        cv = rng.uniform(layout.RIDGE["line"], layout.AREA_UNITS[3])
        radius = rng.uniform(*knolls["radius"])
        rise = rng.uniform(*knolls["height"]) * (-0.6 if rng.random() < 0.25 else 1.0)
        stretch = rng.uniform(0.6, 1.6)
        distance = np.hypot((wu - cu) * stretch, (wv - cv) / stretch) - radius
        height += rise * smooth(1.0 - distance / (radius * knolls["falloff"]))
    for valley in layout.VALLEYS:
        trace = grid.lines([{"width": layout.RESOLUTION * 2, "points": valley["points"]}])
        spread = blur(trace, valley["width"] * units / 2.0)
        height -= valley["depth"] * smooth(spread / spread.max())
    # Un vallon ne descend pas sous le niveau des quais : la ville ne s'inonde pas.
    height = np.maximum(height, layout.QUAY_LEVEL)
    # Le grain du terrain : discret sous la ville, franc dans les collines et les bois.
    wild = 1.0 - smooth(settled * 1.4)
    rough = 0.7 + wild * (2.4 + 0.07 * np.maximum(height, 0.0))
    height += rough * (noise(shape, 64, rng) + 0.45 * noise(shape, 24, rng) + 0.18 * noise(shape, 9, rng))
    # Les cultures et les quartiers gardent leurs collines, pas le grain fin.
    calm = blur(height, 6.0)
    flatten = np.clip(smooth(settled * 1.3) * 0.6 + blur(fields, 6.0) * 0.6, 0.0, 0.9)
    height = height * (1.0 - flatten) + calm * flatten
    # La houle du sol sous le bâti : elle survit à l'aplanissement des îlots.
    for amplitude, cell in layout.DISTRICT_RELIEF["swell"]:
        height += amplitude * noise(shape, cell, rng) * (0.35 + 0.65 * smooth(settled * 1.3))
    # Les terrasses de la ville close : une part de la pente en paliers, le reste en rampe ; la part
    # change d'un îlot à l'autre, et les paliers ne sont pas tous au même niveau.
    step = layout.CITY_TERRACES["step"]
    low, high = layout.DISTRICT_RELIEF["terraceShare"]
    share = low + (high - low) * (0.5 + 0.5 * noise(shape, 55, rng))
    shifted = height + step * 0.5 * noise(shape, 90, rng)
    stepped = height - shifted + step * (np.floor(shifted / step) + smooth((shifted / step % 1.0 - 0.7) / 0.3))
    urban = blur(np.clip(walled - greens, 0, 1), 4.0) * share
    height = height * (1.0 - urban) + stepped * urban
    # Aucun creux ne descend sous le niveau des quais.
    height = np.maximum(height, layout.QUAY_LEVEL)
    pads: dict[str, float] = {}
    for pad in layout.PADS:
        level = pad["z"] if pad["z"] is not None else float(height[grid.vertex(pad["centre"])])
        pads[pad["id"]] = level
        weight = smooth(1.0 - grid.ellipse(pad["centre"], pad["radii"]) / pad["blend"])
        height = height * (1.0 - weight) + level * weight
    # La rive : la terre descend à l'eau sur sa plage, le fond se creuse vers le large.
    sea = layout.SEA_LEVEL
    beach = smooth((shore - 0.5) / 0.42)
    depth = 1.6 + 11.0 * open_water
    bed = sea - depth * smooth((0.5 - shore) / 0.45)
    height = np.where(shore >= 0.5, sea + (height - sea) * beach, bed)
    for pad in layout.PADS:
        # Un terre-plein au bord de l'eau reste plan jusqu'à son quai.
        weight = smooth(1.0 - grid.ellipse(pad["centre"], pad["radii"]) / 6.0) * (shore > 0.62)
        height = height * (1.0 - weight) + pads[pad["id"]] * weight

    # Urban construction is composed AFTER hydrology. Roads never fill a river.
    import capital_urban_terrain
    height = capital_urban_terrain.shape_city(grid, height, water)

    terraces=layout.city.GARDEN_TERRACES
    # Shape the complete garden after the palace pad, including its stairs.
    knots=[];levels=[];centres=[];widths=[]
    for t in terraces:
        knots.extend([t['centre'][1]-t['halfSize'][1],t['centre'][1]+t['halfSize'][1]])
        levels.extend([t['z']-.35,t['z']-.35])
        centres.extend([t['centre'][0]]*2);widths.extend([t['halfSize'][0]]*2)
    profile=np.interp(grid.v,knots,levels)
    distance=np.maximum(np.abs(grid.u-np.interp(grid.v,knots,centres))-np.interp(grid.v,knots,widths),np.maximum(knots[0]-grid.v,grid.v-knots[-1]))*layout.METRES_PER_UNIT
    weight=smooth(1-distance/9)
    height=height*(1-weight)+profile*weight
    stair=np.clip((grid.u-628)/17,0,1)
    distance=np.maximum(np.maximum(628-grid.u,grid.u-645),np.abs(grid.v-686)-3.2)*layout.METRES_PER_UNIT
    weight=smooth(1-distance/3)
    height=height*(1-weight)+(54+8*stair-.35)*weight

    # Only offshore edges descend. A forced sea-level rim on every side invented
    # a moat behind Cyan Fortress and severed the inland hills.
    rows, columns = shape
    j, i = np.mgrid[0:rows, 0:columns]
    border = np.minimum.reduce([i, j, columns - 1 - i, rows - 1 - j]) * layout.RESOLUTION
    edge = smooth(border / layout.EDGE["margin"])
    height = np.where(water > .5, layout.EDGE["floor"] + (height-layout.EDGE["floor"]) * edge, height)

    # --- Les couches ---------------------------------------------------------------------------
    gy, gx = np.gradient(height, layout.RESOLUTION)
    slope = np.hypot(gx, gy)
    grain = noise(shape, 16, rng)
    fine = noise(shape, 5, rng)
    weights = {item["id"]: np.zeros(shape) for item in layout.LAYERS}
    weights["herbe"][:] = 1.0

    def paint(layer: str, alpha: np.ndarray) -> None:
        alpha = np.clip(alpha, 0.0, 1.0)
        for name in weights:
            weights[name] *= 1.0 - alpha
        weights[layer] += alpha

    # Les bois : le couvert du relevé, déchiré par le bruit ; les jardins du palais, plus clairs.
    canopy = forest_bias * 1.25 + 0.55 * garden_bias + 0.35 * grain + 0.15 * fine
    paint("sous-bois", smooth((canopy - 0.62) / 0.3) * land)
    # Les hauts secs de la chaîne : la terre affleure sous l'herbe.
    dry = smooth((height - 45.0) / 40.0) * (0.25 + 0.25 * grain)
    paint("terre", dry * land)
    # Le bâti : la terre battue des îlots, que l'herbe reprend dans les faubourgs.
    paint("terre", blur(built, 1.5) * (0.82 + 0.18 * grain))
    # Les cours et les jardins d'îlot : l'herbe revient par taches dans les murs.
    courts = smooth((noise(shape, 11, rng) + 0.3 * fine - 0.38) / 0.2)
    paint("herbe", blur(built, 1.5) * courts * 0.85)
    # Les cultures : des parcelles tournées, en rangs, en labour ou en pré.
    parcel = 46.0
    angle = 0.42
    pu = grid.u * math.cos(angle) + grid.v * math.sin(angle)
    pv = -grid.u * math.sin(angle) + grid.v * math.cos(angle)
    cell = np.floor(pu / parcel) * 7919.0 + np.floor(pv / (parcel * 0.7)) * 104729.0
    kind = (np.sin(cell) * 43758.5453) % 1.0
    rows = (np.sin(pv * units * 2.0 * math.pi / 5.0) > 0.0).astype(np.float64)
    hedge = np.minimum((pu / parcel) % 1.0, (pv / (parcel * 0.7)) % 1.0) < 0.05
    crop = np.where(kind < 0.45, rows * 0.9, np.where(kind < 0.72, 0.85, 0.08))
    paint("terre", fields * np.where(hedge, 0.0, crop))
    paint("sous-bois", fields * hedge * 0.45)
    # La roche : là où la pente dépasse ce que tient la terre.
    paint("roche", smooth((slope - 0.5) / 0.35) * (shore > 0.45))
    # Les voies : du sable graveleux.
    paint("sable", blur(roads, 0.8) * 0.95)
    # La grève et le fond : le sable sur la rive, la terre sombre au large.
    strand = smooth(1.0 - np.abs(shore - 0.5) / 0.16)
    paint("sable", strand * (0.75 + 0.25 * grain))
    paint("sable", water * smooth(1.0 - open_water * 1.4))
    paint("terre", water * smooth(open_water * 1.4) * 0.8)

    stack = np.stack([weights[item["id"]] for item in layout.LAYERS])
    stack = np.rint(stack / stack.sum(axis=0, keepdims=True) * 255.0).astype(np.int32)
    # La somme à 255 exactement : l'arrondi va à la couche dominante.
    top = stack.argmax(axis=0)
    rest = 255 - stack.sum(axis=0)
    np.put_along_axis(stack, top[None], np.take_along_axis(stack, top[None], 0) + rest[None], 0)
    final = {item["id"]: stack[index].astype(np.uint8) for index, item in enumerate(layout.LAYERS)}
    return Landscape(grid.quads, grid.area, np.round(height, 4), final, water > 0.5)


def preview(terrain: Landscape) -> Image.Image:
    """L'aperçu qu'on relit avant le moteur : les couches à leur couleur, l'ombre du relief, l'eau."""
    rgb = np.zeros(terrain.heights.shape + (3,))
    for item in layout.LAYERS:
        colour = np.array([int(item["colour"][k:k + 2], 16) for k in (1, 3, 5)], dtype=np.float64)
        rgb += terrain.weights[item["id"]][..., None] / 255.0 * colour
    gy, gx = np.gradient(terrain.heights, layout.RESOLUTION)
    shade = np.clip(0.82 + 0.9 * (-gx - gy) / np.sqrt(2.0), 0.35, 1.3)
    rgb *= shade[..., None]
    depth = np.clip((layout.SEA_LEVEL - terrain.heights) / 12.0, 0.0, 1.0)
    sea = np.array([70.0, 190.0, 185.0]) * (1 - depth[..., None]) + np.array([20.0, 80.0, 120.0]) * depth[..., None]
    wet = (terrain.heights < layout.SEA_LEVEL)[..., None]
    rgb = np.where(wet, 0.25 * rgb + 0.75 * sea, rgb)
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
