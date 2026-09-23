import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_detail_arrival import join_lags,eligible,target_values,fit_probability


def panel():
    return pl.DataFrame({'origin_year':[2015,2016,2017,2019,2021,2022],
        'player_id':[1,1,2,3,4,5],'pa_h1':[0.,100.,10.,0.,500.,None],
        'pa_h2':[0.,0.,450.,500.,500.,None],'pa_h3':[0.,600.,450.,500.,0.,None]})


def test_whole_maturity_and_pandemic_exclusion():
    f=eligible(panel(),2021,'arrival_three')
    assert f['origin_year'].to_list()==[2015,2016]
    assert f['identity_weight'].to_list()==[.5,.5]
    assert eligible(panel(),2021,'arrival_three',[1]).is_empty()
    with pytest.raises(ValueError):eligible(panel(),2024,'arrival_three')


def test_targets_keep_nonarrivals_and_differ_from_sustained_workload():
    f=panel().head(5)
    assert target_values(f,'arrival_three').tolist()==[0,1,1,1,1]
    assert target_values(f,'regular_three').tolist()==[0,0,1,1,1]
    with pytest.raises(ValueError):target_values(panel(),'arrival_three')


def test_calendar_lags_not_previous_available_season():
    p=pl.DataFrame({'origin_year':[2021],'player_id':[1]})
    a=pl.DataFrame({'season':[2019,2021,2022],'player_id':[1]*3,'rate':[.1,.2,.9]})
    f,c=join_lags(p,a,['rate'],'x')
    assert f['x0__rate'][0]==.2 and f['x1__rate'][0] is None and f['x2__rate'][0]==.1
    assert f['x1__available'][0]==0
    with pytest.raises(ValueError):join_lags(p,pl.concat([a,a.head(1)]),['rate'],'x')


def test_future_mutation_does_not_change_training_rows():
    p=panel();q=p.with_columns(pl.when(pl.col('origin_year')+3>2021).then(9999.).otherwise(pl.col('pa_h3')).alias('pa_h3'))
    assert eligible(p,2021,'regular_three').equals(eligible(q,2021,'regular_three'))


def test_feature_leak_rejected():
    with pytest.raises(ValueError):fit_probability(panel(),panel(),['pa_h1'],'next_year')
