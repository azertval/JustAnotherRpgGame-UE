"""Regenerable coherent PBR fields; normals derive from physical height, not colour."""
from pathlib import Path
import sys
import json
import hashlib
import numpy as np
from PIL import Image
ROOT=Path('E:/JustAnotherRpgGame_UR/JustAnotherRpgGame')
sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import build_arena_witness_textures as lib  # noqa: E402
OUT=ROOT/'Source/Elements/Assets/Built/aof-pilot-surfaces-v2';OUT.mkdir(parents=True,exist_ok=True)
N=2048;a=np.arange(N,dtype=np.float32)/N;u,v=np.meshgrid(a,a)
doc={'version':2,'tileMetres':2,'size':N,'normalConvention':'OpenGL; flip green on Unreal import','provenance':'Original periodic procedural material fields, common physical features drive height, colour, roughness and metal masks. No normal derived from albedo.','materials':{}}
for j,name in enumerate(['stone_cream','marble_white','dark_metal','wood','mortar','bronze']):
 seed=902+j*37
 macro=lib.field(u,v,seed,2,12,count=12);mid=lib.field(u,v,seed+1,20,90,count=16);fine=lib.field(u,v,seed+2,100,360,count=16)
 metal=np.zeros_like(u);ao=np.ones_like(u);h=np.zeros_like(u)
 if name in ('stone_cream','mortar'):
  pores=lib.granules(u,v,seed+3,100,97,.48);pits=lib.granules(u,v,seed+4,19,21,.34)
  cuts=lib.physical_scratches(u,v,seed+5,65,.0018)
  h=.0015*macro+.0008*mid+.00025*fine-.004*pores-.006*pits-.0015*cuts
  rough=np.clip(.73+.17*macro+.12*pores+.08*pits-.06*mid,.4,.98)
  base=np.array([.66,.60,.48] if name=='stone_cream' else [.38,.35,.29])
  colour=base+(macro*.07+mid*.025+fine*.009-pores*.045-pits*.065)[...,None]
  ao=1-.28*pores-.35*pits
 elif name=='wood':
  flow,knots,rings=lib.wood_flow(u,v,seed+3)
  grain=np.sin(2*np.pi*(70*u+flow*2));fibre=np.maximum(grain-.35,0)**2
  h=.0009*macro-.0018*fibre-.0025*knots+.00045*rings+.00018*fine
  colour=np.array([.32,.145,.055])+(macro*.055-fibre*.055-knots*.07+rings*.015)[...,None]
  rough=np.clip(.54+.17*macro+.22*fibre+.09*knots,.28,.9);ao=1-.20*fibre-.25*knots
 elif name=='marble_white':
  veins=np.exp(-(np.sin(2*np.pi*(2*u+v+.24*macro))/.10)**2)
  scratches=lib.physical_scratches(u,v,seed+3,95,.0008)
  h=.00018*mid+.00010*fine-.00055*scratches
  colour=np.array([.81,.80,.74])-(veins*.19)[...,None]+(macro*.025)[...,None]
  rough=np.clip(.20+.10*macro+.09*veins+.22*scratches,.08,.6)
 else:
  dents=lib.granules(u,v,seed+3,45,49,.8);scratches=lib.physical_scratches(u,v,seed+4,120,.001)
  oxide=np.clip((macro+.2*mid-.05)*3,0,1)
  h=-.0012*dents-.0006*scratches+.00035*mid+.00008*fine
  fresh=np.array([.57,.35,.12] if name=='bronze' else [.26,.28,.30]);patina=np.array([.09,.18,.13] if name=='bronze' else [.16,.075,.026])
  colour=fresh*(1-oxide[...,None])+patina*oxide[...,None]+(mid*.018)[...,None]
  metal=1-oxide;rough=np.clip(.24+.13*macro+.48*oxide+.12*scratches,.12,.9);ao=1-.17*dents
 spacing=2/N;dx=(np.roll(h,-1,1)-np.roll(h,1,1))/(2*spacing);dy=(np.roll(h,-1,0)-np.roll(h,1,0))/(2*spacing)
 normal=np.stack([-dx,-dy,np.ones_like(h)],-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
 # Fixed centred 4 cm height range matches the stock Sensei Nanite parent magnitude.
 height=np.clip(.5+h/.04,0,1)
 arrays={'baseColor':colour,'normal':normal*.5+.5,'roughness':rough,'metallic':metal,'ao':ao,'orm':np.stack([ao,rough,metal],-1)}
 files={}
 for role,arr in arrays.items():
  p=OUT/f'{name}_{role}.png';Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)).save(p);files[role]={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 p=OUT/f'{name}_height.png';Image.fromarray(np.uint16(height*65535+.5)).save(p);files['height']={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 angle=np.degrees(np.arctan(np.sqrt(dx*dx+dy*dy)))
 doc['materials'][name]={'files':files,'heightRangeMm':[float(h.min()*1000),float(h.max()*1000)],'normalAngleP50P95':np.percentile(angle,[50,95]).tolist(),'metallicRange':[float(metal.min()),float(metal.max())]}
 print(name,doc['materials'][name]['normalAngleP50P95'],flush=True)
(OUT/'manifest.json').write_text(json.dumps(doc,indent=2))
