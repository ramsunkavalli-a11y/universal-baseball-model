import numpy as np
import pytest
from universal_baseball.model_decision_audit import batting_identity,exposure_weighted_identity


def test_marginal_product_contrast_does_not_depend_on_new_workload():
    a=batting_identity(2,300,np.array([0,100,600]),3)
    np.testing.assert_allclose(a['marginal']-a['product'],.5)
    # A direct residual can survive even when new exposure is zero.
    assert a['marginal'][0]==.5 and a['product'][0]==0


def test_weighted_rate_product_does_not_require_independence():
    a=exposure_weighted_identity([.5,.5],[100,600],[0,4])
    assert a['expected_production']==1200
    assert a['unweighted_product']==700
    assert np.isclose(a['expected_exposure']*a['weighted_rate'],1200)


def test_mean_and_median_scores_can_legitimately_disagree():
    # Ninety no-value outcomes and ten ten-win outcomes: mean one, median zero.
    y=np.array([0]*90+[10]*10)
    assert np.mean((y-1)**2)<np.mean(y**2)
    assert np.mean(abs(y-1))>np.mean(abs(y))


@pytest.mark.parametrize('p,w,r', [([1],[0],[1]),([.5],[1],[1]),([1],[-1],[1]),([1],[1],[float('nan')])])
def test_invalid_weighted_identity(p,w,r):
    with pytest.raises(ValueError):exposure_weighted_identity(p,w,r)
