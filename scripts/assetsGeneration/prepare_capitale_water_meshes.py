"""Extend existing water skins under the banks; preserve wet-point elevations and terrain."""
from pathlib import Path
import json
import struct
import hashlib
import numpy as np
P=Path('E:/JustAnotherRpgGame_UR/JustAnotherRpgGame');D=P/'Saved/Jadg/capital-landscape-districts';O=P/'Source/Elements/Assets/Built/capitale-eau';O.mkdir(parents=True,exist_ok=True)
manifest=json.loads((D/'manifest.json').read_text());wet=np.zeros((3277,2773),bool);z=np.zeros(wet.shape,np.float32)
for t in manifest['tiles']:
 tx,ty=map(int,t['id'][1:].split('_'));f=np.load(D/'tiles'/t['id']/'fields.npz');sl=np.s_[ty*252:ty*252+253,tx*252:tx*252+253];wet[sl]=f['water'];z[sl]=f['water_z']
original=wet.copy()
for _step in range(3):
 sums=np.zeros(z.shape,np.float32);counts=np.zeros(z.shape,np.float32)
 for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
  ys=slice(max(0,dy),min(z.shape[0],z.shape[0]+dy));xs=slice(max(0,dx),min(z.shape[1],z.shape[1]+dx));yt=slice(max(0,-dy),min(z.shape[0],z.shape[0]-dy));xt=slice(max(0,-dx),min(z.shape[1],z.shape[1]-dx))
  sums[yt,xt]+=z[ys,xs]*wet[ys,xs];counts[yt,xt]+=wet[ys,xs]
 take=(~wet)&(counts>0);z[take]=sums[take]/counts[take];wet|=take

def glb(name,v,faces,path):
 n=np.zeros_like(v);n[:,1]=1;uv=v[:,[0,2]]/10
 arrays=[v.astype('<f4'),n.astype('<f4'),uv.astype('<f4'),faces.astype('<u4').ravel()];views=[];data=b''
 for i,a in enumerate(arrays):
  chunk=a.tobytes();views.append({'buffer':0,'byteOffset':len(data),'byteLength':len(chunk),'target':34963 if i==3 else 34962});data+=chunk
 acc=[{'bufferView':0,'componentType':5126,'count':len(v),'type':'VEC3','min':v.min(0).tolist(),'max':v.max(0).tolist()},{'bufferView':1,'componentType':5126,'count':len(v),'type':'VEC3'},{'bufferView':2,'componentType':5126,'count':len(v),'type':'VEC2'},{'bufferView':3,'componentType':5125,'count':faces.size,'type':'SCALAR'}]
 doc={'asset':{'version':'2.0','generator':'Capitale shoreline extension'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':name}],'meshes':[{'name':name,'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}]}],'materials':[{'name':'water-placeholder','pbrMetallicRoughness':{'baseColorFactor':[.04,.2,.24,1],'metallicFactor':0,'roughnessFactor':.1}}],'buffers':[{'byteLength':len(data)}],'bufferViews':views,'accessors':acc}
 js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);data+=b'\0'*((-len(data))%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data)
rows=[]
for t in manifest['tiles']:
 if t['wetFraction']==0:continue
 tx,ty=map(int,t['id'][1:].split('_'));sl=np.s_[ty*252:ty*252+253,tx*252:tx*252+253];m=wet[sl];h=z[sl];cells=m[:-1,:-1]&m[1:,:-1]&m[:-1,1:]&m[1:,1:];rr,cc=np.nonzero(cells);a=rr*253+cc;faces=np.concatenate([np.stack([a,a+253,a+254],1),np.stack([a,a+254,a+1],1)]);used,idx=np.unique(faces,return_inverse=True);yy,xx=np.divmod(used,253)
 v=np.stack([xx*t['spacing_m']+t['origin_m'][0],h.ravel()[used],yy*t['spacing_m']+t['origin_m'][1]],1).astype(np.float32)
 name='eau-'+t['id'];path=O/(name+'.glb');glb(name,v,idx.reshape(-1,3),path);rows.append({'id':name,'triangles':len(faces),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
(O/'manifest.json').write_text(json.dumps({'waterLevelChanged':False,'terrainChanged':False,'shoreExtensionMetres':12,'meshes':rows},indent=2));print('WATER_GEOMETRY_READY',len(rows),sum(r['triangles'] for r in rows))

