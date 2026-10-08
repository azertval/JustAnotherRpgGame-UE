#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Author Meshy sculptures -> mounted Colosseum copies, without decimation.

Blender --background --factory-startup --threads 2 --python-exit-code 1 --python FILE
Original files and basecolor bytes remain unchanged. Composition dimensions are
specific to this map, not a decor standard or a new polygon/texture budget.
"""
import bpy
import json
import math
import struct
import hashlib
import numpy as np
from pathlib import Path
from mathutils import Matrix

ROOT=Path(__file__).resolve().parents[2]
WORK=ROOT/'Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/V2'
OUT=WORK/'Sculptures'

def read_glb(path):
    data=path.read_bytes();cursor=12;doc=None;blob=None
    assert data[:4]==b'glTF'
    while cursor<len(data):
        size,kind=struct.unpack_from('<II',data,cursor);chunk=data[cursor+8:cursor+8+size];cursor+=size+8
        if kind==0x4e4f534a:doc=json.loads(chunk)
        elif kind==0x004e4942:blob=chunk
    return doc,blob

def image_bytes(doc,blob,index):
    im=doc['images'][index];view=doc['bufferViews'][im['bufferView']];start=view.get('byteOffset',0)
    return blob[start:start+view['byteLength']]

def restore_exact_albedo(path,original):
    """Preserve original PNG bytes even if the glTF exporter repacks an image."""
    doc,blob=read_glb(path);assert len(doc['images'])==1
    image_view=doc['images'][0]['bufferView'];packed=bytearray()
    for i,view in enumerate(doc['bufferViews']):
        old=view.get('byteOffset',0);part=original if i==image_view else blob[old:old+view['byteLength']]
        packed.extend(b'\0'*((-len(packed))%4));view['byteOffset']=len(packed);view['byteLength']=len(part);packed.extend(part)
    doc['buffers'][0]['byteLength']=len(packed);packed.extend(b'\0'*((-len(packed))%4))
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
    path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(packed))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(packed),0x004e4942)+packed)

def clean():
    for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
    for collection in [bpy.data.meshes,bpy.data.materials,bpy.data.images]:
        for item in list(collection):
            if item.users==0:collection.remove(item)

def normalize(info,role,reservation=None,side=None):
    clean();source=Path(info['source']);original=source.read_bytes();source_hash=hashlib.sha256(original).hexdigest()
    assert source_hash==info['source_sha256'],str(source)
    doc,blob=read_glb(source);prims=[p for m in doc['meshes'] for p in m['primitives']]
    assert len(prims)==len(doc['meshes'])==len(doc['materials'])==1
    source_triangles=doc['accessors'][prims[0]['indices']]['count']//3
    bc=doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture'];im_index=doc['textures'][bc['index']]['source']
    albedo=image_bytes(doc,blob,im_index);albedo_hash=hashlib.sha256(albedo).hexdigest()
    transfer=OUT/'.basecolor-transfer.png';transfer.write_bytes(albedo)
    bpy.ops.import_scene.gltf(filepath=str(source))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(objects)==1
    obj=objects[0];bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    coords=np.array([v.co[:] for v in obj.data.vertices]);lo=coords.min(axis=0);hi=coords.max(axis=0);height=hi[2]-lo[2]
    # The low contact band is measured from the actual sculpted plinth/paws.
    contact=coords[coords[:,2]<=lo[2]+height*.025]
    contact_center=(contact[:,:2].min(axis=0)+contact[:,:2].max(axis=0))/2
    if role=='deity':
        key=info['key'];target=1.55 if key=='nature-spirits' else 2.8
        factor=target/height;point=reservation['at'];cx=(point[0]+.5)*1.5-25.5;cy=18-(point[1]+.5)*1.5
        angle=math.atan2(-cx,cy);base=3.94;floor=1;offset=np.array([0.,0.,base-3*floor]);piece='meshy-statue-'+key
    else:
        # Keep the sculpture's physical base within the portal's 1.90x1.70m top.
        contact_size=np.ptp(contact[:,:2],axis=0)
        factor=min(1.7/height,1.80/contact_size[0],1.60/contact_size[1]);target=factor*height
        cx=-4.65 if side=='left' else 4.65;cy=-15.8;angle=0.;base=7.69;floor=2;piece='meshy-portal-guardian-lion-'+side
        offset=np.array([0.,0.,base-3*floor]);key=None
    coords[:,:2]-=contact_center;coords[:,2]-=lo[2];coords*=factor
    rotation=np.array([[math.cos(angle),-math.sin(angle),0],[math.sin(angle),math.cos(angle),0],[0,0,1]])
    coords=coords@rotation.T
    contact_scaled=(contact-np.array([*contact_center,lo[2]]))*factor@rotation.T
    extents=np.max(np.abs(coords[:,:2]),axis=0)
    footprint=[]
    for extent in extents:
        n=max(1,math.ceil(2*extent/1.5));footprint.append(n if n%2 else n+1)
    if role=='deity':
        at=[reservation['at'][j]-(footprint[j]-1)//2 for j in range(2)]
    else:
        at=[round((cx+25.5)/1.5-footprint[0]/2),round((18-cy)/1.5-footprint[1]/2)]
        origin=np.array([(at[0]+footprint[0]/2)*1.5-25.5,18-(at[1]+footprint[1]/2)*1.5])
        offset[:2]=np.array([cx,cy])-origin
        # The grid rounding offset must also remain inside the declared footprint.
        for j in range(2):
            while np.max(np.abs(coords[:,j]+offset[j]))>footprint[j]*.75:
                footprint[j]+=2;at[j]-=1
    coords+=offset
    affine=np.eye(4);affine[:3,:3]=rotation*factor
    affine[:3,3]=offset-affine[:3,:3]@np.array([*contact_center,lo[2]])
    obj.matrix_world=Matrix(affine.tolist())
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj.data.update();obj.name=piece;obj.data.name=piece
    # Author's UVs and indexed topology are retained. Only rigid transforms and
    # one uniform scale have been applied; no decimation, sculpting or remesh.
    mat=bpy.data.materials.new(piece+'-original-albedo');mat.use_nodes=True;mat.use_backface_culling=False
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0.;bs.inputs['Roughness'].default_value=1.
    image=bpy.data.images.load(str(transfer),check_existing=False);image.pack();size=list(image.size)
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    obj.data.materials.clear();obj.data.materials.append(mat)
    for poly in obj.data.polygons:poly.material_index=0
    dest=OUT/(piece+'.glb')
    bpy.ops.export_scene.gltf(filepath=str(dest),export_format='GLB',use_selection=True,export_yup=True,export_normals=True,export_texcoords=True,export_materials='EXPORT',export_animations=False,export_cameras=False,export_lights=False)
    restore_exact_albedo(dest,albedo)
    exported,binout=read_glb(dest);primitive=exported['meshes'][0]['primitives'][0]
    assert len(exported['meshes'])==len(exported['meshes'][0]['primitives'])==len(exported['materials'])==len(exported['images'])==1
    assert {'POSITION','NORMAL','TEXCOORD_0'}<=set(primitive['attributes'])
    tris=exported['accessors'][primitive['indices']]['count']//3;assert tris==source_triangles
    assert hashlib.sha256(image_bytes(exported,binout,0)).hexdigest()==albedo_hash
    assert 'normalTexture' not in exported['materials'][0] and 'metallicRoughnessTexture' not in exported['materials'][0]['pbrMetallicRoughness']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
    assert abs(float(coords[:,2].min())+floor*3-base)<.00001
    local_bounds=[coords.min(axis=0).tolist(),coords.max(axis=0).tolist()]
    origin=np.array([(at[0]+footprint[0]/2)*1.5-25.5,18-(at[1]+footprint[1]/2)*1.5,floor*3])
    support=[max(1.20,float(2*np.max(np.abs(contact_scaled[:,j]))+.12)) for j in range(2)] if role=='deity' else [1.9,1.7]
    placement={'piece':piece,'role':role,'deity':key,'at':at,'footprint':footprint,'floor':floor,'supportTopMetres':base,'localMountOffsetMetres':offset.tolist(),'rotationZDegrees':math.degrees(angle),'name':info['name'] if role=='deity' else 'Lion gardien '+side}
    measurement={'piece':piece,'source':str(source),'sourceSha256':source_hash,'outputSha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'triangles':tris,'bytes':dest.stat().st_size,'basecolorSize':size,'basecolorSha256':albedo_hash,'basecolorBytesPreserved':True,'heightMetres':float(target),'uniformScale':float(factor),'localBounds':local_bounds,'worldBounds':[(coords.min(axis=0)+origin).tolist(),(coords.max(axis=0)+origin).tolist()],'footprint':footprint,'supportSizeMetres':support,'contactBoundsXY':[contact_scaled[:,:2].min(axis=0).tolist(),contact_scaled[:,:2].max(axis=0).tolist()],'rotationZDegrees':math.degrees(angle),'decimated':False}
    print('NORMALIZED',piece,tris,measurement['bytes'],footprint,flush=True)
    return placement,measurement

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    identity=json.loads((WORK/'MeshyReferences/meshy-identification.json').read_text(encoding='utf-8-sig'))
    layout=json.loads((WORK/'arena-layout-contract.json').read_text(encoding='utf-8-sig'))
    reservations={v['piece'].removeprefix('statue-'):v for v in layout['statueReservations']}
    placements=[];measures=[];textures={};supports=[]
    for model in identity['models']:
        if model['key'] in reservations:jobs=[('deity',reservations[model['key']],None)]
        else:jobs=[('lion',None,side) for side in ['left','right']]
        for role,reservation,side in jobs:
            placement,measure=normalize(model,role,reservation,side);placements.append(placement);measures.append(measure)
            textures['scene/arena-of-fate/'+placement['piece']]={'mesh':placement['piece']+'.glb','class':'tall','footprint':placement['footprint'],'tactical':'solid'}
            if role=='deity':supports.append({'deity':model['key'],'at':reservation['at'],'sizeMetres':measure['supportSizeMetres'],'topMetres':3.94})
    assert len(placements)==16 and len(supports)==14
    overlaps=[]
    for i,left in enumerate(measures):
        for right in measures[i+1:]:
            if all(min(left['worldBounds'][1][j],right['worldBounds'][1][j])-max(left['worldBounds'][0][j],right['worldBounds'][0][j])>.001 for j in range(3)):overlaps.append([left['piece'],right['piece']])
    assert not overlaps,overlaps
    (OUT/'sculptures-manifest.json').write_text(json.dumps({'version':1,'tile':[256,159],'storey':283.742841317,'textures':textures},indent=2),encoding='utf8')
    report={'scope':'Colosseum composition only, not a standard','sourceCount':15,'outputCount':16,'totalPlacedTriangles':sum(v['triangles'] for v in measures),'totalOutputBytes':sum(v['bytes'] for v in measures),'pairwiseBoundsOverlaps':overlaps,'measurements':measures}
    (OUT/'sculptures-measurements.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    (OUT/'sculptures-supports.json').write_text(json.dumps({'supports':supports},indent=2),encoding='utf8')
    (WORK/'Meshy').mkdir(exist_ok=True)
    (WORK/'Meshy/placement-contract.json').write_text(json.dumps({'placements':placements},indent=2),encoding='utf8')
    (OUT/'.basecolor-transfer.png').unlink(missing_ok=True)
    clean();print('COMPLETE',len(placements),report['totalPlacedTriangles'],report['totalOutputBytes'],flush=True)

if __name__=='__main__':main()
