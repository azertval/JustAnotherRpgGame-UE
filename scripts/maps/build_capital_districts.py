#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Build the approved complete Arenarea and Martpart districts, reproducibly.

Blender source: build_arenarea_district.py and build_martpart_district.py.
Geometry manifests: Built/arenarea-district/manifest.json and
Built/martpart-district/manifest.json. Engine outputs: /Game/Districts,
/Game/Kit/Built/arenarea-district, /Game/Kit/Built/martpart-district and
/Game/Maps/Levels/central-empire/capital. Existing quest contracts are checked
before committing a canonical map. Saved/Jadg/districts holds recovery copies.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import gc
import hashlib
import html
import json
import math
from pathlib import Path
import shutil
import sys
import time

# Archived generator: the current construction world must not be overwritten.
if __name__ == "__main__":
    raise RuntimeError("Generateur historique archive apres nettoyage. Ouvrir /Game/Capitale/Cartes/Capitale ; restauration explicite requise pour regenerer les anciens essais.")

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "Source/Elements/Assets"
REPORTS = ROOT / "Saved/Jadg/districts"
DISTRICTS = ("arenarea", "martpart")
REVISION = "capital-urban-relief-20261011"
SHARED_FURNITURE = frozenset(
    f"Built/arena-fate-props/{name}.glb"
    for name in ("afp-loge-table-sculpted", "afp-loge-chair-sculpted", "afp-bench", "afp-barrel")
)
sys.path.insert(0, str(ROOT / "scripts/maps"))
sys.path.insert(0, str(ROOT / "scripts/assetsGeneration"))
import jadg_map  # noqa: E402
import district_surface  # noqa: E402


def source_path(district: str) -> Path:
    if district not in DISTRICTS:
        raise ValueError(f"Unknown district: {district}")
    return ROOT / "Source/Elements/Levels/central-empire/capital" / f"{district}.json"


def manifest_path(district: str) -> Path:
    return ASSETS / f"Built/{district}-district/manifest.json"


def read_manifest(district: str) -> dict:
    path = manifest_path(district)
    manifest = json.loads(path.read_text(encoding="utf-8"))
    for item in manifest["meshes"]:
        mesh = path.parent / item["file"]
        if not mesh.is_file():
            raise RuntimeError(f"Missing mesh: {mesh}")
        if item.get("sha256") and hashlib.sha256(mesh.read_bytes()).hexdigest() != item["sha256"]:
            raise RuntimeError(f"Stale geometry manifest: {mesh}")
    collision_plan(district, manifest)
    return manifest


def collision_plan(district: str, manifest: dict) -> list[dict]:
    """Resolve authored physical meshes, never instantiate them as scenery.

    Arenarea requires coverage for every colliding local visual mesh: exporting
    its repeated sculpted foliage/houses to Recast exhausted the process commit.
    Existing Martpart manifests retain their previous policy until they declare
    proxies, at which point the same complete-coverage contract applies.
    """
    meshes = {item["id"]: item for item in manifest["meshes"]}
    if len(meshes) != len(manifest["meshes"]):
        raise RuntimeError("Duplicate district mesh identifier")
    paths = {f"Built/{district}-district/{item['file']}": item for item in meshes.values()}
    required = district == "arenarea" or any(item.get("collisionMesh") for item in meshes.values())
    result = {}
    for placed in manifest["objects"]:
        visual = meshes.get(placed.get("meshId")) if not placed.get("mesh") else paths.get(placed["mesh"])
        if visual is None:
            # Shared Arena meshes retain their own previously validated proxies.
            # These compact furnishings retain their source collision, too.
            source = placed.get("mesh", "")
            if source.startswith("Built/arena-fate-modern/") or source in SHARED_FURNITURE:
                continue
            raise RuntimeError(f"Unknown district visual mesh: {placed['id']}")
        if visual.get("role") == "collision-proxy":
            raise RuntimeError(f"Collision proxy cannot be placed as scenery: {placed['id']}")
        if placed.get("collision") is False:
            continue
        proxy_id = visual.get("collisionMesh")
        if not proxy_id:
            if required:
                raise RuntimeError(f"Missing architectural collision proxy: {visual['id']}")
            continue
        proxy = meshes.get(proxy_id)
        if proxy is None or proxy.get("role") != "collision-proxy" or proxy_id == visual["id"]:
            raise RuntimeError(f"Invalid collisionMesh for {visual['id']}: {proxy_id}")
        if visual["id"] not in result:
            result[visual["id"]] = {
                "source": f"Built/{district}-district/{visual['file']}",
                "collisionSource": f"Built/{district}-district/{proxy['file']}",
                "visualSourceTriangles": visual["triangles"],
                "collisionSourceTriangles": proxy["triangles"], "instances": 0,
            }
        result[visual["id"]]["instances"] += 1
    return [result[key] for key in sorted(result)]


def tag_occlusion_supports(placed: list[dict]) -> int:
    """Hide dependent roofs and fittings with their supporting scene object."""
    actors = {item["id"]: item["actor"] for item in placed}
    relationships = []
    for item in placed:
        supports = item.get("supportsObject", [])
        if isinstance(supports, str):
            supports = [supports]
        if not isinstance(supports, list):
            raise RuntimeError(f"Invalid occlusion supports: {item['id']}")
        for support in supports:
            if not isinstance(support, str) or support not in actors or support == item["id"]:
                raise RuntimeError(f"Unknown or self-referencing occlusion support: {item['id']} -> {support}")
            relationships.append((item["id"], support))
    for dependent, support in relationships:
        for actor, tag in ((actors[support], "JadgWitnessSurface:" + support),
                           (actors[dependent], "JadgWitnessSupport:" + support)):
            tags = list(actor.tags)
            if tag not in {str(value) for value in tags}:
                actor.tags = tags + [tag]
    return len(relationships)


def memory_snapshot() -> dict:
    """Read this process and system commit via Windows, without a UE extension."""
    if sys.platform != "win32":
        return {"available": False, "reason": "Windows process counters unavailable"}
    import ctypes
    from ctypes import wintypes

    size = ctypes.c_size_t

    class ProcessCounters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (name, size) for name in ("peakWorkingSet", "workingSet", "peakPaged", "paged",
                                      "peakNonPaged", "nonPaged", "pagefile", "peakPagefile", "private")]

    class PerformanceInfo(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD)] + [(name, size) for name in (
            "commitTotal", "commitLimit", "commitPeak", "physicalTotal", "physicalAvailable",
            "systemCache", "kernelTotal", "kernelPaged", "kernelNonPaged", "pageSize")] + [
            (name, wintypes.DWORD) for name in ("handles", "processes", "threads")]

    try:
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessCounters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        psapi.GetPerformanceInfo.argtypes = [ctypes.POINTER(PerformanceInfo), wintypes.DWORD]
        psapi.GetPerformanceInfo.restype = wintypes.BOOL
        process, system = ProcessCounters(), PerformanceInfo()
        process.cb, system.cb = ctypes.sizeof(process), ctypes.sizeof(system)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(process), process.cb):
            return {"available": False, "windowsError": ctypes.get_last_error()}
        report = {"available": True, "source": "Windows GetProcessMemoryInfo/GetPerformanceInfo",
                  "processWorkingSetBytes": process.workingSet, "processPrivateCommitBytes": process.private,
                  "processPeakPrivateCommitBytes": process.peakPagefile}
        if psapi.GetPerformanceInfo(ctypes.byref(system), system.cb):
            report.update({"systemCommitBytes": system.commitTotal * system.pageSize,
                           "systemCommitLimitBytes": system.commitLimit * system.pageSize,
                           "systemPhysicalAvailableBytes": system.physicalAvailable * system.pageSize})
        return report
    except (AttributeError, OSError) as error:
        return {"available": False, "reason": str(error)}


def install_architectural_collision(library, district: str, manifest: dict) -> dict:
    """Bind exact authored proxies to visual BodySetup before actors/nav exist.

    This is the same recook path as the Arena ring proxies. Nanite geometry,
    fallback geometry and visual materials are deliberately left intact.
    """
    import unreal

    entries = []
    plan = collision_plan(district, manifest)
    for index, item in enumerate(plan, 1):
        proxy = library.static_mesh(item["collisionSource"], collision_proxy=True)
        settings = proxy.get_editor_property("nanite_settings").copy()
        if settings.enabled:
            settings.enabled = False
            proxy.set_editor_property("nanite_settings", settings)
        if not proxy.get_editor_property("allow_cpu_access"):
            proxy.set_editor_property("allow_cpu_access", True)
        proxy_body = proxy.get_editor_property("body_setup")
        if proxy_body is None:
            raise RuntimeError(f"Collision proxy has no BodySetup: {item['collisionSource']}")
        proxy_body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        if not unreal.EditorAssetLibrary.save_loaded_asset(proxy):
            raise RuntimeError(f"Could not save collision proxy: {item['collisionSource']}")
        if proxy.get_editor_property("nanite_settings").enabled or not proxy.get_editor_property("allow_cpu_access"):
            raise RuntimeError(f"Collision proxy rejected non-Nanite CPU geometry: {item['collisionSource']}")
        triangles = proxy.get_num_triangles(0)
        if triangles <= 0 or triangles != item["collisionSourceTriangles"]:
            raise RuntimeError(f"Proxy LOD0 differs from authored triangles: {item['collisionSource']}")
        visual = library.static_mesh(item["source"])
        body = visual.get_editor_property("body_setup")
        if body is None:
            raise RuntimeError(f"Visual mesh has no BodySetup: {item['source']}")
        nanite_before = visual.get_editor_property("nanite_settings").copy()
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        # Always notify: reimport can replace a proxy at the same object path.
        # UE recooks physics and NavCollision from ComplexCollisionMesh.
        visual.set_editor_property("complex_collision_mesh", proxy)
        if visual.get_editor_property("complex_collision_mesh") != proxy:
            raise RuntimeError(f"Visual mesh rejected collision proxy: {item['source']}")
        if not unreal.EditorAssetLibrary.save_loaded_asset(visual):
            raise RuntimeError(f"Could not save architectural collision: {item['source']}")
        nanite_after = visual.get_editor_property("nanite_settings")
        for field in ("enabled", "fallback_target", "fallback_percent_triangles", "fallback_relative_error"):
            if getattr(nanite_before, field) != getattr(nanite_after, field):
                raise RuntimeError(f"Collision binding changed visual Nanite/fallback: {item['source']}/{field}")
        entries.append({**item, "collisionTriangles": triangles, "collisionAsset": proxy.get_path_name(),
                        "collisionNanite": False, "collisionTraceFlag": "CTF_USE_COMPLEX_AS_SIMPLE",
                        "navigationGeometry": "architectural-proxy-body-setup"})
        if index % 16 == 0 or index == len(plan) or triangles >= 1_000_000:
            before = memory_snapshot()
            # All pairs are saved; actors do not exist yet. Release Python's
            # mesh/BodySetup wrappers before synchronous commandlet GC, which
            # can unload these packages. Later placement reloads saved assets.
            # Dense terrain pairs need this immediately, before another import
            # retains its temporary geometry alongside the saved terrain.
            del proxy, proxy_body, visual, body, settings, nanite_before, nanite_after
            library.static.clear()
            gc.collect()
            unreal.collect_garbage()
            after = memory_snapshot()
            if before.get("available") and after.get("available"):
                mib = 1024 * 1024
                previous = before["processPrivateCommitBytes"] / mib
                current = after["processPrivateCommitBytes"] / mib
                print(f"[DistrictCollisionGC] {index}/{len(plan)} pairs; private MiB "
                      f"{previous:.0f} -> {current:.0f}; released {previous - current:.0f}", flush=True)
            else:
                print(f"[DistrictCollisionGC] {index}/{len(plan)} pairs; memory unavailable", flush=True)
    repeated = sum(item["collisionTriangles"] * item["instances"] for item in entries)
    return {"meshes": entries, "proxyMeshes": len({item["collisionSource"] for item in entries}),
            "coveredVisualMeshes": len(entries), "coveredInstances": sum(item["instances"] for item in entries),
            "authoredVisualTrianglesTimesInstances": sum(item["visualSourceTriangles"] * item["instances"] for item in entries),
            "physicalTrianglesTimesInstances": repeated,
            "estimatedRecastRawCacheBytes": repeated * 84,
            "estimateScope": "9 doubles and 3 int32 per triangle; excludes Arena, headers, temporaries and nav tiles"}


def gameplay_contract(doc: dict) -> dict:
    """Only authored spatial fields may change; preserve all conditions and IDs."""
    spatial = {"x", "y", "storey", "volume", "cells"}
    return {
        "entities": sorted(
            [{k: deepcopy(v) for k, v in entity.items() if k not in spatial}
             for entity in doc.get("entities", [])], key=lambda entity: entity["id"]),
        "party": deepcopy(doc.get("party")),
        "nextEntityId": doc.get("nextEntityId"),
        "name": doc.get("name"), "place": doc.get("place"),
    }


def make_document(district: str, manifest: dict, original: dict) -> tuple[dict, dict]:
    meta = manifest["metadata"]
    surface_errors = district_surface.validate_surface(meta)
    if surface_errors:
        raise RuntimeError("; ".join(surface_errors))
    x0, y0, x1, y1 = meta["area"]
    origin = [math.floor(x0 / 1.5) * 1.5, math.floor(y0 / 1.5) * 1.5]
    levels = deepcopy(meta.get("levels", [{"name": "rez", "z": 0.0}]))
    entities = deepcopy(original.get("entities", []))
    positions = meta["entityPositions"]
    for entity in entities:
        if entity["id"] not in positions:
            raise RuntimeError(f"Unmapped existing entity: {district}/{entity['id']}")
        point = positions[entity["id"]]
        entity["x"], entity["y"] = jadg_map.cell_of(point[0], point[1], origin)
        entity["storey"] = district_surface.storey_at(meta, point)
        if entity["type"] == "zone":
            columns, rows = entity.get("width", 1), entity.get("height", 1)
            # Core triggers rectangular zones from x/y (their top-left cell),
            # not their visual volume. Keep both representations identical.
            entity["x"] -= columns // 2
            entity["y"] -= rows // 2
            left = origin[0] + entity["x"] * 1.5
            top = origin[1] + entity["y"] * 1.5
            entity.pop("cells", None)
            entity["volume"] = {
                "min": [left, top, point[2] - .3],
                "max": [left + columns * 1.5, top + rows * 1.5, point[2] + 3.0],
            }
    registry = {mesh["id"]: f"Built/{district}-district/{mesh['file']}" for mesh in manifest["meshes"]}
    objects = []
    for placed in manifest["objects"]:
        mesh = placed.get("mesh") or registry[placed["meshId"]]
        if not (ASSETS / mesh).is_file():
            raise RuntimeError(f"Missing scenery source: {mesh}")
        item = {
            "id": placed["id"], "mesh": mesh, "position": list(placed["position"]),
            "yaw": placed.get("yaw", 0.0), "folder": placed.get("role", "architecture"),
            "storey": placed.get("storey", 0),
        }
        # Manifest positions are absolute, JSON positions are relative to their storey.
        if isinstance(item["storey"], str):
            item["storey"] = next(i for i, level in enumerate(levels) if level["name"] == item["storey"])
        item["position"][2] -= levels[item["storey"]]["z"]
        for field in ("scale", "height", "pitch", "roll", "mirrored"):
            if field in placed:
                item[field] = deepcopy(placed[field])
        objects.append(item)
    start = meta["start"]
    cx, cy = jadg_map.cell_of(start[0], start[1], origin)
    distant_ground_z = min([-3.0] + [water["position"][2] - 3.0 for water in meta.get("waters", [])])
    doc = {
        "format": jadg_map.FORMAT, "version": jadg_map.VERSION,
        "name": original["name"], "place": original["place"],
        "comment": f"Quartier sculpte et peint, relief urbain autorise le 11 octobre 2026. {REVISION}",
        "width": math.ceil((x1 - origin[0]) / 1.5), "height": math.ceil((y1 - origin[1]) / 1.5),
        "origin": origin, "storeys": levels, "nextEntityId": original["nextEntityId"],
        "tiles": [{"x": cx, "y": cy, "type": "entry"}], "entities": entities,
        "objects": objects, "party": deepcopy(original["party"]),
        "lighting": {
            "lampCandelas": 36.0, "fireCandelas": 24.0,
            "sunScale": 1.65, "ambientScale": .34, "skyLuminance": 1.8,
            "exposureBias": 0.0,
            "fog": {"density": .0015, "falloff": .15, "volumetric": True},
            "post": {"bloom_intensity": .25, "vignette_intensity": .12,
                     "motion_blur_amount": 0.0, "film_grain_intensity": 0.0},
        },
        "daylight": original.get("daylight", jadg_map.DAYLIGHT),
        "ground": {"colour": "#716650", "size": 3000.0, "height": distant_ground_z},
        "navigation": {"area": list(meta["area"]), "floor": -8.0, "height": 60.0},
        "shots": [{"id": shot.get("id", shot.get("name")), "target": shot["target"],
                   "heading": shot.get("heading", shot.get("yaw", 0)) % 360,
                   "pitch": shot["pitch"], "distance": shot["distance"]}
                  for shot in meta["shots"]],
        "hours": ["12:00", "22:00"],
    }
    for key in ("groundHeightfield", "storeyRegions"):
        if key in meta:
            doc[key] = deepcopy(meta[key])
    if gameplay_contract(original) != gameplay_contract(doc):
        raise RuntimeError(f"Gameplay contract changed: {district}")
    errors = jadg_map.validate(doc)
    if errors:
        raise RuntimeError("; ".join(errors))
    return doc, {"gameplayPreserved": True, "entityCount": len(entities),
                 "objects": len(objects), "landmarks": meta.get("landmarks", []),
                 "renderRevision": REVISION}


def prepare(district: str) -> tuple[dict, dict, dict]:
    manifest = read_manifest(district)
    original = json.loads(source_path(district).read_text(encoding="utf-8"))
    doc, evidence = make_document(district, manifest, original)
    folder = REPORTS / district
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "proposed-map.json").write_text(jadg_map.dumps(doc), encoding="utf-8")
    return doc, evidence, manifest


def archive_original(district: str) -> None:
    folder = REPORTS / district
    folder.mkdir(parents=True, exist_ok=True)
    for source, backup in (
        (source_path(district), folder / "source-before-district.json"),
        (ROOT / f"Content/Maps/Levels/central-empire/capital/{district}.umap", folder / "map-before-district.umap"),
    ):
        if source.is_file() and not backup.exists():
            shutil.copy2(source, backup)


def district_materials(manifest: dict) -> dict:
    import unreal
    import arena_wicked_materials as approved

    keys = list(approved.NAMES) + list(approved.ALIASES)
    base = {}
    for name in keys:
        path = f"/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_{name}"
        base[name] = (unreal.EditorAssetLibrary.load_asset(path)
                      if unreal.EditorAssetLibrary.does_asset_exist(path) else None)
    if any(value is None for value in base.values()):
        base = approved.build_materials("painted")
    # District aliases retain the approved physical PBR texture inputs. Their
    # authored colour identifies foliage, plaster, tile or textiles, not light.
    aliases = {
        "foliage": {"source": "stone_cream", "colour": [.085, .20, .045]},
        "leaf": {"source": "stone_cream", "colour": [.085, .20, .045]},
        "grass": {"source": "sand", "colour": [.10, .18, .045]},
        "roof_blue": {"source": "roof_terracotta", "colour": [.025, .07, .16]},
        "cloth_blue": {"source": "linen", "colour": [.03, .09, .20]},
        "cloth_ochre": {"source": "linen", "colour": [.38, .22, .045]},
        "plaster": {"source": "stone_cream", "colour": [.60, .46, .29]},
        "water": {"source": "marble_white", "colour": [.025, .13, .15]},
    }
    meta = manifest.get("metadata", {})
    aliases.update(meta.get("materialAliases", {}))
    for name, colour in meta.get("materialColors", {}).items():
        spec = aliases.get(name, name if name in base else "stone_cream")
        aliases[name] = {"source": spec, "colour": colour[:3]} if isinstance(spec, str) else {**spec, "colour": colour[:3]}
    # Independent instances per district: creating Martpart must never recolour
    # an Arenarea material which is already saved on actors.
    district = manifest.get("generator", "").split("build_")[-1].split("_district")[0]
    if district not in DISTRICTS:
        raise RuntimeError("District material namespace cannot be determined")
    folder = f"/Game/Districts/{district}/Materials"
    unreal.EditorAssetLibrary.make_directory(folder)
    ml = unreal.MaterialEditingLibrary
    for name, spec in aliases.items():
        if isinstance(spec, str):
            base[name] = base[spec]
            continue
        source = base[spec.get("source", "stone_cream")]
        path = f"{folder}/MI_{name}"
        material = (unreal.EditorAssetLibrary.load_asset(path)
                    if unreal.EditorAssetLibrary.does_asset_exist(path) else None)
        if material is None:
            material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
                f"MI_{name}", folder, unreal.MaterialInstanceConstant,
                unreal.MaterialInstanceConstantFactoryNew())
        ml.set_material_instance_parent(material, source)
        if "colour" in spec:
            ml.set_material_instance_vector_parameter_value(material, "QuietColour", unreal.LinearColor(*spec["colour"], 1))
            ml.set_material_instance_scalar_parameter_value(material, "ColourDetail", spec.get("detail", .22))
        ml.update_material_instance(material)
        unreal.EditorAssetLibrary.save_loaded_asset(material)
        base[name] = material
    return base


def assign_materials(actor, item: dict, materials: dict, meta: dict) -> None:
    component = actor.static_mesh_component
    overrides = meta.get("materialOverrides", {})
    swaps = {**overrides.get(Path(item["mesh"]).stem, {}), **overrides.get(item["id"], {})}
    scripted = item["mesh"].startswith("Built/")
    for index, slot in enumerate(component.static_mesh.get_editor_property("static_materials")):
        names = [str(slot.get_editor_property(key)) for key in ("imported_material_slot_name", "material_slot_name")]
        name = next((name for name in names if name in materials), None)
        if name is None:
            if scripted:
                raise RuntimeError(f"Unmapped material {item['mesh']}: {names}")
            continue  # Master/legacy pieces retain their complete original textures.
        target = swaps.get(name, name)
        component.set_material(index, materials[target])


def preserve_collision(library, objects: list[dict]) -> list[dict]:
    import unreal
    result = []
    roles = {"floor", "ground", "street", "paving", "stairs", "bridge", "deck", "seating"}
    for source in sorted({item["mesh"] for item in objects if item["folder"] in roles and item["mesh"].startswith("Built/")}):
        mesh = library.static_mesh(source)
        settings = mesh.get_editor_property("nanite_settings").copy()
        if settings.fallback_target != unreal.NaniteFallbackTarget.PERCENT_TRIANGLES or settings.fallback_percent_triangles != 1 or settings.fallback_relative_error != 0:
            settings.fallback_target = unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
            settings.fallback_percent_triangles = 1.0
            settings.fallback_relative_error = 0.0
            mesh.set_editor_property("nanite_settings", settings)
            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        result.append({"source": source, "triangles": mesh.get_num_triangles(0)})
    return result


def build_editor(district: str) -> dict:
    import unreal
    import build_level as scene
    from arena_lighting import sculpted_ambient_cube
    import district_atmosphere

    started = time.perf_counter()
    memory = {"beforeAssetImports": memory_snapshot()}
    manifest_bytes = manifest_path(district).read_bytes()
    original_bytes = source_path(district).read_bytes()
    doc, evidence, manifest = prepare(district)
    if manifest_path(district).read_bytes() != manifest_bytes:
        raise RuntimeError("Geometry manifest changed while it was being read")
    archive_original(district)
    meta = manifest["metadata"]
    materials = district_materials(manifest)
    scene.GROUND_MATERIAL = f"/Game/Districts/{district}/M_DistantGround"
    scene.CONTOUR_MATERIAL = f"/Game/Districts/{district}/M_Contour"
    scene.OUTLINE_MATERIAL = f"/Game/Districts/{district}/M_Outline"
    library = scene.Library()
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE))
    architectural_collision = install_architectural_collision(library, district, manifest)
    architectural_collision["manifestSha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    (REPORTS / district / "collision.json").write_text(
        json.dumps(architectural_collision, indent=2), encoding="utf-8")
    scene.log(f"District {district}: architectural collision covers "
              f"{architectural_collision['coveredInstances']} instances, "
              f"{architectural_collision['physicalTrianglesTimesInstances']} physical triangles")
    # Bind physics first: preserving the visual full fallback may recook the
    # mesh, and that recook must already read its architectural collision.
    collision = preserve_collision(library, doc["objects"])
    shared_collision = []
    arena_sources = {item["mesh"] for item in doc["objects"]
                     if item["mesh"].startswith("Built/arena-fate-modern/")}
    if arena_sources:
        # Reusing the monument must retain its authored collision proxies and
        # full floor geometry, including after a shared GLB was reimported.
        from build_arena_fate_modern_scene import preserve_walkable_collision
        arena_source = source_path("arenarea").parent / "arenarea/arena-of-fate.json"
        arena_doc = json.loads(arena_source.read_text(encoding="utf-8"))
        arena_doc["objects"] = [item for item in arena_doc["objects"] if item["mesh"] in arena_sources]
        shared_collision = preserve_walkable_collision(library, arena_doc)
    memory["afterCollisionImports"] = memory_snapshot()
    world = unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
    if world is None:
        raise RuntimeError("Cannot create district world")
    level = scene.Level(world)
    occluders = set(meta.get("roofsIds", meta.get("roofObjectIds", [])))
    occluders.update(item["id"] for item in manifest["objects"] if item.get("occluder"))
    placed = []
    source_objects = {item["id"]: item for item in manifest["objects"]}
    for item in doc["objects"]:
        actor = scene.place_object(level, frame, doc, library, item, item["folder"])
        assign_materials(actor, item, materials, meta)
        raw = source_objects[item["id"]]
        if raw.get("occluder") is not False and (item["id"] in occluders or item["folder"] in ("wall", "roof")):
            actor.tags = list(actor.tags) + ["JadgWitnessOccluder"]
        if raw.get("collision") is False:
            actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        placed.append({**item, **raw, "actor": actor})
    occlusion_supports = tag_occlusion_supports(placed)
    scene.place_sky(level, doc, frame)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == "SolLointain":
            actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        if isinstance(actor, unreal.SkyLight):
            actor.light_component.set_editor_property("cubemap", sculpted_ambient_cube())
            actor.light_component.set_editor_property("lower_hemisphere_is_black", False)
    scene.place_navigation(level, doc, frame)
    scene.place_characters(level, doc, frame, library)
    scene.place_entities(level, doc, frame)
    map_id = f"central-empire/capital/{district}"
    scene.place_frame(level, doc, frame, map_id, source_path(district))
    scene.place_shots(level, doc, frame)
    atmosphere = district_atmosphere.build_environment(level, frame, doc, library, meta)
    if hasattr(district_atmosphere, "decorate_components"):
        atmosphere["wind"] = district_atmosphere.decorate_components(placed, meta)
    review = level.spawn(scene.game_class("JadgWitnessReview"), unreal.Vector(), unreal.Rotator(),
                         "DistrictPhysicalReview", "controle")
    # A cutaway exposes a room to the player's view and light together. Retaining
    # an invisible roof's shadow made playable interiors unreadable at noon.
    review.set_editor_property("keep_hidden_shadows", False)
    review.set_editor_property("keep_hidden_indirect_lighting", False)
    route = meta.get("visitRoute", meta["route"])
    if len(route) < 2:
        raise RuntimeError("A district must provide a physical inspection route")
    review.set_editor_property("route_points", [frame.map_point(point) for point in route])
    review.set_editor_property("point_tolerance", 65.0)
    review.set_editor_property("height_tolerance", 25.0)
    review.set_editor_property("leg_timeout", 180.0)
    review.set_editor_property("startup_timeout", 600.0)
    review.set_editor_property("fine_navigation", True)
    review.set_editor_property("navigation_cell_size", 12.0)
    review.set_editor_property("navigation_cell_height", 5.0)
    review.set_editor_property("navigation_tile_size", 2400.0)
    # The district includes roofs, raised gardens and the arena galleries. The
    # default three layers exhausted the runtime pool during the first review.
    review.set_editor_property("navigation_average_layers", 12.0)
    review.set_editor_property("navigation_max_search_nodes", 65536)
    world.get_world_settings().set_editor_property("default_game_mode", scene.game_class("JadgGameMode"))
    start = frame.map_point([*route[0][:2], route[0][2] + .25])
    memory["beforeNavigation"] = memory_snapshot()
    memory_file = REPORTS / district / "memory.json"
    # Persist the pre-build measurement: an OOM cannot write the final report.
    memory_file.write_text(json.dumps(memory, indent=2), encoding="utf-8")
    # The first call creates Recast before PrepareFineNavigation can configure
    # it. Seed its capacity locally so that this initial build is not truncated.
    # Restore the class defaults immediately; never persist project-wide config.
    nav_defaults = unreal.get_default_object(unreal.RecastNavMesh)
    initial_capacity = {key: nav_defaults.get_editor_property(key)
                        for key in ("average_layers_per_tile", "tile_size_uu")}
    try:
        nav_defaults.set_editor_property("average_layers_per_tile", 12.0)
        nav_defaults.set_editor_property("tile_size_uu", 2400.0)
        unreal.JadgSceneBuild.unreachable_points(world, start, [])
    finally:
        for key, value in initial_capacity.items():
            nav_defaults.set_editor_property(key, value)
    if not review.prepare_fine_navigation():
        raise RuntimeError("District navigation profile could not be applied")
    targets = [(item["id"], item["position"]) if isinstance(item, dict) else (str(i), item)
               for i, item in enumerate(meta.get("navigationTargets", []))]
    # Verify actual quantized quest arrivals as well as authored landmarks.
    for entity in doc["entities"]:
        if entity.get("sealed") or entity["type"] == "zone":
            continue
        point = jadg_map.cell_centre(entity["x"], entity["y"], doc["origin"])
        point[2] = district_surface.ground_height(doc, point[0], point[1], entity.get("storey", 0))
        targets.append(("entity-" + entity["id"], point))
    checks = [(f"route-{i}", p) for i, p in enumerate(route)] + targets
    crowd_ids = set()
    for route_index, crowd_route in enumerate(meta.get("crowdRoutes", [])):
        if len(crowd_route) < 2:
            raise RuntimeError(f"Crowd route {route_index} needs at least two points")
        for point_index, point in enumerate(crowd_route):
            identifier = f"crowd-route-{route_index}-point-{point_index}"
            crowd_ids.add(identifier)
            checks.append((identifier, point))
    points = [frame.map_point([p[0], p[1], p[2] + .25]) for _, p in checks]
    disconnected = list(unreal.JadgSceneBuild.unreachable_points(world, start, points))
    memory["afterNavigation"] = memory_snapshot()
    memory_file.write_text(json.dumps(memory, indent=2), encoding="utf-8")
    projections = []
    for identifier, point in checks:
        # Match DistrictLife's vertical search and rejection threshold for
        # residents, while retaining the tighter authored visit-point check.
        is_crowd = identifier in crowd_ids
        requested = frame.map_point(point)
        projected = unreal.NavigationSystemV1.project_point_to_navigation(
            world, requested, None, None, unreal.Vector(80, 80, 150 if is_crowd else 30))
        height_error_cm = abs(projected.z - requested.z) if projected is not None else None
        valid = projected is not None and (not is_crowd or height_error_cm <= 100)
        projections.append({"id": identifier, "requested": point,
                            "projected": frame.map_of_point(projected) if projected is not None else None,
                            "valid": valid, "heightErrorCm": height_error_cm,
                            "projectionExtentCm": [80, 80, 150 if is_crowd else 30]})
    unreachable = ["entry" if i == -1 else checks[i][0] if 0 <= i < len(checks)
                   else f"unknown-navigation-index-{i}" for i in disconnected]
    report = {**evidence, "district": district, "route": route, "targetChecks": projections,
              "unreachable": unreachable,
              "missingNavigation": [p["id"] for p in projections if not p["valid"]],
              "navigation": json.loads(review.get_navigation_settings_json()),
              "collision": collision, "architecturalCollision": architectural_collision,
              "sharedArenaCollision": shared_collision, "memory": memory, "atmosphere": atmosphere,
              "occlusionSupports": occlusion_supports,
              "manifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
              "imports": library.imported, "seconds": round(time.perf_counter() - started, 2),
              "sourceCommitted": False, "artisticApproval": "full-district-review-pending"}
    folder = REPORTS / district
    (folder / "build.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    package = jadg_map.package(map_id)
    if report["unreachable"] or report["missingNavigation"]:
        # Diagnostics stay in Saved; a failed build must not leave another playable package.
        raise RuntimeError(f"District navigation failed: {report['unreachable']}; missing: {report['missingNavigation']}")
    if manifest_path(district).read_bytes() != manifest_bytes or source_path(district).read_bytes() != original_bytes:
        raise RuntimeError("District sources changed during construction; rebuild before committing")
    if not unreal.EditorLoadingAndSavingUtils.save_map(world, package):
        raise RuntimeError(f"Cannot save district: {package}")
    source_path(district).write_text(jadg_map.dumps(doc), encoding="utf-8")
    report["sourceCommitted"] = True
    report["mapSha256"] = hashlib.sha256(source_path(district).read_bytes()).hexdigest()
    (folder / "build.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    write_gallery()
    scene.log(f"District {district}: {len(doc['objects'])} objects; all {len(checks)} navigation targets connected")
    return report


def review_is_current(district: str, kind: str, proposal: Path) -> bool:
    """Never attach an older walk/capture proof to a newer district variant."""
    try:
        build = json.loads((REPORTS / district / "build.json").read_text(encoding="utf-8"))
        proof = json.loads((REPORTS / district / f"{kind}-review.json").read_text(encoding="utf-8"))
        hashes = {
            "manifestSha256": hashlib.sha256(manifest_path(district).read_bytes()).hexdigest(),
            "mapSha256": hashlib.sha256(proposal.read_bytes()).hexdigest(),
        }
        if not build.get("sourceCommitted") or hashlib.sha256(source_path(district).read_bytes()).hexdigest() != hashes["mapSha256"]:
            return False
        return all(build.get(key) == value and proof.get(key) == value for key, value in hashes.items())
    except (OSError, ValueError, TypeError, AttributeError):
        return False


def write_gallery() -> Path:
    folder = ROOT / "Saved/Captures/districts"
    folder.mkdir(parents=True, exist_ok=True)
    panels = []
    for district in DISTRICTS:
        proposal = REPORTS / district / "proposed-map.json"
        if not proposal.exists():
            continue
        doc = json.loads(proposal.read_text(encoding="utf-8"))
        facts = [f'{len(doc["objects"]):,} éléments de décor'.replace(',', ' ')]
        walk_path = REPORTS / district / "walk.json"
        if walk_path.exists() and review_is_current(district, "walk", proposal):
            walk = json.loads(walk_path.read_text(encoding="utf-8"))
            if walk.get("completed") and walk.get("return"):
                facts.append(f'Parcours réel : {walk["pointsReached"]}/{walk["pointsPlanned"]} étapes, aller-retour')
        measurement = folder / district / "mesure.json"
        captures_current = review_is_current(district, "capture", proposal)
        if measurement.exists() and captures_current:
            measured = json.loads(measurement.read_text(encoding="utf-8"))
            for sample in measured.get("measures", []):
                facts.append(f'{sample["hour"]} : {sample["fps"]:.1f} images/s en moyenne')
        facts_html = '<p>' + ' · '.join(html.escape(fact) for fact in facts) + '</p>'
        facts_html += '<p>Population animée avec apparences provisoires Manny et Quinn. Les mesures sont des séquences courtes en 1080p.</p>'
        visual_path = REPORTS / district / "visual-review.json"
        if visual_path.exists() and review_is_current(district, "visual", proposal):
            visual = json.loads(visual_path.read_text(encoding="utf-8"))
            reservations = ''.join(
                '<li>' + html.escape(item["observation"]) + '</li>'
                for item in visual.get("finishingReservations", [])
            )
            facts_html += (
                '<details><summary>Notes de revue visuelle</summary><p>'
                + str(visual["imagesActuallyViewedCount"])
                + ' captures finales inspectées. Appréciation artistique finale réservée à l’auteur.</p>'
                + ('<ul>' + reservations + '</ul>' if reservations else '')
                + '</details>'
            )
        cards = []
        if not captures_current:
            facts_html += '<p>Captures à renouveler pour cette variante.</p>'
        for shot in doc["shots"] if captures_current else []:
            images = "".join(f'<figure style="margin:0"><figcaption>{label}</figcaption><a href="{district}/{html.escape(shot["id"])}-{hour}.png"><img loading="lazy" src="{district}/{html.escape(shot["id"])}-{hour}.png" alt="{html.escape(shot["id"])} {label}"></a></figure>' for hour, label in (("1200", "Midi"), ("2200", "22 h")))
            cards.append(f'<article><h3>{html.escape(shot["id"].replace("-", " "))}</h3><div class="pair">{images}</div></article>')
        panels.append(f'<section id="{district}"><h2>{district.title()}</h2>{facts_html}{"".join(cards)}</section>')
    target = folder / "index.html"
    target.write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Arenarea et Martpart — revue Unreal</title><style>body{margin:0;background:#171b20;color:#e8e0d1;font:16px system-ui}main{max-width:1600px;margin:auto;padding:36px}h1{font-size:38px}h2{border-bottom:1px solid #82745c;padding-bottom:12px;margin-top:60px}h3{font-weight:500;text-transform:capitalize}.pair{display:grid;grid-template-columns:1fr 1fr;gap:12px}img{width:100%;border-radius:5px}a{color:#d5b475}article{margin:30px 0}p{color:#b6b8b9}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><main><h1>Arenarea & Martpart</h1><p>Quartiers complets — captures Unreal, midi à gauche et 22 h à droite. Cliquer pour ouvrir la pleine résolution.</p><p>Direction sculptée et peinte de l’Arena of Fate. Revue des quartiers complets : à apprécier par l’auteur.</p><nav><a href="#arenarea">Arenarea</a> · <a href="#martpart">Martpart</a></nav>' + ''.join(panels) + '</main></html>', encoding="utf-8")
    return target


def main() -> None:
    if "unreal" in sys.modules:
        import build_level as scene
        name = scene.scenery.command_line_option("JadgDistrict")
        for district in ([name] if name else DISTRICTS):
            build_editor(district)
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--prepare", action="store_true")
        parser.add_argument("--district", choices=DISTRICTS)
        parser.add_argument("--gallery", action="store_true")
        args = parser.parse_args()
        if args.prepare:
            for district in ([args.district] if args.district else DISTRICTS):
                _, evidence, _ = prepare(district)
                print(json.dumps({key: value for key, value in evidence.items() if key != "landmarks"}, ensure_ascii=False))
        if args.gallery:
            print(write_gallery())


if __name__ == "__main__":
    main()
