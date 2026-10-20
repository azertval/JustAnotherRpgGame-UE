"""Read-only collision/path diagnostic for a recorded physical traversal failure."""
import sys
import json
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/maps'));sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import build_level as scene  # noqa: E402
report=ROOT/'Saved/Jadg/capital-landscape'
walk=json.loads((report/'runtime-walk.json').read_text(encoding='utf-8-sig'))
route=json.loads((report/'runtime-route.json').read_text())['pointsMetres']
index=walk['pointsReached']
world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/Levels/capital-landscape/ensemble')
fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
disabled=[]
if '-JadgDiagnosisNoForge' in unreal.SystemLibrary.get_command_line():
    for actor in actors:
        if str(actor.get_folder_path())=='L08-03':
            disabled.append(actor.get_actor_label())
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
review=next(a for a in actors if a.get_actor_label()=='CapitalOutdoorNavigation')
start=frame.map_point(route[index-1]);target=frame.map_point(route[index])
result={'point':index,'paths':{},'temporarilyDisabled':disabled,'traceApi':unreal.SystemLibrary.line_trace_single.__doc__}
trace_only='-JadgTraceOnly' in unreal.SystemLibrary.get_command_line()
if not trace_only:
    review.prepare_fine_navigation()
    unreal.JadgSceneBuild.unreachable_points(world,start,[target])
for name,extent in ([] if trace_only else [('strict',unreal.Vector(50,50,35)),('party',unreal.Vector(200,200,400))]):
    goal=unreal.NavigationSystemV1.project_point_to_navigation(world,target,None,None,extent)
    path=unreal.NavigationSystemV1.find_path_to_location_synchronously(world,start,goal)
    result['paths'][name]={'goal':frame.map_of_point(goal),'points':[frame.map_of_point(p) for p in path.path_points]}
result['traces']=[]
result['actorLabels']={a.get_path_name():a.get_actor_label() for a in actors}
feet=unreal.Vector(*walk['samples'][-1]['feetCm'])
for name,p in [('target',target),('stopped',feet)]:
    for axis,delta in [('vertical',unreal.Vector(0,0,3000)),('x',unreal.Vector(200,0,0)),('y',unreal.Vector(0,200,0))]:
        base=p+unreal.Vector(0,0,70)
        try:
            hit=unreal.SystemLibrary.line_trace_single(world,base+delta,base-delta,unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE,True)
            data=hit.to_tuple() if hasattr(hit,"to_tuple") else hit if hit else None
            result['traces'].append({'name':name,'axis':axis,'hit':str(data)})
        except Exception as error:result['traces'].append({'name':name,'axis':axis,'error':str(error)})
if trace_only:
    probes=json.loads((report/'walk-failure-probes.json').read_text())
    for i,p in enumerate(probes):
        a=frame.map_point(p);b=a+unreal.Vector(0,0,2500)
        hit=unreal.SystemLibrary.line_trace_single(world,b,a-unreal.Vector(0,0,100),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,True,[],unreal.DrawDebugTrace.NONE,True)
        result['traces'].append({'probe':i,'requested':p,'hit':str(hit.to_tuple() if hasattr(hit,"to_tuple") else hit) if hit else None})
(report/('walk-failure-traces.json' if trace_only else 'walk-failure-diagnostic.json')).write_text(json.dumps(result,indent=2),encoding='utf8')
print('Physical failure diagnostic written for point',index)
