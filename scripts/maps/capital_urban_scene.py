"""Urban placement and evidence on the single global Landscape.

Existing district pieces keep their physical dimensions. Named ensembles are
translated as rigid groups from local anchors to surveyed global anchors;
street distances, ground and scattered residential plots are regenerated.
"""
from pathlib import Path
import json
import math
import random
import hashlib
import capital_landscape_layout as layout
import capital_city_layout as city

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'Saved/Jadg/capital-landscape'
ASSETS=ROOT/'Source/Elements/Assets'
REFS=Path('D:/Codex/2026-10-11/references-capitale/collection')


def distance_segment(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy),t


def prepare(terrain):
    rng=random.Random(layout.SEED)
    objects=[];footprints=[];transforms=[]
    def h(u,v):return terrain.height_at(*layout.metres((u,v)))
    def put(identifier,mesh,u,v,z=None,yaw=0,scale=None,group='urban',surface=None):
        x,y=layout.metres((u,v))
        item={'id':identifier,'mesh':mesh,'position':[x,y,h(u,v) if z is None else z],
              'yaw':yaw,'folder':group,'scale':scale or [1,1,1]}
        if surface:item['surface']=surface
        objects.append(item)
        return item
    def built(name):return f'Built/capital-urban/cu-{name}.glb'
    def source(d,name):return f'Built/{d}-district/{name}.glb'
    manifests={d:json.loads((ASSETS/f'Built/{d}-district/manifest.json').read_text()) for d in ('arenarea','martpart')}
    def rigid(identifier,d,predicate,anchor,offset=(0,0)):
        u,v,z,*_=city.LANDMARKS[identifier];gx,gy=layout.metres((u,v))
        gx+=offset[0];gy+=offset[1]
        destination_z=h(u,v)
        count=0
        for o in manifests[d]['objects']:
            if not predicate(o):continue
            p=o['position'];mesh=o.get('mesh') or source(d,o['meshId'])
            item={'id':identifier+'-'+o['id'],'mesh':mesh,
                  'position':[gx+p[0]-anchor[0],gy+p[1]-anchor[1],destination_z+p[2]-anchor[2]],
                  'yaw':o.get('yaw',0),'scale':o.get('scale',[1,1,1]),'folder':identifier}
            objects.append(item);count+=1
        transforms.append({'reference':identifier,'sourceDistrict':d,'sourceAnchorMetres':anchor,
                           'globalAnchorMetres':[gx,gy,destination_z],
                           'translation':[gx-anchor[0],gy-anchor[1],destination_z-anchor[2]],
                           'rotationDegrees':0,'scale':1,'objects':count,
                           'artisticOffsetMetres':list(offset),
                           'method':'rigid ensemble; roads and terrain regenerated at global scale'})
    # Main Arena is unmodified, including its sculpted visible assembly.
    rigid('L07-01','arenarea',lambda o:o['id'].startswith('reused-') and o['position'][2]>=0,[0,-65,0])
    rigid('L07-02','arenarea',lambda o:o.get('meshId','').startswith('ard-golden-chalice'),[-53,182,7.4])
    rigid('L07-04','arenarea',lambda o:o.get('meshId','').startswith('ard-dusk-of-justice'),[0,76,1],offset=(-38,0))
    rigid('L07-03','arenarea',lambda o:o.get('meshId','') in ('ard-track','ard-stand','ard-stand-roof'),[148,185,4.5])
    # Hall and round arena remain separate, no affine distortion of their architecture.
    for key,pieces in [('L06-01',['mp-hall','mp-hall-roof']),('L06-02',['mp-illu-die','mp-illu-canopy'])]:
        u,v,*_=city.LANDMARKS[key]
        for name in pieces:put(key+'-'+name,source('martpart',name),u,v,group=key)
    # Proposed civic silhouettes. Reported heights come from meshes in the engine,
    # not from this starting range alone.
    special={'L11-01':'cathedral','L12-01':'palace','L05-01':'arcane-tower',
             'L04-01':'university','L04-02':'museum','L04-04':'forum','L05-03':'manor-court','L08-03':'stonebreaker-forge',
             'X14':'watchtower','X15':'fortress','X16':'fortress','X19':'fortress'}
    skip={'L07-01','L07-02','L07-03','L07-04','L06-01','L06-02','L07-06','L09-03',
          'L12-02','L08-01','X12','X13','X07','X08','X09','X10','X20'}
    for key,(u,v,z,_facade,_roof,_total) in city.LANDMARKS.items():
        if u is None or key in skip or key in city.GATES:continue
        if key in special:
            put(key,built(special[key]),u,v,z=z if key=='L08-03' else None,group=key)
        elif key=='L09-01':
            for piece in ['mp-illu-die','mp-illu-canopy']:
                put(key+'-'+piece,source('martpart',piece),u,v,scale=[.7,.7,.65],group=key)
        elif key=='L06-03':put(key,source('martpart','mp-shaft-garden'),u,v,group=key)
        elif key in ('L02-01','L04-01','L04-02','L04-03','L04-04','L11-02','L11-03','L12-03','L12-05','X11'):
            scale= .75 if key=='L04-02' else 1.0
            put(key,built('civic-hall'),u,v,scale=[scale,scale,scale],group=key)
        elif key=='X17':
            # Ruins use open remains, not a populated castle.
            for i in range(5):put(f'{key}-ruin-{i}',built('retaining'),u+i*7,v+i%2*6,scale=[1,1,2.4-i*.3],group=key)
        elif key=='X18':
            put(key+'-mine-mouth',source('arenarea','ard-neighbour-gate'),u,v,scale=[.5,.6,.4],group=key)
        else:
            n=int(hashlib.sha256(key.encode()).hexdigest()[:4],16)%6
            for piece in (f'ard-house-{n}',f'ard-house-roof-{n}'):
                put(key+'-'+piece,source('arenarea',piece),u,v,group=key)
        footprints.append((u,v,45 if key in special and key!='L08-03' else 26))
    # Reserve EVERY named ensemble, pool, palace garden and arena apron.
    for key,(u,v,_z,*_) in city.LANDMARKS.items():
        if u is None:continue
        radius=110 if key=='L07-01' else 92 if key=='L07-03' else 60 if key=='L12-01' else 35
        footprints.append((u,v,radius))
    # Gates follow their access axes and stand on the same threshold as the road.
    for key,(a,b) in city.GATES.items():
        u,v,*_=city.LANDMARKS[key]
        yaw=-math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))+90
        put(key,source('arenarea','ard-gate'),u,v,yaw=yaw,group='gates')
    # Segmented walls have real footings and coping. Openings are removed, not
    # covered by gate facades. Gate width + clear shoulder is 26m.
    for name,poly in [('city-wall',layout.CITY_WALL),('palace-wall',layout.PALACE_WALL)]:
        for s,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])):
            length=math.dist(a,b)*layout.METRES_PER_UNIT
            count=max(1,math.ceil(length/12));step=length/count
            yaw=-math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
            for n in range(count):
                t=(n+.5)/count;u=a[0]+(b[0]-a[0])*t;v=a[1]+(b[1]-a[1])*t
                if any(math.dist((u,v),city.LANDMARKS[k][:2])*layout.METRES_PER_UNIT<20 for k in city.GATES):continue
                if name=='palace-wall' and math.dist((u,v),(782,560))*layout.METRES_PER_UNIT<17:continue
                ta,tb=n/count,(n+1)/count
                za=h(a[0]+(b[0]-a[0])*ta,a[1]+(b[1]-a[1])*ta)
                zb=h(a[0]+(b[0]-a[0])*tb,a[1]+(b[1]-a[1])*tb)
                low,high=min(za,zb),max(za,zb)
                put(f'{name}-{s}-{n}',built('curtain'),u,v,z=high-.3,yaw=yaw,
                    scale=[step/12,1,.85 if name=='palace-wall' else 1],group=name)
                if high-low>1:
                    put(f'{name}-footing-{s}-{n}',built('footing'),u,v,z=low-.6,yaw=yaw,
                        scale=[step,2.8,high-low+.8],group='foundations')
    for name,(a,b) in layout.BRIDGES.items():
        # Surveyed ends extend 12m onto dry abutments without filling the channel.
        dx,dy=b[0]-a[0],b[1]-a[1];unit=math.hypot(dx,dy)
        ax,ay=a[0]-dx/unit*10,a[1]-dy/unit*10
        bx,by=b[0]+dx/unit*10,b[1]+dy/unit*10
        length=math.dist((ax,ay),(bx,by))*layout.METRES_PER_UNIT
        count=math.ceil(length/12);yaw=-math.degrees(math.atan2(dy,dx))
        for i in range(count):
            t=(i+.5)/count
            piece='aqueduct' if name=='aqueduct' else 'bridge'
            if name=='old-bridge':
                # The diagonal bank roads join through open abutments; continuous
                # parapets here used to close both approaches to the deck.
                if i in (0,count-1):piece='bridge-open'
                elif i==1:piece='bridge-entry'
                elif i==count-2:piece='bridge-exit'
            put(f'{name}-{i}',built(piece),ax+(bx-ax)*t,ay+(by-ay)*t,
                z=city.BRIDGE_LEVELS[name],yaw=yaw,scale=[length/count/12,.40 if name=='aqueduct' else 1,1],group=name)
    # Quays grow seaward from the existing dry dock frontage.
    for i in range(9):
        u=655+i*19
        for j in range(3):put(f'dock-{i}-{j}',built('pier'),u,396-j*10,z=1.2,group='Q13')
    # The inhabited street outside Market Gate must not disappear into a
    # gate-to-bridge shortcut. Two frontages leave the merchant carriageway open.
    a,b=(1589,658),(1677,590)
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
    for n in range(6):
        t=(n+.5)/6
        for side in (-1,1):
            u=a[0]+dx*t-dy/length*18*side;v=a[1]+dy*t+dx/length*18*side
            if h(u,v)<.5:continue
            for piece in (f'mp-shop-{n%3}-2',f'mp-roof-{n%3}-2'):
                put(f'market-exterior-{n}-{side}-{piece}',source('martpart',piece),u,v,
                    yaw=-math.degrees(math.atan2(dy,dx))+90,group='market-exterior')
    # The cemetery is an open burial ground with its own tower, not a house.
    for row in range(6):
        for column in range(7):
            u=1400+(column-3)*4;v=166+(row-2.5)*5
            put(f'cemetery-{row}-{column}',built('grave'),u,v,group='L08-01')
    put('moon-tower',built('moon-tower'),1419,145,group='L08-01')
    # Residential parcels follow each irregular district boundary. Access strips
    # and gardens are deliberately left between them, with deterministic seeds.
    for key,(_name,poly,spacing,kind) in city.REGIONS.items():
        if kind=='garden':continue
        minx=min(p[0] for p in poly);maxx=max(p[0] for p in poly)
        miny=min(p[1] for p in poly);maxy=max(p[1] for p in poly)
        count=0
        v=miny+spacing/2
        while v<maxy:
            u=minx+spacing/2
            while u<maxx:
                px=u+rng.uniform(-spacing*.17,spacing*.17);py=v+rng.uniform(-spacing*.17,spacing*.17)
                u+=spacing
                if not city.inside(px,py,poly):continue
                if any(math.dist((px,py),(a,b))<r for a,b,r in footprints):continue
                if any(distance_segment((px,py),a,b)[0]*layout.METRES_PER_UNIT<road['width']/2+12
                       for road in layout.ROADS for a,b in zip(road['points'],road['points'][1:])):continue
                z=h(px,py)
                corners=[h(px+dx,py+dy) for dx,dy in [(8,7),(-8,7),(8,-7),(-8,-7)]]
                if z<1 or max(corners)-min(corners)>5.0:continue
                base=max(corners)+.06
                n=count%6;count+=1
                nearby=min(((distance_segment((px,py),a,b)[0],a,b) for road in layout.ROADS
                            for a,b in zip(road['points'],road['points'][1:])),key=lambda t:t[0])
                yaw=-math.degrees(math.atan2(nearby[2][1]-nearby[1][1],nearby[2][0]-nearby[1][0]))+rng.choice([0,0,5,-5])
                if kind in ('shop','workshop','warehouse','farm'):
                    floor=2 if key in ('Q01','Q09','Q10','Q13') else (2+count%2)
                    meshes=[source('martpart',f'mp-shop-{count%3}-{floor}'),source('martpart',f'mp-roof-{count%3}-{floor}')]
                else:meshes=[source('arenarea',f'ard-house-{n}'),source('arenarea',f'ard-house-roof-{n}')]
                for m in meshes:put(f'{key}-home-{count}-{Path(m).stem}',m,px,py,z=base,yaw=yaw,group=key)
                # A local constructed plinth supports the house; no district-scale flattening.
                put(f'{key}-home-{count}-footing',built('footing'),px,py,z=min(corners)-.45,yaw=yaw,
                    scale=[21,18,base-min(corners)+.45],group='foundations')
                if kind in ('manor','civic'):
                    put(f'{key}-garden-{count}',source('arenarea','ard-cypress'),px+9,py+8,group=key)
            v+=spacing
    # Planted woodland follows mapped substrata, with exclusions for all works.
    for n in range(18000):
        u=rng.uniform(-100,2170);v=rng.uniform(0,1440)
        forest=any(city.inside(u,v,poly) for poly in layout.FORESTS)
        garden=city.inside(u,v,layout.PALACE_WALL)
        if not (forest or garden):continue
        if garden and 558<u<638 and 668<v<782:continue
        if any(math.dist((u,v),(a,b))<r+6 for a,b,r in footprints):continue
        if any(distance_segment((u,v),a,b)[0]*layout.METRES_PER_UNIT<road['width']/2+9
               for road in layout.ROADS for a,b in zip(road['points'],road['points'][1:])):continue
        if h(u,v)<-.5:continue
        scale=rng.uniform(1.7,3.0) if not garden else rng.uniform(1.25,2.0)
        put(f'grove-{n}',source('arenarea','ard-cypress' if garden or n%3==0 else 'ard-noble-tree'),u,v,
            yaw=rng.uniform(0,360),scale=[scale]*3,group='vegetation')
    # Repeated raised beds, fountains and benches make the botanical garden
    # legible without inventing a monumental hydraulic source for Natural Pool.
    for row,t in enumerate(city.GARDEN_TERRACES):
        for col,offset in enumerate(t['halfSize'][0]*f for f in (-.55,.55)):
            u=t['centre'][0]+offset;v=t['centre'][1]
            put(f'palace-bed-{row}-{col}',source('arenarea','ard-garden-bed'),u,v,z=t['z']+.05,scale=[1.8,1.8,1],group='L12-02')
            put(f'palace-tree-{row}-{col}',source('arenarea','ard-cypress'),u,v+7,z=t['z']+.05,scale=[1.6,1.6,1.6],group='L12-02')
            put(f'palace-bench-{row}-{col}',source('arenarea','ard-bench'),u,v-7,z=t['z']+.05,group='L12-02')
    for i,(u,v) in enumerate(t['centre'] for t in city.GARDEN_TERRACES):
        put(f'palace-fountain-{i}',source('arenarea','ard-fountain'),u,v,z=city.GARDEN_TERRACES[i]['z']+.05,group='L12-02')
    # Built road strips are exported on the exact sampled Landscape surface.
    for road in layout.ROADS:
        objects.append({'id':'road-'+road['id'],'mesh':built('road-'+road['id']),
                        'position':[0,0,0],'yaw':0,'scale':[1,1,1],'folder':'roads'})
    # Civil works are generated from the encoded surface, grouped by district.
    for name in ('road-retaining','terrace-gardens','monument-foundations','horizon'):
        objects.append({'id':name,'mesh':built(name),'position':[0,0,0],'yaw':0,'scale':[1,1,1],'folder':name})
    footings=[o for o in objects if o['mesh']==built('footing')]
    objects=[o for o in objects if o['mesh']!=built('footing')]
    report={'version':2,'seed':layout.SEED,'objects':objects,'foundations':footings,'transformations':transforms,
            'referenceMap':'capital_city_layout.py','provisional':['secondary civic interiors',
                'Praharebaagh statue asset not yet represented','underground sites have no invented entrance',
                'house-to-secondary-lane traversal not yet verified']}
    (REPORT/'urban-placement.json').write_text(json.dumps(report,indent=1),encoding='utf8')
    write_evidence(terrain,report)
    return report


def write_evidence(terrain,scene):
    from review_capital_navigation import road_surface_height
    entries=[]
    revisions={
        'L12-01':'Proposed floor 62m; faceted rotunda, galleries and constructed foundations',
        'L12-02':'Three built garden terraces at 54/45/36m, linked by stairs; separate upper stair to the palace',
        'L04-01':'Proposed floor 46m; marble arcades and two wings around an open courtyard',
        'L04-02':'Distinct museum hall with columned portico and pediment',
        'L04-04':'Distinct circular forum and front colonnade',
        'L05-03':'Distinct court and two manor wings',
        'L08-03':'Compact working forge, 14x16m, proposed floor 27m, two chimneys and an open arched entry; replaces generic manor',
        'X08':'Open parapets at the diagonal bank approaches; continuous central bridge parapets and deck retained'}
    for path in sorted(REFS.glob('*/reference.json')):
        ref=json.loads(path.read_text(encoding='utf-8-sig'));key=ref['id']
        if key.startswith('Q'):
            name,poly,_,_=city.REGIONS[key];anchor=[sum(p[i] for p in poly)/len(poly) for i in (0,1)]
            kind='district';coordinates={'polygonPlan':poly}
        else:
            anchor=list(city.LANDMARKS[key][:2]);kind='underground' if key in ('X12','X13') else 'landscape' if key in ('L07-06','L09-03','L12-02') else 'ensemble'
            coordinates={'anchorPlan':anchor}
        folders={'X01':'gates','X02':'gates','X03':'gates','X04':'gates','X05':'gates','X06':'gates',
                 'X07':'arching-bridge','X08':'old-bridge','X09':'aqueduct','X10':'eastern-bridge'}
        matching=[o['id'] for o in scene['objects'] if o['folder']==folders.get(key,key)
                  and (key not in city.GATES or o['id']==key)]
        status=('reserved, not built' if kind=='underground' or key=='X20' else
                'terrain region; landscape and planting' if kind in ('district','landscape') else
                'proposed assembled silhouette' if matching else 'not represented')
        entries.append({'id':key,'name':ref['name'],'sceneKind':kind,**coordinates,
                        'positionEvidence':'source-map survey, +/-15 plan units; proposals where no precise site is attested',
                        'bookAndMapFacts':ref.get('source_facts',[]),'sourceRelations':ref.get('connections',[]),
                        'referenceSources':ref.get('sources',[]),
                        'projectDecisionSources':[s for s in ref.get('sources',[]) if s.get('label')=='PROJET'],
                        'revisionDecisions':['2026-10-13: preserve global grid and sea datum; height revisions explicitly authorized',
                          'Relief revision: narrow platforms, route-specific grades, elongated urban ridges, constructed foundations']+([revisions[key]] if key in revisions else []),
                        'artisticPlacementAdjustments':[t for t in scene.get('transformations',[]) if t['reference']==key],
                        'artisticProposals':ref.get('proposals',[]),
                        'uncertainties':ref.get('uncertainties',[]),
                        'source':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'placementIds':matching,'meshSources':sorted(set(o['mesh'] for o in scene['objects'] if o['id'] in matching)),'status':status,
                        'fidelity':'individual architecture not yet approved against the reference'})
    if len(entries)!=80:raise RuntimeError(f'Expected 80 references, got {len(entries)}')
    (REPORT/'references-80.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),encoding='utf8')
    heights=[]
    for key,(u,v,z,facade,roof,total) in city.LANDMARKS.items():
        if u is None or z is None:continue
        ground=terrain.height_at(*layout.metres((u,v)))
        approaches={'L12-01':(655,690),'L11-01':(1215,812),'L04-01':(1175,1180)}
        street=approaches.get(key)
        if street is None:
            nearest=min(((distance_segment((u,v),a,b),a,b) for road in layout.ROADS for a,b in zip(road['points'],road['points'][1:])),key=lambda r:r[0][0])
            (_,t),a,b=nearest;street=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
        street_height=road_surface_height(layout.metres(street),terrain.height_at,layout)
        bridge_for={'X07':'arching-bridge','X08':'old-bridge','X09':'aqueduct','X10':'eastern-bridge'}
        if key in bridge_for:street_height=city.BRIDGE_LEVELS[bridge_for[key]]
        heights.append({'id':key,'terrainMetres':round(ground,3),'streetMetres':round(street_height,3),'streetSamplePlan':street,
                        'streetSampleMethod':'exported road triangle surface at explicit approach or nearest surveyed road; no undocumented access inferred',
                        'thresholdMetres':round(ground,3),'facadeProposalMetres':facade,'roofProposalMetres':roof,
                        'totalProposalMetres':total,'summitProposalAbsolute':round(ground+total,3),
                        'status':'proposal; measured mesh bounds are recorded in engine-built.json'})
    (REPORT/'heights-design.json').write_text(json.dumps(heights,indent=2),encoding='utf8')


def precise_civil_collision(mesh):
    """Thin, curved civil surfaces need the full mesh in the collision fallback."""
    import unreal
    settings=mesh.get_editor_property('nanite_settings').copy()
    if settings.fallback_target==unreal.NaniteFallbackTarget.PERCENT_TRIANGLES and settings.fallback_percent_triangles==1. and settings.fallback_relative_error==0.:return
    settings.fallback_target=unreal.NaniteFallbackTarget.PERCENT_TRIANGLES
    settings.fallback_percent_triangles=1.
    settings.fallback_relative_error=0.
    mesh.set_editor_property('nanite_settings',settings)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)


def build_editor(level,frame,library,water_parent):
    import unreal
    import build_level as scene
    import build_capital_districts as districts
    import capital_surface_materials as finishes
    ml=unreal.MaterialEditingLibrary
    plan=json.loads((REPORT/'urban-placement.json').read_text())
    bases={d:districts.district_materials(json.loads((ASSETS/f'Built/{d}-district/manifest.json').read_text()))
           for d in ('arenarea','martpart')}
    palette=dict(bases['arenarea']);palette.update(bases['martpart'])
    palette.update(finishes.instances())
    import build_capital_landscape_scene as landscape_scene
    horizon_material=landscape_scene.terrain_material(scene,for_horizon=True)[0]
    meshes={};groups={};bounds=[]
    for item in plan['objects']:
        key=(item['mesh'],item['folder'])
        groups.setdefault(key,[]).append(item)
    for (path,folder),items in groups.items():
        if path not in meshes:meshes[path]=library.static_mesh(path)
        mesh=meshes[path]
        if folder in ('roads','road-retaining','terrace-gardens','monument-foundations','arching-bridge','old-bridge','eastern-bridge','L08-03'):
            precise_civil_collision(mesh)
        transforms=[]
        for item in items:
            scale=item.get('scale',[1,1,1]);scale=[scale]*3 if isinstance(scale,(int,float)) else scale
            transforms.append(unreal.Transform(frame.map_point(item['position']),frame.rotation(item.get('yaw',0)),unreal.Vector(*scale)))
        # Repeated residences, trees and masonry use actual instanced geometry.
        if len(items)>1:
            actor=level.instances(mesh,transforms,folder+'-'+Path(path).stem,folder)
            components=actor.get_components_by_class(unreal.InstancedStaticMeshComponent)
        else:
            item=items[0];t=transforms[0]
            actor=level.spawn(mesh,t.translation,frame.rotation(item.get('yaw',0)),item['id'],folder,t.scale3d)
            components=[actor.static_mesh_component]
        for component in components:
            for index,slot in enumerate(mesh.get_editor_property('static_materials')):
                name=str(slot.get_editor_property('material_slot_name'))
                imported=str(slot.get_editor_property('imported_material_slot_name'))
                material=palette.get(name) or palette.get(imported)
                if material:component.set_material(index,material)
            if folder=='roads':
                # This thin lane overlaps Oldtown's spine; the graded Landscape
                # carries its navigation without rasterizing a second ceiling.
                component.set_editor_property('can_ever_affect_navigation',Path(path).stem!='cu-road-oldtown-upper-lane')
                variant=int(hashlib.sha256(path.encode()).hexdigest()[:2],16)%3
                rural=any(token in path for token in ('grain-road','hudlodge','old-path','northwoods','fortway'))
                surf=unreal.EditorAssetLibrary.load_asset(f'/Game/Capitale/Ressources/Surfaces/MI_{"soil" if rural else "paving"}_{variant}')
                for index in range(len(mesh.get_editor_property('static_materials'))):component.set_material(index,surf)
            if folder=='vegetation':component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            if folder=='horizon':
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                component.set_editor_property('cast_shadow',False)
                for index in range(len(mesh.get_editor_property('static_materials'))):component.set_material(index,horizon_material)
        origin,extent=actor.get_actor_bounds(False)
        if folder in city.LANDMARKS:
            bounds.append({'reference':folder,'actor':actor.get_actor_label(),
                           'minimumZMetres':(origin.z-extent.z)/100,'maximumZMetres':(origin.z+extent.z)/100,
                           'widthMetres':extent.x*.02,'depthMetres':extent.y*.02})
        if folder=='gates':
            box=mesh.get_bounding_box()
            for item in items:
                bounds.append({'reference':item['id'],'actor':actor.get_actor_label(),
                               'minimumZMetres':item['position'][2]+box.min.z*.01,
                               'maximumZMetres':item['position'][2]+box.max.z*.01,
                               'widthMetres':(box.max.x-box.min.x)*.01,
                               'depthMetres':(box.max.y-box.min.y)*.01})
    # Water uses one parameterized parent, separate environments and no overlap.
    waters={}
    for name,spec in city.WATER_ENVIRONMENTS.items():
        path=f'/Game/Capitale/Ressources/MI_Water_{name}'
        inst=finishes.instance(path,water_parent)
        ml.set_material_instance_scalar_parameter_value(inst,'Roughness',spec['roughness'])
        for i in range(2):
            ml.set_material_instance_scalar_parameter_value(inst,f'WavePeriodCm{i}',spec['waveMetres'][i]*100)
            speed=spec['waveSpeed'][i]
            ml.set_material_instance_vector_parameter_value(inst,f'WaveSpeed{i}',unreal.LinearColor(speed,speed*.6,0,1))
        for param,values in [('AbsorptionPerCm',spec['absorption']),('ScatteringPerCm',spec['scattering']),
                             ('WaveNormalScale',[spec['waveStrength'],spec['waveStrength'],.5])]:
            ml.set_material_instance_vector_parameter_value(inst,param,unreal.LinearColor(*values,1))
        ml.update_material_instance(inst);unreal.EditorAssetLibrary.save_loaded_asset(inst)
        mesh=library.static_mesh(f'Built/capital-urban/cu-water-{name}.glb')
        nanite=mesh.get_editor_property('nanite_settings').copy();nanite.enabled=False
        mesh.set_editor_property('nanite_settings',nanite)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
        actor=level.spawn(mesh,frame.map_point([0,0,0]),frame.rotation(0),'water-'+name,'water')
        actor.static_mesh_component.set_material(0,inst)
        actor.static_mesh_component.set_editor_property('disallow_nanite',True)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        actor.static_mesh_component.set_editor_property('cast_shadow',False)
        waters[name]={'instance':path,'parameters':spec}
    # Street lights accompany actual access geometry, independent of emissive pixels.
    lights=0
    for road in layout.ROADS:
        if road['width']<9:continue
        for u,v in road['points']:
            x,y=layout.metres((u,v));z=0
            # Read the encoded data so lights cannot use a stale pre-revision height.
            from array import array
            data=array('H');data.frombytes((REPORT/'hauteurs.r16').read_bytes())
            spec=json.loads((REPORT/'relief.json').read_text());ix=round((x-spec['area'][0])/2);iy=round((y-spec['area'][1])/2)
            z=(data[iy*(spec['quads'][0]+1)+ix]-32768)/128
            if z<-1:continue
            lamp=level.spawn(unreal.PointLight,frame.map_point([x+road['width']/2+1,y,z+4]),unreal.Rotator(0,0,0),f'lamp-{lights}','lights')
            lamp.tags=[scene.LAMP_TAG]
            c=lamp.point_light_component;c.set_editor_property('intensity',650)
            c.set_editor_property('attenuation_radius',1400)
            c.set_editor_property('light_color',unreal.Color(255,190,115,255));c.set_editor_property('cast_shadows',False)
            lights+=1
    result={'placedObjects':len(plan['objects']),'instanceGroups':len(groups),'uniqueMeshes':len(meshes),
            'measuredBounds':bounds,'waterEnvironments':waters,'lights':lights,
            'artisticApproval':'pending','navigation':'not yet measured; collision is present'}
    (REPORT/'engine-built.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return {k:v for k,v in result.items() if k not in ('measuredBounds','waterEnvironments')}
