# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests de la carte de contrôle d'une pièce de décor (LOT-1019, `build_piece_check.py`) : la pièce
seule, quatre cadrages autour d'elle, une carte v5 que `jadg_map.validate` accepte. Le `.glb` est
écrit par le test ; les maîtres, hors Git, ne sont lus que s'ils sont installés."""

import json
import struct

import pytest

import build_piece_check as check
import jadg_map


def fake_glb(low, high) -> bytes:
    document = {"asset": {"version": "2.0"}, "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
                "accessors": [{"count": 3, "type": "VEC3", "componentType": 5126, "min": low, "max": high}]}
    text = json.dumps(document).encode()
    text += b" " * ((4 - len(text) % 4) % 4)
    return struct.pack("<III", 0x46546C67, 2, 20 + len(text)) + struct.pack("<II", len(text), 0x4E4F534A) + text


@pytest.fixture
def assets(tmp_path):
    root = tmp_path / "Assets"
    (root / "Master" / "Scenery").mkdir(parents=True)
    # Une façade de 1,7 × 1,9 × 1,3 unités, posée à 12 m de haut.
    (root / "Master" / "Scenery" / "facade.glb").write_bytes(fake_glb([-0.85, -0.95, -0.65], [0.85, 0.95, 0.65]))
    (root / "Master" / "manifest.json").write_text(json.dumps({"pieces": [
        {"id": "Scenery/facade", "file": "Master/Scenery/facade.glb", "meshy_id": "1", "sheet": {"family": "02", "height": 12.0}},
        {"id": "Weapons/epee", "file": "Master/Weapons/epee.glb", "meshy_id": "2", "sheet": {}},
    ]}), encoding="utf-8")
    return root


def test_seules_les_pieces_dont_la_fiche_donne_une_famille_se_controlent(assets):
    assert [p["id"] for p in check.pieces(assets)] == ["Scenery/facade"]


def test_la_carte_montre_les_quatre_cotes_a_midi_et_a_22_h(assets):
    (piece,) = check.pieces(assets)
    doc = check.control_map(piece, assets)
    assert jadg_map.validate(doc) == []
    assert [shot["id"] for shot in doc["shots"]] == ["face", "droite", "dos", "gauche"]
    assert sorted(shot["heading"] for shot in doc["shots"]) == [0.0, 90.0, 180.0, 270.0]
    assert doc["hours"] == ["12:00", "22:00"]
    (item,) = doc["objects"]
    assert item["height"] == 12.0 and item["mesh"] == "Master/Scenery/facade.glb"
    # Mise à 12 m, la façade fait 10,7 m de large : la caméra s'en tient à 2,4 fois.
    assert doc["shots"][0]["distance"] == pytest.approx(25.8, abs=0.1)
    assert doc["shots"][0]["target"][2] == pytest.approx(5.4)


def test_une_piece_dont_le_glb_manque_n_a_pas_de_carte(assets):
    (assets / "Master" / "Scenery" / "facade.glb").unlink()
    assert check.files(assets) == {}


@pytest.mark.skipif(not (check.ASSETS / "Master" / "Scenery" / "arenarea-palazzo-terracotta.glb").is_file(),
                    reason="maîtres Meshy non installés (hors Git)")
def test_la_carte_de_controle_de_la_facade_temoin_est_a_jour():
    assert check.main(["--check"]) == 0
