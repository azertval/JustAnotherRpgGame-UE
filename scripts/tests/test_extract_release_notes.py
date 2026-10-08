# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

"""Notes de release tirées du CHANGELOG (scripts/release/extract_release_notes.py)."""
import pytest

from extract_release_notes import extract, normalize_version

CHANGELOG = """# Changelog

## [Non publié]

## [0.0.2.5] - 2026-10-05

Le passage à la 3D.

- Un lot.

## [0.0.2] - 2026-09-30

Le combat.
"""


@pytest.mark.parametrize('reference, version', [
    ('v0.0.2', '0.0.2'),
    ('0.0.2', '0.0.2'),
    ('v0.0.2.5', '0.0.2.5'),  # une version intercalée : le tag gardait son `v` (LOT-1010)
    ('0.0.2.5', '0.0.2.5'),
    ('v10.20.30', '10.20.30'),
    ('debug-latest', 'debug-latest'),
    ('v0.0', 'v0.0'),
    ('v0.0.2.5.1', 'v0.0.2.5.1'),
])
def test_le_prefixe_du_tag_est_retire(reference, version):
    assert normalize_version(reference) == version


def test_la_section_d_une_version_a_quatre_nombres_se_lit():
    assert extract(CHANGELOG, normalize_version('v0.0.2.5')) == 'Le passage à la 3D.\n\n- Un lot.'


def test_une_version_ne_prend_pas_la_section_de_celle_qu_elle_prefixe():
    assert extract(CHANGELOG, '0.0.2') == 'Le combat.'


def test_une_section_absente_ne_rend_rien():
    assert extract(CHANGELOG, '0.0.3') is None
