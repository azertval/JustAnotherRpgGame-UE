# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""La comparaison des captures à tolérance, par blocs (LOT-1014, `compare_captures.py`).

Sur des images fabriquées : le bruit d'un rendu temporel passe, un objet qui disparaît, une lumière
qui change ou une capture absente ne passent pas, et une référence vide n'est pas un succès.
"""
import json

import numpy as np
import pytest
from PIL import Image

import compare_captures as C

WIDTH, HEIGHT, BLOCK = 96, 48, 24


def _scene(seed=0, noise=0):
    """Un ciel en dégradé au-dessus d'un sol uni, avec un bloc clair : (HEIGHT, WIDTH, 3)."""
    rows = np.linspace(40, 200, HEIGHT)[:, None, None] * np.ones((1, WIDTH, 3))
    pixels = rows.copy()
    pixels[HEIGHT // 2:, :, :] = (140, 125, 98)
    pixels[12:36, 24:48, :] = (230, 225, 210)
    if noise:
        pixels += np.random.default_rng(seed).integers(-noise, noise + 1, pixels.shape)
    return np.clip(pixels, 0, 255).astype(np.uint8)


def _save(folder, name, pixels):
    folder.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, 'RGB').save(folder / name)


@pytest.fixture
def reference(tmp_path):
    """Une référence d'une capture, écrite par `--update` depuis une capture sans bruit."""
    captures = tmp_path / 'premiere'
    _save(captures, 'vue-1200.png', _scene())
    folder = tmp_path / 'reference'
    assert C.update(folder, captures, ['vue-1200.png']) == 0
    return folder


def test_un_bloc_vaut_la_moyenne_de_ses_pixels():
    pixels = np.zeros((BLOCK, 2 * BLOCK, 3), dtype=np.uint8)
    pixels[:, BLOCK:, :] = (10, 20, 30)
    pixels[0, :4, 0] = 144  # quatre pixels à 144 sur 576 : une unité de moyenne sur le rouge
    means = C.block_means(pixels, BLOCK)
    assert means.shape == (1, 2, 3)
    assert means[0, 0] == pytest.approx([1.0, 0.0, 0.0])
    assert means[0, 1] == pytest.approx([10.0, 20.0, 30.0])
    with pytest.raises(ValueError):
        C.block_means(np.zeros((BLOCK + 1, BLOCK, 3), dtype=np.uint8), BLOCK)


def test_la_reference_est_une_image_de_blocs(reference):
    settings = json.loads((reference / C.REFERENCE_FILE).read_text(encoding='utf-8'))
    assert settings['size'] == [WIDTH, HEIGHT]
    assert settings['captures'] == ['vue-1200.png']
    assert settings['block'] == C.DEFAULT_BLOCK
    with Image.open(reference / 'vue-1200.png') as image:
        assert image.size == (WIDTH // BLOCK, HEIGHT // BLOCK)


def test_la_meme_capture_passe(reference, tmp_path):
    _save(tmp_path / 'captures', 'vue-1200.png', _scene())
    assert C.check(reference, tmp_path / 'captures') == []


def test_le_bruit_d_un_rendu_temporel_passe(reference, tmp_path):
    """Un bruit de ±12 niveaux par pixel ne déplace pas la moyenne d'un bloc de 576 pixels."""
    _save(tmp_path / 'captures', 'vue-1200.png', _scene(seed=7, noise=12))
    assert C.check(reference, tmp_path / 'captures') == []


def test_un_objet_disparu_est_refuse(reference, tmp_path):
    pixels = _scene()
    pixels[12:36, 24:48, :] = (140, 125, 98)  # le bloc clair n'est plus là
    _save(tmp_path / 'captures', 'vue-1200.png', pixels)
    (error,) = C.check(reference, tmp_path / 'captures')
    assert 'vue-1200.png' in error and 'blocs' in error


def test_une_lumiere_qui_change_est_refusee(reference, tmp_path):
    darker = (_scene().astype(np.float64) * 0.8).astype(np.uint8)
    _save(tmp_path / 'captures', 'vue-1200.png', darker)
    assert len(C.check(reference, tmp_path / 'captures')) == 1


def test_un_ecart_sous_la_tolerance_passe(reference, tmp_path):
    shifted = np.clip(_scene().astype(np.int16) + 5, 0, 255).astype(np.uint8)
    _save(tmp_path / 'captures', 'vue-1200.png', shifted)
    assert C.check(reference, tmp_path / 'captures') == []


def test_la_part_de_blocs_admise_est_tenue(reference, tmp_path):
    """Un bloc sur huit hors tolérance : refusé à 1 %, admis à 20 %."""
    pixels = _scene()
    pixels[:BLOCK, :BLOCK, :] = 255
    _save(tmp_path / 'captures', 'vue-1200.png', pixels)
    assert len(C.check(reference, tmp_path / 'captures')) == 1
    settings = json.loads((reference / C.REFERENCE_FILE).read_text(encoding='utf-8'))
    settings['outliers'] = 0.2
    (reference / C.REFERENCE_FILE).write_text(json.dumps(settings), encoding='utf-8')
    assert C.check(reference, tmp_path / 'captures') == []


def test_une_capture_absente_ou_d_une_autre_taille_est_une_erreur(reference, tmp_path):
    (tmp_path / 'vide').mkdir()
    (error,) = C.check(reference, tmp_path / 'vide')
    assert 'capture absente' in error
    _save(tmp_path / 'petite', 'vue-1200.png', _scene()[:BLOCK, :, :])
    (error,) = C.check(reference, tmp_path / 'petite')
    assert 'attendus' in error


def test_une_reference_vide_n_est_pas_un_succes(tmp_path):
    assert C.check(tmp_path, tmp_path) != []
    (tmp_path / C.REFERENCE_FILE).write_text(json.dumps(
        {'block': BLOCK, 'tolerance': 8, 'outliers': 0.01, 'size': [WIDTH, HEIGHT], 'captures': []}),
        encoding='utf-8')
    (error,) = C.check(tmp_path, tmp_path)
    assert 'aucune capture de référence' in error
