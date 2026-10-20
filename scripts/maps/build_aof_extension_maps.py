import unreal
import json
import sys
import math
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir()).resolve();sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/assetsGeneration')]
import build_level as scene  # noqa: E402
import jadg_map  # noqa: E402
E=unreal.EditorAssetLibrary;M=unreal.MaterialEditingLibrary;D='/Game/ArenaFateExtension'
records=json.loads((ROOT/'Saved/Jadg/aof-extension/report.json').read_text(encoding='utf-8'))['meshes']
cube=E.load_asset('/Engine/BasicShapes/Cube');sphere=E.load_asset('/Engine/BasicShapes/Sphere')
gray=scene.flat_material(D+'/Lab/M_ReviewFloor',unreal.LinearColor(.18,.2,.22,1),.7)
metal=E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_dark_metal')
fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix());frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
def build_map(name,rows,physics=False,columns=6):
 world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);level=scene.Level(world);shots=[]
 centrex=(columns-1)*3.5;centrey=(math.ceil(len(rows)/columns)-1)*4
 floor=level.spawn(cube,frame.map_point([centrex,centrey,-.45]),unreal.Rotator(),'Sol de contrôle','Lab',unreal.Vector(max(90,columns*7+15),max(90,math.ceil(len(rows)/columns)*8+15),.5));floor.static_mesh_component.set_material(0,gray)
 wind=level.spawn(unreal.WindDirectionalSource,frame.map_point([0,0,5]),unreal.Rotator(0,20,0),'Vent de contrôle','Lab')
 wc=wind.get_component_by_class(unreal.WindDirectionalSourceComponent);wc.set_editor_property('strength',.4);wc.set_editor_property('speed',3.);wc.set_editor_property('min_gust_amount',.1);wc.set_editor_property('max_gust_amount',.35)
 for index,row in enumerate(rows):
  i=row['catalogueId'];x=(index%columns)*7;y=(index//columns)*8
  asset=row.get('nativeAsset') or row['referenceAssets'][0];mesh=E.load_asset(asset)
  if not mesh:raise RuntimeError('Missing '+asset)
  label=f'AOF_{i:03d}';z=.0
  if isinstance(mesh,unreal.SkeletalMesh):
   actor=level.spawn(unreal.JadgArenaSimulatedAsset,frame.map_point([x,y,z]),frame.rotation(0),label,'Assets')
   actor.set_editor_property('simulate_articulation',physics and row['physics']!='cloth')
   comp=actor.skeletal_mesh_component;comp.set_skeletal_mesh_asset(mesh);comp.set_mobility(unreal.ComponentMobility.MOVABLE)
   comp.set_editor_property('visibility_based_anim_tick_option',unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
   comp.set_editor_property('wait_for_parallel_cloth_task',True)
   if row['physics']=='cloth':
    comp.set_editor_property('disable_cloth_simulation',False);comp.set_editor_property('cloth_blend_weight',1.);comp.set_editor_property('collide_with_environment',True)
    # Visible supports correspond to the fixed attachment line/corners.
    if i in (71,89):
     for dx in (-1.5,1.5):
      for dy in (-1,1):
       a=level.spawn(cube,frame.map_point([x+dx,y+dy,1.25]),unreal.Rotator(),label+' support','Supports',unreal.Vector(.08,.08,2.5));a.static_mesh_component.set_material(0,metal)
    else:
     a=level.spawn(cube,frame.map_point([x,y,2.65]),unreal.Rotator(),label+' traverse','Supports',unreal.Vector(2.1,.06,.06));a.static_mesh_component.set_material(0,metal)
     a=level.spawn(cube,frame.map_point([x+1.1,y,1.3]),unreal.Rotator(),label+' mât','Supports',unreal.Vector(.07,.07,2.6));a.static_mesh_component.set_material(0,metal)
   elif physics:
    if row['physics']=='chain':actor.set_actor_rotation(unreal.Rotator(0,0,12),False)
    comp.set_collision_profile_name('PhysicsActor');comp.set_enable_gravity(True);comp.set_simulate_physics(True)
   actor.tags=[unreal.Name(label),unreal.Name('AOF_PhysicsWitness')]
  else:
   if physics and row['physics']=='rigid':z=.6
   actor=level.spawn(mesh,frame.map_point([x,y,z]),frame.rotation(0),label,'Assets')
   if i in (60,76):
    bounds=mesh.get_bounds();h=bounds.box_extent.z*2;actor.set_actor_scale3d(unreal.Vector(300/h,300/h,300/h))
   if physics and row['physics']=='rigid':
    comp=actor.static_mesh_component;comp.set_mobility(unreal.ComponentMobility.MOVABLE);comp.set_collision_profile_name('PhysicsActor');comp.set_enable_gravity(True);comp.set_simulate_physics(True)
  if physics:
   shots.append({'id':label,'target':[x,y,1.5],'heading':335,'pitch':25,'distance':7})
  if index%6==0 and not physics:shots.append({'id':f'{i:03d}-{min(i+5,192):03d}','target':[x+17.5,y,1.3],'heading':0,'pitch':30,'distance':29})
  lamp=level.spawn(unreal.RectLight,frame.map_point([x-2,y+3,4]),frame.look(335,35),label+' éclairage','Studio')
  light=lamp.light_component;light.set_editor_property('intensity_units',unreal.LightUnits.CANDELAS);light.set_editor_property('intensity',35.);light.set_editor_property('source_width',200.);light.set_editor_property('source_height',220.);light.set_editor_property('attenuation_radius',650.)
 shots.append({'id':'ensemble','target':[centrex,centrey,1.5],'heading':335,'pitch':50,'distance':min(120,max(58,centrey*2))})
 config={'format':jadg_map.FORMAT,'version':jadg_map.VERSION,'name':name,'width':80,'height':80,'origin':[-40,-40],'storeys':[{'name':'sol','z':0}],'nextEntityId':1,'tiles':[{'x':20,'y':20,'type':'entry'}],'entities':[],'daylight':jadg_map.DAYLIGHT,'lighting':{'sunScale':.7,'ambientScale':1.25,'skyLuminance':1.5,'exposureBias':0,'post':{'bloom_intensity':.05}},'shots':shots,'hours':['12:00','22:00']}
 scene.place_sky(level,config,frame);scene.place_shots(level,config,frame);world.get_world_settings().set_editor_property('default_game_mode',scene.game_class('JadgGameMode'))
 if physics and hasattr(unreal,'JadgArenaPhysicsWitness'):level.spawn(unreal.JadgArenaPhysicsWitness,unreal.Vector(),unreal.Rotator(),'Contrôle physique','Lab')
 package='/Game/Atelier/Cartes/'+name
 if not unreal.EditorLoadingAndSavingUtils.save_map(world,package):raise RuntimeError('Save '+package)
 (ROOT/'Saved/Jadg/aof-extension'/f'{name}.json').write_text(json.dumps(config,indent=2));print('MAP_READY',package,flush=True)
if __name__=='__main__':
 ids=[71,81,89,90,192,91,128,114,116,159,132,163,164,165,46,47,48]
 build_map('PhysiqueTissus',[next(r for r in records if r['catalogueId']==i) for i in ids],True)
 unreal.log('AOF_EXTENSION_MAPS_COMPLETE')
