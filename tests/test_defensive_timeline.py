import pytest
from universal_baseball.defensive_timeline import defensive_timeline, attach_battery, TimelineError


def fixture():
    teams={}
    for side,offset in [('home',0),('away',100)]:
        players={f'ID{offset+i}':{'person':{'id':offset+i},'position':{'code':str(i)},
            'allPositions':[{'code':str(i)}],'battingOrder':str(i*100),
            'stats':{'fielding':{'gamesStarted':1}}} for i in range(1,10)}
        players[f'ID{offset+20}']={'person':{'id':offset+20},'position':{'code':'2'},
            'allPositions':[{'code':'2'}],'stats':{'fielding':{}}}
        teams[side]={'players':players}
    return {'liveData':{'boxscore':{'teams':teams},'plays':{'allPlays':[]}}}


def play(events,runners=()):
    return {'about':{'atBatIndex':0,'isTopInning':True},'matchup':{'pitcher':{'id':1}},
        'playEvents':events,'runners':list(runners)}


def test_mid_pa_catcher_change_is_not_applied_backwards():
    p=fixture();p['liveData']['plays']['allPlays']=[play([
        {'index':0,'isPitch':True},
        {'index':1,'details':{'eventType':'defensive_substitution'},'player':{'id':20},
            'position':{'code':'2'},'replacedPlayer':{'id':2}},
        {'index':2,'isPitch':True}])]
    t=defensive_timeline(p)
    events=[{'at_bat_index':0,'event_index':i,'catcher_id':None,'pitcher_id':None} for i in (0,2)]
    assert [e['catcher_id'] for e in attach_battery(events,t)]==[2,20]


def test_mid_pa_pitcher_change_is_not_applied_backwards():
    p=fixture();a=play([{'index':0,'isPitch':True},
        {'index':1,'details':{'eventType':'pitching_substitution'},'player':{'id':20},'position':{'code':'1'}},
        {'index':2,'isPitch':True}]);a['matchup']['pitcher']['id']=20
    p['liveData']['plays']['allPlays']=[a];t=defensive_timeline(p)
    assert t['snapshots'][(0,0)][1]==1 and t['snapshots'][(0,2)][1]==20
    assert t['matchups'][0]['match']


def test_sequential_position_switches_complete_before_pitch():
    p=fixture();p['liveData']['plays']['allPlays']=[play([
        {'index':0,'details':{'eventType':'defensive_switch'},'player':{'id':4},'position':{'code':'6'}},
        {'index':1,'details':{'eventType':'defensive_switch'},'player':{'id':6},'position':{'code':'4'}},
        {'index':2,'isPitch':True}])]
    t=defensive_timeline(p);assert t['snapshots'][(0,2)][4]==6 and t['snapshots'][(0,2)][6]==4


def test_missing_starter_fails_closed():
    p=fixture();del p['liveData']['boxscore']['teams']['home']['players']['ID2']
    p['liveData']['plays']['allPlays']=[play([{'index':0,'isPitch':True}])]
    with pytest.raises(TimelineError):defensive_timeline(p)


def test_pinch_hitter_does_not_silently_inherit_catcher_position():
    p=fixture();a=play([
        {'index':0,'details':{'eventType':'offensive_substitution'},'player':{'id':20},
            'battingOrder':'201','position':{'code':'11'},'replacedPlayer':{'id':2}},
        {'index':1,'isPitch':True}]);a['about']['isTopInning']=False
    b=play([{'index':0,'isPitch':True}]);b['about']['atBatIndex']=1
    p['liveData']['plays']['allPlays']=[a,b]
    with pytest.raises(TimelineError):defensive_timeline(p)


def test_bench_listing_on_both_teams_does_not_change_actual_team():
    p=fixture()
    p['liveData']['boxscore']['teams']['away']['players']['ID20']={'person':{'id':20},'stats':{}}
    p['liveData']['plays']['allPlays']=[play([
        {'index':0,'details':{'eventType':'defensive_substitution'},'player':{'id':20},
            'position':{'code':'2'},'replacedPlayer':{'id':2}}, {'index':1,'isPitch':True}])]
    assert defensive_timeline(p)['snapshots'][(0,1)][2]==20


def test_duplicate_pregame_position_requires_explicit_resolution_before_pitch():
    p=fixture();players=p['liveData']['boxscore']['teams']['home']['players']
    players['ID4']['allPositions']=[{'code':'8'},{'code':'4'}]
    p['liveData']['plays']['allPlays']=[play([
        {'index':0,'details':{'eventType':'defensive_switch'},'player':{'id':4},'position':{'code':'4'}},
        {'index':1,'details':{'eventType':'defensive_substitution'},'player':{'id':8},'position':{'code':'8'}},
        {'index':2,'isPitch':True}])]
    assert defensive_timeline(p)['snapshots'][(0,2)][4]==4
    p['liveData']['plays']['allPlays'][0]['playEvents']=[{'index':2,'isPitch':True}]
    with pytest.raises(TimelineError):defensive_timeline(p)
