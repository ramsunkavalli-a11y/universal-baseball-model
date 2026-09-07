import numpy as np
import pytest
from scipy.optimize import check_grad
from universal_baseball.hitter_calibration_batch import (
    objective,
    fit_calibration,
    Calibration,
    cluster_rmse_interval,
)


def toy():
    rng = np.random.default_rng(12)
    p = rng.dirichlet(np.ones(12) * 4, 30)
    counts = np.array([rng.multinomial(300, q) for q in p])
    groups = np.arange(30) % 7
    return p, counts, groups


@pytest.mark.parametrize("by_origin", [False, True])
def test_analytic_gradient_and_probability_validity(by_origin):
    p, counts, groups = toy()
    theta = np.zeros(13 + (84 if by_origin else 0))
    theta[0] = 0.9
    args = (np.log(p), counts, groups, by_origin)
    assert (
        check_grad(
            lambda t: objective(t, *args)[0], lambda t: objective(t, *args)[1], theta
        )
        < 1e-5
    )
    fit = fit_calibration(
        p,
        counts,
        groups,
        by_origin=by_origin,
        forecast_year=2023,
        training_years=[2022],
    )
    q = fit.predict(p, groups)
    assert np.all(q > 0)
    assert np.allclose(q.sum(axis=1), 1)
    assert 0.5 <= fit.theta[0] <= 1.5


def test_identity_and_future_outcomes_rejected():
    p, counts, groups = toy()
    theta = np.zeros(13)
    theta[0] = 1
    assert np.allclose(Calibration(theta, False, 2022, (), 0).predict(p, groups), p)
    with pytest.raises(ValueError, match="precede"):
        fit_calibration(
            p,
            counts,
            groups,
            by_origin=False,
            forecast_year=2023,
            training_years=[2023],
        )
    with pytest.raises(ValueError, match="precede"):
        fit_calibration(
            p,
            counts,
            groups,
            by_origin=False,
            forecast_year=2026,
            training_years=[2022],
        )


def test_player_cluster_resampling_keeps_repeat_years_together():
    ids = np.array([1, 1, 2, 2])
    pa = np.ones(4)
    reference = np.array([0.1, 0.2, 0.3, 0.4])
    same = cluster_rmse_interval(ids, pa, reference, reference, replicates=50)
    assert same["lower"] == same["upper"] == 0
    assert same["unique_players"] == 2
    # Splitting each observation into two half-weight rows preserves every replicate.
    a = cluster_rmse_interval(ids, pa, reference * 0.9, reference, replicates=50)
    b = cluster_rmse_interval(
        np.repeat(ids, 2),
        np.repeat(pa / 2, 2),
        np.repeat(reference * 0.9, 2),
        np.repeat(reference, 2),
        replicates=50,
    )
    assert a["lower"] == pytest.approx(b["lower"])
    assert a["upper"] == pytest.approx(b["upper"])
