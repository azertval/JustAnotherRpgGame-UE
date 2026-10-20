"""Reproducible 48-piece pilot. Run with Blender --background --python.
Outputs Source/Elements/Assets/Built/aof-pilot-001-048/*.glb and manifest.json.
Dimensions are pilot proposals, not a revision of the 300 x 246 m Arena envelope.
"""
from pathlib import Path
import sys
import math
import json
import hashlib
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import arena_geometry as g  # noqa: E402
OUT=ROOT/'Source/Elements/Assets/Built/aof-pilot-001-048'
OUT.mkdir(parents=True,exist_ok=True)
R=12.; ANG=math.pi/12
names=['Fondation droite','Fondation courbe','Dalle carrée','Dalle radiale','Dalle triangulaire','Bordure de piste','Mur droit','Mur courbe','Angle intérieur','Angle extérieur','Mur de fermeture','Mur à ouverture','Pilier carré','Poutre droite','Poutre courbe','Contrefort','Support de gradins','Console','Arc plein cintre','Demi-arc','Clé de voûte','Fût de colonne','Base de colonne','Chapiteau','Gradins droits','Gradins courbes','Escalier droit','Escalier radial','Palier droit','Palier courbe','Voûte droite','Voûte courbe','Croisée de voûtes','Entrée de gradins','Rampe droite','Rampe courbe','Parapet droit','Parapet courbe','Corniche droite','Corniche courbe','Couronnement droit','Couronnement courbe','Podium droit','Podium courbe','Cadre de porte','Porte double','Herse','Trappe de piste']
def B(x,y,z,w,d,h,m='stone_cream'):g.block(x,y,z,w,d,h,m)
def sector(r0,r1,z,h,a0=0,a1=ANG,m='stone_cream',n=16):
 # Local origin at inner leading corner. Shared radius centre (0,-12).
 pts=[]
 for zz in (z,z+h):
  for rr in (r0,r1):
   for j in range(n+1):
    a=a0+(a1-a0)*j/n;pts.append((rr*math.sin(a),rr*math.cos(a)-R,zz))
 k=n+1;faces=[]
 for j in range(n):faces += [(j,j+1,k+j+1,k+j),(2*k+j,3*k+j,3*k+j+1,2*k+j+1),(j,2*k+j,2*k+j+1,j+1),(k+j,k+j+1,3*k+j+1,3*k+j)]
 faces += [(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)]
 g.solid(pts,faces,m,bevel=.008)
def arch(start=0,end=math.pi,ri=1.5,thick=.3,spring=0,depth=.5,center=0,m='stone_cream'):
 steps=max(4,round((end-start)/math.pi*20))
 for j in range(steps):
  a=start+(end-start)*j/steps;b=start+(end-start)*(j+1)/steps
  p=[(center+rr*math.cos(t),spring+rr*math.sin(t)) for rr,t in [(ri,a),(ri+thick,a),(ri+thick,b),(ri,b)]]
  g.prism(p,-depth/2,depth/2,m)
def stairs(curved=False,seats=False):
 n=3 if seats else 8;t=.85 if seats else .30;rise=.5 if seats else .1875
 for j in range(n):
  if curved:sector(R+j*t,R+(j+1)*t,0,(j+1)*rise)
  else:B(0,(j+.5)*t,0,3,t,(j+1)*rise)
def opening(arched=False):
 if arched:
  B(-1.65,0,0,.3,.5,3);B(1.65,0,0,.3,.5,3);arch(spring=3)
 else:
  B(-1.25,0,0,.5,.5,3);B(1.25,0,0,.5,.5,3);B(0,0,2.4,2,.5,.6)
def groin():
 n=24;pts=[]
 for layer in (0,.25):
  for j in range(n+1):
   y=-1.5+3*j/n
   for i in range(n+1):
    x=-1.5+3*i/n;z=math.sqrt(max(0,2.25-min(x*x,y*y)))+layer
    pts.append((x,y,z))
 k=(n+1)**2;faces=[]
 for j in range(n):
  for i in range(n):
   a=j*(n+1)+i;b=a+1;d=a+n+1;e=d+1
   faces +=[(a,d,e,b),(a+k,b+k,e+k,d+k)]
 boundary=list(range(n+1))+[j*(n+1)+n for j in range(1,n+1)]+[n*(n+1)+i for i in range(n-1,-1,-1)]+[j*(n+1) for j in range(n-1,0,-1)]
 for i,a in enumerate(boundary):b=boundary[(i+1)%len(boundary)];faces.append((a,b,b+k,a+k))
 g.solid(pts,faces,bevel=0)
def curved_vault():
 pts=[];nu=24;nv=24
 for rr in (1.5,1.75):
  for i in range(nu+1):
   a=ANG*i/nu
   for j in range(nv+1):
    t=math.pi*j/nv;rad=R+1.5+rr*math.cos(t);pts.append((rad*math.sin(a),rad*math.cos(a)-R,rr*math.sin(t)))
 k=(nu+1)*(nv+1);faces=[]
 for i in range(nu):
  for j in range(nv):
   a=i*(nv+1)+j;b=a+nv+1;faces.extend([(a,a+1,b+1,b),(a+k,b+k,b+1+k,a+1+k)])
 boundary=list(range(nv+1))+[i*(nv+1)+nv for i in range(1,nu+1)]+[nu*(nv+1)+j for j in range(nv-1,-1,-1)]+[i*(nv+1) for i in range(nu-1,0,-1)]
 for i,a in enumerate(boundary):b=boundary[(i+1)%len(boundary)];faces.append((a,b,b+k,a+k))
 g.solid(pts,faces,bevel=.006)
def ramp(curved=False):
 if not curved:g.prism([(-1.5,0),(1.5,0),(1.5,1.5),(-1.5,.05)],-1.5,1.5)
 else:
  n=32;pts=[]
  for top in (False,True):
   for rr in (R,R+3):
    for j in range(n+1):
     a=ANG*j/n;pts.append((rr*math.sin(a),rr*math.cos(a)-R,(.05+1.45*j/n) if top else 0))
  k=n+1;faces=[]
  for j in range(n):faces +=[(j,j+1,k+j+1,k+j),(2*k+j,3*k+j,3*k+j+1,2*k+j+1),(j,2*k+j,2*k+j+1,j+1),(k+j,k+j+1,3*k+j+1,3*k+j)]
  faces +=[(0,k,3*k,2*k),(n,2*k+n,3*k+n,k+n)];g.solid(pts,faces)
def profile(curved=False,cap=False):
 for z,w,h in ([(0,.65,.12),(.12,.8,.12)] if cap else [(0,.5,.15),(.15,.6,.12),(.27,.75,.12),(.39,.85,.10)]):
  if curved:sector(R,R+w,z,h)
  else:B(0,0,z,3,w,h)
def door():
 for j in range(12):
  x0=-1.48+j*2.96/12;x1=x0+2.96/12-.012
  def top(x):
   return 3+math.sqrt(max(0,1.48**2-x*x))
  g.prism([(x0,0),(x1,0),(x1,top(x1)),(x0,top(x0))],-.12,.12,'wood')
 for side in (-1,1):
  for z in (.35,1.6,2.7):B(side*.76,-.14,z,1.30,.06,.1,'dark_metal')
  g.rod((side*.22,-.22,1.3),(side*.22,-.22,1.65),.04,'dark_metal')
def gate():
 for j in range(11):
  x=-1.4+j*.28;h=3+math.sqrt(max(0,1.48**2-x*x));B(x,0,0,.07,.10,h,'dark_metal')
 for z in (.4,1.2,2,2.8,3.4):
  width=2.9 if z<=3 else 2*math.sqrt(1.48**2-(z-3)**2)
  B(0,0,z,width,.14,.08,'dark_metal')
def hatch():
 for x,y,w,d in [(0,-.85,1.8,.15),(0,.85,1.8,.15),(-.85,0,.15,1.5),(.85,0,.15,1.5)]:B(x,y,0,w,d,.2)
 for j in range(6):B(-.625+j*.25,0,.04,.24,1.5,.12,'wood')
 for y in (-.45,.45):B(0,y,.16,1.5,.08,.03,'dark_metal')
 g.rod((-.15,0,.23),(.15,0,.23),.035,'dark_metal')
def build(i):
 if i==1:B(0,0,0,3,1.5,.6)
 elif i==2:sector(R,R+1.5,0,.6)
 elif i==3:B(0,0,0,3,3,.2)
 elif i==4:sector(R,R+3,0,.2)
 elif i==5:g.prism([(0,0),(3,0),(0,.2)],0,3) # replaced below by triangular plan
 elif i==6:sector(R,R+.25,0,.3)
 elif i==7:g.masonry(-1.5,1.5,0,0,3,depth=.5,course=.5,brick=1.5)
 elif i==8:sector(R,R+.5,0,3)
 elif i in (9,10):
  B(0,0,0,3,.5,3);B(1.25,1.5 if i==9 else -1.5,0,.5,2.5,3)
 elif i==11:B(0,0,0,1.5,.5,3)
 elif i==12:opening()
 elif i==13:B(0,0,0,.6,.6,3)
 elif i==14:B(0,0,0,3,.5,.4)
 elif i==15:sector(R,R+.5,0,.4)
 elif i==16:g.prism([(-.6,0),(.6,0),(.25,3),(-.25,3)],-.35,.35)
 elif i==17:g.prism([(0,0),(2.55,0),(2.55,1.5),(1.7,1.5),(1.7,1),(.85,1),(.85,.5),(0,.5)],-.25,.25)
 elif i==18:g.prism([(-.4,.8),(.4,.8),(.4,.55),(-.2,0),(-.4,0)],-.3,.3)
 elif i==19:arch()
 elif i==20:arch(0,math.pi/2)
 elif i==21:g.prism([(-.12,0),(.12,0),(.2,.35),(-.2,.35)],-.25,.25)
 elif i==22:g.turned(0,0,0,[(.3,0),(.30,.12),(.28,2.8),(.28,3)],'marble_white',64,0.012)
 elif i==23:
  B(0,0,0,.8,.8,.12,'marble_white');g.turned(0,0,.12,[(.36,0),(.36,.08),(.3,.12),(.33,.18),(.28,.28)],'marble_white')
 elif i==24:
  g.turned(0,0,0,[(.28,0),(.28,.1),(.38,.28),(.4,.3)],'marble_white');B(0,0,.3,.85,.85,.12,'marble_white')
 elif i in (25,26,27,28):stairs(i in (26,28),i in (25,26))
 elif i==29:B(0,0,0,3,1.5,.2)
 elif i==30:sector(R,R+1.5,0,.2)
 elif i==31:arch(depth=3)
 elif i==32:curved_vault()
 elif i==33:groin()
 elif i==34:
  B(-1.75,0,0,.5,3,3);B(1.75,0,0,.5,3,3);arch(spring=3,depth=3)
 elif i in (35,36):ramp(i==36)
 elif i==37:B(0,0,0,3,.3,1.1);B(0,0,1.1,3,.4,.12)
 elif i==38:sector(R,R+.3,0,1.1);sector(R-.05,R+.35,1.1,.12)
 elif i in (39,40,41,42):profile(i in (40,42),i in (41,42))
 elif i==43:B(0,0,0,3,.6,2.85);B(0,0,2.85,3,.8,.15)
 elif i==44:sector(R,R+.6,0,2.85);sector(R-.1,R+.7,2.85,.15)
 elif i==45:opening(True)
 elif i==46:door()
 elif i==47:gate()
 elif i==48:hatch()
def triangle():
 g.solid([(0,0,0),(3,0,0),(0,3,0),(0,0,.2),(3,0,.2),(0,3,.2)],[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
materials=g.build_materials();records=[]
for i,label in enumerate(names,1):
 name=f'SM_AOF_{i:03d}'
 g.export_piece(name,triangle if i==5 else lambda i=i:build(i),OUT,materials,clean_degenerate=True)
 entry=dict(g.PIECES[-1]);entry.update({'catalogueId':i,'label':label,'sha256':hashlib.sha256((OUT/entry['file']).read_bytes()).hexdigest(),'units':'metres','uvRepeatMetres':2,'status':'pilot-awaiting-user-review'})
 records.append(entry)
# Retain a reusable native source scene containing all individual objects.
for i,row in enumerate(records):
 bpy.ops.import_scene.gltf(filepath=str(OUT/row['file']))
 for obj in bpy.context.selected_objects:obj.location.x+=(i%6)*6;obj.location.y+=(i//6)*7
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'AOF_001_048_source.blend'))
(OUT/'manifest.json').write_text(json.dumps({'version':1,'generator':'scripts/assetsGeneration/build_aof_001_048.py','scope':'48 base types, pilot variants only','radiusMetres':R,'sectorDegrees':15,'closureCount':24,'meshes':records},ensure_ascii=False,indent=2),encoding='utf-8')
print('AOF_GEOMETRY_COMPLETE',len(records),flush=True)
