"""La matiere du relief naturel de la capitale : `M_TerrainNaturel`, son instance `MI_TerrainNaturel`
et le Runtime Virtual Texture `RVT_TerrainNaturel`.

Lancer dans l'editeur (sans fenetre) :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript
        -script=<chemin absolu de ce fichier> -unattended -nosplash -NoSound

Neuf couches peintes : Pelouse, Prairie, HerbeSauvage, Terre, Sable, Roche et Pavage servies par les
textures PBR retenues de `Metropole/MI_Surfaces` ; Foret (sous-bois, `PBR4K/forest`) et Chemin (terre
battue des voies hors les murs, `AOF/dust`). Par-dessus, ce que le moteur sait faire d'un terrain
(les techniques des tutoriels d'Unreal Sensei, matiere « tout-en-un » et matiere de Landscape) :

- fondu de distance : au-dela de `Lointain_Debut`, chaque couche se relit a une echelle `Lointain_Echelle`
  fois plus grande, sans motif repete jusqu'a l'horizon ;
- variations de couleur et de normale a grande echelle (textures du pack SenseiTerrain) ;
- roche d'elle-meme sur les pentes et sur les rivages rocheux, projetee sur trois plans ;
- melange des couches par leur hauteur (la terre et le sable passent entre les herbes) ;
- rivage : berge humide (plus sombre, plus lisse) et fonds teintes, lus dans
  `T_Capitale_Rivage` (prepare par `prepare_capitale_reference.py`) ;
- deplacement Nanite (tessellation) de toutes les couches, lu sur leur carte de hauteur, chacune a
  son amplitude (roche 30 cm, sous-bois 8 cm, terre battue 7 cm, paves 5 cm, herbes 2 a 4 cm),
  pleine jusqu'a 15 m, fondue a 60 m ;
- sortie vers un Runtime Virtual Texture (couleur, normale, rugosite, hauteur), que d'autres
  matieres pourront lire pour se fondre au sol.
"""
from pathlib import Path
import json
import sys

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
sys.path.insert(0, str(ROOT / 'scripts/maps'))
import revise_capitale_surface as retained  # noqa: E402  textures retenues des sept couches

CONTENT = '/Game/Capitale/Ressources/ReliefReference'
RIVAGE = ROOT / 'Source/Elements/Terrain/capital/relief-reference/T_Capitale_Rivage.png'
SENSEI = '/Game/Bibliotheque/Materiaux/SenseiTerrain/Textures'
PBR = '/Game/Capitale/Ressources/PBR4K/Textures'
AOF = '/Game/Bibliotheque/Materiaux/AOF/Textures'
LAYERS = ('Pelouse', 'Prairie', 'HerbeSauvage', 'Foret', 'Terre', 'Chemin', 'Sable', 'Roche', 'Pavage')
GRASSES = ('Pelouse', 'Prairie', 'HerbeSauvage')
# Les deux couches que `MI_Surfaces` n'a pas : textures, canal de rugosite de l'ORM, taille (cm).
EXTRA = {'Foret': ([f'{PBR}/forest/T_forest_{k}' for k in ('baseColor', 'normal', 'orm')], 'G', 400.),
         'Chemin': ([f'{AOF}/dust/T_dust_{k}' for k in ('baseColor', 'normal', 'orm')], 'G', 300.)}
# La carte de hauteur de chaque couche (melange par hauteur et deplacement Nanite), et l'amplitude
# du deplacement en centimetres.
HEIGHTS = {'Pelouse': (f'{PBR}/grass/T_grass_height', 2.), 'Prairie': (f'{PBR}/grass/T_grass_height', 3.),
           'HerbeSauvage': (f'{PBR}/grass/T_grass_height', 4.), 'Foret': (f'{PBR}/forest/T_forest_height', 8.),
           'Terre': (f'{PBR}/soil/T_soil_height', 6.), 'Chemin': (f'{AOF}/dust/T_dust_height', 7.),
           'Sable': (f'{PBR}/sand/T_sand_height', 4.), 'Roche': (f'{PBR}/rock/T_rock_height', 30.),
           'Pavage': (f'{PBR}/paving/T_paving_height', 5.)}
# La trame anti-repetition (trois lectures decalees) fait un damier sur ces textures 8K : chaque
# cellule lit une region de luminosite differente. La repetition se casse au fondu de distance a
# trame tournee et aux macro-variations ; la trame reste disponible pour d'autres textures.
SCATTER = False
EXTENT_CM = (-201600.0, 403200.0)  # origine et cote du terrain
LANDSCAPE_Z_SCALE = 100.0  # echelle Z des Landscape (build_reference_relief.py)

al, ml = u.EditorAssetLibrary, u.MaterialEditingLibrary
tools = u.AssetToolsHelpers.get_asset_tools()


def asset(path, cls, factory):
    if al.does_asset_exist(path):
        return al.load_asset(path)
    folder, name = path.rsplit('/', 1)
    made = tools.create_asset(name, folder, cls, factory)
    if made is None:
        raise RuntimeError('Creation impossible : ' + path)
    return made


def import_rivage():
    task = u.AssetImportTask()
    task.filename = str(RIVAGE)
    task.destination_path = CONTENT
    task.destination_name = 'T_Capitale_Rivage'
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    tex = al.load_asset(CONTENT + '/T_Capitale_Rivage')
    tex.set_editor_property('srgb', False)
    tex.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property('address_x', u.TextureAddress.TA_CLAMP)
    tex.set_editor_property('address_y', u.TextureAddress.TA_CLAMP)
    al.save_loaded_asset(tex, False)
    return tex


def runtime_virtual_texture():
    path = CONTENT + '/RVT_TerrainNaturel'
    rvt = asset(path, u.RuntimeVirtualTexture, u.RuntimeVirtualTextureFactory())
    rvt.set_editor_property('material_type', u.RuntimeVirtualTextureMaterialType.BASE_COLOR_NORMAL_ROUGHNESS)
    rvt.set_editor_property('compress_textures', True)
    al.save_loaded_asset(rvt, False)
    return rvt


def build():
    rivage = import_rivage()
    rvt = runtime_virtual_texture()
    sources = dict(retained.sources())
    sources.update(EXTRA)
    # La matiere se recree a neuf : delete_all_material_expressions laisse des noeuds d'une
    # construction precedente (une seconde sortie RVT, des Custom dont l'entree est partie).
    path = CONTENT + '/M_TerrainNaturel'
    if al.does_asset_exist(path) and not al.delete_asset(path):
        raise RuntimeError('Impossible de recreer ' + path)
    material = asset(path, u.Material, u.MaterialFactoryNew())
    material.set_editor_property('used_with_nanite', True)
    count = 0

    def node(kind, **props):
        nonlocal count
        count += 1
        n = ml.create_material_expression(material, getattr(u, 'MaterialExpression' + kind),
                                          -3000 + (count % 16) * 180, (count // 16) * 180)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def link(a, b, pin, out=''):
        if not ml.connect_material_expressions(a, out, b, pin):
            raise RuntimeError(f'Lien {a.get_class().get_name()} -> {b.get_class().get_name()} {pin}')

    def scalar(name, value):
        return node('ScalarParameter', parameter_name=name, default_value=value)

    def custom(code, inputs, size=1):
        pins = []
        for key in inputs:
            p = u.CustomInput()
            p.set_editor_property('input_name', key)
            pins.append(p)
        n = node('Custom', code=code, inputs=pins,
                 output_type=getattr(u.CustomMaterialOutputType, 'CMOT_FLOAT' + str(size)))
        for key, val in inputs.items():
            link(val, n, key)
        return n

    def mask(a, channels):
        n = node('ComponentMask', r='r' in channels, g='g' in channels, b='b' in channels, a='a' in channels)
        link(a, n, '')
        return n

    def texture(param, tex, kind, uv, mip=None):
        sampler = {'BC': u.MaterialSamplerType.SAMPLERTYPE_COLOR, 'N': u.MaterialSamplerType.SAMPLERTYPE_NORMAL}.get(
            kind, u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
        s = node('TextureSampleParameter2D', parameter_name=param, texture=tex, sampler_type=sampler,
                 sampler_source=u.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        if mip == 'derivative':
            s.set_editor_property('mip_value_mode', u.TextureMipValueMode.TMVM_DERIVATIVE)
        elif mip == 'level':
            s.set_editor_property('mip_value_mode', u.TextureMipValueMode.TMVM_MIP_LEVEL)
        link(uv[0] if isinstance(uv, tuple) else uv, s, 'UVs')
        if mip == 'derivative':
            link(uv[1], s, 'DDX(UVs)')
            link(uv[2], s, 'DDY(UVs)')
        return s

    wp = node('WorldPosition')
    xy = mask(wp, 'rg')
    cam = node('CameraPositionWS')
    nrm = node('VertexNormalWS')
    distance = custom('return distance(P, C);', {'P': wp, 'C': cam})
    far_alpha = custom('return smoothstep(A, B, D) * F;', {
        'D': distance, 'A': scalar('Lointain_Debut', 1500.), 'B': scalar('Lointain_Fin', 12000.),
        'F': scalar('Lointain_Force', 0.85)})
    far_scale = scalar('Lointain_Echelle', 4.37)

    # Le masque du rivage, en coordonnees du terrain : R berge humide, G fond, B roche, A champs.
    rivage_uv = custom('return (P - O) / S;', {'P': xy, 'O': node('Constant2Vector', r=EXTENT_CM[0], g=EXTENT_CM[0]),
                                                 'S': node('Constant', r=EXTENT_CM[1])}, 2)
    shore = node('TextureSampleParameter2D', parameter_name='Rivage_Masques', texture=rivage,
                 sampler_type=u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR,
                 sampler_source=u.SamplerSourceMode.SSM_CLAMP_WORLD_GROUP_SETTINGS)
    link(rivage_uv, shore, 'UVs')

    # Les variations a grande echelle : deux lectures croisees de la carte de macro-variation, une
    # carte de normales douces. Elles ne changent ni les poids ni les hauteurs.
    macro_tex = al.load_asset(SENSEI + '/T_MacroVariation')
    normal_tex = al.load_asset(SENSEI + '/T_NormalVariation')
    if macro_tex is None or normal_tex is None:
        raise RuntimeError('Textures de variation SenseiTerrain absentes')
    m1 = texture('Macro_Texture', macro_tex, 'BC', custom('return P / S;', {'P': xy, 'S': scalar('Macro_TailleA_Cm', 4200.)}, 2))
    m2 = texture('Macro_Texture', macro_tex, 'BC', custom('return P / S + 0.37;', {'P': xy, 'S': scalar('Macro_TailleB_Cm', 23000.)}, 2))
    macro = custom('float v = M1.r * 0.55 + M2.g * 0.45; return lerp(1 - A, 1 + A, v);', {
        'M1': m1, 'M2': m2, 'A': scalar('Macro_Variation', 0.16)})
    macro_n = texture('Macro_Normales', normal_tex, 'N', custom('return P / S;', {'P': xy, 'S': scalar('Macro_NormalesTailleCm', 6400.)}, 2))

    # Les poids : la couche peinte, plus la roche des pentes et des rivages rocheux.
    paint = {name: node('LandscapeLayerSample', parameter_name=name, preview_weight=1 / len(LAYERS)) for name in LAYERS}
    slope = custom('return saturate(max(smoothstep(A, B, 1 - abs(N.z)) * F, R.b * Rf));', {
        'N': nrm, 'A': scalar('Roche_PenteDebut', 0.14), 'B': scalar('Roche_PenteFin', 0.45),
        'F': scalar('Roche_Automatique', 0.85), 'R': shore, 'Rf': scalar('Roche_Rivages', 0.55)})
    for name in GRASSES + ('Foret', 'Terre', 'Chemin'):
        paint[name] = custom('return W * (1 - S * (1 - P));', {'W': paint[name], 'S': slope, 'P': paint['Pavage']})
    paint['Roche'] = custom('return max(W, S * (1 - P));', {'W': paint['Roche'], 'S': slope, 'P': paint['Pavage']})

    surfaces, heights, displace = {}, {}, {}
    for name in LAYERS:
        paths, channel, tile = sources[name]
        textures = [al.load_asset(p) for p in paths]
        size = scalar(name + '_TailleCm', tile)
        uv = custom('return P / S;', {'P': xy, 'S': size}, 2)
        # La lecture lointaine tourne de 37 degres : sa trame ne s'aligne ni sur celle de pres ni sur le monde.
        far_uv = custom('float2 q = P / (S * F); return float2(q.x * 0.7986 - q.y * 0.6018, q.x * 0.6018 + q.y * 0.7986) + 0.123;',
                        {'P': xy, 'S': size, 'F': far_scale}, 2)
        if name == 'Roche':
            xyz = custom('return P / S;', {'P': wp, 'S': size}, 3)
            coords = [mask(xyz, 'gb'), custom('return P.xz;', {'P': xyz}, 2), mask(xyz, 'rg')]
            tri = custom('float3 a = pow(abs(N), 4); return a / max(a.x + a.y + a.z, 1e-4);', {'N': nrm}, 3)
            weights = [mask(tri, c) for c in 'rgb']
            taps = [(c, w) for c, w in zip(coords, weights)]
            mode = None
        elif name == 'Pavage' or not SCATTER:
            taps, mode = [(uv, None)], None
        else:
            # Trois echantillons decales sur une trame triangulaire, gradients d'origine partages.
            lattice = '''
float2 p = float2(UV.x - UV.y * 0.577350269, UV.y * 1.154700538);
float2 cell = floor(p), f = frac(p);
float2 a, b, c; float3 w;
if (f.x + f.y < 1.0) { a = cell; b = cell + float2(1, 0); c = cell + float2(0, 1); w = float3(1 - f.x - f.y, f.x, f.y); }
else { a = cell + float2(1, 1); b = cell + float2(0, 1); c = cell + float2(1, 0); w = float3(f.x + f.y - 1, 1 - f.x, 1 - f.y); }
'''
            offsets = [custom(lattice + 'float2 id = ' + k + '; return UV + frac(sin(float2(dot(id, float2(127.1, 311.7)), dot(id, float2(269.5, 183.3)))) * 43758.5453) * 7;', {'UV': uv}, 2)
                       for k in 'abc']
            blend = custom(lattice + 'w = pow(max(w, 0), 2); return w / max(dot(w, float3(1, 1, 1)), 1e-5);', {'UV': uv}, 3)
            ddx, ddy = node('DDX'), node('DDY')
            link(uv, ddx, '')
            link(uv, ddy, '')
            taps = [((o, ddx, ddy), mask(blend, c)) for o, c in zip(offsets, 'rgb')]
            mode = 'derivative'

        def tapped(param, tex, kind):
            total = None
            for coord, w in taps:  # noqa: B023
                s = texture(param, tex, kind, coord, mode)  # noqa: B023
                v = mask(s, 'rgb')
                v = custom('return A * W;', {'A': v, 'W': w}, 3) if w is not None else v
                total = v if total is None else custom('return A + B;', {'A': total, 'B': v}, 3)
            return total

        near_bc = tapped(name + '_BC', textures[0], 'BC')
        if name == 'Roche':
            planes = [mask(texture(name + '_N', textures[1], 'N', c), 'rgb') for c in coords]
            # Normales des trois plans ramenees au monde (orientation de Ben Golus), puis a la tangente.
            world_n = custom('return normalize(float3(X.z * sign(N.x), X.x + N.y, X.y + N.z) * W.x'
                             ' + float3(Y.x + N.x, Y.z * sign(N.y), Y.y + N.z) * W.y'
                             ' + float3(Z.x + N.x, Z.y + N.y, Z.z * sign(N.z)) * W.z);',
                             {'X': planes[0], 'Y': planes[1], 'Z': planes[2], 'N': nrm, 'W': tri}, 3)
            near_n = node('Transform', transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
                          transform_type=u.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
            link(world_n, near_n, '')
        else:
            near_n = tapped(name + '_N', textures[1], 'N')
        orm = tapped(name + '_ORM', textures[2], 'ORM')
        if name != 'Pavage':
            far_bc = mask(texture(name + '_BC', textures[0], 'BC', far_uv), 'rgb')
            far_n = mask(texture(name + '_N', textures[1], 'N', far_uv), 'rgb')
            near_bc = custom('return lerp(A, B, T);', {'A': near_bc, 'B': far_bc, 'T': far_alpha}, 3)
            near_n = custom('return lerp(A, B, T);', {'A': near_n, 'B': far_n, 'T': far_alpha}, 3)
        if name in GRASSES:
            # Les herbes 8K ont des ecarts de luminosite a l'echelle de la tuile : chaque repetition
            # dessine une case. On n'en garde que le detail fin (sous ~1 m) : la couleur est divisee
            # par sa lecture au mip 10 (8 x 8 texels par tuile) et ramenee a sa moyenne (mip 13).
            # Les grandes variations viennent des macro-variations, qui ne se repetent pas.
            def flattened(color, coord):
                low = texture(name + '_BC', textures[0], 'BC', coord, 'level')  # noqa: B023
                low.set_editor_property('const_mip_value', 10)
                mean = texture(name + '_BC', textures[0], 'BC', coord, 'level')  # noqa: B023
                mean.set_editor_property('const_mip_value', 13)
                return custom('return C * M.rgb / max(L.rgb, 0.02);', {'C': color, 'M': mean, 'L': low}, 3)
            near_bc = custom('return lerp(N, F, T);', {
                'N': flattened(mask(texture(name + '_BC', textures[0], 'BC', uv), 'rgb'), uv),
                'F': flattened(mask(texture(name + '_BC', textures[0], 'BC', far_uv), 'rgb'), far_uv),
                'T': far_alpha}, 3)
        tint = node('VectorParameter', parameter_name=name + '_Teinte', default_value=u.LinearColor(1, 1, 1, 1))
        color = custom('return A * T.rgb * M;', {'A': near_bc, 'T': tint, 'M': macro}, 3)
        normal = custom('float3 n = normalize(float3(N.xy * F, N.z)); return normalize(float3(n.xy + V.xy * G, n.z));', {
            'N': near_n, 'F': scalar(name + '_Normale', 1.), 'V': macro_n, 'G': scalar('Macro_NormalesForce', 0.35)}, 3)
        rough = custom('return saturate(O.' + channel.lower() + ' * R);', {'O': orm, 'R': scalar(name + '_Rugosite', 1.)})
        ao = custom('return lerp(1, saturate(O.r), F);', {'O': orm, 'F': scalar('Occlusion_Force', 0.6)})
        surfaces[name] = [color, normal, rough, ao]
        ht = al.load_asset(HEIGHTS[name][0])
        if ht is None:
            raise RuntimeError('Hauteur absente : ' + HEIGHTS[name][0])
        heights[name] = mask(tapped(name + '_Hauteur', ht, 'H'), 'r')
        # Etage du deplacement : une lecture a niveau de mip fixe (pas de derivees).
        single = custom('return P / S;', {'P': xy, 'S': size}, 2)
        displace[name] = mask(texture(name + '_Hauteur', ht, 'H', single, 'level'), 'r')

    # Melange par hauteur : chaque couche pese son poids peint, releve par ses reliefs.
    strength = scalar('Transitions_Hauteur', 0.55)
    scores = {n: custom('return max(W, 0) * lerp(1, exp2((H - .5) * 5), F);', {'W': paint[n], 'H': heights[n], 'F': strength})
              for n in LAYERS}
    total = None
    for n in LAYERS:
        total = scores[n] if total is None else custom('return A + B;', {'A': total, 'B': scores[n]})
    blends = [None] * 4
    for n in LAYERS:
        w = custom('return A / max(T, 1e-5);', {'A': scores[n], 'T': total})
        for i, out in enumerate(surfaces[n]):
            size = 3 if i < 2 else 1
            v = custom('return A * W;', {'A': out, 'W': w}, size)
            blends[i] = v if blends[i] is None else custom('return A + B;', {'A': blends[i], 'B': v}, size)

    # Le rivage : la berge mouillee fonce et se lisse (moins sur la roche) ; les fonds se teintent.
    rock_w = custom('return A / max(T, 1e-5);', {'A': scores['Roche'], 'T': total})
    color = custom('float w = R.r * H * (1 - 0.5 * K); float3 c = C * lerp(1, 0.58, w);'
                   ' return lerp(c, c * F.rgb, R.g);', {
                       'C': blends[0], 'R': shore, 'K': rock_w, 'H': scalar('Rives_Humidite', 1.),
                       'F': node('VectorParameter', parameter_name='Fonds_Teinte', default_value=u.LinearColor(.62, .78, .74, 1))}, 3)
    rough = custom('float w = R.r * H; return max(.12, lerp(lerp(X, .18, w * .85), .32, R.g));', {
        'X': blends[2], 'R': shore, 'H': scalar('Rives_Humidite', 1.)})
    normal = custom('return normalize(N);', {'N': blends[1]}, 3)
    for value, prop in [(color, u.MaterialProperty.MP_BASE_COLOR), (normal, u.MaterialProperty.MP_NORMAL),
                        (rough, u.MaterialProperty.MP_ROUGHNESS), (blends[3], u.MaterialProperty.MP_AMBIENT_OCCLUSION)]:
        if not ml.connect_material_property(value, '', prop):
            raise RuntimeError('Sortie de matiere')
    ml.connect_material_property(node('Constant', r=0.), '', u.MaterialProperty.MP_METALLIC)

    # Le Runtime Virtual Texture : ce que voient les autres matieres qui viendront s'y fondre.
    out = node('RuntimeVirtualTextureOutput')
    link(color, out, 'BaseColor')
    link(rough, out, 'Roughness')
    link(normal, out, 'Normal')
    link(mask(wp, 'b'), out, 'WorldHeight')

    # Le deplacement Nanite : chaque couche souleve sa carte de hauteur, ponderee par son poids
    # peint, a pleine amplitude pres de la camera.
    magnitude = 64.0
    total = None
    for n in LAYERS:
        term = custom('return (H - .5) * W * A;', {
            'H': displace[n], 'W': node('LandscapeLayerSample', parameter_name=n, preview_weight=0.),
            'A': scalar('Deplacement_' + n + 'Cm', HEIGHTS[n][1])})
        total = term if total is None else custom('return A + B;', {'A': total, 'B': term})
    disp = custom('float fade = 1 - smoothstep(F0, F1, distance(P, C));'
                  ' return saturate(.5 + H / M * fade);', {
                      'P': wp, 'C': cam, 'M': node('Constant', r=magnitude), 'H': total,
                      'F0': scalar('Deplacement_PleinCm', 1500.), 'F1': scalar('Deplacement_FinCm', 6000.)})
    if not u.JadgSceneBuild.connect_material_displacement(material, disp):
        raise RuntimeError('Deplacement Nanite')
    material.set_editor_property('enable_tessellation', True)
    scaling = material.get_editor_property('displacement_scaling')
    # Le deplacement s'applique dans l'espace local du Landscape, puis passe par son echelle :
    # en Z, 100 (build_reference_relief.py). L'echelle de la matiere en est divisee, pour que les
    # amplitudes restent des centimetres au sol (sans cela, 5 cm de paves soulevaient 5 m de
    # chaussee et dechiraient le maillage tessele, essai du 17 octobre 2026).
    scaling.magnitude = magnitude / LANDSCAPE_Z_SCALE
    scaling.center = .5
    material.set_editor_property('displacement_scaling', scaling)

    ml.recompile_material(material)
    al.save_loaded_asset(material, False)
    inst = asset(CONTENT + '/MI_TerrainNaturel', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
    ml.set_material_instance_parent(inst, material)
    # Une instance reprise d'une matiere precedente garde des surcharges sans objet : on repart a zero.
    ml.clear_all_material_instance_parameters(inst)
    # Les herbes (textures 8K) posees sur 2 m font lire la trame anti-repetition en damier : chaque
    # cellule y prend une luminosite propre. Sur 6 m, la trame se perd sous les macro-variations.
    for name in GRASSES:
        ml.set_material_instance_scalar_parameter_value(inst, name + '_TailleCm', 600.)
    # La litiere de `forest` est claire (feuilles sur sable) : sans arbres au-dessus, les bois se
    # liraient blancs de loin. Elle prend la teinte d'un humus moussu a l'ombre.
    ml.set_material_instance_vector_parameter_value(inst, 'Foret_Teinte', u.LinearColor(.30, .33, .20, 1))
    ml.update_material_instance(inst)
    al.save_loaded_asset(inst, False)
    report = {'material': material.get_path_name(), 'instance': inst.get_path_name(), 'rvt': rvt.get_path_name(),
              'layers': list(LAYERS), 'nodes': count, 'displacementCm': magnitude,
              'parameters': sorted(str(n) for n in ml.get_scalar_parameter_names(inst))}
    (ROOT / 'Saved/Jadg').mkdir(parents=True, exist_ok=True)
    (ROOT / 'Saved/Jadg/capitale-terrain-material.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CAPITALE_TERRAIN_MATERIAL_READY', json.dumps(report), flush=True)
    return inst, rvt


if __name__ == '__main__':
    build()
