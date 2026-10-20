#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Reload saved maps and verify real Nanite resources and physical ground samples.

Read-only audit called from review_capital_terrain_labs.ps1. No world is saved here.
"""

from pathlib import Path
import json
import sys

import unreal as u

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/maps"))
import district_surface  # noqa: E402
from build_capital_terrain_labs import MAPS, REPORT  # noqa: E402
from capital_terrain_lab_materials import CONTENT, LAYERS  # noqa: E402


def main():
    reports = []
    errors = []
    for kind in MAPS:
        world = u.EditorLoadingAndSavingUtils.load_map("/Game/Maps/Levels/essai/" + kind)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
        landscapes = [a for a in actors if isinstance(a, u.Landscape)]
        if len(landscapes) != 1:
            raise RuntimeError("Expected one Landscape: " + kind)
        land = landscapes[0]
        components = land.get_components_by_class(u.LandscapeNaniteComponent)
        triangles = [c.static_mesh.get_num_nanite_triangles() for c in components]
        if not triangles or min(triangles) <= 0:
            errors.append(kind + ": saved Nanite data missing")
        doc = json.loads(
            (ROOT / "Source/Test/Fixtures/Exploration/Levels/essai" / (kind + ".json")).read_text(
                encoding="utf8"
            )
        )
        probes = []
        for x, y in [(-45, 45), (45, 45), (-45, -45), (45, -45)]:
            expected = district_surface.ground_height(doc, x, y)
            hit = u.SystemLibrary.line_trace_single(
                world,
                u.Vector(x * 100, y * 100, 9000),
                u.Vector(x * 100, y * 100, -1000),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                True,
                [],
                u.DrawDebugTrace.NONE,
                True,
            )
            if hit is None:
                errors.append(kind + ": no terrain collision")
                probes.append({"xy": [x, y], "hit": False})
                continue
            values = u.GameplayStatics.break_hit_result(hit)
            z = values[5].z / 100
            probes.append(
                {"xy": [x, y], "expectedZ": expected, "collisionZ": z, "errorMetres": z - expected}
            )
            if not values[0] or abs(z - expected) > 0.03:
                errors.append(f"{kind}: terrain/collision disagreement at {x},{y}")
        if kind in ("capitale-sols-urbains", "capitale-rives"):
            x, y, expected = (
                (0.375, 0.375, 20.265) if kind == "capitale-sols-urbains" else (18.375, 0.375, 3.5)
            )
            hit = u.SystemLibrary.line_trace_single(
                world,
                u.Vector(x * 100, y * 100, 9000),
                u.Vector(x * 100, y * 100, -1000),
                u.TraceTypeQuery.TRACE_TYPE_QUERY1,
                True,
                [],
                u.DrawDebugTrace.NONE,
                True,
            )
            if hit is None:
                errors.append(kind + ": no paving collision")
            else:
                values = u.GameplayStatics.break_hit_result(hit)
                z = values[5].z / 100
                probes.append(
                    {
                        "xy": [x, y],
                        "kind": "paving module",
                        "expectedZ": expected,
                        "collisionZ": z,
                        "errorMetres": z - expected,
                    }
                )
                if not values[0] or abs(z - expected) > 0.04:
                    errors.append(kind + ": paving fallback does not meet expected surface")
        reports.append(
            {"map": kind, "naniteTrianglesAfterReload": triangles, "physicalGroundProbes": probes}
        )
    material = u.EditorAssetLibrary.load_asset(CONTENT + "/Materials/M_Landscape_Capitale")
    declared = [str(x) for x in u.JadgSceneBuild.landscape_layer_names(material)]
    if set(declared) != set(LAYERS):
        errors.append("Landscape layer names do not match imported weights")
    report = {
        "maps": reports,
        "layers": declared,
        "errors": errors,
        "scope": "Saved Nanite resources and terrain contact heights; not a full character traversal certification",
    }
    (REPORT / "audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8"
    )
    if errors:
        raise RuntimeError("; ".join(errors))
    print("CAPITAL_TERRAIN_LABS_AUDIT_OK")


if __name__ == "__main__":
    main()
