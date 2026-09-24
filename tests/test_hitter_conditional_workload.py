import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_conditional_workload import roles,role_means,mixture_mean,active_training,paired_interval


def test_role_boundaries():
    assert roles([1,99,100,449,450,790]).tolist()==[0,0,1,1,2,2]
    with pytest.raises(ValueError):roles([0,100])
    with pytest.raises(ValueError):roles([np.nan])


def test_past_weighted_means():
    np.testing.assert_allclose(role_means([10,90,200,600],[3,1,1,1]),[30,200,600])
    with pytest.raises(ValueError):role_means([10,200],[1,1])


def test_probability_mixture():
    np.testing.assert_allclose(mixture_mean([[.5,.25,.25],[0,0,1]],[30,200,600]),[215,600])
    with pytest.raises(ValueError):mixture_mean([[.2,.2,.2]],[30,200,600])


def test_active_identity_weights_and_maturity():
    p=pl.DataFrame({'origin_year':[2014,2015,2016,2017,2021],'player_id':[1,1,1,2,3], 'pa_h3':[0.,100.,200.,50.,None]})
    f=active_training(p,2022,3)
    assert f['origin_year'].to_list()==[2015,2016]
    assert f['identity_weight'].to_list()==[.5,.5]


def test_paired_identical():
    p=pl.DataFrame({'origin_year':[2016,2021,2022],'player_id':[1,1,2], 'actual_pa':[0.,200.,300.], 'a':[10.,100.,200.]})
    r=paired_interval(p,'a','a',draws=50)
    assert r['delta']==0 and r['interval975']==[0.,0.]
