import numpy as np
from universal_baseball.hitter_workload_risk import mixture_pmf, distribution_terms, fit_concentration


def test_exact_zero_mass_and_fixed_means_including_boundaries():
    p=np.array([0,.05,.95,1,1]); c=np.array([200,100,600,1,800])
    for k in [None,.1,1,1000]:
        pmf=mixture_pmf(p,c,k)
        assert np.array_equal(pmf[:,0],1-p)
        assert np.allclose(pmf@np.arange(801),p*c,atol=1e-6)
        assert pmf[3,1]==1 and pmf[4,800]==1


def test_zero_quantiles_are_not_zero_expected_value():
    pmf=mixture_pmf(np.array([.05]),np.array([200]),2)
    s=distribution_terms(pmf,np.array([0]))
    assert s['q10'][0]==s['q50'][0]==s['q90'][0]==0
    assert pmf@np.arange(801)>0
    assert s['crps'][0]>0  # full distribution still contains a positive tail


def test_crps_matches_pairwise_definition():
    pmf=mixture_pmf(np.array([.8]),np.array([25]),3)
    terms=distribution_terms(pmf,np.array([50]))
    x=np.arange(801); w=pmf[0]
    exact=np.sum(w*np.abs(x-50))-.5*np.sum(w[:,None]*w[None,:]*np.abs(x[:,None]-x[None,:]))
    assert np.isclose(terms['crps'][0],exact,atol=1e-10)


def test_concentration_is_bounded_and_boundary_failures_retained():
    y=np.array([1,100,700,800]); c=np.array([1,350,350,799.])
    f=fit_concentration(y,c,np.ones(4))
    assert .1<=f['concentration']<=1000 and f['optimizer_success']
    assert f['boundary_means']==1
