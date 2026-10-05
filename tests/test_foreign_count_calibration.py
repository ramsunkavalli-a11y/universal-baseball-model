import numpy as np
import pytest
from scipy.optimize._numdiff import approx_derivative
from universal_baseball.foreign_count_calibration import objective, solve, fresh_foreign_route


def data():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(20, 8))
    c = rng.integers(1, 40, size=(20, 8))
    t = c / c.sum(1, keepdims=True)
    env = np.full((20, 8), 1/8)
    return x, t, env, np.full(20, 100.)


@pytest.mark.parametrize('fixed', [None, np.array([np.zeros(8), np.ones(8)])])
def test_gradient_matches_finite_difference(fixed):
    x, t, env, w = data()
    z = np.linspace(-.3, .3, 16 if fixed is None else 8)
    value, gradient = objective(z, x, t, env, w, fixed=fixed)
    numeric = approx_derivative(lambda u: objective(u, x, t, env, w, fixed=fixed)[0], z).ravel()
    assert np.isfinite(value)
    assert np.allclose(gradient, numeric, atol=1e-5, rtol=1e-7)


def test_bound_optimum():
    x, t, env, w = data()
    theta, note = solve(x, t, env, w)
    assert np.all(theta[8:] >= 0) and np.all(theta[8:] <= 2)
    assert note['projected_gradient_per_effective_PA'] < 1e-7


def test_empty_calibration_is_not_supported():
    with pytest.raises(ValueError, match='Missing positive'):
        objective(np.zeros(16), np.empty((0, 8)), np.empty((0, 8)), np.empty((0, 8)), np.array([]))


def source():
    return dict(origin_year=2024, foreign_history_counts={f'{l}_{lag}':
        dict(season=2024-lag, player_identity_and_stat_observed=l == 'NPB' and lag == 0,
             counts={'pa': 500 if l == 'NPB' and lag == 0 else 0})
        for l in ['NPB', 'KBO'] for lag in range(3)})


def test_cameo_does_not_erase_foreign_evidence():
    assert fresh_foreign_route(source(), [dict(season=2024, plate_appearances=10)], 2024)['eligible']


def test_newer_domestic_supersedes_old_foreign():
    s = source()
    s['foreign_history_counts']['NPB_0']['counts']['pa'] = 0
    s['foreign_history_counts']['NPB_1'].update(player_identity_and_stat_observed=True, counts={'pa': 500})
    assert not fresh_foreign_route(s, [dict(season=2024, plate_appearances=100)], 2024)['eligible']


def test_same_year_substantial_work_is_ambiguous():
    r = fresh_foreign_route(source(), [dict(season=2024, plate_appearances=100)], 2024)
    assert not r['eligible'] and r['same_year_ambiguous']


def test_future_domestic_mutation_does_not_change_route():
    s = source()
    assert fresh_foreign_route(s, [], 2024) == fresh_foreign_route(s, [dict(season=2025, plate_appearances=900)], 2024)


def test_future_source_lag_rejected():
    s = source(); s['foreign_history_counts']['NPB_0']['season'] = 2025
    with pytest.raises(ValueError, match='Future'):
        fresh_foreign_route(s, [], 2024)
