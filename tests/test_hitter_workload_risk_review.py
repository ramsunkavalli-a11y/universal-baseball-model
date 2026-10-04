"""Regression checks for risk interpretation without altering the fitted recipe."""
import numpy as np
from universal_baseball.hitter_workload_risk import mixture_pmf, distribution_terms


def test_broadening_can_lower_unconditional_upper_quantile_near_zero_atom():
    p = np.array([.10065097024900589])
    mean = np.array([260.90541426651015])
    narrow = distribution_terms(mixture_pmf(p, mean), np.array([517]))
    broad = distribution_terms(mixture_pmf(p, mean, 5.513228323864157), np.array([517]))
    assert narrow['q90'][0] == 228
    assert broad['q90'][0] == 16
    assert broad['pinball'][0] > narrow['pinball'][0]


def test_positive_spread_cannot_override_appearance_probability():
    p = np.array([0., .06, .99])
    mean = np.array([500., 170., 565.])
    for k in [.1, 5., 1000.]:
        law = mixture_pmf(p, mean, k)
        summary = distribution_terms(law, np.array([0, 489, 0]))
        assert np.all(summary['p400'] <= p + 1e-12)
        assert summary['q90'][1] == 0
        assert np.array_equal(law[:, 0], 1-p)
        assert np.allclose(law @ np.arange(801), p*mean, atol=1e-6)
