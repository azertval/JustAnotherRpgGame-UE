"""Editable Single Layer Water for the existing Capitale water surfaces."""
import unreal as u
import json
from pathlib import Path
P=Path(u.Paths.project_dir()).resolve();E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary;AT=u.AssetToolsHelpers.get_asset_tools()
root='/Game/Capitale/Ressources/Eau'
def asset(name,cls,factory):
 return E.load_asset(root+'/'+name) if E.does_asset_exist(root+'/'+name) else AT.create_asset(name,root,cls,factory())
mat=asset('M_Eau_Capitale',u.Material,u.MaterialFactoryNew)
M.delete_all_material_expressions(mat)
mat.set_editor_property('used_with_instanced_static_meshes',True);mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER);mat.set_editor_property('two_sided',True)
count=0
def node(kind,**props):
 global count
 count+=1;n=M.create_material_expression(mat,getattr(u,'MaterialExpression'+kind),-1800+(count%9)*200,(count//9)*240)
 for k,v in props.items():n.set_editor_property(k,v)
 return n
def link(a,b,pin='',out=''):
 assert M.connect_material_expressions(a,out,b,pin),(b.get_name(),pin)
def scalar(name,value):return node('ScalarParameter',parameter_name=name,default_value=value)
def vector(name,v):return node('VectorParameter',parameter_name=name,default_value=u.LinearColor(*v,1))
def custom(code,inputs,size=1):
 pins=[]
 for k in inputs:p=u.CustomInput();p.set_editor_property('input_name',k);pins.append(p)
 n=node('Custom',code=code,output_type=getattr(u.CustomMaterialOutputType,'CMOT_FLOAT'+str(size)),inputs=pins)
 for k,v in inputs.items():link(v,n,k)
 return n
def rgb(n):
 c=node('ComponentMask',r=True,g=True,b=True);link(n,c);return c
def output(n,property):assert M.connect_material_property(n,'',getattr(u.MaterialProperty,'MP_'+property))
wp=node('WorldPosition');time=node('Time');speed=scalar('Vitesse_Courant',1.)
wave=E.load_asset('/Game/Capitale/Ressources/T_Vagues_N');assert wave
normals=[]
for i,period in enumerate([650.,95.]):
 uv=custom('float2 q=P.xy/Size; return '+('q+float2(.018,.011)*T*Speed;' if i==0 else 'float2(-q.y,q.x)+float2(-.038,.021)*T*Speed;'),{'P':wp,'Size':scalar('Vagues_TailleCm_'+str(i),period),'T':time,'Speed':speed},2)
 n=node('TextureSampleParameter2D',parameter_name='Vagues_Normale',texture=wave,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL,sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS);link(uv,n,'UVs');normals.append(rgb(n))
# Actual screen-space water thickness; supports Single Layer Water, including shallow banks.
depth=node('SceneDepthWithoutWater');pixel=node('PixelDepth')
thickness=custom('return max(D-P,0);',{'D':depth,'P':pixel})
normal=custom('float2 b=float2(B.y,-B.x);float shallow=smoothstep(0,120,D);return normalize(float3((A.xy*.65+b*.35)*Force*lerp(.35,1,shallow),1));',{'A':normals[0],'B':normals[1],'Force':scalar('Vagues_Force',0.65),'D':thickness},3)
output(normal,'NORMAL')
foam=custom('float edge=1-smoothstep(0,Width,D);float n=sin(P.x*.043+sin(P.y*.029)+T*.7)*sin(P.y*.051-T*.5);return edge*smoothstep(-.25,.65,n)*Force;',{'P':wp,'T':time,'D':thickness,'Width':scalar('Ecume_LargeurCm',65),'Force':scalar('Ecume_Force',0.22)})
output(custom('return F*.7;',{'F':foam}),'OPACITY')
output(custom('return lerp(float3(.005,.009,.008),float3(.55,.61,.57),F);',{'F':foam},3),'BASE_COLOR')
output(custom('return lerp(R,.38,F);',{'R':scalar('Rugosite',.085),'F':foam}),'ROUGHNESS')
output(scalar('Reflets',.255),'SPECULAR');output(node('Constant',r=0),'METALLIC')
wpo=custom('float h=sin(P.x*.004+P.y*.002+T*.75)*.65+sin(P.y*.006-P.x*.001-T*.5)*.35;return float3(0,0,h*Height);',{'P':wp,'T':time,'Height':scalar('Vagues_HauteurCm',1.5)},3);output(wpo,'WORLD_POSITION_OFFSET')
water=node('SingleLayerWaterMaterialOutput')
link(rgb(vector('Diffusion_ParCm',[.00045,.00085,.0007])),water,'ScatteringCoefficients')
link(rgb(vector('Absorption_ParCm',[.004,.0014,.0009])),water,'AbsorptionCoefficients')
link(scalar('Diffusion_Direction',.15),water,'PhaseG')
M.recompile_material(mat);E.save_loaded_asset(mat,False)
mi=asset('MI_Eau_Capitale',u.MaterialInstanceConstant,u.MaterialInstanceConstantFactoryNew);M.set_material_instance_parent(mi,mat);M.update_material_instance(mi);E.save_loaded_asset(mi,False)
R=u.AssetRegistryHelpers.get_asset_registry();R.search_all_assets(True);changed=[]
for a in R.get_assets_by_path('/Game/Capitale/Ressources/Metropole/Water',recursive=True):
 if str(a.asset_class_path.asset_name)!='StaticMesh':continue
 mesh=a.get_asset();mesh.set_material(0,mi);E.save_loaded_asset(mesh,False);changed.append(mesh.get_path_name())
report={'material':mi.get_path_name(),'waterMeshes':changed,'shadingModel':'SingleLayerWater','nanite':False,'parameters':{str(n):M.get_material_instance_scalar_parameter_value(mi,n) for n in M.get_scalar_parameter_names(mi)},'bathymetryChanged':False,'fluidSimulation':False}
(P/'Saved/Jadg/capitale-revision-eau.json').write_text(json.dumps(report,indent=2))
print('CAPITALE_WATER_READY',len(changed),flush=True)


