"""Retire toute la vegetation de la carte de la capitale (/Game/Capitale/Cartes/Capitale) :
demande de l'auteur du 19 octobre 2026, qui remplace les forets hors les murs du 18 octobre.

Lancer dans l'editeur, sans rendu :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript
        -script=<chemin absolu de ce fichier> -nullrhi -unattended -nosplash -NoSound

Ce qui part :

- le volume PCG des forets, ses acteurs de partition (les ~227 000 instances generees) et l'acteur
  monde du PCG ;
- le graphe PCG et le Landscape Grass Type des prairies (`/Game/Capitale/Ressources/Vegetation`) ;
  la matiere `M_TerrainNaturel` ne fait plus pousser d'herbe (`build_capitale_terrain_material.py`) ;
- les cadrages `foret-*`, qui ne montrent plus rien.

Les packs du Fab (`CommonHazel`, Megascans) restent dans le projet : ils ne sont plus poses. Sans
effet sur une carte deja nue : l'etape « sans-vegetation » de `rebuild_capitale_relief.ps1` le
rejoue a chaque reconstruction.
"""
from pathlib import Path
import json

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
PACKAGE = '/Game/Capitale/Cartes/Capitale'
FOLDER = '/Game/Capitale/Ressources/Vegetation'
CLASSES = ('PCGVolume', 'PCGPartitionActor', 'PCGWorldActor', 'InstancedFoliageActor')
al = u.EditorAssetLibrary


def main():
    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if world is None:
        raise RuntimeError(PACKAGE)
    descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
    u.WorldPartitionBlueprintLibrary.load_actors(
        [d.guid for d in descs if d.native_class and d.native_class.get_name() in CLASSES + ('JadgShot',)])
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    removed = {}
    for a in actors.get_all_level_actors():
        kind = a.get_class().get_name()
        shot = kind == 'JadgShot' and str(a.get_editor_property('shot_id')).startswith('foret-')
        if kind in CLASSES or shot:
            actors.destroy_actor(a)
            removed[kind] = removed.get(kind, 0) + 1
    # Les composants du Landscape gardent en cache les types d'herbe de leur matiere : relus sur la
    # matiere sans herbe, ils ne citent plus le type des prairies, qui peut partir.
    u.WorldPartitionBlueprintLibrary.load_actors(
        [d.guid for d in descs if d.native_class and d.native_class.get_name() in ('Landscape', 'LandscapeStreamingProxy')])
    grass = 0
    for a in actors.get_all_level_actors():
        if a.get_class().get_name() in ('Landscape', 'LandscapeStreamingProxy'):
            left = u.JadgSceneBuild.refresh_landscape_grass(a)
            if left:
                raise RuntimeError(f'{a.get_actor_label()} cite encore {left} type(s) d\'herbe')
            grass += 1
    # La sauvegarde du niveau retire du disque les paquets externes des acteurs detruits.
    if not u.EditorLevelLibrary.save_current_level() or not u.EditorLoadingAndSavingUtils.save_dirty_packages(True, True):
        raise RuntimeError('Sauvegarde de la carte sans vegetation')
    removed['landscape_grass_refreshed'] = grass
    assets = []
    if al.does_directory_exist(FOLDER):
        # Les composants PCG detruits tiennent encore le graphe en memoire : la carte est dechargee
        # avant la suppression.
        u.EditorLoadingAndSavingUtils.new_blank_map(False)
        u.SystemLibrary.collect_garbage()
        assets = [str(p) for p in al.list_assets(FOLDER, recursive=True)]
        refused = [p for p in assets if not al.delete_asset(p)]
        if refused or not al.delete_directory(FOLDER):
            raise RuntimeError('Suppression de ' + FOLDER + ' : ' + ', '.join(refused))
    report = dict(map=PACKAGE, removed=removed, deleted_assets=assets)
    (ROOT / 'Saved/Jadg').mkdir(parents=True, exist_ok=True)
    (ROOT / 'Saved/Jadg/capitale-sans-vegetation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('CAPITALE_SANS_VEGETATION', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
