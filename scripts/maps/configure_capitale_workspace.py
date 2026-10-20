import unreal as u
import json
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();W=P/'Source/Elements/Terrain/capital/relief-reference'
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Capitale/Cartes/Capitale')
A=u.get_editor_subsystem(u.EditorActorSubsystem);packages=[]
current={str(a.get_editor_property('shot_id')):a for a in A.get_all_level_actors() if a.get_class().get_name()=='JadgShot'}
views=json.loads((W/'views.json').read_text())
# Un cadrage retire de views.json quitte aussi la carte (son paquet externe avec lui).
stale=[a for k,a in current.items() if k not in {row['id'] for row in views}]
stale_packages=[a.get_package().get_name() for a in stale]
for a in stale:A.destroy_actor(a)
for i,row in enumerate(views):
 actor=current.get(row['id']) or A.spawn_actor_from_class(u.JadgShot,u.Vector(),u.Rotator())
 actor.set_actor_location(u.Vector(*[v*100 for v in row['target']]),False,True)
 actor.set_actor_rotation(u.Rotator(pitch=row['pitch'],yaw=row['yaw'],roll=0),False)
 actor.set_actor_label('Vue_'+row['id']);actor.set_folder_path('Atelier/Cadrages')
 actor.set_editor_property('shot_id',row['id']);actor.set_editor_property('distance',row['distance']*100);actor.set_editor_property('order',100+i);actor.set_editor_property('is_spatially_loaded',False)
 packages.append(actor.get_package())
for actor in A.get_all_level_actors():
 if actor.get_class().get_name()=='JadgMapFrame':
  actor.set_editor_property('level_id','Capitale');packages.append(actor.get_package())
u.EditorLoadingAndSavingUtils.save_packages(packages,False)
assert u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Capitale/Cartes/Capitale')
content=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_content_dir()))
for name in stale_packages:
 f=content/(name[len('/Game/'):]+'.uasset')
 if f.is_file():f.unlink()
print('CLEAN_CAPITAL_VIEWS_READY',flush=True)
