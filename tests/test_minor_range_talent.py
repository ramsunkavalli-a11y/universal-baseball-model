import numpy as np
import pytest

from universal_baseball.minor_range_talent import (moments,posterior_deviation,ReferenceEngine,person_weights,design,
    ridge_fit,ridge_predict,preflight,BASE_NAMES)


def test_no_variation_means_no_reliability_not_perfect_certainty():
    q=moments(.1,.01,1/100,50,True)
    assert q['strength'] is None and posterior_deviation(0,10,q)['reliability']==0


def test_beta_moment_and_opportunity_denominator():
    q=moments(.1,.03,1/100,100,True)
    assert q['between_variance']>0 and q['strength']>0
    a=posterior_deviation(1,10,q,True);b=posterior_deviation(10,100,q,True)
    assert a['reliability']<b['reliability'] and a['deviation']==pytest.approx(0)


def test_poisson_prior_and_favorable_plays():
    q=moments(.3,.12,1/100,50,False)
    a=posterior_deviation(40,100,q)
    assert a['deviation']>0 and 0<a['reliability']<1


def test_no_chances_remains_no_signal():
    q=moments(.1,.03,.01,100,True)
    assert posterior_deviation(0,0,q)['raw_rate'] is None
    assert posterior_deviation(0,0,q)['deviation']==0


def source(pid,year=2019,errors=2):
    return dict(player_id=pid,origin_year=year,position=6,level='A',age=20,outs=600,
                errors=errors,throwingErrors=1,chances=100,putOuts=30,assists=68)


def test_reference_excludes_future_held_and_own_people():
    rs=[source(i,2019) for i in range(1,101)]+[source(1234,2020,80),source(1200,2019,80)]
    e=ReferenceEngine(rs);r=source(1)
    q=e.prior(r,0,(0,))
    assert q['people']==79 and q['mean']==pytest.approx(.01)
    assert q['reference_years']==[2019]


def test_no_manufactured_2020_reference():
    e=ReferenceEngine([source(i,2019) for i in range(1,101)]+[source(i,2021) for i in range(1,101)])
    q=e.prior(source(1,2021),0,(0,))
    assert q['reference_years']==[2019,2021]


def test_person_weights_do_not_count_duplicate_years_as_people():
    rows=[{'player_id':1},{'player_id':1},{'player_id':2}]
    assert person_weights(rows).tolist()==[.5,.5,1]


def test_first_base_does_not_get_infield_or_outfield_plays():
    rs=[{**source(i),'position':3} for i in range(1,101)]
    s,t=ReferenceEngine(rs).features([rs[0]],(0,))
    assert s[2]==s[3]==0 and len(t[0]['signals'])==2


def test_future_quality_does_not_enter_design():
    r=dict(age=20,minor_outs=600,position=6,level='A',quality_rate=2.)
    a=design([r],[np.zeros(4)],22,True)
    r['quality_rate']=-100
    assert np.array_equal(a,design([r],[np.zeros(4)],22,True))


def test_ridge_intercept_and_finite_prediction():
    x=np.zeros((5,len(BASE_NAMES)));y=np.ones(5)*2
    fit=ridge_fit(x,y,np.ones(5),100,BASE_NAMES)
    assert np.allclose(ridge_predict(fit,x),2)


def test_empty_early_training_keeps_fixed_design_width():
    assert design([],[],23,True).shape==(0,len(BASE_NAMES)+4)
    assert design([],[],23,False).shape==(0,len(BASE_NAMES))


def test_chronology_or_overlap_stops_fit():
    r=dict(player_id=1,origin_year=2017,position=6,level='A',age_band='20-22',sample_band='1500+',window_end=2020,quality_rate=1.)
    t={**r,'origin_year':2019,'player_id':2};x=np.ones((1,4))
    with pytest.raises(ValueError,match='Immature'):preflight([r],[t],2019,(2,),x,x)
    r['window_end']=2019;t['player_id']=1
    with pytest.raises(ValueError,match='overlap'):preflight([r],[t],2019,(2,),x,x)


def test_future_test_quality_does_not_change_support():
    r=dict(player_id=1,origin_year=2017,position=6,level='A',age_band='20-22',sample_band='1500+',window_end=2020,quality_rate=1.)
    t={**r,'origin_year':2020,'player_id':2};x=np.ones((1,4))
    a=preflight([r],[t],2020,(2,),x,x)
    t['quality_rate']=None
    assert preflight([r],[t],2020,(2,),x,x)==a
