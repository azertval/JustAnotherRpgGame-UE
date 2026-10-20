"""Outdoor traversal evidence on generated collision, using existing Recast tools.

This is an exterior 25cm navigation profile, not a validation of interiors or
small stairs. It belongs to this level and never saves project-wide settings.
"""
import json
from pathlib import Path


def road_surface_height(p, sample, layout):
    """Height of the actual one-metre road triangles, above the Landscape.

    A wide road spans the crossfall with triangles; its centre is not generally
    the bilinear Landscape height. Mirror the exported surface, not Recast's
    projection, so the walking check retains an independent height target.
    """
    import math
    x,y=p;result=sample(x,y)+.10
    for road in layout.ROADS:
        for a,b in zip(road['points'],road['points'][1:]):
            a,b=layout.metres(a),layout.metres(b)
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            t=((x-a[0])*dx+(y-a[1])*dy)/length**2
            cross=abs((x-a[0])*dy-(y-a[1])*dx)/length
            if not 0<=t<=1 or cross>road['width']/2:continue
            count=max(1,math.ceil(length));i=min(int(t*count),count-1)
            t0,t1=i/count,(i+1)/count;nx,ny=-dy/length,dx/length
            if sample(a[0]+dx*(t0+t1)/2,a[1]+dy*(t0+t1)/2)<layout.SEA_LEVEL+.4:continue
            across=math.ceil(road['width']);q=(x-a[0])*nx+(y-a[1])*ny
            j=max(0,min(int((q/road['width']+.5)*across),across-1))
            s0=(j/across-.5)*road['width'];s1=((j+1)/across-.5)*road['width']
            corners=[]
            for along,side in [(t0,s0),(t1,s0),(t1,s1),(t0,s1)]:
                xx=a[0]+dx*along+nx*side;yy=a[1]+dy*along+ny*side
                corners.append((xx,yy,sample(xx,yy)+.10))
            for ia,ib,ic in [(0,1,2),(0,2,3)]:
                aa,bb,cc=[corners[k] for k in (ia,ib,ic)]
                den=(bb[1]-cc[1])*(aa[0]-cc[0])+(cc[0]-bb[0])*(aa[1]-cc[1])
                wa=((bb[1]-cc[1])*(x-cc[0])+(cc[0]-bb[0])*(y-cc[1]))/den
                wb=((cc[1]-aa[1])*(x-cc[0])+(aa[0]-cc[0])*(y-cc[1]))/den
                wc=1-wa-wb
                if min(wa,wb,wc)>=-1e-7:result=max(result,wa*aa[2]+wb*bb[2]+wc*cc[2])
    return result


def build(level,frame,doc):
    import unreal
    import build_level as scene
    import capital_city_layout as city
    import capital_landscape_layout as layout
    from array import array
    root=Path(__file__).resolve().parents[2]
    report=root/'Saved/Jadg/capital-landscape'
    spec=json.loads((report/'relief.json').read_text())
    data=array('H');data.frombytes((report/'hauteurs.r16').read_bytes())
    def z(u,v):
        x,y=layout.metres((u,v));px=(x-spec['area'][0])/2;py=(y-spec['area'][1])/2
        i,j=int(px),int(py);a,b=px-i,py-j;w=spec['quads'][0]+1
        value=(data[j*w+i]*(1-a)+data[j*w+i+1]*a)*(1-b)+(data[(j+1)*w+i]*(1-a)+data[(j+1)*w+i+1]*a)*b
        return (value-32768)/128
    points=[]
    for key in city.GATES:
        u,v,*_=city.LANDMARKS[key]
        points.append((key,*layout.metres((u,v)),z(u,v)))
    for key,ends in layout.BRIDGES.items():
        if key=='aqueduct':continue
        for n,(u,v) in enumerate(ends):
            points.append((key+str(n),*layout.metres((u,v)),city.BRIDGE_LEVELS[key]))
    for key,uv in [('docks',(780,425)),('oldtown',(1400,190)),('palace-approach',(655,690)),
                   ('cathedral-parvis',(1215,812)),('university-approach',(1175,1180))]:
        points.append((key,*layout.metres(uv),z(*uv)))
    u,v=layout.ENTRY_UNITS
    start=frame.map_point([*layout.metres((u,v)),z(u,v)+.25])
    review=level.spawn(scene.game_class('JadgWitnessReview'),unreal.Vector(),unreal.Rotator(),
                       'CapitalOutdoorNavigation','controle')
    for prop,value in [('enable_cutaway',False),('ignore_camera_collision',False),('fine_navigation',True),
                       ('navigation_cell_size',25.),('navigation_cell_height',10.),
                       ('navigation_tile_size',9600.),('navigation_average_layers',8.),
                       ('navigation_max_search_nodes',65536)]:
        review.set_editor_property(prop,value)
    # Real runtime walking follows roads and palace stairs in the priority sectors.
    # Normal game speed and collision; no teleports and no movement acceleration.
    route_uv=[(1083,420),(1060,440),(1150,430),(1240,372),(1275,327),(1288,318),(1345,266),
              (1350,250),(1380,190),(1400,190),(1500,255),(1600,330),(1680,440),(1725,495),
              (1688,575),(1640,600),(1575,675),(1540,760),(1470,870),(1400,950),
              (1340,1000),(1285,1075),(1290,1140),(1280,1235),(1235,1230),(1210,1192),(1175,1180),
              (1160,1190),(1120,1168),(1110,1070),(1135,1010),(1180,950),(1160,950),(1000,935),
              (905,880),(790,920),(650,945),(527,948),(528,923.63636),(600,805),(690,790),(760,740),(800,640),
              (782,560),(772,602),(749,650),(728,688),(702,705),(680,700),(655,690),(645,686),
              (629,686),(598,694),(598,703),(598,718),(598,732),(598,743),(598,757)]
    import math
    from capital_urban_scene import distance_segment
    def walking_height(p):
        u,v=p
        if 628<=u<=645 and abs(v-686)<3.2:return 54+8*(u-628)/17+.04
        for t in city.GARDEN_TERRACES:
            if abs(u-t['centre'][0])<=t['halfSize'][0] and abs(v-t['centre'][1])<=t['halfSize'][1]:return t['z']+.05
        for a,b in zip(city.GARDEN_TERRACES,city.GARDEN_TERRACES[1:]):
            start=a['centre'][1]+a['halfSize'][1];end=b['centre'][1]-b['halfSize'][1]
            if abs(u-a['centre'][0])<3.2 and start<v<end:return a['z']+(b['z']-a['z'])*(v-start)/(end-start)+.04
        for name,(a,b) in layout.BRIDGES.items():
            if name=='aqueduct':continue
            if distance_segment(p,a,b)[0]*layout.METRES_PER_UNIT<4.5:
                return city.BRIDGE_LEVELS[name]+.035
        def sample_metres(x,y):
            return z(x/layout.METRES_PER_UNIT+layout.ARENA[0],y/layout.METRES_PER_UNIT+layout.ARENA[1])
        return road_surface_height(layout.metres(p),sample_metres,layout)
    route=[]
    for a,b in zip(route_uv,route_uv[1:]):
        count=max(1,math.ceil(math.dist(a,b)*layout.METRES_PER_UNIT/65))
        for n in range(count):
            t=n/count;p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
            route.append([*layout.metres(p),walking_height(p)])
    route.append([*layout.metres(route_uv[-1]),walking_height(route_uv[-1])])
    review.set_editor_property('route_points',[frame.map_point(p) for p in route])
    review.set_editor_property('walk_return',False)
    review.set_editor_property('leg_timeout',180.)
    review.set_editor_property('startup_timeout',600.)
    review.set_editor_property('height_tolerance',35.)
    (report/'runtime-route.json').write_text(json.dumps({'pointsMetres':route,'unrealAxes':frame.axes,'normalWalkSpeed':3.,
        'return':False,'lengthMetres':sum(math.dist(a,b) for a,b in zip(route,route[1:]))},indent=2))
    defaults=unreal.get_default_object(unreal.RecastNavMesh)
    old={k:defaults.get_editor_property(k) for k in ('average_layers_per_tile','tile_size_uu')}
    volumes=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    volumes=[a for a in volumes if isinstance(a,unreal.NavMeshBoundsVolume)]
    scales=[a.get_actor_scale3d() for a in volumes]
    defaults_restored=False
    try:
        defaults.set_editor_property('average_layers_per_tile',8.)
        defaults.set_editor_property('tile_size_uu',9600.)
        # Create Recast in a small volume before assigning its exterior profile;
        # avoid a needless full-city build at the engine's finer default size.
        for actor in volumes:actor.set_actor_scale3d(unreal.Vector(.02,.02,1.))
        unreal.JadgSceneBuild.unreachable_points(level.world,start,[])
        for k,value in old.items():defaults.set_editor_property(k,value)
        defaults_restored=True
        configured=review.prepare_fine_navigation()
    finally:
        if not defaults_restored:
            for k,value in old.items():defaults.set_editor_property(k,value)
        for actor,scale in zip(volumes,scales):actor.set_actor_scale3d(scale)
    # One full build and one batch for the destinations and the walking route.
    requested=[frame.map_point([x,y,h+.25]) for _,x,y,h in points]+[frame.map_point([x,y,h+.25]) for x,y,h in route]
    all_unreachable=list(unreal.JadgSceneBuild.unreachable_points(level.world,start,requested))
    unreachable=[i for i in all_unreachable if i<len(points)]
    route_unreachable=[i-len(points) for i in all_unreachable if i>=len(points)]
    if -1 in all_unreachable:route_unreachable=[-1]
    strict_failures=[]
    for i,p in enumerate(route):
        projected=unreal.NavigationSystemV1.project_point_to_navigation(level.world,frame.map_point(p),None,None,unreal.Vector(50,50,35))
        if projected is None:strict_failures.append(i)
    route_unreachable=sorted(set(route_unreachable+strict_failures))
    legs=[]
    for i,(a,b) in enumerate(zip(route,route[1:]),1):
        path=unreal.NavigationSystemV1.find_path_to_location_synchronously(level.world,frame.map_point(a),frame.map_point(b))
        pts=[frame.map_of_point(p) for p in path.path_points]
        direct=math.dist(a,b);length=sum(math.dist(p,q) for p,q in zip(pts,pts[1:]))
        legs.append({'toIndex':i,'directMetres':direct,'navigationMetres':length,'ratio':length/max(direct,.01),
                     'valid':path.is_valid(),'partial':path.is_partial()})
    route_bad=[]
    for i in route_unreachable:
        if i<0:continue
        x,y,h=route[i]
        p=unreal.NavigationSystemV1.project_point_to_navigation(level.world,frame.map_point([x,y,h+.25]),None,None,unreal.Vector(100,100,300))
        route_bad.append({'index':i,'requested':route[i],'projected':frame.map_of_point(p) if p is not None else None})
    projections=[]
    for name,x,y,h in [('start',start.x*.01,start.y*.01,start.z*.01)]+points:
        requested=frame.map_point([x,y,h+.25])
        projected=unreal.NavigationSystemV1.project_point_to_navigation(level.world,requested,None,None,unreal.Vector(100,100,300))
        projections.append({'id':name,'requested':[x,y,h],'projected':frame.map_of_point(projected) if projected is not None else None})
    result={'configured':configured,'profile':json.loads(review.get_navigation_settings_json()),'projections':projections,
            'points':[{'id':name,'position':[x,y,h],'reachable':i not in unreachable and -1 not in unreachable}
                      for i,(name,x,y,h) in enumerate(points)],'unreachableIndices':unreachable,
            'runtimeRoutePointCount':len(route),'unreachableRuntimeRouteIndices':route_unreachable,
            'unreachableRuntimeRouteDetails':route_bad,
            'strictRuntimeRouteProjectionFailures':strict_failures,
            'runtimeLegs':legs,
            'roadNavigation':[{ 'actor':a.get_actor_label(),'affectsNavigation':c.get_editor_property('can_ever_affect_navigation')}
                              for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if str(a.get_folder_path())=='roads'
                              for c in a.get_components_by_class(unreal.StaticMeshComponent)],
            'scope':'exterior pathfinding; no runtime walk or interior stair validation'}
    (report/'navigation-review.json').write_text(json.dumps(result,indent=2),encoding='utf8')


def refresh():
    """Recheck only navigation after a bounds/profile change; same scene builder."""
    import unreal
    import sys
    import hashlib
    root=Path(__file__).resolve().parents[2]
    sys.path.insert(0,str(root/'scripts/maps'));sys.path.insert(0,str(root/'scripts/assetsGeneration'))
    import build_level as scene
    import jadg_map
    import capital_landscape_layout as layout
    report=root/'Saved/Jadg/capital-landscape'
    path=root/'Source/Test/Fixtures/Exploration/Levels/capital-landscape/ensemble.json'
    water_only='-JadgWaterOnly' in unreal.SystemLibrary.get_command_line()
    shots_only='-JadgShotsOnly' in unreal.SystemLibrary.get_command_line()
    horizon_only='-JadgHorizonOnly' in unreal.SystemLibrary.get_command_line()
    civil_collision='-JadgCivilCollision' in unreal.SystemLibrary.get_command_line()
    dress_forge='-JadgDressForge' in unreal.SystemLibrary.get_command_line()
    dress_bridge='-JadgDressBridge' in unreal.SystemLibrary.get_command_line()
    dress_roads='-JadgDressRoads' in unreal.SystemLibrary.get_command_line()
    doc=jadg_map.read(path)
    frozen=json.loads((root/'scripts/maps/capital_comparison_shots.json').read_text())
    frozen={s['id']:s for s in frozen}
    from array import array
    spec=json.loads((report/'relief.json').read_text())
    heights=array('H');heights.frombytes((report/'hauteurs.r16').read_bytes());width=spec['quads'][0]+1
    for shot in doc['shots']:
        if shot['id'] in frozen:
            shot.update(frozen[shot['id']])
            continue
        source=next(s for s in layout.SHOTS if s['id']==shot['id'])
        for key in ('heading','pitch','distance'):shot[key]=source[key]
        x,y=layout.metres(source['target']);u=(x-spec['area'][0])/spec['resolution'];v=(y-spec['area'][1])/spec['resolution']
        i,j=int(u),int(v);a,b=u-i,v-j
        z=((heights[j*width+i]*(1-a)+heights[j*width+i+1]*a)*(1-b)+(heights[(j+1)*width+i]*(1-a)+heights[(j+1)*width+i+1]*a)*b-32768)/128
        shot['target']=[round(x,1),round(y,1),round(max(z,layout.SEA_LEVEL)+source.get('heightOffset',0),1)]
    doc['navigation']['area']=list(layout.metres((100,120)))+list(layout.metres((1950,1440)))
    path.write_text(jadg_map.dumps(doc),encoding='utf8')
    world=unreal.EditorLoadingAndSavingUtils.load_map('/Game/Maps/Levels/capital-landscape/ensemble')
    library=scene.Library()
    actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if horizon_only:
        import build_capital_landscape_scene as landscape_scene
        horizon_material=landscape_scene.terrain_material(scene,for_horizon=True)[0]
    for actor in actors.get_all_level_actors():
        if str(actor.get_folder_path())=='roads':
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                component.set_editor_property('can_ever_affect_navigation',actor.get_actor_label()!='road-oldtown-upper-lane')
                if dress_roads:
                    from capital_urban_scene import precise_civil_collision
                    materials=[component.get_material(i) for i in range(component.get_num_materials())]
                    mesh=library.static_mesh('Built/capital-urban/cu-'+actor.get_actor_label()+'.glb')
                    component.set_static_mesh(mesh);precise_civil_collision(mesh)
                    for i,material in enumerate(materials):component.set_material(i,material)
        if dress_forge and str(actor.get_folder_path())=='L08-03':actors.destroy_actor(actor);continue
        if dress_bridge and str(actor.get_folder_path())=='old-bridge':actors.destroy_actor(actor);continue
        if civil_collision and str(actor.get_folder_path()) in ('roads','road-retaining','terrace-gardens','monument-foundations','arching-bridge','old-bridge','eastern-bridge','L08-03'):
            from capital_urban_scene import precise_civil_collision
            for component in actor.get_components_by_class(unreal.StaticMeshComponent):
                if component.static_mesh:precise_civil_collision(component.static_mesh)
        if water_only and actor.get_actor_label().startswith('water-'):
            component=actor.static_mesh_component
            environment=actor.get_actor_label().removeprefix('water-')
            mesh=library.static_mesh(f'Built/capital-urban/cu-water-{environment}.glb')
            component.set_static_mesh(mesh)
            component.set_material(0,unreal.EditorAssetLibrary.load_asset(f'/Game/Capitale/Ressources/MI_Water_{environment}'))
            settings=component.static_mesh.get_editor_property('nanite_settings').copy();settings.enabled=False
            component.static_mesh.set_editor_property('nanite_settings',settings)
            component.set_editor_property('disallow_nanite',True)
            unreal.EditorAssetLibrary.save_loaded_asset(component.static_mesh)
        if horizon_only and actor.get_actor_label()=='horizon':
            component=actor.static_mesh_component
            component.set_static_mesh(library.static_mesh('Built/capital-urban/cu-horizon.glb'))
            for i in range(component.get_num_materials()):component.set_material(i,horizon_material)
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_editor_property('cast_shadow',False)
        if (civil_collision or dress_roads or not (water_only or shots_only or horizon_only)) and (isinstance(actor,unreal.NavMeshBoundsVolume) or actor.get_actor_label()=='CapitalOutdoorNavigation'):
            actors.destroy_actor(actor)
        if shots_only and actor.get_actor_label().startswith('Cadrage_'):
            actors.destroy_actor(actor)
    water=unreal.EditorAssetLibrary.load_asset('/Game/Capitale/Ressources/M_Eau')
    water.set_editor_property('two_sided',True)
    unreal.MaterialEditingLibrary.recompile_material(water);unreal.EditorAssetLibrary.save_loaded_asset(water)
    fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(root).as_posix())
    frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
    level=scene.Level(world)
    if dress_bridge:
        import capital_urban_scene as urban
        plan=json.loads((report/'urban-placement.json').read_text());groups={}
        for item in plan['objects']:
            if item['folder']=='old-bridge':groups.setdefault(item['mesh'],[]).append(item)
        for mesh_path,items in groups.items():
            mesh=library.static_mesh(mesh_path);urban.precise_civil_collision(mesh)
            transforms=[unreal.Transform(frame.map_point(o['position']),frame.rotation(o['yaw']),unreal.Vector(*o['scale'])) for o in items]
            actor=level.instances(mesh,transforms,'old-bridge-'+Path(mesh_path).stem,'old-bridge')
            component=actor.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
            for i,slot in enumerate(mesh.get_editor_property('static_materials')):
                name=str(slot.get_editor_property('imported_material_slot_name')) or str(slot.get_editor_property('material_slot_name'))
                material=unreal.EditorAssetLibrary.load_asset('/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_'+name)
                if material:component.set_material(i,material)
        engine=json.loads((report/'engine-built.json').read_text())
        engine['placedObjects']=len(plan['objects']);engine['uniqueMeshes']=len(set(o['mesh'] for o in plan['objects']))
        engine['instanceGroups']=len(set((o['folder'],o['mesh']) for o in plan['objects']))
        (report/'engine-built.json').write_text(json.dumps(engine,indent=2),encoding='utf8')
    if dress_forge:
        import capital_urban_scene as urban
        plan=json.loads((report/'urban-placement.json').read_text())
        item=next(o for o in plan['objects'] if o['folder']=='L08-03')
        mesh=library.static_mesh(item['mesh']);urban.precise_civil_collision(mesh)
        actor=level.spawn(mesh,frame.map_point(item['position']),frame.rotation(0),item['id'],'L08-03')
        # Reuse the established painted material family by imported slot name.
        for i,slot in enumerate(mesh.get_editor_property('static_materials')):
            name=str(slot.get_editor_property('imported_material_slot_name')) or str(slot.get_editor_property('material_slot_name'))
            material=unreal.EditorAssetLibrary.load_asset('/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_'+name)
            if material:actor.static_mesh_component.set_material(i,material)
        origin,extent=actor.get_actor_bounds(False)
        engine=json.loads((report/'engine-built.json').read_text())
        engine['placedObjects']=len(plan['objects']);engine['uniqueMeshes']=len(set(o['mesh'] for o in plan['objects']))
        engine['measuredBounds']=[b for b in engine['measuredBounds'] if b['reference']!='L08-03']+[{
            'reference':'L08-03','actor':item['id'],'minimumZMetres':(origin.z-extent.z)/100,
            'maximumZMetres':(origin.z+extent.z)/100,'widthMetres':extent.x*.02,'depthMetres':extent.y*.02}]
        (report/'engine-built.json').write_text(json.dumps(engine,indent=2),encoding='utf8')
    if '-JadgDressGardens' in unreal.SystemLibrary.get_command_line():
        terrace_actor=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='terrace-gardens')
        terrace_component=terrace_actor.static_mesh_component
        materials=[terrace_component.get_material(i) for i in range(terrace_component.get_num_materials())]
        terrace_component.set_static_mesh(library.static_mesh('Built/capital-urban/cu-terrace-gardens.glb'))
        for i,material in enumerate(materials):terrace_component.set_material(i,material)
        plan=json.loads((report/'urban-placement.json').read_text());groups={};bounds=[]
        for item in plan['objects']:
            if item['folder']=='L12-02':groups.setdefault(item['mesh'],[]).append(item)
        for mesh_path,items in groups.items():
            label='L12-02-'+Path(mesh_path).stem
            old=next(a for a in actors.get_all_level_actors() if a.get_actor_label()==label)
            component=old.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
            mesh=component.static_mesh;materials=[component.get_material(i) for i in range(component.get_num_materials())]
            actors.destroy_actor(old)
            transforms=[unreal.Transform(frame.map_point(o['position']),frame.rotation(o['yaw']),unreal.Vector(*o['scale'])) for o in items]
            actor=level.instances(mesh,transforms,label,'L12-02')
            component=actor.get_components_by_class(unreal.InstancedStaticMeshComponent)[0]
            for i,material in enumerate(materials):component.set_material(i,material)
            origin,extent=actor.get_actor_bounds(False)
            bounds.append({'reference':'L12-02','actor':label,'minimumZMetres':(origin.z-extent.z)/100,
                           'maximumZMetres':(origin.z+extent.z)/100,'widthMetres':extent.x*.02,'depthMetres':extent.y*.02})
        engine=json.loads((report/'engine-built.json').read_text())
        engine['placedObjects']=len(plan['objects'])
        engine['measuredBounds']=[b for b in engine['measuredBounds'] if b['reference']!='L12-02']+bounds
        (report/'engine-built.json').write_text(json.dumps(engine,indent=2),encoding='utf8')
    if shots_only:scene.place_shots(level,doc,frame)
    obsolete='/Game/Capitale/Ressources/MI_Horizon'
    if unreal.EditorAssetLibrary.does_asset_exist(obsolete):
        used=any(component.get_material(i) and component.get_material(i).get_path_name().split('.')[0]==obsolete
                 for actor in actors.get_all_level_actors()
                 for component in actor.get_components_by_class(unreal.StaticMeshComponent)
                 for i in range(component.get_num_materials()))
        if not used:unreal.EditorAssetLibrary.delete_asset(obsolete)
    if civil_collision or dress_roads or not (water_only or shots_only or horizon_only):
        scene.place_navigation(level,doc,frame);build(level,frame,doc)
    if not unreal.EditorLoadingAndSavingUtils.save_map(world,'/Game/Maps/Levels/capital-landscape/ensemble'):
        raise RuntimeError('Could not save navigation revision')
    digest,records=scene.footprint(world)
    source_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    for name in ('relief','build'):
        data=json.loads((report/(name+'.json')).read_text());data['levelSha256']=source_hash
        if name=='build':data['digest']=digest;data['actors']=len(records)
        (report/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf8')
    scene.write_footprint('capital-landscape/ensemble',digest,records,{'navigationRefresh':True})


if __name__=='__main__':refresh()
