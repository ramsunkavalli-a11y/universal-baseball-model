import polars as pl
import pytest
from universal_baseball.hitter_followup import annual_followup, support_membership


def inputs():
    origins=pl.DataFrame(dict(row_id=[0,1,2],player_id=[10,20,30],origin_year=[2017,2024,2016],outer_fold=[0,1,2]))
    targets=pl.DataFrame([dict(season=y,player_id=10,mlb_pa=100,component_war=2.,league_pa=180000,schedule_fraction=.37 if y==2020 else 1.) for y in range(2009,2026)])
    return origins,targets


def test_censoring_not_zero_and_inactive_rate_not_zero():
    f,t=inputs();a=annual_followup(f,t,list(range(2009,2026)))
    assert a.filter((pl.col('row_id')==1)&(pl.col('followup_year')==1))['mlb_pa'][0]==0
    assert a.filter((pl.col('row_id')==1)&(pl.col('followup_year')==1))['batting_rate'][0] is None
    later=a.filter((pl.col('row_id')==1)&(pl.col('followup_year')>1))
    assert later['mlb_pa'].null_count()==5 and later['component_value'].null_count()==5
    assert not later['observed'].any()
    assert not a.filter(pl.col('season')==2020)['rate_training_eligible'].any()


def test_cutoff_player_separation_and_window_maturity():
    f,t=inputs();a=annual_followup(f,t,list(range(2009,2026)))
    tr=support_membership(a,2019,2,3)
    assert tr['season'].max()<=2019 and 30 not in tr['player_id'] and 2020 not in tr['season']
    # 2017 has some completed annual evidence but no completed 3-year window.
    assert 10 in tr['player_id']
    assert 10 not in support_membership(a,2019,2,3,cumulative=True)['player_id']
    changed=t.with_columns(pl.when(pl.col('season')>2019).then(999999).otherwise(pl.col('mlb_pa')).alias('mlb_pa'))
    assert tr.equals(support_membership(annual_followup(f,changed,list(range(2009,2026))),2019,2,3))


def test_incomplete_and_protected_inventory_rejected():
    f,t=inputs()
    with pytest.raises(ValueError): annual_followup(f,t,list(range(2009,2025)))
    with pytest.raises(ValueError): annual_followup(f,t.with_columns(pl.lit(2026).alias('season')),list(range(2009,2026)))
