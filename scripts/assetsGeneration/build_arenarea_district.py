#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Build complete Arenarea from small sculpted Blender pieces and existing Arena.

No Unreal launch and no canonical map write. Outputs only Built/arenarea-district.
Closed secondary houses have six coherent families; important buildings have
furnished open rooms and removable roofs. Shared witness helpers remain intact.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "Source/Elements/Assets/Built/arenarea-district"
BLENDER = Path(r"D:\Blender Foundation\Blender 5.2\blender.exe")
TERRAIN_SPACING = .5
TERRAIN_REFINEMENTS = [{"bounds":[-212,216,-198,252],"spacing":.25}]
REFINED_PAVING_BATCHES = {"ard-relief-quay-005","ard-relief-road-048","ard-relief-road-049",
                        "ard-relief-road-067","ard-relief-road-068","ard-relief-road-072"}


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


w = module("arenarea_wicked_geometry", Path(__file__).with_name("arena_sculpted_geometry.py"))
g = w.g
layout = module("arenarea_layout", ROOT / "scripts/maps/arenarea_district_layout.py")
foliage = module("district_sculpted_foliage", Path(__file__).with_name("district_foliage.py"))
relief = module("arenarea_relief_geometry",Path(__file__).with_name("arenarea_relief_geometry.py"))
g.MATERIALS.update({
    "roof_terracotta": ((.47, .13, .065, 1), .87, 0),
    "pottery": ((.55, .23, .11, 1), .65, 0),
    "linen": ((.82, .70, .48, 1), .9, 0),
    "foliage": ((.12, .25, .065, 1), .93, 0),
})
g.NAMES[:] = list(g.MATERIALS)
OBJECTS, LIGHTS, ROOFS, WATERS = [], [], [], []
RELIEF_COLLISIONS = {}
DENSE = True
STREETS = [([224,298],[216,73]),([216,73],[176,72]),([176,72],[94,45]),
           ([94,45],[0,34]),([0,34],[-97,39]),([-97,39],[-187,24]),
           ([-187,24],[-203,112]),([-187,24],[-190,-135]),
           ([216,73],[216,-85]),([-187,112],[-187,292]),
           ([-187,212],[64,212]),([64,212],[88,272]),
           ([-92,114],[66,114]),([0,34],[0,138]),
           ([-107,139],[-107,248]),([66,114],[66,274]),
           ([-188,292],[216,292]),([88,272],[211,272])]


def segment_box(a,b,box):
    lo,hi=0.0,1.0
    for k in [0,1]:
        delta=b[k]-a[k]
        if abs(delta)<1e-8:
            if not box[k]<=a[k]<=box[k+2]:
                return False
        else:
            u,v=(box[k]-a[k])/delta,(box[k+2]-a[k])/delta
            lo,hi=max(lo,min(u,v)),min(hi,max(u,v))
    return lo<=hi


def houses_overlap(x,y,rx,ry,yaw,other,gap=1.5):
    """Oriented footprint test; diagonal frontages must not lose every other bay."""
    px,py,prx,pry,pyaw=other
    ca,sa=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
    cb,sb=math.cos(math.radians(pyaw)),math.sin(math.radians(pyaw))
    axes_a=[(ca,sa),(-sa,ca)]
    axes_b=[(cb,sb),(-sb,cb)]
    for ax,ay in axes_a+axes_b:
        ra=rx*abs(ax*axes_a[0][0]+ay*axes_a[0][1])+ry*abs(ax*axes_a[1][0]+ay*axes_a[1][1])
        rb=prx*abs(ax*axes_b[0][0]+ay*axes_b[0][1])+pry*abs(ax*axes_b[1][0]+ay*axes_b[1][1])
        if abs((px-x)*ax+(py-y)*ay)>ra+rb+gap:
            return False
    return True


def place(mesh, x, y, z=0, yaw=0, role="architecture", occluder=True, tag=None):
    if DENSE and mesh in {"ard-garden-bed","ard-hedge","ard-cypress","ard-bench",
                          "ard-amphora","ard-lamp","ard-stall","ard-merchant-cart"}:
        source=next(m for m in g.PIECES if m["id"]==mesh)["boundsBlender"]
        local_rx=max(abs(source[0][0]),abs(source[1][0]))
        local_ry=max(abs(source[0][1]),abs(source[1][1]))
        c,s=abs(math.cos(math.radians(yaw))),abs(math.sin(math.radians(yaw)))
        rx,ry=c*local_rx+s*local_ry,s*local_rx+c*local_ry
        box=[x-rx-1.8,y-ry-1.8,x+rx+1.8,y+ry+1.8]
        if any(segment_box(a,b,box)
               for a,b in zip(layout.VISIT_ROUTE,layout.VISIT_ROUTE[1:])):
            return None
        for house in OBJECTS:
            if not house["id"].startswith("house-"):
                continue
            hb=next(m for m in g.PIECES if m["id"]==house["meshId"])["boundsBlender"]
            hrx=max(abs(hb[0][0]),abs(hb[1][0]))
            hry=max(abs(hb[0][1]),abs(hb[1][1]))
            hc,hs=abs(math.cos(math.radians(house["yaw"]))),abs(math.sin(math.radians(house["yaw"])))
            hx,hy=house["position"][:2]
            hrx,hry=hc*hrx+hs*hry,hs*hrx+hc*hry
            if x+rx+.15>hx-hrx and x-rx-.15<hx+hrx and y+ry+.15>hy-hry and y-ry-.15<hy+hry:
                return None
    identifier = tag or f"{mesh}-{len(OBJECTS):04d}"
    item = {"id": identifier, "meshId": mesh, "position": [x,y,z],
            "yaw": yaw, "role": role, "occluder": occluder}
    if role == "vegetation":
        item["motion"] = "foliage"
    OBJECTS.append(item)
    if role == "roof" and occluder:
        ROOFS.append(identifier)
    return item


def rotate_geometry(build, yaw=90):
    first = len(g.VERTS)
    build()
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    for j in range(first, len(g.VERTS)):
        x, y, z = g.VERTS[j]
        g.VERTS[j] = (x*c+y*s, -x*s+y*c, z)


def wall(x0, x1, y, height, z=0, depth=.48):
    g.masonry(x0,x1,y,z,z+height,depth,course=.52,brick=1.05)
    g.block((x0+x1)/2,y,z,x1-x0,depth+.08,.16,"marble_white")
    w.broad_cornice((x0+x1)/2,y,z+height,x1-x0,depth+.18)


def side_wall(x,y0,y1,height,z=0):
    rotate_geometry(lambda: wall(y0,y1,-x,height,z))


def front_wall(width,depth,height,closed=False):
    y=depth/2
    # Five metre portal: open ground entrance, dressed jambs and real arch.
    door=5 if not closed else 2.7
    wall(-width/2,-door/2,y,height)
    wall(door/2,width/2,y,height)
    g.arc(0,y,2.9,door/2,.40,.58,21)
    lintel_z=2.9+door/2+.30
    wall(-door/2,door/2,y,height-lintel_z,lintel_z) if height > lintel_z else None
    if closed:
        for j in range(9):
            g.block((j-4)*.29,y+.12,0,.265,.10,3.0,"wood")
        for z in [.6,2.2]:
            g.block(0,y+.2,z,door,.07,.085,"dark_metal")
    for x in [-width*.37,width*.37]:
        w.sculpted_column(x,y+.65,0,min(height,6),.30)
    w.carved_frieze(0,y+.25,height-.85,width-.6)


def tiled_roof(width,depth,z,variant=0):
    # Roof is one removable mesh; hollow attic sides are closed by the gable.
    rise=width*.24
    g.prism([(-width/2-.7,z),(0,z+rise),(width/2+.7,z),
             (width/2+.7,z-.17),(-width/2-.7,z-.17)],-depth/2-.65,depth/2+.65,"roof_terracotta")
    if DENSE:
        half=width/2+.7
        rows=max(3,math.ceil(half/.72))
        columns=max(3,math.ceil((depth+1.1)/.55))
        for side in [-1,1]:
            for row in range(rows):
                x0=side*row*half/rows
                x1=side*min(half,(row+1)*half/rows+.085)
                for col in range(columns):
                    y0=-depth/2-.55+col*(depth+1.1)/columns
                    y1=min(depth/2+.55,y0+(depth+1.1)/columns+.025)
                    clay_tile(x0,x1,y0,y1,z,rise,half,.018*(rows-row))
        for j in range(columns):
            y0=-depth/2-.6+j*(depth+1.2)/columns
            y1=y0+(depth+1.2)/columns-.018
            g.rod((0,y0,z+rise+.12),(0,y1,z+rise+.12),.18,"pottery",24)
    for side in ([] if DENSE else [-1,1]):
        for j in range(max(3,round(width/.75))):
            x=side*(j+.5)*width/(2*max(3,round(width/.75)))
            zz=z+rise*(1-abs(x)/(width/2))+.07
            g.rod((x,-depth/2-.5,zz),(x,depth/2+.5,zz),.08,"roof_terracotta",12)
    g.rod((0,-depth/2-.8,z+rise+.1),(0,depth/2+.8,z+rise+.1),.18,"pottery",16)
    for y in [-depth/2-.4,depth/2+.4]:
        g.block(0,y,z+rise+.12,.37,.37,.65,"marble_white")
    g.block(-width*.25,0,z+rise*.54,1.1,.8,1.7,"stone_cream")
    g.block(-width*.25,0,z+rise*.54+1.6,1.4,1.1,.20,"marble_white")


def clay_tile(x0,x1,y0,y1,z,rise,half,lift):
    """Closed overlapping clay, lip and curved barrel are genuine geometry."""
    nx,ny=2,4
    points=[]
    for layer in range(2):
        for i in range(nx+1):
            u=i/nx
            x=x0+(x1-x0)*u
            for j in range(ny+1):
                v=j/ny
                zz=z+rise*(1-abs(x)/half)+lift+.065*(2*v-1)**2+layer*.055
                points.append((x,y0+(y1-y0)*v,zz))
    stride=(nx+1)*(ny+1)
    faces=[]
    for layer in range(2):
        off=layer*stride
        for i in range(nx):
            for j in range(ny):
                a=off+i*(ny+1)+j
                faces.append((a,a+1,a+ny+2,a+ny+1))
    for j in range(ny):
        for i in [0,nx]:
            a=i*(ny+1)+j
            faces.append((a,a+1,a+1+stride,a+stride))
    for i in range(nx):
        for j in [0,ny]:
            a=i*(ny+1)+j
            faces.append((a,a+ny+1,a+ny+1+stride,a+stride))
    tone=.87+.12*(.5+.5*math.sin((x0+x1)*13.7+(y0+y1)*9.3))
    g.solid(points,faces,"roof_terracotta",bevel=.004,
            color=(min(1,tone+.035),tone,max(.0,tone-.018),1))
    g.FACE_SMOOTH[-len(faces):]=[True]*len(faces)


def courtyard_lawn():
    # Broad sculpted planted ground, shallow enough for continuous walking.
    rim=[(-9,-5),(-7.5,-6),(7,-6),(9,-4.5),(9,4.7),(7.5,6),(-7,6),(-9,4.6)]
    n=len(rim)
    points=[(x,y,-.16) for x,y in rim]+[(x,y,.022) for x,y in rim]
    points.extend((x*.72,y*.72,.16+.035*math.sin(x)) for x,y in rim)
    points.append((0,0,.26))
    faces=[tuple(range(n-1,-1,-1))]
    for j in range(n):
        k=(j+1)%n
        faces.extend([(j,k,k+n,j+n),(j+n,k+n,k+2*n,j+2*n),
                      (j+2*n,k+2*n,3*n)])
    g.solid(points,faces,"foliage",bevel=.008)


def window_bay(x,y,z):
    """Shallow built shutters, reveal and sill, facing local +Y."""
    g.block(x,y+.30,z,1.35,.12,1.75,"dark_metal")
    for dx in [-.82,.82]:
        g.block(x+dx,y+.43,z-.12,.16,.18,2,"marble_white")
    for zz in [z-.15,z+1.72]:
        g.block(x,y+.45,zz,1.9,.3,.18,"marble_white")
    for dx in [-.63,.63]:
        g.block(x+dx,y+.4,z,.33,.12,1.65,"wood")


def shell(width,depth,height,closed=False):
    if closed:
        # Built basements absorb the urban slope without tilting the house.
        g.masonry(-width/2,width/2,depth/2,-1.8,0,.50,course=.45,brick=1.2)
        g.masonry(-width/2,width/2,-depth/2,-1.8,0,.50,course=.45,brick=1.2)
        for x in [-width/2,width/2]:
            rotate_geometry(lambda xx=x:g.masonry(-depth/2,depth/2,-xx,-1.8,0,.50),90)
    front_wall(width,depth,height,closed)
    wall(-width/2,width/2,-depth/2,height)
    side_wall(-width/2,-depth/2,depth/2,height)
    side_wall(width/2,-depth/2,depth/2,height)
    if closed:
        # Window bands, relief shutters and shallow projecting balconies.
        floors=max(1,round(height/3.6))
        for floor in range(floors):
            zz=1.2+floor*3.6
            for x in [-width*.32,0,width*.32]:
                if floor==0 and x==0:
                    continue
                g.block(x,depth/2+.30,zz,1.35,.12,1.75,"dark_metal")
                for dx in [-.82,.82]:
                    g.block(x+dx,depth/2+.43,zz-.12,.16,.18,2,"marble_white")
                g.block(x,depth/2+.45,zz+1.72,1.9,.3,.18,"marble_white")
                for dx in [-.63,.63]:
                    g.block(x+dx,depth/2+.4,zz,.33,.12,1.65,"wood")
            if floor:
                g.block(0,depth/2+.9,zz-.25,width*.72,1.5,.25,"marble_white")
                g.rail(0,depth/2+1.6,zz,width*.69)
            if zz+1.9<height:
                for yaw,span,offset in [(180,width,depth/2),(90,depth,width/2),(-90,depth,width/2)]:
                    for xx in [-span*.30,0,span*.30]:
                        rotate_geometry(lambda xx=xx,offset=offset,zz=zz:window_bay(xx,offset,zz),yaw)


def estate_parts(kind):
    """Complete aristocratic parcels rather than a scaled ordinary house."""
    if kind==4:
        return [(-11,0,10,24,10.8),(11,0,10,24,10.8),(0,-10,12,8,7.2)]
    return [(-11,0,10,28,14.4),(5,-7,22,14,10.8)]


def estate(kind,roof=False,collision=False):
    for x,y,width,depth,height in estate_parts(kind):
        start=len(g.VERTS)
        if roof:
            collision_roof(width,depth,height+.7) if collision else tiled_roof(width,depth,height+.7,kind)
        else:
            collision_house(width,depth,height) if collision else shell(width,depth,height,True)
        relief.transform_new(g,start,{"position":[x,y,0],"yaw":0},layout.ground_height,False)
    if roof:
        return
    # A gated colonnade opens onto the forecourt. It does not seal the passage.
    for x in [-15,-10,-5,5,10,15]:
        if collision:
            collision_column(x,16,4.8,.25)
        else:
            w.sculpted_column(x,16,0,4.8,.25)
    for x,width in [(-10,10),(10,10)]:
        if collision:
            collision_box(x,16,4.8,width,1.2,.45)
        else:
            g.block(x,16,4.8,width,1.2,.45,"marble_white")
            w.carved_frieze(x,16.65,4.85,width-.1)
    # Distinct built gardens sit inside the parcel, beside its open central walk.
    for x in ([-3.8,3.8] if kind==4 else [-2,10]):
        if collision:
            collision_box(x,7,-.15,2.5,6,.8)
        else:
            g.block(x,7,-.15,2.5,6,.55,"stone_cream")
            foliage.hedge(g,x=x,y=7,z=.4,length=2.1,depth=5.4,height=.7,seed=kind+12,material="foliage")


def important_room(building):
    width,depth,height=building["width"],building["depth"],building["height"]
    # Walking geometry is permanently visible; the four walls export separately.
    w.paving(-width/2+.3,width/2-.3,-depth/2+.3,depth/2-.3,0,variant=1)
    # Vestibule, door frames and a back reading/preparation chamber.
    for x in [-width*.25,width*.25]:
        if building["upstairs"] and x < 0:
            continue
        w.sculpted_column(x,depth*.12,0,height-.7,.41)
    if building["upstairs"]:
        # Actual stair to 4m: 20 even risers, 0.5m tread; composed build
        # broadens the public flight to the same 4m circulation requirement.
        g.stair_flight(-7,7,4 if DENSE else 3,.5,.2,.2,20,0,direction=-1)


def important_wall(building,side):
    width,depth,height=building["width"],building["depth"],building["height"]
    if side=="front":
        front_wall(width,depth,height)
    elif side=="rear":
        wall(-width/2,width/2,-depth/2,height)
    elif side=="west":
        side_wall(-width/2,-depth/2,depth/2,height)
    elif side=="east":
        side_wall(width/2,-depth/2,depth/2,height)
    elif side=="partition":
        y=-depth*.19
        wall(-width/2+.4,-3,y,height-1)
        wall(3,width/2-.4,y,height-1)
        g.arc(0,y,2.3,3,.35,.6,21)
    if side!="partition":
        yaw={"front":0,"rear":180,"west":90,"east":-90}[side]
        span=width if side in {"front","rear"} else depth
        offset=depth/2 if side in {"front","rear"} else width/2
        for fraction in [-.40,-.20,0,.20,.40]:
            if side=="front" and fraction==0:
                continue
            rotate_geometry(lambda x=span*fraction:window_bay(x,offset,height-2.6),yaw)


def pub_upper_deck():
    g.floor(-12.6,-3,-11.6,-3,4,tiles=False)
    g.floor(-3,12.6,-11.6,11.6,4,tiles=False)
    g.rail(-3,2.5,4,11,axis="y")
    for x in [0,5,9]:
        g.block(x,-8,4,2,.8,.65,"wood")
        g.block(x,-8,4.65,2.2,1,.2,"linen")


def chandelier():
    # Pivot at the glowing candles; ceiling chain extends upward, not through
    # the character. A circular frame gives the point light a physical source.
    g.turned(0,0,-.12,[(.85,0),(.88,.08),(.82,.14),(.79,.14),(.76,.05)],"bronze",48)
    for j in range(8):
        a=j*math.tau/8
        x,y=.8*math.cos(a),.8*math.sin(a)
        g.turned(x,y,0,[(.07,0),(.07,.22),(.025,.24)],"linen",16)
        g.rod((x,y,-.05),(0,0,1.15),.025,"dark_metal",10)
    for j in range(6):
        g.turned(0,0,1.15+j*.14,[(.032,0),(.055,.045),(.032,.09)],"dark_metal",12)


def table(x,y,z=0,width=2.5):
    for dx in [-width*.38,width*.38]:
        for dy in [-.4,.4]:
            g.block(x+dx,y+dy,z,.13,.13,.84,"wood")
    g.block(x,y,z+.86,width,1.2,.14,"wood")
    g.block(x,y,z+1.0,width-.12,1.13,.028,"linen")


def furniture(building):
    use,width,depth=building["use"],building["width"],building["depth"]
    for x in [-width*.29,width*.29]:
        if use == "pub" and x < 0:
            # The entire southwest flight and landing are circulation space.
            continue
        for y in [0,depth*.22]:
            table(x,y,width=3.8 if use=="casino" else 2.7)
            for dx in [-1,1]:
                w.chair(x+dx,y+1.3,0,principal=use=="casino")
            if use=="casino":
                for j in range(7):
                    g.turned(x+(j-3)*.23,y,.99,[(.10,0),(.10,.04)],"bronze",16)
            elif use=="pub":
                for j in [-1,1]:
                    w.amphora(x+j*.55,y,1.04,.29)
            else:
                g.block(x,y,1.04,1.4,.8,.08,"linen")
    for x in [-width*.34,width*.34]:
        w.bench(x,-depth*.38,3.2)
        w.chest(x,-depth*.35,0,width=1.8)
    for y in [-depth*.15,depth*.24]:
        for x in [-width/2+.8,width/2-.8]:
            w.amphora(x,y,0,1.35)
    if use=="pub":
        g.block(6,-7,0,7,1.2,1.02,"wood")
        g.block(6,-7,1.04,7.2,1.4,.13,"marble_white")
        for x in [3,6,9]:
            g.turned(x,-9,0,[(.48,0),(.58,.75),(.48,1.45)],"wood",32)
            for z in [.15,1.25]:
                g.turned(x,-9,z,[(.49,0),(.51,.06)],"dark_metal",32)
    else:
        for x in [-width*.30,width*.30]:
            table(x,-depth*.32,width=3.0)
            for j in range(5):
                g.block(x+(j-2)*.26,-depth*.32,1.05,.18,.44,.32,"burgundy")


def fountain():
    g.turned(0,0,-.05,[(4.1,0),(4.1,.35),(3.85,.6),(3.6,.6),(3.6,.19)],"marble_white",96)
    g.turned(0,0,0,[(.95,0),(.7,.4),(.42,.65),(.38,2),(.9,2.3),(.8,2.5),(.3,2.5),(.22,3.5)],"marble_white",64)
    for j in range(8):
        a=j*math.tau/8
        w.lozenge(3.98*math.cos(a),3.98*math.sin(a),.35,.4,.4,"bronze")


def garden_bed():
    g.block(0,0,-.1,9,5,.35,"stone_cream")
    g.block(0,0,.25,8.4,4.4,.14,"sand")
    for x in [-4.4,4.4]:
        g.block(x,0,.27,.24,5,.3,"marble_white")
    for y in [-2.4,2.4]:
        g.block(0,y,.27,9,.24,.3,"marble_white")
    foliage.hedge(g,z=.4,length=7.8,depth=3.4,height=1.0,material="foliage",seed=73)


def cypress():
    foliage.cypress(g,height=7.8,radius=.92,material="foliage",seed=17)


def hedge():
    g.block(0,0,-.05,8.2,1.35,.24,"stone_cream")
    foliage.hedge(g,z=.18,length=8,depth=1.25,height=1.45,material="foliage",seed=31)


def market_stock():
    table(0,0,width=4.0)
    for x in [-1.45,-.48,.48,1.45]:
        g.block(x,0,1.03,.80,.90,.13,"wood")
        for yy in [-.45,.45]:
            g.block(x,yy,1.03,.8,.06,.26,"wood")
        for j in range(5):
            xx=x+(j-2)*.11
            g.turned(xx,.1,1.19,[(.04,0),(.105,.10),(.085,.18),(.035,.22)],"pottery",16)
    for x in [-1.5,-.5,.5,1.5]:
        w.amphora(x,.34,1.19,.42)
    for x in [-1.7,1.7]:
        w.chest(x,-.15,0,width=.70,depth=.50,height=.65)


def merchant_cart():
    g.block(0,0,.94,2.25,3.25,.16,"wood")
    for x in [-1.16,1.16]:
        for y in [-1,1]:
            rings=[]
            for xx in [x-.07,x+.07]:
                for radius in [.44,.56]:
                    rings.extend((xx,y+radius*math.cos(j*math.tau/48),.59+radius*math.sin(j*math.tau/48)) for j in range(48))
            faces=[]
            for j in range(48):
                k=(j+1)%48
                faces.extend([(j,k,k+48,j+48),(j+96,k+96,k+144,j+144),
                              (j,k,k+96,j+96),(j+48,k+48,k+144,j+144)])
            g.solid(rings,faces,"wood",bevel=.012)
            for j in range(12):
                a=j*math.tau/12
                g.rod((x,y,.59),(x,y+.45*math.cos(a),.59+.45*math.sin(a)),.035,"wood",10)
            g.rod((x-.1,y,.59),(x+.1,y,.59),.12,"bronze",16)
    for x in [-1.1,1.1]:
        g.block(x,0,1.10,.12,3.25,.6,"wood")
    for y in [-1.56,1.56]:
        g.block(0,y,1.1,2.25,.12,.6,"wood")
    w.chest(-.45,-.6,1.1,width=.9,height=.85)
    w.chest(.45,.4,1.1,width=.9,height=.65)
    w.amphora(.5,-.75,1.1,.8)
    g.rod((-.9,-1.6,1.1),(-.9,-3.5,.4),.08,"wood",12)
    g.rod((.9,-1.6,1.1),(.9,-3.5,.4),.08,"wood",12)


def bridge_bay():
    """One 18m Roman arch bay, full-width vault and a level public deck."""
    g.arc(0,0,-9,8.2,.62,15.4,33)
    # Curved spandrels carry the level deck down to the actual vault, leaving
    # the semicircular water opening empty rather than suspending a thin slab.
    radius=8.82
    profile=[(radius*math.cos(math.pi-j*math.pi/48),-9+radius*math.sin(math.pi-j*math.pi/48))
             for j in range(49)]
    g.prism(profile+[(radius,-.08),(-radius,-.08)],-7.0,7.0)
    for z in [-7,-6.4,-5.8,-5.2,-4.6,-4,-3.4,-2.8,-2.2,-1.6,-1]:
        for x in [j*.58 for j in range(-14,15)]:
            inner=max(0,abs(x)-.24)
            if inner*inner+(z+9.46)**2>radius*radius and abs(x)+.26<radius:
                for y in [-7.08,7.08]:
                    g.block(x,y,z,.51,.11,.46,"stone_cream")
    for y in [-6.9,6.9]:
        wall(-10.2,-7.8,y,9.0,-9.2,1.2)
    g.block(-9,0,-9.2,2.4,14.0,9.1,"stone_cream")
    w.paving(-9,9,-7.5,7.5,.04,variant=1)
    # Solid back beneath the tessellated walkway, continuous into the arch.
    g.block(0,0,-.27,18,15.4,.25,"stone_cream")
    for y in [-7.45,7.45]:
        g.rail(0,y,.04,18)
        w.carved_frieze(0,y,-.75,17.7)
        for x in [-8,8]:
            g.turned(x,y,1.18,[(.16,0),(.28,.16),(.13,.35)],"bronze",20)


def bridge_end_pier():
    g.block(0,0,-9.2,2.4,14,9.2,"stone_cream")
    for y in [-7.1,7.1]:
        w.sculpted_column(0,y,0,3.7,.28)


def neighbour_gate():
    gate_frame()
    # A scenery closure only: no new portal, quest or district gameplay.
    for j in range(22):
        g.block((j-10.5)*.37,0,0,.35,.24,4.1,"wood")
    for z in [.4,1.4,2.8,3.8]:
        g.block(0,.15,z,8.3,.12,.10,"bronze")


def dock_pier():
    for j in range(26):
        g.block(-9+(j+.5)*18/26,0,-.18,18/26-.014,4.6,.18,"wood")
    for x in [-7,0,7]:
        for y in [-1.9,1.9]:
            g.turned(x,y,-5.5,[(.20,0),(.22,5.8)],"wood",20)
            g.turned(x,y,.08,[(.18,0),(.29,.17),(.17,.3)],"dark_metal",20)
    for y in [-1.95,1.95]:
        g.block(0,y,-.34,18,.26,.23,"wood")


def coastal_boat():
    # Closed clinker hull; keel, planks, gunwales and a real folded sail.
    n=48
    points=[]
    profile=[(.02,.08,-1.45),(1.2,4.5,-.50),(1.7,5.7,.30),(1.72,5.7,.65)]
    for rx,ry,z in profile:
        points.extend((rx*math.cos(j*math.tau/n),ry*math.sin(j*math.tau/n),z) for j in range(n))
    faces=[tuple(range(n-1,-1,-1)),tuple(range((len(profile)-1)*n,len(profile)*n))]
    for ring in range(len(profile)-1):
        for j in range(n):
            k=(j+1)%n
            faces.append((ring*n+j,ring*n+k,(ring+1)*n+k,(ring+1)*n+j))
    g.solid(points,faces,"wood",bevel=.025)
    for z,rx,ry in [(-.22,1.45,5.02),(.10,1.6,5.5),(.55,1.75,5.75)]:
        for j in range(n):
            a,b=j*math.tau/n,(j+1)*math.tau/n
            g.rod((rx*math.cos(a),ry*math.sin(a),z),(rx*math.cos(b),ry*math.sin(b),z),.045,"wood",8)
    g.rod((0,0,.65),(0,0,7.1),.085,"wood",16)
    g.rod((-2.2,0,6.25),(2.2,0,6.25),.065,"wood",12)
    w.cloth(0,0,6.25,4.4,4.9,folds=7,swag=.15,material="linen")
    for y in [-3.8,3.8]:
        g.block(0,y,.72,2.2,.50,.18,"wood")
    for x in [-1.7,1.7]:
        g.rod((x,1.1,.7),(0,0,6.1),.021,"linen",8)
    w.chest(.3,-1.8,.65,width=.9,height=.55)


def oldtown_bank():
    w.slab([(322,-151),(397,-151),(397,88),(322,88)],0,.65,"sand")
    for y in range(-139,84,12):
        g.block(322,y,-6,.55,12,6,"stone_cream")


def docks_warehouse_bank():
    w.slab([(-307,30),(-277,30),(-277,180),(-307,180)],0,.65,"stone_cream")
    for y in range(36,179,12):
        g.block(-277,y,-5.5,.55,12,5.5,"stone_cream")


def southern_context_bank():
    # The neighbouring silhouettes stand on land beyond the closed frontage.
    w.slab([(-220,306),(240,306),(240,372),(-220,372)],0,.6,"sand")
    for x in [-182,20]:
        w.paving(x-6,x+6,306,335,.035,variant=1)


def neighbour_landmark(kind):
    height=13 if kind=="downtown" else 15
    shell(28,20,height,True)
    tiled_roof(28,20,height+.7)
    for x in [-11,11]:
        g.turned(x,0,height,[(3.0,0),(3.0,1.0),(2.8,2.0),(1.8,3.1),(.05,4.0)],"bronze",48)
    if kind=="palacedomain":
        for x in [-9,-3,3,9]:
            w.sculpted_column(x,11,0,7.4,.33)


def contextual_edges():
    # Rubicund and Arching Bridge: eastern crossing, not a painted road ending.
    for x in [243,261,279,297,315,333]:
        place("ard-bridge-bay",x,-85,role="bridge",occluder=False)
    place("ard-bridge-end-pier",342,-85,role="bridge",occluder=False)
    bank=place("ard-oldtown-bank",0,441,role="background",occluder=False)
    bank.update(collision=False,scale=[1,14,1])
    # Continue the opposite shore beyond the player frustums, with no collision.
    bank=place("ard-oldtown-bank",-9263,441,-.03,role="background",occluder=False)
    bank.update(collision=False,scale=[30,14,1])
    place("ard-neighbour-gate",344,-85,yaw=90,occluder=False)
    oldtown_plots=[(x,y) for x in [367,389] for y in [-136,-112,-88,-64,-40,-16,8,32,56]]
    for j,(x,y) in enumerate(oldtown_plots):
        for mesh in [f"ard-house-{j%6}",f"ard-house-roof-{j%6}"]:
            place(mesh,x,y,yaw=-90,role="background",occluder=False)["collision"]=False
    for y in range(-229,170,12):
        place("ard-quay",328,y,role="background",occluder=False)["collision"]=False
    for x in [353,377]:
        for y in range(-175,122,12):
            place("ard-road",x,y,role="background",occluder=False)["collision"]=False
    for x in [344,356,368]:
        place("ard-road",x,-85,role="background",occluder=False)["collision"]=False
    # Both shores meet their bridge and retain the water without gaps.
    for y in range(-133,98,12):
        place("ard-quay",234,y,yaw=180,role="floor",occluder=False)
    # Docks visible beyond Water Gate; separate working wharf and moored boats.
    bank=place("ard-docks-bank",0,-1470,role="background",occluder=False)
    bank.update(collision=False,scale=[1,14,1])
    for y in [101,124,152]:
        for x in [-220,-238,-256,-274]:
            place("ard-dock-pier",x,y,role="background",occluder=False)["collision"]=False
    for x,y in [(-237,124),(-265,152),(-283,101),(-219,152)]:
        place("ard-market-stock",x,y,role="background",occluder=False)["collision"]=False
    for x,y,yaw in [(-240,113,0),(-265,136,0),(-249,87,18)]:
        item=place("ard-coastal-boat",x,y,-2.7,yaw=yaw,role="background",occluder=False)
        item["collision"]=False
    for j,y in enumerate([48,78,140,169]):
        for mesh in [f"ard-house-{j%3}",f"ard-house-roof-{j%3}"]:
            place(mesh,-290,y,yaw=90,role="background",occluder=False)["collision"]=False
    # Southern streets physically touch their closed future city frontages.
    place("ard-southern-context-bank",0,0,role="background",occluder=False)["collision"]=False
    # A continuous land apron also covers both flanking houses at the south.
    bank=place("ard-oldtown-bank",-4104,2118,-.03,role="background",occluder=False)
    bank.update(collision=False,scale=[12,12,1])  # x[-240,660], y[306,3174].
    add_road([-182,292],[-182,317])
    add_road([20,292],[20,317])
    for x in range(-214,241,12):
        if min(abs(x+182),abs(x-20))>14:
            place("ard-boundary",x,317)
    for x,kind in [(-182,"palacedomain"),(20,"downtown")]:
        place("ard-neighbour-gate",x,317,occluder=False)
        place("ard-context-"+kind,x,341,yaw=180,role="background",occluder=False)["collision"]=False
        for j,dx in enumerate([-39,39]):
            for mesh in [f"ard-house-{j+3}",f"ard-house-roof-{j+3}"]:
                place(mesh,x+dx,340,yaw=180,role="background",occluder=False)["collision"]=False


def stall():
    for x in [-2.8,2.8]:
        for y in [-1.6,1.6]:
            g.block(x,y,0,.16,.16,3.7,"wood")
    for j in range(7):
        g.block(0,-1.3,.1+j*.11,5.6,1.1,.08,"wood")
    g.block(0,-1.3,.95,5.7,1.2,.13,"wood")
    for j in range(6):
        w.amphora((j-2.5)*.72,-1.3,1.08,.45)
    g.block(0,0,3.65,6.2,3.8,.14,"linen")
    w.cloth(0,1.87,3.67,6.2,.72,folds=6,material="burgundy")


def gate_frame():
    for x in [-7.0,7.0]:
        g.block(x,0,0,5.2,5.2,11,"stone_cream")
        for z in [0,4,8,11]:
            g.block(x,0,z,5.6,5.6,.3,"marble_white")
        for j in [-1,0,1]:
            g.block(x+j*1.65,0,11.3,.8,5.2,.8,"marble_white")
        for z in [2,6,9]:
            g.block(x,2.66,z,1.1,.14,1.9,"dark_metal")
    g.arc(0,0,4.0,4.3,.75,3.5,29)
    g.block(0,0,9,10,3.5,1.3,"stone_cream")
    w.carved_frieze(0,1.92,9.4,9.4)


def hippodrome_track():
    # Real stadium: 104m straight sections, semicircular turns, 76 by 180m.
    w.slab(relief.stadium_points(segments=128),0,.32,"sand")
    g.block(0,0,.01,6,104,.22,"stone_cream")
    for y in [-49,-32,-16,0,16,32,49]:
        g.turned(0,y,.23,[(.7,0),(.6,.35),(.42,1),(.28,2.1),(.06,4)],"marble_white",32)
    for y in [-51,51]:
        for x in [-2.1,2.1]:
            g.turned(x,y,.23,[(.5,0),(.45,.4),(.3,1.8),(.4,2.0),(.1,2.9)],"bronze",32)
    # Edging articulates the course without fencing out physical circulation.
    for x in [-37.6,37.6]:
        g.block(x,0,0,.45,104,.18,"marble_white")


def stand():
    for j in range(6):
        g.block(0,-j*.82,j*.32,8,.8,.32,"stone_cream")
        g.block(0,-j*.82,(j+1)*.32,7.7,.53,.13,"marble_white")
    g.stair_flight(0,0,4 if DENSE else 2.1,.82,.32,.32,6,0,direction=-1)
    for x in [-3.7,3.7]:
        w.sculpted_column(x,-5,0,5.6,.27)


def boundary_segment():
    g.masonry(-6,6,0,-.6,4,.7,.6,1.1)
    for x in [-5.5,-3.3,-1.1,1.1,3.3,5.5]:
        g.block(x,0,4,.65,.82,.65,"marble_white")
    g.block(0,0,3.7,12,.85,.30,"marble_white")


def river_parapet():
    """A low sculpted promenade edge keeps the river visible to the player."""
    g.block(0,0,-1.5,12,.66,1.66,"stone_cream")
    g.block(0,0,.13,12,.76,.14,"marble_white")
    for j in range(15):
        x=-5.6+j*.8
        g.turned(x,0,.26,[(.11,0),(.17,.12),(.10,.25),(.14,.5),(.11,.73)],"marble_white",16)
    g.block(0,0,1.0,12,.64,.18,"marble_white")
    for x in [-6,6]:
        g.block(x,0,.18,.52,.72,.95,"stone_cream")
        g.block(x,0,1.1,.66,.84,.15,"marble_white")


def ground():
    relief.terrain(g,layout.foundation_height,smooth_top=True,spacing=TERRAIN_SPACING,refinements=TERRAIN_REFINEMENTS)


def road_piece(backing=True):
    # Broad dressed paving module, variable floor seeds and staggered joints.
    w.paving(-6,6,-6,6,.035,variant=1,backing=backing)


def quay_piece(backing=True,paving_rects=None):
    for x0,x1,y0,y1 in ([(-6,6,-6,6)] if paving_rects is None else paving_rects):
        w.paving(x0,x1,y0,y1,.04,variant=2,backing=backing)
    g.block(-5.8,0,-3,.5,12,3,"stone_cream")
    for y in [-5.6,5.6]:
        g.turned(-5.3,y,0,[(.18,0),(.18,.60),(.28,.72)],"dark_metal",20)


def add_road(a,b,width=12):
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=math.hypot(dx,dy)
    # Edge-following paving shares a continuous underlying ground surface.
    count=max(1,math.ceil(length/11.8))
    yaw=90-math.degrees(math.atan2(dy,dx))
    # Cardinal modules already align; retain their exact slab pattern and hash.
    if abs(dx)<1e-9 or abs(dy)<1e-9:
        yaw=math.degrees(math.atan2(dy,dx))-90
    for j in range(count):
        t=(j+.5)/count
        place("ard-road",a[0]+dx*t,a[1]+dy*t,yaw=yaw,role="floor",occluder=False)


def gardens():
    # Symmetrical estate garden; paths stay 6m clear around each bed.
    for origin in [(-127,73),(-53,182),(0,76),(88,272)]:
        x,y=origin
        spread=31 if origin==(-53,182) else 26
        for dx in [-spread,spread]:
            for dy in [-24,-8,8,24]:
                if origin==(-127,73) and abs(dy)<24:
                    continue
                place("ard-garden-bed",x+dx,y+dy,role="landscape",occluder=False)
        for dx in [-32,32]:
            for dy in [-32,-16,0,16,32]:
                place("ard-cypress",x+dx,y+dy,role="vegetation",occluder=False)
    for x,y in [(-127,73),(88,272),(-69,226),(-26,34),(26,34)]:
        place("ard-fountain",x,y,role="fountain",occluder=False)
        WATERS.append({"position":[x,y,.27],"size":[6.8,6.8]})
    # Natural Pool is a real sunken basin, with broad flat promenade all round.
    WATERS.append({"position":[-127,73,-.05],"size":[35,23]})
    for y in [58,88]:
        for x in [-143,-127,-111]:
            place("ard-hedge",x,y,role="landscape",occluder=False)
    for x in [-153,-101]:
        for y in [63,83]:
            place("ard-bench",x,y,role="furniture",occluder=False)
    if DENSE:
        for (x,y),spread in [((-127,73),31),((-53,182),36),((0,76),30),((88,272),30)]:
            for dx in [-spread,spread]:
                for dy in [-26,-9,9,26]:
                    place("ard-courtyard-lawn",x+dx,y+dy,role="landscape",occluder=False)
                    # Every lawn has planted volume, rather than green flat land.
                    place("ard-garden-bed",x+dx,y+dy,role="landscape",occluder=False)
            for dx in [-spread-5,spread+5]:
                for dy in range(-31,32,8):
                    place("ard-cypress",x+dx,y+dy,role="vegetation",occluder=False)
            for dy in [-34,34]:
                for dx in range(-24,25,8):
                    place("ard-hedge",x+dx,y+dy,role="landscape",occluder=False)


def secondary_houses():
    # Deliberate curved street frontages with coherent small blocks, not random
    # objects scattered over an empty plane. Street lanes leave >=6m passages.
    rows=[(-190,-130,6,18),(-175,-94,5,15),(-149,-54,3,14),
          (122,-126,6,17),(128,-87,5,17),(139,-37,4,17),
          (-172,14,4,15),(-167,132,4,16),(-166,239,8,16),
          (-166,273,8,16),(-64,265,7,17),(-70,135,4,16),
          (59,108,5,15),(115,16,4,16),(165,113,5,13),
          (8,239,4,15)]
    rng=random.Random(1061021)
    occupied=[]
    courtyard_objects=[]
    # Supplemental compact urban plots fill the gaps between the deliberately
    # curved frontage rows. Reserved boulevards, estates and squares remain open.
    rows.extend(((-174+(row%3)*4, -126+row*26, 24, 17)
                 for row in range(16)))
    candidates=[]
    if DENSE:
        # Two continuous street frontages per boulevard. Houses face their own
        # pavement; courtyard gardens lie behind them. No arbitrary scatter.
        for row,(a,b) in enumerate(STREETS):
            dx,dy=b[0]-a[0],b[1]-a[1]
            length=math.hypot(dx,dy)
            for side in [-1,1]:
                count=max(1,int(length/18))
                for rear,setback in enumerate([20,39,58]):
                    for j in range(count):
                        u=(j+.5+rear*.24)/count
                        if u>.98:
                            continue
                        family=(j+row*6+(side+1)//2*3+rear)%6
                        parcel_setback=setback+(9 if rear==0 and family>=4 else 0)
                        x=a[0]+dx*u-side*dy/length*parcel_setback
                        y=a[1]+dy*u+side*dx/length*parcel_setback
                        yaw=math.degrees(math.atan2(-side*dy,-side*dx))
                        candidates.append((row*6+(side+1)//2*3+rear,j,x,y,yaw))
        # The urban frontage outside Gauntlet follows its ellipse.
        for j in range(48):
            a=j*math.tau/48
            x,y=126*math.cos(a),-65+107*math.sin(a)
            yaw=math.degrees(math.atan2(x,-(y+65)))
            candidates.append((1000,j,x,y,yaw))
    for row,(x0,y0,count,step) in enumerate(rows):
        for j in range(count):
            candidates.append((2000+row if DENSE else 100+row,j,x0+j*step,y0+2.5*math.sin(j*.85+row*.61),
                               0 if row%3 else 180))
    # Reserve complete manor parcels before fitting the smaller street houses.
    # This preserves wings and forecourts instead of squeezing them into gaps.
    candidates.sort(key=lambda candidate:((candidate[0]+candidate[1])%6<4))
    for row,j,x,y,yaw in candidates:
            if DENSE and row>=2000:
                closest=None
                for a,b in STREETS:
                    dx,dy=b[0]-a[0],b[1]-a[1]
                    u=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
                    qx,qy=a[0]+u*dx,a[1]+u*dy
                    distance=math.hypot(qx-x,qy-y)
                    if closest is None or distance<closest[0]:
                        closest=(distance,qx,qy)
                yaw=math.degrees(math.atan2(-(closest[1]-x),closest[2]-y))
            # Outside the ellipse + a 7m clear Gauntlet Street ring.
            if (x/103)**2+((y+65)/87)**2 < 1.12:
                continue
            variant=(j+row)%6
            bounds=next(m for m in g.PIECES if m["id"]==f"ard-house-{variant}")["boundsBlender"]
            local_rx=max(abs(bounds[0][0]),abs(bounds[1][0]))
            local_ry=max(abs(bounds[0][1]),abs(bounds[1][1]))
            c,s=abs(math.cos(math.radians(yaw))),abs(math.sin(math.radians(yaw)))
            rx,ry=c*local_rx+s*local_ry,s*local_rx+c*local_ry
            if x+rx>227 or x-rx < -196 or y-ry < -141 or y+ry>300:
                continue
            if any(houses_overlap(x,y,local_rx,local_ry,yaw,other) for other in occupied):
                continue
            # Monument ellipse also reserves the full half-diagonal of a house.
            if (x/(103+rx))**2+((y+65)/(87+ry))**2 < 1.08:
                continue
            reserved=[(-170,-86,36,113),(-95,-11,142,255),
                      (-36,36,40,111),(-190,-125,140,211),
                      (95,203,90,280),(45,131,257,303)]
            if any(x+rx>a and x-rx<b and y+ry>c and y-ry<d for a,b,c,d in reserved):
                continue
            box=[x-rx-4,y-ry-4,x+rx+4,y+ry+4]
            if any(segment_box(a,b,box) for a,b in STREETS):
                continue
            walk_route=layout.VISIT_ROUTE if DENSE else layout.ROUTE
            if any(segment_box(a,b,box) for a,b in zip(walk_route,walk_route[1:])):
                continue
            if any(abs(x-b["position"][0])<b["width"]/2+rx+4 and abs(y-b["position"][1])<b["depth"]/2+ry+4 for b in layout.BUILDINGS):
                continue
            body_id=f"house-{row:02d}-{j:02d}"
            place(f"ard-house-{variant}",x,y,yaw=yaw,tag=body_id)
            occupied.append((x,y,local_rx,local_ry,yaw))
            roof=place(f"ard-house-roof-{variant}",x,y,yaw=yaw,role="roof",tag=f"roof-house-{row:02d}-{j:02d}")
            # The engine propagates body cutaway to its roof and foundations.
            roof["supportsObject"]=body_id
            if j%2==0:
                courtyard_objects.append(("ard-amphora",x+5.9,y+7,0,"furniture"))
            if rng.random()<.65:
                courtyard_objects.append(("ard-cypress",x-5.3,y-6.5,0,"vegetation"))
            if DENSE:
                ca,sa=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
                backx,backy=x+sa*(local_ry+4),y-ca*(local_ry+4)
                # Ornamented courtyard, no garden in the public entrance.
                courtyard_objects.extend([
                    ("ard-cypress",backx-3*ca,backy-3*sa,0,"vegetation"),
                    ("ard-cypress",backx+3*ca,backy+3*sa,0,"vegetation"),
                    ("ard-hedge",backx,backy,yaw,"landscape")])
    for mesh,x,y,yaw,role in courtyard_objects:
        place(mesh,x,y,yaw=yaw,role=role,occluder=False)


def reuse_arena():
    source=ROOT/"Source/Elements/Assets/Built/arena-fate-modern/manifest.json"
    if not source.is_file():
        raise RuntimeError("The validated Arena manifest is required; do not regenerate it.")
    data=json.loads(source.read_text(encoding="utf-8"))
    allowed={"afm-arcade-sculpted","afm-attic","afm-attic-relief","afm-arcade-relief",
             "afm-south-threshold-pylon","afm-south-threshold-side","afm-south-threshold-textile",
             "afm-ground-arcade-support","afm-sand","afm-statue-course","afm-middle-course",
             "afm-ring-ground","afm-ring-upper","afm-ring-gallery"}
    meshes={m["id"]:m for m in data["meshes"]}
    for item in data["objects"]:
        if item.get("meshId") not in allowed and not item.get("meshId","").startswith(("afm-seats-","afm-seating-relief-")):
            continue
        mi=meshes[item["meshId"]]
        position=[item["position"][i]+layout.ARENA[i] for i in range(3)]
        OBJECTS.append({"id":"reused-"+item["id"],
            "mesh":"Built/arena-fate-modern/"+mi["file"],
            "position":position,"yaw":item.get("yaw",0),"role":"monument","occluder":True})
    # Exterior visual shell only. Closed matte backing prevents holes through
    # arcade mouths from showing nonexistent rooms on the exterior map. South
    # gap remains the actual Arena portal; the complete interior lives there.
    for j in range(96):
        a=(j+.5)*math.tau/96
        x,y=89.5*math.cos(a),-65+73*math.sin(a)
        if abs(x)<8 and y>0:
            continue
        yaw=math.degrees(math.atan2(73*math.cos(a),-89.5*math.sin(a)))
        place("ard-arena-backing",x,y,yaw=yaw,role="monument")


def collision_solid(points,faces):
    """Unbevelled physical geometry; no painted/sculpted visual is replaced."""
    g.solid(points,faces,"stone_cream",bevel=0)


def collision_box(x,y,z,width,depth,height):
    a,b,c,d=x-width/2,x+width/2,y-depth/2,y+depth/2
    collision_solid([(a,c,z),(b,c,z),(b,d,z),(a,d,z),
                     (a,c,z+height),(b,c,z+height),(b,d,z+height),(a,d,z+height)],
                    [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


def collision_prism(profile,y0,y1):
    n=len(profile)
    collision_solid([(x,y0,z) for x,z in profile]+[(x,y1,z) for x,z in profile],
                    [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+
                    [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)])


def collision_slab(points,z,thickness=.25):
    n=len(points)
    collision_solid([(x,y,z-thickness) for x,y in points]+[(x,y,z) for x,y in points],
                    [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+
                    [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)])


def collision_turned(x,y,z,profile,sides=12):
    points=[(x+r*math.cos(j*math.tau/sides),y+r*math.sin(j*math.tau/sides),z+h)
            for r,h in profile for j in range(sides)]
    faces=[tuple(range(sides-1,-1,-1)),tuple(range((len(profile)-1)*sides,len(profile)*sides))]
    for ring in range(len(profile)-1):
        for j in range(sides):
            k=(j+1)%sides
            faces.append((ring*sides+j,ring*sides+k,(ring+1)*sides+k,(ring+1)*sides+j))
    collision_solid(points,faces)


def collision_arch(x,y,spring,radius,thickness,depth,segments=21):
    for j in range(segments):
        a,b=j*math.pi/segments,(j+1)*math.pi/segments
        collision_prism([(x+radius*math.cos(a),spring+radius*math.sin(a)),
                         (x+(radius+thickness)*math.cos(a),spring+(radius+thickness)*math.sin(a)),
                         (x+(radius+thickness)*math.cos(b),spring+(radius+thickness)*math.sin(b)),
                         (x+radius*math.cos(b),spring+radius*math.sin(b))],y-depth/2,y+depth/2)


def collision_stairs(cx,start_y,width,tread,first_top,delta_z,count,base_z,direction=-1):
    profile=[(start_y,base_z),(start_y,first_top)]
    for j in range(count):
        end=start_y+direction*(j+1)*tread
        profile.append((end,first_top+j*delta_z))
        if j<count-1:
            profile.append((end,first_top+(j+1)*delta_z))
    profile.append((start_y+direction*count*tread,base_z))
    n=len(profile)
    collision_solid([(cx-width/2,y,z) for y,z in profile]+[(cx+width/2,y,z) for y,z in profile],
                    [tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+
                    [(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)])


def collision_column(x,y,height,radius):
    collision_turned(x,y,0,[(radius*1.4,0),(radius*1.4,.22),(radius,.22),
                           (radius,height-.3),(radius*1.35,height-.3),(radius*1.35,height)])


def collision_front(width,depth,height,closed=False):
    y=depth/2
    door=2.7 if closed else 5.0
    for x0,x1 in [(-width/2,-door/2),(door/2,width/2)]:
        collision_box((x0+x1)/2,y,0,x1-x0,.56,height)
    collision_arch(0,y,2.9,door/2,.4,.58)
    lintel=2.9+door/2+.3
    if height>lintel:
        collision_box(0,y,lintel,door,.56,height-lintel)
    if closed:
        collision_box(0,y+.12,0,2.585,.10,3.0)
    for x in [-width*.37,width*.37]:
        collision_column(x,y+.65,min(height,6),.30)


def collision_house(width,depth,height):
    collision_box(0,0,-1.8,width,depth,1.8)
    collision_front(width,depth,height,True)
    collision_box(0,-depth/2,0,width,.56,height)
    for x in [-width/2,width/2]:
        collision_box(x,0,0,.56,depth,height)
    # Closed house floors are level with the same continuous district ground.
    collision_box(0,0,-.25,width-.56,depth-.56,.25)
    for floor in range(1,max(1,round(height/3.6))):
        zz=1.2+floor*3.3
        collision_box(0,depth/2+.9,zz-.25,width*.72,1.5,.25)
        collision_box(0,depth/2+1.6,zz,width*.69,.43,1.15)


def collision_roof(width,depth,z):
    rise=width*.24
    collision_prism([(-width/2-.7,z),(0,z+rise),(width/2+.7,z),
                     (width/2+.7,z-.17),(-width/2-.7,z-.17)],-depth/2-.65,depth/2+.65)
    collision_box(-width*.25,0,z+rise*.54,1.4,1.1,1.8)


def collision_room(building):
    width,depth,height=building["width"],building["depth"],building["height"]
    collision_box(0,0,-.24,width-.6,depth-.6,.24)
    for x in [-width*.25,width*.25]:
        if building["upstairs"] and x<0:
            continue
        collision_column(x,depth*.12,height-.7,.41)
    if building["upstairs"]:
        collision_stairs(-7,7,4,.5,.2,.2,20,0)


def collision_room_wall(building,side):
    width,depth,height=building["width"],building["depth"],building["height"]
    if side=="front":
        collision_front(width,depth,height)
    elif side=="rear":
        collision_box(0,-depth/2,0,width,.56,height)
    elif side in {"west","east"}:
        collision_box((-1 if side=="west" else 1)*width/2,0,0,.56,depth,height)
    else:
        y=-depth*.19
        for x0,x1 in [(-width/2+.4,-3),(3,width/2-.4)]:
            collision_box((x0+x1)/2,y,0,x1-x0,.56,height-1)
        collision_arch(0,y,2.3,3,.35,.6)


def collision_upper_deck():
    collision_box(-7.8,-7.3,3.75,9.6,8.6,.25)
    collision_box(4.8,0,3.75,15.6,23.2,.25)
    collision_box(-3,2.5,4,.43,11,1.15)
    for x in [0,5,9]:
        collision_box(x,-8,4,2.2,1,.85)


def collision_table(x,y,width):
    for dx in [-width*.38,width*.38]:
        for dy in [-.4,.4]:
            collision_box(x+dx,y+dy,0,.13,.13,.86)
    collision_box(x,y,.86,width,1.2,.17)


def collision_bench(x,y,width=2.9):
    for dx in [-width*.37,width*.37]:
        collision_box(x+dx,y,.03,.16,.57,.46)
    collision_box(x,y,.49,width,.56,.11)
    collision_box(x,y-.27,.55,width,.15,.57)


def collision_furniture(building):
    use,width,depth=building["use"],building["width"],building["depth"]
    for x in [-width*.29,width*.29]:
        if use=="pub" and x<0:
            continue
        for y in [0,depth*.22]:
            collision_table(x,y,3.8 if use=="casino" else 2.7)
            scale=1.12 if use=="casino" else .84
            for dx in [-1,1]:
                collision_box(x+dx,y+1.3,0,1.02*scale,.8*scale,.65)
                collision_box(x+dx,y+1.3-.34*scale,.60,1.02*scale,.15,1.2 if use=="casino" else .83)
    for x in [-width*.34,width*.34]:
        collision_bench(x,-depth*.38,3.2)
        collision_box(x,-depth*.35,0,1.84,.62,.72)
    for y in [-depth*.15,depth*.24]:
        for x in [-width/2+.8,width/2-.8]:
            collision_turned(x,y,0,[(.26,0),(.53,.65),(.25,1.55)])
    if use=="pub":
        collision_box(6,-7,0,7.2,1.4,1.17)
        for x in [3,6,9]:
            collision_turned(x,-9,0,[(.48,0),(.58,.75),(.48,1.51)])
    else:
        for x in [-width*.30,width*.30]:
            collision_table(x,-depth*.32,3.0)


def collision_cypress():
    sides=10
    points=[]
    radius=.92*.18
    for j in range(10):
        cx=.06*.92*math.sin(j*.8)
        z=7.8*j/10
        points.extend((cx+radius*math.cos(k*math.tau/sides),radius*math.sin(k*math.tau/sides),z)
                      for k in range(sides))
    faces=[tuple(range(sides-1,-1,-1)),tuple(range(9*sides,10*sides))]
    faces.extend((j*sides+k,j*sides+(k+1)%sides,(j+1)*sides+(k+1)%sides,(j+1)*sides+k)
                 for j in range(9) for k in range(sides))
    collision_solid(points,faces)


def collision_hedge():
    collision_box(0,0,-.05,8.2,1.35,.24)
    # Main rounded hedge body, without exporting individual leaves to physics.
    outline=[(-4.36,-.50),(-4.1,-.84),(4.1,-.84),(4.36,-.50),
             (4.36,.50),(4.1,.87),(-4.1,.87),(-4.36,.50)]
    collision_slab(outline,1.90,1.71)


def collision_garden():
    collision_box(0,0,-.1,9,5,.35)
    collision_box(0,0,.25,8.4,4.4,1.35)
    for x in [-4.4,4.4]:
        collision_box(x,0,.27,.24,5,.3)
    for y in [-2.4,2.4]:
        collision_box(0,y,.27,9,.24,.3)


def collision_ground():
    relief.terrain(g,layout.foundation_height,spacing=TERRAIN_SPACING,refinements=TERRAIN_REFINEMENTS)


def collision_quay(spacing=2):
    for ix in range(round(12/spacing)):
        for iy in range(round(12/spacing)):
            collision_box(-6+(ix+.5)*spacing,-6+(iy+.5)*spacing,-.20,spacing,spacing,.24)
    collision_box(-5.8,0,-3,.5,12,3)
    for y in [-5.6,5.6]:
        collision_turned(-5.3,y,0,[(.18,0),(.18,.6),(.28,.72)])


def collision_track():
    collision_slab(relief.stadium_points(segments=128),0,.32)
    collision_box(0,0,.01,6,104,.22)
    for y in [-49,-32,-16,0,16,32,49]:
        collision_turned(0,y,.23,[(.7,0),(.42,1),(.06,4)])


def collision_stand():
    for j in range(6):
        collision_box(0,-j*.82,j*.32,8,.8,.32)
        collision_box(0,-j*.82,(j+1)*.32,7.7,.53,.13)
    collision_stairs(0,0,4,.82,.32,.32,6,0)
    for x in [-3.7,3.7]:
        collision_column(x,-5,5.6,.27)


def collision_gate(closed=False):
    for x in [-7,7]:
        collision_box(x,0,0,5.2,5.2,11.3)
    collision_arch(0,0,4,4.3,.75,3.5,29)
    collision_box(0,0,9,10,3.5,1.3)
    if closed:
        collision_box(0,0,0,8.3,.24,4.1)


def collision_bridge():
    collision_box(0,0,-.27,18,15.4,.31)
    collision_box(-9,0,-9.2,2.4,14,9.2)
    collision_arch(0,0,-9,8.2,.62,15.4,33)
    radius=8.82
    profile=[(radius*math.cos(math.pi-j*math.pi/48),-9+radius*math.sin(math.pi-j*math.pi/48)) for j in range(49)]
    collision_prism(profile+[(radius,-.08),(-radius,-.08)],-7,7)
    for y in [-7.45,7.45]:
        collision_box(0,y,.04,18,.43,1.15)


def collision_fountain():
    # The sunken bowl remains open: water must never become a solid disk.
    n=48
    points=[(r*math.cos(j*math.tau/n),r*math.sin(j*math.tau/n),z)
            for r,z in [(4.1,-.05),(4.1,.55),(3.6,.55),(3.6,.14)] for j in range(n)]
    faces=[]
    for ring in range(4):
        for j in range(n):
            k=(j+1)%n
            faces.append((ring*n+j,ring*n+k,((ring+1)%4)*n+k,((ring+1)%4)*n+j))
    collision_solid(points,faces)
    collision_turned(0,0,0,[(.95,0),(.7,.4),(.38,2),(.9,2.5),(.22,3.5)])


def collision_stall():
    for x in [-2.8,2.8]:
        for y in [-1.6,1.6]:
            collision_box(x,y,0,.16,.16,3.7)
    collision_box(0,-1.3,.1,5.7,1.2,.98)
    collision_box(0,0,3.65,6.2,3.8,.14)


def collision_stock():
    collision_table(0,0,4)
    collision_box(0,0,1.03,3.8,1.0,.65)
    for x in [-1.7,1.7]:
        collision_box(x,-.15,0,.74,.54,.74)


def collision_cart():
    collision_box(0,0,.45,2.4,3.25,1.3)
    for x in [-1.16,1.16]:
        for y in [-1,1]:
            collision_box(x,y,.03,.14,1.12,1.12)
    collision_box(-.45,-.6,1.1,.94,.62,.94)
    collision_box(.45,.4,1.1,.94,.62,.74)


def collision_lawn():
    rim=[(-9,-5),(-7.5,-6),(7,-6),(9,-4.5),(9,4.7),(7.5,6),(-7,6),(-9,4.6)]
    n=len(rim)
    points=[(x,y,-.16) for x,y in rim]+[(x,y,.022) for x,y in rim]
    points.extend((x*.72,y*.72,.16+.035*math.sin(x)) for x,y in rim)
    points.append((0,0,.26))
    faces=[tuple(range(n-1,-1,-1))]
    for j in range(n):
        k=(j+1)%n
        faces.extend([(j,k,k+n,j+n),(j+n,k+n,k+2*n,j+2*n),(j+2*n,k+2*n,3*n)])
    collision_solid(points,faces)


def collision_specs():
    specs={"ard-road":lambda:collision_box(0,0,-.205,12,12,.24),
        "ard-quay":collision_quay,"ard-ground":collision_ground,
        "ard-cypress":collision_cypress,"ard-noble-tree":lambda:collision_turned(0,0,0,[(.38,0),(.27,4.6)]),
        "ard-hedge":collision_hedge,"ard-garden-bed":collision_garden,
        "ard-arena-backing":lambda:collision_box(0,0,0,6.8,.48,45),
        "ard-boundary":lambda:collision_box(0,0,-.587,12,.85,5.237),
        "ard-gate":collision_gate,"ard-neighbour-gate":lambda:collision_gate(True),
        "ard-bridge-bay":collision_bridge,
        "ard-bridge-end-pier":lambda:collision_box(0,0,-9.2,2.4,14,9.2),
        "ard-track":collision_track,"ard-stand":collision_stand,
        "ard-stand-roof":lambda:collision_roof(8.6,6.1,5.8),
        "ard-bench":lambda:collision_bench(0,0),"ard-amphora":lambda:collision_turned(0,0,0,[(.25,0),(.50,.6),(.22,1.44)]),
        "ard-lamp":lambda:collision_turned(0,0,0,[(.5,0),(.5,.15),(.35,1.4),(.31,2.23)]),
        "ard-chandelier":lambda:collision_turned(0,0,-.12,[(.88,0),(.88,.38),(.07,.38),(.07,2.13)]),
        "ard-fountain":collision_fountain,"ard-stall":collision_stall,
        "ard-market-stock":collision_stock,"ard-merchant-cart":collision_cart,
        "ard-cloaked-brewer-upper-deck":collision_upper_deck,
        "ard-courtyard-lawn":collision_lawn}
    for j in range(6):
        width,depth,height=11+j%3*.9,12+(j%2)*2.1,(7.2,10.8,10.8,7.2,10.8,14.4)[j]
        if j>=4:
            specs[f"ard-house-{j}"]=lambda jj=j:estate(jj,collision=True)
            specs[f"ard-house-roof-{j}"]=lambda jj=j:estate(jj,roof=True,collision=True)
        else:
            specs[f"ard-house-{j}"]=lambda ww=width,dd=depth,hh=height:collision_house(ww,dd,hh)
            specs[f"ard-house-roof-{j}"]=lambda ww=width,dd=depth,hh=height:collision_roof(ww,dd,hh+.7)
    for building in layout.BUILDINGS:
        identifier="ard-"+building["id"]
        specs[identifier]=lambda b=building:collision_room(b)
        specs[identifier+"-furniture"]=lambda b=building:collision_furniture(b)
        specs[identifier+"-roof"]=lambda b=building:collision_roof(b["width"],b["depth"],b["height"]+.7)
        for side in ["front","rear","west","east"]+([] if building["upstairs"] else ["partition"]):
            specs[identifier+"-wall-"+side]=lambda b=building,s=side:collision_room_wall(b,s)
    specs.update(RELIEF_COLLISIONS)
    return specs


def supported_exterior_lamp(x,y,fire=False):
    """Place the support before its light; avoid plants as well as circulation."""
    foliage_ids={"ard-hedge","ard-cypress","ard-garden-bed"}
    meshes={m["id"]:m for m in g.PIECES}
    for dx,dy in [(0,0),(0,-3),(0,3),(-3,0),(3,0),(0,-6),(0,6),(-6,0),(6,0)]:
        px,py=x+dx,y+dy
        obstructed=False
        for item in OBJECTS:
            if item.get("meshId") not in foliage_ids:
                continue
            bounds=meshes[item["meshId"]]["boundsBlender"]
            rx=max(abs(bounds[0][0]),abs(bounds[1][0]))
            ry=max(abs(bounds[0][1]),abs(bounds[1][1]))
            c,s=abs(math.cos(math.radians(item["yaw"]))),abs(math.sin(math.radians(item["yaw"])))
            rx,ry=c*rx+s*ry,s*rx+c*ry
            ox,oy=item["position"][:2]
            if abs(px-ox)<rx+.8 and abs(py-oy)<ry+.8:
                obstructed=True
                break
        if obstructed:
            continue
        support=place("ard-lamp",px,py,role="furniture",occluder=False)
        if support is None:
            continue
        light={"position":[px,py,1.7 if fire else 2.0],"candelas":90 if fire else 62,
               "radius":6 if fire else 8,"color":"#ffb872" if fire else "#ffd19b","supportId":support["id"]}
        if fire:
            light.update(fire=True,flameScale=.20)
        LIGHTS.append(light)
        return support
    return None


def garden_terrace_geometry(collision=False):
    """Two actual elevated gardens, dressed retaining faces and twelve-step links."""
    for terrace in layout.GARDEN_TERRACES:
        x0,y0,x1,y1=terrace["bounds"]
        z=terrace["z"]
        if collision:
            collision_box((x0+x1)/2,(y0+y1)/2,z-.55,x1-x0,y1-y0,.55)
        else:
            w.paving(x0,x1,y0,y1,z,variant=0)
        for y in [y0,y1]:
            # Open five-metre gateways at both stair mouths.
            for a,b in [(x0,-55.5),(-50.5,x1)]:
                bottom=min(layout._base_ground_height(a,y),layout._base_ground_height(b,y),z)-1.2
                if collision:
                    collision_box((a+b)/2,y,bottom,b-a,.62,z-bottom+1.1)
                else:
                    g.masonry(a,b,y,bottom,z,.55,course=.45,brick=1.1)
                    g.rail((a+b)/2,y,z+.03,b-a)
                    g.block((a+b)/2,y,z-.15,b-a,.78,.16,"marble_white")
        for x in [x0,x1]:
            bottom=min(layout._base_ground_height(x,y0),layout._base_ground_height(x,y1),z)-1.0
            if collision:
                collision_box(x,(y0+y1)/2,bottom,.55,y1-y0,z-bottom+1.1)
            else:
                g.block(x,(y0+y1)/2,bottom,.55,y1-y0,z-bottom,"stone_cream")
                rotate_geometry(lambda xx=x:g.rail((y0+y1)/2,-xx,z+.03,y1-y0),90)  # noqa: B023
    for stair in layout.GARDEN_STAIRS:
        run=(stair["y1"]-stair["y0"])/stair["steps"]
        rise=(stair["z1"]-stair["z0"])/stair["steps"]
        for j in range(stair["steps"]):
            top=stair["z0"]+(j+1)*rise
            y=stair["y0"]+(j+.5)*run
            if collision:
                collision_box(stair["x"],y,stair["z0"]-.5,stair["width"],run,top-stair["z0"]+.5)
            else:
                g.block(stair["x"],y,stair["z0"]-.5,stair["width"],run,top-stair["z0"]+.5,"stone_cream")
                g.block(stair["x"],y,top-.035,stair["width"]+.08,run,.035,"marble_white")
        for side in [-1,1]:
            x=stair["x"]+side*(stair["width"]/2+.18)
            if not collision:
                g.rod((x,stair["y0"],stair["z0"]+1.05),
                      (x,stair["y1"],stair["z1"]+1.05),.055,"bronze",12)
                for j in range(0,stair["steps"]+1,3):
                    y=stair["y0"]+j*run;z=stair["z0"]+j*rise
                    g.block(x,y,z,.11,.11,1.05,"bronze")


def paving_on_oldtown_bank(item):
    """Background shore is the existing horizontal bank at absolute zero."""
    return (item["meshId"] in {"ard-road","ard-quay"}
            and item.get("collision") is False and 322<=item["position"][0]<=397)


def paving_needs_bank_alignment(item):
    if not paving_on_oldtown_bank(item):
        return False
    x,y,_=item["position"]
    return any(abs(layout.ground_height(x+dx,y+dy))>1e-6
               for dx in [-6,0,6] for dy in [-6,0,6])


def paving_has_curved_support(item):
    """Detect curved terrain-backed support; retain affine/context underlays."""
    if item["meshId"] not in {"ard-road","ard-quay"}:
        return False
    c,s=math.cos(math.radians(item.get("yaw",0))),math.sin(math.radians(item.get("yaw",0)))
    x,y,_=item["position"]
    for dx in [-6,0,6]:
        for dy in [-6,0,6]:
            px,py=x+dx*c+dy*s,y-dx*s+dy*c
            # The actual closed terrain domain excludes the pool. Far-bank
            # context is a separate flat bank: retain its structural underlay.
            if not (-212-1e-6<=px<=240+1e-6 and -148-1e-6<=py<=360+1e-6):
                return False
            if -145<px<-109 and 61<py<85:
                return False
    def height(dx,dy):
        return layout.ground_height(x+dx*c+dy*s,y-dx*s+dy*c)
    a,b,d,e=height(-6,-6),height(6,-6),height(-6,6),height(6,6)
    # Compare against both corner triangles, not a bilinear saddle. Sampling
    # one-metre intervals catches a blend boundary passing through a module.
    for dx in range(-6,7):
        for dy in range(-6,7):
            u,v=(dx+6)/12,(dy+6)/12
            plane=a+(b-a)*u+(e-b)*v if u>=v else a+(e-d)*u+(d-a)*v
            if abs(height(dx,dy)-plane)>.025:
                return True
    return False


def quay_paving_rects(item):
    """Keep quay slabs outside the existing complete bridge walking deck."""
    if item["meshId"]!="ard-quay":
        return None
    x,y,_=item["position"];angle=math.radians(item.get("yaw",0));c,s=math.cos(angle),math.sin(angle)
    corners=[((px-x)*c-(py-y)*s,(px-x)*s+(py-y)*c)
             for px in [234.,342.] for py in [-92.5,-77.5]]
    a,b=max(-6.,min(p[0] for p in corners)),min(6.,max(p[0] for p in corners))
    d,e=max(-6.,min(p[1] for p in corners)),min(6.,max(p[1] for p in corners))
    if b-a<1e-6 or e-d<1e-6:
        return None
    rectangles=[(-6,a,-6,6),(b,6,-6,6),(a,b,-6,d),(a,b,e,6)]
    return [tuple(round(v,8) for v in r) for r in rectangles if r[1]-r[0]>.025 and r[3]-r[2]>.025]


def refine_closed_paving(first_face):
    """Subdivide whole closed slabs before warping; shared edges stay coincident.

    Two midpoint passes give at most 0.29 m edges on 1.15 m stones. This keeps
    the top's interior diagonals from cutting narrow changes of ground slope.
    Stone colours, seed, perimeter and thickness are preserved.
    """
    attributes=[g.FACE_MATERIALS,g.FACE_SMOOTH,g.FACE_COLORS,g.FACE_SEEDS,g.FACE_BEVELS]
    faces=[];data=[];refined_flags=[]
    for i in range(first_face,len(g.FACES)):
        face=g.FACES[i];values=[a[i] for a in attributes]
        if g.NAMES[values[0]]!="marble_white":
            faces.append(face);data.append(values);refined_flags.append(False);continue
        center=len(g.VERTS)
        g.VERTS.append(tuple(sum(g.VERTS[k][axis] for k in face)/len(face) for axis in range(3)))
        triangles=[(face[j],face[(j+1)%len(face)],center) for j in range(len(face))]
        faces.extend(triangles);data.extend([values]*len(triangles));refined_flags.extend([True]*len(triangles))
    for _ in range(2):
        # One cache for the complete closed volume, including top, sides and
        # underside. Coincident but disconnected edge vertices would let the
        # exporter's normal recalculation flip each face independently.
        edges={};new_faces=[];new_data=[];new_flags=[]
        def midpoint(a,b):
            key=tuple(sorted((a,b)))
            if key not in edges:  # noqa: B023
                edges[key]=len(g.VERTS)  # noqa: B023
                g.VERTS.append(tuple((g.VERTS[a][axis]+g.VERTS[b][axis])/2 for axis in range(3)))
            return edges[key]  # noqa: B023
        for face,values,refined in zip(faces,data,refined_flags):
            if not refined:
                new_faces.append(face);new_data.append(values);new_flags.append(False);continue
            a,b,c=face
            ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
            triangles=[(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)]
            new_faces.extend(triangles);new_data.extend([values]*4);new_flags.extend([True]*4)
        faces,data,refined_flags=new_faces,new_data,new_flags
    g.FACES[first_face:]=faces
    for j,attribute in enumerate(attributes):
        attribute[first_face:]=[row[j] for row in data]


def relief_batch_geometry(items,collision=False,refine=False):
    def road_collision():
        # Subdivide ramps before deformation: a twelve-metre box would bridge
        # across concave approaches and leave an invisible floating floor.
        spacing=.5 if refine else 2
        for ix in range(round(12/spacing)):
            for iy in range(round(12/spacing)):
                collision_box(-6+(ix+.5)*spacing,-6+(iy+.5)*spacing,-.205,spacing,spacing,.24)
    builders={"ard-road":(road_piece,road_collision),
              "ard-quay":(quay_piece,lambda:collision_quay(.5 if refine else 2)),
              "ard-river-parapet":(river_parapet,lambda:collision_box(0,0,-1.5,12,.76,2.75))}
    for item in items:
        start=len(g.VERTS)
        start_face=len(g.FACES)
        if not collision and item["meshId"]=="ard-quay":
            quay_piece(backing=not paving_has_curved_support(item),paving_rects=quay_paving_rects(item))
        elif not collision and paving_has_curved_support(item):
            # Only the buried underlay is removed: every closed dressed slab
            # is retained. Terrain already fills its joints. Even a 2 m grid
            # bridges the sharp quay datum transition and emerges by 0.86 m.
            builders[item["meshId"]][0](backing=False)
        else:
            builders[item["meshId"]][1 if collision else 0]()
        if refine and not collision:
            refine_closed_paving(start_face)
        if not collision and item["meshId"] in {"ard-road","ard-quay"}:
            # Paving already has eight authored cut corners and full slab
            # thickness. Keep these constructed edges instead of adding a
            # second tiny bevel to every internal joint in a city-wide batch.
            g.FACE_BEVELS[start_face:]=[0.]*(len(g.FACES)-start_face)
        old_z=[point[2] for point in g.VERTS[start:]]
        relief.transform_new(g,start,item,layout.ground_height,not paving_on_oldtown_bank(item))
        if item["meshId"]=="ard-quay":
            # The masonry retaining face reaches below the fixed water datum,
            # even beside the twelve-metre upper promenade.
            for index,z in enumerate(old_z,start):
                if z<-1:
                    px,py,_=g.VERTS[index]
                    g.VERTS[index]=(px,py,-3.25)


def apply_relief(emit):
    """Rigid buildings + conforming paving, without tilted rooms or hidden steps."""
    grouped={}
    lawns=[]
    pieces={piece["id"]:piece for piece in g.PIECES}
    for item in list(OBJECTS):
        mesh=item.get("meshId","")
        if mesh=="ard-courtyard-lawn":
            lawns.append(dict(item))
            OBJECTS.remove(item)
            continue
        if mesh in {"ard-road","ard-quay","ard-river-parapet"}:
            x,y,_=item["position"]
            key=(mesh,math.floor(x/72),math.floor(y/72),item.get("collision",True))
            grouped.setdefault(key,[]).append(dict(item))
            OBJECTS.remove(item)
            continue
        if item.get("role")=="monument" or mesh in {"ard-ground","ard-coastal-boat"}:
            item["groundZ"]=0.
            continue
        x,y,_=item["position"]
        # Broad context slabs use authored absolute vertices. Only the southern
        # apron needs the high district datum; the far river shore stays low.
        if mesh in {"ard-oldtown-bank","ard-docks-bank","ard-southern-context-bank"}:
            if mesh=="ard-southern-context-bank" or x<-4000 and y>2000:
                item["position"][2]+=12.
            item["groundZ"]=item["position"][2]
            continue
        ground=layout.ground_height(x,y)
        item["groundZ"]=ground
        item["position"][2]+=ground
        if mesh in pieces:
            bounds=pieces[mesh]["boundsBlender"]
            item["verticalBounds"]=[item["position"][2]+bounds[0][2],item["position"][2]+bounds[1][2]]
    batches=[]
    for index,((kind,_,__,physical),items) in enumerate(sorted(grouped.items())):
        identifier=f"ard-relief-{kind.removeprefix('ard-')}-{index:03d}"
        refine=identifier in REFINED_PAVING_BATCHES
        emit(identifier,lambda objects=items,r=refine:relief_batch_geometry(objects,refine=r),"floor")
        RELIEF_COLLISIONS[identifier]=lambda objects=items,r=refine:relief_batch_geometry(objects,True,r)
        OBJECTS.append({"id":identifier,"meshId":identifier,"position":[0,0,0],"yaw":0,
                        "role":"floor" if kind!="ard-river-parapet" else "wall",
                        "occluder":False,"groundZ":0,"collision":physical,
                        "terrainConforming":True})
        batches.append({"meshId":identifier,"sources":items})
    if lawns:
        emit("ard-relief-lawns",lambda:relief.conformed_lawns(g,lawns,layout.foundation_height),"landscape")
        RELIEF_COLLISIONS["ard-relief-lawns"]=lambda:relief.conformed_lawns(g,lawns,layout.foundation_height,True)
        OBJECTS.append({"id":"ard-relief-lawns","meshId":"ard-relief-lawns",
                        "position":[0,0,0],"yaw":0,"role":"landscape","occluder":False,
                        "groundZ":0,"collision":True,"terrainConforming":True})
        batches.append({"meshId":"ard-relief-lawns","sources":lawns})
    emit("ard-garden-terraces",garden_terrace_geometry,"floor")
    RELIEF_COLLISIONS["ard-garden-terraces"]=lambda:garden_terrace_geometry(True)
    OBJECTS.append({"id":"ard-garden-terraces","meshId":"ard-garden-terraces",
                    "position":[0,0,0],"yaw":0,"role":"floor","occluder":False,"groundZ":0})
    for light in LIGHTS:
        light["position"]=layout.ground_position(light["position"])
    for water in WATERS:
        # Oceans/rivers have one physical water level; civic bowls follow their
        # level foundation. A rectangular scale is not an altitude decision.
        if max(water["size"])<60:
            water["position"]=layout.ground_position(water["position"])
    return batches


def interior_dressing():
    """Occupied rooms using untouched, already imported Arena furniture.

    Coordinates are explicit in metres; seat groups leave the public centre
    clear. Feet are on the room datum, including the pub's real upper deck.
    No fixture intersects the inspection walk, with 0.75 m body clearance.
    """
    source=ROOT/"Source/Elements/Assets/Built/arena-fate-props/manifest.json"
    meshes={m["id"]:m for m in json.loads(source.read_text(encoding="utf-8"))["meshes"]}
    items=[]
    def prop(kind,x,y,z=0,yaw=0,zone="pub-upper"):
        identifier={"table":"afp-loge-table-sculpted","chair":"afp-loge-chair-sculpted",
                    "bench":"afp-bench","barrel":"afp-barrel"}[kind]
        piece=meshes[identifier]
        ground=layout.ground_height(x,y)
        bottom=ground+z
        items.append({"id":f"dressing-{zone}-{kind}-{len(items):03d}",
            "mesh":f"Built/arena-fate-props/{identifier}.glb",
            "position":[x,y,bottom],"yaw":yaw,"role":"furniture",
            "occluder":False,"collision":True,"groundZ":ground,
            "verticalBounds":[bottom,bottom+piece["bounds"][1][2]],
            "dressingZone":zone,"storey":1 if zone=="pub-upper" else 0})
    def sitting(x,y,z=0,zone="pub-upper",bench=False):
        prop("table",x,y,z,zone=zone)
        if bench:
            prop("bench",x,y-1.05,z,zone=zone)
            prop("bench",x,y+1.05,z,180,zone)
        else:
            for dx in [-.47,.47]:
                prop("chair",x+dx,y-1.02,z,zone=zone)
                prop("chair",x+dx,y+1.02,z,180,zone)
    # Six tavern booths, plus a snug behind the stair. The landing to the
    # inspected point (194,45) remains clear, as does the central column.
    for x,y in [(190,50),(195,50),(200,50),(200,43),(180,35.5),(184,35.5)]:
        sitting(x,y,4,bench=True)
    for x,y in [(189,54.4),(193,54.4),(198,54.4),(201.3,36)]:
        prop("bench",x,y,4,180)
    for x,y in [(178.5,38.2),(179.5,38.2),(201.5,34),(201.5,35)]:
        prop("barrel",x,y,4)
    # Ground-floor drinking booths use the open eastern and entry-side bays.
    for x,y in [(193,51),(193,44),(199.5,40.5)]:
        sitting(x,y,zone="pub-taproom",bench=True)
    # Casino: gaming room surrounds a 6 m public aisle. Smaller pairs of
    # upholstered seats give the rear reading salons a different use.
    for x in [-59.5,-46.5]:
        for y in [181,187,193]:
            sitting(x,y,zone="casino-gaming")
    for x,y in [(-70,193),(-36,193),(-70,169),(-36,169)]:
        sitting(x,y,zone="casino-salon")
    for x in [-71,-66,-40,-35]:
        prop("bench",x,196.7,0,180,"casino-waiting")
    # Betting hall: paired consultation desks and waiting benches, keeping
    # both the central doorway and the cross aisle to the back office clear.
    for x in [-5.8,5.8]:
        for y in [76.5,82]:
            sitting(x,y,zone="betting-desks")
    for x in [-14,-9,9,14]:
        prop("bench",x,86.7,0,180,"betting-waiting")
    for x in [-4.5,4.5]:
        prop("bench",x,65.2,0,0,"betting-office")
    # Small shared merchant bays add stock and rest seats between the long
    # stall rows, away from the bazaar's central axis and crowd loops.
    for x in [-164,-152]:
        for y in [161.5,187]:
            prop("bench",x,y,zone="bazaar-bays")
            for dx in [-2,2]:
                prop("barrel",x+dx,y,zone="bazaar-bays")
    for item in items:
        piece=meshes[Path(item["mesh"]).stem]
        bounds=piece["bounds"]
        c,s=abs(math.cos(math.radians(item["yaw"]))),abs(math.sin(math.radians(item["yaw"])))
        rx=max(abs(bounds[0][0]),abs(bounds[1][0]))
        ry=max(abs(bounds[0][1]),abs(bounds[1][1]))
        rx,ry=c*rx+s*ry,s*rx+c*ry
        x,y,z=item["position"]
        box=[x-rx-.75,y-ry-.75,x+rx+.75,y+ry+.75]
        for a,b in zip(layout.VISIT_ROUTE,layout.VISIT_ROUTE[1:]):
            if max(a[2],b[2])>=z-.1 and min(a[2],b[2])<=item["verticalBounds"][1]:
                assert not segment_box(a,b,box),("Furniture blocks inspection walk",item["id"],a,b)
        if item["storey"]==0:
            for route in layout.CROWD_ROUTES:
                for a,b in zip(route,route[1:]+route[:1]):
                    assert not segment_box(a,b,box),("Furniture blocks crowd loop",item["id"],a,b)
    return items


def estate_column_supports(objects):
    """Seat existing estate columns on small reused sculpted Arena plinths.

    Building basements cover walls, but a rigid forecourt colonnade also needs
    individual foundations on its downhill side. All dimensions stay explicit
    and reproducible; existing visual masters and physics are unchanged.
    """
    supports=[]
    existing={item["id"] for item in objects}
    for item in objects:
        if not item["id"].startswith("house-") or item.get("meshId") not in {"ard-house-4","ard-house-5"}:
            continue
        x0,y0,z0=item["position"]
        yaw=item.get("yaw",0)
        c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
        for index,x in enumerate([-15,-10,-5,5,10,15]):
            px,py=x0+x*c+16*s,y0-x*s+16*c
            if z0-layout.foundation_height(px,py)<=.08:
                continue
            identifier=f"{item['id']}-column-foundation-{index}"
            if identifier in existing:
                continue
            # Sample the full rotated 1.56 m foot so its downhill edge cannot
            # expose a hole. The first 12 cm are embedded into real ground.
            elevations=[layout.foundation_height(px+dx*c+dy*s,py-dx*s+dy*c)
                        for dx in [-.78,0,.78] for dy in [-.78,0,.78]]
            bottom=min(elevations)-.12
            top=z0+.02
            supports.append({"id":identifier,
                "mesh":"Built/arena-fate-modern/afm-statue-plinth.glb",
                "position":[px,py,bottom],"yaw":yaw,
                "scale":[.65,.65,(top-bottom)/1.7],
                "role":"architecture","occluder":False,"collision":True,
                "groundZ":layout.ground_height(px,py),
                "verticalBounds":[bottom,top],"supportsObject":item["id"]})
    return supports


def stand_column_supports(objects):
    """Seat the complete 1.20 m stand-column feet on sloping promenade edges.

    Reuse the existing sculpted 1.70 m plinth within the column's unchanged
    1.20 m footprint; 12 cm of burial accommodates the
    terrain interpolation, while 2 cm of overlap closes the column junction.
    A 5 mm numerical contact tolerance selects exposed feet without changing
    any authored stand, route, or terrain altitude.
    """
    result=[]
    existing={item["id"] for item in objects}
    for item in objects:
        if item.get("meshId")!="ard-stand":
            continue
        x0,y0,z0=item["position"]
        yaw=item.get("yaw",0);c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
        for index,x in enumerate([-3.7,3.7]):
            px,py=x0+x*c-5*s,y0-x*s-5*c
            def heights(radius):
                return [layout.foundation_height(px+dx*c+dy*s,py-dx*s+dy*c)  # noqa: B023
                        for dx in [-radius,0,radius] for dy in [-radius,0,radius]]
            if z0-min(heights(.6))<=.005:
                continue
            identifier=f"{item['id']}-column-foundation-{index}"
            if identifier in existing:
                continue
            bottom=min(heights(.6))-.12;top=z0+.02
            result.append({"id":identifier,"mesh":"Built/arena-fate-modern/afm-statue-plinth.glb",
                           "position":[px,py,bottom],"yaw":yaw,
                           "scale":[.5,.5,(top-bottom)/1.7],
                           "role":"architecture","occluder":False,"collision":True,
                           "groundZ":layout.ground_height(px,py),"verticalBounds":[bottom,top],
                           "supportsObject":item["id"]})
    return result


def background_silhouettes():
    """Existing closed masters on the two real banks, beyond sealed exits."""
    pieces={m["id"]:m for m in g.PIECES}
    items=[]
    plots=[]
    for row,y in enumerate([380,413,454]):
        for column,x in enumerate(range(-206,232,32)):
            plots.append((x+(row%2)*9,y+(column%3)*3,11.97,180,(row+column)%4))
    for row,x in enumerate([422,451,484]):
        for column,y in enumerate(range(-158,177,37)):
            plots.append((x+(column%2)*4,y+(row%2)*8,-.03,-90,(row*3+column)%4))
    for j,(x,y,z,yaw,kind) in enumerate(plots):
        body=f"context-silhouette-{j:03d}"
        for roof in [False,True]:
            mesh=f"ard-house-{'roof-' if roof else ''}{kind}"
            bounds=pieces[mesh]["boundsBlender"]
            item={"id":body+('-roof' if roof else ''),"meshId":mesh,"position":[x,y,z],
                  "yaw":yaw,"role":"background","collision":False,"occluder":False,
                  "groundZ":z,"verticalBounds":[z+bounds[0][2],z+bounds[1][2]]}
            if roof:
                item["supportsObject"]=body
            items.append(item)
        if j%2==0:
            mesh="ard-cypress" if j%4==0 else "ard-noble-tree"
            bounds=pieces[mesh]["boundsBlender"]
            items.append({"id":body+"-tree","meshId":mesh,"position":[x+12,y+7,z],"yaw":0,
                          "role":"vegetation","collision":False,"occluder":False,"motion":"foliage",
                          "groundZ":z,"verticalBounds":[z+bounds[0][2],z+bounds[1][2]]})
    return items


def append_collision_proxies(manifest,out,materials,reuse=False,rebuild=()):
    specs=collision_specs()
    for batch in manifest["metadata"].get("reliefBatches",[]):
        if batch["meshId"]=="ard-relief-lawns":
            specs[batch["meshId"]]=lambda objects=batch["sources"]:relief.conformed_lawns(g,objects,layout.foundation_height,True)
        else:
            specs[batch["meshId"]]=lambda objects=batch["sources"],r=batch["meshId"] in REFINED_PAVING_BATCHES:relief_batch_geometry(objects,True,r)
    if manifest["metadata"].get("reliefBatches"):
        specs["ard-garden-terraces"]=lambda:garden_terrace_geometry(True)
    active={o["meshId"] for o in manifest["objects"] if "meshId" in o and o.get("collision",True)}
    visual=[m for m in manifest["meshes"] if m.get("role")!="collision-proxy"]
    previous={m["id"]:m for m in manifest["meshes"] if m.get("role")=="collision-proxy"}
    assert not active-specs.keys(),f"Missing physical definition: {active-specs.keys()}"
    proxies=[]
    g.PIECES.clear()
    for piece in visual:
        if piece["id"] not in active:
            piece.pop("collisionMesh",None)
            continue
        identifier=piece["id"]+"-collision"
        if reuse and identifier not in rebuild:
            proxy=previous[identifier]
        else:
            g.export_piece(identifier,specs[piece["id"]],out,materials,role="collision-proxy",clean_degenerate=True)
            proxy=g.PIECES[-1]
            proxy["role"]="collision-proxy"
            proxy["sha256"]=hashlib.sha256((out/proxy["file"]).read_bytes()).hexdigest()
        piece["collisionMesh"]=identifier
        proxies.append(proxy)
    manifest["meshes"]=visual+proxies
    counts={m["id"]:m["triangles"] for m in manifest["meshes"]}
    mapping={m["id"]:m.get("collisionMesh") for m in visual}
    instance_triangles=sum(counts[mapping[o["meshId"]]] for o in manifest["objects"]
                           if "meshId" in o and o.get("collision",True))
    manifest["metadata"]["collision"]={"policy":"authored architectural volumes; visual masters untouched",
        "proxies":len(proxies),"distinctTriangles":sum(p["triangles"] for p in proxies),
        "instanceTriangles":instance_triangles,"foliage":"trunk and planter collision; cypress leaves nonblocking",
        "sharedArena":"existing authored ring proxies remain managed by Arena importer"}


def seam_targets(manifest):
    targets={"ard-ground","ard-ground-collision",*REFINED_PAVING_BATCHES}
    targets.update(m+"-collision" for m in REFINED_PAVING_BATCHES)
    targets.update(b["meshId"] for b in manifest["metadata"]["reliefBatches"]
                   if any(quay_paving_rects(o) is not None for o in b["sources"]))
    return targets


def seams_only(out):
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    targets=seam_targets(manifest)
    before={m["id"]:m["sha256"] for m in manifest["meshes"]}
    digest=hashlib.sha256((out/"manifest.json").read_bytes()).hexdigest()
    backup=ROOT/"Saved/Jadg/districts/relief-20261011"/("seams-before-"+digest[:12])
    backup.mkdir(parents=True,exist_ok=True)
    for name in ["manifest.json"]+[m["file"] for m in manifest["meshes"] if m["id"] in targets]:
        if not (backup/name).exists():shutil.copy2(out/name,backup/name)
        assert hashlib.sha256((backup/name).read_bytes()).digest()==hashlib.sha256((out/name).read_bytes()).digest()
    for source in [Path(__file__),Path(relief.__file__)]:shutil.copy2(source,backup/source.name)
    build(out,True,targets)
    result=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    assert all(m["sha256"]==before[m["id"]] for m in result["meshes"] if m["id"] not in targets)
    print("ARENAREA_SEAMS_COMPLETE "+json.dumps(sorted(targets)),flush=True)


def finishing_targets(manifest,baseline):
    """Only changed facades, raised quays and road batches whose yaw changed."""
    targets={f"ard-house-{j}" for j in range(6)}
    targets.update({"ard-quay","ard-context-downtown","ard-context-palacedomain"})
    targets.update("ard-"+b["id"]+"-wall-"+s for b in layout.BUILDINGS
                   for s in ["front","rear","west","east"])
    previous={b["meshId"]:b["sources"] for b in baseline["metadata"]["reliefBatches"]}
    pieces={m["id"]:m for m in manifest["meshes"]}
    for batch in manifest["metadata"]["reliefBatches"]:
        identifier=batch["meshId"]
        if (any(o["meshId"]=="ard-quay" for o in batch["sources"])
                or batch["sources"]!=previous.get(identifier)):
            targets.add(identifier)
            if pieces[identifier].get("collisionMesh"):
                targets.add(pieces[identifier]["collisionMesh"])
    return targets


def finishing_only(out):
    baseline_path=ROOT/"Saved/Jadg/districts/relief-20261011/avant-polishfinal/manifest.json"
    baseline=json.loads(baseline_path.read_text(encoding="utf-8"))
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    targets=finishing_targets(manifest,baseline)
    before={m["id"]:hashlib.sha256((out/m["file"]).read_bytes()).hexdigest() for m in manifest["meshes"]}
    backup=baseline_path.parent/"glb-before"
    backup.mkdir(parents=True,exist_ok=True)
    for m in manifest["meshes"]:
        if m["id"] in targets:
            destination=backup/m["file"]
            if not destination.exists():
                shutil.copy2(out/m["file"],destination)
            assert hashlib.sha256(destination.read_bytes()).hexdigest()==before[m["id"]]
    shutil.copy2(out/"manifest.json",backup/"placement-manifest-before-export.json")
    shutil.copy2(Path(__file__),backup/Path(__file__).name)
    build(out,True,targets)
    result=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    assert all(m["sha256"]==before[m["id"]] for m in result["meshes"] if m["id"] not in targets)
    print("ARENAREA_FINISHING_COMPLETE "+json.dumps(sorted(targets)),flush=True)


def paving_only(out):
    """Re-export only curved paving batches; preserve every physical GLB."""
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    batches=[b for b in manifest["metadata"]["reliefBatches"]
             if any(paving_has_curved_support(o) or paving_needs_bank_alignment(o)
                    for o in b["sources"])]
    expected={b["meshId"] for b in batches}
    before={m["id"]:m["sha256"] for m in manifest["meshes"]}
    manifest_hash=hashlib.sha256((out/"manifest.json").read_bytes()).hexdigest()
    backup=ROOT/"Saved/Jadg/districts/relief-20261011"/f"paving-before-{manifest_hash[:12]}"
    backup.mkdir(parents=True,exist_ok=True)
    for name in ["manifest.json"]+[m["file"] for m in manifest["meshes"] if m["id"] in expected]:
        saved=backup/name
        if not saved.exists():
            shutil.copy2(out/name,saved)
        assert hashlib.sha256(saved.read_bytes()).digest()==hashlib.sha256((out/name).read_bytes()).digest()
    for source in [Path(__file__),Path(w.__file__)]:
        shutil.copy2(source,backup/source.name)
    g.bpy.ops.object.select_all(action="SELECT")
    g.bpy.ops.object.delete(use_global=False)
    materials=g.build_materials()
    for batch in batches:
        identifier=batch["meshId"]
        previous=next(m for m in manifest["meshes"] if m["id"]==identifier)
        g.export_piece(identifier,lambda items=batch["sources"],r=identifier in REFINED_PAVING_BATCHES:relief_batch_geometry(items,refine=r),
                       out,materials,role="floor",clean_degenerate=True)
        replacement=dict(g.PIECES[-1])
        replacement["sha256"]=hashlib.sha256((out/replacement["file"]).read_bytes()).hexdigest()
        if "collisionMesh" in previous:
            replacement["collisionMesh"]=previous["collisionMesh"]
        manifest["meshes"][manifest["meshes"].index(previous)]=replacement
    assert all(hashlib.sha256((out/m["file"]).read_bytes()).hexdigest()==before[m["id"]]
               for m in manifest["meshes"] if m["id"] not in expected),"Unrelated master changed"
    validate(manifest,out)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ARENAREA_PAVING_COMPLETE "+json.dumps(sorted(expected)),flush=True)


def collision_only(out):
    manifest=json.loads((out/"manifest.json").read_text(encoding="utf-8"))
    visual={m["file"]:hashlib.sha256((out/m["file"]).read_bytes()).hexdigest()
            for m in manifest["meshes"] if m.get("role")!="collision-proxy"}
    g.bpy.ops.object.select_all(action="SELECT")
    g.bpy.ops.object.delete(use_global=False)
    append_collision_proxies(manifest,out,g.build_materials())
    assert all(hashlib.sha256((out/f).read_bytes()).hexdigest()==sha for f,sha in visual.items()),"Visual master changed"
    validate(manifest,out)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("ARENAREA_COLLISION_COMPLETE "+json.dumps(manifest["metadata"]["collision"]),flush=True)


def validate_proxy_geometry(piece,path):
    """Check the actual exported physical triangles, including future --verify."""
    raw=path.read_bytes()
    json_size=struct.unpack_from("<I",raw,12)[0]
    doc=json.loads(raw[20:20+json_size])
    blob=raw[28+json_size:]
    def values(identifier):
        accessor=doc["accessors"][identifier]
        view=doc["bufferViews"][accessor["bufferView"]]
        count={"SCALAR":1,"VEC2":2,"VEC3":3,"VEC4":4}[accessor["type"]]
        fmt={5126:"f",5125:"I",5123:"H",5121:"B"}[accessor["componentType"]]
        stride=view.get("byteStride",struct.calcsize(fmt)*count)
        offset=view.get("byteOffset",0)+accessor.get("byteOffset",0)
        return [struct.unpack_from("<"+fmt*count,blob,offset+j*stride) for j in range(accessor["count"])]
    triangles=0
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            points=values(primitive["attributes"]["POSITION"])
            assert all(all(math.isfinite(x) for x in p) for p in points),piece["id"]
            indices=[p[0] for p in values(primitive["indices"])]
            assert len(indices)%3==0 and min(indices)>=0 and max(indices)<len(points),piece["id"]
            for j in range(0,len(indices),3):
                a,b,c=(points[indices[j+k]] for k in range(3))
                u,v=[b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)]
                cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                assert sum(x*x for x in cross)>1e-20,(piece["id"],"degenerate",j)
            triangles+=len(indices)//3
    assert triangles==piece["triangles"],(piece["id"],triangles,piece["triangles"])


def validate(manifest,out):
    mesh_ids={m["id"] for m in manifest["meshes"]}
    object_ids=[o["id"] for o in manifest["objects"]]
    assert len(object_ids)==len(set(object_ids)), "Duplicate objects"
    for mi in manifest["meshes"]:
        path=out/mi["file"]
        assert path.is_file() and path.read_bytes()[:4]==b"glTF",str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==mi["sha256"]
        if mi.get("role")=="collision-proxy":
            validate_proxy_geometry(mi,path)
    for item in manifest["objects"]:
        assert item.get("meshId") in mesh_ids or (ROOT/"Source/Elements/Assets"/item.get("mesh", "missing")).is_file(),item
        assert all(math.isfinite(x) for x in item["position"])
    assert set(manifest["metadata"]["entityPositions"])=={f"e{i}" for i in range(1,12)}
    assert all(r in object_ids for r in manifest["metadata"]["roofsIds"])
    assert len(manifest["metadata"]["landmarks"])>=9
    for piece in manifest["meshes"]:
        if "collisionMesh" in piece:
            proxy=next(p for p in manifest["meshes"] if p["id"]==piece["collisionMesh"])
            assert proxy["role"]=="collision-proxy"
            assert not any(o.get("meshId")==proxy["id"] for o in manifest["objects"])


def build(out,reuse_meshes=False,rebuild_meshes=()):
    out.mkdir(parents=True,exist_ok=True)
    previous={m["id"]:m for m in json.loads((out/"manifest.json").read_text(encoding="utf-8"))["meshes"]} if reuse_meshes else {}
    if not reuse_meshes or rebuild_meshes:
        g.bpy.ops.object.select_all(action="SELECT")
        g.bpy.ops.object.delete(use_global=False)
    g.PIECES.clear()
    g.OBJECTS.clear()
    g.ROOFS.clear()
    materials=g.build_materials() if not reuse_meshes or rebuild_meshes else []
    facade_lamps=[]
    def emit(identifier,fn,role="architecture"):
        if reuse_meshes and identifier not in rebuild_meshes and identifier in previous:
            g.PIECES.append(previous[identifier])
            return
        g.export_piece(identifier,fn,out,materials,role=role,clean_degenerate=True)
    emit("ard-ground",ground,"floor")
    emit("ard-road",road_piece,"floor")
    emit("ard-quay",quay_piece,"floor")
    emit("ard-boundary",boundary_segment)
    emit("ard-river-parapet",river_parapet)
    emit("ard-gate",gate_frame)
    emit("ard-fountain",fountain,"furniture")
    emit("ard-garden-bed",garden_bed,"landscape")
    emit("ard-cypress",cypress,"vegetation")
    emit("ard-noble-tree",lambda:foliage.noble_tree(g,height=7.4,crown_radius=3.1,seed=92),"vegetation")
    emit("ard-hedge",hedge,"landscape")
    emit("ard-bench",lambda:w.bench(0,0,2.9),"furniture")
    emit("ard-amphora",lambda:w.amphora(0,0,0,1.25),"furniture")
    emit("ard-stall",stall,"furniture")
    emit("ard-market-stock",market_stock,"furniture")
    emit("ard-merchant-cart",merchant_cart,"furniture")
    emit("ard-bridge-bay",bridge_bay,"bridge")
    emit("ard-bridge-end-pier",bridge_end_pier,"bridge")
    emit("ard-neighbour-gate",neighbour_gate)
    emit("ard-dock-pier",dock_pier)
    emit("ard-coastal-boat",coastal_boat)
    emit("ard-oldtown-bank",oldtown_bank)
    emit("ard-docks-bank",docks_warehouse_bank)
    emit("ard-southern-context-bank",southern_context_bank)
    emit("ard-context-downtown",lambda:neighbour_landmark("downtown"))
    emit("ard-context-palacedomain",lambda:neighbour_landmark("palacedomain"))
    emit("ard-chandelier",chandelier,"furniture")
    emit("ard-lamp",lambda:w.lamp(0,0,0,True),"furniture")
    emit("ard-arena-backing",lambda:g.block(0,0,0,6.8,.48,45,"mortar"))
    emit("ard-track",hippodrome_track,"floor")
    emit("ard-stand",stand)
    emit("ard-stand-roof",lambda:tiled_roof(8.6,6.1,5.8))
    if DENSE:
        emit("ard-courtyard-lawn",courtyard_lawn,"landscape")
    for j in range(6):
        ww,dd,hh=11+j%3*.9,12+(j%2)*2.1,(7.2,10.8,10.8,7.2,10.8,14.4)[j]
        if j>=4:
            emit(f"ard-house-{j}",lambda jj=j:estate(jj))
            emit(f"ard-house-roof-{j}",lambda jj=j:estate(jj,roof=True))
        else:
            emit(f"ard-house-{j}",lambda ww=ww,dd=dd,hh=hh:shell(ww,dd,hh,True))
            emit(f"ard-house-roof-{j}",lambda ww=ww,dd=dd,hh=hh,j=j:tiled_roof(ww,dd,hh+.7,j))
    for building in layout.BUILDINGS:
        identifier="ard-"+building["id"]
        emit(identifier,lambda b=building:important_room(b))
        for side in ["front","rear","west","east"]:
            emit(identifier+"-wall-"+side,lambda b=building,s=side:important_wall(b,s))
        if not building["upstairs"]:
            emit(identifier+"-wall-partition",lambda b=building:important_wall(b,"partition"))
        else:
            emit(identifier+"-upper-deck",pub_upper_deck,"floor")
        emit(identifier+"-furniture",lambda b=building:furniture(b),"furniture")
        emit(identifier+"-roof",lambda b=building:tiled_roof(b["width"],b["depth"],b["height"]+.7))
        x,y,z=building["position"]
        place(identifier,x,y,role="floor",occluder=False)
        for side in ["front","rear","west","east"]:
            place(identifier+"-wall-"+side,x,y,role="wall")
        if not building["upstairs"]:
            place(identifier+"-wall-partition",x,y,role="wall")
        else:
            place(identifier+"-upper-deck",x,y,role="floor",occluder=True)
        place(identifier+"-furniture",x,y,role="furniture",occluder=False)
        place(identifier+"-roof",x,y,role="roof")
        for dx in [-building["width"]*.34,building["width"]*.34]:
            facade_lamps.append((x+dx,y+building["depth"]/2+3))
        if building["upstairs"]:
            sources=[(3,-5,2.7),(3,5,2.7),(-6,-7,2.7),(0,-4,6.6),(9,1,6.6)]
        else:
            sources=[(dx,dy,building["height"]*.65) for dx in [-building["width"]*.24,building["width"]*.24]
                     for dy in [-building["depth"]*.24,building["depth"]*.24]]
        for dx,dy,zz in sources:
            support=place("ard-chandelier",x+dx,y+dy,zz,role="furniture",occluder=False)
            if building["upstairs"] and zz<4:
                support["scale"]=[1,1,.5]
            LIGHTS.append({"position":[x+dx,y+dy,zz+(.075 if building["upstairs"] and zz<4 else .15)],"candelas":900 if building["use"]=="casino" else 600,
                           "radius":17 if building["use"]=="casino" else 13,"color":"#ffddb0",
                           "always":True,"interior":True,"shadows":True,"supportId":support["id"]})
    place("ard-ground",0,0,role="floor",occluder=False)
    reuse_arena()
    secondary_houses()
    gardens()
    # Main boulevards connect the two open districts, estates and the gateways.
    streets=STREETS
    for a,b in streets:
        add_road(a,b)
    # Gauntlet Street follows the complete ellipse rather than a square block.
    for j in range(108):
        a=j*math.tau/108
        x,y=107*math.cos(a),-65+89*math.sin(a)
        tangent_yaw=math.degrees(math.atan2(-107*math.sin(a),89*math.cos(a)))
        place("ard-road",x,y,yaw=tangent_yaw,role="floor",occluder=False)
    # Dressed coastal retaining wall and river promenade, no island water ring.
    for y in range(-136,299,12):
        place("ard-quay",-204,y,role="floor",occluder=False)
        if abs(y-112)>15:
            place("ard-river-parapet",-210,y,yaw=90)
    for x in range(-198,235,12):
        place("ard-quay",x,-142,yaw=90,role="floor",occluder=False)
        place("ard-river-parapet",x,-148)
    for y in range(-138,290,12):
        if abs(y+85)>18 and y<250:
            place("ard-boundary",238,y,yaw=90)
    place("ard-gate",216,-85,yaw=90)
    place("ard-gate",-203,112,yaw=90)
    # A continuous crossing and closed neighbouring context, without new quests.
    add_road([224,-85],[234,-85])
    contextual_edges()
    # Hippodrome: six-stepped stands, covered noble benches, stable doors.
    place("ard-track",148,185,z=layout.TRACK_SURFACE_OFFSET,role="floor",occluder=False)
    for y in range(133,238,9):
        for x,yaw in [(107,90),(189,-90)]:
            place("ard-stand",x,y,yaw=yaw,role="seating",occluder=False)
            place("ard-stand-roof",x,y,yaw=yaw,role="roof")
    for centre,sign in [(133,-1),(237,1)]:
        for j in range(16):
            angle=sign*(j+.5)*math.pi/16
            x,y=148+43*math.cos(angle),centre+43*math.sin(angle)
            yaw=-90-math.degrees(angle)
            place("ard-stand",x,y,yaw=yaw,role="seating",occluder=False)
            place("ard-stand-roof",x,y,yaw=yaw,role="roof")
    for x in [125,141,157,173]:
        place("ard-stall",x,112,yaw=180,role="furniture",occluder=False)
    # Luxury bazaar rows shelter merchandise; ample continuous central aisle.
    for y in [151,171,179,199]:
        for x in [-178,-138]:
            yaw=90 if x==-178 else -90
            if place("ard-stall",x,y,yaw=yaw,role="market",occluder=False):
                place("ard-market-stock",x,y,yaw=yaw,role="furniture",occluder=False)
    for x in range(-178,-130,8):
        if place("ard-stall",x,145,role="market",occluder=False):
            place("ard-market-stock",x,145,role="furniture",occluder=False)
    for y in [151,170,178,196]:
        for x,yaw in [(-164,90),(-152,-90)]:
            if place("ard-stall",x,y,yaw=yaw,role="market",occluder=False):
                place("ard-market-stock",x,y,yaw=yaw,role="furniture",occluder=False)
    for x,y,yaw in [(-179,220,90),(-139,227,180),(-169,132,90)]:
        place("ard-merchant-cart",x,y,yaw=yaw,role="furniture",occluder=False)
    # Layered estate gardens: distinct planted rooms replace the empty apron.
    for terrace in layout.GARDEN_TERRACES:
        x0,y0,x1,y1=terrace["bounds"]
        for x in [-77,-64,-41,-28]:
            place("ard-garden-bed",x,(y0+y1)/2,role="landscape",occluder=False)
        for x in [-82,-24]:
            place("ard-noble-tree",x,(y0+y1)/2,role="vegetation",occluder=False)
    for x,y in [(-159,42),(-98,46),(-93,125),(30,126),(29,199),(54,248),(-130,252),(-179,274)]:
        if not any(segment_box(a,b,[x-3,y-3,x+3,y+3]) for a,b in zip(layout.VISIT_ROUTE,layout.VISIT_ROUTE[1:])):
            place("ard-noble-tree",x,y,role="vegetation",occluder=False)
    for x,y in facade_lamps:
        supported_exterior_lamp(x,y)
    for x,y in [(-12,22),(12,22),(-22,49),(22,49),(-82,217),(-24,217)]:
        supported_exterior_lamp(x,y,True)
    # Lighting and planting carry the night silhouette across actual streets.
    for j,(a,b) in enumerate(streets):
        length=math.dist(a,b)
        count=max(1,int(length/24))
        for k in range(count):
            u=(k+.4)/count
            x,y=a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u
            dx,dy=b[0]-a[0],b[1]-a[1]
            side=1 if j%2 else -1
            px,py=x-side*dy/length*7.5,y+side*dx/length*7.5
            supported_exterior_lamp(px,py)
    WATERS.extend([{"position":[-780,-825,-3],"size":[2040,1350]},
                   {"position":[-1006,675,-3],"size":[1588,1650]},
                   {"position":[281,0,-3],"size":[82,3000]}])
    relief_batches=apply_relief(emit)
    OBJECTS.extend(estate_column_supports(OBJECTS))
    OBJECTS.extend(stand_column_supports(OBJECTS))
    OBJECTS.extend(interior_dressing())
    OBJECTS.extend(background_silhouettes())
    for piece in g.PIECES:
        piece["sha256"]=hashlib.sha256((out/piece["file"]).read_bytes()).hexdigest()
    manifest={"format":"jadg-arenarea-district","version":1,
        "generator":"scripts/assetsGeneration/build_arenarea_district.py",
        "layout":"scripts/maps/arenarea_district_layout.py",
        "coordinates":"metres X east / Y south / Z up; object positions absolute",
        "materials":g.NAMES,"meshes":g.PIECES,"objects":OBJECTS,
        "metadata":{"area":layout.AREA,"levels":[{"name":"street","z":0},{"name":"pub-upper","z":layout.ground_height(190,44)+4}],
            "groundHeightfield":relief.heightfield(layout.ground_height),
            "heightFunction":{"module":"arenarea_district_layout","function":"ground_height"},
            "storeyRegions":layout.storey_regions(),
            "terrain":{"source":"scripts/maps/arenarea_district_layout.py", "rangeMetres":[0,12],
                       "pads":layout.TERRAIN_PADS,"terraces":layout.GARDEN_TERRACES,"stairs":layout.GARDEN_STAIRS,
                       "geometry":"closed triangulated architectural terrain; conforming pavement and light collision shells",
                       "arenaDatum":0,"waterDatum":-3,"meshSamplingMetres":TERRAIN_SPACING,
                       "localRefinements":TERRAIN_REFINEMENTS},
            "reliefBatches":relief_batches,
            "shots":layout.SHOTS,"route":layout.VISIT_ROUTE if DENSE else layout.ROUTE,"navigationTargets":layout.NAVIGATION_TARGETS,
            "landmarks":layout.LANDMARKS,"entityPositions":layout.ENTITY_POSITIONS,"start":layout.START,
            "lights":LIGHTS,"waters":WATERS,"crowdRoutes":layout.CROWD_ROUTES,"roofsIds":ROOFS,
            "materialAliases":{"foliage":{"source":"sand","colour":[.055,.13,.025]}},
            "composition":"twelve-metre rising civic terraces, continuous inclined boulevards, two elevated casino gardens, elongated hippodrome, planted courtyards and layered tiled roofs",
            "neighbourConnections":[
                {"from":"Arena Gate","via":"Arching Bridge","to":"Oldtown","status":"closed at far-bank threshold"},
                {"from":"Water Gate","to":"Docks District","status":"visible working wharf, existing sealed exit"},
                {"from":"southwestern boulevard","to":"Palacedomain","status":"closed ornamental boundary"},
                {"from":"southern boulevard","to":"Downtown","status":"closed civic frontage"}],
            "materialNotes":{"roof_terracotta":"painted terracotta; warm variation of pottery",
                "pottery":"witness burgundy ceramic base with warm clay tint",
                "linen":"witness cloth shader with ivory/ochre palette",
                "foliage":"matte painted foliage, deep moss palette"},
            "sourceReferences":["Source/Elements/Assets/Maps/capital/images/arenarea.png",
                "Planning/referentiels/central-empire/capitale.md",
                "Source/Elements/Assets/Built/arena-fate-modern/manifest.json"],
            "notes":["Existing full Arena reused as exterior shell, never regenerated.",
                "Eleven gameplay identifiers preserved; positions relocated into the new streets.",
                "Casino, betting house and pub have furnished walkable interiors; pub has real 4m stair.",
                "Secondary houses remain closed; roofs independently removable for camera.",
                "Ground continuous beneath staggered paving; road pieces are batching units, not one actor per slab.",
                "Foliage extra key requires painted matte foliage material at Unreal import."]}}
    if reuse_meshes:
        manifest["meshes"].extend(m for m in previous.values() if m.get("role")=="collision-proxy")
    append_collision_proxies(manifest,out,materials,reuse=reuse_meshes,rebuild=rebuild_meshes)
    validate(manifest,out)
    (out/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"ARENAREA_COMPLETE meshes={len(manifest['meshes'])} objects={len(OBJECTS)} roofs={len(ROOFS)}",flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--verify",action="store_true")
    parser.add_argument("--layout-only",action="store_true",help="Reuse existing geometry; rebuild deterministic placement manifest only")
    parser.add_argument("--collision-only",action="store_true",help="Export authored physical proxies without changing any visual master or placement")
    parser.add_argument("--paving-only",action="store_true",help="Repair curved paving backing only, preserving all other meshes and physics")
    parser.add_argument("--finishing-only",action="store_true",help="Export only final facade, quay and orientation corrections against saved baseline")
    parser.add_argument("--seams-only",action="store_true",help="Export terrain refinement, the diagnosed curved paving batches and bridge/quay junctions only")
    parser.add_argument("--rebuild-meshes",nargs="*",default=[],help="Rebuild only named GLBs, retaining other exported geometry")
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:] if g.bpy and "--" in sys.argv else ([] if g.bpy else None))
    if args.seams_only:
        if not g.bpy:raise RuntimeError("Run --seams-only inside the serialized Blender worker")
        seams_only(args.output)
        return 0
    if args.finishing_only:
        if not g.bpy:
            raise RuntimeError("Run --finishing-only inside the serialized Blender worker")
        finishing_only(args.output)
        return 0
    if args.paving_only:
        if not g.bpy:
            raise RuntimeError("Run --paving-only inside the serialized Blender worker")
        paving_only(args.output)
        return 0
    if args.verify:
        validate(json.loads((args.output/"manifest.json").read_text(encoding="utf-8")),args.output)
        print("Arenarea manifest, hashes and source references valid.")
        return 0
    if args.collision_only:
        if g.bpy:
            collision_only(args.output)
            return 0
        return subprocess.run([str(BLENDER),"--background","--threads","2","--python-exit-code","1",
            "--python",str(Path(__file__).resolve()),"--","--output",str(args.output),"--collision-only"]).returncode
    if args.rebuild_meshes and not g.bpy:
        command=[str(BLENDER),"--background","--threads","2","--python-exit-code","1",
            "--python",str(Path(__file__).resolve()),"--","--output",str(args.output),
            "--rebuild-meshes",*args.rebuild_meshes]
        return subprocess.run(command).returncode
    if g.bpy or args.layout_only:
        build(args.output,args.layout_only or bool(args.rebuild_meshes),args.rebuild_meshes)
        return 0
    command=[str(BLENDER),"--background","--threads","2","--python-exit-code","1",
        "--python",str(Path(__file__).resolve()),"--","--output",str(args.output)]
    return subprocess.run(command).returncode


if __name__=="__main__":
    raise SystemExit(main())
