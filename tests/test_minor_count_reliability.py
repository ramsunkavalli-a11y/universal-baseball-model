import numpy as np
import pytest
from scipy.stats import betabinom, nbinom

from universal_baseball.minor_count_reliability import (fit_prior,marginal_log_mass,posterior,predictive,validate_counts)


@pytest.mark.parametrize('mean',[.001,.05,.5,.95])
def test_one_trial_cannot_identify_concentration(mean):
    for k in [.001,1.,100.,1e6]:
        mass=np.exp(marginal_log_mass([0,1],[1,1],mean,k,True))
        np.testing.assert_allclose(mass,[1-mean,mean],atol=1e-9,rtol=1e-8)


def test_one_trial_group_has_explicit_limitation():
    r=fit_prior([0,1,0],[1,1,1],True,dict(mean=.3,strength=5.))
    assert r['strength'] is None and r['status']=='one_trial_concentration_unidentified'


@pytest.mark.parametrize('x,n,binomial',[([2],[1],True),([1],[0],False),([.1],[10],True),([1],[None],True),([-1],[2],False)])
def test_invalid_counts_stop(x,n,binomial):
    with pytest.raises(ValueError):validate_counts(x,n,binomial)


def test_beta_mass_normalization_and_scipy_agreement():
    xs=np.arange(21);mass=np.exp(marginal_log_mass(xs,np.full(21,20),.1,17.,True))
    assert abs(sum(mass)-1)<1e-12
    np.testing.assert_allclose(mass,betabinom.pmf(xs,20,1.7,15.3),rtol=1e-12)


def test_gamma_poisson_mass_and_scipy_agreement():
    xs=np.arange(1000);mass=np.exp(marginal_log_mass(xs,np.full(1000,50),.2,40.,False))
    assert abs(sum(mass)-1)<1e-12
    np.testing.assert_allclose(mass,nbinom.pmf(xs,8.,40/90),rtol=1e-10,atol=1e-15)


@pytest.mark.parametrize('binomial',[True,False])
def test_zero_exposure_is_uninformative(binomial):
    prior=dict(mean=.1,strength=20.)
    post=posterior(0,0,prior,binomial)
    assert post['mean']==.1 and post['strength']==20. and post['weight']==0
    assert predictive(0,0,post,binomial)['loss']==0


def test_small_sample_weight_is_not_a_separate_unused_feature():
    prior=dict(mean=.05,strength=100.)
    post=posterior(0,6,prior,True)
    assert post['weight']==6/106
    assert post['mean']==5/106
    assert posterior(0,60,prior,True)['weight']>post['weight']


def test_point_prior_and_impossible_outcome_are_not_floored():
    post=posterior(0,6,dict(mean=0.,strength=None),True)
    r=predictive(1,20,post,True)
    assert r['impossible'] and r['loss'] is None
    assert predictive(0,20,post,True)['loss']==0


def test_all_zero_sources_keep_honest_zero_point():
    r=fit_prior([0,0],[10,100],True,dict(mean=.1,strength=10.))
    assert r['mean']==0 and r['strength'] is None


def test_reference_fit_accepts_no_future_outcome():
    x=np.array([0,1,0,2,0,1]);n=np.array([20,40,10,30,10,100])
    a=fit_prior(x,n,True,dict(mean=.02,strength=None))
    b=fit_prior(x.copy(),n.copy(),True,dict(mean=.02,strength=None))
    assert a==b


def test_future_counts_do_not_change_current_source_population(monkeypatch):
    monkeypatch.syspath_prepend('scripts')
    from run_minor_count_reliability_v20 import source_rows
    def row(year,errors):
        fields=dict(putOuts=9-errors,assists=0,errors=errors,chances=9,throwingErrors=0)
        return dict(season=year,player_id=11,player_name='Example',position_code='9',normalized_level='A',
                    fielding_outs=30,chances_identity=True,throwing_subset_identity=True,**fields,
                    **{k+'_status':'recorded' for k in fields})
    origin=dict(origin_year=2022,player_id=11,position=9,minor_outs=30,age=20.,age_band='20-22',prior_current_MLB_fielding=False)
    a,_=source_rows([row(2022,1),row(2023,0)],[origin])
    b,_=source_rows([row(2022,1),row(2023,8)],[origin])
    assert a==b and len(a)==1
