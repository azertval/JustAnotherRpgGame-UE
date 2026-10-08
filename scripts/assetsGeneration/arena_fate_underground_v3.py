#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Replay underground architecture V3; never writes Scene or Levels.

Blender --background --factory-startup --threads 2 --python-exit-code 1
 --python scripts/assetsGeneration/arena_fate_underground_v3.py
Texture colour adjustments below are deterministic material palette choices,
not baked lighting. All grooves, mouldings, boards and arch stones are geometry.
"""
import argparse
import importlib.util
import json
import math
import random
import struct
import sys
import hashlib
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
PROD=ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production'
OUT=PROD/'V3/Architecture'
spec=importlib.util.spec_from_file_location('arena_v2',Path(__file__).with_name('arena_fate_architecture_v2.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
b=v.b
box=b.box;face=b.face;lathe=b.lathe;rod=b.rod;transform=b.transformed
STONE,MARBLE,CAT,WOOD,BRONZE,IRON,CLOTH,WATER,FIRE,EMBER,STRAW,JOINT=range(12)

def arch(x,y,z,ri,ro,depth,c,n=18):
    start=len(b.C);b.arch(x,y,z,ri,ro,depth,c,n)
    for i in range(start,len(b.C)):b.C[i]=c

def legacy(fn):
    start=len(b.C);fn()
    convert={0:MARBLE,1:STONE,2:STONE,3:STONE,4:CAT,5:CAT,6:BRONZE,7:EMBER,8:FIRE,9:WATER,10:IRON,11:CAT,12:STRAW,13:WOOD,14:MARBLE,15:CLOTH}
    for j in range(start,len(b.C)):b.C[j]=convert.get(b.C[j],CAT)

def cornice(width,depth,z,c=MARBLE):
    for dz,w,d,h in [(0,width-.06,depth-.04,.075),(.075,width,depth,.07),(.145,width-.025,depth-.02,.085)]:box(0,0,z+dz,w,d,h,c)

def wall(w=1.5,h=3,cat=False):
    c=CAT if cat else STONE;d=.55
    box(0,0,0,w,d-.025,h-.10,JOINT)
    rows=round((h-.30)/.38);dh=(h-.30)/rows
    for row in range(rows):
        cuts=sorted(set([-w/2,w/2]+[max(-w/2,min(w/2,-w/2+j*.75+(row%2)*.375)) for j in range(math.ceil(w/.75)+1)]))
        for a,bb in zip(cuts,cuts[1:]):
            if bb-a>.03:box((a+bb)/2,0,.12+row*dh,bb-a-.014,d,dh-.012,c)
    box(0,0,0,w,d+.10,.14,c)
    cornice(w,.71,h-.23,c if cat else MARBLE)
    if h>2:
        for z in [.22,2.43]:box(0,-.288,z,w,.085,.07,c if cat else MARBLE)

def wall_corner(cat=False):
    # NE room corner: centre-line junction with arms towards west and south.
    # Horizontal arm includes the joint; vertical arm terminates at its edge.
    c=CAT if cat else STONE
    for j in range(8):
        box(-.2375,0,j*.375,1.025,.55,.36,c)
        box(0,-.5125,j*.375,.55,.475,.36,c)
    for z,h in [(0,.12),(2.78,.10),(2.88,.12)]:
        box(-.1975,0,z,1.105,.71,h,c)
        box(0,-.5525,z,.71,.395,h,c)

def oriented_corner(cat=False,angle=0,low=False):
    start=len(b.V);transform(lambda:wall_corner(cat),angle=angle)
    if low:
        for i in range(start,len(b.V)):
            x,y,z=b.V[i];b.V[i]=(x,y,z*.4)

def floor(cat=False,variant=0):
    box(0,0,0,1.5,1.5,.055,JOINT)
    for row in range(3):
        for col in range(3):
            # Identical boundary phase in all three variants, no rotated UVs.
            z=.055+.002*((row+col+variant)%3)
            box(-.5+col*.5,-.5+row*.5,z,.488,.488,.055,CAT if cat else STONE)

def pillar(x,y,h=3,c=STONE):
    box(x,y,0,.66,.66,.16,c);box(x,y,.16,.55,.55,.13,c)
    for j in range(max(1,round((h-.6)/.4))):
        n=round((h-.6)/.4);box(x,y,.29+j*(h-.6)/n,.46,.46,(h-.6)/n-.012,c)
    transform(lambda:cornice(.70,.70,h-.31,c),x=x,y=y)
    box(x,y,h-.08,.66,.66,.08,c)

def room_arch(cat=False):
    c=CAT if cat else MARBLE
    for x in [-1.15,1.15]:pillar(x,0,1.90,c)
    arch(0,0,1.90,.94,1.26,.57,c,19)
    # Outer raised archivolt and projecting keystone.
    arch(0,-.30,1.90,1.265,1.31,.07,c,21)
    box(0,-.04,2.97,.26,.72,.26,c)
    transform(lambda:cornice(3,.68,3.17,c))

def open_vault(cat=False):
    c=CAT if cat else STONE
    for y in [-1.88,1.88]:
        for x in [-1.88,1.88]:pillar(x,y,2.35,c)
        arch(0,y,2.35,1.64,1.95,.28,c,23)
    # Open ribs define the vault, never a roof hiding furniture.
    for x in [-1.91,1.91]:box(x,0,2.25,.22,4.10,.20,c)
    rod((0,-1.92,4.22),(0,1.92,4.22),.07,c,10)

def niche(cat=False):
    c=CAT if cat else MARBLE
    box(0,0,0,1.48,1.45,.12,c);box(0,0,.12,1.36,1.30,.13,c)
    box(0,.665,.25,1.44,.16,2.58,CAT if cat else STONE)
    for x in [-.66,.66]:
        box(x,.36,.25,.14,.60,2.23,c)
        box(x,.34,2.43,.18,.66,.12,c)
    arch(0,.37,2.43,.57,.71,.59,c,17)
    arch(0,.055,2.43,.57,.60,.05,c,17)
    box(0,.34,3.13,1.48,.74,.13,c)

def plinth():
    # Flat full-width top accommodates the quadruped without compressing it.
    box(0,0,0,4.5,4.5,.15,CAT)
    box(0,0,.15,4.44,4.44,.16,CAT)
    box(0,0,.31,4.48,4.48,.14,MARBLE)
    for axis in [0,1]:
        for sign in [-1,1]:
            transform(lambda sign=sign:box(0,sign*2.18,.19,4.25,.04,.06,BRONZE),angle=axis*math.pi/2)

def chapel_frame():
    for x in [-3.22,3.22]:
        pillar(x,0,3.0,CAT)
        box(x,0,3,.64,.68,2.65,CAT)
        transform(lambda:cornice(.86,.86,5.65,CAT),x=x)
        for z in [.45,1.8,3.0,4.4]:box(x,-.36,z,.54,.14,.14,MARBLE)
    arch(0,.02,2.55,2.89,3.18,.48,CAT,31)
    arch(0,-.255,2.55,2.89,2.94,.06,MARBLE,31)
    box(0,-.05,5.52,.34,.66,.31,MARBLE)

def ossuary_frame():
    box(0,0,0,2.96,1.49,.18,CAT);box(0,0,.18,2.84,1.45,.14,CAT);box(0,0,.32,2.96,1.49,.13,MARBLE)
    for x in [-1.35,1.35]:
        box(x,.04,.45,.20,1.30,1.53,CAT)
        box(x,-.64,.50,.22,.10,1.37,MARBLE)
    box(0,.68,.45,2.8,.12,1.53,CAT)
    transform(lambda:cornice(2.99,1.49,1.98,CAT))

def fountain():
    box(0,.555,0,2.86,.37,2.67,STONE)
    for x in [-1.14,1.14]:pillar(x,.26,2.43,MARBLE)
    arch(0,.35,1.95,.80,1.09,.26,MARBLE,23)
    transform(lambda:cornice(2.96,.55,2.90,MARBLE),y=.45)
    # Elliptical basin in front; mask back reaches y+.37, board begins+.435.
    start=len(b.V)
    lathe(0,0,0,[(.72,0),(.76,.12),(.53,.23),(.64,.40),(.96,.60),(1.00,.72),(.92,.78),(.84,.69),(.70,.39)],MARBLE,40)
    for j in range(start,len(b.V)):
        x,y,z=b.V[j];b.V[j]=(x,y*.31-.42,z)
    face([(.82*math.cos(j*math.tau/40),-.42+.25*math.sin(j*math.tau/40),.64) for j in range(40)],WATER)
    rod((0,-.40,.85),(0,-.42,.65),.022,WATER)

def bench():
    legacy(b.bench)
    for x in [-1.05,1.05]:
        for y in [-.24,.24]:lathe(x,y,.647,[(.025,0),(.025,.012)],IRON,8)
    box(0,.36,.40,2.8,.12,.58,WOOD)
    for x in [-1.22,1.22]:box(x,.36,.13,.12,.14,.93,WOOD)

def bars():
    legacy(b.bars)
    for x in [-1.4+i*.2 for i in range(15)]:
        for z in [.24,1.54,2.74]:box(x,-.085,z,.075,.045,.075,IRON)
    for x in [-1.44,1.44]:
        box(x,0,0,.12,.36,.17,IRON);box(x,0,2.83,.12,.36,.17,IRON)

def altar():
    for z,w,d,h in [(0,2.95,1.45,.14),(.14,2.68,1.2,.14),(.99,2.84,1.32,.14),(1.13,3,1.48,.14)]:box(0,0,z,w,d,h,CAT)
    for x in [-1.08,1.08]:pillar(x,0,1.02,CAT)
    box(0,0,.28,1.80,.72,.65,CAT)
    box(0,-.377,.40,1.55,.055,.38,CLOTH)
    for x in [-.8,.8]:rod((x,-.414,.38),(x,-.414,.80),.022,BRONZE)
    for x in [-1.1,1.1]:lathe(x,0,1.27,[(.10,0),(.07,.08),(.08,.17)],BRONZE,16)

def torch_wall(cat=False):
    wall(cat=cat)
    start=len(b.V);legacy(b.torch)
    for j in range(start,len(b.V)):
        x,y,z=b.V[j];b.V[j]=(x,y*.68-.53,z)

def prison_door():
    room_arch()
    for i in range(9):box(-.8+i*.2,0,0,.18,.12,2.25,WOOD)
    for z in [.24,1.22,2.12]:box(0,-.083,z,1.88,.06,.10,IRON)
    for x in [-.73,.73]:
        for z in [.28,1.26,2.16]:lathe(x,-.1,z,[(.032,0),(.032,.035)],IRON,8)
    legacy(lambda:b.torus(.5,-.135,1.12,.09,.022,6,True))

RING_ANCHORS={
    'cthraxis':[[-1.059,-.514,3.368],[.967,-.519,3.368]],
    'krynnethoth':[[-1.375,-.377,3.145],[1.125,-.242,3.327]],
    'droggath':[[-1.537,-.764,1.021],[.505,-1.153,1.021]],
    'zulvath':[[-.327,-.953,1.701],[.308,-.952,1.701]],
}
def chain_link(center,tangent,twist):
    tangent=Vector(tangent).normalized();side=tangent.cross(Vector((0,0,1)))
    if side.length<.01:side=Vector((1,0,0))
    side.normalize();up=tangent.cross(side).normalized()
    q=side*math.cos(twist)+up*math.sin(twist);normal=tangent.cross(q)
    center=Vector(center)
    def p(a,t):
        radial=tangent*math.cos(a)+q*math.sin(a)
        return center+tangent*(.099*math.cos(a))+q*(.062*math.sin(a))+(radial*math.cos(t)+normal*math.sin(t))*.017
    for i in range(16):
        for j in range(6):face([p(i*math.tau/16,j*math.tau/6),p((i+1)*math.tau/16,j*math.tau/6),p((i+1)*math.tau/16,(j+1)*math.tau/6),p(i*math.tau/16,(j+1)*math.tau/6)],BRONZE)

def effigy_chains(slug):
    for sign,target in zip([-1,1],RING_ANCHORS[slug]):
        x=sign*3.1;y=.35;h=3.0 if slug in ['cthraxis','krynnethoth'] else 2.35
        pillar(x,y,h,CAT)
        start=Vector((x,-.02,h-.38));end=Vector(target)
        box(x,-.01,h-.53,.20,.16,.32,IRON)
        steps=max(2,round((end-start).length/.13))
        def pos(t,start=start,end=end):return start.lerp(end,t)+Vector((0,0,-.30*math.sin(math.pi*t)))
        for j in range(steps+1):
            t=j/steps;tangent=pos(min(1,t+.01))-pos(max(0,t-.01))
            chain_link(pos(t),tangent,j%2*math.pi/2)

def mat_atlas():
    size=512;pixels=np.ones((size*3,size*4,4),dtype=np.float32)
    # These colour factors define material families, never directional shading.
    recipes=[('limestone',[1,1,1]),('marble',[1,1,1]),('limestone',[.68,.70,.72]),('oak',[1,1,1]),('bronze',[1,1,1]),('bronze',[.32,.37,.43]),('velvet',[.48,.75,1.35]),(None,[.16,.38,.40]),(None,[1,.64,.15]),(None,[.96,.26,.045]),('oak',[1.22,1.25,1.08]),('limestone',[.57,.60,.62])]
    for i,(name,factor) in enumerate(recipes):
        if name:
            path=PROD/('V3/Textures/oak-albedo.png' if name=='oak' else f'V2/Textures/{name}-albedo.png')
            im=bpy.data.images.load(str(path),check_existing=False);im.scale(size,size)
            buf=np.empty(size*size*4,dtype=np.float32);im.pixels.foreach_get(buf);buf=buf.reshape(size,size,4);buf[:,:,:3]*=np.array(factor);buf=np.clip(buf,0,1)
        else:
            buf=np.ones((size,size,4),dtype=np.float32);buf[:,:,:3]=factor
        pixels[(i//4)*size:(i//4+1)*size,(i%4)*size:(i%4+1)*size]=buf
    im=bpy.data.images.new('underground-material-atlas',size*4,size*3,alpha=True);im.pixels.foreach_set(pixels.reshape(-1));im.filepath_raw=str(OUT/'material-atlas.png');im.file_format='PNG';im.save();im.pack()
    return v.material(im,'underground-rich-basecolour-only')

def export(asset,fp,build,mat,kind='tall',bevel=.012):
    b.V=[];b.F=[];b.C=[];build()
    mesh=bpy.data.meshes.new(asset);mesh.from_pydata(b.V,[],b.F);mesh.update()
    obj=bpy.data.objects.new(asset,mesh);bpy.context.collection.objects.link(obj);mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='physical-surface-projection')
    for idx,(poly,slot) in enumerate(zip(mesh.polygons,b.C)):
        axis=max(range(3),key=lambda j:abs(poly.normal[j]));axes=[j for j in range(3) if j!=axis]
        coords=[mesh.vertices[mesh.loops[li].vertex_index].co for li in poly.loop_indices]
        lo=[min(p[j] for p in coords) for j in axes];hi=[max(p[j] for p in coords) for j in axes]
        scale=max(3.0,max(hi[j]-lo[j] for j in range(2))*1.03)
        rng=random.Random(371+idx*7);offset=[rng.random()*(1-(hi[j]-lo[j])/scale) for j in range(2)]
        for li,p in zip(poly.loop_indices,coords):
            q=[.006+.988*((p[axes[j]]-lo[j])/scale+offset[j]) for j in range(2)]
            uv.data[li].uv=((slot%4+q[0])/4,(slot//4+q[1])/3)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(mesh);bm.free()
    if bevel:
        mod=obj.modifiers.new('real-edge-bevel','BEVEL');mod.width=bevel;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.7;bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=obj.modifiers.new('indexed-triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=mod.name)
    points=[p.co for p in obj.data.vertices];bounds=[[min(p[j] for p in points) for j in range(3)],[max(p[j] for p in points) for j in range(3)]]
    assert bounds[0][0]>=-fp[0]*.75-.002 and bounds[1][0]<=fp[0]*.75+.002,(asset,bounds,fp)
    assert bounds[0][1]>=-fp[1]*.75-.002 and bounds[1][1]<=fp[1]*.75+.002,(asset,bounds,fp)
    path=OUT/(asset+'.glb');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_animations=False,export_cameras=False,export_lights=False)
    data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+length]);pr=g['meshes'][0]['primitives'][0]
    assert len(g['meshes'])==len(g['materials'])==len(g['meshes'][0]['primitives'])==1
    assert {'POSITION','NORMAL','TEXCOORD_0'}<=set(pr['attributes']) and g['images'][0].get('bufferView') is not None
    entry={'mesh':asset+'.glb','class':kind,'footprint':fp,'tactical':'open' if kind=='floor' or 'arch-' in asset or 'vault' in asset else 'solid'}
    if 'torch' in asset or asset=='af-brazier':
        entry['light']={'color':'#ffbd72','radius':6.5,'height':2.2 if 'torch' in asset else 1.2,'flicker':True,'always':True};entry['glow']=.4
    m={'id':asset,'triangles':g['accessors'][pr['indices']]['count']//3,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'boundsBlender':bounds,'footprint':fp,'basecolorPixels':[2048,1536]}
    bpy.data.objects.remove(obj,do_unlink=True);print('PRODUCED',asset,m['triangles'],flush=True)
    return entry,m

def main():
    p=argparse.ArgumentParser();p.add_argument('--only',default='');args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    OUT.mkdir(parents=True,exist_ok=True);bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);mat=mat_atlas()
    jobs=[]
    for cat in [False,True]:
        for i in range(3):jobs.append(('af-'+('cat-floor-' if cat else 'v3-paving-')+chr(97+i),[1,1],lambda c=cat,i=i:floor(c,i),'floor',.008))
        fam='catacomb' if cat else 'stone'
        for axis in ['x','y']:
            angle=math.pi/2 if axis=='y' else 0
            for low in [False,True]:jobs.append(('af-wall-'+fam+'-'+axis+('-low' if low else ''),[1,1],lambda c=cat,l=low,a=angle:transform(lambda:wall(h=1.2 if l else 3,cat=c),angle=a),'tall',.014))
            jobs.append(('af-wall-torch-'+fam+'-'+axis,[1,1],lambda c=cat,a=angle:transform(lambda:torch_wall(c),angle=a),'tall',.012))
            jobs.append(('af-arch-'+fam+'-'+axis,[1,2] if axis=='y' else [2,1],lambda c=cat,a=angle:transform(lambda:room_arch(c),angle=a),'tall',.013))
        for direction,angle in [('',0),('-nw',math.pi/2),('-sw',math.pi),('-se',3*math.pi/2)]:
            for low in [False,True]:jobs.append(('af-wall-'+fam+'-corner'+direction+('-low' if low else ''),[1,1],lambda c=cat,a=angle,l=low:oriented_corner(c,a,l),'tall',0))
        jobs.append(('af-statue-niche-'+fam,[1,1],lambda c=cat:niche(c),'tall',.012))
    for name,fp,fn in [('vault',[3,3],open_vault),('vault-catacomb',[3,3],lambda:open_vault(True)),('chapel-frame',[5,1],chapel_frame),('effigy-plinth',[3,3],plinth),('ossuary-frame',[2,1],ossuary_frame),('fountain-body',[2,1],fountain),('bench',[2,1],bench),('prison-bars',[2,1],bars),('altar',[2,1],altar),('prison-door',[2,1],prison_door),('column',[1,1],lambda:legacy(lambda:v.column(0,0,3.6,0,0)))]:jobs.append(('af-'+name,fp,fn,'tall',.012))
    for name,fp,fn in [('stair',[2,3],b.stair),('rack',[2,1],b.rack),('brazier',[1,1],b.brazier),('chains',[1,1],b.chains),('pallet',[2,1],b.pallet),('barrel',[1,1],b.barrel),('bucket',[1,1],b.bucket),('chest',[1,1],b.chest),('guard-table',[2,1],b.guard_table)]:jobs.append(('af-'+name,fp,lambda f=fn:legacy(f),'tall',.008))
    for slug in RING_ANCHORS:jobs.append(('af-effigy-chains-'+slug,[5,3],lambda s=slug:effigy_chains(s),'tall',0))
    textures={};measures=[]
    if args.only and (OUT/'architecture-manifest.json').exists():
        textures=json.loads((OUT/'architecture-manifest.json').read_text())['textures'];measures=json.loads((OUT/'architecture-measurements.json').read_text())
    for name,fp,fn,kind,bevel in jobs:
        if args.only and name not in args.only.split(','):continue
        entry,m=export(name,fp,fn,mat,kind,bevel);textures['scene/arena-of-fate/'+name]=entry;measures=[a for a in measures if a['id']!=name]+[m]
    (OUT/'architecture-manifest.json').write_text(json.dumps({'version':1,'tile':[256,159],'storey':283.742841317,'textures':textures},indent=2),encoding='utf8')
    (OUT/'architecture-measurements.json').write_text(json.dumps(measures,indent=2),encoding='utf8')
    (OUT/'replacement-contract.json').write_text(json.dumps({'mapScope':['undercroft','catacombs'],'preserve':'Colosseum and its installed GLBs','rename':{f'af-paving-{c}':f'af-v3-paving-{c}' for c in 'abc'},'retiredSculpturalArchitecture':['af-ossuary','af-fountain'],'supportTopMetres':{'af-effigy-plinth':.45,'af-statue-niche-stone':.25,'af-statue-niche-catacomb':.25,'af-ossuary-frame':.45},'lighting':'LOT1007 manifest lights; no lighting painted into albedo','normativeBudget':None},indent=2),encoding='utf8')
    print('FINISHED',len(measures),'assets',sum(m['triangles'] for m in measures),'triangles',flush=True)

if __name__=='__main__':main()
