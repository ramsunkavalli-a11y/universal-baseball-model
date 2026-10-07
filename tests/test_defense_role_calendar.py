import copy
import pytest
from universal_baseball.defense_role_calendar import completed_schedule_context


def game(detail='Final',**extras):
    return dict(gamePk=123,gameType='R',season='2024',officialDate='2024-08-09',
        status=dict(abstractGameState='Final',detailedState=detail),
        teams={s:dict(team=dict(id=i,sport=dict(id=1))) for s,i in [('home',142),('away',143)]},**extras)


def context(games):
    return completed_schedule_context(dict(totalGames=len(games),
        dates=[dict(date=d,games=[g]) for d,g in games]),season=2024,sport_id=1)


def test_postponed_abstract_final_is_not_played_early_segment():
    old=game('Postponed',rescheduleDate='2024-08-09T00:00:00Z')
    new=game(rescheduledFromDate='2024-04-07')
    g=context([('2024-04-07',old),('2024-08-09',new)])[123]
    assert g['dates']==['2024-08-09'] and g['period']=='August_onward'
    assert not g['resumed']


def test_real_resumption_keeps_both_periods():
    original=game(resumeDate='2024-08-09T00:00:00Z',resumeGameDate='2024-08-09')
    original['officialDate']='2024-06-26'
    resumed=copy.deepcopy(original);resumed.pop('resumeDate');resumed.pop('resumeGameDate')
    resumed.update(resumedFrom='2024-06-26T00:00:00Z',resumedFromDate='2024-06-26')
    g=context([('2024-06-26',original),('2024-08-09',resumed)])[123]
    assert g['dates']==['2024-06-26','2024-08-09'] and g['period'] is None and g['resumed']


def test_no_played_game_remains_unknown_and_source_unchanged():
    g=game('Cancelled');before=copy.deepcopy(g)
    assert context([('2024-08-09',g)])=={} and g==before
    assert context([('2024-08-09',game('Completed Early: Rain'))])[123]['qualified']
    with pytest.raises(ValueError):
        completed_schedule_context(dict(totalGames=2,dates=[]),season=2024,sport_id=1)
