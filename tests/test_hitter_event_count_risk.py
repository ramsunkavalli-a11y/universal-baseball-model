import numpy as np
import pytest
from scipy.stats import dirichlet_multinomial
from universal_baseball.hitter_event_count_risk import (
    tilt, rate_variance, workload_center, simulate, mixture_terms, fit_count_laws)
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES

REF = np.array([.46, .23, .08, .01, .14, .045, .005, .03])


def test_tilt_preserves_mean_and_all_categories():
    p = tilt(REF, [.15, .3, .5])
    assert (p > 0).all() and np.allclose(p.sum(1), 1)
    assert np.allclose(p @ VALUES, [.15, .3, .5], atol=1e-12)
    assert np.allclose(p[:, 0]/p[:, 1], REF[0]/REF[1])


def test_impossible_center_is_not_clipped():
    with pytest.raises(ValueError): tilt(REF, [-.1])
    with pytest.raises(ValueError): tilt(REF, [VALUES.max()])


def test_count_moment_matches_official_covariance():
    for n in [1, 10, 600]:
        phi = 300.
        cov = dirichlet_multinomial.cov(phi*REF, n)
        expected = UNIT**2*(VALUES @ cov @ VALUES)/n**2
        assert rate_variance(REF[None], np.array([n]), phi)[0] == pytest.approx(expected)


def test_workload_log_center_conserves_batting_mean():
    c, pmf = workload_center([25, 300, 700], 5.)
    n = np.arange(1, 801)
    assert np.allclose((pmf*(n*(np.log(n)[None]-c[:, None]))).sum(1), 0, atol=1e-8)


def test_real_counts_for_one_and_many_pa():
    for mean in [1, 300, 800]:
        r = simulate(REF, 1., .3, .002, .6, mean, 5., 300., .5, row_id=12, draws=128)
        assert np.array_equal(r['counts'].sum(1), r['pa'])
        assert r['expected_value'] == pytest.approx(.6*mean*(1/600+.002))
        assert np.all(r['counts'] >= 0)


def test_zero_atom_exact_with_signed_positive_outcomes():
    t = mixture_terms([-1, 1, 2, 3], .01, 0)
    assert t['q10'] == t['q50'] == t['q90'] == 0
    assert t['p_negative'] == .0025
    assert t['p_two'] == .005


def test_zero_activity_has_zero_metrics():
    t = mixture_terms([-1, 1], 0, 0)
    assert t['q10'] == t['q50'] == t['q90'] == t['pinball'] == t['p_negative'] == t['p_two'] == 0


def test_seed_is_row_order_independent_and_not_recentered():
    kwargs = dict(reference=REF, rate=0., index=.3, rep=.002, p=.8,
                  conditional_mean=100, concentration=5., phi=400., beta=.2, row_id=2, draws=100)
    a, b = simulate(**kwargs), simulate(**kwargs)
    assert np.array_equal(a['counts'], b['counts'])
    assert np.array_equal(a['values'], b['values'])
    assert not np.isclose(.8*a['values'].mean(), a['expected_value'], atol=1e-10)
