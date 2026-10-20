#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Shared geometry primitives used by the current Arena and capital districts."""
from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


import arena_geometry as g  # noqa: E402
COUNTS = {"clothPanels": 0, "carvedPanels": 0, "amphorae": 0, "sculptedColumns": 0}
LIGHTS = []


def slab(points, z, thickness=.14, material="marble_white"):
    """Closed hand-cut perimeter, with a perfectly flat walking surface."""
    n = len(points)
    vertices = [(x, y, z - thickness) for x, y in points] + [(x, y, z) for x, y in points]
    faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))]
    faces += [(j, (j + 1) % n, (j + 1) % n + n, j + n) for j in range(n)]
    g.solid(vertices, faces, material, bevel=.015)
    g.DETAIL_COUNTS["floorSlabs"] += 1


def paving(x0, x1, y0, y1, z, material="marble_white", variant=0, backing=True):
    # A curved district floor has continuous terrain beneath the closed stone
    # slabs. Its buried, coarse underlay would bridge the terrain and emerge.
    # The default preserves all validated flat Arena floor source geometry.
    if backing:
        g.block((x0+x1)/2, (y0+y1)/2, z-.24, x1-x0, y1-y0, .10, "mortar")
    rows = max(1, round((y1-y0)/.78))
    dy = (y1-y0)/rows
    for row in range(rows):
        x = x0
        cell = .91 if variant == 0 else (1.15 if variant == 1 else .72)
        first = cell * (.52 if (row+variant) % 2 else 1)
        while x < x1-.001:
            width = min(first if x == x0 else cell, x1-x)
            a,b = x+.012, x+width-.012
            c,d = y0+row*dy+.012, y0+(row+1)*dy-.012
            cut = min(.052+.016*math.sin(row*2.7+x*3.3)**2, width*.17)
            slab([(a+cut,c),(b-cut*.6,c),(b,c+cut),(b,d-cut*.5),
                  (b-cut,d),(a+cut*.7,d),(a,d-cut),(a,c+cut*.6)], z, material=material)
            x += width


def lozenge(x,y,z,width=.42,height=.48,material="marble_white",depth=.09):
    g.prism([(x,z-height/2),(x+width/2,z),(x,z+height/2),(x-width/2,z)],
            y-depth/2,y+depth/2,material)


def carved_frieze(cx,y,z,width,material="marble_white"):
    """Sculpted frame and deliberate geometric relief, without invented heraldry."""
    g.block(cx,y,z,width,.20,.62,"stone_cream")
    for h in [z+.04,z+.53]:
        g.block(cx,y+.14,h,width,.10,.05,material)
    count = max(1, round(width/.76))
    for j in range(count):
        x = cx-width/2+(j+.5)*width/count
        lozenge(x,y+.16,z+.31,.40,.41,material)
        lozenge(x,y+.225,z+.31,.18,.19,"bronze",.055)
    COUNTS["carvedPanels"] += count


def broad_cornice(cx,y,z,width,depth=1.05):
    for dz,h,ext in [(0,.14,0),(.14,.14,.14),(.28,.10,.31),(.38,.18,.43),(.56,.12,.56)]:
        g.block(cx,y,z+dz,width+ext*.4,depth+ext,h,"marble_white")
    g.block(cx,y+depth/2+.22,z+.41,width,.045,.055,"bronze")
    for j in range(max(1,round(width/.39))):
        x=cx-width/2+(j+.5)*width/max(1,round(width/.39))
        g.block(x,y+depth/2+.07,z+.07,.16,.26,.23,"marble_white")


def sculpted_column(x,y,z,height=4.30,radius=.37):
    g.block(x,y,z,1.20,1.20,.20,"stone_cream")
    g.block(x,y,z+.20,1.02,1.02,.12,"marble_white")
    g.turned(x,y,z+.32,[(.49,0),(.49,.09),(.43,.18),(.41,.26),(.44,.31)])
    shaft = height-1.36
    rings=18
    profile=[]
    for j in range(rings+1):
        u=j/rings
        r=radius*(1-.09*u)+.028*math.sin(math.pi*u)
        profile.append((r,u*shaft))
    g.turned(x,y,z+.63,profile,sides=96,flutes=.030)
    g.DETAIL_COUNTS["flutedDrums"] += 1
    for dz in [.65,.65+shaft-.10]:
        g.turned(x,y,z+dz,[(radius+.035,0),(radius+.053,.045),(radius+.035,.075)],"bronze")
    capz=z+height-.73
    g.turned(x,y,capz,[(.34,0),(.37,.11),(.45,.24),(.50,.39),(.52,.46)])
    # Four broad, curled consoles on every capital, not thin applied texture.
    for dx,dy in [(-.43,0),(.43,0),(0,-.43),(0,.43)]:
        g.turned(x+dx,y+dy,capz+.18,[(.105,0),(.16,.11),(.18,.21),(.13,.31)],"marble_white",32)
    g.block(x,y,z+height-.17,1.22,1.22,.17,"marble_white")
    COUNTS["sculptedColumns"] += 1


def cloth(cx,y,top,width,length,folds=10,swag=.22,material="burgundy",thickness=.028):
    """Closed, double-surface heavy fabric with folds and a shaped lower hem."""
    nx,nz=folds*8,14
    points=[]
    for side in [-1,1]:
        for k in range(nz+1):
            v=k/nz
            for j in range(nx+1):
                u=j/nx
                x=cx+(u-.5)*width
                fold=.070*math.sin(u*math.tau*folds)+.020*math.sin(u*math.tau*folds*2)
                belly=.07*math.sin(math.pi*v)
                hem=swag*math.sin(math.pi*u)**2
                zz=top-v*length-v*v*hem
                points.append((x,y+fold+belly+side*thickness/2,zz))
    layer=(nx+1)*(nz+1)
    faces=[]
    for side in range(2):
        offset=side*layer
        for k in range(nz):
            for j in range(nx):
                a=offset+k*(nx+1)+j
                faces.append((a,a+1,a+nx+2,a+nx+1))
    for j in range(nx):
        faces.append((j,j+1,j+1+layer,j+layer))
        a=nz*(nx+1)+j
        faces.append((a,a+1,a+1+layer,a+layer))
    for k in range(nz):
        for j in [0,nx]:
            a=k*(nx+1)+j
            faces.append((a,a+nx+1,a+nx+1+layer,a+layer))
    g.solid(points,faces,material,bevel=.002)
    g.FACE_SMOOTH[-len(faces):]=[True]*len(faces)
    # Bronze hem as physical round braid following the shape of the cloth.
    for j in range(nx):
        u0,u1=j/nx,(j+1)/nx
        def hem(u):
            return (cx+(u-.5)*width,y+.070*math.sin(u*math.tau*folds)+.020*math.sin(u*math.tau*folds*2)+thickness,
                    top-length-swag*math.sin(math.pi*u)**2)
        g.rod(hem(u0),hem(u1),.016,"bronze",8)
    COUNTS["clothPanels"] += 1


def roof_tile(x0,x1,y0,y1,lift):
    """Closed curved clay tile on the common roof plane, with a raised side lip."""
    nx,ny=3,6
    points=[]
    for side in [0,1]:
        for i in range(nx+1):
            u=i/nx
            x=x0+(x1-x0)*u
            plane=10.0+1.25*(1-abs(x+5)/4.35)
            for j in range(ny+1):
                v=j/ny
                arch=.040*(2*v-1)**2+.012*math.sin(math.pi*u)
                points.append((x,y0+(y1-y0)*v,plane+lift+arch+side*.052))
    layer=(nx+1)*(ny+1)
    faces=[]
    for side in range(2):
        offset=side*layer
        for i in range(nx):
            for j in range(ny):
                a=offset+i*(ny+1)+j
                faces.append((a,a+1,a+ny+2,a+ny+1))
    for j in range(ny):
        for i in [0,nx]:
            a=i*(ny+1)+j
            faces.append((a,a+1,a+1+layer,a+layer))
    for i in range(nx):
        for j in [0,ny]:
            a=i*(ny+1)+j
            faces.append((a,a+ny+1,a+ny+1+layer,a+layer))
    g.solid(points,faces,"dark_metal",bevel=.006)
    g.FACE_SMOOTH[-len(faces):]=[True]*len(faces)


def chair(x,y,z,principal=False):
    scale=1.12 if principal else .84
    for dx in [-.33,.33]:
        for dy in [-.28,.28]:
            g.turned(x+dx*scale,y+dy*scale,z,[(.055,0),(.065,.12),(.045,.45)],"wood",16)
    g.block(x,y,z+.43,.88*scale,.80*scale,.12,"wood")
    g.block(x,y,z+.55,.80*scale,.73*scale,.10,"burgundy")
    g.block(x,y-.34*scale,z+.60,.93*scale,.15,1.11 if principal else .71,"wood")
    cloth(x,y-.24*scale,z+(1.66 if principal else 1.29),.74*scale,.97 if principal else .60,6,.04)
    for dx in [-.47,.47]:
        g.block(x+dx*scale,y,z+.90,.09,.80*scale,.10,"wood")
        g.turned(x+dx*scale,y+.28*scale,z+.58,[(.045,0),(.055,.35)],"bronze",16)
    g.block(x,y-.22*scale,z+(1.71 if principal else 1.34),1.02*scale,.10,.09,"bronze")


def chest(x,y,z,width=1.0,depth=.58,height=.63):
    g.block(x,y,z+.08,width,depth,height-.08,"wood")
    for dx in [-width*.38,width*.38]:
        g.block(x+dx,y,z+.05,.065,depth+.02,height+.04,"dark_metal")
    g.block(x,y,z+height,width+.04,depth+.04,.09,"wood")
    g.block(x,y+depth/2+.017,z+height*.61,.11,.038,.18,"dark_metal")
    for dx in [-width*.40,width*.40]:
        g.block(x+dx,y,z, .10,depth*.75,.08,"wood")


def bench(x,y,width=2.35):
    for dx in [-width*.37,width*.37]:
        g.block(x+dx,y,.03,.16,.57,.46,"wood")
    for j in range(3):
        g.block(x,y+(j-1)*.19,.49,width,.175,.11,"wood")
    g.block(x,y-.27,.55,width,.10,.53,"wood")
    for dx in [-width*.38,width*.38]:
        g.block(x+dx,y-.29,.20,.11,.11,.92,"wood")


def amphora(x,y,z,scale=1):
    profile=[(.18,0),(.20,.09),(.32,.22),(.39,.48),(.33,.73),(.18,.88),(.14,1.04),
             (.18,1.10),(.18,1.15),(.12,1.15),(.105,1.02),(.13,.87),(.27,.70),(.31,.48),(.23,.23),(.16,.12)]
    g.turned(x,y,z,[(r*scale,h*scale) for r,h in profile],"burgundy",48)
    # Real handles are segmented curved rods; they are below any public handrail.
    for side in [-1,1]:
        last=None
        for j in range(17):
            a=math.pi*j/16
            point=(x+side*(.16+.25*math.sin(a))*scale,y,z+(.95-.47*j/16)*scale)
            if last:
                g.rod(last,point,.031*scale,"burgundy",10)
            last=point
    COUNTS["amphorae"] += 1


def lamp(x,y,z,grand=False):
    base=.48 if grand else .33
    g.block(x,y,z,base*1.8,base*1.8,.15,"stone_cream")
    g.turned(x,y,z+.15,[(base,0),(base,.14),(base*.7,.24),(base*.62,.88),(base*.80,1.0)],"marble_white" if grand else "stone_cream")
    g.turned(x,y,z+1.15,[(base*.69,0),(base*.86,.09),(base*.90,.20),(base*.62,.25)],"bronze" if grand else "dark_metal")
    top=z+2.0
    for dx,dy in [(-.18,-.18),(-.18,.18),(.18,-.18),(.18,.18)]:
        g.rod((x+dx,y+dy,z+1.39),(x+dx*.70,y+dy*.70,top),.035,"dark_metal",12)
    g.turned(x,y,top,[(.31,0),(.20,.13),(.08,.23)],"bronze" if grand else "dark_metal",32)
    LIGHTS.append({"position":[x,y,z+1.70],"color":"#f3bf76","range":5.0,"always":True,"flicker":False,"zone":"loge" if grand else "lower"})
