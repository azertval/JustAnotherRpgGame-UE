"""Regression checks for the constructed city, not a test of art approval."""
import numpy as np
import pytest
import capital_city_layout as city
from capital_landscape import Landscape
from capital_urban_terrain import envelope


def test_eighty_references_include_regions_and_separate_underground_sites():
    assert len(city.REGIONS)==13
    assert len(city.LANDMARKS)==67
    assert city.LANDMARKS['X12'][0] is None
    assert city.LANDMARKS['X13'][2] is None
    assert city.LANDMARKS['X16'][:2]!=city.LANDMARKS['X20'][:2]


def test_grade_envelope_propagates_across_junctions_and_respects_endpoints():
    # Diamond-shaped junction: a steep third branch cannot keep a cliff.
    edges=[[(1,1)],[(0,1),(2,1),(3,1)],[(1,1)],[(1,1)]]
    result=envelope([0,20,2,30],edges)
    assert result.tolist()==[0,1,2,2]
    for i,neighbors in enumerate(edges):
        for j,limit in neighbors:assert abs(result[i]-result[j])<=limit


def test_height_sampling_rejects_wrapping_and_interpolates():
    terrain=Landscape((1,1),[0,0,2,2],np.array([[0,2],[4,6]],dtype=float),{},np.zeros((2,2)))
    assert terrain.height_at(1,1)==3
    assert terrain.height_at(2,2)==6
    with pytest.raises(ValueError):terrain.height_at(-1,1)


def test_height_encoding_fails_instead_of_clipping_a_summit():
    terrain=Landscape((1,1),[0,0,2,2],np.full((2,2),256.),{},np.zeros((2,2)))
    with pytest.raises(ValueError):terrain.height_units()
