import pytest
import polars as pl
from universal_baseball.hitter_schedule_opportunity import (
    completed_teams, schedule_features, attach_schedule, restrict_training, FEATURES)


def game(pk=1, state='F', kind='R', home=10):
    return {'gamePk':pk, 'gameType':kind, 'season':'2021', 'status':{'codedGameState':state},
            'teams':{'home':{'team':{'id':home}}, 'away':{'team':{'id':20}}}}


def test_dedup_and_canceled_postseason_exclusion():
    q={'dates':[{'games':[game(),game(),game(2,'C'),game(3,kind='P')]}]}
    r=completed_teams(q,2021,11)
    assert [v['team_games'] for v in r] == [1,1]
    reverse=game();reverse['teams']['home']['team']['id']=20;reverse['teams']['away']['team']['id']=10
    assert completed_teams({'dates':[{'games':[game(),reverse]}]},2021,11)==r
    with pytest.raises(ValueError): completed_teams(q,2026,11)
    with pytest.raises(ValueError): completed_teams(q,2022,11)
    with pytest.raises(ValueError): completed_teams({'dates':[{'games':[game(),game(home=30)]}]},2021,11)
    g=game();g['season']='2021.1'
    assert len(completed_teams({'dates':[{'games':[g]}]},2021,11))==2
    g['officialDate']='2022-01-01'
    with pytest.raises(ValueError):completed_teams({'dates':[{'games':[g]}]},2021,11)


def sample():
    stats=pl.DataFrame({'season':[2021]*5,'sport_id':[11,12,11,11,1],
        'team_id':[10,10,99,10,1], 'player_id':[1,1,2,2,3], 'plate_appearances':[120,140,20,120,600]})
    teams=pl.DataFrame({'season':[2021]*2,'sport_id':[11,12],'team_id':[10,10],'team_games':[120,140]})
    return stats,teams


def test_multilevel_denominators_not_roster_time():
    f=schedule_features(*sample()).sort('player_id')
    assert f[FEATURES[1]].to_list()==[2.,None]
    assert f[FEATURES[2]].to_list()==[130.,None]
    assert f[FEATURES[0]].to_list()==[1.,120/140]
    assert f.height==2  # MLB PA never used in minor denominator


def test_duplicates_fail_closed():
    s,t=sample()
    with pytest.raises(ValueError): schedule_features(pl.concat([s,s.head(1)]),t)
    with pytest.raises(ValueError): schedule_features(s,pl.concat([t,t.head(1)]))


def test_future_sources_cannot_change_earlier_row():
    s,t=sample(); f=schedule_features(s,t)
    panel=pl.DataFrame({'origin_year':[2021,2022], 'player_id':[1,1]})
    future=f.with_columns(pl.lit(2022,dtype=pl.Int64).alias('season'),pl.lit(999.).alias(FEATURES[1]))
    a=attach_schedule(panel,f); b=attach_schedule(panel,pl.concat([f,future]))
    assert a.head(1).equals(b.head(1))
    assert b[FEATURES[1]].to_list()==[2.,999.]


def test_weights_recomputed_after_history_restriction():
    p=pl.DataFrame({'origin_year':[2014,2015,2016,2016], 'player_id':[1,1,1,2], 'identity_weight':[1/3,1/3,1/3,1.]})
    f=restrict_training(p)
    assert f['identity_weight'].to_list()==[.5,.5,1.]
