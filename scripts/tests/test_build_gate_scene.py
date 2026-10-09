# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests de l'anneau du Colisée (LOT-1012) : `build_colosseum.ring_bays`, la pose des pièces par
`build_gate_scene` en préfabriqué, et la carte de la porte au format v5 (LOT-1018) dont la grille
de Core vient de la même géométrie. Sans Blender ni kit : la géométrie des pièces n'est pas
construite."""

import json
import math

import pytest

import build_colosseum as colosseum
import build_gate_scene as gate
import jadg_map


def test_le_perimetre_est_celui_du_colisee_de_rome():
    # 189 × 156 m : 527 m de tour, 80 arcades de 6,6 m.
    assert colosseum.perimeter(94.5, 78.0) == pytest.approx(543.2, abs=0.5)
    assert colosseum.bay_width() == pytest.approx(6.79, abs=0.01)


def test_les_travees_se_suivent_bout_a_bout_a_longueur_egale():
    bays = colosseum.ring_bays()
    assert len(bays) == 80
    chords = [bay["chord"] for bay in bays]
    # Des cordes presque égales : la courbure seule les distingue, au centimètre.
    assert max(chords) - min(chords) < 0.02
    assert sum(chords) == pytest.approx(colosseum.perimeter(94.5, 78.0), rel=1e-3)
    # Chaque centre est sur l'ellipse, à la flèche de la corde près.
    for bay in bays:
        x, y = bay["centre"]
        assert (x / 94.5) ** 2 + (y / 78.0) ** 2 == pytest.approx(1.0, abs=0.003)


def test_la_travee_zero_est_plein_sud_et_regarde_le_sud():
    bays = colosseum.ring_bays()
    assert bays[0]["centre"][0] == pytest.approx(0.0, abs=1e-3)
    # Le centre de la corde, à sa flèche près (5 cm sur une corde de 6,8 m).
    assert bays[0]["centre"][1] == pytest.approx(-78.0, abs=0.1)
    assert bays[0]["normal"] == pytest.approx([0.0, -1.0], abs=1e-4)
    assert bays[0]["yaw"] == pytest.approx(0.0, abs=1e-2) or bays[0]["yaw"] == pytest.approx(360.0, abs=1e-2)
    # L'est (travée 20) regarde +X : lacet de 90°, comme `turn` de la scène l'entend.
    assert bays[20]["normal"] == pytest.approx([1.0, 0.0], abs=1e-3)
    assert bays[20]["yaw"] == pytest.approx(90.0, abs=0.1)
    assert bays[40]["normal"] == pytest.approx([0.0, 1.0], abs=1e-3)


def test_le_lacet_amene_la_facade_sur_la_normale():
    for bay in colosseum.ring_bays()[::7]:
        angle = math.radians(bay["yaw"])
        # La façade d'une pièce regarde −Y ; tournée du lacet, elle regarde la normale sortante.
        turned = [math.sin(angle), -math.cos(angle)]
        assert turned == pytest.approx(bay["normal"], abs=1e-4)


def test_le_repere_de_la_carte_retourne_le_nord():
    # Blender : x est, y nord, z haut ; la carte : x est, y sud, z haut.
    assert gate.scene_point(1.0, 2.0, 3.0) == [1.0, -2.0, 3.0]


def fake_assets(tmp_path):
    """Les maîtres que la pose lit, réduits à leur boîte : les dieux, le lion, la façade."""
    assets = tmp_path / "Assets"
    pieces = []
    for family, names in (("Statues", gate.GODS + ["portal-guardian-lion"]),):
        for name in names:
            path = assets / "Master" / family / f"{name}.glb"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fake_glb([-0.5, -0.95, -0.4], [0.5, 0.95, 0.4]))
            pieces.append({"id": f"{family}/{name}", "file": f"Master/{family}/{name}.glb", "meshy_name": name,
                           "meshy_id": "1"})
    palazzo = assets / gate.PALAZZO
    palazzo.parent.mkdir(parents=True, exist_ok=True)
    # Une façade de 10 m de large, 4 m de profondeur, 6 m de haut : mise à 12 m, elle double.
    palazzo.write_bytes(fake_glb([-5.0, 0.0, -2.0], [5.0, 6.0, 2.0]))
    (assets / "Master" / "manifest.json").write_text(json.dumps({"pieces": pieces}), encoding="utf-8")
    return assets


def test_la_scene_pose_l_anneau_les_dieux_et_les_lions(tmp_path):
    scene = gate.build(fake_assets(tmp_path))
    assert scene["format"] == "jadg-prefab" and scene["version"] == 1

    by_folder = {}
    for item in scene["objects"]:
        by_folder.setdefault(item["id"].split("/")[0], []).append(item)
    assert len(by_folder["ordre-1"]) == len(by_folder["ordre-2"]) == len(by_folder["ordre-3"]) == 77
    assert len(by_folder["attique"]) == 80
    assert len(by_folder["gradins"]) == 4 and sum("mirrored" in g for g in by_folder["gradins"]) == 2
    assert len(by_folder["dieux"]) == 28  # quatorze dieux et leurs socles
    assert len(by_folder["gardiens"]) == 2
    assert len(by_folder["bannieres"]) == len(gate.BANNERS)
    # La porte est plein sud, au sol, sur l'ellipse ; les dieux à 5,2 m dans les arcs du deuxième ordre.
    porte = by_folder["porte"][0]
    assert porte["position"] == [0.0, 78.0, 0.0]
    god = next(g for g in by_folder["dieux"] if g["id"] == "dieux/statue-bauron")
    assert god["scale"] == pytest.approx(5.2 / 1.9, rel=1e-3)
    assert god["position"][2] == pytest.approx(11.0 + 0.94 + 0.95 * 5.2 / 1.9, abs=1e-3)
    assert god["position"][1] > 70.0  # au sud, près de la porte
    # Le sable est au centre ; aucun objet ne manque de maillage.
    assert by_folder["sol"][0]["position"] == [0.0, 0.0, 0.0]
    assert all(item["mesh"] for item in scene["objects"])


def test_la_carte_de_la_porte_joue_la_grille_de_ce_qu_elle_construit(tmp_path):
    doc = gate.gate_map(fake_assets(tmp_path))
    assert jadg_map.validate(doc) == []
    walls = {(t["x"], t["y"]) for t in doc["tiles"] if t["type"] == "wall"}
    entry = jadg_map.entry_of(doc)
    assert entry is not None and entry not in walls

    def wall_at(x, y):
        return jadg_map.cell_of(x, y, doc["origin"]) in walls

    # Le pied du Colisée est un mur, le parvis devant la porte est libre.
    assert wall_at(0.0, -9.0) and not wall_at(0.0, 21.0)
    # L'emprise d'une façade (10 × 4 m doublés autour de x = -18,6, y = 52) arrête le pas ; pas la rue devant.
    assert wall_at(-18.6, 52.0) and wall_at(-27.0, 50.0) and not wall_at(-18.6, 45.0)
    # Hors du dallage, la ruelle est fermée ; dedans, elle est libre.
    assert wall_at(-20.0, 70.0) and not wall_at(0.0, 70.0)
    # Le Colisée est posé en préfabriqué, au centre de son ellipse.
    assert doc["prefabs"][0]["prefab"] == gate.PREFAB_ID
    assert doc["prefabs"][0]["position"] == gate.COLISEE_CENTRE
    # Tout le parvis libre se rejoint depuis l'entrée.
    _, warnings = jadg_map.check_world({"porte-1012": doc})
    assert not [w for w in warnings if "inatteignable" in w]


@pytest.mark.skipif(not (gate.ASSETS / gate.PALAZZO).exists(),
                    reason="les maîtres Meshy ne sont pas suivis par Git : ce contrôle se rejoue sur un poste qui les a")
def test_les_fichiers_du_depot_sont_a_jour():
    assert gate.main(["--check"]) == 0


def fake_glb(low, high) -> bytes:
    """Un .glb réduit à ses accesseurs : ce que `glb_bounds` lit."""
    document = {"asset": {"version": "2.0"}, "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
                "accessors": [{"min": low, "max": high}]}
    text = json.dumps(document).encode("utf-8")
    text += b" " * ((4 - len(text) % 4) % 4)
    import struct
    return struct.pack("<4sII", b"glTF", 2, 20 + len(text)) + struct.pack("<II", len(text), 0x4E4F534A) + text
