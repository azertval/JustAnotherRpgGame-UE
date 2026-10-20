import unreal
import json
import sys
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/assetsGeneration')]
import build_level as scene  # noqa: E402
import jadg_map  # noqa: E402
import import_scenery_unreal as scenery  # noqa: E402
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary
D='/Game/ArenaFateMaterials';report=json.loads((ROOT/'Saved/Jadg/aof-master-v3/report.json').read_text())
world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);level=scene.Level(world)
fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix());frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
cube=unreal.load_asset('/Engine/BasicShapes/Cube');sphere=unreal.load_asset('/Engine/BasicShapes/Sphere')
gray=scene.flat_material(D+'/Lab/M_Neutral',unreal.LinearColor(.22,.24,.27,1),.65)
def spawn(mesh,x,y,z,sx,sy,sz,mat,label):
 a=level.spawn(mesh,frame.map_point([x,y,z]),unreal.Rotator(),label,'MaterialLab',unreal.Vector(sx,sy,sz));a.static_mesh_component.set_material(0,mat);return a
spawn(cube,13,14,-.4,90,80,.5,gray,'Sol neutre')
sky=scene.flat_material(D+'/Lab/M_Background',unreal.LinearColor(.14,.17,.21,1),1)
M.delete_all_material_expressions(sky);n=M.create_material_expression(sky,unreal.MaterialExpressionConstant3Vector,0,0);n.set_editor_property('constant',unreal.LinearColor(.14,.17,.21,1));M.connect_material_property(n,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
sky.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_UNLIT);sky.set_editor_property('two_sided',True);M.recompile_material(sky);E.save_loaded_asset(sky,False)
dome=spawn(sphere,13,14,0,300,300,300,sky,'Fond studio');dome.static_mesh_component.set_cast_shadow(False);dome.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
wp=D+'/Lab/SM_LayerWitness';p=ROOT/'Source/Elements/Assets/Built/aof-material-witness/SM_AOF_LayerWitness.glb'
witness=E.load_asset(wp) if E.does_asset_exist(wp) else scenery.import_glb(p,D+'/Lab/Import',D+'/Lab/Import/SM_AOF_LayerWitness',wp)
scenery.finish(witness);witness.set_material(0,E.load_asset(D+'/Instances/MI_AOF_stone_weathered'));E.save_loaded_asset(witness,False)
shots=[]
for i,row in enumerate(report['instances']):
 x=(i%5)*7;y=(i//5)*8;mat=E.load_asset(row['path']);name=row['name']
 spawn(cube,x,y,.0,5.6,4,.3,gray,name+' socle')
 if row['vertexPaintRGB'] or row['naniteDisplacement']:
  panel=level.spawn(witness,frame.map_point([x,y,.16]),frame.rotation(0),name,'Layer tests');panel.static_mesh_component.set_material(0,mat)
  target=[x,y,1.35];dist=5.5
 else:
  spawn(sphere,x-.95,y,1.05,1.75,1.75,1.75,mat,name+' sphere')
  spawn(cube,x+1.3,y,1.26,1.8,.3,2.2,mat,name+' panneau')
  target=[x+.1,y,1.3];dist=5.5
 shots.append({'id':name,'target':target,'heading':0,'pitch':25,'distance':dist})
 for side,(dx,dy,z,heading,pitch,power) in enumerate([(-1.8,2.8,3.5,335,35,24),(2.5,-1.5,2.8,135,25,9)]):
  a=level.spawn(unreal.RectLight,frame.map_point([x+dx,y+dy,z]),frame.look(heading,pitch),name+' softbox '+str(side),'StudioLights')
  comp=a.light_component;comp.set_mobility(unreal.ComponentMobility.MOVABLE);comp.set_editor_property('intensity_units',unreal.LightUnits.CANDELAS);comp.set_editor_property('intensity',power);comp.set_editor_property('source_width',150.);comp.set_editor_property('source_height',220.);comp.set_editor_property('attenuation_radius',650.)
 shots[-1]['distance']=5.5
shots.append({'id':'ensemble','target':[14,12,1],'heading':335,'pitch':50,'distance':48})
config={'format':jadg_map.FORMAT,'version':jadg_map.VERSION,'name':'AOF Material Library V3','width':60,'height':60,'origin':[-40,-40],'storeys':[{'name':'sol','z':0}],'nextEntityId':1,'tiles':[{'x':20,'y':20,'type':'entry'}],'entities':[],'daylight':jadg_map.DAYLIGHT,'lighting':{'sunScale':.65,'ambientScale':1.25,'skyLuminance':1.5,'exposureBias':0,'post':{'bloom_intensity':.05}},'shots':shots,'hours':['12:00','22:00']}
scene.place_sky(level,config,frame);scene.place_shots(level,config,frame)
world.get_world_settings().set_editor_property('default_game_mode',scene.game_class('JadgGameMode'))
package='/Game/Maps/Levels/essai/aof-master-materiaux-v3'
if not unreal.EditorLoadingAndSavingUtils.save_map(world,package):raise RuntimeError('Save lab')
(ROOT/'Saved/Jadg/aof-master-v3/lab.json').write_text(json.dumps(config,indent=2));unreal.log('AOF_LAB_V3_COMPLETE')

