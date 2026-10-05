import numpy as np
import pytest
from universal_baseball.hitter_mlb_detail import reconstruct


def test_missing_coverage_is_not_zero_and_certified_absence_is():
    env = {y: np.ones(8)/8 for y in [2018, 2019, 2020]}
    values, note = reconstruct(1, 2020, {}, env)
    assert all(v == 0 for v in values.values())
    assert note['seasons'][0]['unshrunk_batting_per600'] is None
    with pytest.raises(ValueError): reconstruct(1, 2020, {}, {2020: np.ones(8)/8})


def test_pooled_shrink_once_and_future_mutation_invariant():
    env = {y: np.ones(8)/8 for y in [2018, 2019, 2020]}
    counts = {(2020, 1): np.array([80, 20, 10, 1, 20, 5, 1, 5.])}
    before, note = reconstruct(1, 2020, counts, env)
    assert np.isclose(before['quality_0'], before['pooled_mlb_quality'])
    counts[2021, 1] = np.ones(8)*10000; env[2021] = np.ones(8)/8
    assert reconstruct(1, 2020, counts, env) == (before, note)
