from datetime import date
import polars as pl
import pytest
from universal_baseball.hitter_arrival_source_repair import census_rows, corrected_cohorts, attach_roster, attach_leagues, FEATURES


def panel():
    return pl.DataFrame({'origin_year':[2017,2017,2021], 'player_id':[1,2,3],
                         'stage':['Upper minors']*3,'on_40man':[0,1,0]})


def test_debut_cutoff_not_eventual_debut():
    d=pl.DataFrame({'player_id':[1,2], 'mlb_debut_date':[date(1995,9,3),date(2018,5,1)]})
    f=corrected_cohorts(panel(),d)
    assert f['prior_debut'].to_list()==[True,False,False]
    assert f['prospect'].to_list()==[False,True,True]
    assert f['minor_returner'].to_list()==[True,False,False]


def test_census_future_rejected():
    with pytest.raises(ValueError): census_rows({'people':[{'id':1,'mlbDebutDate':'2026-01-01'}]},2025)
    with pytest.raises(ValueError): census_rows({'people':[]},2025)
    with pytest.raises(ValueError): census_rows({},2026)
    with pytest.raises(KeyError): census_rows({'people':[{'id':1}]},2025)


def test_roster_exact_date_and_removals():
    r=pl.DataFrame({'season':[2017,2021],'player_id':[1,3], 'as_of_date':[date(2017,12,31),date(2021,12,31)]})
    assert attach_roster(panel(),r)['on_40man'].to_list()==[1,0,1]
    with pytest.raises(ValueError): attach_roster(panel(),r.with_columns(pl.lit(date(2021,10,15)).alias('as_of_date')))
    with pytest.raises(ValueError): attach_roster(panel(),r.filter(pl.col('season')==2017))


def test_league_calendar_lags_and_missing():
    a=pl.DataFrame({'season':[2016,2017,2018,2019], 'player_id':[1,1,1,3],
                    'mexican_pa_share':[.3,.5,.9,1.], 'known_pa_share':[1.,1.,1.,1.]})
    f=attach_leagues(panel(),a)
    assert f[FEATURES[0]].to_list()==[.5,None,None]
    assert f[FEATURES[2]].to_list()==[.3,None,None]
    assert f[FEATURES[4]].to_list()==[None,None,1.]
    assert f[FEATURES[1]].to_list()==[1.,0.,0.]
