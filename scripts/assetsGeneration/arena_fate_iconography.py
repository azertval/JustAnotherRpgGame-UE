"""Rebuild the retained Arena of Fate banners with Blender; no hand-edited meshes.

Run: blender -b --python scripts/assetsGeneration/arena_fate_iconography.py -- --root PATH
Albedos: original imagegen illustrations, prompts retained in Production/Iconography.
Gods and Ungods now use author-supplied Meshy GLBs via the dedicated import scripts.
Procedural sculptures are retired; the previous generator is retained in the
Production/Archive/2026-10-04-procedural-effigies workshop snapshot.
"""
import argparse
import math
import json
import sys
import struct
from pathlib import Path
import bpy
from mathutils import Vector

P=argparse.ArgumentParser(); P.add_argument('--root',type=Path,required=True); P.add_argument('--only',choices=['all','banners'],default='all'); A=P.parse_args(sys.argv[sys.argv.index('--')+1:])
OUT=A.root/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/Iconography'
OUT.mkdir(parents=True,exist_ok=True)
PARTS=[]; MAT=None; SWATCH=True; RECORDS={}
COLORS=['efe6d2','d9c7a3','b6aa96','c9a45c','5c4a2a','514d53','8e8292','312d3d','8d70b0','bdac7d','e4dbb7','8c9ea5','734e52','554934','9d895c','ffffff']
LABELS={}

def reset(texture=None):
    global PARTS,MAT,SWATCH
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False); PARTS=[]
    MAT=bpy.data.materials.new('single-basecolor'); MAT.use_nodes=True; bs=MAT.node_tree.nodes.get('Principled BSDF'); bs.inputs['Roughness'].default_value=1; bs.inputs['Metallic'].default_value=0
    bs.inputs['Specular IOR Level'].default_value=0
    tex=MAT.node_tree.nodes.new('ShaderNodeTexImage')
    if texture: img=bpy.data.images.load(str(texture),check_existing=True); SWATCH=False
    else:
        SWATCH=True; img=bpy.data.images.get('stone-palette')
        if not img:
            img=bpy.data.images.new('stone-palette',width=64,height=4,alpha=True)
            pix=[]
            for _ in range(4):
                for x in range(64):
                    c=COLORS[x//4]; pix.extend([int(c[i:i+2],16)/255 for i in (0,2,4)]+[1])
            img.pixels=pix; img.file_format='PNG'; img.filepath_raw=str(OUT/'stone-palette.png'); img.save()
    tex.image=img; MAT.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])

def adopt(o,c=0):
    o['palette_index']=c
    o.data.materials.clear(); o.data.materials.append(MAT)
    if not o.data.uv_layers: o.data.uv_layers.new(name='UVMap')
    for l in o.data.uv_layers.active.data: l.uv=((c+.5)/16,.5) if SWATCH else (.015,.985)
    PARTS.append(o); return o

def ell(p,s,c=0,seg=24,rings=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=p); o=bpy.context.object; o.scale=s; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for f in o.data.polygons:f.use_smooth=True
    return adopt(o,c)

def cone(p,r1,r2,h,c=0,n=32):
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r1,radius2=r2,depth=h,location=p); return adopt(bpy.context.object,c)

def rod(a,b,r,c=0,r2=None):
    a,b=Vector(a),Vector(b); o=cone((a+b)/2,r,r if r2 is None else r2,(b-a).length,c,24); o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    for f in o.data.polygons:f.use_smooth=True
    return o

def mesh(name,verts,faces,c=0,smooth=False):
    m=bpy.data.meshes.new(name); m.from_pydata(verts,[],faces);m.update();o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);adopt(o,c)
    for p in m.polygons:p.use_smooth=smooth
    return o

def export(key,fp,label):
    bpy.ops.object.select_all(action='DESELECT')
    for o in PARTS:o.select_set(True)
    bpy.context.view_layer.objects.active=PARTS[0];bpy.ops.object.convert(target='MESH');bpy.ops.object.join();o=bpy.context.object
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    # Collapse all material slots to one and triangulate deterministically.
    o.data.materials.clear();o.data.materials.append(MAT)
    for f in o.data.polygons:f.material_index=0
    m=o.modifiers.new('triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=m.name)
    o.name=key;path=OUT/(key+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
    verts=[o.matrix_world@v.co for v in o.data.vertices]
    bounds=[[round(min(v[i] for v in verts),4),round(max(v[i] for v in verts),4)] for i in range(3)]
    raw=path.read_bytes();gltf=json.loads(raw[20:20+struct.unpack_from('<I',raw,12)[0]])
    prim=gltf['meshes'][0]['primitives'][0];triangles=gltf['accessors'][prim['indices']]['count']//3
    RECORDS['scene/arena-of-fate/'+key]={'mesh':key+'.glb','class':'tall','footprint':fp,'tactical':'open','label':LABELS.get(label,label),'triangles':triangles,'boundsBlenderMeters':bounds,'bytes':path.stat().st_size}
    flush()

def flush():
    target=OUT/'iconography-manifest.json'
    existing=json.loads(target.read_text()) if target.exists() else {'version':1,'tile':[256,159],'storey':284,'textures':{}}
    existing['textures'].update({k:{a:b for a,b in v.items() if a in ('mesh','class','footprint','tactical')} for k,v in RECORDS.items()});target.write_text(json.dumps(existing,indent=2)+'\n')
    measured=OUT/'measurements.json';old=json.loads(measured.read_text()) if measured.exists() else {};old.update(RECORDS);measured.write_text(json.dumps(old,indent=2,ensure_ascii=False)+'\n')

def banner(key,alliance=False):
    reset(OUT/(key+'.png'))
    w,h=(2.7,4.05) if alliance else ((2.8,3.8) if key=='empire' else ((1.15,2.4) if key=='cult' else (2.2,3.3)))
    N,M=20,32;v=[];f=[]
    for j in range(M+1):
        for i in range(N+1):
            u=i/N;t=j/M;y=.045*math.sin(u*math.tau*3+.7*t)*(1-t);v.append(((u-.5)*w,y,.10+t*h))
    for j in range(M):
        for i in range(N):a=j*(N+1)+i;f.append((a,a+1,a+N+2,a+N+1))
    o=mesh('textile',v,f);uv=o.data.uv_layers.active.data
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv[li].uv=(co.x/w+.5,(co.z-.1)/h)
    bpy.context.view_layer.objects.active=o;o.select_set(True);mod=o.modifiers.new('cloth edge thickness','SOLIDIFY');mod.thickness=.012;bpy.ops.object.modifier_apply(modifier=mod.name)
    rod((-w/2-.08,0,h+.14),(w/2+.08,0,h+.14),.035)
    for s in [-1,1]:ell((s*(w/2+.10),0,h+.14),(.07,.07,.07))
    for i in range(17):rod(((i/16-.5)*w,0,.1),((i/16-.5)*w,.01,.025),.01)
    export('banner-'+key,[3,1] if alliance or key=='empire' else ([1,1] if key=='cult' else [2,1]),key)



REGIONS=['empire','freelands','bennet','kolbjorn','mage-tower','seashores','sindile','stravian','storm-islands','taii-maku','kepesh','tsvetan','yama']
ALLIANCES=['allied-forces','arcanum','darkall','tanarean-empire']
if A.only in ['all','banners']:
    for key in REGIONS+ALLIANCES+['cult']:banner(key,key in ALLIANCES)
print('Produced',len(RECORDS),'iconographic meshes')
