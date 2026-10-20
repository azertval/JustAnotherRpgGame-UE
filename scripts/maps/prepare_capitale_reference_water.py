from pathlib import Path
import numpy as np
import json
import struct
import hashlib
P=Path(__file__).resolve().parents[2]
D=P/'Source/Elements/Terrain/capital/relief-reference';O=D/'water';O.mkdir(exist_ok=True)
def glb(name,v,faces,path):
 n=np.zeros_like(v);n[:,1]=1;uv=v[:,[0,2]]/10
 arrays=[v.astype('<f4'),n.astype('<f4'),uv.astype('<f4'),faces.astype('<u4').ravel()];views=[];data=b''
 for i,a in enumerate(arrays):
  chunk=a.tobytes();views.append({'buffer':0,'byteOffset':len(data),'byteLength':len(chunk),'target':34963 if i==3 else 34962});data+=chunk
 acc=[{'bufferView':0,'componentType':5126,'count':len(v),'type':'VEC3','min':v.min(0).tolist(),'max':v.max(0).tolist()},{'bufferView':1,'componentType':5126,'count':len(v),'type':'VEC3'},{'bufferView':2,'componentType':5126,'count':len(v),'type':'VEC2'},{'bufferView':3,'componentType':5125,'count':faces.size,'type':'SCALAR'}]
 doc={'asset':{'version':'2.0','generator':'Capitale shoreline extension'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':name}],'meshes':[{'name':name,'primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3,'material':0}]}],'materials':[{'name':'water-placeholder','pbrMetallicRoughness':{'baseColorFactor':[.04,.2,.24,1],'metallicFactor':0,'roughnessFactor':.1}}],'buffers':[{'byteLength':len(data)}],'bufferViews':views,'accessors':acc}
 js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);data+=b'\0'*((-len(data))%4)
 path.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(data))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(data),0x004e4942)+data)
# Les tuiles d'eau suivent le rivage : celles d'un rivage precedent ne restent pas.
for stale in O.glob('eau-reference-*.glb'):stale.unlink()
f=np.load(D/'terrain.npz');z=f['water_z'];h=f['height'];rows=[]
for iy in range(4):
 for ix in range(4):
  sl=np.s_[iy*504:iy*504+505:2,ix*504:ix*504+505:2]
  zz=z[sl];wet=(h[sl]-zz)<2.0
  cells=wet[:-1,:-1]|wet[1:,:-1]|wet[:-1,1:]|wet[1:,1:]
  rr,cc=np.nonzero(cells)
  if not len(rr):continue
  a=rr*253+cc
  faces=np.concatenate([np.stack([a,a+253,a+254],1),np.stack([a,a+254,a+1],1)])
  used,idx=np.unique(faces,return_inverse=True);yy,xx=np.divmod(used,253)
  v=np.stack([xx*4-2016+ix*1008,zz.ravel()[used],yy*4-2016+iy*1008],1).astype(np.float32)
  name=f'eau-reference-{ix}-{iy}';path=O/(name+'.glb');glb(name,v,idx.reshape(-1,3),path)
  rows.append(dict(id=name,triangles=len(faces),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
(O/'manifest.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Water meshes',len(rows),'triangles',sum(r['triangles'] for r in rows))
