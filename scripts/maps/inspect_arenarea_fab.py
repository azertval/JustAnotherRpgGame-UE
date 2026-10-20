#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Read-only inventory for the Arenarea Landscape; see its production guide."""

import json
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Saved/Jadg/arenarea-landscape"
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for data in u.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(
    "/Game/Bibliotheque/Scans/Megascans", recursive=True
):
    cls = str(data.asset_class_path.asset_name)
    if cls not in (
        "StaticMesh",
        "Texture2D",
        "MaterialInstanceConstant",
        "FoliageType_InstancedStaticMesh",
    ):
        continue
    row = {"path": str(data.package_name), "class": cls}
    obj = data.get_asset()
    if cls == "StaticMesh":
        box = obj.get_bounding_box()
        row.update(
            naniteTriangles=obj.get_num_nanite_triangles(),
            minimum=[box.min.x, box.min.y, box.min.z],
            maximum=[box.max.x, box.max.y, box.max.z],
            materials=[
                s.material_interface.get_path_name() if s.material_interface else None
                for s in obj.static_materials
            ],
        )
    elif cls == "Texture2D":
        row.update(
            srgb=obj.srgb,
            virtualTexture=obj.virtual_texture_streaming,
            compression=str(obj.compression_settings),
        )
    elif cls == "MaterialInstanceConstant":
        row["parent"] = obj.parent.get_path_name()
    rows.append(row)
(OUT / "fab-inventory.json").write_text(json.dumps(rows, indent=2), encoding="utf8")
print("ARENAREA_FAB_INVENTORY_OK", len(rows))
