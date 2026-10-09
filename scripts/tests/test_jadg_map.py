# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests du format de carte v5 (LOT-1018) : l'écriture canonique, le contrôle de contenu, la
migration depuis la v4, les pièces des kits et les préfabriqués. Sans moteur."""

import copy
import json

import pytest

import jadg_map


def carte(**extra) -> dict:
    """Une carte v5 minimale de 6 × 4 cases, murs autour, l'entrée en (1, 1)."""
    tiles = [{"x": x, "y": y, "type": "wall"} for y in range(4) for x in range(6) if x in (0, 5) or y in (0, 3)]
    tiles.append({"x": 1, "y": 1, "type": "entry"})
    doc = {"format": "jadg-map", "version": 5, "name": "essai", "width": 6, "height": 4, "origin": [0.0, 0.0],
           "nextEntityId": 1, "tiles": tiles, "entities": []}
    doc.update(extra)
    return doc


def entites(*entities) -> dict:
    listed = [{"id": f"e{n}", **e} for n, e in enumerate(entities, start=1)]
    return carte(entities=listed, nextEntityId=len(listed) + 1)


def test_chaque_carte_du_depot_est_sous_sa_forme_canonique():
    maps = jadg_map.all_maps()
    assert len(maps) >= 10
    for map_id, path in maps.items():
        assert jadg_map.dumps(jadg_map.read(path)) == path.read_text(encoding="utf-8"), map_id


def test_le_controle_du_depot_passe():
    maps = {map_id: jadg_map.read(path) for map_id, path in jadg_map.all_maps().items()}
    errors, _ = jadg_map.check_world(maps)
    assert errors == []


def test_la_fixture_de_core_est_une_v5_valide():
    doc = jadg_map.read(jadg_map.ROOT / "Source" / "Test" / "Fixtures" / "Levels" / "format-v5.json")
    assert jadg_map.validate(doc) == []


def test_l_ecriture_canonique_ne_bouge_pas_une_carte_relue(tmp_path):
    doc = carte(objects=[{"id": "banc", "mesh": "Scene/ilot/wall.glb", "position": [1.5, 2.25, 0.0], "yaw": 30.0}],
                lighting={"lampCandelas": 60.0, "fog": {"density": 0.004}})
    path = tmp_path / "carte.json"
    assert jadg_map.write(path, doc)
    text = path.read_text(encoding="utf-8")
    assert not jadg_map.write(path, jadg_map.read(path))
    assert path.read_text(encoding="utf-8") == text
    # Une case, un objet, une entité par ligne : le fichier se relit et se compare.
    assert '    {"x": 1, "y": 1, "type": "entry"}' in text
    assert '    {"id": "banc", "mesh": "Scene/ilot/wall.glb", "position": [1.5, 2.25, 0.0], "yaw": 30.0}' in text


@pytest.mark.parametrize("faute, mot", [
    ({"entities": [{"id": "e1", "type": "npc", "x": 2, "y": 2, "storey": 1}]}, "étage"),
    ({"entities": [{"id": "e1", "type": "zone", "x": 2, "y": 2, "name": "z",
                    "volume": {"min": [3, 3, 0], "max": [2, 4, 1]}}]}, "volume"),
    ({"entities": [{"id": "e1", "type": "npc", "x": 2, "y": 2}, {"id": "e1", "type": "npc", "x": 3, "y": 2}]}, "deux"),
    ({"entities": [{"id": "e3", "type": "npc", "x": 2, "y": 2}], "nextEntityId": 2}, "nextEntityId"),
    ({"storeys": [{"name": "a", "z": 0.0}, {"name": "b", "z": -1.0}]}, "étages"),
    ({"entities": [{"id": "e1", "type": "npc", "x": 2, "y": 2, "elevation": 1}]}, "schéma"),
])
def test_une_carte_fautive_est_refusee(faute, mot):
    doc = carte(**faute)
    errors = jadg_map.validate(doc)
    assert any(mot in error for error in errors), errors


def test_les_portails_et_les_arrivees_se_controlent():
    a = entites({"type": "portal", "x": 4, "y": 1, "targetMap": "b", "arrival": "porte"},
                {"type": "portal", "x": 4, "y": 2, "targetMap": "nulle-part", "arrival": "x"},
                {"type": "spawnPoint", "x": 2, "y": 2, "name": "seul"})
    b = entites({"type": "spawnPoint", "x": 2, "y": 1, "name": "ailleurs"})
    errors, warnings = jadg_map.check_world({"a": a, "b": b})
    assert any("« nulle-part », qui n'existe pas" in e for e in errors)
    assert any("« porte », que « b » n'a pas" in e for e in errors)
    assert any("« b » n'a aucun passage qui revient" in w for w in warnings)
    assert any("« seul » n'est cité" in w for w in warnings)


def test_un_portail_condamne_ne_vise_rien():
    a = entites({"type": "portal", "x": 4, "y": 1, "sealed": True, "targetMap": "", "arrival": ""})
    errors, _ = jadg_map.check_world({"a": a})
    assert errors == []


def test_les_zones_se_nomment():
    doc = entites({"type": "zone", "x": 1, "y": 1}, {"type": "combatZone", "x": 1, "y": 1, "name": "sable"},
                  {"type": "combatZone", "x": 2, "y": 1, "name": "sable"})
    errors, _ = jadg_map.check_world({"a": doc})
    assert any("zone sans nom" in e for e in errors)
    assert any("2 zones nommées « sable »" in e for e in errors)


def test_une_entite_inatteignable_est_une_erreur():
    # Un mur coupe la salle en deux : le coffre de l'autre côté ne s'atteint pas.
    doc = entites({"type": "chest", "x": 4, "y": 2})
    doc["width"] = 8
    doc["tiles"] = [t for t in doc["tiles"] if t["x"] != 5] + [{"x": 3, "y": y, "type": "wall"} for y in (1, 2)]
    doc["tiles"] += [{"x": x, "y": y, "type": "wall"} for y in range(4) for x in (5, 6, 7) if y in (0, 3)]
    doc["tiles"] += [{"x": 7, "y": y, "type": "wall"} for y in (1, 2)]
    errors, warnings = jadg_map.check_world({"a": doc})
    assert any("e1 (chest)" in e and "inatteignable" in e for e in errors)
    assert any("inatteignable(s) au rez" in w for w in warnings)


def test_une_entite_de_l_etage_n_a_pas_a_s_atteindre_au_rez():
    doc = entites({"type": "sign", "x": 4, "y": 2, "storey": 1})
    doc["storeys"] = [{"name": "rez", "z": 0.0}, {"name": "etage", "z": 3.0}]
    doc["tiles"] += [{"x": 3, "y": y, "type": "wall"} for y in (1, 2)]
    errors, _ = jadg_map.check_world({"a": doc})
    assert errors == []


V4 = {
    "version": 4, "name": "map.essai.name", "width": 3, "height": 2, "nextEntityId": 3, "hour": 21.5,
    "tiles": [{"x": 0, "y": 0, "type": "entry"}],
    "layers": [
        {"name": "sol", "kind": "ground", "scene": "central-empire/capital/arenarea",
         "tiles": [{"x": 0, "y": 0, "type": "pavement", "piece": "ar-paving-1"}]},
        {"name": "toits-2", "kind": "decor", "floor": 2, "tiles": [{"x": 1, "y": 0, "type": "roof", "piece": "ar-roof"}]},
    ],
    "entities": [
        {"id": "e1", "type": "npc", "x": 1, "y": 1, "dialogue": "mere"},
        {"id": "e2", "type": "spawnPoint", "x": 2, "y": 1, "name": "from-martpart"},
    ],
}


def test_la_migration_garde_ce_que_core_joue():
    doc = jadg_map.migrate(copy.deepcopy(V4), [{"column": 2, "row": 1, "text": "une note"}], "essai")
    assert jadg_map.validate(doc) == []
    assert doc["tiles"] == V4["tiles"]
    assert [e["id"] for e in doc["entities"]] == ["e1", "e2"]
    assert doc["entities"][1]["name"] == "from-martpart"
    # L'étage de décor de la v4 devient une hauteur en mètres ; la réserve tombe.
    toits = doc["layers"][1]
    assert "floor" not in toits and toits["z"] == 2 * jadg_map.STOREY_HEIGHT
    assert doc["place"] == "central-empire/capital/arenarea"
    # Le PNJ reçoit son personnage ; l'heure fixe de la carte reste une propriété.
    assert doc["entities"][0]["appearance"] == jadg_map.PUPPET
    assert doc["hour"] == 21.5
    assert doc["notes"] == [{"x": 2, "y": 1, "text": "une note"}]
    assert doc["party"]["appearances"] == list(jadg_map.HEROES)


def test_la_migration_refuse_ce_qu_elle_ne_sait_pas_porter():
    with pytest.raises(jadg_map.MapError, match="variante"):
        jadg_map.migrate({"version": 4, "name": "x", "base": "y", "entities": []})
    reserved = copy.deepcopy(V4)
    reserved["entities"][0]["elevation"] = 1
    with pytest.raises(jadg_map.MapError, match="hauteur"):
        jadg_map.migrate(reserved)
    with pytest.raises(jadg_map.MapError, match="version"):
        jadg_map.migrate({**V4, "version": 3})


def test_migrer_un_fichier_retire_ses_notes_d_editeur(tmp_path):
    path = tmp_path / "carte.json"
    path.write_text(json.dumps(V4), encoding="utf-8")
    (tmp_path / "carte.editor.json").write_text(json.dumps({"version": 1, "notes": [{"column": 0, "row": 0, "text": "a"}]}),
                                                encoding="utf-8")
    jadg_map.migrate_file(path)
    assert not (tmp_path / "carte.editor.json").exists()
    assert jadg_map.read(path)["notes"] == [{"x": 0, "y": 0, "text": "a"}]


def test_une_piece_se_cherche_du_lieu_vers_le_monde(tmp_path):
    regions = tmp_path / "Regions"
    for relative in ("central-empire/capital/arenarea/Scene/ar-paving-1.glb",
                     "central-empire/capital/Common/Scene/buildings/cap-hall.glb",
                     "central-empire/capital/martpart/Scene/mp-only.glb"):
        (regions / relative).parent.mkdir(parents=True, exist_ok=True)
        (regions / relative).write_bytes(b"glTF")
    manifest = {"textures": {"scene/capital/cap-hall": {"footprint": [3, 2]}}}
    (regions / "central-empire/capital/Common/Scene/manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    place = "central-empire/capital/arenarea"
    assert jadg_map.resolve_piece(place, "ar-paving-1", tmp_path) == (
        "Regions/central-empire/capital/arenarea/Scene/ar-paving-1.glb", (1, 1))
    assert jadg_map.resolve_piece(place, "cap-hall", tmp_path) == (
        "Regions/central-empire/capital/Common/Scene/buildings/cap-hall.glb", (3, 2))
    # Hors de la lignée du lieu : le seul maillage de ce nom sous Regions/.
    assert jadg_map.resolve_piece(place, "mp-only", tmp_path)[0].endswith("martpart/Scene/mp-only.glb")
    assert jadg_map.resolve_piece(place, "absente", tmp_path) is None


def test_un_tampon_de_l_ancien_editeur_devient_un_prefabrique():
    old = {"format": "jadg-editor-prefab", "version": 1, "place": "central-empire/capital", "width": 2, "height": 1,
           "layers": [{"name": "sol", "kind": "ground", "pieces": [{"at": [1, 0], "piece": "dalle", "type": "empty"}]},
                      {"name": "toit", "kind": "decor", "floor": 1, "pieces": [{"at": [0, 0], "piece": "tuile", "type": "roof"}]}]}
    prefab = jadg_map.migrate_prefab(old, "essai")
    assert prefab["format"] == "jadg-prefab" and prefab["place"] == "central-empire/capital"
    assert prefab["objects"] == [
        {"id": "sol/1,0", "piece": "dalle", "position": [2.25, 0.75, 0.0]},
        {"id": "toit/0,0", "piece": "tuile", "position": [0.75, 0.75, jadg_map.STOREY_HEIGHT]},
    ]


def test_les_prefabriques_du_depot_se_lisent():
    prefabs = sorted(jadg_map.PREFABS.rglob("*.json"))
    assert prefabs
    for path in prefabs:
        prefab = jadg_map.read_prefab(path.relative_to(jadg_map.PREFABS).with_suffix("").as_posix())
        assert prefab["objects"], path.name
        assert all(("mesh" in o) != ("piece" in o) for o in prefab["objects"])


def test_l_identifiant_et_le_niveau_d_une_carte():
    path = jadg_map.find("essai/etages")
    assert path is not None and jadg_map.map_id_of(path) == "essai/etages"
    assert jadg_map.levels_root(path) == "Source/Test/Fixtures/Exploration/Levels"
    assert jadg_map.levels_root(jadg_map.find("central-empire/capital/martpart")) == ""
    assert jadg_map.package("essai/etages") == "/Game/Maps/Levels/essai/etages"
    assert jadg_map.cell_of(*jadg_map.cell_centre(3, 4, [-6.0, 1.5])[:2], [-6.0, 1.5]) == (3, 4)
