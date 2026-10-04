import numpy as np
from universal_baseball.hitter_error_budget import components,summary


def test_nonarrivals_have_no_observed_production_or_active_workload():
    pa,value=components([.1,.9],[200,500],[0,400],[.01,.01],[np.nan,.02])
    assert np.array_equal(pa[0],[20,0]) and np.array_equal(value[0],[.2,0,0])
    assert np.isclose(value[1].sum(),4.5-8)


def test_offsetting_components_do_not_disappear():
    s=summary(np.array([[100.,-90.]]),[2024],['arrival','workload'])
    assert s['mse']==100 and s['mean_cancellation']==180
    assert s['components']['arrival']['mse_allocation']==1000
    assert s['components']['workload']['mse_allocation']==-900
    assert s['mae']==10


def test_error_matrix_and_mae_identity_equal_year_not_pooled():
    x=np.array([[1.,2.,-1.],[0.,0.,0.],[3.,-2.,5.]])
    s=summary(x,[2022,2022,2023],['arrival','workload','production'])
    assert s['mse']==19 and s['mae']==3.5
    assert np.isclose(sum(v['mse_allocation'] for v in s['components'].values()),19)


def test_realized_zero_rate_not_assumed_for_nonarrival():
    a=components([.2],[300],[0],[.01],[np.nan])
    b=components([.2],[300],[0],[.01],[999])
    assert all(np.array_equal(x,y) for x,y in zip(a,b))


def test_random_accounting_with_signed_yields_and_zero_activity():
    rng=np.random.default_rng(104); n=1000
    p=rng.uniform(0,1,n); c=rng.uniform(1,800,n); y=rng.integers(0,800,n); y[:500]=0
    g=rng.normal(.003,.002,n); t=rng.normal(.003,.005,n); t[y==0]=np.nan
    pa,value=components(p,c,y,g,t)
    assert np.allclose(pa.sum(1),p*c-y)
    assert np.allclose(value.sum(1),p*c*g-np.where(y>0,y*np.nan_to_num(t),0))
