import numpy as np
import pytest
from scipy.optimize import check_grad
from universal_baseball.hitter_mlb_value_calibration import (
    affine_objective,
    fit_value,
    tilt_to_value,
    predict_value,
    WEIGHTS,
)


def test_affine_gradient():
    x = np.array([-0.05, 0.01, 0.04])
    y = x * 0.7 - 0.01
    w = np.array([0.2, 0.5, 0.3])
    assert (
        check_grad(
            lambda t: affine_objective(t, x, y, w)[0],
            lambda t: affine_objective(t, x, y, w)[1],
            np.array([0.01, 0.9]),
        )
        < 1e-7
    )


def test_tilt_hits_target_preserving_equal_weight_ratios():
    p = np.random.default_rng(7).dirichlet(np.ones(12) * 4, 20)
    target = p @ WEIGHTS * 0.9
    q = tilt_to_value(p, target)
    assert np.allclose(q @ WEIGHTS, target, atol=1e-9)
    assert np.all(q > 0) and np.allclose(q.sum(axis=1), 1)
    zero = np.flatnonzero(WEIGHTS == 0)
    assert np.allclose(q[:, zero[0]] / q[:, zero[1]], p[:, zero[0]] / p[:, zero[1]])
    assert np.allclose(tilt_to_value(p, p @ WEIGHTS), p)


def test_chronology_and_group_fallback():
    p = np.ones((10, 12)) / 12
    counts = p * 100
    minor = np.ones(10, dtype=bool)
    with pytest.raises(ValueError, match="precede"):
        fit_value(p, counts, minor, forecast_year=2023, training_years=[2023])
    fit = fit_value(p, counts, minor, forecast_year=2023, training_years=[2022])
    assert np.allclose(fit[0], [0, 1])
    q, clipped = predict_value(p, minor, fit)
    assert clipped == 0 and np.allclose(q, p)
