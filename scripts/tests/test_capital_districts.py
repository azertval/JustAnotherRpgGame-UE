# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Quest and transition preservation when rebuilding districts at a new scale."""
from copy import deepcopy
import json
import hashlib
import sys
from types import SimpleNamespace

import pytest

import build_capital_districts as districts
import jadg_map


def test_roof_and_footings_follow_their_shell_cut_without_losing_other_tags():
    shell = SimpleNamespace(tags=["JadgWitnessOccluder"])
    roof = SimpleNamespace(tags=["JadgWitnessOccluder", "ExistingRoofTag"])
    footing = SimpleNamespace(tags=[])
    placed = [{"id": "roof", "actor": roof, "supportsObject": "shell"},
              {"id": "footing", "actor": footing, "supportsObject": ["shell"]},
              {"id": "shell", "actor": shell}]
    assert districts.tag_occlusion_supports(placed) == 2
    assert districts.tag_occlusion_supports(placed) == 2
    assert shell.tags == ["JadgWitnessOccluder", "JadgWitnessSurface:shell"]
    assert roof.tags == ["JadgWitnessOccluder", "ExistingRoofTag", "JadgWitnessSupport:shell"]
    assert footing.tags == ["JadgWitnessSupport:shell"]


@pytest.mark.parametrize("support", ["absent", "roof", 42])
def test_invalid_cutaway_dependency_is_rejected_before_tagging(support):
    shell, roof = SimpleNamespace(tags=[]), SimpleNamespace(tags=[])
    placed = [{"id": "shell", "actor": shell},
              {"id": "roof", "actor": roof, "supportsObject": support}]
    with pytest.raises(RuntimeError, match="occlusion support"):
        districts.tag_occlusion_supports(placed)
    assert shell.tags == roof.tags == []


@pytest.fixture
def original():
    return json.loads(districts.source_path("arenarea").read_text(encoding="utf-8"))


def manifest_for(original):
    ids = [entity["id"] for entity in original["entities"]]
    return {"meshes": [], "objects": [], "metadata": {
        "area": [-300, -200, 300, 200], "levels": [{"name": "rez", "z": 0.0}],
        "start": [-12, 22, 0], "shots": [],
        "entityPositions": {identifier: [-100 + 3 * i, 20, 0] for i, identifier in enumerate(ids)},
    }}


def test_new_extent_keeps_live_quest_changes_and_is_idempotent(original):
    guard = next(entity for entity in original["entities"] if entity["id"] == "e5")
    guard["dialogue"] = "garde-modifie-par-auteur"
    guard["presenceValue"] = "nouvelle-etape"
    manifest = manifest_for(original)
    doc, evidence = districts.make_document("arenarea", manifest, original)
    again, _ = districts.make_document("arenarea", manifest, doc)
    assert again == doc
    assert evidence["gameplayPreserved"]
    assert districts.gameplay_contract(doc) == districts.gameplay_contract(original)
    for entity in doc["entities"]:
        if entity["type"] == "zone":
            continue
        point = jadg_map.cell_centre(entity["x"], entity["y"], doc["origin"])
        expected = manifest["metadata"]["entityPositions"][entity["id"]]
        assert abs(point[0] - expected[0]) <= .75
        assert abs(point[1] - expected[1]) <= .75
    zone = next(entity for entity in doc["entities"] if entity["id"] == "e7")
    expected = manifest["metadata"]["entityPositions"]["e7"]
    for axis in range(3):
        assert zone["volume"]["min"][axis] < expected[axis] < zone["volume"]["max"][axis]


def test_guard_trigger_cells_match_the_visible_zone(original):
    manifest = manifest_for(original)
    manifest["metadata"]["entityPositions"]["e7"] = [-10, 30, 0]
    doc, _ = districts.make_document("arenarea", manifest, original)
    zone = next(entity for entity in doc["entities"] if entity["id"] == "e7")
    for dy in range(-1, zone["height"] + 1):
        for dx in range(-1, zone["width"] + 1):
            x, y = zone["x"] + dx, zone["y"] + dy
            point = jadg_map.cell_centre(x, y, doc["origin"])
            core_triggers = 0 <= dx < zone["width"] and 0 <= dy < zone["height"]
            within_volume = all(zone["volume"]["min"][axis] <= point[axis] < zone["volume"]["max"][axis] for axis in (0, 1))
            assert core_triggers == within_volume


def test_forgetting_an_existing_sealed_exit_stops_reconstruction(original):
    manifest = manifest_for(original)
    del manifest["metadata"]["entityPositions"]["e8"]
    with pytest.raises(RuntimeError, match="Unmapped existing entity"):
        districts.make_document("arenarea", manifest, original)


def test_contract_detects_quest_or_portal_change_even_after_repositioning(original):
    changed = deepcopy(original)
    portal = next(entity for entity in changed["entities"] if entity["type"] == "portal")
    portal["arrival"] = "wrong-arrival"
    assert districts.gameplay_contract(changed) != districts.gameplay_contract(original)
    changed = deepcopy(original)
    changed["entities"][0]["x"] += 10
    assert districts.gameplay_contract(changed) == districts.gameplay_contract(original)


def test_invalid_negative_grid_position_is_rejected(original):
    manifest = manifest_for(original)
    manifest["metadata"]["entityPositions"]["e1"] = [-1000, -1000, 0]
    with pytest.raises(RuntimeError, match="hors|schéma"):
        districts.make_document("arenarea", manifest, original)


def physical_manifest():
    return {"meshes": [
        {"id": "floor", "file": "floor.glb", "triangles": 1000000, "collisionMesh": "floor-collision"},
        {"id": "floor-collision", "file": "floor-collision.glb", "triangles": 120, "role": "collision-proxy"},
    ], "objects": [
        {"id": "floor-1", "meshId": "floor"},
        {"id": "floor-2", "mesh": "Built/arenarea-district/floor.glb", "scale": 2},
        {"id": "background", "meshId": "floor", "collision": False},
        {"id": "arena", "mesh": "Built/arena-fate-modern/afm-ring-ground.glb"},
    ]}


def test_physical_plan_counts_repetition_without_placing_proxies_or_background():
    manifest = physical_manifest()
    before = deepcopy(manifest)
    plan = districts.collision_plan("arenarea", manifest)
    assert len(plan) == 1
    assert plan[0]["instances"] == 2
    assert plan[0]["collisionSource"] == "Built/arenarea-district/floor-collision.glb"
    assert plan[0]["visualSourceTriangles"] == 1000000
    assert manifest == before


def test_missing_physical_coverage_stops_arenarea_before_asset_loading():
    manifest = physical_manifest()
    del manifest["meshes"][0]["collisionMesh"]
    with pytest.raises(RuntimeError, match="Missing architectural collision"):
        districts.collision_plan("arenarea", manifest)
    manifest["objects"] = [{"id": "floor-1", "meshId": "floor"}]
    assert districts.collision_plan("martpart", manifest) == []


@pytest.mark.parametrize("mutation", ["missing", "visual", "self"])
def test_invalid_collision_reference_is_rejected(mutation):
    manifest = physical_manifest()
    if mutation == "missing":
        manifest["meshes"][0]["collisionMesh"] = "absent"
    elif mutation == "visual":
        manifest["meshes"][1].pop("role")
    else:
        manifest["meshes"][0]["collisionMesh"] = "floor"
    with pytest.raises(RuntimeError, match="Invalid collisionMesh"):
        districts.collision_plan("arenarea", manifest)


def test_proxy_cannot_be_placed_even_with_collision_disabled():
    manifest = physical_manifest()
    manifest["objects"].append({"id": "accidental-visible-proxy", "meshId": "floor-collision", "collision": False})
    with pytest.raises(RuntimeError, match="cannot be placed"):
        districts.collision_plan("arenarea", manifest)


def test_duplicate_mesh_identity_cannot_replace_a_visual_with_a_proxy():
    manifest = physical_manifest()
    manifest["meshes"].append(deepcopy(manifest["meshes"][0]))
    with pytest.raises(RuntimeError, match="Duplicate"):
        districts.collision_plan("arenarea", manifest)


class MeshSettings(SimpleNamespace):
    def copy(self):
        return deepcopy(self)


class MeshProperties:
    def __init__(self, triangles):
        self.properties = {
            "nanite_settings": MeshSettings(enabled=True, fallback_target="percent", fallback_percent_triangles=1,
                                             fallback_relative_error=0),
            "allow_cpu_access": False, "body_setup": self,
            "collision_trace_flag": "default", "complex_collision_mesh": None,
        }
        self.triangles = triangles
        self.notifications = 0

    def get_editor_property(self, name):
        return self.properties[name]

    def set_editor_property(self, name, value):
        self.properties[name] = value
        if name == "complex_collision_mesh":
            self.notifications += 1

    def get_num_triangles(self, lod):
        assert lod == 0
        return self.triangles

    def get_path_name(self):
        return "/Game/Test/Proxy"


@pytest.mark.parametrize("pairs", [1, 16, 17])
def test_proxy_install_recooks_existing_reference_and_preserves_visual_settings(monkeypatch, pairs):
    visual, proxy = MeshProperties(1000000), MeshProperties(120)
    saved, loaded, collected = [], [], []

    def collect():
        assert not library.static
        collected.append(len(saved))

    fake = SimpleNamespace(CollisionTraceFlag=SimpleNamespace(CTF_USE_COMPLEX_AS_SIMPLE="complex"),
                           EditorAssetLibrary=SimpleNamespace(save_loaded_asset=lambda mesh: saved.append(mesh) or True),
                           collect_garbage=collect)
    monkeypatch.setitem(sys.modules, "unreal", fake)
    plan = districts.collision_plan("arenarea", physical_manifest()) * pairs
    monkeypatch.setattr(districts, "collision_plan", lambda district, manifest: plan)

    def load(source, collision_proxy=False):
        assert collision_proxy == ("-collision" in source)
        loaded.append(source)
        mesh = proxy if "-collision" in source else visual
        library.static[source] = mesh
        return mesh

    before = deepcopy(visual.properties["nanite_settings"])
    library = SimpleNamespace(static_mesh=load, static={})
    for _ in range(2):
        report = districts.install_architectural_collision(library, "arenarea", physical_manifest())
        assert report["physicalTrianglesTimesInstances"] == 240 * pairs
        assert report["estimatedRecastRawCacheBytes"] == 240 * pairs * 84
        assert report["authoredVisualTrianglesTimesInstances"] == 2000000 * pairs
    assert visual.notifications == 2 * pairs  # Same path can hold a newly reimported proxy.
    assert visual.properties["nanite_settings"] == before
    assert visual.properties["complex_collision_mesh"] is proxy
    assert visual.properties["collision_trace_flag"] == "complex"
    assert not proxy.properties["nanite_settings"].enabled
    assert proxy.properties["allow_cpu_access"]
    assert proxy.properties["collision_trace_flag"] == "complex"
    assert saved == [proxy, visual] * (2 * pairs)
    checkpoints = [index for index in range(1, pairs + 1) if index % 16 == 0 or index == pairs]
    assert collected == [2 * (offset + index) for offset in (0, pairs) for index in checkpoints]
    assert loaded[0].endswith("floor-collision.glb")


def test_proxy_install_rejects_imported_geometry_mismatch(monkeypatch):
    visual, proxy = MeshProperties(1000000), MeshProperties(2)
    fake = SimpleNamespace(CollisionTraceFlag=SimpleNamespace(CTF_USE_COMPLEX_AS_SIMPLE="complex"),
                           EditorAssetLibrary=SimpleNamespace(save_loaded_asset=lambda mesh: True))
    monkeypatch.setitem(sys.modules, "unreal", fake)
    library = SimpleNamespace(static_mesh=lambda source, collision_proxy=False: proxy if "-collision" in source else visual)
    with pytest.raises(RuntimeError, match="differs from authored"):
        districts.install_architectural_collision(library, "arenarea", physical_manifest())
    assert visual.notifications == 0
    assert visual.properties["complex_collision_mesh"] is None


@pytest.mark.parametrize("changed", [None, "manifest", "proposal", "canonical", "proof", "uncommitted"])
def test_gallery_requires_proof_of_the_actual_built_variant(tmp_path, monkeypatch, changed):
    monkeypatch.setattr(districts, "ROOT", tmp_path)
    monkeypatch.setattr(districts, "ASSETS", tmp_path / "assets")
    monkeypatch.setattr(districts, "REPORTS", tmp_path / "reports")
    manifest = districts.manifest_path("arenarea")
    canonical = districts.source_path("arenarea")
    proposal = districts.REPORTS / "arenarea/proposed-map.json"
    for path, content in ((manifest, '{"version":1}'), (canonical, '{"objects":[]}'), (proposal, '{"objects":[]}')):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    hashes = {"manifestSha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
              "mapSha256": hashlib.sha256(proposal.read_bytes()).hexdigest()}
    build = {**hashes, "sourceCommitted": changed != "uncommitted"}
    (proposal.parent / "build.json").write_text(json.dumps(build), encoding="utf-8")
    proof = {**hashes, "completedUtc": "2026-10-10T19:00:00Z"}
    if changed == "proof":
        proof["mapSha256"] = "older-map"
    (proposal.parent / "capture-review.json").write_text(json.dumps(proof), encoding="utf-8")
    changed_path = {"manifest": manifest, "proposal": proposal, "canonical": canonical}.get(changed)
    if changed_path:
        changed_path.write_text('{"changed":true}', encoding="utf-8")
    assert districts.review_is_current("arenarea", "capture", proposal) is (changed is None)
    assert not districts.review_is_current("arenarea", "walk", proposal)
