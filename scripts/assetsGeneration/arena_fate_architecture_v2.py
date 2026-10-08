#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Colosseum V2 only. Procedural geometry, generated diffuse materials, surface UVs.

Blender --background --threads 2 --python-exit-code 1 --python FILE.
Never installs outputs. Underground and figurative sculptures are untouched.
"""
import bpy
import bmesh
import math
import json
import struct
import sys
import argparse
import random
import importlib.util
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/V2'
spec=importlib.util.spec_from_file_location('base',Path(__file__).with_name('arena_fate_architecture.py'))
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
box=b.box;lathe=b.lathe;rod=b.rod;arch=b.arch;face=b.face;transform=b.transformed
UV=[]

def column(x,y,h=3,c=0,order=0):
    """True fluted shaft, stacked torus mouldings and nonfigurative capitals."""
    box(x,y,0,.72,.72,.14,0);box(x,y,.14,.62,.62,.11,0)
    lathe(x,y,.25,[(.29,0),(.32,.055),(.30,.11),(.25,.16),(.24,.23)],0,24)
    n=48
    for z0,z1,r0,r1 in [(.48,h*.42,.235,.218),(h*.42,h-.65,.218,.19)]:
        for j in range(n):
            a=j*math.tau/n;aa=(j+1)*math.tau/n
            rr0=r0*(1-.12*(j%2));rr1=r1*(1-.12*(j%2))
            ss0=r0*(1-.12*((j+1)%2));ss1=r1*(1-.12*((j+1)%2))
            face([(x+rr0*math.cos(a),y+rr0*math.sin(a),z0),(x+ss0*math.cos(aa),y+ss0*math.sin(aa),z0),(x+ss1*math.cos(aa),y+ss1*math.sin(aa),z1),(x+rr1*math.cos(a),y+rr1*math.sin(a),z1)],0)
    lathe(x,y,h-.65,[(.21,0),(.25,.05),(.26,.09),(.25,.16),(.33,.39),(.35,.43)],0,24)
    box(x,y,h-.22,.70,.70,.10,0);box(x,y,h-.12,.75,.75,.12,0)
    if order:
        for dx in [-.24,.24]:b.torus(x+dx,y-.26,h-.32,.10,.025,0,True)
    if order==2:
        for j in range(8):
            a=j*math.tau/8
            lathe(x+.22*math.cos(a),y+.22*math.sin(a),h-.57,[(.035,0),(.075,.10),(.075,.18),(.025,.29)],0,6)
b.column=column

def cloth(w,d,z):
    # A canopy's scallops and edge piping are physical, never painted folds.
    for j in range(24):
        x=-w/2+w*j/24;xx=x+w/24
        for k in range(6):
            y=-d/2+d*k/6;yy=y+d/6
            def p(u,v):return (u,v,z+.48*(1-abs(2*v/d))+.04*math.cos((u+w/2)*24/w*math.tau/4))
            face([p(x,y),p(xx,y),p(xx,yy),p(x,yy)],7)
        a=z+.04*math.cos(j*math.tau/4);aa=z+.04*math.cos((j+1)*math.tau/4)
        face([(x,-d/2,a),(xx,-d/2,aa),(xx,-d/2,aa-.24),(x,-d/2,a-.24)],7)
    for a,bb in [((-w/2,-d/2,z-.24),(w/2,-d/2,z-.24)),((-w/2,d/2,z),(w/2,d/2,z)),((-w/2,-d/2,z),(-w/2,0,z+.48)),((-w/2,0,z+.48),(-w/2,d/2,z)),((w/2,-d/2,z),(w/2,0,z+.48)),((w/2,0,z+.48),(w/2,d/2,z))]:rod(a,bb,.035,8)

def loge(imperial=False,open_front=False):
    w=6.5 if imperial else 3.9;d=3.0 if imperial else 2.3;h=4.25 if imperial else 3.2
    box(0,0,0,w,d,.20,0);box(0,0,.20,w-.16,d-.12,.10,0)
    transform(lambda:b.balustrade(w),y=-d/2+.12,z=.30)
    for x in [-w/2+.25,w/2-.25]:
        transform(lambda:b.balustrade(d-.2),x=x,angle=math.pi/2,z=.30)
        if not open_front:column(x,-d/2+.22,h,0,2)
        box(x,d/2-.18,.30,.5,.5,1.20,0)
    for x in [-1,0,1]:
        box(x,.35,.32,.74,.64,.42,0);box(x,.55,.74,.65,.14,.86,7);box(x,.25,.74,.65,.44,.12,7)
    if open_front:return
    for x in [-w/2+.25,w/2-.25]:column(x,d/2-.22,h,0,2)
    for z,ww,dd,hh in [(h,w+.10,d+.12,.14),(h+.14,w+.28,d+.30,.13),(h+.27,w+.13,d+.16,.18)]:
        for y in [-dd/2+.12,dd/2-.12]:box(0,y,z,ww,.24,hh,0)
        for x in [-ww/2+.12,ww/2-.12]:box(x,0,z,.24,dd-.48,hh,0)
    for j in range(round(w/.32)):
        box(-w/2+(j+.5)*w/round(w/.32),-d/2-.06,h+.03,.11,.14,.14,0)
    transform(lambda:cloth(w+.02,d+.02,h+.47))
    if imperial:
        # Raised marble tympanum, gilded geometric crest, larger double columns.
        face([(-w/2-.12,-d/2-.1,h+.44),(w/2+.12,-d/2-.1,h+.44),(0,-d/2-.1,h+1.52)],0)
        for a,bb in [((-w/2-.15,-d/2-.14,h+.46),(0,-d/2-.14,h+1.55)),((0,-d/2-.14,h+1.55),(w/2+.15,-d/2-.14,h+.46))]:rod(a,bb,.095,0,12)
        for x in [-w/2+.85,w/2-.85]:column(x,-d/2+.25,h,0,2)
        for x in [-1.1,0,1.1]:box(x,.1,.35,.85,.75,.5,8)
        box(0,.45,.85,1.1,.22,1.35,7)

def gateway():
    """Front axial triumphal gate: lions are reserved for Meshy, not imitated."""
    for x in [-4.65,4.65]:
        for k in range(15):box(x,0,k*.45,2.25,2.55,.433,1)
        for z,w,d,h in [(0,2.65,2.85,.30),(6.65,2.65,2.85,.20),(6.85,2.9,3.05,.20),(7.05,2.72,2.92,.20)]:box(x,0,z,w,d,h,0)
        # Lion plinths, intentionally empty until author-selected Meshy outputs.
        box(x,0,7.25,2.2,2.0,.26,0);box(x,0,7.51,1.9,1.7,.18,0)
        for dx in [-.77,.77]:
            transform(lambda:column(0,0,6.55,0,2),x=x+dx,y=-1.25)
    arch(0,0,3.2,2.70,3.34,2.15,0,28)
    for x in [-3.05,3.05]:
        for k in range(7):box(x,0,k*.46,.74,2.12,.44,1)
    for z,w,d,h in [(6.48,11.85,2.45,.19),(6.67,12.15,2.7,.19),(6.86,11.95,2.5,.20)]:box(0,0,z,w,d,h,0)
    for j in range(32):box(-5.8+j*.374,-1.3,6.56,.13,.20,.17,0)
    # Recessed panel, uninscribed, flanked by real bead mouldings.
    box(0,-1.3,5.92,4.7,.12,.52,0)
    for z in [5.92,6.44]:rod((-2.4,-1.42,z),(2.4,-1.42,z),.045,8)

def attic():
    """L'attique plein de la DA (referentiel de la Capitale) : au-dessus des trois ordres, un mur
    a pilastres perce de fenetres carrees, ses corbeaux et ses mats de velum. Au nord seulement :
    cote camera il cacherait le sable."""
    bays=42
    for j in range(bays):
        a=(j+.5)*math.tau/bays
        if math.sin(a)<.16:continue
        x=24.0*math.cos(a);y=16.9*math.sin(a)
        tangent=math.atan2(16.9*math.cos(a),-24.0*math.sin(a))+math.pi
        width=math.hypot(24.0*math.sin(a),16.9*math.cos(a))*math.tau/bays+.06
        def bay(w=width):
            b.masonry(w,3.9,.72,1)
            for side in [-1,1]:
                box(side*(w/2-.22),-.40,.14,.44,.16,3.5,0)
                box(side*(w/2-.22),-.42,3.42,.56,.22,.22,0)
            # La fenetre carree, son encadrement de marbre et son volet de bronze.
            box(0,-.37,1.55,1.06,.10,1.06,0);box(0,-.41,1.68,.78,.06,.80,8)
            for z,d,h in [(3.9,.96,.16),(4.06,1.12,.16),(4.22,.98,.20)]:box(0,-.04,z,w,d,h,0)
            # Le corbeau et le mat : le velum s'y tend les jours de grande audience.
            box(0,-.52,2.95,.30,.36,.30,0)
            rod((0,-.56,3.1),(0,-.56,8.2),.075,8,10)
            lathe(0,-.56,8.2,[(.10,0),(.15,.12),(.05,.34)],8,10)
            face([(0,-.56,7.9),(1.25,-.56,7.55),(0,-.56,7.2)],7)
        transform(bay,x=x,y=y,z=9.0,angle=tangent)

def shell():
    # Preserve the approved oval and two existing long-axis passages.
    oldloge=b.loge;b.loge=lambda:None
    b.arena_shell();b.loge=oldloge
    # The new axial entry must be a real opening through the old seating ring.
    # Remove the central strip, then close both cut edges with masonry jambs.
    kept=[];colors=[]
    for ids,c in zip(b.F,b.C):
        points=[b.V[i] for i in ids]
        center=[sum(p[j] for p in points)/len(points) for j in range(3)]
        if abs(center[0])<2.8 and center[1]<-9.8 and center[2]<6.60:continue
        kept.append(ids);colors.append(c)
    b.F=kept;b.C=colors
    for x in [-2.98,2.98]:
        for row in range(8):box(x,-13.45,row*.4,.42,6.2,.383,1)
        box(x,-13.45,3.17,.54,6.22,.18,0)
    for degrees in [20,42,64,90,110,130,150,170,194,212,230,310,330]:
        a=math.radians(degrees);x=23.1*math.cos(a);y=16*math.sin(a)
        tangent=math.atan2(16*math.cos(a),-23.1*math.sin(a))+math.pi
        transform(lambda d=degrees:loge(d==90,d>180),x=x,y=y,z=6 if degrees<180 else 5.25,angle=tangent)
    transform(gateway,y=-15.8)
    attic()
    contract=json.loads((WORK/'arena-layout-contract.json').read_text(encoding='utf-8-sig'))
    support_file=WORK/'Sculptures/sculptures-supports.json'
    support_sizes={tuple(p['at']):p['sizeMetres'] for p in json.loads(support_file.read_text(encoding='utf-8-sig'))['supports']} if support_file.exists() else {}
    for reservation in contract['statueReservations']:
        col,row=reservation['at'];x=(col+.5)*1.5-25.5;y=18-(row+.5)*1.5
        sw,sd=support_sizes.get((col,row),(1.20,1.20))
        box(x,y,3,1.28,1.28,.16,0)
        box(x,y,3.16,1.10,1.10,.12,0)
        box(x,y,3.28,.94,.94,.44,0)
        box(x,y,3.72,sw-.10,sd-.10,.10,0)
        box(x,y,3.82,sw,sd,.12,0)
    for group in contract['groups']:
        banners=[(entry,False) for entry in group['regions']]
        if group.get('commonBanner'):banners.append((group['commonBanner'],True))
        for entry,alliance in banners:
            col,row=entry['at'];fp=entry['footprint']
            x=(col+fp[0]/2)*1.5-25.5;y=18-(row+.5)*1.5+.08
            base=6 if y>0 else 3
            height=4.05 if alliance else 3.8 if entry['piece']=='banner-empire' else 3.3
            top=entry['floor']*3+height+.14
            box(x,y,base,.32,.32,.18,0)
            rod((x,y,base+.18),(x,y,top),.055,8,12)
            lathe(x,y,top,[(.07,0),(.11,.09),(.035,.23)],8,12)

def make_atlas(output):
    names=['limestone','marble','sand','velvet','bronze']
    size=1024;pix=np.ones((size*2,size*3,4),dtype=np.float32)
    for i,name in enumerate(names):
        im=bpy.data.images.load(str(WORK/'Textures'/f'{name}-albedo.png'),check_existing=True);im.scale(size,size)
        buf=np.empty(size*size*4,dtype=np.float32);im.pixels.foreach_get(buf)
        pix[(i//3)*size:(i//3+1)*size,(i%3)*size:(i%3+1)*size,:]=buf.reshape(size,size,4)
    img=bpy.data.images.new('colosseum-real-material-atlas',size*3,size*2,alpha=True)
    img.pixels.foreach_set(pix.reshape(-1));img.filepath_raw=str(output/'material-atlas.png');img.file_format='PNG';img.save();img.pack()
    return material(img,'colosseum-stone-marble-textile')

def material(img,name,alpha=False):
    mat=bpy.data.materials.new(name);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.78
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=img
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    if alpha:
        mat.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        mat.surface_render_method='DITHERED';mat.use_backface_culling=False
    return mat

def export(asset,fp,build,out,mat,kind='tall',bevel=.014,crowd=False):
    b.V=[];b.F=[];b.C=[];UV.clear();build()
    mesh=bpy.data.meshes.new(asset);mesh.from_pydata(b.V,[],b.F);mesh.update()
    obj=bpy.data.objects.new(asset,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='material-surface-UV')
    for index,(poly,c) in enumerate(zip(mesh.polygons,b.C)):
        if crowd:
            for li,p in zip(poly.loop_indices,UV[index]):uv.data[li].uv=p
            continue
        slot=2 if asset.startswith('af-sand-') else (1 if c==0 else 3 if c==7 else 4 if c in [6,8,12] else 0)
        normal=poly.normal;axis=max(range(3),key=lambda j:abs(normal[j]));axes=[j for j in range(3) if j!=axis]
        coords=[mesh.vertices[mesh.loops[li].vertex_index].co for li in poly.loop_indices]
        mins=[min(p[j] for p in coords) for j in axes];maxs=[max(p[j] for p in coords) for j in axes]
        scale=max(1.5 if slot==2 else 3.5 if slot in [1,3,4] else 5.0,max(maxs[j]-mins[j] for j in range(2))*1.05)
        # Physical surface projection per face. Offset selection changes stone
        # grain without distorting texel scale; gutters protect atlas neighbours.
        rng=random.Random(index*13+71);offset=[rng.random()*(1-(maxs[j]-mins[j])/scale) for j in range(2)]
        if slot==2:offset=[0,0]
        for li,p in zip(poly.loop_indices,coords):
            values=[.003+.994*((p[axes[j]]-mins[j])/scale+offset[j]) for j in range(2)]
            if slot==2:
                u=(p.x+.75)/1.5;v=(p.y+.75)/1.5
                uv.data[li].uv=(u,v)
            else:uv.data[li].uv=((slot%3+values[0])/3,(slot//3+values[1])/2)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    if bevel:
        bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(mesh);bm.free()
        mod=obj.modifiers.new('physical-edge-mouldings','BEVEL');mod.width=bevel;mod.segments=1;mod.limit_method='ANGLE';mod.angle_limit=1.2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    tri=obj.modifiers.new('triangulated','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=tri.name)
    path=out/(asset+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_animations=False,export_cameras=False,export_lights=False)
    data=path.read_bytes();ln=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+ln])
    assert len(g['meshes'])==len(g['materials'])==len(g['meshes'][0]['primitives'])==1
    prim=g['meshes'][0]['primitives'][0];assert {'POSITION','NORMAL','TEXCOORD_0'}<=set(prim['attributes'])
    assert g['images'][0].get('bufferView') is not None
    if crowd:assert g['materials'][0].get('alphaMode') in ['BLEND','MASK']
    bounds=[[min(p[j] for p in b.V) for j in range(3)],[max(p[j] for p in b.V) for j in range(3)]]
    measure={'id':asset,'triangles':g['accessors'][prim['indices']]['count']//3,'bytes':len(data),'boundsBlender':bounds,'footprint':fp,'materialAtlas':not asset.startswith('af-sand-')}
    bpy.data.objects.remove(obj,do_unlink=True)
    print('PRODUCED',json.dumps(measure),flush=True)
    return {'mesh':asset+'.glb','class':kind,'footprint':fp,'tactical':'open' if kind in ['floor','wide'] else 'solid'},measure

def crowd_material(out):
    w=2172;h=724;pix=np.zeros((h*2,w,4),dtype=np.float32)
    for j,name in enumerate(['crowd-seated-a-clean.png','crowd-seated-b-rear-clean.png']):
        im=bpy.data.images.load(str(WORK/'Textures'/name));im.scale(w,h)
        buf=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(buf);pix[j*h:(j+1)*h]=buf.reshape(h,w,4)
    im=bpy.data.images.new('crowd-front-and-rear',w,h*2,alpha=True);im.pixels.foreach_set(pix.reshape(-1));im.filepath_raw=str(out/'crowd-atlas.png');im.file_format='PNG';im.save();im.pack()
    return material(im,'crowd-alpha-cutouts',True)

def crowds():
    rng=random.Random(2306)
    for row in range(9):
        rx=17.6+row*.61;ry=11.6+row*.61;z=row*.34+.14
        count=85+row*3
        for i in range(count):
            a=(i+.5+rng.uniform(-.13,.13))*math.tau/count
            # radial stair aisles, two gates, monumental portal.
            if abs(math.sin(a))<.17 or 250<math.degrees(a)<290:continue
            if abs(((a+math.pi/24)%(math.pi/6))-math.pi/24)<.035:continue
            x=rx*math.cos(a);y=ry*math.sin(a)
            # Fixed orthographic camera: each small cutout faces the camera,
            # while centres remain on the physical elliptical seating rows.
            dx=.52/math.sqrt(2);dy=.52/math.sqrt(2)
            height=1.2+rng.uniform(-.06,.04);k=rng.randrange(0,9)
            u0=k/10;u1=(k+2)/10
            if rng.random()<.45:u0,u1=u1,u0
            half=0 if y>0 else .5
            # Native atlas has transparent top/bottom margins. Crop those UV
            # margins so displayed seated bodies retain 1.2m actual height.
            up=(-.62*height/math.sqrt(2),.62*height/math.sqrt(2),math.sqrt(1-.62**2)*height)
            face([(x-dx,y-dy,z),(x+dx,y+dy,z),(x+dx+up[0],y+dy+up[1],z+up[2]),(x-dx+up[0],y-dy+up[1],z+up[2])],0)
            UV.append([(u0,half+.075),(u1,half+.075),(u1,half+.44),(u0,half+.44)])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--only',default='');args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=WORK/'Architecture';out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    mat=make_atlas(out)
    sandmat=material(bpy.data.images.load(str(WORK/'Textures/sand-albedo.png'),check_existing=True),'sand-dedicated-repeat')
    jobs=[('af-arena-shell',[34,24],shell,'wide',.014)]
    for kind in ['sand','paving']:
        for n in range(3):jobs.append(('af-'+kind+'-'+chr(97+n),[1,1],lambda k=kind,n=n:b.floor(k,n),'floor',0))
    for name,fp,fn in [('loge',[3,2],loge),('balustrade',[2,1],b.balustrade),('column',[1,1],lambda:column(0,0,3.9,0,2))]:jobs.append(('af-'+name,fp,fn,'tall',.014))
    textures={};measures=[]
    if args.only and (out/'architecture-manifest.json').exists():
        textures=json.loads((out/'architecture-manifest.json').read_text())['textures'];measures=json.loads((out/'architecture-measurements.json').read_text())
    for asset,fp,fn,kind,bevel in jobs:
        if args.only and asset not in args.only.split(','):continue
        entry,measurement=export(asset,fp,fn,out,sandmat if asset.startswith('af-sand-') else mat,kind,bevel);textures['scene/arena-of-fate/'+asset]=entry;measures=[m for m in measures if m['id']!=asset]+[measurement]
    if not args.only or 'af-arena-crowd' in args.only.split(','):
        entry,measurement=export('af-arena-crowd',[34,24],crowds,out,crowd_material(out),'wide',0,True)
        textures['scene/arena-of-fate/af-arena-crowd']=entry;measures=[m for m in measures if m['id']!='af-arena-crowd']+[measurement]
    (out/'architecture-manifest.json').write_text(json.dumps({'version':1,'tile':[256,159],'storey':283.742841317,'textures':textures},indent=2),encoding='utf8')
    (out/'architecture-measurements.json').write_text(json.dumps(measures,indent=2),encoding='utf8')
    (out/'production-contract.json').write_text(json.dumps({'scope':'Colosseum only; no installation','localGeometry':['oval masonry','three classical orders','fluted columns','mouldings','nine seating rows','13 loges','Imperial loge at 90 degrees','triumphal gateway at 270 degrees','two empty guardian plinths','balustrades','sand and paving'],'MeshyRequired':['14 deity sculptures; parent/iconography owns source images','two guardian lions on portal towers'],'MeshyOptional':['figurative narrative reliefs or masks if added; no procedural substitutes'],'portalLionReservationsBlender':[[-4.65,-15.8,7.69],[4.65,-15.8,7.69]],'crowd':{'piece':'af-arena-crowd','at':[0,0],'footprint':[34,24],'floor':1,'heightOffsetMetres':3,'method':'hundreds of discrete two-person alpha cutouts on exact seat rows; no panorama'}},indent=2),encoding='utf8')

if __name__=='__main__':main()
