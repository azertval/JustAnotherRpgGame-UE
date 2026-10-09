# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests du mode Quêtes (LOT-144, LOT-1018) : la présence d'une entité sous des drapeaux, selon la
règle de Core, et les drapeaux qu'une carte lit sans qu'aucune quête ne les déclare."""

import pytest

import quest_mode


@pytest.mark.parametrize("entity, flags, expected", [
    ({}, {}, True),
    ({"presenceFlag": "porte/ouverte"}, {}, False),
    ({"presenceFlag": "porte/ouverte"}, {"porte/ouverte": "1"}, True),
    ({"presenceFlag": "porte/ouverte", "presenceTest": "unset"}, {}, True),
    ({"presenceFlag": "quete.pommes", "presenceValue": "acceptee|condamne"}, {"quete.pommes": "condamne"}, True),
    ({"presenceFlag": "quete.pommes", "presenceValue": "acceptee"}, {"quete.pommes": "inconnue"}, False),
    ({"presenceFlag": "quete.pommes", "presenceTest": "notEquals", "presenceValue": "acceptee"},
     {"quete.pommes": "inconnue"}, True),
])
def test_la_presence_suit_la_regle_de_core(entity, flags, expected):
    assert quest_mode.present(entity, flags)[0] is expected


def test_une_etape_suppose_les_drapeaux_qui_y_menent():
    flags = quest_mode.step_flags("pommes/acceptee")
    assert flags["quete.pommes"] == "acceptee"
    assert flags["quest/pommes/step/acceptee"] == "1"
    assert "quest/pommes/step/condamne" not in flags


def test_a_l_etape_acceptee_le_garde_parait_sur_le_parvis():
    shown = {entity["id"]: visible for entity, visible, _ in quest_mode.view("essai/parvis", quest_mode.step_flags("pommes/acceptee"))}
    hidden = {entity["id"]: visible for entity, visible, _ in quest_mode.view("essai/parvis", {})}
    guard = next(e["id"] for e, _, _ in quest_mode.view("essai/parvis", {}) if e.get("dialogue") == "garde")
    assert shown[guard] and not hidden[guard]


def test_un_drapeau_que_rien_ne_declare_se_signale():
    doc = {"entities": [{"id": "e1", "type": "npc", "presenceFlag": "quete.pomes"},
                        {"id": "e2", "type": "portal", "requiresFlag": "encounter/arene-bandits/won"}]}
    assert quest_mode.undeclared(doc, quest_mode.declared_flags()) == ["quete.pomes"]


def test_les_cartes_du_depot_ne_lisent_que_des_drapeaux_declares():
    assert quest_mode.main(["--check"]) == 0
