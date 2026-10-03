import polars as pl
import pytest
from universal_baseball.prospect_graduation import overlay


def frames():
    f=pl.DataFrame(dict(row_id=[1,2,3],player_id=[11,11,12],origin_year=[2018,2019,2018],
        scout_listed_0=[0.,-1.,0.],scout_listed_1=[1.,1.,-1.],scout_listed_2=[1.,1.,0.],
        scout_rank_score_1=[.5,.9,-1.],scout_rank_score_2=[.8,.5,0.]))
    s=pl.DataFrame(dict(player_id=[11,11,12],season=[2018,2019,2018],sport_id=[1,1,1],
        at_bats=[130,1,131],plate_appearances=[140,1,150]))
    return f,s


def test_threshold_cutoff_and_unknown():
    f,s=frames();r=overlay(f,s)
    assert r['scout_ab_graduated'].to_list()==[0,1,1]
    assert r['scout_graduated_absent'].to_list()==[0,-1,1]
    assert r['scout_graduated_prior_score'].to_list()==[0.,-1.,-1.]
    assert r['observed_mlb_ab_lower_bound'].to_list()==[130,131,131]
    s=s.with_columns(pl.when(pl.col('season')==2019).then(700).otherwise(pl.col('at_bats')).alias('at_bats'),
        pl.when(pl.col('season')==2019).then(700).otherwise(pl.col('plate_appearances')).alias('plate_appearances'))
    assert overlay(f,s).row(0)==r.row(0)


def test_most_recent_not_peak():
    f,s=frames();s=s.with_columns(pl.lit(131).alias('at_bats'),pl.lit(150).alias('plate_appearances'))
    assert overlay(f,s)['scout_graduated_prior_score'][0]==.5


def test_duplicate_rejected():
    f,s=frames()
    with pytest.raises(ValueError,match='Duplicate'):overlay(f,pl.concat([s,s.head(1)]))


def test_missing_ab_rejected():
    f,s=frames();s=s.with_columns(pl.lit(None,dtype=pl.Int64).alias('at_bats'))
    with pytest.raises(ValueError,match='missing'):overlay(f,s)
