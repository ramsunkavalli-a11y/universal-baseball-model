import copy
import pytest

from universal_baseball.defense_role_scope import (
    schedule_context, parse_team_logs, parse_people_isolated, certify_measurements,
)
from test_defense_role_logs import payload


def context(cross=False, resumed=False):
    return {123: dict(teams=[142, 143], official_date='2024-08-01', qualified=True,
        dates=['2024-08-01'], period=None if cross else 'August_onward', resumed=resumed)}


def parse(p, ctx=None):
    return parse_team_logs(p, player_id=1, season=2024, sport_id=1,
                          source_id='fixture', context=ctx if ctx is not None else context())


def test_team_grain_requires_suspended_opposing_teams():
    p=payload(); other=copy.deepcopy(p['stats'][0]['splits'][0]); other['team']['id']=143
    p['stats'][0]['splits'].append(other)
    with pytest.raises(ValueError):parse(p)
    rows=parse(p,context(resumed=True))
    assert len(rows)==2 and sum(r['fielding_outs'] for r in rows)==52
    p['stats'][0]['splits'].append(copy.deepcopy(other))
    with pytest.raises(ValueError):parse(p,context(resumed=True))


def test_cross_period_keeps_annual_outs_and_nulls_period():
    rows=parse(payload(),context(cross=True,resumed=True))
    assert rows[0]['fielding_outs']==26 and rows[0]['period'] is None
    assert rows[0]['date_status']=='cross_period_resumption'
    assert parse(payload(),{})[0]['period'] is None


def test_single_failure_does_not_discard_other_person():
    good=payload(); bad=copy.deepcopy(good); bad['stats'][0]['splits'][0]['stat']['innings']='8.3'
    bad['stats'][0]['splits'][0]['player']['id']=2
    p=dict(people=[dict(id=1,**good),dict(id=2,**bad)])
    rows,errors=parse_people_isolated(p,player_ids=[1,2],season=2024,sport_id=1,
        source_id='fixture',context=context())
    assert set(rows)=={1} and set(errors)=={2}


def test_measurements_independent_and_zero_has_no_date_exposure():
    rows=parse(payload('10','0.0',1),context(cross=True,resumed=True))
    c=[dict(annual=dict(fielding_outs=0,raw_starts=1,appearances=2),
            log=dict(fielding_outs=0,raw_starts=1,appearances=1))]
    cert=certify_measurements(c,rows)
    assert cert['fielding_outs']['periods']
    assert cert['reviewed_starts']['full_year'] and not cert['reviewed_starts']['periods']
    assert not cert['appearances']['full_year']
    assert not certify_measurements(c,[])['fielding_outs']['full_year']


def test_schedule_periods_use_all_segments_not_original_date():
    game=dict(gamePk=123,season='2024',gameType='R',officialDate='2024-07-31',
        status=dict(abstractGameState='Final'),resumeDate='2024-08-02T00:00:00Z',
        resumeGameDate='2024-08-02',teams={s:dict(team=dict(id=i,sport=dict(id=1)))
                                        for s,i in [('home',142),('away',143)]})
    p=dict(totalGames=1,dates=[dict(date='2024-07-31',games=[game])])
    g=schedule_context(p,season=2024,sport_id=1)[123]
    assert g['period'] is None and g['resumed']
    game['resumeGameDate']='2024-07-31'
    assert schedule_context(p,season=2024,sport_id=1)[123]['period']=='before_August'
    p['totalGames']=2
    with pytest.raises(ValueError):schedule_context(p,season=2024,sport_id=1)


def test_preserve_original_payload_and_strict_total_count():
    p=payload(); original=copy.deepcopy(p);parse(p);assert p==original
    p['stats'][0]['totalSplits']=2
    with pytest.raises(ValueError):parse(p)
