"""Read-only comparison of local packs in UE 5.8; run once per source project."""
import json
from pathlib import Path
import unreal

OUT=Path(__file__).resolve().parents[2]/'Saved/Jadg/capital-landscape/audit/packs'
OUT.mkdir(parents=True,exist_ok=True)
project=Path(unreal.Paths.project_dir()).resolve()
registry=unreal.AssetRegistryHelpers.get_asset_registry()
registry.search_all_assets(True)
report={'project':str(project),'engine':unreal.SystemLibrary.get_engine_version(),'materials':{},'errors':[]}
select=('M_SenseiTerrain','M_BlendMaster','M_Landscape','M_CastleMasterBlend','M_HouseWallBase','M_Landforms_Master',
        'Water','Foliage','Grass')
for data in registry.get_assets_by_path('/Game',recursive=True):
    name=str(data.asset_name)
    if 'Material' not in str(data.asset_class_path) or (project.name not in ('IntroUnrealProject','tuto') and not any(s.lower() in name.lower() for s in select)):
        continue
    try:
        asset=data.get_asset()
        if not isinstance(asset,unreal.MaterialInterface): continue
        lib=unreal.MaterialEditingLibrary
        row={'class':asset.get_class().get_name(),
             'scalars':[str(p) for p in lib.get_scalar_parameter_names(asset)],
             'textures':[str(p) for p in lib.get_texture_parameter_names(asset)],
             'switches':[str(p) for p in lib.get_static_switch_parameter_names(asset)],
             'dependencies':[str(p) for p in registry.get_dependencies(data.package_name,unreal.AssetRegistryDependencyOptions())]}
        if isinstance(asset,unreal.Material):
            task=unreal.AssetExportTask();task.object=asset
            task.filename=str(OUT/(project.name+'__'+name+'.copy'))
            task.automated=True;task.prompt=False;task.replace_identical=True
            row['graphExport']=bool(unreal.Exporter.run_asset_export_task(task))
        report['materials'][str(data.package_name)]=row
    except Exception as exc: report['errors'].append(name+': '+str(exc))
(OUT/(project.name+'.json')).write_text(json.dumps(report,indent=2),encoding='utf8')
unreal.log('CAPITAL_PACK_AUDIT_COMPLETE')
