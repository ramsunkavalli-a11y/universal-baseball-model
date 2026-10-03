import json
import html
import pytest
from universal_baseball.historical_prospect_rank import project,features


def sample():
    entries=[dict(rank=i,playerEntity=dict(player={'__ref':f'Person:{i}'},eta='2099',prospectBio=[])) for i in range(1,101)]
    payload={'ROOT_QUERY':{'getPlayerRankingsFromSelection({"limit":100,"slug":"sel-pr-2016-top100"})':entries}}
    payload.update({f'Person:{i}':dict(id=i,useName='Player',useLastName=str(i),currentAge=99,currentTeam='Future team') for i in range(1,101)})
    return dict(context=dict(year='2016',list='top100'),payload=payload)


def encode(s):return '<span data-init-state="'+html.escape(json.dumps(s),quote=True)+'"></span>'


def test_live_biography_and_future_grades_never_enter():
    s=sample();a=project(encode(s),2016);s['payload']['Person:1']['currentAge']=17
    s['payload']['ROOT_QUERY'][next(iter(s['payload']['ROOT_QUERY']))][0]['playerEntity']['eta']='2017'
    assert project(encode(s),2016)==a
    assert set(a[0])=={'season','player_id','rank','list_capacity','list_complete','player_name'}


def test_missing_duplicate_and_wrong_year_fail_closed():
    s=sample();s['payload']['ROOT_QUERY'][next(iter(s['payload']['ROOT_QUERY']))].pop()
    with pytest.raises(ValueError):project(encode(s),2016)
    with pytest.raises(ValueError):project(encode(sample()),2017)
    with pytest.raises(ValueError):project(encode(sample()),2026)


def test_missing_list_not_unranked_and_future_rank_cannot_change_features():
    ranks={(2016,1):31};coverage={2016:100}
    a=features(1,2016,ranks,coverage)
    assert a['scout_listed_1'] is None and a['scout_rank_score_1'] is None
    assert features(2,2016,ranks,coverage)['scout_listed_0']==0
    assert features(1,2016,{**ranks,(2017,1):1},{**coverage,2017:100})==a
    assert features(2,2020,{(2020,1):1},{2020:99})['scout_listed_0'] is None
    assert features(1,2020,{(2020,1):1},{2020:99})['scout_listed_0']==1
