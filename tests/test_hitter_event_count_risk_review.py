"""Independent moment and numerical-score checks for the count-risk review."""
import numpy as np
from scipy.stats import dirichlet_multinomial

from universal_baseball.hitter_event_count_risk import mixture_terms, rate_variance, simulate, tilt
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES

REF = np.array([.46, .23, .08, .01, .14, .045, .005, .03])


def test_exact_one_pa_distribution_mean_and_variance():
    q = tilt(REF, [.32])[0]
    draws = simulate(REF, 0., .32, .003, 1., 1., 5., 400., 0., row_id=5, draws=60000)
    assert np.all(draws['pa'] == 1)
    assert np.all(draws['counts'].sum(1) == 1)
    expected = .003
    var = rate_variance(q[None], np.array([1]), 400.)[0]/600**2
    assert abs(draws['values'].mean()-expected) < 5*np.sqrt(var/60000)
    assert np.isclose(draws['values'].var(), var, rtol=.035)


def test_multinomial_limit_covariance_and_event_weights():
    q = tilt(REF, [.4])[0]; n = 600; phi = 1e6
    cov = dirichlet_multinomial.cov(phi*q, n)
    variance = float(VALUES @ cov @ VALUES)*UNIT**2/n**2
    assert np.isclose(rate_variance(q[None], np.array([n]), phi)[0], variance, rtol=1e-12)


def test_mixture_proper_losses_independent_direct_formula():
    values = np.array([-1., 1., 2., 3.]); p = .6; actual = 4.
    terms = mixture_terms(values, p, actual)
    # Weighted support is (-1,.15),(0,.4),(1,.15),(2,.15),(3,.15).
    quantiles = np.array([-1., 0., 3.])
    assert [terms['q10'], terms['q50'], terms['q90']] == quantiles.tolist()
    assert np.isclose(terms['pinball'], np.mean(np.array([.1,.5,.9])*(actual-quantiles)))
    assert terms['interval_score'] == 14.
    assert terms['p_negative'] == .15
    assert terms['p_two'] == .3


def test_associated_mean_identity_at_both_slope_limits():
    for beta in [-1., 1.]:
        draw = simulate(REF, .7, .32, .003, .37, 140., 4.8, 400., beta,
                        row_id=105, draws=20000, replicate=3)
        theoretical = .37*140*(.7/600+.003)
        assert np.isclose(draw['expected_value'], theoretical, atol=1e-10, rtol=0)
        # Sampling variation is measured, never subtracted from every draw.
        se = .37*np.std(draw['values'], ddof=1)/np.sqrt(20000)
        assert abs(.37*draw['values'].mean()-theoretical) < 5*se
