"""Separate pigments and procedural physical maps; same physical field drives
normal and height, never the brightness of albedo. 2m coverage per UV repeat.
"""
from pathlib import Path
import json
import hashlib

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'Source/Elements/Assets/Built/capital-surfaces'
CONTENT='/Game/Capitale/Ressources/Surfaces'


def prepare():
    import numpy as np
    from PIL import Image
    SOURCE.mkdir(parents=True,exist_ok=True)
    size=1024;y,x=np.mgrid[0:size,0:size]/size
    entries=[]
    for family in ('soil','paving','wet-soil'):
        for variant in range(3):
            rng=np.random.default_rng(20261013+variant)
            grain=rng.random((size,size))
            macro=.5+.3*np.sin(2*np.pi*x)*np.cos(4*np.pi*y)+.2*np.cos(6*np.pi*x+4*np.pi*y)
            if family=='paving':
                row=np.floor(y*8);u=(x*6+(row%2)*.5)%1;v=(y*8)%1
                joint=np.minimum.reduce([u,1-u,v,1-v])
                top=np.clip((joint-.045)/.07,0,1);top=top*top*(3-2*top)
                physical=.007*top+.00035*(grain-.5)
                pigment=np.array([166,151,128]);rough=.88-.12*top+.04*(macro-.5)
                colour= pigment[None,None,:]*(.82+.15*top[...,None]+.10*macro[...,None])
            else:
                # Compaction, mineral granules and shallow ruts share physical
                # provenance; pigment follows separate broad mineral variation.
                rut=.5+.5*np.cos(2*np.pi*x*4)
                physical=.0015*(grain-.5)+.003*macro+.002*rut
                pigment=np.array([105,79,52]) if family=='soil' else np.array([75,63,47])
                rough=.86+.10*macro if family=='soil' else .44+.14*macro
                colour=pigment[None,None,:]*(.82+.30*macro[...,None]+.08*grain[...,None])
            gy,gx=np.gradient(physical,2/size)
            normal=np.dstack([-gx,gy,np.ones_like(gx)]) # DirectX convention
            normal/=np.linalg.norm(normal,axis=2,keepdims=True)
            orm=np.dstack([.91+.09*macro,np.clip(rough,0,1),np.zeros_like(x)])
            arrays={'BC':np.clip(colour,0,255).astype('uint8'),
                    'N':np.rint((normal*.5+.5)*255).astype('uint8'),
                    'ORM':np.rint(orm*255).astype('uint8'),
                    'H':np.rint(np.clip(.5+physical/.02,0,1)*65535).astype('uint16')}
            for role,array in arrays.items():
                name=f'T_{family.replace("-","_")}_{variant}_{role}'
                path=SOURCE/(name+'.png');Image.fromarray(array).save(path)
                entries.append({'name':name,'file':path.name,'role':role,'family':family,'variant':variant,
                                'tileMetres':2,'normalConvention':'DirectX','srgb':role=='BC',
                                'channels':'R=AO G=roughness B=metallic' if role=='ORM' else role,
                                'heightNeutral':.5 if role=='H' else None,'heightRangeCm':2 if role=='H' else None,
                                'geometryDisplacement':False,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (SOURCE/'manifest.json').write_text(json.dumps({'generator':'scripts/maps/capital_surface_materials.py',
                     'textures':entries},indent=2),encoding='utf8')


def instance(path,parent):
    import unreal
    asset=unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
    if asset is None:
        folder,name=path.rsplit('/',1)
        asset=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(asset,parent)
    return asset


def build():
    import unreal
    import import_scenery_unreal as scenery
    doc=json.loads((SOURCE/'manifest.json').read_text())
    for row in doc['textures']:
        path=f"{CONTENT}/{row['name']}"
        current=unreal.EditorAssetLibrary.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else None
        if current is None or unreal.EditorAssetLibrary.get_metadata_tag(current,'JadgCapitalSourceHash')!=row['sha256']:
            task=unreal.AssetImportTask();task.filename=str(SOURCE/row['file'])
            task.destination_path=CONTENT;task.destination_name=row['name'];task.automated=True;task.save=True
            task.replace_existing=True;task.replace_existing_settings=True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        texture=unreal.EditorAssetLibrary.load_asset(path)
        texture.set_editor_property('srgb',row['srgb'])
        texture.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if row['role']=='N'
                                    else unreal.TextureCompressionSettings.TC_HALF_FLOAT if row['role']=='H' else unreal.TextureCompressionSettings.TC_BC7)
        texture.set_editor_property('flip_green_channel',False)
        unreal.EditorAssetLibrary.set_metadata_tag(texture,'JadgCapitalSourceHash',row['sha256'])
        unreal.EditorAssetLibrary.save_loaded_asset(texture)
    parent=scenery.parent_material(False)
    ml=unreal.MaterialEditingLibrary
    for family in ('soil','paving','wet_soil'):
        for variant in range(3):
            inst=instance(f'{CONTENT}/MI_{family}_{variant}',parent)
            for role,param in [('BC','BaseColor'),('N','Normal'),('ORM','ORM')]:
                texture=unreal.EditorAssetLibrary.load_asset(f'{CONTENT}/T_{family}_{variant}_{role}')
                ml.set_material_instance_texture_parameter_value(inst,param,texture)
            ml.set_material_instance_scalar_parameter_value(inst,'NormalStrength',.35 if family=='paving' else .45)
            ml.set_material_instance_scalar_parameter_value(inst,'RoughnessFactor',1)
            ml.set_material_instance_scalar_parameter_value(inst,'MetallicFactor',1)
            ml.set_material_instance_scalar_parameter_value(inst,'OcclusionStrength',.3)
            physical_path=f'{CONTENT}/PM_{family}'
            physical=unreal.EditorAssetLibrary.load_asset(physical_path) if unreal.EditorAssetLibrary.does_asset_exist(physical_path) else None
            if physical is None:
                physical=unreal.AssetToolsHelpers.get_asset_tools().create_asset('PM_'+family,CONTENT,unreal.PhysicalMaterial,unreal.PhysicalMaterialFactoryNew())
            physical.set_editor_property('friction',.65 if family!='wet_soil' else .45)
            inst.set_editor_property('phys_material',physical)
            ml.update_material_instance(inst);unreal.EditorAssetLibrary.save_loaded_asset(inst);unreal.EditorAssetLibrary.save_loaded_asset(physical)
    # Independent roof instances retain full PBR maps of the painted tile finish.
    for name,colour in [('roof_green',[.06,.17,.09,1]),('roof_blue',[.045,.04,.16,1])]:
        base=unreal.EditorAssetLibrary.load_asset('/Game/Bibliotheque/Commun/ArenaWickedWitness/Materials/painted/MI_roof_terracotta')
        if base:
            inst=instance(f'{CONTENT}/MI_{name}',base)
            ml.set_material_instance_vector_parameter_value(inst,'QuietColour',unreal.LinearColor(*colour))
            ml.set_material_instance_scalar_parameter_value(inst,'ColourDetail',.30)
            ml.update_material_instance(inst);unreal.EditorAssetLibrary.save_loaded_asset(inst)
    foliage_path=f'{CONTENT}/M_CapitalFoliage'
    if not unreal.EditorAssetLibrary.does_asset_exist(foliage_path):
        foliage=unreal.AssetToolsHelpers.get_asset_tools().create_asset('M_CapitalFoliage',CONTENT,unreal.Material,unreal.MaterialFactoryNew())
    else:foliage=unreal.EditorAssetLibrary.load_asset(foliage_path)
    ml.delete_all_material_expressions(foliage)
    foliage.set_editor_property('shading_model',unreal.MaterialShadingModel.MSM_TWO_SIDED_FOLIAGE)
    foliage.set_editor_property('two_sided',True)
    foliage.set_editor_property('used_with_instanced_static_meshes',True)
    foliage.set_editor_property('used_with_nanite',True)
    for name,colour,prop in [('LeafPigment',[.075,.17,.035,1],unreal.MaterialProperty.MP_BASE_COLOR),
                             ('LeafTransmission',[.12,.25,.055,1],unreal.MaterialProperty.MP_SUBSURFACE_COLOR)]:
        node=ml.create_material_expression(foliage,unreal.MaterialExpressionVectorParameter)
        node.set_editor_property('parameter_name',name);node.set_editor_property('default_value',unreal.LinearColor(*colour))
        ml.connect_material_property(node,'RGB',prop)
        if name=='LeafPigment':
            variation=ml.create_material_expression(foliage,unreal.MaterialExpressionPerInstanceRandom)
            blend=ml.create_material_expression(foliage,unreal.MaterialExpressionLinearInterpolate)
            blend.set_editor_property('const_a',.72);blend.set_editor_property('const_b',1.22)
            ml.connect_material_expressions(variation,'',blend,'Alpha')
            pigment=ml.create_material_expression(foliage,unreal.MaterialExpressionMultiply)
            ml.connect_material_expressions(node,'RGB',pigment,'A')
            ml.connect_material_expressions(blend,'',pigment,'B')
            ml.connect_material_property(pigment,'',prop)
    rough=ml.create_material_expression(foliage,unreal.MaterialExpressionScalarParameter)
    rough.set_editor_property('parameter_name','LeafRoughness');rough.set_editor_property('default_value',.86)
    ml.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    ml.recompile_material(foliage);unreal.EditorAssetLibrary.save_loaded_asset(foliage)
    # Isolated Nanite displacement test. The capital keeps collision-aligned
    # surfaces; only the two labelled witness pads compare 0 and 2cm range.
    test_path=CONTENT+'/M_CapitalDisplacementTest'
    if unreal.EditorAssetLibrary.does_asset_exist(test_path):
        test=unreal.EditorAssetLibrary.load_asset(test_path)
    else:test=unreal.EditorAssetLibrary.duplicate_asset('/Game/Bibliotheque/Commun/Common/M_Scenery',test_path)
    # Recreate from the common opaque parent once per build, avoiding accumulated
    # experimental nodes on repeat runs.
    ml.delete_all_material_expressions(test)
    for role,prop,sampler in [('BC',unreal.MaterialProperty.MP_BASE_COLOR,unreal.MaterialSamplerType.SAMPLERTYPE_COLOR),
                             ('N',unreal.MaterialProperty.MP_NORMAL,unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)]:
        tex=ml.create_material_expression(test,unreal.MaterialExpressionTextureSample)
        tex.set_editor_property('texture',unreal.EditorAssetLibrary.load_asset(f'{CONTENT}/T_soil_0_{role}'))
        tex.set_editor_property('sampler_type',sampler);ml.connect_material_property(tex,'RGB',prop)
    rough=ml.create_material_expression(test,unreal.MaterialExpressionConstant);rough.set_editor_property('r',.92)
    ml.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
    tex=ml.create_material_expression(test,unreal.MaterialExpressionTextureSample)
    tex.set_editor_property('texture',unreal.EditorAssetLibrary.load_asset(f'{CONTENT}/T_soil_0_H'))
    tex.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    subtract=ml.create_material_expression(test,unreal.MaterialExpressionSubtract);subtract.set_editor_property('const_b',.5)
    ml.connect_material_expressions(tex,'R',subtract,'A')
    strength=ml.create_material_expression(test,unreal.MaterialExpressionScalarParameter)
    strength.set_editor_property('parameter_name','HeightStrength');strength.set_editor_property('default_value',1.)
    mul=ml.create_material_expression(test,unreal.MaterialExpressionMultiply)
    ml.connect_material_expressions(subtract,'',mul,'A');ml.connect_material_expressions(strength,'',mul,'B')
    add=ml.create_material_expression(test,unreal.MaterialExpressionAdd);add.set_editor_property('const_b',.5)
    ml.connect_material_expressions(mul,'',add,'A')
    if not unreal.JadgSceneBuild.connect_material_displacement(test,add):
        raise RuntimeError('Nanite witness displacement connection failed')
    test.set_editor_property('enable_tessellation',True)
    scaling=test.get_editor_property('displacement_scaling');scaling.magnitude=2.;scaling.center=.5
    test.set_editor_property('displacement_scaling',scaling)
    ml.recompile_material(test);unreal.EditorAssetLibrary.save_loaded_asset(test)
    for suffix,value in [('flat',0.),('2cm',1.)]:
        inst=instance(f'{CONTENT}/MI_Displacement_{suffix}',test)
        ml.set_material_instance_scalar_parameter_value(inst,'HeightStrength',value)
        ml.update_material_instance(inst);unreal.EditorAssetLibrary.save_loaded_asset(inst)


def instances():
    import unreal
    result={name:unreal.EditorAssetLibrary.load_asset(f'{CONTENT}/MI_{name}') for name in ('roof_green','roof_blue')}
    leaf=unreal.EditorAssetLibrary.load_asset(f'{CONTENT}/M_CapitalFoliage')
    result.update({'foliage':leaf,'leaf':leaf,'grass':leaf})
    return result
