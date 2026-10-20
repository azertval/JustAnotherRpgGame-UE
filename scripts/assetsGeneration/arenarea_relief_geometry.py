#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Reproducible sculpted city terrain; no engine state and no external assets."""
import math


def subdivisions(a,b,spacing=3.):
    count=math.ceil((b-a)/spacing)
    return [a+(b-a)*j/count for j in range(count+1)]


def terrain_axes(region,spacing,refinements=()):
    x0,x1,y0,y1=region
    xs,ys=subdivisions(x0,x1,spacing),subdivisions(y0,y1,spacing)
    for refinement in refinements:
        a,b,c,d=refinement["bounds"]
        # Propagate knots along each axis across neighbouring regions. Shared
        # boundaries then retain identical vertices, without T-junction gaps.
        if a<x1 and c>x0:
            xs+=subdivisions(max(a,x0),min(c,x1),refinement["spacing"])
        if b<y1 and d>y0:
            ys+=subdivisions(max(b,y0),min(d,y1),refinement["spacing"])
    return sorted(set(xs)),sorted(set(ys))


def terrain(g,height,smooth_top=False,spacing=3.,refinements=()):
    """Closed grid volumes with the same diagonal in render and physics.

    Large planar n-gons cannot represent slopes: each upper cell is explicitly
    triangulated. The pool opening has exact edges, independent of grid phase.
    """
    regions=[(-212,-145,-148,360),(-109,240,-148,360),
             (-145,-109,-148,61),(-145,-109,85,360)]
    for x0,x1,y0,y1 in regions:
        xs,ys=terrain_axes((x0,x1,y0,y1),spacing,refinements)
        points=[(x,y,height(x,y)) for y in ys for x in xs]
        count=len(points)
        points.extend((x,y,z-1.4) for x,y,z in points[:])
        nx=len(xs)
        faces=[]
        for row in range(len(ys)-1):
            for col in range(nx-1):
                a=row*nx+col;b=a+1;c=b+nx;d=a+nx
                faces.extend([(a,b,c),(a,c,d),(a+count,c+count,b+count),
                              (a+count,d+count,c+count)])
        boundary=[*range(nx),*[row*nx+nx-1 for row in range(1,len(ys))],
                  *range(count-2,count-nx-1,-1),*[row*nx for row in range(len(ys)-2,0,-1)]]
        faces.extend((a,b,b+count,a+count) for a,b in zip(boundary,boundary[1:]+boundary[:1]))
        first_face=len(g.FACE_SMOOTH)
        g.solid(points,faces,"stone_cream",bevel=0)
        if smooth_top:
            # Only the outdoor upper surface interpolates normals. The closed
            # volume sides and underside keep their architectural hard edges.
            for index,face in enumerate(faces):
                if len(face)==3 and all(vertex<count for vertex in face):
                    g.FACE_SMOOTH[first_face+index]=True
    pool_z=height(-127,73)
    g.block(-127,73,pool_z-1.15,36,24,.25,"mortar")
    for x in [-145,-109]:
        g.block(x,73,pool_z-1,.45,24,1.35,"marble_white")
    for y in [61,85]:
        g.block(-127,y,pool_z-1,36,.45,1.35,"marble_white")


def transform_new(g,start,item,height,warp):
    """Transform helper buffers (Blender north=-map Y) to absolute map coords."""
    x0,y0,z0=item["position"]
    c,s=math.cos(math.radians(item.get("yaw",0))),math.sin(math.radians(item.get("yaw",0)))
    for index in range(start,len(g.VERTS)):
        x,north,z=g.VERTS[index]
        y=-north
        # The exporter/in-game yaw convention rotates map coordinates clockwise.
        px,py=x*c+y*s+x0,-x*s+y*c+y0
        g.VERTS[index]=(px,-py,z+z0+(height(px,py) if warp else 0.))


def heightfield(height):
    origin=[-312.,-168.]; spacing=[1.5,1.5];width=485;rows=361
    return {"origin":origin,"spacing":spacing,"width":width,"height":rows,
            "heights":[round(height(origin[0]+x*1.5,origin[1]+y*1.5),5)
                       for y in range(rows) for x in range(width)]}


def stadium_points(radius=38.,straight=104.,segments=64):
    return [(radius*math.cos(math.tau*j/segments),
             radius*math.sin(math.tau*j/segments)+(straight/2 if math.sin(math.tau*j/segments)>=0 else -straight/2))
            for j in range(segments)]


def conformed_lawns(g,sources,height,collision=False):
    """Closed planted patches follow the terrain, including their buried rim."""
    rim=[(-9,-5),(-7.5,-6),(7,-6),(9,-4.5),(9,4.7),(7.5,6),(-7,6),(-9,4.6)]
    n=len(rim)
    points=[(x,y,-.22) for x,y in rim]+[(x,y,.022) for x,y in rim]
    points.extend((x*.72,y*.72,.16+.035*math.sin(x)) for x,y in rim)
    points.append((0,0,.26))
    faces=[(0,j+1,j) for j in range(1,n-1)]
    for j in range(n):
        k=(j+1)%n
        for a,b,c,d in [(j,k,k+n,j+n),(j+n,k+n,k+2*n,j+2*n)]:
            faces.extend([(a,b,c),(a,c,d)])
        faces.append((j+2*n,k+2*n,3*n))
    # Shared edge midpoints preserve a watertight shell. Three refinements
    # retain the sculpted profile while resolving changes in the city slope.
    for _ in range(3):
        edges={}
        def midpoint(a,b):
            key=tuple(sorted((a,b)))
            if key not in edges:  # noqa: B023
                edges[key]=len(points)  # noqa: B023
                points.append(tuple((points[a][k]+points[b][k])/2 for k in range(3)))
            return edges[key]  # noqa: B023
        refined=[]
        for a,b,c in faces:
            ab,bc,ca=midpoint(a,b),midpoint(b,c),midpoint(c,a)
            refined.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
        faces=refined
    for item in sources:
        ox,oy,oz=item['position']
        a=math.radians(item.get('yaw',0));c,s=math.cos(a),math.sin(a)
        verts=[]
        for x,y,z in points:
            px,py=ox+x*c+y*s,oy-x*s+y*c
            verts.append((px,py,z+oz+height(px,py)))
        first=len(g.FACE_SMOOTH)
        g.solid(verts,faces,'stone_cream' if collision else 'foliage',bevel=0)
        if not collision:
            for index,face in enumerate(faces):
                if all(points[v][2]>=.02 for v in face):
                    g.FACE_SMOOTH[first+index]=True
