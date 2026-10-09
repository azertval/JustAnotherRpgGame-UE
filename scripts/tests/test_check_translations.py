# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Contrôle des catalogues de textes du jeu (scripts/checks/check_translations.py, LOT-1020)."""

from check_translations import code_keys, load, parse, problems


def catalogues(french, english):
    return {'fr': parse(french, 'fr.lang'), 'en': parse(english, 'en.lang')}


def test_catalogues_coherents_acceptes():
    assert problems(catalogues('hud.map = Carte\ncombat.round = Round %1\n',
                               'hud.map = Map\ncombat.round = Round %1\n')) == []


def test_cle_absente_refusee():
    found = problems(catalogues('hud.map = Carte\nhud.menu = Menu\n', 'hud.map = Map\n'))
    assert any('hud.menu' in line and 'manque' in line for line in found)


def test_cle_en_trop_refusee():
    found = problems(catalogues('hud.map = Carte\n', 'hud.map = Map\nhud.old = Old\n'))
    assert any('hud.old' in line for line in found)


def test_trous_differents_refuses():
    found = problems(catalogues('combat.round = Round %1\n', 'combat.round = Round\n'))
    assert any('trous' in line for line in found)


def test_valeur_vide_refusee():
    found = problems(catalogues('hud.map =\n', 'hud.map = Map\n'))
    assert any('vide' in line for line in found)


def test_cle_repetee_refusee():
    found = problems(catalogues('hud.map = Carte\nhud.map = Atlas\n', 'hud.map = Map\n'))
    assert any('répétée' in line for line in found)


def test_cle_du_code_absente_refusee():
    found = problems(catalogues('hud.map = Carte\n', 'hud.map = Map\n'), {'hud.menu'})
    assert any('code du jeu' in line and 'hud.menu' in line for line in found)


def test_espace_francais_avant_ponctuation_admis():
    assert problems(catalogues('a.b = Rencontre : %1\n', 'a.b = Encounter: %1\n')) == []


def test_catalogues_du_depot_coherents():
    assert problems(load(), code_keys()) == []
