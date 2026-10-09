# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Tests du contrôle des orphelins (`scripts/checks/check_orphans.py`, LOT-1001)."""
import json

import check_orphans as O


def ecrire(path, content=''):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content)
    path.write_text(content, encoding='utf-8')
    return path


def kit(tmp_path):
    """Un arbre d'assets conforme : une scène, un effet animé, un personnage, une police."""
    assets = tmp_path / 'Assets'
    ecrire(assets / 'Zone/Scene/manifest.json', {'textures': {
        'scene/wall': {'file': 'walls/wall.png', 'source': {'file': 'Atelier/mur.png'}},
        'scene/roof': {'mesh': 'roofs/roof.glb'}}})
    ecrire(assets / 'Zone/Scene/walls/wall.png')
    ecrire(assets / 'Zone/Scene/roofs/roof.glb')
    ecrire(assets / 'Common/Fx/manifest.json', {'textures': {'arrow': {'file': 'arrow.png'}}})
    ecrire(assets / 'Common/Fx/arrow.png')
    ecrire(assets / 'Common/Fx/arrow.anim.json', {'clips': {}})
    ecrire(assets / 'Common/Characters/manifest.json', {'npcs': ['Heroes/brawler']})
    ecrire(assets / 'Common/Characters/Heroes/brawler/walk-se.png')
    ecrire(assets / 'Common/Characters/Heroes/brawler/walk-se.anim.json', {'clips': {}})
    ecrire(assets / 'Fonts/Cinzel.ttf')
    ecrire(assets / 'Fonts/Cinzel-LICENSE.txt')
    ecrire(assets / 'README.md')
    ecrire(assets / '.kits/common.json', {'walls/ghost.png': 'abc'})
    return assets


CODE = 'load("manifest.json"); font("Cinzel.ttf");'


def test_un_arbre_conforme_n_a_pas_d_orphelin(tmp_path):
    assert O.check_assets(kit(tmp_path), CODE) == []


def test_un_fichier_que_rien_ne_cite_est_un_orphelin(tmp_path):
    assets = kit(tmp_path)
    ecrire(assets / 'Zone/Scene/walls/old-wall.png')
    ecrire(assets / 'Zone/Scene/roofs/old-roof.glb')
    errors = O.check_assets(assets, CODE)
    assert [e.split(' : ')[0] for e in errors] == ['Zone/Scene/roofs/old-roof.glb', 'Zone/Scene/walls/old-wall.png']


def test_une_entree_sans_fichier_est_une_erreur(tmp_path):
    assets = kit(tmp_path)
    (assets / 'Zone/Scene/roofs/roof.glb').unlink()
    (errors,) = O.check_assets(assets, CODE)
    assert 'Zone/Scene/manifest.json' in errors and 'fichier absent roofs/roof.glb' in errors


def test_un_dossier_de_personnage_absent_est_une_erreur(tmp_path):
    assets = kit(tmp_path)
    ecrire(assets / 'Common/Characters/manifest.json', {'npcs': ['Heroes/mage']})
    errors = O.check_assets(assets, CODE)
    assert any('dossier absent Heroes/mage' in e for e in errors)
    # Et les bandes du brawler, que plus personne ne cite, ressortent.
    assert any(e.startswith('Common/Characters/Heroes/brawler/walk-se.png') for e in errors)


def test_la_provenance_ne_cite_rien(tmp_path):
    assets = kit(tmp_path)
    # Le fichier nommé par `source` existe par hasard dans l'arbre : il n'en est pas cité pour autant.
    ecrire(assets / 'Zone/Scene/Atelier/mur.png')
    (error,) = O.check_assets(assets, CODE)
    assert error.startswith('Zone/Scene/Atelier/mur.png')


def test_l_animation_suit_son_image(tmp_path):
    assets = kit(tmp_path)
    (assets / 'Common/Fx/arrow.png').unlink()
    ecrire(assets / 'Common/Fx/manifest.json', {'textures': {}})
    (error,) = O.check_assets(assets, CODE)
    assert error.startswith('Common/Fx/arrow.anim.json')


def test_un_manifeste_ou_une_police_que_le_code_ne_nomme_pas_est_un_orphelin(tmp_path):
    assets = kit(tmp_path)
    ecrire(assets / 'Zone/Scene/legacy.json', {})
    ecrire(assets / 'Fonts/Oubliee.ttf')
    errors = O.check_assets(assets, CODE)
    assert sorted(e.split(' : ')[0] for e in errors) == ['Fonts/Oubliee.ttf', 'Zone/Scene/legacy.json']


def test_l_atlas_cite_depuis_la_racine_des_assets(tmp_path):
    assets = kit(tmp_path)
    ecrire(assets / 'Zone/Map/zone.jpg')
    ecrire(assets / 'Maps/world.jpg')
    assert len(O.check_assets(assets, CODE)) == 2
    atlas = ecrire(tmp_path / 'world-maps.json', {'zones': [{'image': 'Zone/Map/zone.jpg'}], 'file': 'world.jpg'})
    assert O.check_assets(assets, CODE, atlas) == []


def test_un_manifeste_cite_aussi_depuis_la_racine_des_assets(tmp_path):
    """Le manifeste des maîtres nomme ses pièces depuis la racine, et ses doublons écartés ne citent rien."""
    assets = kit(tmp_path)
    ecrire(assets / 'Master/manifest.json', {
        'pieces': [{'file': 'Master/Npc/guard.glb', 'source': 'Npc/Meshy_guard.glb'}],
        'duplicates': [{'file': 'Npc/Meshy_guard (1).glb'}]})
    ecrire(assets / 'Master/Npc/guard.glb')
    assert O.check_assets(assets, CODE) == []
    (assets / 'Master/Npc/guard.glb').unlink()
    (error,) = O.check_assets(assets, CODE)
    assert 'fichier absent Master/Npc/guard.glb' in error


def test_une_piece_en_attente_de_son_lecteur_n_est_pas_orpheline(tmp_path):
    assets = kit(tmp_path)
    ecrire(assets / 'Fonts/Attendue.ttf')
    assert len(O.check_assets(assets, CODE)) == 1
    ecrire(assets / 'awaiting.json', {'awaiting': [{'file': 'Fonts/Attendue.ttf', 'lot': 'LOT-1020'}]})
    planning = tmp_path / 'Planning'
    fiche = ecrire(planning / 'versions/v0/lots/LOT-1020-interface.md', '+++\nstatut = "a-faire"\n+++\n')
    code = CODE + ' "awaiting.json"'
    assert O.check_assets(assets, code, planning=planning) == []
    # Le lot livré, la pièce n'attend plus : son lecteur la cite, ou elle se supprime.
    ecrire(fiche, '+++\nstatut = "livre"\n+++\n')
    (error,) = O.check_assets(assets, code, planning=planning)
    assert 'Fonts/Attendue.ttf attend le LOT-1020, qui est livré' in error
    # Une entrée sans lot n'attend rien.
    ecrire(assets / 'awaiting.json', {'awaiting': [{'file': 'Fonts/Attendue.ttf'}]})
    (error,) = O.check_assets(assets, code, planning=planning)
    assert "n'attend aucun lot" in error


def depot(tmp_path):
    scripts = tmp_path / 'scripts'
    ecrire(scripts / 'checks/check_a.py', 'import helper\n')
    ecrire(scripts / 'checks/helper.py')
    ecrire(scripts / 'build.ps1')
    ecrire(scripts / 'outil/__init__.py')
    ecrire(scripts / 'outil/__main__.py', 'from .extraction import run\n')
    ecrire(scripts / 'outil/extraction.py')
    ecrire(scripts / 'tests/test_check_a.py', 'import check_a\n')
    ecrire(scripts / 'tests/conftest.py')
    return scripts


CALLERS = 'run: python3 scripts/checks/check_a.py\npwsh scripts/build.ps1\npython -m outil extraire\n'


def test_un_script_appele_et_ce_qu_il_importe_ne_sont_pas_orphelins(tmp_path):
    assert O.check_scripts(depot(tmp_path), CALLERS) == []


def test_un_script_que_seul_son_test_nomme_est_un_orphelin(tmp_path):
    scripts = depot(tmp_path)
    ecrire(scripts / 'assetsGeneration/check_figure_walk.py')
    ecrire(scripts / 'tests/test_check_figure_walk.py', 'import check_figure_walk\n')
    (error,) = O.check_scripts(scripts, CALLERS)
    assert error.startswith('scripts/assetsGeneration/check_figure_walk.py')


def test_un_nom_plus_long_n_appelle_pas_un_script(tmp_path):
    scripts = depot(tmp_path)
    # `pre_check_a.py` et `check_a.pyc` ne sont pas `check_a.py`.
    errors = O.check_scripts(scripts, 'run: python3 scripts/pre_check_a.py\npwsh scripts/build.ps1\n-m outil\n')
    assert sorted(e.split(' : ')[0] for e in errors) == ['scripts/checks/check_a.py', 'scripts/checks/helper.py']


def test_un_paquet_sans_appelant_emporte_ses_modules(tmp_path):
    errors = O.check_scripts(depot(tmp_path), 'run: python3 scripts/checks/check_a.py\npwsh scripts/build.ps1\n')
    assert sorted(e.split(' : ')[0] for e in errors) == [
        'scripts/outil/__init__.py', 'scripts/outil/__main__.py', 'scripts/outil/extraction.py']


def test_l_histoire_n_appelle_rien(tmp_path):
    ecrire(tmp_path / 'CHANGELOG.md', 'scripts/vieux.py')
    ecrire(tmp_path / 'Planning/standards/archives/ancien.md', 'python scripts/vieux.py')
    ecrire(tmp_path / 'Planning/versions/v0/lots/LOT-1.md', 'scripts/vieux.py')
    ecrire(tmp_path / 'Documentation/Guide/guide.md', 'python scripts/neuf.py')
    text = O.callers(tmp_path)
    assert 'neuf.py' in text and 'vieux.py' not in text


def projet(tmp_path):
    """Un dépôt dont trois scripts produisent des sorties du moteur."""
    ecrire(tmp_path / 'scripts/maps/build_scene.py', 'KIT_ROOT = "/Game/Kit"\nCUBE = "/Game/Scenes/Common/T_White"\n')
    ecrire(tmp_path / 'scripts/assets/build_manifest.py', 'FAMILIES = {"npc": "/Game/Master/Npc"}\n')
    ecrire(tmp_path / 'scripts/tests/test_build_scene.py', 'assert "/Game/Essai/SM_Test"\n')
    ecrire(tmp_path / 'scripts/maps/build_level.py', 'PORTE = "/Game/Maps/Porte"\n')
    content = tmp_path / 'Content'
    ecrire(content / 'Kit/Regions/arena/af-pyre/StaticMeshes/SM_af-pyre.uasset')
    ecrire(content / 'Master/Npc/guard/StaticMeshes/SM_Npc_Guard.uasset')
    ecrire(content / 'Scenes/Common/T_White.uasset')
    ecrire(content / 'Maps/Porte.umap')
    return content


def test_une_sortie_du_moteur_citee_par_son_script_n_est_pas_orpheline(tmp_path):
    content = projet(tmp_path)
    cited = O.content_citations(tmp_path)
    assert cited == {'/Game/Kit', '/Game/Scenes/Common/T_White', '/Game/Master/Npc', '/Game/Maps/Porte'}
    assert O.check_content(content, cited) == []


def test_un_uasset_qu_aucun_script_ne_produit_est_une_erreur(tmp_path):
    content = projet(tmp_path)
    ecrire(content / 'Developers/auteur/BP_Essai.uasset')
    ecrire(content / 'Maps/Porte_Essai.umap')       # un nom plus long n'est pas la carte citée
    ecrire(content / 'Scenes/Common/T_Whiter.uasset')
    ecrire(content / 'Essai/SM_Test.uasset')        # un test n'est pas un script qui produit
    errors = O.check_content(content, O.content_citations(tmp_path))
    assert sorted(e.split(' : ')[0] for e in errors) == [
        'Content/Developers/auteur/BP_Essai.uasset', 'Content/Essai/SM_Test.uasset',
        'Content/Maps/Porte_Essai.umap', 'Content/Scenes/Common/T_Whiter.uasset']


def test_un_fichier_qui_n_est_pas_une_sortie_du_moteur_n_a_rien_a_faire_sous_content(tmp_path):
    content = projet(tmp_path)
    ecrire(content / 'Kit/notes.txt')
    (error,) = O.check_content(content, O.content_citations(tmp_path))
    assert error.startswith('Content/Kit/notes.txt')


def test_une_piece_de_decor_est_citee_par_sa_fiche(tmp_path):
    # LOT-1019 : la fiche d'une pièce (manifeste des maîtres, des bibliothèques) nomme son asset ;
    # le dossier de la pièce est cité, pas ses voisins.
    content = projet(tmp_path)
    ecrire(tmp_path / 'Source/Elements/Assets/Library/manifest.json', json.dumps({'pieces': [
        {'id': 'rocher', 'asset': '/Game/Library/rocher/StaticMeshes/SM_rocher'}]}))
    ecrire(content / 'Library/rocher/StaticMeshes/SM_rocher.uasset')
    ecrire(content / 'Library/caillou/StaticMeshes/SM_caillou.uasset')
    cited = O.content_citations(tmp_path)
    assert '/Game/Library/rocher' in cited
    (error,) = O.check_content(content, cited)
    assert error.startswith('Content/Library/caillou/')


def test_sans_dossier_content_il_n_y_a_rien_a_verifier(tmp_path):
    assert O.check_content(tmp_path / 'Content', set()) == []


def test_le_depot_n_a_pas_de_script_orphelin():
    # Les assets demandent les kits installés ; les scripts, eux, se jugent sur le dépôt nu.
    assert O.check_scripts(O.ROOT / 'scripts', O.callers(O.ROOT)) == []
