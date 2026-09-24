import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_arrival_value_transfer import training,annual_labels,propagate


def test_annual_not_cumulative():
    f=pl.DataFrame({'pa_h1':[20,0], 'pa_h2':[0,30], 'pa_h3':[0,0]})
    assert annual_labels(f,2).tolist()==[0,1]
    assert annual_labels(f,3).tolist()==[0,0]


def test_maturity_and_cancellation():
    f=pl.DataFrame({'origin_year':[2015,2016,2017,2019,2021], 'player_id':[1,1,2,3,4], 'pa_h3':[1.,2.,3.,4.,None]})
    t=training(f,2022,3)
    assert t['origin_year'].to_list()==[2015,2016]
    assert t['identity_weight'].to_list()==[.5,.5]
    with pytest.raises(ValueError):training(f,2024,3)


def test_zero_not_missing():
    assert annual_labels(pl.DataFrame({'pa_h1':[0,10]}),1).tolist()==[0,1]
    with pytest.raises(ValueError):annual_labels(pl.DataFrame({'pa_h1':[None,10]}),1)


def test_delta_not_division_of_direct_value():
    f=pl.DataFrame({'B_p':[.1,.5], 'B_pa':[20.,200.], 'B_value':[.8,1.5], 'rate':[3.,-1.]})
    p,pa,v=propagate(f,[.2,.9],[True,False])
    np.testing.assert_allclose(pa,[40.,200.]);np.testing.assert_allclose(v,[.9,1.5])
    np.testing.assert_allclose(p,[.2,.5])
    _,same_pa,same_v=propagate(f,f['B_p'],[True,True])
    np.testing.assert_array_equal(same_pa,f['B_pa']);np.testing.assert_array_equal(same_v,f['B_value'])


def test_invalid_hurdle():
    f=pl.DataFrame({'B_p':[0.], 'B_pa':[2.], 'B_value':[.2], 'rate':[1.]})
    with pytest.raises(ValueError):propagate(f,[.1],[True])
