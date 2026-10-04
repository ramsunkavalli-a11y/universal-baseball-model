import numpy as np
import polars as pl
from universal_baseball.hitter_minor_precision import variance_components, information_share, bootstrap_best_half, references
from universal_baseball.post_arrival_history import player_fold


def test_components_match_balanced_anova():
    r=variance_components([1,3],[10,10],[9,9])
    assert r['within_variance']==1
    assert np.isclose(r['between_variance'],1.9)
    assert np.isclose(r['prior_contacts'],1/1.9)
    assert variance_components([1,1],[10,10],[9,9])['prior_contacts'] is None


def test_sample_and_mlb_information_have_required_direction():
    assert information_share(6,6,1988,30)<.003
    assert information_share(200,200,0,30)>information_share(6,6,0,30)
    assert information_share(20,20,1600,30)<information_share(20,20,0,30)
    assert information_share(0,0,0,None)==0


def test_bootstrap_reproducible_and_not_zero_noise_for_constant_mean_mix():
    assert bootstrap_best_half([80,90,100,110],12)==bootstrap_best_half([80,90,100,110],12)
    assert bootstrap_best_half([80,90,100,110],12)>0
    assert bootstrap_best_half([95],12) is None


def test_reference_whole_player_and_season_exclusion():
    rows=[]
    for pid in range(10,30):
        rows.append(dict(player_id=pid,season=2022,league_id=117,ev_n=30,la_n=30,pair_n=30,
            ev_ss=900.,la_ss=900.,pair_ss=6.,mean_ev=80.+pid,best_half_ev=90.+pid,
            mean_la=10.+pid,hard_air_fraction=pid/100,bootstrap_best_half_variance=1.))
    a=pl.DataFrame(rows);before=references(a,0)
    altered=a.with_columns(pl.when(pl.col('player_id').map_elements(player_fold,return_dtype=pl.Int64)==0)
        .then(9999.).otherwise(pl.col('mean_ev')).alias('mean_ev'))
    assert references(altered,0)==before
    later=a.with_columns(pl.lit(2023).cast(a.schema['season']).alias('season'),pl.lit(9999.).alias('mean_ev'))
    assert [r for r in references(pl.concat([altered,later]),0) if r['season']==2022]==before
