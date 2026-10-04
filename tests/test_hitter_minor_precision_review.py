import numpy as np
import polars as pl
from universal_baseball.hitter_minor_precision import materialize,names


def annual():
    return pl.DataFrame([dict(player_id=i,season=2022,league_id=117,ev_n=30,la_n=30,pair_n=30,
        ev_ss=900.,la_ss=900.,pair_ss=6.,mean_ev=70.+i,best_half_ev=80.+i,mean_la=float(i),
        hard_air_fraction=i/100,bootstrap_best_half_variance=1.) for i in range(10,30)])


def features(pid):
    return pl.DataFrame([dict(row_id=1,player_id=pid,origin_year=2022,sc_own_ev_n=100,
        sc_own_pair_n=100,sc_0_la_sample=np.log1p(100)/np.log(601),sc_1_la_sample=0.,
        sc_2_la_sample=0.,next_pa=100,next_value=1.)])


def test_future_targets_do_not_change_precision_features():
    f=features(11);a=annual();q,_=materialize(f,a,0)
    mutated=f.with_columns(pl.lit(0).alias('next_pa'),pl.lit(-999.).alias('next_value'))
    got,_=materialize(mutated,a,0);cols=sum(names(),[])
    assert q.select(cols).equals(got.select(cols))
    later=a.with_columns(pl.lit(2023).cast(a.schema['season']).alias('season'),pl.lit(9999.).alias('mean_ev'))
    got,_=materialize(f,pl.concat([a,later]),0)
    assert q.select(cols).equals(got.select(cols))


def test_untracked_player_cannot_receive_an_adjustment():
    q,_=materialize(features(9999),annual(),0)
    assert not q.select(sum(names(),[])).to_numpy().any()
