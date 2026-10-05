import numpy as np
import pytest

from universal_baseball.hitter_past_direct_value import baseline, fit


def test_zero_past_profile_is_league_mean_and_target_is_residual():
    ref = np.tile(np.array([.5, .2, .1, .01, .1, .05, .01, .03]), (4, 1))
    ref /= ref.sum(1, keepdims=True)
    assert np.allclose(baseline(np.zeros_like(ref), ref), 0)
    x = np.zeros((4, 2)); past = np.array([1, 2, 3, 4.])
    model = fit(x, past + 2, past, np.ones(4))
    assert np.allclose(model.predict(x), 2)


def test_profile_and_training_shape_or_missing_labels_raise():
    with pytest.raises(ValueError):
        baseline(np.zeros((1, 8)), np.zeros((1, 8)))
    with pytest.raises(ValueError):
        fit(np.zeros((2, 1)), [1, np.nan], [0, 0], [1, 1])
    with pytest.raises(ValueError):
        fit(np.zeros((2, 1)), [1, 1], [0, 0], [1, 0])
