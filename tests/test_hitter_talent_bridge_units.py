"""Regression examples for the two evaluation-unit errors caught in V74."""
import numpy as np

from universal_baseball.hitter_compatible_value import labels, envelope, UNIT
from universal_baseball.mlb_event_logit import VALUES


def test_common_origin_label_is_not_relative_target_label():
    counts = np.array([[60., 20., 8., 1., 7., 2., 0., 2.]])
    origin = counts / counts.sum(1, keepdims=True)
    target = origin.copy()
    target[0, 0] -= .02
    target[0, 7] += .02
    result = labels(counts, origin, target, np.array([.003]))
    assert np.allclose(result['common_rate'], 0)
    assert not np.allclose(result['common_rate'], result['relative_rate'])
    assert np.allclose(result['relative_rate'], -.02 * VALUES[7] * UNIT)


def test_season_value_bounds_are_not_rate_bounds():
    index = np.array([.32])
    pa, rep = np.array([10.]), np.array([.003])
    lo, hi = envelope(pa, index, rep)
    rate_lo = -index * UNIT
    rate_hi = (VALUES.max() - index) * UNIT
    rate = np.array([2.])
    assert ((rate >= rate_lo) & (rate <= rate_hi)).all()
    # A legal rate can look invalid against season-value bounds at ten PA.
    assert (rate > hi).all()
    value = pa * (rate / 600 + rep)
    assert ((value >= lo) & (value <= hi)).all()
