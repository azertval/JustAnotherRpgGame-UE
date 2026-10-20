"""Le streaming World Partition de la capitale : ce qui se charge autour du joueur, ce qui se voit
de loin (HLOD), pour que le poste de 16 Go ne tienne jamais toute la carte en memoire.

Lancer dans l'editeur, sans rendu, apres `finalize_reference_relief.py` (Nanite construit) :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript
        -script=<chemin absolu de ce fichier> -nullrhi -unattended -nosplash -NoSound

La carte est convertie avec un `WorldPartitionRuntimeHashSet` (une partition principale et trois
niveaux de HLOD : instancie, fusionne, persistant). Les Landscape sont decoupes en mandataires de
504 m (4 x 4 composants de 63 quads de 2 m). Reglages :

- partition principale : cellules de 504 m (un mandataire par cellule), chargees a 1 600 m : le
  relief Nanite complet, ses couches et sa collision n'existent qu'autour du joueur ;
- HLOD 1 (instancie) : les memes cellules de 504 m, chargees a 3 200 m. Un HLOD ne reste affiche
  que tant que toutes les cellules qu'il couvre ne sont pas chargees : plus grand que la cellule
  principale, il chevaucherait le relief deja charge (scintillement, ombres parasites, essai du
  17 octobre 2026) ;
- HLOD 2 (fusionne) : encore les cellules de 504 m (a 1 008 m, il masquait les cellules chargees
  qu'il couvrait en partie : une bande manquait a la vue d'ensemble), chargees a 6 400 m, toute la
  carte vue d'en haut ;
- le HLOD du Landscape se prend a la LOD 2 (mailles de 8 m), texture de 512 par mandataire : le
  constructeur ajoute toujours a un Landscape Nanite une jupe d'une maille de profondeur ; a la LOD
  la plus grossiere (reglage d'origine) elle faisait 63 m et passait pour une rangee manquante au
  bord sud de la vue d'ensemble ;
- l'eau (huit maillages, ~200 000 triangles) reste toujours chargee et hors des HLOD : sa matiere
  (Single Layer Water) ne s'aplatit pas en texture, le constructeur de HLOD echoue a la cuire ;
- les acteurs sans etendue (ciel, lumiere, cadrages, depart) restent toujours charges.

Les HLOD se construisent ensuite par `WorldPartitionHLODsBuilder` (etape « hlod » de
`rebuild_capitale_relief.ps1`).
"""
import json
from pathlib import Path

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
PACKAGE = '/Game/Capitale/Cartes/Capitale'
# Nom de la partition ou du niveau de HLOD -> (cellule, portee de chargement), en centimetres.
# Les portees ne sont pas des multiples de la cellule : une cellule dont le bord tombe pile a la
# portee restait ni chargee ni representee par son HLOD (un trou dans la vue d'ensemble).
GRIDS = {'MainPartition': (50400, 160000), 'HLODLayer_Instanced': (50400, 320000), 'HLODLayer_Merged': (50400, 640000),
         'Arene': (100800, 450000)}
# L'Arena of Fate (place_capitale_arena.py) a sa partition, sans HLOD : le HLOD fusionne de sa
# cellule (2 300 acteurs Nanite) fait planter le processeur graphique du poste a la cuisson
# (19 octobre 2026). Chargee a 4,5 km, elle se voit de toute la carte ; ses acteurs y vont par
# leur RuntimeGrid.
ARENA_GRID = 'Arene'
# HLOD du Landscape (reglages « HLOD Mesh Source LOD » et « HLOD Texture Size » du Landscape).
HLOD_MESH_LOD, HLOD_TEXTURE = 2, 512
GLOBAL = ('JadgShot', 'JadgDayLight', 'JadgMapFrame', 'PlayerStart', 'SkyAtmosphere', 'SkyLight', 'DirectionalLight',
          'ExponentialHeightFog', 'PostProcessVolume', 'WorldPartitionMiniMap')


def main():
    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    assert world, PACKAGE
    if not u.JadgSceneBuild.set_world_partition_streaming(world, True):
        raise RuntimeError('Streaming World Partition refuse')
    runtime_hash = u.JadgSceneBuild.world_partition_runtime_hash(world)
    if runtime_hash.get_class().get_name() != 'WorldPartitionRuntimeHashSet':
        raise RuntimeError('Hachage inattendu : ' + runtime_hash.get_class().get_name())
    report = {}
    partitions = runtime_hash.get_editor_property('RuntimePartitions')
    if ARENA_GRID not in [str(d.get_editor_property('Name')) for d in partitions]:
        # Python ne sait ni construire la description d'une partition ni nommer sa grille.
        cell, reach = GRIDS[ARENA_GRID]
        if not u.JadgSceneBuild.add_runtime_partition(world, ARENA_GRID, cell, reach):
            raise RuntimeError('Partition ' + ARENA_GRID)
        partitions = runtime_hash.get_editor_property('RuntimePartitions')
    for desc in partitions:
        layers = [(str(desc.get_editor_property('Name')), desc.get_editor_property('MainLayer'))]
        layers += [(str(s.get_editor_property('Name')), s.get_editor_property('PartitionLayer'))
                   for s in desc.get_editor_property('HLODSetups')]
        for name, layer in layers:
            if name not in GRIDS:
                report[name or 'persistant'] = layer.get_class().get_name()
                continue
            cell, reach = GRIDS[name]
            layer.modify()
            layer.set_editor_property('CellSize', cell)
            layer.set_editor_property('LoadingRange', reach)
            layer.set_editor_property('bBlockOnSlowStreaming', False)
            report[name] = dict(cell_m=cell / 100, loading_m=reach / 100)
    missing = set(GRIDS) - set(report)
    if missing:
        raise RuntimeError('Partitions absentes : ' + ', '.join(sorted(missing)))
    runtime_hash.modify()
    runtime_hash.set_editor_property('RuntimePartitions', partitions)

    # Les acteurs : le terrain dans les cellules, l'eau et le reste toujours charges.
    descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
    u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    spatial, always, packages = 0, 0, {}
    for a in actors:
        kind = a.get_class().get_name()
        if kind in ('Landscape', 'LandscapeStreamingProxy'):
            # Le HLOD du relief : maillage pris a la LOD 2 (pas de 8 m) et texture de 512 (1 m par
            # texel) pour 504 m. La LOD la plus grossiere, reglage d'origine, ne garde qu'un quad par
            # composant de 126 m : le constructeur y ajoute une jupe d'une maille de profondeur
            # (63 m), visible au bord de la carte comme une rangee de cellules manquante (vue
            # d'ensemble, 17 octobre 2026) ; a la LOD 2 elle descend a 4 m.
            a.set_editor_property('hlod_mesh_source_lod_policy', u.LandscapeHLODMeshSourceLODPolicy.SPECIFIC_LOD)
            a.set_editor_property('hlod_mesh_source_lod', HLOD_MESH_LOD)
            a.set_editor_property('hlod_texture_size_policy', u.LandscapeHLODTextureSizePolicy.SPECIFIC_SIZE)
            a.set_editor_property('hlod_texture_size', HLOD_TEXTURE)
            if kind == 'Landscape':
                packages[a.get_package().get_name()] = a.get_package()
                continue
            a.set_editor_property('is_spatially_loaded', True)
            spatial += 1
        elif kind == 'StaticMeshActor' and 'CapitaleEauReference' in [str(t) for t in a.tags]:
            a.set_editor_property('is_spatially_loaded', False)
            a.set_editor_property('enable_auto_lod_generation', False)
            always += 1
        elif kind in GLOBAL:
            a.set_editor_property('is_spatially_loaded', False)
            always += 1
        else:
            continue
        packages[a.get_package().get_name()] = a.get_package()
    if not u.EditorLoadingAndSavingUtils.save_packages(list(packages.values()), False):
        raise RuntimeError('Acteurs non enregistres')
    if not u.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        raise RuntimeError('Carte non enregistree')
    report = dict(map=PACKAGE, streaming=u.JadgSceneBuild.is_world_partition_streaming(world), partitions=report,
                  spatially_loaded=spatial, always_loaded=always,
                  landscape_hlod=dict(mesh_lod=HLOD_MESH_LOD, texture=HLOD_TEXTURE))
    (ROOT / 'Saved/Jadg').mkdir(parents=True, exist_ok=True)
    (ROOT / 'Saved/Jadg/capitale-streaming.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CAPITALE_STREAMING_READY', json.dumps(report), flush=True)


main()
