import polars as pl
import numpy as np
import pytest
from universal_baseball.hitter_shared_development import representation, preflight_shared,HORIZON_FEATURES


def test_horizon_one_is_not_later_arrival_and_origin_age_preserved():
    f=pl.DataFrame(dict(dominant_level=['DSL','AAA','MLB'],age_centered=[-2.2,-.8,1.],horizon=[1,3,6]))
    q=representation(f)
    assert q['age_centered'].equals(f['age_centered'])
    assert (q.head(1).select(HORIZON_FEATURES).to_numpy()==0).all()
    assert q['development_age_DSL'][0]==-2.2
    assert q['development_horizon_3_AAA'][1]==1
    assert q['development_horizon_age_6'][2]==1


def test_mixed_gate_checks_completion_and_whole_players():
    a=pl.DataFrame(dict(row_id=[0,0],player_id=[10,10],origin_year=[2015,2015],horizon=[1,3],target_year=[2016,2018],
        outer_fold=[0,0],next_pa=[100,200],next_batting_rate=[1.,2.],feature=[.2,.2]))
    b=pl.DataFrame(dict(row_id=[1],player_id=[20],origin_year=[2018],horizon=[1],target_year=[2019],outer_fold=[1],feature=[.3]))
    assert preflight_shared(a,b,2018,1,['feature'],[1])['integrity_pass']
    with pytest.raises(ValueError): preflight_shared(a,b,2017,1,['feature'],[1])
    with pytest.raises(ValueError): preflight_shared(a,b.with_columns(pl.lit(10).alias('player_id')),2018,1,['feature'],[1])
