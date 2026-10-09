# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests des cartes d'essai (LOT-1016, LOT-1017, LOT-1018) : une description v5 par carte, où la
grille que Core joue et ce que le moteur construit viennent du même plan. Sans moteur."""

import pytest

import build_essai_maps as essai
import jadg_map


def written(identifier: str) -> dict:
    return essai.map_doc(identifier, essai.MAPS[identifier])


def test_les_fichiers_du_depot_sont_a_jour():
    for path, text in essai.files().items():
        assert path.read_text(encoding="utf-8") == text, f"{path.name} : relancer build_essai_maps.py"


@pytest.mark.parametrize("identifier", sorted(essai.MAPS))
def test_une_carte_d_essai_passe_le_controle(identifier):
    doc = written(identifier)
    assert jadg_map.validate(doc) == []
    assert doc["format"] == "jadg-map" and doc["version"] == 5


@pytest.mark.parametrize("identifier", sorted(essai.MAPS))
def test_un_mur_de_la_grille_est_un_mur_construit(identifier):
    doc = written(identifier)
    walls = {(tile["x"], tile["y"]) for tile in doc["tiles"] if tile["type"] == "wall"}
    blocks = {(round(item["position"][0] / essai.CELL - 0.5), round(item["position"][1] / essai.CELL - 0.5))
              for item in doc["objects"] if item.get("folder") == "murs"}
    assert walls == blocks
    # Le mobilier montre une entité de la carte, sur sa case, à son étage : un coffre, un panneau.
    shown = {item["entity"]: item for item in doc["objects"] if "entity" in item}
    places = {entity["id"]: entity for entity in doc["entities"]}
    expected = {"essai/etals": ["chest", "sign"], "essai/etages": ["sign"]}.get(identifier, [])
    assert sorted(places[key]["type"] for key in shown) == expected
    storeys = doc.get("storeys") or [{"z": 0.0}]
    for key, item in shown.items():
        entity = places[key]
        assert item["position"] == essai.centre(entity["x"], entity["y"], storeys[entity.get("storey", 0)]["z"])
    # Le sol et la navigation couvrent la grille entière, coin de la case (0, 0) à l'origine.
    extent = [0.0, 0.0, doc["width"] * essai.CELL, doc["height"] * essai.CELL]
    assert doc["fills"][0]["areas"] == [extent]
    assert doc["navigation"]["area"] == extent
    assert doc["origin"] == [0.0, 0.0]


@pytest.mark.parametrize("identifier", sorted(essai.MAPS))
def test_chaque_pnj_a_son_personnage_et_le_groupe_entre(identifier):
    doc = written(identifier)
    assert doc["party"]["appearances"] == list(essai.HEROES)
    for entity in doc["entities"]:
        if entity["type"] == "npc":
            assert entity["appearance"] == essai.PUPPET
    assert doc["nextEntityId"] == len(doc["entities"]) + 1


def test_les_portails_menent_a_un_point_d_arrivee_qui_existe():
    docs = {identifier: written(identifier) for identifier in essai.MAPS}
    errors, _ = jadg_map.check_world(docs)
    assert errors == []
    crossed = sum(1 for doc in docs.values() for e in doc["entities"] if e["type"] == "portal" and not e["sealed"])
    assert crossed == 4


def test_la_zone_de_combat_et_le_marqueur_sont_des_volumes():
    doc = written("essai/arene")
    zone = next(e for e in doc["entities"] if e["type"] == "combatZone")
    assert zone["volume"] == {"min": [0.0, 0.0, -0.5], "max": [30.0, 21.0, 4.0]}
    assert "width" not in zone and "height" not in zone
    marker = next(e for e in doc["entities"] if e["type"] == "encounter")
    low, high = marker["volume"]["min"], marker["volume"]["max"]
    # Le volume du marqueur tient dans sa case.
    assert (low[0], low[1]) == (marker["x"] * essai.CELL, marker["y"] * essai.CELL)
    assert (high[0] - low[0], high[1] - low[1]) == (essai.CELL, essai.CELL)


def test_la_carte_a_deux_etages_superpose_le_portail_et_le_panneau():
    doc = written("essai/etages")
    assert [s["z"] for s in doc["storeys"]] == [0.0, essai.STOREY]
    by_id = {e["id"]: e for e in doc["entities"]}
    portal = next(e for e in by_id.values() if e["type"] == "portal")
    sign = next(e for e in by_id.values() if e["type"] == "sign")
    assert (portal["x"], portal["y"], portal.get("storey", 0)) == (11, 7, 0)
    assert (sign["x"], sign["y"], sign["storey"]) == (11, 7, 1)
    assert portal["targetMap"] == "essai/etages" and portal["arrival"] == "palier"
    landing = next(e for e in by_id.values() if e["type"] == "spawnPoint")
    assert landing["storey"] == 1
    # Le plancher couvre le portail et le palier ; la rampe monte du rez à son bord.
    objects = {item["id"]: item for item in doc["objects"]}
    slab = objects["plancher"]
    c0, r0, c1, r1 = essai.SLAB_CELLS
    assert slab["position"][2] + essai.SLAB == pytest.approx(essai.STOREY)
    assert c0 <= portal["x"] <= c1 and r0 <= portal["y"] <= r1
    assert c0 <= landing["x"] <= c1 and r0 <= landing["y"] <= r1
    ramp = objects["rampe"]
    assert ramp["pitch"] == pytest.approx(26.565, abs=1e-3)
    # Les cases de la rampe sont un passage, au rez.
    stairs = {(t["x"], t["y"]) for t in doc["tiles"] if t["type"] == "stairs"}
    assert stairs == {(c, r) for c in range(4, 8) for r in (1, 2)}


def test_une_entite_ne_tient_pas_dans_un_mur():
    for identifier in essai.MAPS:
        doc = written(identifier)
        walls = {(tile["x"], tile["y"]) for tile in doc["tiles"] if tile["type"] == "wall"}
        for entity in doc["entities"]:
            if entity["type"] in ("combatZone", "portal"):
                continue  # une zone couvre l'enceinte ; un portail est percé dans le mur
            assert (entity["x"], entity["y"]) not in walls, f"{identifier} : {entity['id']}"
