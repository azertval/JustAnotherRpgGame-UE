# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Tests de la fiche d'une pièce de décor et de la matière lue dans un `.glb` (LOT-1019) :
`scenery_sheets.py`, que partagent la chaîne de décor du moteur (`import_scenery_unreal.py`) et le
manifeste des maîtres (`build_master_manifest.py --refresh`). Les `.glb` sont écrits par le test ;
ceux du kit et des maîtres, hors Git, ne sont lus que s'ils sont installés."""

import hashlib
import json
import struct
import zlib
from pathlib import Path

import pytest

import build_master_manifest
import scenery_sheets as sheets

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "Source" / "Elements" / "Assets"
MASTER = ASSETS / "Master" / "manifest.json"


def png(width: int, height: int, pixel=(200, 180, 150, 255)) -> bytes:
    raw = b"".join(b"\x00" + bytes(pixel) * width for _ in range(height))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def glb(materials: list[dict], images: list[bytes]) -> bytes:
    """Un .glb d'un triangle, ses matières et ses images incorporées."""
    binary = bytearray(struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 1, 0)) + struct.pack("<3H", 0, 1, 2) + b"\x00\x00"
    views = [{"buffer": 0, "byteOffset": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": 6}]
    for image in images:
        binary += b"\x00" * ((4 - len(binary) % 4) % 4)
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(image)})
        binary += image
    binary += b"\x00" * ((4 - len(binary) % 4) % 4)
    document = {
        "asset": {"version": "2.0"},
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1, "material": 0}]}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3", "min": [0, 0, 0], "max": [1, 1, 0]},
                      {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}],
        "bufferViews": views,
        "buffers": [{"byteLength": len(binary)}],
        "images": [{"bufferView": 2 + i, "mimeType": "image/png"} for i in range(len(images))],
        "textures": [{"source": i} for i in range(len(images))],
        "materials": materials,
    }
    text = json.dumps(document).encode()
    text += b" " * ((4 - len(text) % 4) % 4)
    return (struct.pack("<III", 0x46546C67, 2, 28 + len(text) + len(binary)) + struct.pack("<II", len(text), 0x4E4F534A)
            + text + struct.pack("<II", len(binary), 0x004E4942) + bytes(binary))


COMPLETE = {"name": "pierre", "doubleSided": True,
            "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicRoughnessTexture": {"index": 2},
                                     "roughnessFactor": 0.8},
            "normalTexture": {"index": 1}, "occlusionTexture": {"index": 2}}


def write(tmp_path: Path, name: str, materials: list[dict], images: list[bytes]) -> Path:
    path = tmp_path / name
    path.write_bytes(glb(materials, images))
    return path


def test_une_matiere_complete_donne_ses_trois_cartes_et_son_occlusion(tmp_path):
    path = write(tmp_path, "a.glb", [COMPLETE], [png(8, 4), png(8, 4, (128, 128, 255, 255)), png(8, 4, (255, 200, 0, 255))])
    document, binary = sheets.read_glb(path)
    (slot,) = sheets.material_slots(document, binary)
    assert sorted(slot["images"]) == ["baseColor", "normal", "orm"]
    assert slot["images"]["baseColor"]["size"] == [8, 4]
    assert slot["roughnessFactor"] == pytest.approx(0.8)
    # L'occlusion est dans le rouge de l'image d'occlusion-rugosité-métal : la même image.
    assert slot["occlusionStrength"] == 1.0
    assert slot["alpha"] == "opaque"
    report = sheets.material_report(path)
    assert report["complete"] and report["missing"] == []


def test_une_occlusion_qui_n_est_pas_la_meme_image_n_est_pas_lue_dans_le_rouge(tmp_path):
    material = {**COMPLETE, "occlusionTexture": {"index": 0}}
    path = write(tmp_path, "b.glb", [material], [png(4, 4), png(4, 4), png(4, 4)])
    (slot,) = sheets.material_slots(*sheets.read_glb(path))
    assert slot["occlusionStrength"] == 0.0


def test_une_carte_absente_est_dite_absente(tmp_path):
    material = {"name": "couleur", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}, "metallicFactor": 0.0}}
    path = write(tmp_path, "c.glb", [material], [png(4, 4)])
    report = sheets.material_report(path)
    assert not report["complete"]
    assert report["missing"] == ["normal", "orm"]
    (slot,) = sheets.material_slots(*sheets.read_glb(path))
    # Le métal de glTF vaut 1 par défaut : ici 0, écrit dans le fichier, est gardé.
    assert slot["metallicFactor"] == 0.0


def test_un_alpha_melange_devient_un_masque(tmp_path):
    material = {"name": "foule", "alphaMode": "BLEND", "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}}}
    (slot,) = sheets.material_slots(*sheets.read_glb(write(tmp_path, "d.glb", [material], [png(4, 4)])))
    assert slot["alpha"] == "masked"


def test_deux_pieces_qui_portent_la_meme_image_ont_la_meme_empreinte(tmp_path):
    image = png(16, 16)
    first = sheets.material_slots(*sheets.read_glb(write(tmp_path, "e.glb", [COMPLETE], [image, png(2, 2), png(2, 2)])))
    second = sheets.material_slots(*sheets.read_glb(write(tmp_path, "f.glb", [COMPLETE], [image, png(4, 4), png(4, 4)])))
    assert first[0]["images"]["baseColor"]["sha256"] == second[0]["images"]["baseColor"]["sha256"]
    assert first[0]["images"]["baseColor"]["sha256"] == hashlib.sha256(image).hexdigest()


def test_un_glb_sans_matiere_ne_s_installe_pas(tmp_path):
    with pytest.raises(sheets.SceneryError):
        sheets.material_slots(*sheets.read_glb(write(tmp_path, "g.glb", [], [])))
    (tmp_path / "h.glb").write_bytes(b"pas un glb")
    with pytest.raises(sheets.SceneryError):
        sheets.read_glb(tmp_path / "h.glb")


def test_la_taille_d_un_jpeg_se_lit_dans_son_en_tete():
    jpeg = b"\xff\xd8" + b"\xff\xe0" + struct.pack(">H", 4) + b"\x00\x00" + b"\xff\xc0" + struct.pack(">HBHH", 11, 8, 1536, 2048) + b"\x00" * 8
    assert sheets.image_size(jpeg) == (2048, 1536)


def test_une_fiche_complete_passe():
    piece = {"id": "facade", "mesh": "a.glb", "family": "02", "class": "tall", "footprint": [3, 1], "tactical": "solid",
             "light": {"color": "#ffd69a", "range": 7.5, "height": 2.9}}
    assert sheets.validate(piece) == []


@pytest.mark.parametrize("change, message", [
    ({"family": "11"}, "famille"),
    ({"class": "haute"}, "classe"),
    ({"footprint": [1.5, 1]}, "emprise"),
    ({"tactical": "mur"}, "tactique"),
    ({"light": {"color": "jaune", "range": 3, "height": 1}}, "couleur"),
    ({"light": {"color": "#ffffff", "height": 1}}, "portée"),
    ({"library": {"provider": "Sketchfab", "identifier": "x", "licence": "CC"}}, "D-55"),
    ({"library": {"provider": "Fab", "identifier": "x"}}, "licence"),
])
def test_une_fiche_fautive_dit_ce_qui_manque(change, message):
    piece = {"id": "p", "mesh": "a.glb", "family": "02", **change}
    errors = sheets.validate(piece)
    assert errors and message in " ".join(errors)


def test_la_fiche_d_un_maitre_est_son_objet_sheet():
    master = {"id": "Scenery/x", "family": "Scenery", "file": "Master/Scenery/x.glb", "meshy_id": "1",
              "sheet": {"family": "02", "class": "tall"}}
    assert sheets.sheet_of(master) == {"id": "Scenery/x", "file": "Master/Scenery/x.glb", "family": "02", "class": "tall"}
    # Le dossier du kit (`Scenery`) n'est pas une famille du standard : sans fiche, rien n'est validé.
    assert sheets.validate(sheets.sheet_of({**master, "sheet": {}})) == []
    kit = {"mesh": "af-pyre.glb", "class": "tall", "footprint": [1, 1]}
    assert sheets.sheet_of(kit) is kit


def test_une_piece_de_bibliotheque_cite_sa_source(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"pieces": [{"id": "rocher", "file": "Library/rocher.glb", "family": "07"}]}), encoding="utf-8")
    with pytest.raises(sheets.SceneryError, match="library"):
        sheets.library_manifest(path)
    piece = {"id": "rocher", "file": "Library/rocher.glb", "family": "07",
             "library": {"provider": "Megascans", "identifier": "abc123", "licence": "Fab Standard License"}}
    path.write_text(json.dumps({"pieces": [piece]}), encoding="utf-8")
    assert sheets.library_manifest(path) == [piece]
    assert sheets.library_manifest(tmp_path / "absent.json") == []


def test_le_manifeste_des_bibliotheques_du_depot_se_lit():
    assert isinstance(sheets.library_manifest(ASSETS / "Library" / "manifest.json"), list)


def test_le_rafraichissement_refait_les_fiches_des_maitres(tmp_path):
    dest = tmp_path / "Master"
    (dest / "Scenery").mkdir(parents=True)
    path = dest / "Scenery" / "facade.glb"
    path.write_bytes(glb([COMPLETE], [png(4, 4), png(4, 4), png(4, 4)]))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    (dest / "manifest.json").write_text(json.dumps({"version": 1, "pieces": [
        {"id": "Scenery/facade", "family": "Scenery", "file": "Master/Scenery/facade.glb", "meshy_id": "1", "sha256": digest}]}),
        encoding="utf-8")
    (dest / "references.json").write_text(json.dumps({"references": {"NPC/Facade": {
        "id": "Scenery/facade", "sheet": {"family": "02", "class": "tall"}}}}), encoding="utf-8")
    assert build_master_manifest.main(["--refresh", "--dest", str(dest)]) == 0
    (piece,) = json.loads((dest / "manifest.json").read_text(encoding="utf-8"))["pieces"]
    assert piece["sheet"]["family"] == "02"
    assert piece["sheet"]["material"]["complete"]
    # Un .glb retouché arrête le rafraîchissement.
    path.write_bytes(path.read_bytes() + b"    ")
    assert build_master_manifest.main(["--refresh", "--dest", str(dest)]) == 1


@pytest.mark.skipif(not MASTER.is_file() or not (ASSETS / "Master" / "Scenery").is_dir(),
                    reason="maîtres Meshy non installés (hors Git)")
def test_la_facade_temoin_porte_une_matiere_complete():
    manifest = json.loads(MASTER.read_text(encoding="utf-8"))
    facade = next(p for p in manifest["pieces"] if p["id"] == "Scenery/arenarea-palazzo-terracotta")
    assert facade["sheet"]["family"] == "02"
    assert facade["sheet"]["material"]["complete"]
    glb_path = ASSETS / facade["file"]
    if glb_path.is_file():
        assert sheets.material_report(glb_path) == facade["sheet"]["material"]
