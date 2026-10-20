"""Bind the supplied Unreal Sensei parent to the Arena pilot surface library."""
import unreal
import json
import sys
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve()
sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import import_scenery_unreal as scenery  # noqa: E402
E=unreal.EditorAssetLibrary;ML=unreal.MaterialEditingLibrary
DEST='/Game/ArenaFatePilot001048';SOURCE=ROOT/'Source/Elements/Assets/Built/aof-pilot-surfaces-v2'
def create():
 doc=json.loads((SOURCE/'manifest.json').read_text());result={};report=[]
 parent=E.load_asset('/Game/Bibliotheque/Materiaux/Sensei/Materials/M_BlendMaster')
 if not parent:raise RuntimeError('Supplied Sensei parent missing')
 for name,row in doc['materials'].items():
  tx={}
  for role,item in row['files'].items():
   if role not in ('baseColor','normal','orm','height'):continue
   p=SOURCE/item['file'];path=DEST+'/TexturesV2/T_'+name+'_'+role
   tex=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_image(p.read_bytes(),'png',path,role)
   if role=='height':
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_DISPLACEMENTMAP)
    tex.set_editor_property('srgb',False);E.save_loaded_asset(tex,False)
   tx[role]=tex
  path=DEST+'/Materials/MI_'+name;mi=E.load_asset(path)
  if not mi:mi=unreal.AssetToolsHelpers.get_asset_tools().create_asset('MI_'+name,DEST+'/Materials',unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
  ML.set_material_instance_parent(mi,parent)
  # A/B/C all hold valid PBR maps; paint layers can be enabled without flat defaults.
  for layer in 'ABC':
   for role,param in [('baseColor','Albedo Color'),('normal','Normal'),('orm','MaskORM'),('height','Height')]:
    ML.set_material_instance_texture_parameter_value(mi,param+' '+layer,tx[role])
   for param,val in [('Use Mask?',True),('Use Metallic?',True),('Use AO?',True),('Use Specular?',True)]:
    ML.set_material_instance_static_switch_parameter_value(mi,param+' '+layer,val)
   for param,val in [('Normal Strength',1.),('Roughness Strength',1.),('Roughness Contrast',1.),('Size',1.),('Displacement Amount',1.),('Displacement Strength',1.),('Displacement Contrast',1.),('Displacement Offset',0.)]:
    ML.set_material_instance_scalar_parameter_value(mi,param+' '+layer,val)
  ML.set_material_instance_static_switch_parameter_value(mi,'Second Material Layer?',False)
  ML.set_material_instance_static_switch_parameter_value(mi,'Third Material Layer?',False)
  ML.set_material_instance_static_switch_parameter_value(mi,'Puddle Layer?',False)
  ML.update_material_instance(mi);E.save_loaded_asset(mi,False);result[name]=mi
  report.append({'name':name,'parent':parent.get_path_name(),'normalStrength':1,'roughnessClamped':False,'metalEnabled':True,'maps':{k:v.get_path_name() for k,v in tx.items()},'layers':'A active; B/C configured but not painted','heightRangeMm':row['heightRangeMm']})
 # Displacement on an open surface avoids splitting hard-edged architectural seams.
 testpath=DEST+'/Materials/MI_stone_displacement'
 test=E.load_asset(testpath) if E.does_asset_exist(testpath) else E.duplicate_asset(DEST+'/Materials/MI_stone_cream',testpath)
 ML.set_material_instance_parent(test,E.load_asset('/Game/Bibliotheque/Materiaux/Sensei/Materials/M_BlendMaster_Nanite'))
 ML.update_material_instance(test);E.save_loaded_asset(test,False)
 (ROOT/'Saved/Jadg/aof-pilot-001-048/sensei-v2.json').write_text(json.dumps(report,indent=2))
 return result
