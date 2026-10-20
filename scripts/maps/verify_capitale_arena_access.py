"""Les gradins de l'Arena of Fate desservis depuis le parvis, sur la carte de la capitale.

Lancer dans l'editeur, sans rendu, apres `place_capitale_arena.py` :

    UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript
        -script=<chemin absolu de ce fichier> -nullrhi -unattended -nosplash -NoSound

Charge l'arene et le relief, pose un volume de navigation autour de l'arene (jamais
sauvegarde), construit le maillage de navigation et cherche un chemin depuis le parvis vers
chaque point du parcours et chaque cible du manifeste de l'arene (`route`, `navigationTargets` :
deambulatoires, escaliers caches, praecinctiones, loges), puis vers l'arrivee du groupe et chaque
personnage de la demo (`capitale_demo.py`). La carte n'est pas sauvegardee.

Les catacombes (-12 m) s'ouvrent par un mur a interrupteur cache (precision de l'auteur, 19 octobre
2026) : ferme au repos, il les retire du maillage de navigation, et leurs points sont comptes a
part. Tout autre point inatteignable est une erreur.
"""
from pathlib import Path
import json
import sys

import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
if str(ROOT / 'scripts/maps') not in sys.path:
    sys.path.insert(0, str(ROOT / 'scripts/maps'))

import capitale_demo  # noqa: E402
import jadg_map  # noqa: E402
PACKAGE = '/Game/Capitale/Cartes/Capitale'
GEOMETRY = ROOT / 'Source/Elements/Assets/Built/arena-fate-modern/manifest.json'
PLACED = ROOT / 'Saved/Jadg/capitale-arene.json'
START = [97.0, 0.0, 0.0]  # sur le parvis, devant la porte monumentale de l'est
CLOSED_BELOW = -11.0  # les catacombes, derriere le mur a interrupteur cache


def main():
    metadata = json.loads(GEOMETRY.read_text(encoding='utf-8'))['metadata']
    placed = json.loads(PLACED.read_text(encoding='utf-8'))
    (cx, cy), ground = placed['centre_m'], placed['ground_m']

    def world(p):
        return u.Vector((cx + p[0]) * 100.0, (cy + p[1]) * 100.0, (ground + p[2]) * 100.0 + 25.0)

    world_ = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if world_ is None:
        raise RuntimeError(PACKAGE)
    descs = u.WorldPartitionBlueprintLibrary.get_actor_descs()
    u.WorldPartitionBlueprintLibrary.load_actors([d.guid for d in descs])
    u.JadgSceneBuild.spawn_box_volume(world_, u.NavMeshBoundsVolume, u.Vector(cx * 100.0, cy * 100.0, ground * 100.0 + 2500.0),
                                      u.Vector(21000.0, 18000.0, 7000.0))
    # Le profil fin de la carte de l'arene (build_arena_fate_modern_scene.py) : des tuiles de 3 m et
    # douze couches par tuile. Aux tuiles de 10 m par defaut, les sept etages de l'arene depassaient
    # le nombre de couches d'une tuile, qui ne se raccordait plus a ses voisines.
    review = u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(
        u.load_class(None, '/Script/JustAnotherRpgGame.JadgWitnessReview'), u.Vector(), u.Rotator())
    for name, value in (('fine_navigation', True), ('navigation_cell_size', 10.0), ('navigation_cell_height', 5.0),
                        ('navigation_elevation_ratio', 1.0), ('navigation_tile_size', 300.0),
                        ('navigation_average_layers', 12.0), ('navigation_max_simplification_error', 1.3),
                        ('navigation_max_search_nodes', 32768)):
        review.set_editor_property(name, value)
    u.JadgSceneBuild.unreachable_points(world_, world(START), [])
    if not review.prepare_fine_navigation():
        raise RuntimeError('Profil de navigation fin refuse')
    # La demo (capitale_demo.py) : l'arrivee du groupe et chaque personnage, a son etage.
    demo = json.loads(capitale_demo.TARGET.read_text(encoding='utf-8'))
    places = [('entree', [*jadg_map.cell_centre(*jadg_map.entry_of(demo), demo['origin'])[:2], 0.0])]
    for entity in demo['entities']:
        if entity['type'] == 'npc':
            places.append((f"{entity['id']} {entity['dialogue']}", capitale_demo.reach_point(entity, demo)))
    points = metadata['route'] + metadata['navigationTargets']
    first_demo = len(points)
    points += [p for _, p in places]
    missing = list(u.JadgSceneBuild.unreachable_points(world_, world(START), [world(p) for p in points]))
    if missing == [-1]:
        raise RuntimeError('Le depart sur le parvis n\'est pas sur le maillage de navigation')
    route = len(metadata['route'])
    closed = [i for i in missing if points[i][2] < CLOSED_BELOW]
    missing = [i for i in missing if i not in closed]
    report = {
        'start': START,
        'route': route,
        'targets': len(metadata['navigationTargets']),
        'closedCatacombs': len(closed),
        'demo': len(places),
        'unreachableRoute': [{'index': i, 'point': points[i]} for i in missing if i < route],
        'unreachableTargets': [{'index': i - route, 'point': points[i]} for i in missing if route <= i < first_demo],
        'unreachableDemo': [{'place': places[i - first_demo][0], 'point': points[i]} for i in missing if i >= first_demo],
    }
    out = ROOT / 'Saved/Jadg/capitale-arene-acces.json'
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    summary = {k: report[k] if not isinstance(report[k], list) else len(report[k]) for k in report}
    if missing:
        raise RuntimeError(f"Points de l'arene inatteignables depuis le parvis (journal : {out}) : {summary}")
    print('CAPITALE_ARENA_ACCESS', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
