import numpy as np
import pytest
from scipy.optimize import lsq_linear

from universal_baseball.foreign_borrowed_stability import domestic_pairs,solve_stability,source_coordinates
from universal_baseball.foreign_component_translation import References
from test_foreign_component_translation import row


def test_closed_form_matches_constrained_solver():
    rng=np.random.default_rng(5);x=rng.normal(size=(80,8));y=.8*x+rng.normal(size=(80,8));w=rng.uniform(.1,1,80)
    a,b=solve_stability(x,y,w)
    for j in range(8):
        d=np.c_[np.ones(80),x[:,j]];z=np.vstack([d*np.sqrt(w)[:,None],np.eye(2)*np.sqrt(2)])
        t=np.r_[y[:,j]*np.sqrt(w),[0,0]]
        fit=lsq_linear(z,t,bounds=([-np.inf,0],[np.inf,2]),tol=1e-12)
        assert np.allclose([a[j],b[j]],fit.x,rtol=0,atol=1e-9)


def test_negative_and_extreme_slope_constraints():
    x=np.tile(np.linspace(-2,2,40)[:,None],(1,8));w=np.ones(40)
    assert (solve_stability(x,-x,w)[1]==0).all()
    assert (solve_stability(x,20*x,w)[1]==2).all()
    with pytest.raises(ValueError):solve_stability([],[],[])


def test_calibration_coverage_roles_and_future_rows():
    rows=[dict(row(1,y,'MLB'),position='4',reported_age=25) for y in range(2012,2016)]
    pairs=domestic_pairs(rows)
    assert len(pairs)==3 and len(pairs[-1]['history'])==3
    assert domestic_pairs(rows+[dict(rows[-1],season=2099)])==pairs
    assert domestic_pairs([dict(r,position='1') for r in rows])==[]
    assert domestic_pairs([dict(r,position='X') for r in rows])==[]


def test_primary_2020_exclusions_not_fake_zero_history():
    rows=[dict(row(1,y,'MLB'),position='4',reported_age=25) for y in range(2018,2024)]
    p=domestic_pairs(rows)
    assert all(a['source_year']!=2020 and a['target_year']!=2020 for a in p)
    assert any(s['season']==2020 for a in p for s in a['history'])


def test_no_future_observation_in_source_pool():
    rows=[dict(row(1,y,'MLB'),position='4',reported_age=25) for y in range(2012,2015)]
    p=domestic_pairs(rows)[0];refs=References(rows)
    x=source_coordinates(p,refs,[])
    with pytest.raises(ValueError):source_coordinates(dict(p,history=p['history']+[dict(season=2014,recency=5,counts=[100,0,0,0,0,0,0,0])]),refs,[])
    assert np.isfinite(x).all()
