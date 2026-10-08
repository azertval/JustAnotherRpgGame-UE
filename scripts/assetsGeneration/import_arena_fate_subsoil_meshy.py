#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Normalize eight author Meshy underground sculptures without changing originals.

Run with Blender --background --factory-startup --python FILE -- --root WORKTREE.
Only uniform scaling, origin/mount translation and basecolor-only material setup.
Dimensions are V3 composition choices, not a new decor budget or standard.
"""
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix

parser=argparse.ArgumentParser()
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=args.root
OUT=ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/V3/Sculptures'
spec=importlib.util.spec_from_file_location('arena_meshy_common',ROOT/'scripts/assetsGeneration/import_arena_fate_meshy.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)

def normalize(info):
    common.clean()
    source=Path(info['source']);source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_hash==info['source_sha256'],source
    doc,blob=common.read_glb(source);prim=doc['meshes'][0]['primitives'][0]
    assert len(doc['meshes'])==len(doc['meshes'][0]['primitives'])==len(doc['materials'])==1
    source_triangles=doc['accessors'][prim['indices']]['count']//3
    image_index=doc['textures'][doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']]['source']
    albedo=common.image_bytes(doc,blob,image_index);albedo_hash=hashlib.sha256(albedo).hexdigest()
    transfer=OUT/'.basecolor-transfer.png';transfer.write_bytes(albedo)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    obj=objects[0];bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    coords=np.array([v.co[:] for v in obj.data.vertices]);lo=coords.min(axis=0);hi=coords.max(axis=0);dimensions=hi-lo
    factors=[info[key]/dimensions[axis] for key,axis in [('target_width',0),('target_depth',1),('target_height',2)] if info[key] is not None]
    assert len(factors)==1
    factor=float(factors[0]);center=(lo+hi)/2
    origin=np.array([center[0],center[1],center[2] if info['mount_mode']=='center' else lo[2]])
    offset=np.array([0.,0.,info['mount_offset_z']])
    transformed=(coords-origin)*factor+offset
    footprint=info['footprint']
    assert np.max(np.abs(transformed[:,0]))<=footprint[0]*.75+.00001
    assert np.max(np.abs(transformed[:,1]))<=footprint[1]*.75+.00001
    affine=np.eye(4);affine[:3,:3]*=factor;affine[:3,3]=offset-origin*factor
    obj.matrix_world=Matrix(affine.tolist());bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj.data.update();obj.name=info['piece'];obj.data.name=info['piece']
    material=bpy.data.materials.new(info['piece']+'-original-albedo');material.use_nodes=True
    bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0.;bs.inputs['Roughness'].default_value=1.
    image=bpy.data.images.load(str(transfer),check_existing=False);image.pack();size=list(image.size)
    assert size==[2048,2048],size
    tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;material.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    obj.data.materials.clear();obj.data.materials.append(material)
    for poly in obj.data.polygons:poly.material_index=0
    dest=OUT/(info['piece']+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_yup=True,export_normals=True,export_texcoords=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False)
    common.restore_exact_albedo(dest,albedo)
    exported,out_blob=common.read_glb(dest);out_prim=exported['meshes'][0]['primitives'][0]
    assert len(exported['meshes'])==len(exported['meshes'][0]['primitives'])==len(exported['materials'])==len(exported['images'])==1
    assert {'POSITION','NORMAL','TEXCOORD_0'}<=set(out_prim['attributes'])
    triangles=exported['accessors'][out_prim['indices']]['count']//3;assert triangles==source_triangles
    assert hashlib.sha256(common.image_bytes(exported,out_blob,0)).hexdigest()==albedo_hash
    assert 'normalTexture' not in exported['materials'][0]
    assert 'metallicRoughnessTexture' not in exported['materials'][0]['pbrMetallicRoughness']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
    contact=transformed[coords[:,2]<=lo[2]+dimensions[2]*.025]
    report={'piece':info['piece'],'name':info['name'],'source':str(source),'sourceSha256':source_hash,'outputSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size,'triangles':triangles,'sourceTriangles':source_triangles,'basecolorSize':size,'basecolorSha256':albedo_hash,'basecolorBytesPreserved':True,'sourceDimensionsMetres':dimensions.tolist(),'dimensionsMetres':(dimensions*factor).tolist(),'localBounds':[transformed.min(axis=0).tolist(),transformed.max(axis=0).tolist()],'contactBoundsXY':[contact[:,:2].min(axis=0).tolist(),contact[:,:2].max(axis=0).tolist()],'uniformScale':factor,'mountMode':info['mount_mode'],'mountOffsetZMetres':info['mount_offset_z'],'footprint':footprint,'frontAxisBlender':'-Y','decimated':False,'textureRetouched':False}
    print('NORMALIZED',info['piece'],triangles,report['dimensionsMetres'],flush=True)
    return report

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    identity=json.loads((OUT/'identification.json').read_text(encoding='utf8'))
    measures=[normalize(info) for info in identity['models']]
    textures={'scene/arena-of-fate/'+r['piece']:{'mesh':r['piece']+'.glb','class':'tall','footprint':r['footprint'],'tactical':'solid'} for r in measures}
    (OUT/'sculptures-manifest.json').write_text(json.dumps({'version':1,'tile':[256,159],'storey':283.742841317,'textures':textures},indent=2)+'\n',encoding='utf8')
    (OUT/'sculptures-measurements.json').write_text(json.dumps({'scope':'V3 underground composition only; not a decor standard','sourceCount':8,'outputCount':8,'totalTriangles':sum(r['triangles'] for r in measures),'totalBytes':sum(r['bytes'] for r in measures),'measurements':measures},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (OUT/'.basecolor-transfer.png').unlink(missing_ok=True)
    common.clean();print('COMPLETE',len(measures),flush=True)

if __name__=='__main__':main()
