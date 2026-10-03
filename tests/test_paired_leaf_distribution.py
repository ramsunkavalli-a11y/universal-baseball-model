import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from universal_baseball.paired_leaf_distribution import predictions,observation_weights


def test_paired_mean_probability_and_nonarrival_preserved():
    x=np.arange(60).reshape(-1,1).astype(float);pa=np.tile([0,50,500],20);v=np.tile([0,-1,3],20)
    w=np.linspace(.5,2,60);m=ExtraTreesRegressor(n_estimators=5,min_samples_leaf=5,random_state=43,bootstrap=False)
    m.fit(x,np.column_stack([pa/600,v/2]),sample_weight=w)
    means,p,q=predictions(m,x,x[:4],pa,v,w)
    for j in range(4):
        a=observation_weights(m,x,x[j],w)
        assert np.allclose([a@pa,a@v],means[j])
        assert np.allclose([a@(pa>0),a@(pa>=400),a@(v<0),a@(v>=2)],p[j])
    assert (q[:,0]<=q[:,1]).all() and (q[:,1]<=q[:,2]).all()
