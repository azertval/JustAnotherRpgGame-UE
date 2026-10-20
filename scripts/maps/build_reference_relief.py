"""Build the natural relief of the Guide de Creation in a staging world: Landscape tiles with their painted layers (roads included), water, sky; no building or placed vegetation."""
from pathlib import Path
from array import array
import json
import sys
import gc
import unreal as u
P=Path(u.Paths.project_dir()).resolve();D=P/'Source/Elements/Terrain/capital/relief-reference'
sys.path.insert(0,str(P/'scripts/maps'));sys.path.insert(0,str(P/'scripts/assetsGeneration'))
import build_level as scene  # noqa: E402
import import_scenery_unreal as scenery  # noqa: E402
import jadg_map  # noqa: E402
E=u.EditorAssetLibrary;ML=u.MaterialEditingLibrary
PACKAGE='/Game/Capitale/Cartes/Capitale_Reconstruction'
CONTENT='/Game/Capitale/Ressources/ReliefReference'
world=u.EditorLoadingAndSavingUtils.new_blank_map(False);level=scene.Level(world)
if E.does_asset_exist(PACKAGE):
 assert E.delete_asset(PACKAGE), 'Cannot clear the temporary reconstruction world'
# The natural terrain material (build_capitale_terrain_material.py) and its runtime virtual texture.
mi=E.load_asset(CONTENT+'/MI_TerrainNaturel');rvt=E.load_asset(CONTENT+'/RVT_TerrainNaturel')
assert mi and mi.get_editor_property('parent').get_name()=='M_TerrainNaturel','Run build_capitale_terrain_material.py first'
assert rvt,'Missing RVT_TerrainNaturel'
manifest=json.loads((D/'manifest.json').read_text(encoding='utf-8'));built=[]
for t in manifest['tiles']:
 hs=array('H');hs.frombytes((D/(t['id']+'.r16')).read_bytes())
 land=u.JadgSceneBuild.spawn_landscape(world,u.Vector(t['origin'][0]*100,t['origin'][1]*100,0),u.Vector(200,200,100),504,504,hs.tolist(),manifest['layers'],list((D/(t['id']+'.r8')).read_bytes()),mi,CONTENT+'/Couches',True)
 assert land is not None,t['id']
 scene.Level.name(land,t['id'],'01_Relief');land.tags=['CapitaleReliefReference']
 # The generated relief is one named edit layer; hand sculpting and painting go to Retouches above it.
 assert u.JadgSceneBuild.name_landscape_edit_layers(land,'Relief_Reference',['Retouches'])
 assert u.JadgSceneBuild.finalize_landscape_layers(land)
 # Build Nanite only after partitioning, one saved proxy at a time.
 land.set_editor_property('enable_nanite',False)
 land.set_editor_property('nanite_skirt_enabled',True);land.set_editor_property('nanite_skirt_depth',.2)
 tris=0
 built.append(dict(id=t['id'],nanite_triangles=tris))
 print('REFERENCE_TILE_READY',t['id'],tris,flush=True)
 del hs;gc.collect()

# Existing production water master, with the newly generated sloping water skins.
registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Interchange/Pipelines'],True,True)
pipeline=E.load_asset('/Game/Capitale/Ressources/Eau/P_ImportEau')
options=u.InterchangePipelineStackOverride();options.set_editor_property('override_pipelines',[u.SoftObjectPath(pipeline.get_path_name()),u.SoftObjectPath('/Interchange/Pipelines/DefaultGLTFPipeline.DefaultGLTFPipeline')]);scenery._COLLISION_IMPORT_OPTIONS=options
water=E.load_asset('/Game/Capitale/Ressources/Eau/MI_Eau_Capitale')
waters=json.loads((D/'water/manifest.json').read_text(encoding='utf-8'))
for row in waters:
 name=row['id'];folder=CONTENT+'/Eau'
 mesh=scenery.import_glb(D/'water'/(name+'.glb'),folder,folder+'/'+name,folder+'/'+name+'/StaticMeshes/SM_'+name,collision_proxy=True)
 ns=mesh.get_editor_property('nanite_settings');ns.enabled=False;mesh.set_editor_property('nanite_settings',ns)
 mesh.set_material(0,water);E.save_loaded_asset(mesh,False)
 a=level.spawn(mesh,u.Vector(),u.Rotator(),name,'02_Eau');a.tags=['CapitaleEauReference']
 a.set_actor_enable_collision(False);a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.static_mesh_component.set_editor_property('cast_shadow',False)

# The material writes RVT_TerrainNaturel, but the Landscape does not render into it yet: with the RVT
# assigned and its volume placed, UE 5.8 crashes loading the partitioned map in a rendering editor
# (IsInGameThread assertion in ShowFlags.cpp from a worker, 17 October 2026). Left to a later trial.

class IdentityFrame:
 def map_point(self,p):return u.Vector(*[v*100 for v in p])
 def map_direction(self,p):return u.Vector(*p)
frame=IdentityFrame()
doc={'daylight':jadg_map.DAYLIGHT,'lighting':{'sunScale':1.65,'ambientScale':.34,'skyLuminance':1.8,'exposureBias':0.,'fog':{'density':.00025,'falloff':.08,'volumetric':False},'post':{'bloom_intensity':.25,'vignette_intensity':.08,'motion_blur_amount':0.,'film_grain_intensity':0.}}}
scene.place_sky(level,doc,frame)
mf=level.spawn(u.JadgMapFrame,u.Vector(),u.Rotator(),'Carte_Capitale','Atelier')
mf.set_editor_property('level_id','Capitale');mf.set_editor_property('levels_root','')
mf.set_editor_property('cell_size',150.);mf.set_editor_property('east',u.Vector(1,0,0));mf.set_editor_property('south',u.Vector(0,1,0));mf.set_editor_property('storey_heights',[0.])
shots=json.loads((D/'views.json').read_text(encoding='utf-8'))
for i,s in enumerate(shots):
 a=level.spawn(u.JadgShot,frame.map_point(s['target']),u.Rotator(pitch=s['pitch'],yaw=s['yaw'],roll=0),'Vue_'+s['id'],'Atelier/Cadrages')
 a.set_editor_property('shot_id',s['id']);a.set_editor_property('distance',s['distance']*100);a.set_editor_property('order',i);a.set_editor_property('is_spatially_loaded',False)
start=level.spawn(u.PlayerStart,u.Vector(0,0,5500),u.Rotator(),'Depart','Atelier')
world.get_world_settings().set_editor_property('default_game_mode',scene.game_class('JadgGameMode'))
E.save_directory(CONTENT,only_if_is_dirty=False,recursive=True)
assert u.EditorLoadingAndSavingUtils.save_map(world,PACKAGE)
report=dict(map=PACKAGE,landscapes=built,water_meshes=len(waters),edit_layers=['Relief_Reference','Retouches'],paint_layers=manifest['layers'],rvt_written_by_material=rvt.get_path_name(),rvt_assigned=False,painted_roads=manifest['roads'],buildings=0,vegetation=0,building_sites=0,material=mi.get_path_name())
(P/'Saved/Jadg/relief-reference-build.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('REFERENCE_WORLD_READY',report,flush=True)
