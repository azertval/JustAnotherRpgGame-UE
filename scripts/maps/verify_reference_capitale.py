import unreal as u
import json
import collections
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();O=P/'Saved/Jadg';O.mkdir(parents=True,exist_ok=True)
waters=len(json.loads((P/'Source/Elements/Terrain/capital/relief-reference/water/manifest.json').read_text(encoding='utf-8')))
R=u.AssetRegistryHelpers.get_asset_registry();R.search_all_assets(True);R.scan_paths_synchronous(['/Game'],True)
opts=u.AssetRegistryDependencyOptions(include_soft_package_references=True,include_hard_package_references=True,include_searchable_names=False,include_soft_management_references=False,include_hard_management_references=False)
assets=list(R.get_assets_by_path('/Game',recursive=True));known={str(a.package_name) for a in assets}
missing=[]
for a in assets:
 for dep in R.get_dependencies(a.package_name,opts):
  d=str(dep)
  if d.startswith('/Game/') and d not in known:missing.append({'source':str(a.package_name),'target':d})
worlds=[str(a.package_name) for a in assets if str(a.asset_class_path.asset_name)=='World']
# The renamer leaves its source world on disk; it is regenerated (and replaced) by build_reference_relief.py.
worlds=[w for w in worlds if w!='/Game/Capitale/Cartes/Capitale_Reconstruction']
# Les packs du Fab apportent leur carte de demonstration (CommonHazel_Asset_Zoo) : elle reste a eux.
worlds=[w for w in worlds if not w.startswith('/Game/CommonHazel/')]
assert set(worlds)=={'/Game/Capitale/Cartes/Capitale','/Game/Atelier/Cartes/GalerieAssets','/Game/Atelier/Cartes/GalerieMateriaux','/Game/Atelier/Cartes/PhysiqueTissus'},worlds
assert not missing,missing[:20]
world=u.EditorLoadingAndSavingUtils.load_map('/Game/Capitale/Cartes/Capitale');assert world
descs=u.WorldPartitionBlueprintLibrary.get_actor_descs()
classes=dict(collections.Counter(d.native_class.get_name() for d in descs))
assert classes.get('Landscape',0)==16,classes
assert classes.get('LandscapeStreamingProxy',0)==64,classes
# L'eau, puis l'Arena of Fate (place_capitale_arena.py : un acteur par objet de sa description).
objects=json.loads((P/'Source/Elements/Levels/central-empire/capital/arenarea/arena-of-fate.json').read_text(encoding='utf-8'))['objects']
# Chaque brasero ou lanterne porte en plus sa flamme (place_capitale_arena.py), et chaque applique,
# lanterne ou brasero des accessoires la sienne (arena_fate_atmosphere.install, rapport de la pose).
placed=json.loads((P/'Saved/Jadg/capitale-arene.json').read_text(encoding='utf-8'))
arena=len(objects)+sum(1 for o in objects if o.get('flame'))+placed.get('atmosphere',{}).get('flames',0)
assert classes.get('StaticMeshActor',0)==waters+arena,(classes,waters,arena)
# Aucune vegetation (demande de l'auteur du 19 octobre 2026, retire_capitale_vegetation.py).
for kind in ('PCGVolume','PCGPartitionActor','PCGWorldActor','InstancedFoliageActor'):assert classes.get(kind,0)==0,classes
assert not u.EditorAssetLibrary.does_directory_exist('/Game/Capitale/Ressources/Vegetation')
assert classes.get('TargetPoint',0)==0
# Le streaming World Partition est actif (configure_capitale_streaming.py) : la carte ne se charge que par cellules.
assert u.JadgSceneBuild.is_world_partition_streaming(world),'Streaming World Partition inactif'
report={'hlodActors':classes.get('WorldPartitionHLOD',0),'mainMap':'/Game/Capitale/Cartes/Capitale','worlds':worlds,'actorClasses':classes,'missingDependencies':missing,'runtimeStreaming':u.JadgSceneBuild.is_world_partition_streaming(world),'assetCount':len(assets)}
(O/'verification-finale.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('CAPITALE_REFERENCE_FINAL_OK',report,flush=True)
