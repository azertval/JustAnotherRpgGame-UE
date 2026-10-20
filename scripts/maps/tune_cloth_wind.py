import unreal as u
maps=['aof-049-096-materiaux','aof-097-144-materiaux','aof-145-192-materiaux','aof-galerie-complete-001-192','aof-physique-tissus-mecanismes']
for name in maps:
 world=u.EditorLoadingAndSavingUtils.load_map('/Game/Maps/Levels/essai/'+name)
 for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
  if isinstance(a,u.WindDirectionalSource):
   c=a.get_component_by_class(u.WindDirectionalSourceComponent)
   c.set_editor_property('speed',3.0)
   c.set_editor_property('strength',.4)
 if not u.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/Levels/essai/'+name):raise RuntimeError(name)
 print('WIND_TUNED',name,flush=True)
