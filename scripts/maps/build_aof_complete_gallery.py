import unreal as u
import json
import sys
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();sys.path.insert(0,str(P/'scripts/maps'))
import build_aof_extension_maps as b  # noqa: E402
pilot=json.loads((P/'Source/Elements/Assets/Built/aof-pilot-001-048/manifest.json').read_text(encoding='utf-8'))['meshes']
rows=[dict(r,physics='static',nativeAsset='/Game/Bibliotheque/ArenaFate/Pieces001048/Meshes/'+r['id']) for r in pilot if r['catalogueId']<46]+b.records
b.build_map('GalerieAssets',sorted(rows,key=lambda r:r['catalogueId']),columns=12)
world=u.EditorLoadingAndSavingUtils.new_blank_map(False);level=b.scene.Level(world);frame=b.frame;shots=[]
floor=level.spawn(b.cube,frame.map_point([12,12,-.45]),u.Rotator(),'Sol','Studio',u.Vector(70,70,.5));floor.static_mesh_component.set_material(0,b.gray)
materials=[('/Game/Capitale/Ressources/PBR4K/Materials/MI_'+k,k) for k in ['grass','forest','rock','sand','soil','wet_soil','paving','paving_worn']]
materials += [('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_'+k,k) for k in ['stone_cream','marble_white','wood','dark_metal','metal_clean','bronze','mortar','stone_worn','stone_weathered','floor_wet']]
materials += [('/Game/Bibliotheque/ArenaFate/Materials/MI_AOF_'+k,k) for k in ['linen','sacking','leather','LinenBurgundy']]
for i,(path,label) in enumerate(materials):
 mat=b.E.load_asset(path)
 if not mat:raise RuntimeError(path)
 x=i%4*8;y=i//4*7
 tile=level.spawn(b.cube,frame.map_point([x,y,0]),u.Rotator(),label+' dalle 2m','Textures',u.Vector(2,2,.12));tile.static_mesh_component.set_material(0,mat)
 ball=level.spawn(b.sphere,frame.map_point([x+1.8,y,1]),u.Rotator(),label+' sphere','Textures',u.Vector(1.5,1.5,1.5));ball.static_mesh_component.set_material(0,mat)
 text=level.spawn(u.TextRenderActor,frame.map_point([x-1,y+1.8,.5]),frame.rotation(0),label,'Etiquettes')
 comp=text.get_component_by_class(u.TextRenderComponent);comp.set_text(label);comp.set_world_size(25)
 shots.append({'id':label,'target':[x+.8,y,.6],'heading':335,'pitch':35,'distance':6})
config={'format':b.jadg_map.FORMAT,'version':b.jadg_map.VERSION,'name':'GalerieMateriaux','width':70,'height':70,'origin':[-35,-35],'storeys':[{'name':'sol','z':0}],'nextEntityId':1,'tiles':[{'x':20,'y':20,'type':'entry'}],'entities':[],'daylight':b.jadg_map.DAYLIGHT,'lighting':{'sunScale':.7,'ambientScale':1.25,'skyLuminance':1.5,'exposureBias':0},'shots':shots,'hours':['12:00','22:00']}
b.scene.place_sky(level,config,frame);b.scene.place_shots(level,config,frame);world.get_world_settings().set_editor_property('default_game_mode',b.scene.game_class('JadgGameMode'))
if not u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Atelier/Cartes/GalerieMateriaux'):raise RuntimeError('save gallery')
print('COMPLETE_GALLERIES_READY',len(rows),len(materials),flush=True)
