import unreal
import json
import sys
import hashlib
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/assetsGeneration')]
import import_scenery_unreal as scenery  # noqa: E402
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;AT=unreal.AssetToolsHelpers.get_asset_tools()
SRC=ROOT/'Source/Elements/Assets/Built/aof-extension-049-192';D='/Game/ArenaFateExtension'
doc=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'));report={'meshes':[],'materials':[],'maps':[]}
def save(a):
 if not E.save_loaded_asset(a,False):raise RuntimeError('Save '+a.get_path_name())
def copy(src,path):return E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path)
parent=E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Masters/M_AOF_Surface')
parent.set_editor_property('used_with_skeletal_mesh',True);parent.set_editor_property('used_with_clothing',True);M.recompile_material(parent);save(parent)
clothparent=copy(parent.get_path_name(),D+'/Materials/M_AOF_Cloth');clothparent.set_editor_property('two_sided',True);clothparent.set_editor_property('used_with_skeletal_mesh',True);clothparent.set_editor_property('used_with_clothing',True);M.recompile_material(clothparent);save(clothparent)
mats={k:E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_'+k) for k in ['stone_cream','marble_white','wood','dark_metal','bronze','mortar','dust','stone_worn']}
texdoc=json.loads((ROOT/'Source/Elements/Assets/Library/aof-pbr-extension/manifest.json').read_text())
for key,row in texdoc['materials'].items():
 mi=copy(mats['mortar'].get_path_name(),D+'/Materials/MI_AOF_'+key);M.set_material_instance_parent(mi,clothparent if key in ('linen','sacking') else parent)
 for role,f in row['files'].items():
  path=D+'/Textures/'+key+'/T_'+key+'_'+role;file=ROOT/'Source/Elements/Assets/Library/aof-pbr-extension'/f['file']
  t=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_image(file.read_bytes(),'png',path,role)
  t.set_editor_property('srgb',role=='baseColor');t.set_editor_property('flip_green_channel',False);t.set_editor_property('max_texture_size',4096)
  t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else unreal.TextureCompressionSettings.TC_DISPLACEMENTMAP if role=='height' else unreal.TextureCompressionSettings.TC_BC7);save(t)
  param={'baseColor':'Albedo Color','normal':'Normal','roughness':'Roughness','height':'Height','ao':'Ambient Occlusion'}[role]
  M.set_material_instance_texture_parameter_value(mi,param+' A',t)
 for n,v in [('Use Metallic? A',False),('Use AO? A','ao' in row['files']),('Second Material Layer?',False),('Third Material Layer?',False)]:M.set_material_instance_static_switch_parameter_value(mi,n,v)
 size=row['tileMetres'];M.set_material_instance_vector_parameter_value(mi,'Tiling A',unreal.LinearColor(2/size[0],2/size[1],0,0));M.update_material_instance(mi);save(mi);mats[key]=mi
 report['materials'].append({'name':key,'source':row,'instance':mi.get_path_name()})
burgundy=copy(mats['linen'].get_path_name(),D+'/Materials/MI_AOF_LinenBurgundy');M.set_material_instance_vector_parameter_value(burgundy,'Albedo Tint A',unreal.LinearColor(.34,.018,.035,1));M.update_material_instance(burgundy);save(burgundy);mats['burgundy']=burgundy;mats['sand']=mats['dust']
pot=copy(mats['mortar'].get_path_name(),D+'/Materials/MI_AOF_UnglazedClay');M.set_material_instance_vector_parameter_value(pot,'Albedo Tint A',unreal.LinearColor(.65,.22,.09,1));M.set_material_instance_scalar_parameter_value(pot,'Roughness Strength A',.9);M.update_material_instance(pot);save(pot)
def assign(mesh,i,skeletal=False):
 slots=mesh.get_editor_property('materials' if skeletal else 'static_materials')
 for j,s in enumerate(slots):
  key=str(s.material_slot_name);key=next((k for k in mats if key==k or key.startswith(k+'.') or key.startswith(k+'_')),None)
  if key is None:raise RuntimeError('Unknown material '+str(s.material_slot_name))
  mat=mats[key]
  if i in (91,92,165) and key=='mortar':mat=mats['sacking']
  if i==162 and key=='burgundy':mat=pot
  if skeletal:s.material_interface=mat;slots[j]=s
  else:mesh.set_material(j,mat)
 if skeletal:mesh.set_editor_property('materials',slots)
 save(mesh)
def import_skin(row):
 i=row['catalogueId'];name=f'SK_AOF_{i:03d}';path=D+'/Rigged/'+name
 digest=hashlib.sha256((SRC/row.get('skeletalFile',row['file'])).read_bytes()).hexdigest()
 if E.does_asset_exist(path):
  existing=E.load_asset(path)
  if E.get_metadata_tag(existing,'AOFSkelHash')==digest:return existing
  E.delete_asset(path)
 task=unreal.AssetImportTask();task.set_editor_property('filename',str(SRC/row.get('skeletalFile',row['file'])));task.set_editor_property('destination_path',D+'/Import/'+name);task.set_editor_property('automated',True);task.set_editor_property('replace_existing',True);task.set_editor_property('save',True)
 AT.import_asset_tasks([task])
 found=[E.load_asset(p) for p in E.list_assets(D+'/Import/'+name,True)];found=[x for x in found if isinstance(x,unreal.SkeletalMesh)]
 if len(found)!=1:raise RuntimeError('Expected one skeletal mesh '+name+' got '+str(len(found)))
 mesh=E.duplicate_asset(found[0].get_path_name(),path);E.set_metadata_tag(mesh,'AOFSkelHash',digest);save(mesh);return mesh
meshes={}
for row in doc['meshes']:
 i=row['catalogueId'];record=dict(row)
 if row.get('referenceAssets'):
  mesh=E.load_asset(row['referenceAssets'][0]);meshes[i]=mesh;record['nativeAssets']=row['referenceAssets'];report['meshes'].append(record);continue
 if row['physics']=='cloth' or 'skeletalFile' in row:
  mesh=import_skin(row);assign(mesh,i,True)
  pa=unreal.JadgArenaPhysicsBuild.build_bodies(mesh,D+f'/Physics/PA_AOF_{i:03d}',row.get('anchorRoot',True),row['physics'],unreal.Vector(1,0,0) if i in (48,94,114,124,129,132,137,188,189) else unreal.Vector(0,1,0) if i in (93,127) else unreal.Vector(0,0,1))
  if not pa:raise RuntimeError('Physics asset '+str(i))
  save(pa);save(mesh)
  if row['physics']=='cloth':
   result=unreal.JadgArenaPhysicsBuild.build_cloth(mesh,row['maxDistanceCm'],True);record['clothResult']=result
   if result.startswith('ERROR'):raise RuntimeError(result)
   save(mesh)
  record['physicsAsset']=pa.get_path_name()
 else:
  name=row['id'];path=D+('/RefinedMeshes/' if i in (105,139,140,141,171,181,183) else '/Meshes/')+name
  mesh=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_glb(SRC/row['file'],D+'/Import',D+'/Import/'+name,path)
  scenery.finish(mesh);assign(mesh,i)
  # Simple hulls are required by rigid-body simulation; complex triangles are not a dynamic body.
  if row['physics']=='rigid':
   if not unreal.JadgArenaPhysicsBuild.build_rigid_collision(mesh):raise RuntimeError('Rigid collision '+str(i))
   body=mesh.get_editor_property('body_setup');body.set_editor_property('collision_trace_flag',unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX);save(mesh)
 meshes[i]=mesh;record['nativeAsset']=mesh.get_path_name();report['meshes'].append(record)
 print('IMPORTED_AOF',i,row['physics'],flush=True)
reportdir=ROOT/'Saved/Jadg/aof-extension';reportdir.mkdir(parents=True,exist_ok=True);(reportdir/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('AOF_EXTENSION_IMPORT_COMPLETE')
