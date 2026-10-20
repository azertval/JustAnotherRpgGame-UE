# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Le paysage de la capitale se calcule depuis son relevé : la géographie du plan y tient."""
import numpy as np
import pytest

import capital_landscape as landscape
import capital_landscape_layout as layout


@pytest.fixture(scope="module")
def terrain():
    return landscape.generate()


def at(terrain, units):
    return terrain.height_at(*layout.metres(units))


def test_terrain_is_a_whole_number_of_landscape_components(terrain):
    assert terrain.quads == (1512, 1008)
    assert all(quads % landscape.QUADS_PER_COMPONENT == 0 for quads in terrain.quads)
    assert terrain.heights.shape == (1009, 1513)


def test_same_survey_gives_same_bytes(terrain):
    again = landscape.generate()
    assert again.height_units().tobytes() == terrain.height_units().tobytes()
    assert all(again.weights[name].tobytes() == terrain.weights[name].tobytes() for name in terrain.weights)


def test_arena_threshold_is_the_datum(terrain):
    assert terrain.height_at(0.0, 0.0) == 0.0
    assert at(terrain, layout.ENTRY_UNITS) == 0.0


@pytest.mark.parametrize("name,units", [("baie", (600, 250)), ("rivière", (1500, 418)), ("ruisseau", (240, 1200)),
                                         ("natural pool", (910, 437)), ("aqueduc", (1905, 610))])
def test_water_lies_below_sea_level(terrain, name, units):
    assert at(terrain, units) < layout.SEA_LEVEL - 0.5, name


@pytest.mark.parametrize("name,units", [("palais", (655, 640)), ("downtown", (1100, 850)), ("oldtown", (1400, 250)),
                                         ("sloghood", (400, 1000)), ("île de cyan fortress", (100, 540)),
                                         ("cultures", (1700, 1400)), ("stone fortress", (1850, 262))])
def test_districts_stand_above_the_water(terrain, name, units):
    assert at(terrain, units) > layout.SEA_LEVEL + 2.0, name


def test_river_separates_oldtown_from_the_walled_city(terrain):
    """De l'Arena Gate à Oldtown, on traverse l'eau : aucune rivière ne coupe la ville close."""
    (x0, y0), (x1, y1) = layout.metres((1275, 345)), layout.metres((1345, 275))
    crossing = [terrain.height_at(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t) for t in np.linspace(0, 1, 40)]
    assert min(crossing) < layout.SEA_LEVEL
    (x0, y0), (x1, y1) = layout.metres((700, 900)), layout.metres((1600, 900))
    inside = [terrain.height_at(x0 + (x1 - x0) * t, y0) for t in np.linspace(0, 1, 80)]
    assert min(inside) > layout.SEA_LEVEL + 2.0


def test_city_has_hills_and_ridge_dominates(terrain):
    """La ville n'est pas plate : ses collines dominent leurs vallons, le palais reste sous la chaîne."""
    assert at(terrain, (1190, 790)) - at(terrain, (1083, 420)) > 25.0     # Downtown au-dessus du seuil de l'arène
    assert at(terrain, (1190, 790)) - at(terrain, (1120, 700)) > 5.0      # et de Shield Avenue, en vallon
    assert at(terrain, (1440, 1010)) - at(terrain, (1400, 950)) > 4.0     # la butte de Dweomer
    assert at(terrain, (655, 640)) < at(terrain, (1850, 262)) < 256.0
    assert 100.0 < terrain.heights.max() < 250.0
    assert terrain.heights.min() >= layout.EDGE["floor"]


def test_layer_weights_sum_to_full_everywhere(terrain):
    total = sum(weights.astype(np.int32) for weights in terrain.weights.values())
    assert total.min() == 255 and total.max() == 255
    assert set(terrain.weights) == {item["id"] for item in layout.LAYERS}


def test_layers_follow_the_survey(terrain):
    def weight(name, units):
        x, y = layout.metres(units)
        i, j = round((x - terrain.area[0]) / layout.RESOLUTION), round((y - terrain.area[1]) / layout.RESOLUTION)
        return int(terrain.weights[name][j - 3:j + 4, i - 3:i + 4].mean())

    assert weight("sous-bois", (2050, 900)) > 150      # The Northwoods
    assert weight("sable", (1120, 700)) > 150         # Shield Avenue
    assert weight("herbe", (860, 835)) > 150           # Tyreen's Verdant
    assert weight("sous-bois", (1100, 900)) < 30       # pas de bois dans Downtown


def test_no_valley_floods_inside_the_walls(terrain):
    """Hors du Natural Pool, rien dans l'enceinte n'est sous le niveau de la mer."""
    for units in ((1120, 700), (1160, 880), (1280, 1110), (1400, 950), (700, 945), (1000, 935)):
        assert at(terrain, units) > layout.SEA_LEVEL + 2.0, units


def test_stacked_masks_rebuild_the_painted_weights(terrain):
    """Empilées dans l'ordre de la matière, les couches redonnent les poids peints."""
    order = [item["id"] for item in layout.LAYERS]
    masks = terrain.masks()
    assert list(masks) == order[1:]
    cover = {order[0]: np.ones(terrain.heights.shape)}
    for name in order[1:]:
        mask = masks[name] / 255.0
        cover = {k: v * (1.0 - mask) for k, v in cover.items()}
        cover[name] = mask
    for name in order:
        assert np.abs(cover[name] - terrain.weights[name] / 255.0).max() < 0.03, name
