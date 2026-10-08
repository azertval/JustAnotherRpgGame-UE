# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Les cartes de matière d'un modèle (D-46) : ce que l'outil écrit dans un `.glb`.

Le mur de la carte d'essai sert de modèle : une couleur de base en PNG, rien d'autre. Ce qui peut
dériver en silence : la géométrie, qui ne doit pas bouger ; les références de la matière ; le fait
qu'un second passage redonne les mêmes octets ; et le choix de la matière par case d'un atlas.
"""
import io
import json

import pytest

import build_mesh_fixture as F
import material_maps as M
from reduce_model import read_glb

pytest.importorskip('numpy')
Image = pytest.importorskip('PIL.Image')

TABLE = json.loads(M.MATTERS_DEFAUT.read_text(encoding='utf-8'))


@pytest.fixture
def wall(tmp_path):
    path = tmp_path / 'wall.glb'
    path.write_bytes(F.files()[f'Assets/Scene/{F.PLACE}/wall.glb'])
    return path


def test_un_modele_recoit_ses_deux_cartes_sans_que_sa_geometrie_bouge(wall):
    before, binary = read_glb(wall.read_bytes())
    position = before['meshes'][0]['primitives'][0]['attributes']['POSITION']
    view = before['bufferViews'][before['accessors'][position]['bufferView']]
    vertices = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]

    assert 'dérivées' in M.enrich(wall, TABLE, {}, 1024, {})

    after, rebuilt = read_glb(wall.read_bytes())
    material = after['materials'][0]
    assert material['normalTexture'] == {'index': 1}
    assert material['occlusionTexture'] == {'index': 2}
    assert material['pbrMetallicRoughness']['metallicRoughnessTexture'] == {'index': 2}
    assert [image['mimeType'] for image in after['images'][1:]] == ['image/jpeg', 'image/jpeg']
    moved = after['bufferViews'][after['accessors'][position]['bufferView']]
    assert rebuilt[moved['byteOffset']:moved['byteOffset'] + moved['byteLength']] == vertices
    images = M.material_images(after, rebuilt)
    assert images['occluded']
    color = Image.open(io.BytesIO(images['color']))
    assert Image.open(io.BytesIO(images['normal'])).size == color.size


def test_un_second_passage_redonne_les_memes_octets(wall):
    M.enrich(wall, TABLE, {}, 1024, {})
    once = wall.read_bytes()
    M.enrich(wall, TABLE, {}, 1024, {})
    assert wall.read_bytes() == once


def test_une_couleur_opaque_passe_en_jpeg_une_transparente_reste():
    opaque, clear = io.BytesIO(), io.BytesIO()
    Image.new('RGBA', (8, 8), (200, 180, 150, 255)).save(opaque, 'PNG')
    Image.new('RGBA', (8, 8), (200, 180, 150, 40)).save(clear, 'PNG')
    assert M.compact_color(opaque.getvalue(), {})[1] == 'image/jpeg'
    assert M.compact_color(clear.getvalue(), {}) == (clear.getvalue(), 'image/png')
    smaller, mime = M.compact_color(opaque.getvalue(), {}, largest=4)
    assert mime == 'image/jpeg' and Image.open(io.BytesIO(smaller)).size == (4, 4)


def test_la_matiere_d_une_case_d_atlas_vient_de_la_table():
    atlas = TABLE['atlases'][1]
    cells = M.cells_for('af-bench', tuple(atlas['size']), TABLE)
    # La table compte ses rangées du bas : le calcaire de la première case est en bas à gauche.
    assert cells[-1][0] == TABLE['matters']['limestone']
    assert cells[1][0] == TABLE['matters']['bronze']
    assert M.cells_for('banner-empire', (1024, 1536), TABLE) == [[TABLE['matters']['cloth']]]
    assert M.cells_for('piece-inconnue', (640, 480), TABLE) == [[TABLE['matters']['default']]]


def test_un_creux_sombre_penche_la_normale_et_perd_de_l_ambiance():
    stripes = Image.new('RGB', (64, 64), (200, 200, 200))
    for x in range(28, 36):
        for y in range(64):
            stripes.putpixel((x, y), (60, 60, 60))
    normal, material = M.derive_maps(stripes, [[TABLE['matters']['limestone']]])
    left, flat, right = normal.getpixel((27, 32)), normal.getpixel((8, 32)), normal.getpixel((36, 32))
    assert abs(flat[0] - 128) <= 2 and abs(flat[1] - 128) <= 2
    assert left[0] > 140 and right[0] < 116, 'les deux bords du joint penchent vers lui'
    assert material.getpixel((32, 32))[0] < material.getpixel((8, 32))[0], 'le creux est occlus'
    assert material.getpixel((8, 32))[2] == 0, 'le calcaire n\'est pas un métal'
