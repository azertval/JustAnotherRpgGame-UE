import unreal as u
import json
import sys
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();sys.path.insert(0,str(P/'scripts/assetsGeneration'));import import_scenery_unreal as scenery  # noqa: E402
E=u.EditorAssetLibrary;R=u.AssetRegistryHelpers.get_asset_registry();R.scan_paths_synchronous(['/Interchange/Pipelines'],True,True)
p='/Game/Capitale/Ressources/Eau/P_ImportEau'
pipeline=E.load_asset(p) if E.does_asset_exist(p) else E.duplicate_asset('/Interchange/Pipelines/DefaultGLTFAssetsPipeline.DefaultGLTFAssetsPipeline',p)
pipeline.get_editor_property('mesh_pipeline').set_editor_property('build_nanite',False);pipeline.get_editor_property('mesh_pipeline').set_editor_property('distance_field_resolution_scale',0.)
pipeline.get_editor_property('material_pipeline').set_editor_property('import_materials',False);E.save_loaded_asset(pipeline,False)
options=u.InterchangePipelineStackOverride();options.set_editor_property('override_pipelines',[u.SoftObjectPath(pipeline.get_path_name()),u.SoftObjectPath('/Interchange/Pipelines/DefaultGLTFPipeline.DefaultGLTFPipeline')]);scenery._COLLISION_IMPORT_OPTIONS=options
mi=E.load_asset('/Game/Capitale/Ressources/Eau/MI_Eau_Capitale');folder='/Game/Capitale/Ressources/Metropole/Water'
rows=json.loads((P/'Source/Elements/Assets/Built/capitale-eau/manifest.json').read_text())['meshes']
for r in rows:
 name=r['id'];mesh=scenery.import_glb(P/'Source/Elements/Assets/Built/capitale-eau'/(name+'.glb'),folder,folder+'/'+name,folder+'/'+name+'/StaticMeshes/SM_'+name,collision_proxy=True)
 ns=mesh.get_editor_property('nanite_settings');ns.enabled=False;mesh.set_editor_property('nanite_settings',ns);mesh.set_material(0,mi);E.save_loaded_asset(mesh,False)
 assert mesh.get_material(0)==mi
 print('WATER_SHORE_REPAIRED',name,mesh.get_num_triangles(0),flush=True)
print('WATER_SHORE_REPAIR_COMPLETE',len(rows),flush=True)
