from datetime import date
from pathlib import Path
import sys
import polars as pl
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_hitter_statcast_next_year import materialize,METRICS


def annual():
    return pl.DataFrame([dict(player_id=7,season=y,measured_ev_contacts=4,measured_la_contacts=4,
        measured_pair_contacts=4,pair_coverage=1.,last_date=date(y,9,1),**{m:100. if 'ev' in m else .3 for m in METRICS})
        for y in [2015,2016]])


def test_own_origin_ignores_future_tracking_and_future_labels():
    f=pl.DataFrame([dict(row_id=1,player_id=7,origin_year=2015,next_pa=99)])
    a=annual(); q,c,m=materialize(f,a)
    changed=a.with_columns(pl.when(pl.col('season')==2016).then(125.).otherwise(pl.col('mean_ev')).alias('mean_ev'))
    z,_,_=materialize(f.with_columns(pl.lit(0).alias('next_pa')),changed)
    assert q.select(c+m).equals(z.select(c+m)) and q['sc_own_ev_n'].item()==4
    assert len(c+m)==len(set(c+m)) and set(c+m)<=set(q.columns)


def test_untracked_unknown_history_not_observed_mean():
    f=pl.DataFrame([dict(row_id=1,player_id=8,origin_year=2015)])
    q,c,m=materialize(f,annual())
    assert not q['sc_tracked'].item() and q['sc_0_ev95_known'].item()==0.
    assert q['sc_0_ev95'].item()==0. and q['sc_1_source_year_available'].item()==0.
    assert q['sc_0_source_year_available'].item()==1.


def test_tracking_does_not_change_original_fields():
    f=pl.DataFrame([dict(row_id=1,player_id=7,origin_year=2016,next_pa=99)])
    q,_,_=materialize(f,annual())
    assert q.select(f.columns).equals(f) and q['sc_own_ev_n'].item()==8
