import numpy as np
import pytest
from universal_baseball.hitter_frozen_scoring import realized, error_metrics, score


def test_nonarrival_has_no_observed_talent_but_zero_delivery():
    env=np.ones(8)/8
    a=realized(np.array([[0]*8,[10]*8]),env,env,np.arange(8),1,.01)
    assert np.isnan(a['actual_relative_rate'][0])
    assert a['actual_relative_value'][0]==0
    assert np.isclose(a['actual_relative_value'][1],.8)
    s=score(np.array([.1,.9]),np.array([8,72]),np.array([99,0]),np.array([.08,.72]),a)
    assert s['conditional_rate_pa_weighted']['n']==1
    assert s['conditional_rate_pa_weighted']['rmse']==0
    assert np.isclose(s['brier'],.01)


def test_future_and_origin_references_differ_without_changing_forecast():
    o=np.ones(8)/8;t=np.array([0]*7+[1.])
    a=realized(np.array([[0]*7+[100]]),o,t,np.arange(8),2,.01)
    assert a['actual_relative_rate'][0]==0
    assert a['actual_common_rate'][0]==7
    assert np.isclose(a['actual_relative_value'][0],1)


def test_full_league_relative_batting_sums_zero():
    c=np.array([[0,1,2,3,4,5,6,7],[7,6,5,4,3,2,1,0]])
    env=c.sum(0)/c.sum()
    a=realized(c,env,env,np.arange(8),50,.003)
    assert np.isclose(a['actual_relative_value'].sum(),c.sum()*.003)


def test_invalid_unknown_outcomes_not_zeros():
    with pytest.raises(ValueError):error_metrics([1],[float('nan')])
    with pytest.raises(ValueError):realized(np.full((1,8),np.nan),np.ones(8)/8,np.ones(8)/8,np.arange(8),1,.01)
