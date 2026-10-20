"""Catalogue 049-192, including native cloth sources and articulated variants.
Run with Blender background; all geometry, attachments and physics intents are text driven.
"""
from pathlib import Path
import json
import sys
import math
import hashlib
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/assetsGeneration'))
import arena_geometry as g  # noqa: E402
import arena_sculpted_geometry as sculpt  # noqa: E402
import build_arena_fate_props as p  # noqa: E402
sculpt.g=g;p.w=g
OUT=ROOT/'Source/Elements/Assets/Built/aof-extension-049-192';OUT.mkdir(parents=True,exist_ok=True)
CAT=json.loads((ROOT/'Source/Elements/Assets/aof-catalogue.json').read_text(encoding='utf-8'))
LABELS={i['id']:i['name'] for group in CAT for i in group['items']}
materials=g.build_materials();records=[]
B=g.block;rod=g.rod
cloth_ids={71,81,89,90,192}
rig_modes={46:'hinge',47:'slider',48:'hinge',91:'chain',93:'hinge',94:'hinge',103:'hinge',110:'hinge',114:'hinge',116:'hinge',118:'hinge',121:'slider',124:'hinge',125:'hinge',126:'chain',127:'hinge',128:'chain',129:'slider',131:'hinge',132:'wheel',137:'hinge',159:'chain',188:'hinge',189:'slider'}
loose={61,62,63,72,78,79,92,109,112,113,117,119,130,136,152,153,154,155,157,158,161,162,163,164,165,166,167,168,181,182,183,184,185,186,187,190,191}
def lat(profile,m='stone_cream',x=0,y=0,z=0):g.turned(x,y,z,profile,m,64)
def trim(w=3,d=.6,z=0):
 for dz,ww,dd,hh in [(0,w,d,.12),(.12,w+.12,d+.1,.12),(.24,w+.24,d+.2,.1)]:B(0,0,z+dz,ww,dd,hh)
def column(x=0,y=0,h=3):g.column(x,y,0,h,.22)
def table(w=1.6,d=.9,h=.8,m='wood'):
 for x in (-w*.4,w*.4):
  for y in (-d*.35,d*.35):B(x,y,0,.1,.1,h-.1,m)
 for j in range(6):B(-w/2+(j+.5)*w/6,0,h-.1,w/6-.008,d,.1,m)
 for y in (-d*.35,d*.35):B(0,y,.2,w*.8,.07,.08,m)
def frame(w=1.4,h=2.6,m='wood'):
 B(-w/2,0,0,.15,.2,h,m);B(w/2,0,0,.15,.2,h,m);B(0,0,h,w+.15,.2,.15,m)
def door(w=1.4,h=2.6,grille=False):
 frame(w,h,'stone_cream')
 for j in range(9):B(-w/2+.1+(j+.5)*(w-.2)/9,0,.06,(w-.2)/9-(.09 if grille else .009),.09,h-.1,'dark_metal' if grille else 'wood')
 for z in (.25,h*.5,h-.25):B(0,-.065,z,w-.2,.04,.08,'dark_metal')
 p.ring(w*.32,-.11,h*.47,.05,.07,.013,'bronze','y')
def niche(w=1.6,h=2.3):
 B(-w/2,0,0,.22,.65,h);B(w/2,0,0,.22,.65,h);B(0,-.3,0,w,.15,h)
 g.arc(0,0,h,w/2,.22,.65);B(0,0,0,w,.7,.15)
def basin(w=1.5,d=.7,h=.6):
 B(0,0,0,w,d,.15)
 for y in (-d/2,d/2):B(0,y,.15,w,.12,h)
 for x in (-w/2,w/2):B(x,0,.15,.12,d,h)
def ring(x=0,y=0,z=.2,rx=.12,ry=.17,t=.025,m='dark_metal',axis='y'):p.ring(x,y,z,rx,ry,t,m,axis)
def pulley(z=1):
 ring(0,0,z,.32,.32,.055,axis='y');ring(0,0,z,.27,.27,.035,axis='y')
 rod((0,-.19,z),(0,.19,z),.07,'dark_metal',32)
 for a in range(8):
  t=math.tau*a/8;rod((0,0,z),(.26*math.cos(t),0,z+.26*math.sin(t)),.023,'dark_metal')
 for x in (-.38,.38):B(x,0,z-.4,.08,.16,.8,'wood')
def pipe(path,r=.18):
 points=[];faces=[];n=32
 for j,center in enumerate(path):
  center=Vector(center);direction=Vector(path[min(j+1,len(path)-1)])-Vector(path[max(0,j-1)])
  direction.normalize();a=direction.cross(Vector((0,1,0)))
  if a.length<.01:a=direction.cross(Vector((1,0,0)))
  a.normalize();b=direction.cross(a)
  for radius in (r,r-.025):
   for k in range(n):points.append(tuple(center+radius*(a*math.cos(k*math.tau/n)+b*math.sin(k*math.tau/n))))
 for j in range(len(path)-1):
  for layer in (0,1):
   for k in range(n):
    q=j*2*n+layer*n+k;t=j*2*n+layer*n+(k+1)%n;faces.append((q,t,t+2*n,q+2*n))
 for j in (0,len(path)-1):
  for k in range(n):q=j*2*n+k;t=j*2*n+(k+1)%n;faces.append((q,q+n,t+n,t))
 g.solid(points,faces,'bronze',bevel=.003)
 g.FACE_SMOOTH[-len(faces):]=[True]*len(faces)
def channel(curve=False):
 if not curve:
  B(0,0,0,3,.6,.12);B(0,-.3,.12,3,.12,.24);B(0,.3,.12,3,.12,.24)
 else:
  for j in range(20):
   a=math.pi/2*j/20;b=math.pi/2*(j+1)/20
   for rr,ww,zz,hh in [(2,.6,0,.12),(1.72,.12,.12,.24),(2.28,.12,.12,.24)]:
    q=[((rr+s*ww/2)*math.cos(t),(rr+s*ww/2)*math.sin(t),z) for z in (zz,zz+hh) for s,t in [(-1,a),(1,a),(1,b),(-1,b)]]
    g.solid(q,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
def build(i):
 if i==49:B(0,0,0,.65,.28,3);trim(.7,.4);trim(.75,.5,2.66)
 elif i==50:trim(.8,.55)
 elif i==51:lat([(.2,0),(.32,.22),(.4,.27)],x=0);B(0,0,.27,.85,.55,.13)
 elif i==52:trim(3,.8);sculpt.carved_frieze(0,.4,.36,3);B(0,0,.34,3,.6,.55);trim(3,.9,.89)
 elif i==53:sculpt.carved_frieze(0,0,0,3)
 elif i==54:
  ring(z=.55,rx=.5,ry=.5,t=.06,m='bronze');g.prism([(.45*math.cos(a*math.tau/48),.55+.45*math.sin(a*math.tau/48)) for a in range(48)],-.03,.03,'marble_white')
 elif i in (55,77):niche(1.6,2.3 if i==55 else 3)
 elif i==56:g.prism([(-1.7,0),(1.7,0),(0,.9)],-.25,.25);rod((-1.75,-.3,0),(0,-.3,.95),.08,'marble_white');rod((0,-.3,.95),(1.75,-.3,0),.08,'marble_white')
 elif i==57:g.rail(0,0,0,3)
 elif i==58:lat([(.13,0),(.13,.1),(.09,.16),(.15,.4),(.1,.7),(.12,.8)],'marble_white')
 elif i in (59,73,156):
  trim(1.4,1.4);B(0,0,.34,1.1,1.1,1.0 if i==59 else .4);trim(1.4,1.4,1.34 if i==59 else .74)
 elif i==61:p.sculpted_armchair()
 elif i in (62,109,155):p.bench()
 elif i==63:lat([(.06,0),(.09,.15),(.055,.45)],'marble_white');B(0,0,.45,.15,.6,.08,'marble_white')
 elif i==64:g.prism([(0,0),(2.55,0),(2.55,1.5),(1.7,1.5),(1.7,1),(.85,1),(.85,.5),(0,.5)],-.12,.12)
 elif i==65:B(0,0,0,3,.32,.1,'marble_white');rod((-1.5,.16,.05),(1.5,.16,.05),.045,'marble_white')
 elif i in (66,67):
  for x in (-1.2,0,1.2):rod((x,0,0),(x,0,1.1+(x+1.2)*(.5 if i==66 else 0)),.045,'bronze')
  rod((-1.3,0,1.1),(1.3,0,1.1+2.6*(.5 if i==66 else 0)),.06,'bronze')
 elif i==68:g.rail(0,0,0,3);column(-1.6,0);column(1.6,0);B(0,0,3,3.7,.65,.3)
 elif i in (69,120):g.masonry(-1.5,1.5,0,0,2.8,.25)
 elif i==70:column(-1.4,0,3.5);column(1.4,0,3.5);trim(3.6,.8,3.5)
 elif i==72:p.lectern()
 elif i==74:trim(1.7,1.1);B(0,0,.34,1.3,.8,.8);trim(1.8,1.2,1.14)
 elif i==75:trim(.9,.65);g.prism([(-.35,.34),(.35,.34),(.35,1.7),(0,2.0),(-.35,1.7)],-.15,.15,'marble_white')
 elif i in (78,113,167):p.sculpted_table() if i==167 else table(m='marble_white' if i==78 else 'wood')
 elif i in (79,158):p.brazier()
 elif i==80:
  lat([(.3,0),(.3,.12),(.12,.2)],'bronze');rod((0,0,.2),(0,0,3.2),.055,'bronze');rod((-.85,0,3.05),(.85,0,3.05),.035,'bronze')
 elif i==82:p.shield()
 elif i in (83,84):B(0,0,0,1.3 if i==83 else 3.5,.12,.6,'marble_white');trim(1.4 if i==83 else 3.6,.15,.6)
 elif i==85:trim(.9,.9);lat([(.22,.34),(.22,.6),(.18,.65)],'bronze')
 elif i==86:
  lat([(.18,0),(.17,3),(.13,5)],'wood')
  for z in (.15,2.5,4.85):ring(z=z,rx=.19,ry=.19,t=.028,axis='z')
 elif i==87:rod((-.6,0,.3),(.6,0,.3),.075,'wood');ring(-.5,0,.3,.12,.12);ring(.5,0,.3,.12,.12)
 elif i==88:rod((0,0,0),(0,.7,.8),.06,'dark_metal');B(0,0,0,.3,.1,1,'dark_metal');ring(0,.7,.8,.16,.16,axis='z')
 elif i==91:
  for strand in range(3):
   p.sweep([(.018*math.cos(t*.8+strand*math.tau/3),.018*math.sin(t*.8+strand*math.tau/3),3.2-t*.02) for t in range(161)],.013,'mortar',12)
 elif i==92:p.ropes()
 elif i in (93,127):pulley(.7)
 elif i in (94,124):p.velum_winch()
 elif i==95:p.velum_anchor()
 elif i==96:B(0,0,0,.3,.12,.1,'dark_metal');rod((-.18,0,.2),(.18,0,.2),.035,'bronze');rod((0,0,.05),(0,0,.2),.04,'bronze')
 elif i in (97,150):g.masonry(-1.5,1.5,0,0,3,.65)
 elif i==98:B(0,0,0,.7,.7,3);trim(.9,.9,2.7)
 elif i==99:
  for j in range(10):B(-1.35+j*.3,0,.15,.29,3,.15,'wood')
  for y in (-1.2,1.2):B(0,y,0,3,.15,.2,'wood')
 elif i==100:
  for y in (-.8,.8):B(0,y,0,2,.2,.3)
  for x in (-.9,.9):B(x,0,0,.2,1.4,.3)
 elif i in (101,148):g.stair_flight(0,0,2.4,.3,.1875,.1875,8,0)
 elif i==102:
  for x in (-.3,.3):rod((x,0,0),(x,0,3.2),.035,'dark_metal')
  for j in range(11):rod((-.3,0,.15+j*.28),(.3,0,.15+j*.28),.025,'dark_metal')
 elif i in (103,116,131):door(grille=i==116)
 elif i==105:
  for x in (-1.5,1.5):
   for y in (-1.5,1.5):B(x,y,0,.45,.45,2.4)
  for y in (-1.5,1.5):g.arc(0,y,2.4,1.28,.25,.45)
  for x in (-1.5,1.5):g.arc(x,0,2.4,1.28,.25,.45,axis='y')
 elif i in (104,106):
  for y in (-1.5,1.5):g.masonry(-1.5,1.5,y,0,2.4,.45)
  g.vault(-1.5,1.5,0,2.4,1.5)
  if i==106:B(-1.4,0,0,.2,3,2.4)
  if i==105:g.arc(0,0,2.4,1.4,.22,3)
 elif i==107:niche(1.1,.7)
 elif i==108:B(0,0,0,1.1,.15,.85,'marble_white')
 elif i==110:
  for x in (-.5,0,.5):B(x,0,0,.06,.55,1.9,'wood')
  for z in (.04,.85,1.84):B(0,0,z,1.05,.55,.06,'wood')
  B(0,-.25,0,1,.04,1.9,'wood');B(0,.29,0,1,.05,1.9,'wood')
 elif i==111:
  B(0,0,.3,1.2,.08,.12,'wood')
  for x in (-.45,-.15,.15,.45):p.sweep([(x,0,.3),(x,.15,.25),(x,.23,.32),(x,.23,.4)],.018,'bronze')
 elif i==112:p.weapon_rack()
 elif i==114:p.chest()
 elif i==115:p.grille_panel(2.4)
 elif i==117:p.bench();sculpt.cloth(0,0,.56,1.8,.55,12,.06,'burgundy',.035)
 elif i==118:frame(1.2,1.1);B(0,0,0,1.1,.08,1.1,'wood')
 elif i in (119,161):basin()
 elif i==121:table(2.5,2.5,.35)
 elif i==122:
  for x in (-1.3,1.3):
   for y in (-1.3,1.3):B(x,y,0,.18,.18,4,'wood')
  for y in (-1.3,1.3):B(0,y,3.8,2.8,.18,.2,'wood')
 elif i==123:B(0,0,0,.12,.1,3,'dark_metal');B(0,0,0,.3,.2,.08,'dark_metal');B(0,0,2.92,.3,.2,.08,'dark_metal')
 elif i==125:
  lat([(.45,0),(.45,.2),(.3,.3),(.3,.9),(.4,1)],'wood')
  for j in range(4):a=j*math.pi/2;rod((0,0,.9),(1.4*math.cos(a),1.4*math.sin(a),.9),.055,'wood')
 elif i==126:B(0,0,0,.6,.5,.8);ring(z=.95,rx=.15,ry=.18)
 elif i==128:
  for j in range(24):ring(0,0,3.3-j*.135,.075,.11,.018,axis='y' if j%2==0 else 'x')
 elif i in (129,189):B(0,0,0,.25,.08,.2,'bronze');rod((-.2,.07,.1),(.2,.07,.1),.025,'dark_metal')
 elif i in (130,153):
  for x in (-1,1):B(x,0,0,.12,.6,.1,'wood');B(x,0,0,.1,.1,1.1,'wood')
  for z in (.4,.9):B(0,0,z,2.2,.07,.12,'wood')
 elif i==132:p.cart()
 elif i in (133,134,135):channel(i!=133)
 elif i in (136,143):
  for j in range(10):B(-.45+j*.1,0,0,.04,.6,.035,'dark_metal')
  for y in (-.28,.28):B(0,y,0,1,.04,.04,'dark_metal')
 elif i==137:
  for y in (-.5,.5):B(0,y,0,1.2,.15,.15)
  for x in (-.525,.525):B(x,0,0,.15,.85,.15)
  B(0,0,.1,.85,.85,.08,'dark_metal');ring(z=.22,rx=.08,ry=.08)
 elif i==138:basin(.7,.7,.25)
 elif i==139:pipe([(0,0,0),(0,0,2)])
 elif i==140:pipe([(math.sin(j*math.pi/40)*.7,0,.7*(1-math.cos(j*math.pi/40))) for j in range(21)])
 elif i==141:pipe([(-.7,0,.7),(.7,0,.7)]);pipe([(0,0,0),(0,0,.7)])
 elif i==142:basin(3,3,2)
 elif i==144:channel();B(-1.35,0,.25,.3,.8,.3)
 elif i==145:g.dressed_block(0,0,0,.3,.3,.1,walkable=True)
 elif i==146:sculpt.paving(-1.5,1.5,-1.5,1.5,0)
 elif i in (147,151,175,178):B(0,0,0,3,.35,.25);B(0,0,.25,3,.4,.08,'marble_white')
 elif i==149:g.prism([(-1.5,0),(1.5,0),(1.5,.7),(-1.5,.05)],-1.5,1.5)
 elif i==152:lat([(.2,0),(.2,.12),(.15,.2),(.15,.85),(.1,.98)],'stone_cream')
 elif i==154:rod((0,0,0),(0,0,2.4),.06,'wood');B(.3,0,1.9,.9,.06,.35,'wood')
 elif i==157:p.wall_lamp()
 elif i==159:p.loge_lantern();ring(z=1.15,rx=.12,ry=.17)
 elif i==160:p.sweep([(0,0,0),(0,.45,.45),(0,.65,.4),(0,.65,.3)],.035,'dark_metal');B(0,0,0,.16,.06,.5,'dark_metal')
 elif i==162:p.amphora(0,0)
 elif i==163:p.barrel()
 elif i==164:p.crate(0,0,0)
 elif i==165:
  lat([(.25,0),(.38,.12),(.42,.4),(.3,.65),(.15,.75),(.12,.8)],'mortar')
  ring(z=.75,rx=.15,ry=.15,t=.018,m='mortar',axis='z')
 elif i==166:
  for j in range(12):ring(z=.08+j*.035,rx=.3,ry=.22,t=.018,m='wood',axis='z')
  for a in range(20):t=a*math.tau/20;rod((.3*math.cos(t),.22*math.sin(t),0),(.3*math.cos(t),.22*math.sin(t),.5),.012,'wood')
  B(0,0,0,.55,.4,.03,'wood');ring(z=.48,rx=.3,ry=.3,t=.025,m='wood',axis='y')
 elif i==168:table(.45,.45,.55)
 elif i==169:trim(.4,.8)
 elif i==170:trim(1.5,.8);p.transform(lambda:trim(1.5,.8),(.35,.35,0),angle=math.pi/2)
 elif i==171:
  for j in range(20):
   a=j/20;b=(j+1)/20
   pts=[((12+3*t+off)*math.sin(t*math.pi/12),(12+3*t+off)*math.cos(t*math.pi/12)-12,z) for z in (0,.3) for t,off in [(a,0),(a,.6),(b,.6),(b,0)]]
   g.solid(pts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
 elif i==172:g.prism([(-.1,0),(.1,0),(.04,3),(-.04,3)],-.3,.3)
 elif i in (173,174):g.arc(0,0,0,1.5,.3,.3)
 elif i==176:frame(1.6,2.8,'stone_cream')
 elif i==177:B(0,0,0,3,.55,.45)
 elif i==179:B(0,0,0,3,.04,.05,'mortar')
 elif i==180:B(0,0,0,.6,.3,.08,'bronze')
 elif i in (181,183):g.prism([(-.65,0),(.65,0),(.65,.28),(.48,.34),(.42,.45),(-.65,.45)],-.4,.4)
 elif i==182:trim(1.3,.8);g.prism([(.65,0),(.85,.1),(.65,.3)],-.4,.4)
 elif i==184:
  sculpt.slab([(-1,-1),(.1,-1),(-.05,0),(.15,1),(-1,1)],0,.18)
  sculpt.slab([(.13,-1),(1,-1),(1,1),(.18,1),(-.02,0)],0,.18)
 elif i==185:
  for j in range(12):p.transform(lambda:g.dressed_block(0,0,0,.18+(j%3)*.12,.25,.15),((j%4)*.3,(j//4)*.25,0),angle=j*.7)  # noqa: B023
 elif i==186:B(0,0,0,2.2,.22,.055,'wood')
 elif i==187:B(0,0,0,.65,.08,.04,'dark_metal');p.rivets(-.25,.25,.06,.02,5)
 elif i==188:ring(z=.15,rx=.1,ry=.14,t=.018,m='bronze');B(0,-.03,.1,.08,.04,.1,'bronze')
 elif i==190:lat([(.012,0),(.012,.04),(.035,.04),(.035,.055),(.02,.068)],'bronze')
 elif i==191:B(0,0,0,.8,.2,.04,'wood');p.rivets(-.3,.3,.11,.03,3)
 else:raise ValueError('No geometry '+str(i))

def cloth(i):
 """Simulation rest shape and attachment weights; source retains Blender Cloth."""
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 w,h=(3,2) if i in (71,89) else (1.3,2.2) if i==81 else (2,.25) if i==90 else (.85,1.1)
 nx,ny=48,64 if i in (81,192) else 40;verts=[];faces=[];pins=[]
 for j in range(ny+1):
  v=j/ny
  for k in range(nx+1):
   u=k/nx;x=(u-.5)*w
   if i in (71,89):co=(x,(v-.5)*h,2.5-.13*math.sin(u*math.pi)*math.sin(v*math.pi));pin=(k in (0,nx) and j in (0,ny))
   else:co=(x,.035*math.sin(u*math.pi*12)*v,2.6-v*h);pin=j==0
   verts.append(co);pins.append(pin)
 for j in range(ny):
  for k in range(nx):
   if i==192 and j>ny*.7 and (k%11 in (0,1)):continue
   a=j*(nx+1)+k;faces.append((a,a+1,a+nx+2,a+nx+1))
 mesh=bpy.data.meshes.new('ClothSurface');mesh.from_pydata(verts,[],faces);mesh.materials.append(materials[g.NAMES.index('burgundy')]);mesh.update()
 ob=bpy.data.objects.new(f'SK_AOF_{i:03d}',mesh);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
 uv=mesh.uv_layers.new(name='UV0')
 for face in mesh.polygons:
  face.use_smooth=True
  for li in face.loop_indices:
   vi=mesh.loops[li].vertex_index;uv.data[li].uv=((vi%(nx+1))/nx*w/2,(vi//(nx+1))/ny*h/2)
 color=mesh.color_attributes.new(name='COLOR_0',type='BYTE_COLOR',domain='POINT')
 for j,yes in enumerate(pins):color.data[j].color=(0 if yes else 1,0,0,1)
 group=ob.vertex_groups.new(name='Attachment');group.add([j for j,v in enumerate(pins) if v],1,'REPLACE')
 mod=ob.modifiers.new('Blender cloth rest drape','CLOTH');mod.settings.quality=6;mod.settings.mass=.35;mod.settings.vertex_group_mass=group.name;mod.settings.tension_stiffness=30;mod.settings.compression_stiffness=30;mod.settings.shear_stiffness=20;mod.settings.bending_stiffness=.5;mod.collision_settings.use_self_collision=True;mod.collision_settings.self_distance_min=.006
 scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=35
 for f in range(1,36):scene.frame_set(f)
 deps=bpy.context.evaluated_depsgraph_get();evaluated=ob.evaluated_get(deps);rest=[v.co.copy() for v in evaluated.data.vertices]
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'AOF_{i:03d}_cloth_source.blend'))
 ob.modifiers.remove(mod)
 for v,co in zip(mesh.vertices,rest):v.co=co
 arm=bpy.data.armatures.new('Attachments');rig=bpy.data.objects.new('Attachments',arm);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;ob.select_set(False);rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bone=arm.edit_bones.new('root');bone.head=(0,0,2.6);bone.tail=(0,0,2.7);bpy.ops.object.mode_set(mode='OBJECT')
 vg=ob.vertex_groups.new(name='root');vg.add(list(range(len(mesh.vertices))),1,'REPLACE');mod=ob.modifiers.new('Skin','ARMATURE');mod.object=rig;ob.parent=rig
 ob.select_set(True);rig.select_set(True)
 export_skin(i,ob,rig)
 return {'id':f'SK_AOF_{i:03d}','file':f'SK_AOF_{i:03d}.glb','catalogueId':i,'label':LABELS[i],'physics':'cloth','pins':sum(pins),'vertices':len(verts),'blenderDrapeFrames':35,'materials':['burgundy'],'sourceBlend':f'AOF_{i:03d}_cloth_source.blend','maxDistanceCm':400}

def export_skin(i,ob,rig):
 bpy.ops.export_scene.gltf(filepath=str(OUT/f'SK_AOF_{i:03d}.glb'),export_format='GLB',use_selection=True,export_yup=True,export_skins=True,export_animations=False,export_vertex_color='NAME',export_vertex_color_name='COLOR_0',export_tangents=True)

def rig_static(i,row):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(OUT/row['file']));meshes=[o for o in bpy.context.selected_objects if o.type=='MESH']
 bpy.ops.object.select_all(action='DESELECT')
 for o in meshes:o.select_set(True)
 bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();ob=bpy.context.object;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 lo=[min(v.co[k] for v in ob.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in ob.data.vertices) for k in range(3)]
 # Root is an explicit support; moving-bone origins are authored hinge points.
 mode=rig_modes[i];points=[('root',(0,0,hi[2]+.08),-1)]
 if i in (91,128):
  count=24 if i==128 else 20
  for j in range(count):points.append((f'link_{j:02d}',(0,0,hi[2]-j*(hi[2]-lo[2])/count),j))
 elif mode=='wheel':
  points=[('root',(0,0,0),-1)]+[(f'wheel_{j}',(x,y,.32),0) for j,(x,y) in enumerate([(-.61,-.43),(.61,-.43),(-.61,.43),(.61,.43)])]
 elif i==46:
  points += [('left',(lo[0],0,1.5),0),('right',(hi[0],0,1.5),0)]
 else:
  hinge=(lo[0]+.1,0,(lo[2]+hi[2])/2) if i in (46,103,110,116,118,131) else (0,lo[1]+.04,hi[2]*.65) if i in (48,114,137) else (0,0,hi[2]-.1)
  if i in (93,127):hinge=(0,0,.7)
  if i in (94,124):hinge=(0,0,.56)
  if i==125:hinge=(0,0,.2)
  if i==114:hinge=(0,.30,.60)
  points.append(('moving',hinge,0))
 arm=bpy.data.armatures.new(f'Rig_{i:03d}');rig=bpy.data.objects.new(f'Rig_{i:03d}',arm);bpy.context.collection.objects.link(rig);ob.select_set(False);rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for name,xyz,parent in points:
  bone=arm.edit_bones.new(name);bone.head=xyz;axis=(.08,0,0) if i in (48,94,114,124,129,132,137,188,189) else (0,.08,0) if i in (93,127) else (0,0,.08);bone.tail=Vector(xyz)+Vector(axis);bone.parent=arm.edit_bones[points[parent][0]] if parent>=0 else None
 bpy.ops.object.mode_set(mode='OBJECT');groups=[ob.vertex_groups.new(name=x[0]) for x in points]
 # Rigid islands stay intact: no bending of a metal link or a wood board.
 adjacency=[[] for _ in ob.data.vertices]
 for edge in ob.data.edges:a,b=edge.vertices;adjacency[a].append(b);adjacency[b].append(a)
 remaining=set(range(len(adjacency)))
 if i==91:
  for v in ob.data.vertices:
   t=min(len(points)-2.001,max(0,(hi[2]-v.co.z)/max(.001,hi[2]-lo[2])*(len(points)-2)))
   a=int(t)+1;f=t-int(t);groups[a].add([v.index],1-f,'REPLACE');groups[a+1].add([v.index],f,'REPLACE')
  remaining.clear()
 while remaining:
  first=remaining.pop();island=[first]
  for v in island:
   for n in adjacency[v]:
    if n in remaining:remaining.remove(n);island.append(n)
  center=sum((ob.data.vertices[v].co for v in island),Vector())/len(island)
  if i in (91,128):idx=1+min(len(points)-2,max(0,int((hi[2]-center.z)/max(.001,hi[2]-lo[2])*(len(points)-1))))
  elif mode=='wheel':idx=min(range(1,len(points)),key=lambda j:(center-Vector(points[j][1])).length) if center.z<.66 and abs(center.x)>.53 else 0
  elif i==46:idx=1 if center.x<0 else 2
  elif i in (93,127):idx=0 if abs(center.x)>.34 else 1
  elif i in (94,124):idx=0 if center.z<.18 or (.33<abs(center.x)<.46 and center.z<.81) else 1
  elif i==125:idx=0 if center.z<.2 else 1
  elif i in (129,189):idx=1 if center.y<-.04 else 0
  elif i in (114,137,48):idx=1 if center.z>hi[2]*.64 else 0
  elif i in (103,110,116,118,131,46):idx=1 if lo[0]+.16<center.x<hi[0]-.16 and center.z<hi[2]-.16 else 0
  else:idx=1
  groups[idx].add(island,1,'REPLACE')
 ob.parent=rig;mod=ob.modifiers.new('Articulated skin','ARMATURE');mod.object=rig;ob.select_set(True);rig.select_set(True)
 export_skin(i,ob,rig);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'AOF_{i:03d}_rig_source.blend'))
 row.update({'skeletalFile':f'SK_AOF_{i:03d}.glb','bones':len(points),'physics':mode,'anchorRoot':mode!='wheel','sourceBlend':f'AOF_{i:03d}_rig_source.blend'})

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
only=set(map(int,sys.argv[sys.argv.index('--')+1:])) if '--' in sys.argv else None
old={r['catalogueId']:r for r in json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))['meshes']} if (OUT/'manifest.json').exists() else {}
for i in [46,47,48]+list(range(49,193)):
 if only and i not in only:
  if i in old:records.append(old[i])
  continue
 if i in (60,76):
  master=json.loads((ROOT/'Source/Elements/Assets/Master/manifest.json').read_text(encoding='utf-8'))
  statues=[r for r in master['pieces'] if r['family']=='Statues']
  records.append({'id':f'REF_AOF_{i:03d}','catalogueId':i,'label':LABELS[i],'physics':'static','referenceAssets':[r['asset'] for r in statues[:1 if i==60 else 14]],'note':'Existing approved master statues, no invented deity.'});continue
 if i in (46,47,48):
  import shutil
  source=ROOT/'Source/Elements/Assets/Built/aof-pilot-001-048'
  base=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
  row=dict(next(r for r in base['meshes'] if r['catalogueId']==i));shutil.copy2(source/row['file'],OUT/row['file']);rig_static(i,row)
 elif i in cloth_ids:row=cloth(i)
 else:
  name=f'SM_AOF_{i:03d}';g.export_piece(name,lambda i=i:build(i),OUT,materials,clean_degenerate=True)
  row=dict(g.PIECES[-1]);row.update({'catalogueId':i,'label':LABELS[i],'physics':'rigid' if i in loose else 'static'})
  if i in rig_modes:rig_static(i,row)
 row['sha256']=hashlib.sha256((OUT/row['file']).read_bytes()).hexdigest();records.append(row)
 (OUT/'manifest.json').write_text(json.dumps({'version':1,'uvRepeatMetres':2,'meshes':records,'generator':'scripts/assetsGeneration/build_aof_extension.py'},ensure_ascii=False,indent=2),encoding='utf-8')
 print('EXTENSION_READY',i,row['physics'],flush=True)
(OUT/'manifest.json').write_text(json.dumps({'version':1,'uvRepeatMetres':2,'meshes':records,'generator':'scripts/assetsGeneration/build_aof_extension.py'},ensure_ascii=False,indent=2),encoding='utf-8')
print('AOF_EXTENSION_COMPLETE',len(records),flush=True)
