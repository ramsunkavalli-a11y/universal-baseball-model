import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_arrival_coherence import age_band, cell_probability, eligible, linked_value


def test_age_boundaries_and_missing():
    assert [age_band(x) for x in [None,18,19,20,21,22,23]]==['unknown','<=18','19-20','19-20','21-22','21-22','23+']


def test_rare_rookies_do_not_borrow_aaa_arrival_rate():
    train=pl.DataFrame({'level':['RK']*1000+['AAA']*100,'age':[18.]*1100,'prospect':[True]*1100,'pa_h2':[0]*1000+[200]*100})
    test=pl.DataFrame({'level':['RK','AAA','UNKNOWN'],'age':[18.,18.,18.],'prospect':[True]*3})
    prob,support,_=cell_probability(train,test,2)
    assert 0<prob[0]<.001 and prob[1]>.99
    assert support.tolist()==[True,True,False] and np.isnan(prob[2])


def test_returners_and_unknown_age_not_eligible():
    f=pl.DataFrame({'level':['RK']*3,'age':[18.,18.,None],'prospect':[True,False,True]})
    assert eligible(f).tolist()==[True,False,False]


def test_accounting_uses_same_pa_and_preserves_negative_talent():
    pa,value=linked_value([0,.1,1],[400,300,600],[3,2,-1])
    np.testing.assert_allclose(pa,[0,30,600]); np.testing.assert_allclose(value,[0,.1,-1])
    with pytest.raises(ValueError): linked_value([1.1],[200],[1])


def test_null_labels_rejected():
    f=pl.DataFrame({'level':['RK'],'age':[18.],'prospect':[True],'pa_h2':[None]})
    with pytest.raises(ValueError): cell_probability(f,f,2)
