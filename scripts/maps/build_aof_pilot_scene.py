"""Import the 001-048 pilot, create materials and three isolated review maps.
Outputs /Game/ArenaFatePilot001048 and /Game/Maps/Levels/essai/aof-001-048-*.
Reuses existing physical PBR source maps without changing the approved Arena.
"""
import json
import math
import sys
import hashlib
from pathlib import Path
import unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
sys.path[:0]=[str(ROOT/'scripts/maps'),str(ROOT/'scripts/assetsGeneration')]
import build_level as scene  # noqa: E402
import jadg_map  # noqa: E402
import import_scenery_unreal as scenery  # noqa: E402
SOURCE=ROOT/'Source/Elements/Assets/Built/aof-pilot-001-048'
DEST='/Game/ArenaFatePilot001048'
REPORT=ROOT/'Saved/Jadg/aof-pilot-001-048';REPORT.mkdir(parents=True,exist_ok=True)
E=unreal.EditorAssetLibrary;ML=unreal.MaterialEditingLibrary;AT=unreal.AssetToolsHelpers.get_asset_tools()
doc=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
REPORT_DATA={'scope':'001-048','references':['https://www.youtube.com/watch?v=WUtl1K9Pn7k&t=137s','https://www.youtube.com/watch?v=k-zMkzmduqI&t=12723s'],'materialImplementation':'Independent pilot graph inspired by parameterized master-material workflow; not the downloaded Sensei package. Three-layer height painting and tessellation deferred.','maps':[],'meshes':[],'materials':[],'acceptance':'Awaiting user visual review; not accepted production art.'}
def save(asset):
 if not E.save_loaded_asset(asset,only_if_is_dirty=False):raise RuntimeError('Save failed '+asset.get_path_name())
def new(name,folder,cls,factory):
 path=folder+'/'+name
 return E.load_asset(path) if E.does_asset_exist(path) else AT.create_asset(name,folder,cls,factory)
def load_textures():
 base=ROOT/'Source/Elements/Assets/Built/arena-witness-materials'
 source=json.loads((base/'manifest.json').read_text(encoding='utf-8'))
 result={}
 for name in ('stone_cream','marble_white','dark_metal','wood','mortar','bronze'):
  result[name]={}
  for role in ('baseColor','normal','orm'):
   entry=source['styles']['painted'][name][role];p=base/entry['file'];content=p.read_bytes()
   digest=hashlib.sha256(content).hexdigest()
   if digest!=entry['sha256']:raise RuntimeError('Source hash mismatch '+str(p))
   path=DEST+'/Textures/T_'+name+'_'+role
   tex=E.load_asset(path) if E.does_asset_exist(path) else scenery.import_image(content,'png',path,role)
   result[name][role]=tex
   if role=='normal' and not tex.get_editor_property('flip_green_channel'):raise RuntimeError('Normal convention mismatch')
 return result
def parent(textures):
 mat=new('M_AOF_Pilot',DEST+'/Materials',unreal.Material,unreal.MaterialFactoryNew())
 ML.delete_all_material_expressions(mat)
 pos=[0]
 def node(cls):
  pos[0]+=1;return ML.create_material_expression(mat,cls,-1800+(pos[0]%8)*230,(pos[0]//8)*180)
 def con(a,p,b,q):
  if not ML.connect_material_expressions(a,p,b,q):raise RuntimeError('Graph connection '+a.get_name()+' -> '+b.get_name()+'/'+q)
 def prop(a,p,kind):
  if not ML.connect_material_property(a,p,kind):raise RuntimeError('Material property failed')
 def scalar(name,value,group):
  n=node(unreal.MaterialExpressionScalarParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',value);n.set_editor_property('group',group);return n
 def vector(name,val,group):
  n=node(unreal.MaterialExpressionVectorParameter);n.set_editor_property('parameter_name',name);n.set_editor_property('default_value',unreal.LinearColor(*val));n.set_editor_property('group',group);return n
 def const(v):n=node(unreal.MaterialExpressionConstant);n.set_editor_property('r',v);return n
 def op(cls,a,b,ap='',bp=''):
  n=node(cls);con(a,ap,n,'A');con(b,bp,n,'B');return n
 def lerp(a,b,t,ap='',bp='',tp=''):
  n=node(unreal.MaterialExpressionLinearInterpolate);con(a,ap,n,'A');con(b,bp,n,'B');con(t,tp,n,'Alpha');return n
 uv=node(unreal.MaterialExpressionTextureCoordinate)
 tiling=scalar('Tiling',1,'01 UV');scaled=op(unreal.MaterialExpressionMultiply,uv,tiling)
 offset=node(unreal.MaterialExpressionAppendVector);con(scalar('OffsetU',0,'01 UV'),'',offset,'A');con(scalar('OffsetV',0,'01 UV'),'',offset,'B')
 coords=op(unreal.MaterialExpressionAdd,scaled,offset)
 samples={}
 for role,name in [('baseColor','BaseColor'),('normal','Normal'),('orm','ORM')]:
  n=node(unreal.MaterialExpressionTextureSampleParameter2D);n.set_editor_property('parameter_name',name);n.set_editor_property('texture',textures[role]);n.set_editor_property('group','00 Maps')
  n.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='baseColor' else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
  con(coords,'',n,'UVs');samples[role]=n
 tint=vector('Tint',(1,1,1,1),'02 Colour');colour=op(unreal.MaterialExpressionMultiply,samples['baseColor'],tint,'RGB','RGB')
 colour=op(unreal.MaterialExpressionMultiply,colour,scalar('ColourGain',1,'02 Colour'))
 # Thin dust and wetness are deliberately bounded first-loop controls, not the
 # complete 3-layer height-painting system shown by Sensei.
 dust=scalar('DustAmount',0,'05 Surface');dustc=vector('DustColour',(.55,.45,.31,1),'05 Surface')
 colour=lerp(colour,dustc,dust,bp='RGB')
 wet=scalar('Wetness',0,'05 Surface');wetcolour=op(unreal.MaterialExpressionMultiply,colour,scalar('WetDarkening',.65,'05 Surface'))
 colour=lerp(colour,wetcolour,wet);prop(colour,'',unreal.MaterialProperty.MP_BASE_COLOR)
 rough=op(unreal.MaterialExpressionMultiply,samples['orm'],scalar('RoughnessScale',1,'03 Physical'),'G')
 rough=op(unreal.MaterialExpressionAdd,rough,scalar('RoughnessBias',0,'03 Physical'))
 rough=lerp(rough,scalar('DustRoughness',.95,'05 Surface'),dust)
 rough=lerp(rough,scalar('WetRoughness',.25,'05 Surface'),wet)
 clamp=node(unreal.MaterialExpressionClamp);con(rough,'',clamp,'');con(scalar('RoughnessMin',.05,'03 Physical'),'',clamp,'Min');con(scalar('RoughnessMax',1,'03 Physical'),'',clamp,'Max');prop(clamp,'',unreal.MaterialProperty.MP_ROUGHNESS)
 metal=op(unreal.MaterialExpressionMultiply,samples['orm'],scalar('MetallicScale',1,'03 Physical'),'B');prop(metal,'',unreal.MaterialProperty.MP_METALLIC)
 ao=lerp(const(1),samples['orm'],scalar('AOStrength',.6,'03 Physical'),bp='R');prop(ao,'',unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
 strength=scalar('NormalStrength',.5,'04 Normal');flat=vector('FlatNormal',(0,0,1,1),'04 Normal')
 normal=lerp(flat,samples['normal'],strength,ap='RGB',bp='RGB');norm=node(unreal.MaterialExpressionNormalize);con(normal,'',norm,'');prop(norm,'',unreal.MaterialProperty.MP_NORMAL)
 prop(scalar('Specular',.35,'03 Physical'),'',unreal.MaterialProperty.MP_SPECULAR)
 mat.set_editor_property('two_sided',False);mat.set_editor_property('used_with_instanced_static_meshes',True);mat.set_editor_property('used_with_nanite',True)
 ML.recompile_material(mat);save(mat);return mat
def materials():
 keys=('stone_cream','marble_white','dark_metal','wood','mortar','bronze')
 result={k:E.load_asset('/Game/Bibliotheque/Materiaux/AOF/Instances/MI_AOF_'+k) for k in keys}
 if any(v is None for v in result.values()):raise RuntimeError('Run build_aof_master_v3.py first')
 gray=scene.flat_material(DEST+'/Materials/M_Clay',unreal.LinearColor(.42,.42,.42,1),.78)
 report=json.loads((ROOT/'Saved/Jadg/aof-master-v3/report.json').read_text())
 REPORT_DATA['materials']=[r for r in report['instances'] if r['name'] in keys]
 REPORT_DATA['materialImplementation']='AOF V3 masters based on supplied Sensei, original CC0 4K maps, dedicated layered presets.'
 return result,gray

def import_meshes(mats):
 meshes={}
 for row in doc['meshes']:
  i=row['catalogueId'];p=SOURCE/row['file'];name=row['id'];path=DEST+'/Meshes/'+name
  if hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Mesh hash mismatch '+name)
  if E.does_asset_exist(path) and E.get_metadata_tag(E.load_asset(path),'AOFSourceHash')==row['sha256']:mesh=E.load_asset(path)
  else:mesh=scenery.import_glb(p,DEST+'/Import',DEST+'/Import/'+name,path)
  scenery.finish(mesh)
  slots=[]
  for index,slot in enumerate(mesh.get_editor_property('static_materials')):
   key=str(slot.material_slot_name)
   # Interchange can append a numeric suffix to Blender's material names.
   match=next((x for x in mats if key==x or key.startswith(x+'.') or key.startswith(x+'_')),None)
   if match is None:
    old=slot.material_interface.get_name() if slot.material_interface else ''
    match=next((x for x in mats if x in old),None)
   if match is None:raise RuntimeError('Unmapped material slot '+name+'/'+key)
   mesh.set_material(index,mats[match]);slots.append(match)
  E.set_metadata_tag(mesh,'AOFSourceHash',row['sha256']);E.set_metadata_tag(mesh,'AOFCatalogueId',f'{i:03d}');save(mesh)
  box=mesh.get_bounding_box();dim=[(box.max.x-box.min.x)/100,(box.max.y-box.min.y)/100,(box.max.z-box.min.z)/100]
  expected=[row['boundsBlender'][1][j]-row['boundsBlender'][0][j] for j in range(3)]
  if any(abs(a-b)>.03 for a,b in zip(dim,expected)):raise RuntimeError('Scale mismatch '+name+str(dim)+str(expected))
  meshes[i]=mesh;REPORT_DATA['meshes'].append({'id':i,'path':mesh.get_path_name(),'dimensionsMetres':dim,'trianglesSource':row['triangles'],'slots':slots,'nanite':mesh.get_editor_property('nanite_settings').enabled,'collision':str(mesh.get_editor_property('body_setup').get_editor_property('collision_trace_flag'))})
 return meshes
def create_maps(meshes,gray,mats):
 fixtures=scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix());frame=scene.Frame(scene.FIXTURE_ASSETS/scene.FRAME_REFERENCE,fixtures.static_mesh(scene.FRAME_REFERENCE))
 cube=E.load_asset('/Engine/BasicShapes/Cube')
 for variant in ('gris','materiaux','assemblage'):
  world=unreal.EditorLoadingAndSavingUtils.new_blank_map(False);level=scene.Level(world);count={i:0 for i in meshes}
  def place(i,x,y,z=0,yaw=0,label=None,clay=False):
   a=level.spawn(meshes[i],frame.map_point([x,y,z]),frame.rotation(yaw),label or f'AOF-{i:03d}-{count[i]:03d}',f'AOF/{i:03d}');count[i]+=1  # noqa: B023
   if clay:
    for slot in range(len(meshes[i].get_editor_property('static_materials'))):a.static_mesh_component.set_material(slot,gray)
   return a
  def cub(name,x,y,z,w,d,h,mat=gray):
   a=level.spawn(cube,frame.map_point([x,y,z]),unreal.Rotator(),name,'Atelier',unreal.Vector(w,d,h));a.static_mesh_component.set_material(0,mat);return a  # noqa: B023
  def label(s,x,y,z=.03):
   a=level.spawn(unreal.TextRenderActor,frame.map_point([x,y,z]),unreal.Rotator(-90,0,0),s,'Etiquettes')  # noqa: B023
   comp=a.get_component_by_class(unreal.TextRenderComponent);comp.set_text(s);comp.set_world_size(32);comp.set_text_render_color(unreal.Color(45,45,45,255))
  shots=[]
  if variant!='assemblage':
   for row in doc['meshes']:
    i=row['catalogueId'];col=(i-1)%6;line=(i-1)//6;x=col*7;y=line*8
    low,high=row['boundsBlender'];cx=(low[0]+high[0])/2;cy=-(low[1]+high[1])/2
    place(i,x-cx,y-cy,0,clay=variant=='gris');label(f'{i:03d}',x-1.4,y-3)
   cub('Sol atelier',17.5,28,-.25,46,68,.5)
   shots=[{'id':'ensemble','target':[17.5,28,1],'heading':345,'pitch':60,'distance':90}]
   for j in range(8):shots.append({'id':f'famille-{chr(65+j)}','target':[17.5,j*8,1.5],'heading':0,'pitch':32,'distance':44})
   if variant=='materiaux':
    shots.extend([{'id':'detail-pierre','target':[0,8,1.5],'heading':165,'pitch':28,'distance':7},{'id':'detail-bois','target':[21,56,1.8],'heading':165,'pitch':28,'distance':7},{'id':'detail-metal','target':[28,56,1.8],'heading':165,'pitch':28,'distance':7},{'id':'detail-marbre','target':[21,24,1.5],'heading':165,'pitch':28,'distance':7}])
  else:
   cub('Sol atelier',0,0,-.45,95,80,.5)
   # Exact 24 x 15-degree closure, using the same local pivot as source geometry.
   for k in range(24):
    a=k*math.pi/12
    # Clockwise map yaw maps (sin(t),cos(t)) to (sin(t+a),cos(t+a)).
    ox=R*math.sin(a);oy=R*math.cos(a)
    for i,z in ((4,0),(26,.2)):
     place(i,ox,oy,z,yaw=k*15)
   # Three joined arcade bays and walkable stair/landing witness.
   for j in range(3):
    x=-5.4+j*3.6;y=-24
    place(45,x,y)
    place(3,x,y+1.5,-.2)
   place(46,-5.4,-24);place(47,1.8,-24)
   place(27,7,-27);place(29,7,-23.85,1.3);place(37,7,-23.1,1.5)
   place(34,13,-24);place(33,13,-21,3);place(31,13,-18,3)
   for x in (11.25,14.75):place(7,x,-18,0,yaw=90)
   place(12,-13,-24);place(9,-18,-24);place(10,-23,-24)
   # Dedicated copied plane: never change an Engine asset.
   pp=DEST+'/Meshes/SM_SurfaceWitness'
   preview=E.load_asset(pp) if E.does_asset_exist(pp) else E.duplicate_asset('/Engine/BasicShapes/Plane',pp)
   scenery.finish(preview);E.save_loaded_asset(preview,False)
   pa=level.spawn(preview,frame.map_point([-30,10,0]),unreal.Rotator(),'Temoin deplacement pierre','Atelier',unreal.Vector(5,5,1))
   pa.static_mesh_component.set_material(0,E.load_asset(DEST+'/Materials/MI_stone_displacement'))
   # Joined 3x3 floor patch: exact edge contact, useful for UV continuity.
   for x in range(3):
    for y in range(3):place(3,22+x*3,-9+y*3,0)
   for i,x,y,z in [(1,-23,-15,0),(13,-23,-15,.6),(23,-18,-15,0),(22,-18,-15,.4),(24,-18,-15,3.4),(48,-13,-15,0),(35,-8,-15,0)]:place(i,x,y,z)
   shots=[{'id':'boucle','target':[0,0,1],'heading':330,'pitch':48,'distance':65},{'id':'raccords','target':[0,-23,2],'heading':15,'pitch':32,'distance':32},{'id':'galerie','target':[12,-19,2],'heading':290,'pitch':30,'distance':22},{'id':'sols','target':[25,-6,.3],'heading':320,'pitch':45,'distance':16}]
  config={'format':jadg_map.FORMAT,'version':jadg_map.VERSION,'name':'AOF pilot '+variant,'width':80,'height':80,'origin':[-60,-60],'storeys':[{'name':'sol','z':0}],'nextEntityId':1,'tiles':[{'x':40,'y':40,'type':'entry'}],'entities':[],'daylight':jadg_map.DAYLIGHT,'lighting':{'sunScale':1.65,'ambientScale':.45,'skyLuminance':1.5,'exposureBias':0},'shots':shots,'hours':['12:00','22:00']}
  # Lighting helpers use only shared existing resources; ground is local above.
  scene.place_sky(level,config,frame);scene.place_shots(level,config,frame)
  for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
   if isinstance(actor,unreal.SkyLight):
    sc=actor.light_component
    sc.set_editor_property('source_type',unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sc.set_editor_property('cubemap',unreal.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap.DaylightAmbientCubemap'))
    sc.set_editor_property('real_time_capture',False)
  for x,y in [(-15,-24),(0,-24),(15,-24),(0,10),(28,25)]:
   lamp=level.spawn(unreal.PointLight,frame.map_point([x,y,5]),unreal.Rotator(),'Lampe atelier','Eclairage')
   lamp.light_component.set_mobility(unreal.ComponentMobility.MOVABLE);lamp.light_component.set_editor_property('intensity',900.);lamp.light_component.set_editor_property('attenuation_radius',2200.);lamp.tags=['JadgLamp']
  world.get_world_settings().set_editor_property('default_game_mode',scene.game_class('JadgGameMode'))
  package='/Game/Maps/Levels/essai/aof-001-048-'+variant
  if not unreal.EditorLoadingAndSavingUtils.save_map(world,package):raise RuntimeError('Map save failed')
  (REPORT/(variant+'.json')).write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
  if variant!='assemblage' and any(v!=1 for v in count.values()):raise RuntimeError('Gallery missing/duplicate ID')
  REPORT_DATA['maps'].append({'package':package,'instancesById':count,'shots':[s['id'] for s in shots]})
R=12.
mats,gray=materials();meshes=import_meshes(mats);create_maps(meshes,gray,mats)
(REPORT/'build.json').write_text(json.dumps(REPORT_DATA,ensure_ascii=False,indent=2),encoding='utf-8')
unreal.log('AOF_PILOT_COMPLETE 48 meshes, 6 PBR instances, 3 maps')






