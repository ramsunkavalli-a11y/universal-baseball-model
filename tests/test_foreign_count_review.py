import numpy as np
import pytest
from universal_baseball.foreign_count_review import loss_gradient, kkt_residual, peer_distance, pooled_coordinate


@pytest.mark.parametrize('foreign', [False, True])
def test_independent_gradient(foreign):
    rng = np.random.default_rng(8)
    x = rng.normal(size=(5,8)); y=rng.dirichlet(np.ones(8),5); ref=rng.dirichlet(np.ones(8),5)
    w=np.arange(1.,6.); theta=rng.normal(size=8 if foreign else 16)
    fixed=rng.normal(size=(2,8)) if foreign else None
    _, g=loss_gradient(theta,x,y,ref,w,fixed)
    numerical=[]
    for j in range(len(theta)):
        step=np.zeros(len(theta)); step[j]=1e-5
        numerical.append((loss_gradient(theta+step,x,y,ref,w,fixed)[0]-loss_gradient(theta-step,x,y,ref,w,fixed)[0])/2e-5)
    np.testing.assert_allclose(g,numerical,atol=1e-7,rtol=0)


def test_bound_stationarity_is_not_zero_raw_gradient():
    theta=np.r_[np.zeros(8),np.zeros(4),np.ones(4)*2]
    g=np.r_[np.zeros(8),np.ones(4),-np.ones(4)]
    assert kkt_residual(theta,g,True)==0
    g[8]=-1
    assert kkt_residual(theta,g,True)==1


def test_peer_selection_cannot_see_future():
    a=dict(age=25,recent_foreign_pa=500,prior_debut=0,positive_MLB_context=False)
    b=dict(a,next_pa=0)
    before=peer_distance(a,b); b['next_pa']=600
    assert peer_distance(a,b)==before==0


def test_smoothed_pool_uses_exposure_and_centering():
    c=np.arange(8)*10
    x=pooled_coordinate([dict(counts=c,recency=5,reference=(c+.5)/(sum(c)+4))])
    np.testing.assert_allclose(x,0,atol=1e-12)
    with pytest.raises(ValueError): pooled_coordinate([])
