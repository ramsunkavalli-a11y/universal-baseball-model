import numpy as np
import pytest
from scipy.optimize import check_grad
from universal_baseball.mlb_event_logit import objective,probabilities,batting_rate
from universal_baseball.mlb_event_anchor import empirical_anchor,transport_anchor


def test_gradient_matches_independent_finite_difference():
    rng=np.random.default_rng(36);x=rng.normal(size=(4,3));counts=rng.integers(1,20,size=(4,8)).astype(float)
    q=np.ones((4,8))/8;b=rng.normal(scale=.1,size=28)
    assert check_grad(lambda z:objective(z,x,counts,q)[0],lambda z:objective(z,x,counts,q)[1],b)<1e-6


def test_zero_effect_is_league_average_not_invented_talent():
    q=np.array([[.48,.23,.08,.01,.13,.035,.005,.03]])
    p=probabilities(np.zeros((3,7)),np.zeros((1,2)),q)
    assert p==pytest.approx(q);assert batting_rate(p,q)[0]==pytest.approx(0,abs=1e-12)


def test_strong_log_odds_still_produce_coherent_event_probabilities():
    q=np.ones((2,8))/8;p=probabilities(np.full((2,7),50.),np.array([[1.],[-1.]]),q)
    assert (p>=0).all() and np.allclose(p.sum(1),1)


def test_empirical_anchor_retains_actual_evidence_and_empty_prior():
    q=np.ones((2,8))/8;counts=np.array([[40,20,10,0,15,5,0,10],[0]*8],float)
    anchor=empirical_anchor(counts,q)
    assert anchor.sum(1)==pytest.approx([1.,1.]);assert anchor[1]==pytest.approx(q[1])
    assert anchor[0,7]==pytest.approx((10+12.5)/200)


def test_transport_has_identity_and_recoverable_origin_odds():
    q=np.ones((1,8))/8;r=np.array([[.40,.25,.1,.01,.15,.04,.01,.04]])
    anchor=empirical_anchor(np.array([[30,20,5,1,20,5,2,17]],float),q)
    assert transport_anchor(anchor,q,q)==pytest.approx(anchor)
    assert transport_anchor(transport_anchor(anchor,q,r),r,q)==pytest.approx(anchor)
