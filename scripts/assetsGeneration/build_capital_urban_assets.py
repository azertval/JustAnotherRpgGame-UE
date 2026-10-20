#!/usr/bin/env python3
"""Reproducible civic architecture and civil works, using the existing dressed
stone export chain. Sourcebook images are never used as textures. New designs
are proposals, and are identified as such in the capital review report.
"""
from pathlib import Path
import sys
import math
import json
import hashlib
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parent))
import arena_sculpted_geometry as w
g=w.g
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Source/Elements/Assets/Built/capital-urban'
g.MATERIALS.update({'roof_green':((.075,.20,.115,1),.62,0),
                    'roof_blue':((.055,.09,.20,1),.78,0),
                    'roof_terracotta':((.43,.17,.08,1),.87,0)})
g.NAMES[:]=list(g.MATERIALS)


def roof(x,y,z,width,depth,rise,material='roof_terracotta'):
    if width>depth:
        start=len(g.VERTS)
        roof(0,0,z,depth,width,rise,material)
        # Rotate the complete roof, including ridge and courses, around its long axis.
        g.VERTS[start:]=[(x-vy,-y+vx,vz) for vx,vy,vz in g.VERTS[start:]]
        return
    # Four constructed slopes, caps, ridge and eaves; UVs retain construction direction.
    a,b,c,d=x-width/2,x+width/2,y-depth/2,y+depth/2
    g.solid([(a,c,z),(b,c,z),(b,d,z),(a,d,z),(x,c+width*.25,z+rise),(x,d-width*.25,z+rise)],
            [(0,4,1),(1,4,5,2),(2,5,3),(3,5,4,0),(3,0,1,2)],material,.025)
    g.block(x,y,z+rise,.24,max(1,depth-width*.5),.2,'bronze')
    for xx in (a,b): g.block(xx,y,z-.18,.32,depth,.28,'marble_white')
    # Parallel tile courses are geometry, while fine pores remain in the material.
    for side in (-1,1):
        for n in range(1,10):
            t=n/10
            g.block(x+side*width*.5*t,y,z+rise*(1-t),.075,depth-width*.5*(1-t),.085,material)


def wall(x,y,z,width,height,depth=.8,openings=True):
    g.block(x,y,z,width,depth,height,'stone_cream')
    g.block(x,y,z-.2,width+.4,depth+.4,.6,'marble_white')
    g.block(x,y,z+height-.3,width+.5,depth+.5,.3,'marble_white')
    if openings:
        count=max(1,int(width/4))
        for n in range(count):
            px=x-width/2+(n+.5)*width/count
            for zz in range(3,int(height-1),4):
                g.block(px,y+depth*.55,z+zz,1.3,.09,2,'dark_metal')
                for ox in (-.8,.8):g.block(px+ox,y+depth*.6,z+zz-.2,.22,.25,2.4,'marble_white')
                g.block(px,y+depth*.6,z+zz+2,1.9,.3,.2,'marble_white')


def hall(width=30,depth=40,height=12,roof_rise=5,roof_material='roof_terracotta'):
    g.block(0,0,-.5,width+3,depth+3,.5,'marble_white')
    for y in (-depth/2,depth/2): wall(0,y,0,width,height)
    for x in (-width/2,width/2):g.block(x,0,0,.8,depth,height,'stone_cream')
    for x in (-width/2,width/2):
        for y in range(-int(depth/2)+2,int(depth/2),5):
            g.block(x,y,0,1.3,1.6,height+1,'marble_white')
    # Public portico with a real open walking band, separate from the hall body.
    for x in range(-int(width/2)+3,int(width/2),5):
        w.sculpted_column(x,depth/2+3,0,height=6,radius=.38)
    w.broad_cornice(0,depth/2+3,6,width+2,depth=2)
    roof(0,0,height,width+2,depth+2,roof_rise,roof_material)


def round_tower(x,y,base,height,radius=4,cap=True):
    g.turned(x,y,base,[(radius+.45,0),(radius+.45,.7),(radius,.9),(radius,height-1),
                     (radius+.45,height-1),(radius+.45,height)],'stone_cream',sides=32)
    for z in range(4,int(height),5):
        g.turned(x,y,base+z,[(radius+.12,0),(radius+.12,.22)],'marble_white',sides=32)
    if cap:
        for n in range(12):
            a=n*math.tau/12
            g.block(x+math.cos(a)*radius,y+math.sin(a)*radius,base+height,.75,.75,.9)


def wall_module():
    # Bottom extends into a real footing. Nine metre curtain, 2.2m thick.
    g.block(0,0,-2,12,2.8,2,'stone_cream')
    g.block(0,0,0,12,2.2,8.1,'stone_cream')
    for z in [0,2.7,5.4,8.1]:g.block(0,0,z,12.1,2.5,.25,'marble_white')
    for x in [-5,-3,-1,1,3,5]:g.dressed_block(x,0,8.35,1.05,2.3,.9)
    for x in [-5.5,0,5.5]:g.block(x,0,-.5,.9,3.0,6.0)


def retaining():
    g.block(0,0,-.5,8,1.3,.7,'stone_cream')
    g.block(0,0,0,8,.8,3,'stone_cream')
    g.block(0,0,3,8.2,1.1,.25,'marble_white')
    for x in [-3.5,0,3.5]:g.block(x,.2,0,.65,1.1,2.9,'stone_cream')


def cathedral():
    hall(32,65,27,11,'roof_blue')
    for x in (-18,18):
        g.block(x,20,0,9,12,40,'stone_cream')
        for z in [10,20,30,40]:g.block(x,20,z,10,13,.6,'marble_white')
        for ox in (-4,4):g.block(x+ox,20,0,.8,13,42,'marble_white')
        g.turned(x,20,41,[(5,0),(3,6),(.4,15)],'roof_blue',sides=8)
    for y in [-26,-16,-6,4]:
        for x in (-19,19):
            g.block(x,y,0,1.5,2.6,23,'marble_white')
            g.turned(x,y,23,[(1.2,0),(.05,8)],'stone_cream',sides=4)


def palace():
    # Reference L12-01: faceted green/gold rotunda and long blue-green axis.
    # The former four generic castle turrets are replaced by a colonnaded drum.
    hall(22,100,18,7,'roof_blue')
    g.turned(0,-24,-2,[(22,0),(22,3),(19,3),(19,20)],'stone_cream',sides=16)
    for n in range(16):
        a=n*math.tau/16
        x,y=math.cos(a)*20,math.sin(a)*20-24
        w.sculpted_column(x,y,0,height=23,radius=.65)
        g.turned(x,y,23,[(1.3,0),(.3,7)],'bronze',sides=8)
    g.turned(0,-24,24,[(23,0),(23,1),(21,1),(19,11),(12,23),(3,29),(.3,32)],'roof_green',sides=16)
    for n in range(12):
        a=n*math.tau/12
        # Gold structural ribs follow the sloping dome, no floating vertical rods.
        for r,z in [(20,27),(17,34),(12,44),(5,51)]:
            g.turned(math.cos(a)*r,math.sin(a)*r-24,z,[(.28,0),(.24,2.8)],'bronze',sides=8)
    for x in (-18,18):
        for y in range(0,48,6):w.sculpted_column(x,y,0,height=10,radius=.46)
        roof(x,23,11,10,56,4,'roof_green')
    for y in (-52,50):
        for x in (-18,18):round_tower(x,y,0,15,2.8,False)
    for i in range(8):g.block(0,57-i*.4,-1.4+i*.175,18,1.0,.18,'marble_white')


def arcade(x,y,z,count=7,spacing=4.4,height=7):
    for i in range(count+1):
        w.sculpted_column(x+(i-count/2)*spacing,y,z,height=height,radius=.38)
    for i in range(count):
        cx=x+(i+.5-count/2)*spacing
        for n in range(12):
            lo=n*math.pi/12;hi=(n+1)*math.pi/12
            pts=[(cx+r*math.cos(a),z+height-1.8+r*math.sin(a)) for r,a in [(2.3,lo),(2.3,hi),(1.85,hi),(1.85,lo)]]
            g.prism(pts,y-.42,y+.42,'marble_white')
    g.block(x,y,z+height+1,count*spacing+1,1.2,.6,'marble_white')


def university():
    # White marble U around an open court; two storeys of arcades, distinct roofs.
    for x in (-31,31):
        g.block(x,0,0,14,68,15,'stone_cream')
        roof(x,0,15,16,70,5,'roof_blue')
        for y in range(-28,33,6):
            for z in (2,7,12):g.block(x+(7.02 if x<0 else -7.02),y,z,.08,2,2.5,'dark_metal')
    wall(0,-32,0,62,16,depth=12)
    roof(0,-32,16,64,17,5,'roof_blue')
    for z in (0,8):arcade(0,-24,z,count=10,spacing=4.5,height=6)
    for x in (-23,23):
        for y in range(-16,34,6):w.sculpted_column(x,y,0,height=6,radius=.42)
    # The approach and courtyard share level 46m; do not bury decorative stairs
    # below that pad. A raised 12cm paving slab avoids coplanar terrain flicker.
    g.block(0,44,-.18,28,25,.30,'marble_white')
    g.block(0,0,-.18,47,67,.30,'marble_white')


def museum():
    hall(30,42,13,6,'roof_blue')
    for x in range(-12,13,4):w.sculpted_column(x,25,0,height=9,radius=.65)
    g.prism([(-16,10),(16,10),(0,17)],22,28,'marble_white')


def forum():
    g.turned(0,0,-.5,[(18,0),(18,1),(16,1),(16,12)],'stone_cream',sides=24)
    g.turned(0,0,12,[(18,0),(15,3),(8,7),(.2,9)],'roof_blue',sides=24)
    for x in (-10,-6,-2,2,6,10):w.sculpted_column(x,18,0,height=8,radius=.5)
    g.prism([(-13,8),(13,8),(0,14)],16,20,'marble_white')


def manor_court():
    hall(22,30,11,5)
    for x in (-20,20):
        g.block(x,12,0,12,36,8,'stone_cream');roof(x,12,8,14,38,4)
    arcade(0,30,0,count=5,spacing=4,height=6)


def footing():
    # Unit plinth: per-instance dimensions encode the actual foundation depth.
    g.block(0,0,0,1,1,1,'stone_cream')


def arcane():
    for base,h,r in [(0,18,8),(18,18,6.4),(36,14,4.8)]:
        round_tower(0,0,base,h,r,False)
        g.turned(0,0,base+h-.3,[(r+1.2,0),(r+1.2,.7)],'marble_white',sides=12)
    for n in range(8):
        a=n*math.tau/8
        g.turned(math.cos(a)*7.5,math.sin(a)*7.5,0,[(1.2,0),(.8,34),(.05,40)],'marble_white',sides=6)
    g.turned(0,0,50,[(5.2,0),(3.4,5),(.15,12)],'roof_green',sides=8)


def fortress():
    for x in (-25,25):g.block(x,0,0,2.8,46,10,'stone_cream')
    for y in (-23,23):g.block(0,y,0,50,2.8,10,'stone_cream')
    for x in (-25,25):
        for y in (-23,23):round_tower(x,y,0,16,4)
    hall(18,25,11,5)


def bridge(parapet_start=-6,parapet_end=6):
    # Repeatable 12m open span: full stone deck, voussoirs, piers, coping.
    g.block(0,0,-.7,12,9,.7,'stone_cream')
    for y in (-4.5,4.5):
        if parapet_end>parapet_start:
            centre=(parapet_start+parapet_end)/2;length=parapet_end-parapet_start
            g.block(centre,y,0,length,.65,1.1,'stone_cream')
            g.block(centre,y,1.1,length,.85,.18,'marble_white')
        # An arc in the span's XZ plane, no solid wall across the water.
        for n in range(20):
            lo=n*math.pi/20;hi=(n+1)*math.pi/20
            pts=[(r*math.cos(a),-4.8+r*math.sin(a)) for r,a in [(4.9,lo),(4.9,hi),(4.3,hi),(4.3,lo)]]
            g.prism(pts,y-.35,y+.35,'stone_cream')
    g.block(-6,0,-9,1.5,10,8.3,'stone_cream')


def aqueduct():
    bridge()
    # Clearly different from a road: raised conduit with an open trough.
    g.block(0,0,.1,12,2.2,.4,'stone_cream')
    for y in (-1.2,1.2):g.block(0,y,.1,12,.35,1.1,'stone_cream')


def pier():
    for x in [-3,3]:
        for y in [-5,0,5]:g.turned(x,y,-6,[(.32,0),(.30,6.6)],'wood',sides=12)
    for y in [-5,0,5]:g.block(0,y,-.35,7,.4,.35,'wood')
    for j in range(25):g.block(0,-6+j*.5,0,7,.48,.17,'wood')


def stonebreaker_forge():
    # Compact working hall replaces the manor that overlapped Smithheim Way.
    # Scale, equipment and raised forecourt are explicitly reversible proposals.
    g.block(0,0,-12,14,16,12,'stone_cream')
    g.block(0,-7.7,0,14,.6,6.4,'stone_cream')
    for x in (-6.7,6.7):g.block(x,0,0,.6,16,6.4,'stone_cream')
    for x in (-4.75,4.75):g.block(x,7.7,0,4.5,.6,6.4,'stone_cream')
    # Voussoirs around a real open entrance.
    for i in range(16):
        a,b=i*math.pi/16,(i+1)*math.pi/16
        ring=[(r*math.cos(t),yy,3.7+r*math.sin(t)) for yy in (7.25,8.15)
              for r,t in ((2.9,a),(2.9,b),(2.35,b),(2.35,a))]
        g.solid(ring,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'stone_cream',.015)
    roof(0,0,6.4,15.2,17.2,3.0,'mortar')
    for x in (-4.6,4.6):
        g.block(x,-3,0,2,2,11.5,'mortar')
        g.block(x,-3,11.2,2.4,2.4,.45,'stone_cream')
        g.block(x,-1.8,0,2.8,1.6,1.3,'mortar')
        g.block(x,-.95,.3,1.7,.12,.7,'dark_metal')
        g.block(x,3,0,1.1,1.1,.7,'wood')
        g.block(x,3,.7,1.5,.55,.35,'dark_metal')
    # Burgundy awning, timber rack, iron stock and an unobstructed centre aisle.
    g.block(-4.9,5,4.5,3.2,4,.12,'burgundy')
    for x in (-6.3,-3.5):g.block(x,6.8,0,.18,.18,4.5,'wood')
    for y in (-4,0):g.block(5.5,y,.7,.5,2.8,.2,'wood')
    for n in range(6):g.block(5.05+n*.17,-2,.9,.08,5,.08,'dark_metal')
    g.stair_flight(0,20,4,.28,-7.65,.18,44,-8.4,direction=-1)


def grave():
    g.block(0,0,-.2,1.1,2.0,.25,'stone_cream')
    g.block(0,-.75,0,.85,.25,1.1,'stone_cream')
    g.turned(0,-.75,1.0,[(.43,0),(.3,.25),(.04,.4)],'marble_white',sides=8)


def moon_tower():
    round_tower(0,0,0,17,3.8,False)
    g.turned(0,0,17,[(4.4,0),(2.5,2.6),(.08,5)],'roof_blue',sides=8)


def build(only_water=False,only_piece=None):
    OUT.mkdir(parents=True,exist_ok=True)
    if only_piece:
        export=g.export_piece
        def filtered(name,*args,**kwargs):
            if name in only_piece.split(','):return export(name,*args,**kwargs)
        g.export_piece=filtered
    materials=g.build_materials()
    for name,fn in ([] if only_water else [('curtain',wall_module),('retaining',retaining),('bridge',bridge),('aqueduct',aqueduct),
                    ('bridge-open',lambda:bridge(0,0)),('bridge-entry',lambda:bridge(0,6)),('bridge-exit',lambda:bridge(-6,0)),
                    ('pier',pier),('cathedral',cathedral),('palace',palace),('arcane-tower',arcane),
                    ('fortress',fortress),('civic-hall',hall),('university',university),('museum',museum),
                    ('forum',forum),('manor-court',manor_court),('stonebreaker-forge',stonebreaker_forge),('footing',footing),('watchtower',lambda:round_tower(0,0,0,18,3)),
                    ('grave',grave),('moon-tower',moon_tower),
                    ('paving-0',lambda:w.paving(-4,4,-4,4,0,variant=0)),
                    ('paving-1',lambda:w.paving(-4,4,-4,4,0,variant=1)),
                    ('paving-2',lambda:w.paving(-4,4,-4,4,0,variant=2))]):
        g.export_piece('cu-'+name,fn,OUT,materials,clean_degenerate=name=='stonebreaker-forge')
    # The roads and water are built from the same 16-bit terrain used by Unreal.
    # Render and collision offsets stay explicit (road surface +10cm).
    import numpy as np
    sys.path.insert(0,str(ROOT/'scripts/maps'))
    import capital_landscape_layout as layout
    report=ROOT/'Saved/Jadg/capital-landscape'
    spec=json.loads((report/'relief.json').read_text())
    heights=(np.fromfile(report/'hauteurs.r16',dtype='<u2').reshape(spec['quads'][1]+1,spec['quads'][0]+1).astype(float)-32768)/128
    x0,y0,x1,y1=spec['area'];step=spec['resolution']
    def sample(x,y):
        u=np.clip((x-x0)/step,0,heights.shape[1]-1);v=np.clip((y-y0)/step,0,heights.shape[0]-1)
        i,j=min(int(u),heights.shape[1]-2),min(int(v),heights.shape[0]-2);a,b=u-i,v-j
        return (heights[j,i]*(1-a)+heights[j,i+1]*a)*(1-b)+(heights[j+1,i]*(1-a)+heights[j+1,i+1]*a)*b
    if not only_water:
        import capital_city_layout as city
        placement=json.loads((report/'urban-placement.json').read_text())
        def foundations():
            for o in placement.get('foundations',[]):
                x,y,z=o['position'];sx,sy,sz=o['scale'];angle=math.radians(-o['yaw'])
                corners=[]
                for zz in (z,z+sz):
                    for dx,dy in [(-sx/2,-sy/2),(sx/2,-sy/2),(sx/2,sy/2),(-sx/2,sy/2)]:
                        corners.append((x+dx*math.cos(angle)-dy*math.sin(angle),y+dx*math.sin(angle)+dy*math.cos(angle),zz))
                g.solid(corners,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'stone_cream',0)
            # Main platforms match mesh footprints, with enough depth to meet the hill.
            for key,(width,depth) in {'L12-01':(53,114),'L04-01':(80,98),'L04-02':(37,58),'L04-04':(40,45),
                                     'L11-01':(51,78),'L05-01':(24,24),'L05-03':(58,63)}.items():
                u,v,_,*_=city.LANDMARKS[key];x,y=layout.metres((u,v));z=sample(x,y)
                low=min(sample(x+dx,y+dy) for dx in (-width/2,width/2) for dy in (-depth/2,depth/2))-.8
                if z>low:g.block(x,y,low,width,depth,z-low,'stone_cream')
        g.export_piece('cu-monument-foundations',foundations,OUT,materials)

        def road_retaining():
            for road in layout.ROADS:
                if road['width']<6:continue
                for a,b in zip(road['points'],road['points'][1:]):
                    a,b=layout.metres(a),layout.metres(b);length=math.dist(a,b)
                    nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
                    for i in range(math.ceil(length/6)):
                        t=(i+.5)/math.ceil(length/6);cx=a[0]+(b[0]-a[0])*t;cy=a[1]+(b[1]-a[1])*t
                        z=sample(cx,cy)
                        if z<0:continue
                        for side in (-1,1):
                            distance=road['width']/2+2
                            x,y=cx+nx*distance*side,cy+ny*distance*side
                            outside=sample(cx+nx*(distance+5)*side,cy+ny*(distance+5)*side)
                            delta=z-outside
                            if abs(delta)<1.4:continue
                            # Leave all intersections open.
                            uu=x/layout.METRES_PER_UNIT+layout.ARENA[0];vv=y/layout.METRES_PER_UNIT+layout.ARENA[1]
                            from capital_urban_scene import distance_segment
                            if any(r is not road and distance_segment((uu,vv),aa,bb)[0]*layout.METRES_PER_UNIT<r['width']/2+2
                                   for r in layout.ROADS for aa,bb in zip(r['points'],r['points'][1:])):continue
                            top=max(z,outside)-.15;bottom=min(z,outside)-.7
                            half=length/math.ceil(length/6)/2
                            dx,dy=(b[0]-a[0])/length*half,(b[1]-a[1])/length*half
                            vertices=[(x-dx+nx*s*.55,y-dy+ny*s*.55,zz) for zz in (bottom,top) for s in (-1,1)]
                            vertices += [(x+dx+nx*s*.55,y+dy+ny*s*.55,zz) for zz in (bottom,top) for s in (-1,1)]
                            g.solid(vertices,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],'stone_cream',0)
                            # Coping and foot thickness are real geometry, UVs baked at 2m/repeat.
                            g.solid([(vx,vy,top) for vx,vy,_ in [vertices[0],vertices[1],vertices[5],vertices[4]]]+
                                    [(vx,vy,top+.25) for vx,vy,_ in [vertices[0],vertices[1],vertices[5],vertices[4]]],
                                    [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'marble_white',0)
        g.export_piece('cu-road-retaining',road_retaining,OUT,materials)

        def terrace_gardens():
            # Upper landing joins the palace forecourt through a broad real stair.
            xa,yy=layout.metres((628,686));xb,_=layout.metres((645,686))
            count=math.ceil(8/.18);tread=(xb-xa)/count
            for i in range(count):
                z=54+(i+1)*8/count
                g.block(xa+(i+.5)*tread,yy,z-.32,tread+.015,8,.36,'marble_white')
            for ti,t in enumerate(city.GARDEN_TERRACES):
                x,y=layout.metres(t['centre']);a,b=[v*layout.METRES_PER_UNIT for v in t['halfSize']];z=t['z']
                g.block(x,y,z-.6,a*2,b*2,.65,'marble_white')
                for side in (-1,1):
                    for i in range(int(2*a/8)):
                        px=x-a+(i+.5)*8;py=y+b*side
                        incoming=city.GARDEN_TERRACES[ti-1]['centre'][0] if ti else None
                        opening=incoming if side<0 else (t['centre'][0] if ti<len(city.GARDEN_TERRACES)-1 else None)
                        if opening is not None and abs(px-layout.metres((opening,0))[0])<8:continue
                        low=sample(px,py+side*5)-.7
                        if z>low:g.block(px,py,low,8.05,1.2,z-low,'stone_cream')
                        g.block(px,py,z,7.9,.75,.8,'marble_white')
            for a,b in zip(city.GARDEN_TERRACES,city.GARDEN_TERRACES[1:]):
                x,ya=layout.metres((a['centre'][0],a['centre'][1]+a['halfSize'][1]))
                _,yb=layout.metres((b['centre'][0],b['centre'][1]-b['halfSize'][1]))
                count=math.ceil((a['z']-b['z'])/.18);tread=(yb-ya)/count
                for i in range(count):
                    z=a['z']-(i+1)*(a['z']-b['z'])/count
                    g.block(x,ya+(i+.5)*tread,z-.3,8,tread+.015,.34,'marble_white')
        g.export_piece('cu-terrace-gardens',terrace_gardens,OUT,materials)

        def horizon():
            # A triangulated ring preserves all four edges and corners. Offshore
            # vertices remain submerged; inland continuation has broad irregular
            # ridges, rather than extruding each shoreline into a flat rectangle.
            def background(x,y):
                ex=max(x0,min(x1,x));ey=max(y0,min(y1,y))
                distance=math.hypot(x-ex,y-ey)
                drift=(120*math.sin(distance/370)+80*math.sin((ex+ey)/460))*(1-math.exp(-distance/250))
                edge=sample(ex+(drift if y!=ey else 0),ey+(drift if x!=ex else 0))
                blend=1-math.exp(-distance/350)
                land=max(0,min(1,(edge-layout.SEA_LEVEL)/35))
                inland=60+55*math.sin(x/260+y/430)**2+45*math.sin(x/510-y/290)**2
                return edge*(1-blend)+(-15+land*inland)*blend-.12
            # Every inner edge vertex matches the 2m Landscape. The former 32m
            # chord across a rugged boundary left visible gaps and angular seams.
            rings=(0,4,8,12,20,*range(40,1620,20))
            for side in range(4):
                count=spec['quads'][0 if side%2==0 else 1]
                def edge(t,d):
                    if side==0:return x0+(x1-x0)*t+(2*t-1)*d,y0-d  # noqa: B023
                    if side==1:return x1+d,y0+(y1-y0)*t+(2*t-1)*d  # noqa: B023
                    if side==2:return x1-(x1-x0)*t+(1-2*t)*d,y1+d  # noqa: B023
                    return x0-d,y1-(y1-y0)*t+(1-2*t)*d
                for k in range(count):
                    for a,b in zip(rings,rings[1:]):
                        xy=[edge(k/count,a),edge((k+1)/count,a),edge((k+1)/count,b),edge(k/count,b)]
                        g.solid([(x,y,background(x,y)) for x,y in xy],[(0,1,2),(0,2,3)],'stone_cream',0)
        masks=[np.fromfile(report/f'couche-{layer}.r8',dtype='u1').reshape(heights.shape).astype(float)/255
               for layer in ('roche','sous-bois','terre','sable')]
        from functools import lru_cache
        @lru_cache(maxsize=None)
        def horizon_colour(x,y,z):
            ex,ey=np.clip(x,x0,x1),np.clip(y,y0,y1)
            u,v=(ex-x0)/step,(ey-y0)/step;i,j=min(int(u),heights.shape[1]-2),min(int(v),heights.shape[0]-2);a,b=u-i,v-j
            fade=math.exp(-math.hypot(x-ex,y-ey)/100)
            return tuple(float((m[j,i]*(1-a)*(1-b)+m[j,i+1]*a*(1-b)+m[j+1,i]*(1-a)*b+m[j+1,i+1]*a*b)*fade) for m in masks)
        g.export_piece('cu-horizon',horizon,OUT,materials,heightfield_surface_up=True,vertex_color=horizon_colour)
    for road in ([] if only_water else layout.ROADS):
        def road_mesh(road=road):
            for a,b in zip(road['points'],road['points'][1:]):
                a=layout.metres(a);b=layout.metres(b);length=math.dist(a,b)
                nx,ny=-(b[1]-a[1])/length,(b[0]-a[0])/length
                count=max(1,math.ceil(length));across=math.ceil(road['width'])
                for i in range(count):
                    t0=i/count;t1=(i+1)/count
                    cx=a[0]+(b[0]-a[0])*(t0+t1)/2;cy=a[1]+(b[1]-a[1])*(t0+t1)/2
                    if sample(cx,cy)<layout.SEA_LEVEL+.4:continue
                    top=[]
                    for t in (t0,t1):
                        for j in range(across+1):
                            side=(j/across-.5)*road['width']
                            x=a[0]+(b[0]-a[0])*t+nx*side;y=a[1]+(b[1]-a[1])*t+ny*side
                            top.append((x,y,sample(x,y)+.10))
                    row=across+1;bottom=len(top);faces=[]
                    for j in range(across):
                        faces.extend([(j,row+j,row+j+1),(j,row+j+1,j+1),
                                      (bottom+j+1,bottom+row+j+1,bottom+row+j,bottom+j),
                                      (j+1,bottom+j+1,bottom+j,j),
                                      (row+j,bottom+row+j,bottom+row+j+1,row+j+1)])
                    faces.extend([(0,bottom,bottom+row,row),(across,row+across,bottom+row+across,bottom+across)])
                    g.solid(top+[(x,y,z-.12) for x,y,z in top],faces,
                            'stone_cream' if road['width']>=9 else 'sand',0)
        g.export_piece('cu-road-'+road['id'],road_mesh,OUT,materials)
    for env in ('bay','river','creek','pool'):
        def water_mesh(env=env):
            if env=='bay':
                for a,b,c,d in [(x0-6000,x1+6000,y0-6000,y0),(x0-6000,x1+6000,y1,y1+6000),
                                (x0-6000,x0,y0,y1),(x1,x1+6000,y0,y1)]:
                    g.solid([(a,c,layout.SEA_LEVEL),(b,c,layout.SEA_LEVEL),(b,d,layout.SEA_LEVEL),(a,d,layout.SEA_LEVEL)],[(3,2,1,0)],'marble_white',0)
            # Tile partition covers the whole domain, including hidden parts
            # under dry land. No coplanar overlapping sheets at the transitions.
            for j in range(0,spec['quads'][1],8):
                for i in range(0,spec['quads'][0],8):
                    u=layout.AREA_UNITS[0]+(i+4)*step/layout.METRES_PER_UNIT
                    v=layout.AREA_UNITS[1]+(j+4)*step/layout.METRES_PER_UNIT
                    kind='pool' if 845<u<980 and 393<v<478 else 'creek' if v>950 and u<310 else 'river' if u>980 else 'bay'
                    if kind!=env:continue
                    a=x0+i*step;b=min(x1,a+8*step);c=y0+j*step;d=min(y1,c+8*step)
                    # solid() mirrors map Y into Blender Y. Reverse this open
                    # face explicitly; closed solids repair their own normals.
                    g.solid([(a,c,layout.SEA_LEVEL),(b,c,layout.SEA_LEVEL),(b,d,layout.SEA_LEVEL),(a,d,layout.SEA_LEVEL)],[(3,2,1,0)],'marble_white',0)
        g.export_piece('cu-water-'+env,water_mesh,OUT,materials,horizontal_surface_up=True)
    for m in g.PIECES:m['sha256']=hashlib.sha256((OUT/m['file']).read_bytes()).hexdigest()
    if only_water:
        previous=json.loads((OUT/'manifest.json').read_text())
        g.PIECES[:0]=[m for m in previous['meshes'] if not m['id'].startswith('cu-water-')]
    elif only_piece:
        previous=json.loads((OUT/'manifest.json').read_text())
        g.PIECES[:0]=[m for m in previous['meshes'] if m['id'] not in only_piece.split(',')]
    doc={'generator':'scripts/assetsGeneration/build_capital_urban_assets.py','version':1,
         'coordinates':'metres, image right/down, Z up','uvMetres':2,'meshes':g.PIECES,
         'status':'proposed architecture; visual and traversal review required'}
    (OUT/'manifest.json').write_text(json.dumps(doc,indent=2),encoding='utf8')


if __name__=='__main__':
    if g.bpy:build(only_water='--water-only' in sys.argv,only_piece=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--only=')),None))
    else:raise SystemExit(subprocess.run([str(g.BLENDER),'--background','--threads','2','--python-exit-code','1',
                                         '--python',str(Path(__file__).resolve()),'--',*sys.argv[1:]]).returncode)
