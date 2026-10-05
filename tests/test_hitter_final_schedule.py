import pytest
from universal_baseball.hitter_final_schedule import completed_schedule


def game(code,state,day='2026-04-03',away=1):
    return dict(gamePk=10,gameType='R',officialDate=day,status=dict(codedGameState=code,abstractGameState='Final',detailedState=state),
        teams={'away':{'team':{'id':away}},'home':{'team':{'id':2}}})


def test_postponed_abstract_final_is_not_a_played_game():
    p={'dates':[{'date':'2026-04-02','games':[game('D','Postponed')]}]}
    r=completed_schedule(p,2026)
    assert r['completed_games']==0 and len(r['unresolved_games'])==1


def test_rescheduled_listing_counts_game_once_and_preserves_both_versions():
    p={'dates':[{'date':'2026-04-02','games':[game('D','Postponed')]},{'date':'2026-04-03','games':[game('F','Final')]}]}
    r=completed_schedule(p,2026)
    assert r['completed_games']==1 and r['unique_regular_games']==1 and not r['unresolved_games']
    assert len(r['resolved_multiple_listing_games'][0]['versions'])==2
    assert r['team_game_counts']=={1:1,2:1} and not r['complete_regular_season_coverage']


def test_conflicting_game_participants_or_played_dates_fail():
    with pytest.raises(ValueError):completed_schedule({'dates':[{'date':'2026-04-03','games':[game('F','Final'),game('F','Final',away=3)]}]},2026)
    with pytest.raises(ValueError):completed_schedule({'dates':[{'date':'2026-04-03','games':[game('F','Final'),game('F','Final','2026-04-04')]}]},2026)


def test_empty_schedule_is_not_a_complete_zero_season():
    assert not completed_schedule({'dates':[]},2026)['complete_regular_season_coverage']
