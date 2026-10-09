# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests des cartes d'essai de l'exploration (LOT-1016) : la carte de Core et la description de
scène d'une même carte viennent du même plan et se répondent. Sans moteur."""

import json

import pytest

import build_essai_maps as essai


def written(identifier: str) -> tuple[dict, dict]:
    spec = essai.MAPS[identifier]
    return json.loads(essai.level_text(identifier, spec)), json.loads(essai.scene_text(identifier, spec))


def test_les_fichiers_du_depot_sont_a_jour():
    for path, text in essai.files().items():
        assert path.read_text(encoding="utf-8") == text, f"{path.name} : relancer build_essai_maps.py"


@pytest.mark.parametrize("identifier", sorted(essai.MAPS))
def test_un_mur_de_la_carte_est_un_mur_de_la_scene(identifier):
    level, scene = written(identifier)
    walls = {(tile["x"], tile["y"]) for tile in level["tiles"] if tile["type"] == "wall"}
    blocks = {(round(item["position"][0] / essai.CELL - 0.5), round(item["position"][2] / essai.CELL - 0.5))
              for item in scene["objects"] if item["folder"] == "murs"}
    assert walls == blocks
    # Le reste du décor montre une entité de la carte, sur sa case : un coffre, un panneau.
    shown = {item["entity"]: item for item in scene["objects"] if item["folder"] != "murs"}
    places = {entity["id"]: entity for entity in level["entities"]}
    assert sorted(places[key]["type"] for key in shown) == (["chest", "sign"] if identifier == "essai/etals" else [])
    for key, item in shown.items():
        assert item["position"] == essai.centre(places[key]["x"], places[key]["y"])
    assert len(scene["objects"]) == len(walls) + len(shown)
    # Le sol et la navigation couvrent la grille entière, coin de la case (0, 0) à l'origine.
    extent = [0.0, 0.0, level["width"] * essai.CELL, level["height"] * essai.CELL]
    assert scene["fills"][0]["areas"] == [extent]
    assert scene["navigation"]["area"] == extent
    assert scene["level"]["origin"] == [0.0, 0.0] and scene["level"]["cell"] == essai.CELL


@pytest.mark.parametrize("identifier", sorted(essai.MAPS))
def test_la_scene_joue_sa_carte_de_core(identifier):
    level, scene = written(identifier)
    assert scene["level"]["id"] == identifier
    # Le chemin qu'un portail ouvre (`AJadgMapFrame::MapPackage`).
    assert scene["map"] == f"/Game/Maps/Levels/{identifier}"
    assert (essai.ROOT / scene["level"]["root"] / f"{identifier}.json").is_file()
    assert sorted(character["party"] for character in scene["characters"] if "party" in character) == [0, 1, 2, 3]
    # Chaque PNJ de la carte a son personnage dans la scène, et lui seul.
    npcs = {entity["id"] for entity in level["entities"] if entity["type"] == "npc"}
    shown = [character["entity"] for character in scene["characters"] if "entity" in character]
    assert sorted(shown) == sorted(npcs)
    assert level["nextEntityId"] == len(level["entities"]) + 1


def test_les_portails_menent_a_un_point_d_arrivee_qui_existe():
    levels = {identifier: written(identifier)[0] for identifier in essai.MAPS}
    crossed = 0
    for level in levels.values():
        for entity in level["entities"]:
            if entity["type"] != "portal" or entity["sealed"]:
                continue
            target = levels[entity["targetMap"]]
            arrivals = {other["name"] for other in target["entities"] if other["type"] == "spawnPoint"}
            assert entity["arrival"] in arrivals
            crossed += 1
    assert crossed == 3


def test_une_entite_ne_tient_pas_dans_un_mur():
    for identifier in essai.MAPS:
        level, _ = written(identifier)
        walls = {(tile["x"], tile["y"]) for tile in level["tiles"] if tile["type"] == "wall"}
        for entity in level["entities"]:
            if entity["type"] == "combatZone":
                # Une zone de combat est un rectangle : sa case est son coin, l'enceinte comprise.
                continue
            assert (entity["x"], entity["y"]) not in walls, f"{identifier} : {entity['id']} est dans un mur"
        entries = [tile for tile in level["tiles"] if tile["type"] == "entry"]
        assert len(entries) == 1 and (entries[0]["x"], entries[0]["y"]) not in walls


def test_une_figurine_se_nomme_par_son_dossier_et_ne_s_ecrit_que_pour_un_pnj():
    for identifier in essai.MAPS:
        level, _ = written(identifier)
        for entity in level["entities"]:
            assert ("figure" in entity) == (entity["type"] == "npc")
            assert not {"heading", "block", "entry"} & set(entity), "ce que la scène seule lit n'entre pas dans la carte"
            if entity["type"] == "npc":
                assert entity["figure"].startswith("Regions/") and entity["figure"].count("/") >= 3


def test_l_arene_porte_ce_que_le_combat_lit():
    level, scene = written("essai/arene")
    assert scene["map"] == "/Game/Maps/Levels/essai/arene"
    zones = [entity for entity in level["entities"] if entity["type"] == "combatZone"]
    assert [(zone["x"], zone["y"], zone["width"], zone["height"]) for zone in zones] == [(0, 0, level["width"], level["height"])]
    entries = sorted((entity["rank"], entity["side"]) for entity in level["entities"] if entity["type"] == "arenaEntry")
    assert entries == [(0, "allies"), (1, "allies"), (2, "allies"), (3, "allies")]
    markers = [entity for entity in level["entities"] if entity["type"] == "encounter"]
    assert [marker["encounterId"] for marker in markers] == ["arene-bandits"]
    # Aucun adversaire dans la scène : le combat les pose depuis la rencontre.
    assert all("entity" not in character for character in scene["characters"])


def test_un_plan_irregulier_est_refuse():
    with pytest.raises(ValueError):
        essai.rows_of("###\n##\n###")
    with pytest.raises(ValueError):
        essai.entities_of({"plan": "#?#", "marks": {}, "zones": []})
