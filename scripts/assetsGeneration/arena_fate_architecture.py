#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Arena of Fate: replayable architecture workshop, Blender --background --python FILE.

All dimensions are metres; whole-cell footprints are documented in the fragment.
Colours distinguish stone courses and physical mouldings, never baked lighting.
The workshop measures its production; it does not prescribe a decor budget.
"""
import bpy
import bmesh
import math
import json
import struct
import sys
import argparse
import random
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
DEFAULT = ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/Architecture'
P = ['efe6d2','e1d6bf','d9c7a3','cbb89a','9c948a','b9b0a2','5c4a2a','8e2335','c9a45c','2f7f86','414248','736e69','ad9161','583f30','ddd8cd','715082',
     '958d80','9b9387','90887e','807a73','cfc2a9','d4c7af','cabea7','b9ad97','aaa094','a59b90','b0a69a','938b80','aaa094','aaa094','aaa094','aaa094']
V=[]; F=[]; C=[]
def face(v,c):
    n=len(V); V.extend(v); F.append(tuple(range(n,n+len(v)))); C.append(c)
def box(x,y,z,w,d,h,c=0):
    a=x-w/2;b=x+w/2;e=y-d/2;f=y+d/2
    pts=[(a,e,z),(b,e,z),(b,f,z),(a,f,z),(a,e,z+h),(b,e,z+h),(b,f,z+h),(a,f,z+h)]
    for ids in [(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]:face([pts[i] for i in ids],c)
def lathe(x,y,z,profile,c=0,n=16):
    for i in range(len(profile)-1):
        r,h=profile[i];s,k=profile[i+1]
        for j in range(n):
            a=j*math.tau/n;b=(j+1)*math.tau/n
            face([(x+r*math.cos(a),y+r*math.sin(a),z+h),(x+r*math.cos(b),y+r*math.sin(b),z+h),(x+s*math.cos(b),y+s*math.sin(b),z+k),(x+s*math.cos(a),y+s*math.sin(a),z+k)],c)
    for radius,height,rev in [(profile[0][0],profile[0][1],True),(profile[-1][0],profile[-1][1],False)]:
        verts=[(x+radius*math.cos(j*math.tau/n),y+radius*math.sin(j*math.tau/n),z+height) for j in range(n)]
        face(verts[::-1] if rev else verts,c)
def rod(a,b,r,c=6,n=10):
    a=Vector(a);b=Vector(b);t=(b-a).normalized();q=t.cross(Vector((0,0,1)))
    if q.length<.01:q=t.cross(Vector((0,1,0)))
    q.normalize();v=t.cross(q)
    for j in range(n):
        aa=j*math.tau/n;bb=(j+1)*math.tau/n
        p=r*(q*math.cos(aa)+v*math.sin(aa));s=r*(q*math.cos(bb)+v*math.sin(bb))
        face([a+p,a+s,b+s,b+p],c)
def torus(x,y,z,r,t,c=8,vertical=False):
    for i in range(20):
        for j in range(8):
            pts=[]
            for u,v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]:
                a=u*math.tau/20;b=v*math.tau/8
                xx=(r+t*math.cos(b))*math.cos(a); yy=(r+t*math.cos(b))*math.sin(a);zz=t*math.sin(b)
                pts.append((x+xx,y+(zz if vertical else yy),z+(yy if vertical else zz)))
            face(pts,c)
def arch(x,y,z,ri,ro,depth,c=0,n=18):
    for i in range(n):
        a=i*math.pi/n+.009;b=(i+1)*math.pi/n-.009
        p=[(x+ri*math.cos(a),z+ri*math.sin(a)),(x+ro*math.cos(a),z+ro*math.sin(a)),(x+ro*math.cos(b),z+ro*math.sin(b)),(x+ri*math.cos(b),z+ri*math.sin(b))]
        color=24+i%3 if c==4 else c+i%3
        face([(u,y-depth/2,v) for u,v in p],color)
        face([(u,y+depth/2,v) for u,v in p[::-1]],color)
        for k in range(4):
            u,v=p[k];s,t=p[(k+1)%4];face([(u,y-depth/2,v),(u,y+depth/2,v),(s,y+depth/2,t),(s,y-depth/2,t)],color)
def column(x,y,h=3,c=0,order=0):
    box(x,y,0,.68,.68,.16,c+1);box(x,y,.16,.57,.57,.12,c)
    lathe(x,y,.28,[(.27,0),(.3,.07),(.28,.15),(.22,.23),(.20,h-.7),(.26,h-.61),(.30,h-.53),(.29,h-.43)],c,20)
    box(x,y,h-.15,.66,.66,.15,c)
    if order>0:
        for dx in [-.24,.24]:torus(x+dx,y-.27,h-.32,.105,.032,8,True)
    if order>1:
        for j in range(8):
            a=j*math.tau/8
            lathe(x+.23*math.cos(a),y+.23*math.sin(a),h-.65,[(.04,0),(.085,.17),(.03,.34)],8,6)
def masonry(w,h=3,d=.55,c=1):
    rows=round(h/.375)
    for row in range(rows):
        edges=[-w/2]+[v for v in [(-w/2+(j+.5*(row%2))*.75) for j in range(1,math.ceil(w/.75)+1)] if v<w/2]+[w/2]
        for i in range(len(edges)-1):
            a,b=edges[i:i+2];box((a+b)/2,0,row*h/rows,b-a-.018,d,h/rows-.015,(24 if c==4 else c)+(row+i)%3)
    edge=26 if c==4 else c
    box(0,0,0,w,d+.10,.14,edge);box(0,0,h-.18,w,d+.16,.18,edge)
def balustrade(w=3):
    box(0,0,0,w,.44,.15,1);box(0,0,.94,w,.48,.16,0)
    for i in range(round(w/.3)):
        x=-w/2+(i+.5)*w/round(w/.3)
        lathe(x,0,.15,[(.10,0),(.10,.08),(.05,.16),(.09,.26),(.1,.38),(.055,.51),(.065,.64),(.10,.70),(.10,.79)],0,12)
def floor(kind,variant):
    if kind=='sand':
        n=10
        for y in range(n):
            for x in range(n):
                def p(a,b):return (-.75+a*1.5/n,-.75+b*1.5/n,.025+.006*math.sin(a*.27+b*.22+variant)*math.sin(math.pi*a/n)*math.sin(math.pi*b/n))
                face([p(x,y),p(x+1,y),p(x+1,y+1),p(x,y+1)],2)
    else:
        box(0,0,0,1.5,1.5,.04,11 if kind=='cat-floor' else 4)
        for row in range(3):
            for col in range(3):
                box(-.5+col*.5,-.5+row*.5,.035,.485,.485,.075,(16 if kind=='cat-floor' else 20)+(row*7+col*3+variant)%3)
def arcade(order):
    for x in [-1.875,1.875]:
        for k in range(8):box(x,.1,k*.45,.74,.72,.433,1+k%3)
        column(x,-.36,3.7,0,order)
    arch(0,.08,2.12,1.47,1.83,.70,0)
    for z,w,d,h,c in [(3.97,4.5,.94,.18,1),(4.15,4.5,1.08,.16,0),(4.31,4.5,.94,.19,2)]:box(0,.02,z,w,d,h,c)
    for x in [-1.4,-.7,0,.7,1.4]:box(x,-.48,4.13,.14,.12,.16,8)
def seating():
    for i in range(9):
        y=-2.25+(i+.5)*.5;h=(i+1)/3
        box(0,y,0,4.5,.50,h,1)
        box(0,y,h-.05,4.46,.45,.05,0)
        for j in range(10):box(-2.025+j*.45,y+.04,h,.38,.31,.095,7)
def loge():
    box(0,0,0,4.5,3,.25,0)
    for x in [-2,2]:column(x,-1.05,3.9,0,2);column(x,1.05,3.9,0,1)
    box(0,1.27,.25,4.4,.22,3.5,7)
    for x in [-1.5,0,1.5]:
        box(x,.88,.25,.75,.65,.45,8);box(x,1.12,.70,.72,.17,.85,7)
    box(0,0,3.9,4.5,3,.2,0)
    face([(-2.25,-1.5,4.1),(2.25,-1.5,4.1),(0,-1.5,4.5)],7)
    face([(-2.25,1.5,4.1),(0,1.5,4.5),(2.25,1.5,4.1)],7)
    face([(-2.25,-1.5,4.1),(0,-1.5,4.5),(0,1.5,4.5),(-2.25,1.5,4.1)],7)
    face([(0,-1.5,4.5),(2.25,-1.5,4.1),(2.25,1.5,4.1),(0,1.5,4.5)],7)
    for a,b in [((-2.25,-1.5,4.1),(0,-1.5,4.5)),((0,-1.5,4.5),(2.25,-1.5,4.1))]:rod(a,b,.06,8)
    balustrade(4.5)
def stair():
    for i in range(15):box(0,-2.25+(i+.5)*.3,0,3,.3,(i+1)*.2,1+i%2)
    for x in [-1.40,1.4]:
        for i in range(5):box(x,-1.8+i*.9,0,.2,.88,(i+1)*.6+.45,0)
def bars():
    box(0,0,2.8,3,.3,.2,6)
    for z in [.2,1.5,2.7]:box(0,0,z,3,.14,.12,6)
    for i in range(15):rod((-1.4+i*.2,0,0),(-1.4+i*.2,0,2.8),.027,10)
    for x in [-1.45,1.45]:box(x,0,0,.1,.2,2.8,6)
    box(.32,-.12,1.3,.2,.07,.28,8)
def bench():
    for y in [-.24,0,.24]:box(0,y,.52,2.8,.2,.13,13)
    for x in [-1,1]:
        box(x,0,0,.18,.62,.52,6);box(x,0,.08,.38,.66,.12,6)
def rack():
    for x in [-1.3,1.3]:box(x,0,0,.16,.22,1.9,13);box(x,0,0,.32,.75,.12,6)
    for z in [.3,1.5]:box(0,0,z,2.7,.15,.16,13)
    for i in range(7):
        x=-1.05+i*.35;rod((x,-.1,.1),(x,-.1,1.75),.025,6)
        face([(x-.09,-.1,1.7),(x,-.1,1.95),(x+.09,-.1,1.7),(x,-.15,1.74)],14)
        rod((x-.12,-.1,.8),(x+.12,-.1,.8),.03,8)
def fountain():
    box(0,.45,0,2.7,.4,1.8,1);arch(0,.45,1.15,.65,1.02,.44,0)
    lathe(0,-.2,0,[(.65,0),(.70,.13),(.5,.25),(.53,.4),(.75,.55),(.83,.75),(.72,.82),(.69,.66)],0,32)
    face([(.67*math.cos(j*math.tau/32),-.2+.67*math.sin(j*math.tau/32),.67) for j in range(32)],9)
    torus(0,.18,1.2,.23,.07,8,True);rod((0,.1,1.2),(0,-.2,.8),.025,9)
def brazier():
    lathe(0,0,0,[(.28,0),(.28,.13),(.16,.20),(.09,.72),(.15,.85),(.35,1.02),(.38,1.12),(.28,1.14)],6,16)
    for j in range(7):
        a=j*math.tau/7;lathe(.16*math.cos(a),.16*math.sin(a),1.08,[(.06,0),(.08,.10),(.02,.25),(0,.32)],8,5)
def altar():
    box(0,0,0,2.7,1.2,.16,11)
    for x in [-1,1]:column(x,0,1,4,1)
    box(0,0,1,3,1.5,.2,5);box(0,0,1.2,2.25,.85,.025,15)
def plinth():
    for z,w,d,h in [(0,4.5,4.5,.2),(.2,4.15,4.15,.2),(.4,3.75,3.75,.2),(.6,3.4,3.4,.2)]:box(0,0,z,w,d,h,5)
def ossuary():
    masonry(3,2.6,.4,4)
    for z in [.2,.95,1.7,2.45]:box(0,-.37,z,2.8,.45,.12,5)
    for x in [-1.35,1.35]:box(x,-.35,0,.15,.45,2.6,5)
    for k in range(3):
        for j in range(7):
            x=-1.1+j*.36;z=.35+k*.75
            lathe(x,-.4,z,[(.07,0),(.13,.06),(.14,.19),(.10,.28),(0,.31)],14,10)
            for dx in [-.043,.043]:box(x+dx,-.535,z+.15,.055,.02,.06,10)
def chains():
    box(0,.1,0,.3,.24,1.8,11)
    for i in range(13):torus(.14*math.sin(i*.3),-.13,1.65-i*.11,.075,.018,6,i%2==0)
def room_arch(c=1):
    for x in [-1.24,1.24]:
        for k in range(5):box(x,0,k*.34,.45,.58,.325,(24 if c==4 else c)+k%2)
        box(x,0,1.63,.53,.68,.15,26 if c==4 else c)
    arch(0,0,1.7,1.00,1.27,.58,c,15)
    box(0,0,2.97,3,.64,.12,26 if c==4 else c)
def torch():
    box(0,.40,1.20,.25,.09,.56,6)
    for z in [1.30,1.65]:torus(0,.34,z,.07,.022,8,True)
    rod((0,.35,1.3),(0,-.05,1.50),.065,6)
    rod((0,-.05,1.3),(0,-.05,2.04),.07,13)
    for z in [1.75,1.86,1.97]:torus(0,-.05,z,.11,.025,6)
    for j in range(5):
        a=j*math.tau/5;lathe(.07*math.cos(a),-.05+.07*math.sin(a),1.98,[(.045,0),(.06,.12),(.03,.24),(0,.40 if j==0 else .29)],8,6)
    lathe(0,-.05,1.98,[(.09,0),(.075,.08),(.025,.2),(0,.28)],7,8)
def torch_wall(c=1):
    masonry(1.5,3,.55,c)
    start=len(V);torch()
    for i in range(start,len(V)):
        x,y,z=V[i];V[i]=(x,y*.70-.555,z)
def pallet():
    box(0,0,0,2.7,1.2,.12,13)
    rng=random.Random(83)
    for i in range(110):
        x=rng.uniform(-1.27,1.27);y=rng.uniform(-.5,.5);z=rng.uniform(.13,.22)
        rod((x,y,z),(max(-1.33,min(1.33,x+rng.uniform(.15,.38))),y+rng.uniform(-.08,.08),z+.015),.018,12 if i%3 else 3,5)
    for x in [-1.15,1.15]:box(x,0,.12,.12,1.25,.09,6)
def barrel():
    profile=[(.32,0),(.37,.08),(.42,.3),(.44,.55),(.42,.8),(.37,1.02),(.32,1.08)]
    start=len(C);lathe(0,0,0,profile,13,18)
    for ci in range(start,len(C)-2):C[ci]=13 if (ci-start)%18%3 else 6
    for r,z in [(.378,.12),(.435,.4),(.435,.7),(.378,.98)]:lathe(0,0,z,[(r,0),(r+.018,.025),(r+.018,.07),(r,.085)],10,20)
    for i in range(5):box(0,(i-2)*.12,1.082,.55,.10,.018,13 if i%2 else 6)
def bucket():
    lathe(0,0,0,[(.19,0),(.21,.04),(.27,.4),(.27,.44),(.235,.44),(.175,.07)],13,16)
    for z,r in [(.05,.205),(.37,.265)]:torus(0,0,z,r,.025,10)
    torus(0,0,.57,.24,.022,6,True)
def chest():
    for j in range(5):box(-.44+j*.22,0,.09,.20,.80,.58,13)
    box(0,0,0,1.1,.86,.1,6)
    for j in range(14):
        a=j*math.pi/14;b=(j+1)*math.pi/14
        face([(-.55,.4*math.cos(a),.67+.28*math.sin(a)),(.55,.4*math.cos(a),.67+.28*math.sin(a)),(.55,.4*math.cos(b),.67+.28*math.sin(b)),(-.55,.4*math.cos(b),.67+.28*math.sin(b))],13 if j%3 else 6)
    for x in [-.40,.40]:
        box(x,0,.10,.08,.84,.58,10)
        for j in range(14):
            a=j*math.pi/14;b=(j+1)*math.pi/14
            rod((x,.415*math.cos(a),.67+.295*math.sin(a)),(x,.415*math.cos(b),.67+.295*math.sin(b)),.026,10)
    box(0,-.445,.47,.16,.055,.24,8);torus(0,-.485,.51,.035,.009,10,True)
def guard_table():
    for j in range(5):box(0,-.42+j*.21,.88,2.7,.195,.11,13)
    for x in [-1.1,1.1]:
        for y in [-.34,.34]:box(x,y,0,.14,.14,.9,6)
    rod((-1.1,0,.30),(1.1,0,.30),.045,6)
    box(-.55,-.05,1,.65,.48,.013,14);box(-.15,.08,1.015,.42,.40,.012,2)
    for x in [.65,.85]:lathe(x,0,.99,[(.065,0),(.065,.14),(.07,.15)],8,12)
def vault():
    for y in [-1.95,0,1.95]:arch(0,y,2.35,1.75,2.05,.28,1)
    for x in [-1.98,1.98]:
        for k in range(6):box(x,0,k*.39,.35,4.5,.38,2+k%2)
    for j in range(15):
        a=j*math.pi/15;b=(j+1)*math.pi/15
        face([(2*math.cos(a),-2.25,2.35+2*math.sin(a)),(2*math.cos(b),-2.25,2.35+2*math.sin(b)),(2*math.cos(b),2.25,2.35+2*math.sin(b)),(2*math.cos(a),2.25,2.35+2*math.sin(a))],1+j%3)
def podium():
    masonry(4.5,3,.75,0)
    for x in [-2,2]:box(x,-.43,.2,.27,.16,2.6,0)
    for x in [-1.4,0,1.4]:
        torus(x,-.45,1.65,.22,.06,8,True)
def corner():
    for i in range(8):
        z=i*.375;box(0,.48,z,1.5,.54,.36,1+i%3);box(.48,-.27,z,.54,.96,.36,1+i%3)
    box(0,.48,2.82,1.5,.65,.18,0);box(.48,-.27,2.82,.65,.96,.18,0)

def transformed(fn,x=0,y=0,z=0,angle=0):
    start=len(V);fn();co=math.cos(angle);si=math.sin(angle)
    for i in range(start,len(V)):
        a,b,c=V[i];V[i]=(x+a*co-b*si,y+a*si+b*co,z+c)
def elliptic_band(rx,ry,width,z,h,c=0,segments=120,gap=True):
    for i in range(segments):
        a=i*math.tau/segments;b=(i+1)*math.tau/segments
        mid=(a+b)/2
        if gap and abs(math.sin(mid))<.105:continue
        p=[(rx*math.cos(a),ry*math.sin(a)),((rx+width)*math.cos(a),(ry+width)*math.sin(a)),((rx+width)*math.cos(b),(ry+width)*math.sin(b)),(rx*math.cos(b),ry*math.sin(b))]
        face([(x,y,z+h) for x,y in p],c)
        for j in range(4):
            x,y=p[j];u,v=p[(j+1)%4];face([(x,y,z),(u,v,z),(u,v,z+h),(x,y,z+h)],c)
def arena_shell():
    # Podium courses are real individual stones, with a physical recessed joint.
    for k in range(8):elliptic_band(16.5,10.5,.72,k*.375,.36,k%3)
    elliptic_band(16.45,10.45,.9,2.82,.18,0)
    for k in range(9):
        rx=17.3+k*.61;ry=11.3+k*.61;z=3+k*.34
        elliptic_band(rx,ry,.61,0,z,1)
        elliptic_band(rx,ry,.60,z,.10,0)
        # Long burgundy seat cushions create the dense rake visible in the mockup.
        for j in range(112):
            a=(j+.5)*math.tau/112
            if abs(math.sin(a))<.13:continue
            x=(rx+.30)*math.cos(a);y=(ry+.30)*math.sin(a)
            tangent=math.atan2((ry+.3)*math.cos(a),-(rx+.3)*math.sin(a))
            transformed(lambda:box(0,0,0,.78,.32,.13,7),x,y,z+.10,tangent)
    # Low front parapet gives a cutaway view; back ring carries loges.
    for j in range(42):
        a=(j+.5)*math.tau/42
        if abs(math.sin(a))<.14:continue
        for order in range(3 if math.sin(a)>.08 else 2):
            start=len(V);arcade(order)
            # Shape each bay to its actual elliptical sector: the two ends
            # meet the neighbouring bay, with no overlapping straight modules.
            for vi in range(start,len(V)):
                x,y,z=V[vi];angle=a+x*(math.tau/42)/4.5
                V[vi]=((24-y)*math.cos(angle),(16.9-y)*math.sin(angle),order*3+z*2/3)
    for j in range(13):
        a=math.radians(160-j*140/12)
        x=23.1*math.cos(a);y=16.0*math.sin(a)
        tangent=math.atan2(16*math.cos(a),-23.1*math.sin(a))
        # Tangent rotated by pi faces loges inward toward the sand.
        transformed(loge,x,y,6,tangent+math.pi)
    for j in range(48):
        a=(j+.5)*math.tau/48
        if abs(math.sin(a))<.14:continue
        x=17.1*math.cos(a);y=11.1*math.sin(a)
        tangent=math.atan2(11.1*math.cos(a),-17.1*math.sin(a))
        transformed(lambda:balustrade(1.5),x,y,3,tangent)
    # Gate masonry frames span the long-axis openings, without obstructing them.
    for sign in [-1,1]:transformed(lambda:arcade(2),sign*22.5,0,0,math.pi/2)

def material(output):
    img=bpy.data.images.new('arena-matter-atlas',256,128,alpha=True)
    colors=[tuple(int(h[i:i+2],16)/255 for i in [0,2,4]) for h in P]
    pixels=[]
    for y in range(128):
        for x in range(256):
            index=(x//32)+8*(y//32);rgb=colors[index]
            if index==2:
                u=(x%32)/31;v=(y%32)/31
                # Broad clean sand modulation, zero at every edge. No grains,
                # directional shadow, regular marks or alternating polygons.
                delta=.012*math.sin(math.pi*u)*math.sin(math.pi*v)*math.sin(2.1*u+1.4*v)
                rgb=tuple(max(0,min(1,c+delta)) for c in rgb)
            pixels.extend((*rgb,1))
    img.pixels=pixels
    img.filepath_raw=str(output/'matter-atlas.png');img.file_format='PNG';img.save();img.pack()
    mat=bpy.data.materials.new('painted-matter');mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return mat
def export(asset,footprint,build,output,mat,kind='tall',bevel=.025):
    global V,F,C
    V=[];F=[];C=[];build()
    mesh=bpy.data.meshes.new(asset);mesh.from_pydata(V,[],F);mesh.update()
    obj=bpy.data.objects.new(asset,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='albedo')
    for poly,c in zip(mesh.polygons,C):
        u=(c%8+.5)/8;v=(c//8+.5)/4
        for li in poly.loop_indices:uv.data[li].uv=(u,v)
    if asset.startswith('af-sand-'):
        variant=ord(asset[-1])-ord('a')
        for loop in mesh.loops:
            p=mesh.vertices[loop.vertex_index].co;u=(p.x+.75)/1.5;v=(p.y+.75)/1.5
            for _ in range(variant):u,v=v,1-u
            uv.data[loop.index].uv=((64.5+u*31)/256,(.5+v*31)/128)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(mesh);bm.free()
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    if bevel:
        mod=obj.modifiers.new('physical-stone-and-wood-bevels','BEVEL');mod.width=bevel;mod.segments=1 if asset=='af-arena-shell' else 2;mod.affect='EDGES';mod.limit_method='ANGLE';mod.angle_limit=1.2 if asset=='af-arena-shell' else .5
        bpy.ops.object.modifier_apply(modifier=mod.name)
    tri=obj.modifiers.new('triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
    path=output/(asset+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_animations=False,export_cameras=False,export_lights=False)
    data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+length])
    assert len(g['meshes'])==1 and len(g['meshes'][0]['primitives'])==1 and len(g['materials'])==1
    prim=g['meshes'][0]['primitives'][0];assert all(k in prim['attributes'] for k in ['POSITION','NORMAL','TEXCOORD_0'])
    assert g['images'][0].get('bufferView') is not None
    tris=g['accessors'][prim['indices']]['count']//3
    bounds=[list(v) for v in [tuple(min(p[i] for p in V) for i in range(3)),tuple(max(p[i] for p in V) for i in range(3))]]
    result={'mesh':asset+'.glb','class':kind,'footprint':footprint,'tactical':'open' if kind=='floor' else 'solid'}
    measurement={'id':asset,'triangles':tris,'bytes':len(data),'boundsBlender':bounds,'footprint':footprint}
    bpy.data.objects.remove(obj,do_unlink=True)
    print('PRODUCED',asset,tris,len(data),flush=True)
    return result,measurement
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=DEFAULT);parser.add_argument('--only',default='');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    output=args.output;output.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);mat=material(output)
    jobs=[]
    for kind in ['sand','paving','cat-floor']:
        for n in range(3):jobs.append(('af-'+kind+'-'+chr(97+n),[1,1],lambda k=kind,n=n:floor(k,n),'floor',0))
    for name,fp,fn in [('wall-stone',[2,1],lambda:masonry(3)),('wall-catacomb',[2,1],lambda:masonry(3,3,.55,4)),('wall-corner',[1,1],corner),('podium',[3,1],podium),('seating',[3,3],seating),('loge',[3,2],loge),('balustrade',[2,1],balustrade),('stair',[2,3],stair),('gate',[3,1],lambda:arcade(2)),('prison-bars',[2,1],bars),('vault',[3,3],vault),('bench',[2,1],bench),('rack',[2,1],rack),('fountain',[2,1],fountain),('brazier',[1,1],brazier),('chains',[1,1],chains),('altar',[2,1],altar),('effigy-plinth',[3,3],plinth),('ossuary',[2,1],ossuary),('column',[1,1],lambda:column(0,0,3.9,0,2))]:jobs.append(('af-'+name,fp,fn,'tall',.025))
    for i,order in enumerate(['tuscan','ionic','corinthian']):jobs.append(('af-arcade-'+order,[3,1],lambda i=i:arcade(i),'tall',.02))
    def railcorner():
        transformed(lambda:balustrade(1.0),x=-.25,y=.5)
        transformed(lambda:balustrade(1.0),x=.5,y=-.25,angle=math.pi/2)
        box(.5,.5,0,.5,.5,1.10,0)
    jobs.append(('af-balustrade-corner',[1,1],railcorner,'tall',.012))
    for family,color in [('stone',1),('catacomb',4)]:
        for axis in ['x','y']:
            for low in [False,True]:
                name='af-wall-'+family+'-'+axis+('-low' if low else '')
                jobs.append((name,[1,1],lambda c=color,a=axis,l=low:transformed(lambda:masonry(1.5,1.2 if l else 3,.55,c),angle=math.pi/2 if a=='y' else 0),'tall',.018))
    jobs.append(('af-arena-shell',[34,24],arena_shell,'wide',.018))
    for family,color in [('stone',1),('catacomb',4)]:
        for axis in ['x','y']:
            jobs.append(('af-arch-'+family+'-'+axis,[2,1] if axis=='x' else [1,2],lambda c=color,a=axis:transformed(lambda:room_arch(c),angle=math.pi/2 if a=='y' else 0),'tall',.018))
    for name,fp,fn in [('torch',[1,1],torch),('pallet',[2,1],pallet),('barrel',[1,1],barrel),('bucket',[1,1],bucket),('chest',[1,1],chest),('guard-table',[2,1],guard_table)]:
        jobs.append(('af-'+name,fp,fn,'tall',.01))
    for family,color in [('stone',1),('catacomb',4)]:
        for axis in ['x','y']:
            jobs.append(('af-wall-torch-'+family+'-'+axis,[1,1],lambda c=color,a=axis:transformed(lambda:torch_wall(c),angle=math.pi/2 if a=='y' else 0),'tall',.012))
    textures={};measurements=[]
    if args.only and (output/'architecture-manifest.json').exists():
        textures=json.loads((output/'architecture-manifest.json').read_text(encoding='utf8'))['textures']
        measurements=json.loads((output/'architecture-measurements.json').read_text(encoding='utf8'))
    for name,fp,fn,kind,bev in jobs:
        if args.only and name not in args.only.split(','):continue
        result,measure=export(name,fp,fn,output,mat,kind,bev)
        if name=='af-arena-shell' or name.startswith('af-arch-'):result['tactical']='open'
        textures['scene/arena-of-fate/'+name]=result;measurements=[m for m in measurements if m['id']!=name];measurements.append(measure)
    # These modules model a three-metre level. Preserve the installed place's
    # calibration, expressed against its 256 x 159 pixel art diamond.
    storey_art=3*256/(1.5*math.sqrt(2))*math.sqrt(1-(159/256)**2)
    (output/'architecture-manifest.json').write_text(json.dumps({'version':1,'tile':[256,159],'storey':storey_art,'textures':textures},indent=2),encoding='utf8')
    (output/'architecture-measurements.json').write_text(json.dumps(measurements,indent=2),encoding='utf8')
    placements=[]
    for j in range(13):
        a=math.radians(160-j*140/12);x=23.1*math.cos(a);y=16*math.sin(a)
        placements.append({'index':j,'blender':[x,y,6],'anchorCellApprox':[round((x+25.5)/1.5-.5),round((18-y)/1.5-.5)],'rotationRadians':math.atan2(16*math.cos(a),-23.1*math.sin(a))+math.pi})
    (output/'arena-placements.json').write_text(json.dumps({'shellFootprint':[34,24],'shellAnchor':[0,0],'sandEllipseCells':[22,14],'mapCenter':[17,12],'loges':placements},indent=2),encoding='utf8')
if __name__=='__main__':main()
