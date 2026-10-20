#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Phase 3 placement plan: only Arenarea, using the supplied Fab vegetation.

Density here describes planting, not a global performance optimisation. Native
FoliageTypes retain their source rendering rules and master meshes.
"""

from pathlib import Path
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved/Jadg/arenarea-landscape"


def main():
    definition = json.loads(
        (ROOT / "Source/Elements/Terrain/arenarea/definition.json").read_text(encoding="utf8")
    )
    with np.load(OUT / "placement.npz") as archive:
        fields = {key: archive[key] for key in archive.files}
    inventory = json.loads((OUT / "fab-inventory.json").read_text(encoding="utf8"))
    rng = np.random.default_rng(definition["seed"])
    ox, oy = definition["origin_m"]
    step = definition["spacing_m"]
    qx, qy = definition["quads"]
    groups = {}
    families = {
        "garden": "vlkhcbxia",
        "wild": "vczndjqja",
        "bank": "tbdpec3r",
        "meadow": "tdcrdbur",
    }
    for row in inventory:
        if row["class"] != "StaticMesh" or "/Plants/" not in row["path"]:
            continue
        # The wheat F variant is fallen debris only; reserve it for a later prop pass.
        if row["path"].endswith("SM_tdcrdbur_VarF"):
            continue
        code = next(c for c in families.values() if c in row["path"])
        name = row["path"].rsplit("/", 1)[1]
        prefix = row["path"].split("/Raw/")[0]
        groups[name] = {
            "id": name,
            "code": code,
            "mesh": row["path"],
            "foliageType": prefix + "/Raw/FoliageTypes/FT_" + name[3:],
            "instances": [],
        }
    choices = {
        key: [name for name, g in groups.items() if g["code"] == code]
        for key, code in families.items()
    }

    def plant(x, y, density, force=None):
        ix = np.floor((x - ox) / step).astype(int)
        iy = np.floor((y - oy) / step).astype(int)
        ix = np.clip(ix, 0, qx - 1)
        iy = np.clip(iy, 0, qy - 1)
        allowed = fields["district"][iy, ix] & ~fields["water"][iy, ix]
        allowed &= (fields["reserved"][iy, ix] == 0) & (fields["road_distance"][iy, ix] > 2)
        allowed &= (fields["slope"][iy, ix] < 0.28) & (fields["height"][iy, ix] > 0.5)
        allowed &= rng.random(len(x)) < density
        for xx, yy, i, j in zip(x[allowed], y[allowed], ix[allowed], iy[allowed]):
            family = force or (
                "garden"
                if fields["gardens"][j, i] > 0.5
                else "bank"
                if fields["bank_distance"][j, i] < 25
                else "wild"
                if rng.random() < 0.7
                else "meadow"
            )
            name = rng.choice(choices[family])
            fx, fy = (xx - ox) / step - i, (yy - oy) / step - j
            h = fields["height"]
            z = (h[j, i] * (1 - fx) + h[j, i + 1] * fx) * (1 - fy) + (
                h[j + 1, i] * (1 - fx) + h[j + 1, i + 1] * fx
            ) * fy
            # Vendor roots remain embedded a centimetre; do not lift whole tufts by their bounds.
            groups[name]["instances"].append(
                [
                    round(float(xx), 3),
                    round(float(yy), 3),
                    round(float(z - 0.01), 4),
                    round(float(rng.uniform(0, 360)), 2),
                    round(float(rng.uniform(0.85, 1.15)), 3),
                ]
            )

    # A sparse initial vegetation cover for the whole Q07 envelope.
    y, x = np.mgrid[oy : oy + qy * step : 6, ox : ox + qx * step : 6]
    x = x.ravel() + rng.uniform(0, 6, x.size)
    y = y.ravel() + rng.uniform(0, 6, y.size)
    plant(x, y, 0.22)
    # First authored local planting passes: three gardens, prairie and pool bank.
    patches = [(g["bounds"], 0.9, 0.48, "garden") for g in definition["gardens"]]
    patches += [
        ([-1900, -700, -1790, -585], 1.1, 0.6, "wild"),
        ([-1830, 850, -1660, 1040], 1.4, 0.38, "bank"),
    ]
    for bounds, spacing, density, family in patches:
        x0, y0, x1, y1 = bounds
        yy, xx = np.mgrid[y0:y1:spacing, x0:x1:spacing]
        count = xx.size
        plant(
            xx.ravel() + rng.uniform(0, spacing, count),
            yy.ravel() + rng.uniform(0, spacing, count),
            density,
            family,
        )
    result = {
        "seed": definition["seed"],
        "groups": [g for g in groups.values() if g["instances"]],
        "scope": "Q07 only, initial cover and five authored patches; no global density optimisation",
    }
    (OUT / "foliage-plan.json").write_text(
        json.dumps(result, separators=(",", ":")), encoding="utf8"
    )
    print(
        "ARENAREA_FOLIAGE_PREPARED",
        sum(len(g["instances"]) for g in result["groups"]),
        "instances",
        len(result["groups"]),
        "variants",
    )


if __name__ == "__main__":
    main()
