import numpy as np
import pytest
from universal_baseball.hitter_compatible_value import replacement,labels,envelope


def test_short_season_reference_is_not_scaled_twice():
    full=replacement(180000,1)
    short=replacement(180000*60/162,60/162)
    assert full==pytest.approx(short)
    assert short*600==pytest.approx(1.9)
    with pytest.raises(ValueError):replacement(0,1)


def test_zero_is_delivered_zero_not_observed_talent():
    env=np.tile(np.array([.45,.23,.08,.01,.15,.045,.005,.03]),(2,1))
    counts=np.array([[0]*8,[40,20,10,1,17,6,1,5]],dtype=float)
    z=labels(counts,env,env,np.array([.003,.003]))
    assert z['common_value'][0]==0 and z['relative_value'][0]==0
    assert z['pa'][0]==0
    assert np.array_equal(z['common_rate'],z['relative_rate'])
    lo,hi=envelope(z['pa'],env@__import__('universal_baseball.mlb_event_logit',fromlist=['VALUES']).VALUES,.003)
    assert np.all((z['common_value']>=lo)&(z['common_value']<=hi))


def test_target_environment_changes_labels_not_origin_input():
    origin=np.full((1,8),1/8);target=origin.copy();target[0,0]-=.02;target[0,7]+=.02
    counts=np.array([[10,3,1,0,2,1,0,1]],float)
    a=labels(counts,origin,origin,np.array([.003]));b=labels(counts,origin,target,np.array([.003]))
    assert np.array_equal(a['common_value'],b['common_value'])
    assert not np.array_equal(a['relative_value'],b['relative_value'])
    assert np.array_equal(origin,np.full((1,8),1/8))
