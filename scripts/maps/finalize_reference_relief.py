import unreal as u
import json
from pathlib import Path
from collections import Counter
from array import array
P=Path(u.Paths.project_dir()).resolve();D=P/'Source/Elements/Terrain/capital/relief-reference'
package='/Game/Capitale/Cartes/Capitale'
world=u.EditorLoadingAndSavingUtils.load_map(package)
assert world
assert u.JadgSceneBuild.set_world_partition_streaming(world,False)
desc=u.WorldPartitionBlueprintLibrary.get_actor_descs()
u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in desc])
A=u.get_editor_subsystem(u.EditorActorSubsystem);actors=A.get_all_level_actors()
terrain=[a for a in actors if isinstance(a,u.LandscapeProxy)]
result=[]
for a in terrain:
 a.set_editor_property('enable_nanite',True)
 if len(a.get_components_by_class(u.LandscapeComponent)):
  if not u.JadgSceneBuild.is_landscape_nanite_current(a):assert u.JadgSceneBuild.build_landscape_nanite(a)
  tris=sum(c.static_mesh.get_num_nanite_triangles() for c in a.get_components_by_class(u.LandscapeNaniteComponent) if c.static_mesh)
  assert tris>0,a.get_actor_label()
  result.append({'label':a.get_actor_label(),'components':len(a.get_components_by_class(u.LandscapeComponent)),'naniteTriangles':tris})
  assert u.EditorLoadingAndSavingUtils.save_packages([a.get_package()],False)
  print('REFERENCE_PROXY_VERIFIED',len(result),a.get_actor_label(),tris,flush=True)
for a in actors:
 if a.get_class().get_name() in ['JadgShot','JadgDayLight','JadgMapFrame']:
  a.set_editor_property('is_spatially_loaded',False)
water=[a for a in actors if isinstance(a,u.StaticMeshActor)]
assert len(water)==len(json.loads((D/'water/manifest.json').read_text(encoding='utf-8')))
assert all('CapitaleEauReference' in [str(t) for t in a.tags] for a in water)
assert not any(isinstance(a,u.InstancedFoliageActor) for a in actors)
assert not any(isinstance(a,u.TargetPoint) for a in actors)
mi=u.EditorAssetLibrary.load_asset('/Game/Capitale/Ressources/ReliefReference/MI_TerrainNaturel')
assert mi.get_editor_property('parent').get_name()=='M_TerrainNaturel'
assert all(a.get_editor_property('landscape_material')==mi for a in terrain if isinstance(a,u.Landscape))
checks=[]
for t in json.loads((D/'manifest.json').read_text(encoding='utf-8'))['tiles']:
 hs=array('H');hs.frombytes((D/(t['id']+'.r16')).read_bytes())
 for ix,iy in [(32,32),(252,252),(472,472)]:
  x=t['origin'][0]+ix*2;y=t['origin'][1]+iy*2;expected=(hs[iy*505+ix]-32768)/128
  hit=u.SystemLibrary.line_trace_single(world,u.Vector(x*100,y*100,30000),u.Vector(x*100,y*100,-5000),u.TraceTypeQuery.ECC_VISIBILITY,True,[],u.DrawDebugTrace.NONE,True)
  values=hit.to_tuple() if hit else None;actual=values[5].z/100 if values and values[0] else None
  assert actual is not None and abs(actual-expected)<.04,(t['id'],expected,actual)
  checks.append(dict(tile=t['id'],xy=[x,y],expected=expected,actual=actual))
packages=list({a.get_package().get_name():a.get_package() for a in actors}.values())
assert u.EditorLoadingAndSavingUtils.save_packages(packages,False)
assert u.EditorLoadingAndSavingUtils.save_map(world,package)
report={'map':package,'worldPartition':True,'runtimeStreaming':False,'counts':dict(Counter(a.get_class().get_name() for a in actors)),'terrain':result,'waterMeshes':len(water),'roads':0,'buildings':0,'vegetation':0,'buildingSites':0,'naniteTriangles':sum(r['naniteTriangles'] for r in result),'heightChecks':checks}
(P/'Saved/Jadg/relief-reference-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('REFERENCE_AUDIT_READY',report,flush=True)
# The reconstruction world was duplicated into Capitale; the renamer may leave its source behind.
for leftover in ['/Game/Capitale/Cartes/Capitale_Reconstruction']:
 if u.EditorAssetLibrary.does_asset_exist(leftover):assert u.EditorAssetLibrary.delete_asset(leftover),leftover
