import numpy as np
import pytest

from universal_baseball.hitter_direct_events import convert, proper_losses, rate_routing
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES

REF = np.array([.52,.22,.08,.01,.1,.04,.005,.025])


def test_reference_is_zero_and_power_conversion_is_defined():
    rate, terms = convert(REF, REF)
    assert rate == 0 and not terms.any()
    p = REF.copy(); p[0] -= .01; p[7] += .01
    assert np.isclose(convert(p, REF)[0], .01 * VALUES[7] * UNIT)
    assert np.isclose(convert(p, REF)[1].sum(), convert(p, REF)[0])


def test_hit_to_strikeout_cannot_improve_defined_value():
    p = REF.copy(); p[4] -= .01; p[1] += .01
    assert convert(p, REF)[0] < 0


def test_proper_brier_is_expected_one_hot_not_frequency_distance():
    c = REF * 1000
    ll, br = proper_losses(REF, c)
    assert np.isclose(ll, -(REF * np.log(REF)).sum())
    assert np.isclose(br, 1 - (REF * REF).sum())
    alternative = REF.copy(); alternative[0] -= .04; alternative[7] += .04
    assert proper_losses(alternative, c)[0] > ll
    assert proper_losses(alternative, c)[1] > br


def test_zero_actual_pa_is_not_an_observed_rate():
    with pytest.raises(ValueError): proper_losses(REF, np.zeros(8))


def test_no_negative_or_unpaired_probabilities():
    with pytest.raises(ValueError): convert(REF * 2, REF)
    with pytest.raises(ValueError): convert(REF, REF[None,:])


def test_missing_profile_and_mlb_routes_preserved():
    result, used = rate_routing(np.array([4.,4.,4.,4.]),
        np.array([True,False,True,False]),np.array([0,0,1,1]),
        np.array([False,False,False,True]),np.array([1.,1.,1.,1.]),np.array([2.,2.,2.,2.]))
    assert np.array_equal(result, [4.,1.,1.,2.])
    assert np.array_equal(used, [True,False,False,False])
