#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Rebuild the native editable Capitale surface material from retained PBR textures."""

CONTENT = "/Game/Capitale/Ressources/Arenarea"
LAYERS = ("Pelouse", "Prairie", "HerbeSauvage", "Terre", "Sable", "Roche", "Pavage")


def sources():
    import unreal as u
    mi=u.EditorAssetLibrary.load_asset('/Game/Capitale/Ressources/Metropole/Materials/MI_Surfaces')
    rows={}
    for name in LAYERS:
        textures=[u.MaterialEditingLibrary.get_material_instance_texture_parameter_value(mi,name+'_'+r) for r in ('BC','N','ORM')]
        if any(t is None for t in textures):raise RuntimeError('Missing retained texture '+name)
        rows[name]=([t.get_path_name() for t in textures], 'R' if name=='Terre' else 'G', u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(mi,name+'_TailleCm'))
    return rows


def build(relief=False, metropole=True):
    if relief or not metropole: raise ValueError("This generator only updates Capitale/Metropole")
    import unreal as u

    ml, al = u.MaterialEditingLibrary, u.EditorAssetLibrary
    at = u.AssetToolsHelpers.get_asset_tools()

    def asset(path, cls, factory):
        if al.does_asset_exist(path):
            return al.load_asset(path)
        folder, name = path.rsplit("/", 1)
        obj = at.create_asset(name, folder, cls, factory())
        if obj is None:
            raise RuntimeError("Could not create " + path)
        return obj

    retained_sources=sources()
    suffix = "Relief" if relief else "Surfaces"
    output_content = "/Game/Capitale/Ressources/Metropole" if metropole else CONTENT
    material = asset(output_content + "/Materials/M_" + suffix, u.Material, u.MaterialFactoryNew)
    ml.delete_all_material_expressions(material)
    material.set_editor_property("used_with_nanite", True)
    count = 0

    def node(kind, **props):
        nonlocal count
        count += 1
        n = ml.create_material_expression(
            material,
            getattr(u, "MaterialExpression" + kind),
            -2000 + (count % 12) * 160,
            (count // 12) * 200,
        )
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def link(a, b, pin, out=""):
        if not ml.connect_material_expressions(a, out, b, pin):
            raise RuntimeError(
                f"Material link {a.get_class().get_name()} -> {b.get_class().get_name()} {pin}"
            )

    def scalar(name, value):
        return node("ScalarParameter", parameter_name=name, default_value=value)

    def op(kind, a, b=None, **kw):
        n = node(kind, **kw)
        link(a, n, "A" if kind in ("Add", "Multiply", "Divide", "Subtract") else "")
        if b is not None:
            link(b, n, "B")
        return n

    def rgb(a, out=""):
        n = node("ComponentMask", r=True, g=True, b=True)
        link(a, n, "", out)
        return n

    def scattered_uvs(uv):
        # Three translated samples on a triangular lattice. The original PBR
        # maps keep the same scale and orientation; all channels share offsets.
        # Explicit original UV gradients avoid mip seams at lattice boundaries.
        common = """
float2 p = float2(UV.x - UV.y * 0.577350269, UV.y * 1.154700538);
float2 cell = floor(p), f = frac(p);
float2 a, b, c; float3 w;
if (f.x + f.y < 1.0) {
    a=cell; b=cell+float2(1,0); c=cell+float2(0,1);
    w=float3(1-f.x-f.y,f.x,f.y);
} else {
    a=cell+float2(1,1); b=cell+float2(0,1); c=cell+float2(1,0);
    w=float3(f.x+f.y-1,1-f.x,1-f.y);
}
"""
        def custom(code, size):
            uv_input = u.CustomInput()
            uv_input.set_editor_property("input_name", "UV")
            n = node("Custom", code=common+code,
                output_type=getattr(u.CustomMaterialOutputType, "CMOT_FLOAT"+str(size)),
                inputs=[uv_input])
            link(uv, n, "UV")
            return n
        coords = [custom("float2 id="+key+"; return UV + frac(sin(float2(dot(id,float2(127.1,311.7)),dot(id,float2(269.5,183.3))))*43758.5453)*7;", 2)
                  for key in ("a", "b", "c")]
        weights = custom("w=pow(max(w,0),2); return w/max(dot(w,float3(1,1,1)),0.00001);", 3)
        channels = []
        for i in range(3):
            n = node("ComponentMask", r=i == 0, g=i == 1, b=i == 2)
            link(weights, n, "")
            channels.append(n)
        return coords, channels, op("DDX", uv), op("DDY", uv)


    def custom(code, inputs, size=1):
        pins=[]
        for key in inputs:
            p=u.CustomInput();p.set_editor_property('input_name',key);pins.append(p)
        n=node('Custom',code=code,output_type=getattr(u.CustomMaterialOutputType,'CMOT_FLOAT'+str(size)),inputs=pins)
        for key,val in inputs.items():link(val,n,key)
        return n
    wp_global=node('WorldPosition')
    surface_normal=node('VertexNormalWS')
    usage=al.load_asset('/Game/Capitale/Ressources/Plan/T_Capitale_Usage')
    if usage is None:raise RuntimeError('Missing capital usage mask')
    usage_uv=custom('return saturate(((P.xy-float2(-504000,-604800))/400+.5)/float2(2773,3277));',{'P':wp_global},2)
    usage_sample=node('TextureSampleParameter2D',parameter_name='Plan_Usages',texture=usage,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS,sampler_source=u.SamplerSourceMode.SSM_CLAMP_WORLD_GROUP_SETTINGS)
    link(usage_uv,usage_sample,'UVs')
    usage_rgb=rgb(usage_sample)
    shoulder=custom('return U.r*Amount;',{'U':usage_rgb,'Amount':scalar('Plan_Accotements',0.75)})
    reserve=custom('return U.b*Amount;',{'U':usage_rgb,'Amount':scalar('Plan_Emprises',0.65)})
    dirt_overlay=custom('return saturate(max(A,B));',{'A':shoulder,'B':reserve})
    slope=custom('return smoothstep(Debut,Fin,1-abs(N.z))*Force;',{'N':surface_normal,'Debut':scalar('Roche_PenteDebut',0.12),'Fin':scalar('Roche_PenteFin',0.42),'Force':scalar('Roche_Automatique',0.8)})
    macro=custom('float2 p=P.xy/Scale; float v=sin(p.x*.73+sin(p.y*.63))*sin(p.y*.47+sin(p.x*.39)); return 1+v*Amount;',{'P':wp_global,'Scale':scalar('Macro_TailleCm',8500),'Amount':scalar('Macro_Variation',0.10)})

    # Read native paint weights explicitly. Their sum is normalized in the shader,
    # so independent UE 5.8 target layers also remain well-defined after painting.
    paint = {name: node("LandscapeLayerSample", parameter_name=name, preview_weight=1/7)
             for name in LAYERS}
    original_road=paint['Pavage']
    for name in LAYERS:
        if name in ('Pelouse','Prairie','HerbeSauvage'):
            paint[name]=custom('return W*(1-D)*(1-S*(1-R));',{'W':paint[name],'D':dirt_overlay,'S':slope,'R':original_road})
    paint['Terre']=custom('return max(W,max(D*(1-R),Reserve));',{'W':paint['Terre'],'D':dirt_overlay,'R':original_road,'Reserve':reserve})
    paint['Pavage']=custom('return W*(1-Reserve);',{'W':paint['Pavage'],'Reserve':reserve})
    original_road=paint['Pavage']
    paint['Roche']=custom('return max(W,S*(1-R));',{'W':paint['Roche'],'S':slope,'R':original_road})
    surfaces={}; heights={}
    blends=[None,None,None,None]
    for name, (paths, channel, tile) in retained_sources.items():
        if relief:
            colors = {
                "Pelouse": (0.32, 0.34, 0.30),
                "Prairie": (0.32, 0.34, 0.30),
                "HerbeSauvage": (0.32, 0.34, 0.30),
                "Terre": (0.34, 0.32, 0.28),
                "Sable": (0.50, 0.46, 0.36),
                "Roche": (0.28, 0.29, 0.29),
                "Pavage": (0.58, 0.55, 0.48),
            }
            outputs = [
                node("Constant3Vector", constant=u.LinearColor(*colors[name], 1)),
                node("Constant3Vector", constant=u.LinearColor(0, 0, 1, 1)),
                node("Constant", r=0.85),
            ]
        else:
            wp = node("WorldPosition")
            xy = node("ComponentMask", r=True, g=True, b=False)
            link(wp, xy, "")
            uv = op("Divide", xy, scalar(name + "_TailleCm", tile))
            scatter = scattered_uvs(uv) if metropole and name not in ('Pavage','Roche') else None
            rock_normals=[]
            if name=='Roche':
                xyz=op('Divide',wp,scalar('Roche_TailleCm',tile))
                coords=[custom('return P.yz;',{'P':xyz},2),custom('return P.xz;',{'P':xyz},2),custom('return P.xy;',{'P':xyz},2)]
                tri=custom('float3 a=pow(abs(N),4);return a/max(a.x+a.y+a.z,0.0001);',{'N':surface_normal},3)
                weights=[]
                for channel_id in range(3):
                    c=node('ComponentMask',r=channel_id==0,g=channel_id==1,b=channel_id==2);link(tri,c,'');weights.append(c)
                scatter=(coords,weights,None,None)

            samples = []
            for path, role in zip(paths, ("BC", "N", "ORM")):
                tex=al.load_asset(path)
                if tex is None:raise RuntimeError('Missing '+path)
                combined = None
                for i, coord in enumerate(scatter[0] if scatter else [uv]):
                    sample = node(
                        "TextureSampleParameter2D", parameter_name=name + "_" + role,
                        texture=tex,
                        sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == "N"
                        else u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == "BC"
                        else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
                        sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS,
                    )
                    if scatter and name!='Roche':
                        sample.set_editor_property("mip_value_mode", u.TextureMipValueMode.TMVM_DERIVATIVE)
                        link(scatter[2], sample, "DDX(UVs)")
                        link(scatter[3], sample, "DDY(UVs)")
                    link(coord, sample, "UVs")
                    if name=='Roche' and role=='N':rock_normals.append(rgb(sample))
                    contribution = op("Multiply", rgb(sample), scatter[1][i]) if scatter else rgb(sample)
                    combined = contribution if combined is None else op("Add", combined, contribution)
                if name=='Roche' and role=='N':
                    wn=custom('float3 sx=float3(X.z*sign(N.x),X.x+N.y,X.y+N.z); float3 sy=float3(Y.x+N.x,Y.z*sign(N.y),Y.y+N.z); float3 sz=float3(Z.x+N.x,Z.y+N.y,Z.z*sign(N.z)); return normalize(sx*W.x+sy*W.y+sz*W.z);',{'X':rock_normals[0],'Y':rock_normals[1],'Z':rock_normals[2],'N':surface_normal,'W':tri},3)
                    combined=node('Transform',transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,transform_type=u.MaterialVectorCoordTransform.TRANSFORM_TANGENT);link(wn,combined,'')
                samples.append(combined)
            heights[name]=node('Constant',r=0.5)
            height_key={'Terre':'soil','Sable':'sand','Roche':'rock','Pavage':'paving'}.get(name)
            if height_key:
                ht=al.load_asset('/Game/Capitale/Ressources/PBR4K/Textures/'+height_key+'/T_'+height_key+'_height')
                if ht is None:raise RuntimeError('Missing real height '+height_key)
                combined_h=None
                for i,coord in enumerate(scatter[0] if scatter else [uv]):
                    h=node('TextureSampleParameter2D',parameter_name=name+'_Hauteur',texture=ht,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
                    if scatter and name!='Roche':
                        h.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_DERIVATIVE);link(scatter[2],h,'DDX(UVs)');link(scatter[3],h,'DDY(UVs)')
                    link(coord,h,'UVs');red=node('ComponentMask',r=True,g=False,b=False);link(h,red,'')
                    v=op('Multiply',red,scatter[1][i]) if scatter else red
                    combined_h=v if combined_h is None else op('Add',combined_h,v)
                heights[name]=combined_h

            tint = node(
                "VectorParameter",
                parameter_name=name + "_Teinte",
                default_value=u.LinearColor(
                    *((1.12, 1.07, 0.94, 1) if name == "Pavage" else (1, 1, 1, 1))
                ),
            )
            color = op("Multiply", rgb(samples[0]), rgb(tint))
            color=op('Multiply',color,macro)
            normal=custom('return normalize(float3(N.xy*Force,N.z));',{'N':rgb(samples[1]),'Force':scalar(name+'_Normale',1)},3)
            rough = node("ComponentMask", r=channel == "R", g=channel == "G", b=False)
            link(samples[2], rough, "")
            rough = op("Saturate", op("Multiply", rough, scalar(name + "_Rugosite", 1)))
            damp=custom('return saturate(U.g*Force)*(1-abs(N.x)*0.25);',{'U':usage_rgb,'Force':scalar('Rives_Humidite',0.45),'N':surface_normal})
            color=custom('return C*(1-W*.22);',{'C':color,'W':damp},3)
            rough=custom('return max(.18,R*(1-W*.45));',{'R':rough,'W':damp})
            ao=node('ComponentMask',r=True,g=False,b=False);link(samples[2],ao,'')
            if name=='Terre':
                ao_tex=al.load_asset('/Game/Capitale/Ressources/PBR4K/Textures/soil/T_soil_ao')
                combined_ao=None
                for i,coord in enumerate(scatter[0] if scatter else [uv]):
                    sample_ao=node('TextureSampleParameter2D',parameter_name='Terre_AO',texture=ao_tex,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
                    sample_ao.set_editor_property('mip_value_mode',u.TextureMipValueMode.TMVM_DERIVATIVE);link(scatter[2],sample_ao,'DDX(UVs)');link(scatter[3],sample_ao,'DDY(UVs)');link(coord,sample_ao,'UVs')
                    red=node('ComponentMask',r=True,g=False,b=False);link(sample_ao,red,'')
                    v=op('Multiply',red,scatter[1][i]);combined_ao=v if combined_ao is None else op('Add',combined_ao,v)
                ao=combined_ao
            ao=custom('return lerp(1,saturate(A),Force);',{'A':ao,'Force':scalar('Occlusion_Force',0.65)})
            outputs = [color, normal, rough, ao]
        surfaces[name]=outputs
    dirt_in_joints=custom('return (1-smoothstep(.20,.58,H))*R*Amount;',{'H':heights['Pavage'],'R':paint['Pavage'],'Amount':scalar('Rues_TerreDansJoints',0.35)})
    paint['Terre']=op('Add',paint['Terre'],dirt_in_joints)
    paint['Pavage']=custom('return max(0,R-D);',{'R':paint['Pavage'],'D':dirt_in_joints})
    scores={}
    strength=scalar('Transitions_Hauteur',0.55)
    total=None
    for name in LAYERS:
        scores[name]=custom('return max(W,0)*lerp(1,exp2((H-.5)*5),Force);',{'W':paint[name],'H':heights[name],'Force':strength})
        total=scores[name] if total is None else op('Add',total,scores[name])
    total=op('Add',total,const_b=0.00001)
    for name in LAYERS:
        weight=op('Divide',scores[name],total)
        for i,output in enumerate(surfaces[name]):
            contribution=op('Multiply',output,weight)
            blends[i]=contribution if blends[i] is None else op('Add',blends[i],contribution)
    zero=node('Constant',r=0)
    ml.connect_material_property(zero,'',u.MaterialProperty.MP_METALLIC)
    for n, p in zip(
        [blends[0], op("Normalize", blends[1]), blends[2], blends[3]],
        [
            u.MaterialProperty.MP_BASE_COLOR,
            u.MaterialProperty.MP_NORMAL,
            u.MaterialProperty.MP_ROUGHNESS,
            u.MaterialProperty.MP_AMBIENT_OCCLUSION,
        ],
    ):
        if not ml.connect_material_property(n, "", p):
            raise RuntimeError("Material output")
    # Separate mip-level height branch is valid in the Nanite displacement stage.
    # Pixel height blends use derivatives and must not be connected to this stage.
    pave_height=al.load_asset('/Game/Capitale/Ressources/PBR4K/Textures/paving/T_paving_height')
    disp_sample=node('TextureSampleParameter2D',parameter_name='Pavage_Hauteur',texture=pave_height,sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS,mip_value_mode=u.TextureMipValueMode.TMVM_MIP_LEVEL)
    disp_uv=custom('return P.xy/Size;',{'P':wp_global,'Size':scalar('Pavage_TailleCm',retained_sources['Pavage'][2])},2)
    link(disp_uv,disp_sample,'UVs')
    disp_h=node('ComponentMask',r=True,g=False,b=False);link(disp_sample,disp_h,'')
    cam=node('CameraPositionWS')
    displacement=custom('float fade=1-smoothstep(1500,6000,distance(P,C));return .5+(H-.5)*R*saturate(Cm/4)*fade;',{'H':disp_h,'R':original_road,'Cm':scalar('Pavage_ReliefCm',2),'P':wp_global,'C':cam})
    if not u.JadgSceneBuild.connect_material_displacement(material,displacement):raise RuntimeError('Displacement connection')
    material.set_editor_property('enable_tessellation',True)
    scaling=material.get_editor_property('displacement_scaling');scaling.magnitude=4.;scaling.center=.5;material.set_editor_property('displacement_scaling',scaling)
    ml.recompile_material(material)
    al.save_loaded_asset(material, only_if_is_dirty=False)
    inst = asset(
        output_content + "/Materials/MI_" + suffix,
        u.MaterialInstanceConstant,
        u.MaterialInstanceConstantFactoryNew,
    )
    ml.set_material_instance_parent(inst, material)
    ml.update_material_instance(inst)
    al.save_loaded_asset(inst)
    return inst

if __name__=='__main__':
    import unreal as u
    import json
    from pathlib import Path
    root=Path(u.Paths.project_dir()).resolve()
    task=u.AssetImportTask();task.filename=str(root/'Source/Elements/Terrain/capital/revision-textures/T_Capitale_Usage.png');task.destination_path='/Game/Capitale/Ressources/Plan';task.destination_name='T_Capitale_Usage';task.automated=True;task.save=True;task.replace_existing=True
    u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tx=u.EditorAssetLibrary.load_asset('/Game/Capitale/Ressources/Plan/T_Capitale_Usage');tx.set_editor_property('srgb',False);tx.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS);tx.set_editor_property('address_x',u.TextureAddress.TA_CLAMP);tx.set_editor_property('address_y',u.TextureAddress.TA_CLAMP);tx.set_editor_property('max_texture_size',4096);u.EditorAssetLibrary.save_loaded_asset(tx,False)
    result=build(metropole=True)
    report={'material':result.get_path_name(),'layers':list(LAYERS),'parameters':{str(n):u.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(result,n) for n in u.MaterialEditingLibrary.get_scalar_parameter_names(result)},'foliageOutput':False,'geometryDisplacement':'Pavage only, 2 cm full range; fades from 15 to 60 metres','heightBlending':True,'rockTriplanar':True,'roadMask':tx.get_path_name()}
    (root/'Saved/Jadg/capitale-revision-textures.json').write_text(json.dumps(report,indent=2))
    print('CAPITALE_TERRAIN_MATERIAL_READY',report,flush=True)

