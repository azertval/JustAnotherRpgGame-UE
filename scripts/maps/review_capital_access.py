"""Localize a disconnected exterior road without modifying the saved level."""
import sys
import json
import math
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/maps'))
sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import capital_landscape_layout as layout  # noqa: E402
import build_level as scene  # noqa: E402
from array import array  # noqa: E402

world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/Levels/capital-landscape/ensemble')
fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
report=ROOT/'Saved/Jadg/capital-landscape'
spec=json.loads((report/'relief.json').read_text());heights=array('H');heights.frombytes((report/'hauteurs.r16').read_bytes())
def ground(u,v):
    x,y=layout.metres((u,v));i=round((x-spec['area'][0])/2);j=round((y-spec['area'][1])/2)
    return (heights[j*(spec['quads'][0]+1)+i]-32768)/128
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
review=next(a for a in actors if a.get_actor_label()=='CapitalOutdoorNavigation')
review.prepare_fine_navigation()
points=[]
for road in layout.ROADS:
    if road['id'] not in ('hudlodge-route','sloghood-gate-lane','knights-avenue-uptown'):continue
    for a,b in zip(road['points'],road['points'][1:]):
        n=math.ceil(math.dist(a,b)*layout.METRES_PER_UNIT/12)
        for i in range(n+1):
            u=a[0]+(b[0]-a[0])*i/n;v=a[1]+(b[1]-a[1])*i/n
            z=2 if road['id']=='hudlodge-route' and 197<u<274 else ground(u,v)
            points.append({'road':road['id'],'plan':[u,v],'ground':z,'world':[*layout.metres((u,v)),z+.25]})
start=frame.map_point([*layout.metres(layout.ENTRY_UNITS),.25])
bad=list(unreal.JadgSceneBuild.unreachable_points(world,start,[frame.map_point(p['world']) for p in points]))
for i,p in enumerate(points):
    p['reachable']=i not in bad and -1 not in bad
    result=unreal.NavigationSystemV1.project_point_to_navigation(world,frame.map_point(p['world']),None,None,unreal.Vector(100,100,300))
    p['projected']=frame.map_of_point(result) if result is not None else None
(report/'access-diagnostic.json').write_text(json.dumps(points,indent=2),encoding='utf8')
print('Access diagnostics written:',len(points),'points,',len(bad),'unreachable')
