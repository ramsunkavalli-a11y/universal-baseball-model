import numpy as np
import pytest
from scipy.optimize import check_grad
from universal_baseball.hitter_bounded_workload import SmoothWorkload,objective


@pytest.mark.parametrize('link',['logit','identity'])
def test_fraction_objective_gradient(link):
    x=np.array([[0.,1.],[1.,0.],[.2,.3]])
    y=np.array([0.,1.,.4]);w=np.array([1.,2.,1.])
    args=(x,y,w,link,.0001);b=np.array([.1,.3,-.2])
    assert check_grad(lambda v:objective(v,*args)[0],lambda v:objective(v,*args)[1],b)<1e-6


def test_zero_outcomes_kept_and_trace_reconstructs():
    names=['prior_debut','age_centered','MLB_0_pa']
    x=np.array([[0,0,0],[0,1,0],[1,1,500],[1,0,600],[1,-1,700.]],float)
    pa=np.array([0.,0.,400.,600.,700.])
    m=SmoothWorkload(names,'logit').fit(x,pa,np.ones(5))
    out=m.predict(x)
    assert np.all((out>0)&(out<800))
    assert out[0]<out[-1]
    t=m.trace(x[0]);assert t['raw_pa']==pytest.approx(out[0])
    assert t['intercept']+sum(v['term']for v in t['all_terms'])==pytest.approx(t['eta'])
    with pytest.raises(ValueError):m.basis(np.array([[0,np.nan,0]]))
    with pytest.raises(ValueError):m.fit(x,np.array([0,0,400,600,801]),np.ones(5))
