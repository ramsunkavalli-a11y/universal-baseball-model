import numpy as np
from scipy.optimize._numdiff import approx_derivative
from universal_baseball.mlb_predictive_reliability import objective,predict,transported_counts


def test_analytic_gradient_and_exact_zero_exposure_prior():
    rng=np.random.default_rng(50);x=rng.normal(size=(9,3));env=rng.dirichlet(np.ones(8),size=9)
    own=rng.uniform(0,30,(9,8));own[0]=0;counts=rng.uniform(0,40,(9,8))
    flat=np.r_[rng.normal(scale=.03,size=28),np.log(np.arange(8)*100+50)]
    value,g=objective(flat,x,own,counts,env,True)
    numerical=approx_derivative(lambda p:objective(p,x,own,counts,env,True)[0],flat,method='3-point').ravel()
    assert np.isfinite(value) and np.allclose(g,numerical,rtol=1e-5,atol=1e-8)
    result=predict(flat[:28].reshape(4,7),np.exp(flat[28:]),x,own,env)
    assert np.allclose(result['probabilities'].sum(1),1)
    assert np.allclose(result['probabilities'][0],result['prior'][0])


def test_transport_preserves_each_source_exposure_and_missing_history():
    history=np.zeros((2,3,8));history[0,0]=np.arange(8);history[0,1]=np.arange(8)*2
    old=np.full((2,3,8),1/8);new=np.tile(np.arange(1,9)/36,(2,1))
    pooled=transported_counts(history,old,new)
    assert np.allclose(pooled.sum(1),[28+.8*56,0])
    assert np.allclose(pooled[1],0)
