import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_canceled_season import available_columns, outage_mask, hide_annual_block


def test_removes_whole_annual_block_and_only_dependent_changes():
    columns = ['age','missing_lag1','log_pa_lag1','share_AA_lag1','ubb_rate_lag1',
               'raw1__available','pitch1__pa_count','context1__foo','park1__foo',
               'missing_lag2','raw2__foo','change__ubb_rate','path0__available','ubb_rate_lag0']
    assert available_columns(columns,[1]) == ['age','missing_lag2','raw2__foo','path0__available','ubb_rate_lag0']
    assert 'change__ubb_rate' in available_columns(columns,[2])
    assert available_columns(columns,[1,2]) == ['age','path0__available','ubb_rate_lag0']
    with pytest.raises(ValueError): available_columns(columns,[0])


def test_only_system_outage_and_never_debuted_minors():
    f = pl.DataFrame({'prospect':[True,False,True], 'missing_lag1':[1,1,0], 'missing_lag2':[0,1,1]})
    assert outage_mask(f,2021).tolist() == [True,False,False]
    assert outage_mask(f,2022).tolist() == [False,False,True]
    assert not outage_mask(f,2023).any()


def test_hidden_query_no_fake_performance_or_damage_to_other_players():
    f = pl.DataFrame({'prospect':[True,False],'missing_lag1':[0,0],'log_pa_lag1':[6.,5.],
                      'share_AA_lag1':[1.,1.],'ubb_rate_lag1':[.1,.2], 'raw1__available':[1,1],
                      'raw1__contact_events':[400.,200.], 'mlb_value_history_available_lag1':[1,1],
                      'change__ubb_rate':[.03,.04],'ubb_rate_lag0':[.13,.24],
                      'path0__level_path__primary_level_change':[1.,1.]})
    q = hide_annual_block(f,1)
    assert q.tail(1).equals(f.tail(1))
    assert q['missing_lag1'][0] == 1 and q['log_pa_lag1'][0] == 0
    assert q['share_AA_lag1'][0] == 0 and q['raw1__available'][0] == 0
    assert q['ubb_rate_lag1'][0] is None and q['change__ubb_rate'][0] is None
    assert q['raw1__contact_events'][0] is None and q['mlb_value_history_available_lag1'][0] == 1
    retained = available_columns(f.columns,[1])
    assert q.select(retained).equals(f.select(retained))
