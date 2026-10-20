#!/usr/bin/env python3
"""Read-only Unreal evidence for the capital; never saves inspected pack assets."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/maps'))
import capital_landscape_layout as layout  # noqa: E402
import unreal  # noqa: E402


def value(obj, name):
    try:
        v = obj.get_editor_property(name)
        if isinstance(v, (str, int, float, bool)) or v is None:
            return v
        return str(v)
    except Exception as exc:
        return {'unavailable': str(exc)}


def main():
    after = 'JadgAuditAfter' in unreal.SystemLibrary.get_command_line()
    out = ROOT / ('Saved/Jadg/capital-landscape/audit-after' if after else 'Saved/Jadg/capital-landscape/audit')
    out.mkdir(parents=True, exist_ok=True)
    report = {'engine': unreal.SystemLibrary.get_engine_version(), 'assets': {}, 'errors': []}
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.search_all_assets(True)
    names = {layout.MATERIAL['source'], layout.MATERIAL['ported'], '/Game/Capitale/Ressources/MI_Capitale',
             '/Game/Capitale/Ressources/M_Eau', '/Game/Bibliotheque/Commun/Common/M_Scenery',
             '/Game/Bibliotheque/Commun/Common/M_SceneryMasked'}
    for root in ('/Game/Surfaces', '/Game/CapitalLandscape', '/Game/Bibliotheque/Materiaux/SenseiTerrain/MaterialFunctions',
                 '/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted'):
        names.update(str(d.package_name) for d in registry.get_assets_by_path(root, recursive=True))
    for name in sorted(names):
        asset = unreal.EditorAssetLibrary.load_asset(name)
        if asset is None:
            report['assets'][name] = {'missing': True}
            continue
        record = {'class': asset.get_class().get_name()}
        if isinstance(asset, unreal.Texture):
            record.update({p: value(asset, p) for p in ('srgb', 'compression_settings', 'flip_green_channel',
                         'virtual_texture_streaming', 'lod_group', 'max_texture_size')})
            if isinstance(asset,unreal.Texture2D):
                record['dimensions']=[asset.blueprint_get_size_x(),asset.blueprint_get_size_y()]
            import_data=asset.get_editor_property('asset_import_data')
            record['sourceFiles']=list(import_data.extract_filenames()) if import_data else []
        elif isinstance(asset, unreal.MaterialInterface):
            lib = unreal.MaterialEditingLibrary
            record['scalars'] = {str(p): (lib.get_material_instance_scalar_parameter_value(asset, p)
                    if isinstance(asset, unreal.MaterialInstance) else lib.get_material_default_scalar_parameter_value(asset, p))
                    for p in lib.get_scalar_parameter_names(asset)}
            record['textures'] = {str(p): str(lib.get_material_instance_texture_parameter_value(asset, p)
                    if isinstance(asset, unreal.MaterialInstance) else lib.get_material_default_texture_parameter_value(asset, p))
                    for p in lib.get_texture_parameter_names(asset)}
            record['switches'] = {str(p): (lib.get_material_instance_static_switch_parameter_value(asset,p)
                    if isinstance(asset,unreal.MaterialInstanceConstant) else lib.get_material_default_static_switch_parameter_value(asset,p))
                    for p in lib.get_static_switch_parameter_names(asset)}
            record['vectors'] = {str(p): str(lib.get_material_instance_vector_parameter_value(asset,p)
                    if isinstance(asset,unreal.MaterialInstance) else lib.get_material_default_vector_parameter_value(asset,p))
                    for p in lib.get_vector_parameter_names(asset)}
            record.update({p: value(asset, p) for p in ('parent', 'shading_model', 'displacement_scaling', 'enable_tessellation')})
        if isinstance(asset, (unreal.Material, unreal.MaterialFunction)):
            task = unreal.AssetExportTask()
            task.object = asset
            task.filename = str(out / (name.replace('/Game/', '').replace('/', '__') + '.copy'))
            task.automated = True
            task.prompt = False
            task.replace_identical = True
            record['graphExport'] = bool(unreal.Exporter.run_asset_export_task(task))
        report['assets'][name] = record
    try:
        unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/Levels/capital-landscape/ensemble')
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        report['usedMaterials']={}
        report['collisionMeshes']={}
        report['emptySlots']=[]
        for actor in actors:
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                mesh=component.static_mesh
                if mesh is None:continue
                report['collisionMeshes'][mesh.get_path_name()]={
                    'nanite':value(mesh.get_editor_property('nanite_settings'),'enabled'),
                    'navigationRelevant':value(component,'can_ever_affect_navigation'),
                    'fallbackTarget':value(mesh.get_editor_property('nanite_settings'),'fallback_target'),
                    'fallbackPercentTriangles':value(mesh.get_editor_property('nanite_settings'),'fallback_percent_triangles'),
                    'fallbackRelativeError':value(mesh.get_editor_property('nanite_settings'),'fallback_relative_error'),
                    'collision':value(mesh.get_editor_property('body_setup'),'collision_trace_flag'),
                    'complexCollisionMesh':value(mesh,'complex_collision_mesh')}
                for i in range(component.get_num_materials()):
                    mat=component.get_material(i)
                    if mat is None:report['emptySlots'].append(actor.get_actor_label()+':'+str(i))
                    else:report['usedMaterials'].setdefault(mat.get_path_name(),0);report['usedMaterials'][mat.get_path_name()]+=1
        report['world'] = [{'label': a.get_actor_label(), 'class': a.get_class().get_name(),
                            'location': str(a.get_actor_location()),
                            **({'nanite': value(a, 'enable_nanite'), 'material': value(a, 'landscape_material'),
                                'scale': str(a.get_actor_scale3d())} if isinstance(a, unreal.Landscape) else {})}
                           for a in actors]
    except Exception as exc:
        report['errors'].append(str(exc))
    report['runtimeConfiguration']={name:unreal.SystemLibrary.get_console_variable_int_value(name) for name in (
        'r.Nanite','r.Nanite.AllowTessellation','r.Nanite.Tessellation','r.DynamicGlobalIlluminationMethod',
        'r.ReflectionMethod','r.Shadow.Virtual.Enable','r.VirtualTextures','r.Substrate')}
    (out / ('engine-after.json' if after else 'engine-before.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    unreal.log('CAPITAL_AUDIT_COMPLETE')


if __name__ == '__main__':
    main()
