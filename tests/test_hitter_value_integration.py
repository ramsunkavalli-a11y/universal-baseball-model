import numpy as np
import pytest
from sklearn.ensemble import HistGradientBoostingRegressor
from universal_baseball.hitter_value_integration import (
    contribution, count_forecast, poisson_trace, restricted_weights,
)
from universal_baseball.hitter_compatible_value import labels


def test_count_value_matches_independent_label_and_preserves_zero():
    counts = np.array([[100, 30, 20, 2, 40, 10, 1, 7], [0]*8], float)
    origin = np.tile([.4, .25, .1, .01, .15, .05, .01, .03], (2, 1))
    rep = np.array([.003, .003])
    from universal_baseball.mlb_event_logit import VALUES
    pa, value = contribution(counts, origin @ VALUES, rep)
    expected = labels(counts, origin, origin, rep)
    np.testing.assert_allclose(pa, expected['pa'])
    np.testing.assert_allclose(value, expected['common_value'])
    assert pa[1] == value[1] == 0


def test_count_cap_is_joint_and_hard_unavailable_is_zero():
    counts = np.array([[1000, 250, 100, 5, 100, 25, 2, 40], [1]*8], float)
    pred = count_forecast(counts, [False, True], [.31, .31], [.003, .003])
    assert pred['capped'].tolist() == [True, False]
    np.testing.assert_allclose(pred['counts'][0] / counts[0], 800 / counts[0].sum())
    np.testing.assert_allclose(pred['pa'], [800, 0])
    assert pred['value'][1] == 0
    with pytest.raises(ValueError):
        contribution(np.full((1, 8), -1), [.3], [.003])


def test_active_weights_restrict_full_measure_without_new_origin_balance():
    w = restricted_weights([1, 1, 2, 2], [True, False, True, True])
    np.testing.assert_allclose(w, [.6, 1.2, 1.2])


def test_poisson_path_reconstructs_count_mean_not_log_mean():
    x = np.arange(80, dtype=float)[:, None]
    y = np.where(x[:, 0] < 40, 0., 12.)
    model = HistGradientBoostingRegressor(loss='poisson', max_iter=8,
        min_samples_leaf=5, early_stopping=False, random_state=31).fit(x, y)
    result = poisson_trace(model, x[60], ['exposure'])
    np.testing.assert_allclose(result['mean'], model.predict(x[60:61])[0])
    assert result['mean'] != result['log_mean']
