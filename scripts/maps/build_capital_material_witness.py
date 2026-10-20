"""A reproducible material review room in the same daylight/capture pipeline."""
from pathlib import Path


def build(frame,library):
    import unreal
    import build_level as scene
    import jadg_map
    import capital_surface_materials as surfaces
    root=Path(__file__).resolve().parents[2]
    doc={'format':jadg_map.FORMAT,'version':jadg_map.VERSION,'name':'CapitalMaterialWitness',
         'width':20,'height':20,'origin':[-15,-15],'storeys':[{'name':'sol','z':0}],
         'nextEntityId':1,'tiles':[{'x':10,'y':10,'type':'entry'}],'entities':[],
         'party':{'appearances':['heros-brawler'],'walkSpeed':3.,'heading':0},
         'ground':{'colour':'#c2b99c','size':200,'height':-1.},
         'lighting':{'sunScale':1.65,'ambientScale':.34,'skyLuminance':1.8,'exposureBias':0},
         'daylight':jadg_map.DAYLIGHT,'shots':[
             {'id':'atelier','target':[18,5,1],'heading':330,'pitch':36,'distance':60},
             {'id':'rasant','target':[10,0,1],'heading':290,'pitch':8,'distance':20},
             {'id':'deplacement','target':[16,24,.2],'heading':0,'pitch':10,'distance':13}],
         'hours':['12:00','22:00']}
    path=root/'Source/Test/Fixtures/Exploration/Levels/capital-landscape/material-witness.json'
    path.write_text(jadg_map.dumps(doc),encoding='utf8')
    world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);level=scene.Level(world)
    cube=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube')
    sphere=unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Sphere')
    stone=unreal.EditorAssetLibrary.load_asset('/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_stone_cream')
    wood=unreal.EditorAssetLibrary.load_asset('/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_wood')
    dry=unreal.EditorAssetLibrary.load_asset(surfaces.CONTENT+'/MI_soil_0')
    wet=unreal.EditorAssetLibrary.load_asset(surfaces.CONTENT+'/MI_wet_soil_0')
    paving=unreal.EditorAssetLibrary.load_asset(surfaces.CONTENT+'/MI_paving_0')
    def piece(name,x,y,z,w,d,h,mat,mesh=cube,pitch=0,yaw=0):
        actor=level.spawn(mesh,frame.map_point([x,y,z]),unreal.Rotator(pitch,yaw,0),name,'witness',unreal.Vector(w,d,h))
        actor.static_mesh_component.set_material(0,mat)
        return actor
    piece('neutral-base',18,6,-.8,65,35,1,stone)
    piece('plane',0,0,0,5,5,.3,stone)
    piece('slope-22deg',8,0,1,5,5,.3,stone,pitch=22)
    piece('rock-response',16,0,1.5,4,3,3,stone,mesh=sphere)
    piece('wall-foot',24,0,1.5,5,.8,3,stone)
    piece('wall-foundation',24,0,0,5,1.4,.4,stone)
    piece('inside-angle-a',32,0,1.5,5,.8,3,stone)
    piece('inside-angle-b',34,2,1.5,.8,5,3,stone)
    piece('outside-angle-a',40,0,1.5,5,.8,3,stone)
    piece('outside-angle-b',42,-2,1.5,.8,5,3,stone)
    piece('dry-contact',0,10,0,4,5,.3,dry)
    piece('wet-contact',4,10,0,4,5,.3,wet)
    for i in range(3):
        actor=level.spawn(library.static_mesh(f'Built/capital-urban/cu-paving-{i}.glb'),frame.map_point([12+i*8,12,0]),frame.rotation(0),f'paving-{i}','witness')
        for j in range(len(actor.static_mesh_component.static_mesh.static_materials)):actor.static_mesh_component.set_material(j,paving)
    piece('wood-junction',36,12,0,4,6,.4,wood)
    piece('stone-junction',40,12,0,4,6,.4,stone)
    water=unreal.EditorAssetLibrary.load_asset('/Game/Capitale/Ressources/MI_Water_pool')
    piece('shore-bed',46,10,-.2,8,8,.3,dry,pitch=8)
    water_actor=piece('shore-water',46,10,.25,8,8,.01,water)
    water_actor.static_mesh_component.set_editor_property('disallow_nanite',True)
    water_actor.static_mesh_component.set_editor_property('cast_shadow',False)
    water_actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for i,suffix in enumerate(('flat','2cm')):
        actor=level.spawn(library.static_mesh('Built/capital-urban/cu-paving-0.glb'),frame.map_point([12+i*9,24,0]),frame.rotation(0),'displacement-'+suffix,'witness')
        mat=unreal.EditorAssetLibrary.load_asset(surfaces.CONTENT+'/MI_Displacement_'+suffix)
        for j in range(len(actor.static_mesh_component.static_mesh.static_materials)):actor.static_mesh_component.set_material(j,mat)
    scene.place_sky(level,doc,frame);scene.place_frame(level,doc,frame,'capital-landscape/material-witness',path)
    scene.place_shots(level,doc,frame);scene.place_characters(level,doc,frame,library)
    world.get_world_settings().set_editor_property('default_game_mode',scene.game_class('JadgGameMode'))
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/Levels/capital-landscape/material-witness'):
        raise RuntimeError('Material witness save failed')


if __name__=='__main__':
    import sys
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'scripts/maps'));sys.path.insert(0,str(root/'scripts/assetsGeneration'))
    import build_level as scene
    fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(root).as_posix())
    frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
    build(frame,scene.Library())
