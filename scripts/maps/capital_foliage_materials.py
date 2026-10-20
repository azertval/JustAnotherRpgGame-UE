#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Compile supplied foliage for instancing/Nanite through owned material copies."""

from pathlib import Path
import json
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
CONTENT = "/Game/Capitale/Ressources/Arenarea"


def prepare():
    al, ml = u.EditorAssetLibrary, u.MaterialEditingLibrary
    path = CONTENT+"/Materials/M_Fab_Foliage"
    parent = al.load_asset(path) if al.does_asset_exist(path) else al.duplicate_asset(
        "/Game/Bibliotheque/Scans/Materials/Standard/M_MS_Foliage", path)
    parent.set_editor_property("used_with_instanced_static_meshes", True)
    parent.set_editor_property("used_with_nanite", True)
    ml.recompile_material(parent)
    al.save_loaded_asset(parent, only_if_is_dirty=False)
    inventory = json.loads((ROOT/"Saved/Jadg/arenarea-landscape/fab-inventory.json").read_text())
    provenance = json.loads((ROOT/"Source/Elements/Assets/Library/arenarea-fab-sources.json").read_text(encoding="utf8"))
    supplied = {path for item in provenance["items"] if item["role"] == "foliage" for path in item["sources"]}
    inventory = [row for row in inventory if row["path"] in supplied]
    materials = {}
    for row in inventory:
        if row["class"] != "MaterialInstanceConstant" or "/Plants/" not in row["path"]:
            continue
        code = row["path"].rsplit("/", 1)[1][3:]
        target = CONTENT+"/Materials/MI_Fab_"+code
        mi = al.load_asset(target) if al.does_asset_exist(target) else al.duplicate_asset(row["path"], target)
        ml.set_material_instance_parent(mi, parent)
        ml.update_material_instance(mi)
        al.set_metadata_tag(mi, "SourceAsset", row["path"])
        al.save_loaded_asset(mi, only_if_is_dirty=False)
        materials[code] = mi
    for row in inventory:
        if row["class"] != "StaticMesh" or "/Plants/" not in row["path"]:
            continue
        name = row["path"].rsplit("/", 1)[1]
        target = CONTENT+"/Foliage/FT_"+name
        if not al.does_asset_exist(target):
            continue
        ft = al.load_asset(target)
        code = next(c for c in materials if c in name)
        ft.set_editor_property("override_materials", [materials[code]])
        ft.set_editor_property("nanite_override_materials", [materials[code]])
        al.save_loaded_asset(ft, only_if_is_dirty=False)
    return materials


def repair_saved_arenarea():
    materials = prepare()
    path = "/Game/Maps/Levels/capital-landscape/arenarea"
    world = u.EditorLoadingAndSavingUtils.load_map(path)
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, u.InstancedFoliageActor):
            continue
        for component in actor.get_components_by_class(u.InstancedStaticMeshComponent):
            name = component.static_mesh.get_name()
            code = next(c for c in materials if c in name)
            component.set_material(0, materials[code])
    u.EditorLoadingAndSavingUtils.save_map(world, path)
    print("CAPITAL_FOLIAGE_MATERIALS_OK")


if __name__ == "__main__":
    repair_saved_arenarea()
