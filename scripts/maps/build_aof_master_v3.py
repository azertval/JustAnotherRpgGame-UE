"""Install original CC0 4K maps and production presets on supplied Sensei masters."""
import unreal
import json
import sys
import hashlib
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/assetsGeneration')]
import import_scenery_unreal as scenery  # noqa: E402
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;AT=unreal.AssetToolsHelpers.get_asset_tools()
DEST='/Game/ArenaFateMaterials';SRC=ROOT/'Source/Elements/Assets/Library/aof-pbr-v3'
doc=json.loads((SRC/'manifest.json').read_text(encoding='utf-8'));report={'version':3,'textures':[],'instances':[],'masters':[],'sources':doc['materials']}
def save(a):
 if not E.save_loaded_asset(a,False):raise RuntimeError('Save failed '+a.get_path_name())
def duplicate(src,path):
 a=E.load_asset(path) if E.does_asset_exist(path) else E.duplicate_asset(src,path)
 if not a:raise RuntimeError('Missing '+path)
 return a
parents={}
for key,suffix in [('surface',''),('nanite','_Nanite')]:
 p=duplicate('/Game/Bibliotheque/Materiaux/Sensei/Materials/M_BlendMaster'+suffix,DEST+'/Masters/M_AOF_Surface'+suffix)
 p.set_editor_property('used_with_instanced_static_meshes',True);p.set_editor_property('used_with_nanite',True);save(p)
 parents[key]=p;report['masters'].append({'path':p.get_path_name(),'source':'/Game/Bibliotheque/Materiaux/Sensei/Materials/M_BlendMaster'+suffix,'parameters':{k:[str(n) for n in getattr(M,'get_'+k+'_parameter_names')(p)] for k in ['scalar','vector','texture','static_switch']}})
tx={}
for key,row in doc['materials'].items():
 tx[key]={}
 # Import the true individual physical maps as well as available source ORM packs.
 for role,item in row['files'].items():
  file=SRC/item['file'];path=DEST+'/Textures/'+key+'/T_'+key+'_'+role
  if hashlib.sha256(file.read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Source changed '+str(file))
  t=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_image(file.read_bytes(),'png',path,role)
  t.set_editor_property('srgb',role=='baseColor');t.set_editor_property('flip_green_channel',False)
  t.set_editor_property('max_texture_size',4096)
  if role=='height':t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DISPLACEMENTMAP)
  elif role=='normal':t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
  else:t.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_BC7)
  E.set_metadata_tag(t,'AOFSourceURL',row['url']);E.set_metadata_tag(t,'AOFSourceSHA256',item['sha256']);save(t);tx[key][role]=t
  report['textures'].append({'material':key,'role':role,'path':t.get_path_name(),'sourceSha256':item['sha256'],'sRGB':t.get_editor_property('srgb'),'flipGreen':t.get_editor_property('flip_green_channel')})
 print('TEXTURES_READY',key,flush=True)
# Sensei supplied AO defaults reference an unavailable Fab texture. Give every
# texture expression a valid default before compiling optional AO branches.
for parent in parents.values():
 for node in M.get_material_expressions(parent):
  if isinstance(node,unreal.MaterialExpressionTextureBase) and node.get_editor_property('texture') is None:
   node.set_editor_property('texture',tx['stone_cream']['ao'])
 M.recompile_material(parent);save(parent)

def scalar(mi,n,v):
 M.set_material_instance_scalar_parameter_value(mi,n,float(v))
 if abs(M.get_material_instance_scalar_parameter_value(mi,n)-v)>1e-4:raise RuntimeError('Scalar '+n)
def switch(mi,n,v):
 M.set_material_instance_static_switch_parameter_value(mi,n,v)
 if M.get_material_instance_static_switch_parameter_value(mi,n)!=v:raise RuntimeError('Switch '+n)
def preset(name,layers,blend=False,nanite=False,wet=False,triplanar=False):
 path=DEST+'/Instances/MI_AOF_'+name
 mi=E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset('MI_AOF_'+name,DEST+'/Instances',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
 M.set_material_instance_parent(mi,parents['nanite' if nanite else 'surface'])
 for layer,key in zip('ABC',layers):
  maps=tx[key];row=doc['materials'][key]
  for role,param in [('baseColor','Albedo Color'),('normal','Normal'),('height','Height'),('roughness','Roughness'),('metallic','Metallic'),('ao','Ambient Occlusion'),('orm','MaskORM')]:
   if role in maps:M.set_material_instance_texture_parameter_value(mi,param+' '+layer,maps[role])
  for n,v in [('Use Mask?',False),('Use Metallic?','metallic' in maps),('Use AO?','ao' in maps),('Use Specular?',True),('Triplanar?',triplanar),('Extra Size & Offset Options?',True),('Rotation?',True)]:switch(mi,n+' '+layer,v)
  for n,v in [('Normal Strength',1.),('Roughness Strength',1.),('Roughness Contrast',1.),('Size',1.),('Height Blend Strength',1.),('Height Blend Power',1.),('Height Blend Offset',0.),('AO Intensity',1.)]:scalar(mi,n+' '+layer,v)
  size=row.get('tileMetres',[1,1]);M.set_material_instance_vector_parameter_value(mi,'Tiling '+layer,unreal.LinearColor(2/max(size[0],.01),2/max(size[1],.01),0,0))
  if nanite:
   scalar(mi,'Displacement Amount '+layer,.15);scalar(mi,'Displacement Strength '+layer,1.);scalar(mi,'Displacement Contrast '+layer,1.)
 switch(mi,'Second Material Layer?',blend);switch(mi,'Third Material Layer?',blend)
 switch(mi,'UseOldVertexBlending?',blend);switch(mi,'Use Height for Blend?',True);switch(mi,'Puddle Layer?',wet)
 scalar(mi,'AB Blend Contrast',.25);scalar(mi,'BC Blend Contrast',.25)
 if wet:
  scalar(mi,'Liquid Roughness',.12);scalar(mi,'Liquid Opacity',.12);scalar(mi,'Normal Flatten Amount',.4)
 M.update_material_instance(mi);save(mi)
 entry={'name':name,'path':path,'parent':mi.get_editor_property('parent').get_path_name(),'layers':dict(zip('ABC',layers)),'vertexPaintRGB':blend,'wetLayer':wet,'triplanar':triplanar,'naniteDisplacement':nanite}
 report['instances'].append(entry);return mi
instances={}
for key in tx:instances[key]=preset(key,[key,'mortar','dust'])
variants=[('stone_weathered',['stone_cream','stone_cracked','dust'],True,False,False,False),('stone_masonry',['stone_worn','mortar','dust'],True,False,False,False),('iron_worn',['metal_clean','dark_metal','dust'],True,False,False,False),('bronze_dust',['bronze','mortar','dust'],True,False,False,False),('wood_weathered',['wood','mortar','dust'],True,False,False,False),('stone_triplanar',['stone_cream','stone_cracked','dust'],False,False,False,True),('floor_displaced',['stone_worn','mortar','dust'],False,True,False,False),('floor_wet',['stone_cream','mortar','dust'],True,False,True,False)]
for name,layers,b,n,w,t in variants:preset(name,layers,b,n,w,t)
# Assign the six principal presets to every slot in the existing 48-piece pilot.
meshdoc=json.loads((ROOT/'Source/Elements/Assets/Built/aof-pilot-001-048/manifest.json').read_text())
for row in meshdoc['meshes']:
 mesh=E.load_asset('/Game/Bibliotheque/ArenaFate/Pieces001048/Meshes/'+row['id'])
 if not mesh:raise RuntimeError('Missing pilot '+row['id'])
 for i,slot in enumerate(mesh.get_editor_property('static_materials')):
  key=next((k for k in instances if str(slot.material_slot_name)==k or str(slot.material_slot_name).startswith(k+'.')),None)
  if not key:raise RuntimeError('Unmapped '+str(slot.material_slot_name))
  mesh.set_material(i,instances[key])
 save(mesh)
report['meshesUpdated']=48
(ROOT/'Saved/Jadg/aof-master-v3').mkdir(parents=True,exist_ok=True)
(ROOT/'Saved/Jadg/aof-master-v3/report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
unreal.log('AOF_MASTER_V3_COMPLETE')
