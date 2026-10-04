import numpy as np
import pytest
from scipy.stats import norm
from universal_baseball.hitter_offense_risk import (
    fit_rate_variances, offense_distribution, rate_variance)


def point_pmf(p, n):
    z = np.zeros((1, 801)); z[0, 0] = 1-p; z[0, n] = p
    return z


def args():
    return dict(origin_index=np.array([.3]), unit=50., event_min=0., event_max=2.)


def test_fixed_negative_yield_quantiles_reverse_pa_order():
    z = point_pmf(.8, 600)
    t = offense_distribution(z, [-2.], [.001], [0.])
    assert np.allclose([t['q10'][0], t['q50'][0], t['q90'][0]], [-1.4, -1.4, 0])
    assert t['p_negative'][0] == .8


def test_conditional_normal_matches_scalar_and_mean():
    z = point_pmf(1, 600)
    t = offense_distribution(z, [1.], [.002], [2.], a=4., **args())
    assert np.allclose([t['q10'][0], t['q50'][0], t['q90'][0]], norm.ppf([.1, .5, .9], 2.2, 2), atol=1e-8)
    assert t['expected_value'][0] == pytest.approx(2.2)
    assert t['p_two'][0] == pytest.approx(norm.sf(2, 2.2, 2))


def test_zero_atom_can_contain_all_three_quantiles():
    t = offense_distribution(point_pmf(.01, 500), [1.], [.002], [0.], a=2., **args())
    assert all(t[q][0] == 0 for q in ['q10', 'q50', 'q90'])
    assert 0 <= t['p_negative'][0] <= .01


def test_nonarrival_has_exact_zero_and_zero_events():
    t = offense_distribution(point_pmf(0, 200), [2.], [.002], [0.], a=4., **args())
    assert t['pinball'][0] == t['expected_value'][0] == t['p_negative'][0] == t['p_two'][0] == 0


def test_sample_dependent_rate_noise_shrinks_not_to_zero():
    assert np.allclose(rate_variance([60, 600], 1, 2), [21, 3])


def test_variance_fit_keeps_bias_and_boundaries():
    fit = fit_rate_variances([1, 1, 1, 1], [60, 120, 300, 600], np.ones(4))
    assert fit['constant_variance'] == fit['residual_bias'] == 1
    assert fit['sample_dependent']['a'] == pytest.approx(1, abs=1e-4)
    assert fit['sample_dependent']['b'] < 1e-5


def test_impossible_normal_mass_is_reported_not_clipped():
    t = offense_distribution(point_pmf(1, 1), [0.], [.002], [0.], a=10000., **args())
    assert t['impossible_mass'][0] > .1
    assert t['expected_value'][0] == pytest.approx(.002)


def test_bad_calibration_is_not_zero():
    with pytest.raises(ValueError):
        fit_rate_variances([0], [0], [1])
    with pytest.raises(ValueError):
        rate_variance([10], -1, 0)
