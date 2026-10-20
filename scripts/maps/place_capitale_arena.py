"""L'Arena of Fate posee sur la carte de la capitale (/Game/Capitale/Cartes/Capitale), a son emprise.

Lancer dans l'editeur, avec rendu (les maillages Nanite et les matieres s'y construisent) :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript
        -script=<chemin absolu de ce fichier> -unattended -nosplash -NoSound

Le monument est celui du LOT-1022, decrit en texte dans
`Source/Elements/Levels/central-empire/capital/arenarea/arena-of-fate.json` (temoin imperial
sculpte et peint, valide le 10 octobre 2026) : ses 1 826 objets, ses sept etages (sable, -1, -2,
tribunes, galerie haute, attique, terrasse), ses finitions peintes approuvees et ses feux. Rien
n'y est redessine ; il est pose au centre et au niveau du sol que `prepare_capitale_reference.py`
a ecrits dans `relief-reference/manifest.json` (cle `arena`), le grand axe tourne de `cap_deg`.

Les etages -1 et -2 sont poses avec le reste : les portes du triomphe et des morts y descendent
depuis le sable ; le relief est creuse sous l'ovale pour les recevoir. L'acces des catacombes reste
ferme comme dans la carte du LOT-1022. L'atmosphere propre a la carte de l'arene (brouillard,
ciel d'atelier) n'est pas reprise : la capitale a son ciel.

Les pieces que le manifeste marque comme coupes portent `JadgWitnessOccluder`, et chaque objet est
lie au sol qui le porte (`JadgWitnessSupport:`) : la camera de la demo (`capitale_demo.py`) voit le
groupe sous le sable et sous les voutes, comme dans la carte du LOT-1022.

Les acteurs portent l'etiquette `JadgCapitaleArene` : une relance retire les precedents avant de
reposer. Chaque objet garde son etiquette `JadgObject:<id>` de la description.
"""
from pathlib import Path
import json
import sys
import time

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
for sub in ('scripts/maps', 'scripts/assetsGeneration'):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

import build_level as scene  # noqa: E402
import arena_fate_atmosphere  # noqa: E402
import arena_wicked_materials  # noqa: E402
import build_arena_fate_modern_scene as arena  # noqa: E402  (fonctions seules : sa carte est archivee)

PACKAGE = '/Game/Capitale/Cartes/Capitale'
SOURCE = ROOT / 'Source/Elements/Levels/central-empire/capital/arenarea/arena-of-fate.json'
GEOMETRY = ROOT / 'Source/Elements/Assets/Built/arena-fate-modern/manifest.json'
RELIEF = ROOT / 'Source/Elements/Terrain/capital/relief-reference/manifest.json'
KIT = '/Game/Bibliotheque/ArenaFate/Kit'
# Les pieces unitaires du catalogue de l'arene (192 types, LOT-106), deja importees avec leurs
# matieres PBR : la description les cite par leur .glb, la carte pose l'asset du projet.
AOF = '/Game/Bibliotheque/ArenaFate'
FLAME = 'Built/arena-fate-atmosphere/afa-flame.glb'
TAG = 'JadgCapitaleArene'
FOLDER = 'Arene'
LIGHT_DISTANCE, LIGHT_FADE = 6000.0, 1500.0  # cm


def aof_library(library):
    """Les .glb du catalogue AOF se resolvent vers leurs assets du projet, sans reimport."""
    base = library.static_mesh

    def static_mesh(mesh, *args, **kwargs):
        if not mesh.startswith('Built/aof-'):
            return base(mesh, *args, **kwargs)
        if mesh not in library.static:
            stem = Path(mesh).stem
            folders = ['Pieces001048/Meshes'] if int(stem[-3:]) <= 45 else ['RefinedMeshes', 'Meshes']
            found = [f'{AOF}/{folder}/{stem}' for folder in folders if u.EditorAssetLibrary.does_asset_exist(f'{AOF}/{folder}/{stem}')]
            if not found:
                raise RuntimeError(f'Piece du catalogue absente du projet : {stem} ({", ".join(folders)})')
            library.static[mesh] = u.EditorAssetLibrary.load_asset(found[0])
        return library.static[mesh]

    library.static_mesh = static_mesh
    return library


def aof_materials(actor, materials):
    """Une piece du catalogue prend les finitions peintes de l'arene, emplacement par emplacement
    (stone_cream, bronze, wood...) : elle s'accorde au monument, et les instances de
    M_AOF_Surface a occlusion (stone_cream, wood) ne compilent pas (19 octobre 2026)."""
    comp = actor.static_mesh_component
    for index, slot in enumerate(comp.static_mesh.get_editor_property('static_materials')):
        name = str(slot.get_editor_property('material_slot_name'))
        key = next((k for k in materials if name == k or name.startswith((k + '_', k + '.'))), None)
        if key is not None:
            comp.set_material(index, materials[key])


def place_flames(level, frame, doc, library, items):
    """La flamme des braseros et des lanternes (leur lumiere vient de `light` dans la description)."""
    burning = [item for item in items if item.get('flame')]
    if not burning:
        return 0
    material = arena_fate_atmosphere.fire_material()
    mesh = library.static_mesh(FLAME)
    nanite = mesh.get_editor_property('nanite_settings')
    if nanite.enabled:
        # Les petites flammes passent par le deplacement de sommets ordinaire (comme dans l'arene).
        nanite.enabled = False
        mesh.set_editor_property('nanite_settings', nanite)
        u.EditorAssetLibrary.save_loaded_asset(mesh)
    for item in burning:
        x, y, z = item['position']
        z += scene.storey_z(doc, item.get('storey', 0)) + item['light'].get('height', 0.0)
        size = item['flame']
        actor = level.spawn(mesh, frame.map_point([x, y, z]), frame.rotation(item.get('yaw', 0)),
                            'Feu_' + item['id'], f"{FOLDER}/feux", u.Vector(size, size, size))
        comp = actor.static_mesh_component
        comp.set_mobility(u.ComponentMobility.MOVABLE)
        comp.set_material(0, material)
        comp.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property('cast_shadow', False)
    return len(burning)


def main():
    t0 = time.time()
    doc = json.loads(SOURCE.read_text(encoding='utf-8'))
    metadata = json.loads(GEOMETRY.read_text(encoding='utf-8'))['metadata']
    site = json.loads(RELIEF.read_text(encoding='utf-8')).get('arena')
    if not site:
        raise RuntimeError('relief-reference/manifest.json sans emprise d\'arene : relancer prepare_capitale_reference.py')
    cx, cy = site['centre_m']
    ground = site['sol_m']
    cap = site['cap_deg']

    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if world is None:
        raise RuntimeError(PACKAGE)
    # Les acteurs d'une pose precedente (statiques et feux), tous charges pour etre retires.
    u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in u.WorldPartitionBlueprintLibrary.get_actor_descs()])
    old = [a for a in u.EditorLevelLibrary.get_all_level_actors() if TAG in [str(t) for t in a.tags]]
    stale = [a.get_package().get_name() for a in old]
    for a in old:
        u.get_editor_subsystem(u.EditorActorSubsystem).destroy_actor(a)

    materials = arena_wicked_materials.build_materials('painted')
    materials['wash_water'] = scene.flat_material('/Game/Bibliotheque/ArenaFate/Materials/M_WashWater',
                                                  u.LinearColor(0.035, 0.095, 0.115, 1.0), roughness=0.22)
    library = aof_library(arena.arena_library(scene))
    library.content_root = KIT
    # Le repere des .glb, mesure sur la piece temoin des accessoires, comme la carte de l'arene :
    # une piece du kit ne convient pas, son repli Nanite complet (collision fidele) deplace ses bornes.
    fixtures = scene.Library(scene.FIXTURE_ASSETS.relative_to(ROOT).as_posix())
    frame = scene.Frame(scene.FIXTURE_ASSETS / scene.FRAME_REFERENCE, fixtures.static_mesh(scene.FRAME_REFERENCE))
    # La marche suit les sols, gradins et escaliers tels qu'ils sont dessines : repli Nanite
    # complet (la collision d'un maillage Nanite se prend sur son repli, qui effacait les
    # marches des escaliers caches) et anneaux par leur collision architecturale ; les portes du
    # haut mur et les bouches des vomitoires de meme.
    walkable = dict(doc, objects=[dict(o, folder='stairs') if Path(o['mesh']).stem in ('afm-summa-wall-door', 'afm-vomitorium')
                                  else o for o in doc['objects']])
    arena.preserve_walkable_collision(library, walkable)
    east, south = frame.map_point([1, 0, 0]), frame.map_point([0, 1, 0])
    if (round(east.x), round(east.y), round(south.x), round(south.y)) != (100, 0, 0, 100):
        raise RuntimeError(f'Repere inattendu : est {east}, sud {south} (la capitale pose x a l\'est, y au sud)')

    level = scene.Level(world)
    offset = u.Vector(cx * 100.0, cy * 100.0, ground * 100.0)
    turn = u.Rotator(0.0, 0.0, cap)  # roll, pitch, yaw
    before = {a.get_path_name() for a in u.EditorLevelLibrary.get_all_level_actors()}
    placed = 0
    # La coupe de la camera (AJadgWitnessReview, pose par capitale_demo.py) : les pieces que le
    # manifeste marque cachent ce qui les traverse entre la camera et le groupe, et ce qu'elles
    # portent part avec elles, comme dans la carte de l'arene du LOT-1022.
    occluders = {o['id'] for o in json.loads(GEOMETRY.read_text(encoding='utf-8'))['objects'] if o.get('occluder')}
    cut, props = [], []
    for item in doc['objects']:
        actor = scene.place_object(level, frame, doc, library, item, f"{FOLDER}/{item.get('folder', 'objets')}")
        if item['id'] in occluders:
            actor.tags = list(actor.tags) + ['JadgWitnessOccluder']
        cut.append({**item, 'actor': actor})
        if item['mesh'].startswith('Built/arena-fate-props/'):
            props.append({**item, 'actor': actor})
        if item['mesh'].startswith(('Built/arena-fate-modern/', 'Built/arena-fate-props/', arena.LEGACY_SCENE + 'af-effigy-chains-')):
            arena.set_materials(actor, materials, item, metadata)
        elif item['mesh'].startswith('Built/aof-'):
            aof_materials(actor, materials)
        stem = Path(item['mesh']).stem
        if stem.startswith('afp-nameplate-') or stem == 'afp-fumetsu-plinth-collar':
            actor.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
        placed += 1
    # Avant le deplacement : le lien se trace sous chaque objet, autour de l'origine.
    supports = arena.link_cutaway_supports(frame, doc, cut, metadata)
    flames = place_flames(level, frame, doc, library, doc['objects'])
    # Les appliques, lanternes et braseros des accessoires de l'arene : leur flamme et leur lumiere,
    # aux profils interieurs de la description (vestiaires 240 cd, prison 200...), comme dans la
    # carte du LOT-1022. Sans elles, vestiaires, prison et couloirs restaient noirs (20 octobre 2026).
    atmosphere = arena_fate_atmosphere.install(level, frame, doc, library, metadata, props)
    # Les objets et leurs feux, poses autour de l'origine, rejoignent l'emprise.
    tagged = [a for a in u.EditorLevelLibrary.get_all_level_actors() if a.get_path_name() not in before]
    for a in tagged:
        local = a.get_actor_location()
        a.set_actor_location(offset + u.MathLibrary.rotate_angle_axis(local, cap, u.Vector(0, 0, 1)), False, False)
        a.set_actor_rotation(u.MathLibrary.compose_rotators(a.get_actor_rotation(), turn), False)
        a.tags = list(a.tags) + [TAG]
        # Sa partition de streaming, sans HLOD (configure_capitale_streaming.py, grille Arene).
        a.set_editor_property('runtime_grid', 'Arene')
        a.set_editor_property('is_spatially_loaded', True)
        a.set_editor_property('enable_auto_lod_generation', False)
        # Les feux et les lampes s'effacent au-delà de 60 m (fondu de 15 m) : leur flamme reste, seule
        # leur lumière, invisible de si loin, ne coûte plus (profil du 20 octobre 2026, 43 lumières).
        if a.get_class().get_name() == 'PointLight':
            light = a.point_light_component
            light.set_editor_property('max_draw_distance', LIGHT_DISTANCE)
            light.set_editor_property('max_distance_fade_range', LIGHT_FADE)
    if not u.EditorLevelLibrary.save_current_level() or not u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Sauvegarde de la carte et des acteurs de l\'arene')
    # La sauvegarde n'efface pas toujours le paquet externe d'un acteur detruit : il revenait au
    # chargement suivant, a cote de la nouvelle pose (19 octobre 2026, 1 826 acteurs en double).
    content = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_content_dir()))
    erased = 0
    for name in stale:
        path = content / (name[len('/Game/'):] + '.uasset')
        if path.is_file():
            path.unlink()
            erased += 1
    report = dict(map=PACKAGE, source=str(SOURCE.relative_to(ROOT)), objects=placed, actors=len(tagged),
                  removed=len(old), erased=erased, flames=flames, centre_m=[cx, cy], ground_m=ground, cap_deg=cap, kit=KIT,
                  atmosphere={k: (len(v) if isinstance(v, list) else v) for k, v in atmosphere.items()},
                  occluders=len(occluders & {o['id'] for o in doc['objects']}), supported=len(supports['linked']),
                  without_floor=len(supports['withoutFloorBelow']),
                  imported=library.imported, seconds=round(time.time() - t0, 1))
    out = ROOT / 'Saved/Jadg/capitale-arene.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CAPITALE_ARENA_READY', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
