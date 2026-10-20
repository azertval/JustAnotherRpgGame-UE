"""Material-only revision: preserve landscape height, paint, actors and road meshes."""
import unreal as u
import json
import sys
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();sys.path[:0]=[str(P/'scripts/maps'),str(P/'scripts/assetsGeneration')]
import import_scenery_unreal as scenery  # noqa: E402
E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
D='/Game/Capitale/Ressources/PBR4K';S=P/'Source/Elements/Assets/Library/aof-pbr-landscape'
doc=json.loads((S/'manifest.json').read_text());report={'textures':[],'materials':[],'overrides':[],'geometryModified':False}
def save(a):
 if not E.save_loaded_asset(a,False):raise RuntimeError(a.get_path_name())
def backup(a):
 path=D+'/Before/'+a.get_path_name().split('.')[0].removeprefix('/Game/Capitale/Ressources/').replace('/','_')
 if not E.does_asset_exist(path):
  b=E.duplicate_asset(a.get_path_name(),path)
  if not b:raise RuntimeError('backup '+path)
  save(b)
 return path
def copy(src,path):
 a=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path)
 if not a:raise RuntimeError(path)
 return a
tx={}
for key,row in doc['materials'].items():
 tx[key]={}
 for role,f in row['files'].items():
  path=D+'/Textures/'+key+'/T_'+key+'_'+role
  t=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_image((S/f['file']).read_bytes(),'png',path,role)
  t.set_editor_property('srgb',role=='baseColor');t.set_editor_property('flip_green_channel',False);t.set_editor_property('max_texture_size',4096)
  t.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DISPLACEMENTMAP if role=='height' else u.TextureCompressionSettings.TC_BC7)
  save(t);tx[key][role]=t;report['textures'].append({'asset':t.get_path_name(),'role':role,'source':f})
 print('PBR_IMPORTED',key,flush=True)
def scalar(a,n,v):
 if n in {str(x) for x in M.get_scalar_parameter_names(a)}:M.set_material_instance_scalar_parameter_value(a,n,v)
def switch(a,n,v):
 if n in {str(x) for x in M.get_static_switch_parameter_names(a)}:M.set_material_instance_static_switch_parameter_value(a,n,v)
def vector(a,n,v):
 if n in {str(x) for x in M.get_vector_parameter_names(a)}:M.set_material_instance_vector_parameter_value(a,n,u.LinearColor(*v))
def texture(a,n,t):
 if n in {str(x) for x in M.get_texture_parameter_names(a)}:M.set_material_instance_texture_parameter_value(a,n,t)
def record(a,before=None):
 M.update_material_instance(a);save(a);report['materials'].append({'asset':a.get_path_name(),'before':before})
# Five-layer Sensei terrain used by ensemble and its horizon.
for name in ['MI_Capitale','MI_Horizon']:
 a=E.load_asset('/Game/Capitale/Ressources/'+name)
 if not a:continue
 before=backup(a)
 for slot,key in zip('ABCDE',['grass','rock','forest','soil','sand']):
  for role,param in [('baseColor','Albedo Color'),('normal','Normal'),('roughness','Roughness'),('height','Height'),('height','Height Blend'),('orm','MaskORM'),('ao','Ambient Occlusion')]:texture(a,param+' '+slot,tx[key][role])
  switch(a,'Use Mask? '+slot,True);switch(a,'Use AO? '+slot,True);switch(a,'Use Metallic? '+slot,False)
  scalar(a,'Normal Strength '+slot,1.);scalar(a,'Roughness Strength '+slot,1.);scalar(a,'Displacement Amount '+slot,0.)
  scalar(a,'Size '+slot,1/doc['materials'][key]['tileMetres'][0]);vector(a,'Albedo Tint '+slot,[1,1,1,1])
 record(a,before)
# Native seven-layer district material. Preserve supplied 8K grass variants.
# Terre's existing graph reads R of its third sampler, so supply roughness there.
for area in ['Metropole','Arenarea']:
 a=E.load_asset('/Game/Capitale/Ressources/'+area+'/Materials/MI_Surfaces')
 if not a:continue
 before=backup(a)
 for layer,key in [('Terre','soil'),('Sable','sand'),('Roche','rock'),('Pavage','paving')]:
  for role,param in [('baseColor','BC'),('normal','N'),('roughness' if layer=='Terre' else 'orm','ORM')]:texture(a,layer+'_'+param,tx[key][role])
  scalar(a,layer+'_TailleCm',doc['materials'][key]['tileMetres'][0]*100);scalar(a,layer+'_Rugosite',1.);vector(a,layer+'_Teinte',[1,1,1,1])
 record(a,before)
# AOF Sensei instances also provide the swatches and the actual road materials.
parent=E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Masters/M_AOF_Surface')
for key in tx:
 a=copy('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_mortar',D+'/Materials/MI_'+key)
 M.set_material_instance_parent(a,parent)
 for role,param in [('baseColor','Albedo Color'),('normal','Normal'),('roughness','Roughness'),('height','Height'),('ao','Ambient Occlusion'),('orm','MaskORM')]:texture(a,param+' A',tx[key][role])
 switch(a,'Use Mask? A',False);switch(a,'Use AO? A',True);switch(a,'Use Metallic? A',False);switch(a,'Second Material Layer?',False);switch(a,'Third Material Layer?',False)
 vector(a,'Tiling A',[2/doc['materials'][key]['tileMetres'][0],2/doc['materials'][key]['tileMetres'][1],0,0]);vector(a,'Albedo Tint A',[1,1,1,1]);scalar(a,'Normal Strength A',1.);record(a)
for family in ['soil','paving','wet_soil']:
 for variant in range(3):
  a=E.load_asset('/Game/Capitale/Ressources/Surfaces/MI_'+family+'_'+str(variant))
  if not a:continue
  before=backup(a);key='paving_worn' if family=='paving' and variant==2 else family
  # Clear old parameter overrides: names belong to the old scenery parent.
  M.clear_all_material_instance_parameters(a)
  M.set_material_instance_parent(a,E.load_asset(D+'/Materials/MI_'+key))
  vector(a,'Albedo Tint A',[[1,1,1,1],[.94,.97,1,1],[1.02,.99,.94,1]][variant]);record(a,before)
# Border/retaining components in ensemble use the same PBR stone as the arena.
level=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
level.load_level('/Game/Maps/Levels/capital-landscape/ensemble')
for a in actors.get_all_level_actors():
 if not any(s in str(a.get_folder_path()).lower() for s in ['road-retaining','monument-foundations']):continue
 for c in a.get_components_by_class(u.StaticMeshComponent):
  for i,old in enumerate(c.get_materials()):
   if old and 'stone' in old.get_name():
    c.set_material(i,E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_stone_worn'));report['overrides'].append({'actor':a.get_actor_label(),'slot':i,'before':old.get_path_name()})
if report['overrides']:level.save_current_level()
out=P/'Saved/Jadg/capital-pbr4k';out.mkdir(exist_ok=True,parents=True);(out/'revision.json').write_text(json.dumps(report,indent=2))
print('CAPITAL_PBR_REVISION_COMPLETE',len(report['textures']),len(report['materials']),len(report['overrides']),flush=True)
