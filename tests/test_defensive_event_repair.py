import pytest
from universal_baseball.defensive_event_repair import (
    official_events, reconcile_box, ground_ball_responsibility, narrative_capacity,
)


def feed(runners, actions=()):
    return {'gameData':{'game':{'pk':42,'type':'R'},'datetime':{'officialDate':'2018-06-01'},
        'status':{'abstractGameState':'Final'}},'liveData':{'plays':{'allPlays':[
            {'about':{'atBatIndex':0,'isTopInning':True},'runners':runners,'playEvents':list(actions)}]},
        'boxscore':{'teams':{'home':{'teamStats':{}},'away':{'teamStats':{}}}}}}


def runner(event, identity, index):
    return {'details':{'eventType':event,'runner':{'id':identity},'playIndex':index,
        'movementReason':'r_'+event}}


def test_double_steal_and_multiple_events_preserved():
    p = feed([runner('stolen_base_2b',1,2),runner('stolen_base_3b',2,2),runner('stolen_base_3b',1,5)])
    e,_ = official_events(p,42,2018)
    assert len(e) == 3
    assert all(x['catcher_id'] is None for x in e)


def test_one_wp_advances_two_runners_with_action_not_three_wps():
    p = feed([runner('wild_pitch',1,2),runner('wild_pitch',2,2)],
        [{'index':2,'details':{'eventType':'wild_pitch'}}])
    e,_ = official_events(p,42,2018)
    assert len(e) == 1 and e[0]['family'] == 'WP'


def test_runner_advancing_on_cs_play_is_not_caught():
    other=runner('caught_stealing_2b',2,3)
    other['details']['movementReason']='r_adv_play'
    e,_=official_events(feed([runner('caught_stealing_2b',1,3),other]),42,2018)
    assert len(e)==1 and e[0]['runner_id']==1


def test_safe_on_error_can_retain_official_caught_stealing_credit():
    r=runner('pickoff_caught_stealing_3b',1,3)
    r['movement']={'isOut':False}
    e,_=official_events(feed([r]),42,2018)
    assert len(e)==1 and e[0]['family']=='POCS'


def test_unrecognized_movement_reason_fails_closed():
    r=runner('stolen_base_2b',1,3)
    r['details']['movementReason']=None
    with pytest.raises(ValueError): official_events(feed([r]),42,2018)


def test_pickoff_caught_is_separate_but_reconciles_official_cs():
    p = feed([runner('pickoff_caught_stealing_2b',1,2)])
    p['liveData']['boxscore']['teams']['away']['teamStats'] = {'batting':{'caughtStealing':1}}
    e,_ = official_events(p,42,2018)
    assert e[0]['family'] == 'POCS'
    r = reconcile_box(p,e)
    assert next(x for x in r if x['side']=='away' and x['family']=='CS')['status']=='matched'
    assert next(x for x in r if x['side']=='home' and x['family']=='PB')['status']=='unknown_box_count'


@pytest.mark.parametrize('year',[2017,2026])
def test_wrong_year_rejected(year):
    with pytest.raises(ValueError): official_events(feed([]),42,year)


@pytest.mark.parametrize('outcome',['1B','2B','3B','ROE'])
def test_through_grounder_not_outfielder_range_opportunity(outcome):
    row={'game_pk':1,'at_bat_index':2,'bb_type':'ground_ball','hit_location':7,
        'terminal_outcome_group':outcome,'fielder_5':55,'fielder_6':66,'fielder_7':77}
    r=ground_ball_responsibility(row)
    assert sum(x['share'] for x in r)==1
    assert {x['candidate_fielder_id'] for x in r}=={55,66}
    assert not any(x['ex_ante_opportunity_certified'] for x in r)


@pytest.mark.parametrize('pos',[None,1,3,8])
def test_unknown_outcomes_positions_and_ids_never_disappear(pos):
    r=ground_ball_responsibility({'game_pk':1,'at_bat_index':2,'bb_type':'ground_ball',
        'hit_location':pos,'terminal_outcome_group':'UNKNOWN'})
    assert sum(x['share'] for x in r)==1
    assert all(x['unknown_fielder'] for x in r)


def test_conflicting_source_is_fully_unassigned():
    r=ground_ball_responsibility({'game_pk':1,'at_bat_index':2,'bb_type':'ground_ball',
        'hit_location':6,'fielder_6':66,'has_source_conflict':True})
    assert r[0]['candidate_position'] is None and r[0]['basis']=='source_conflict'


def test_terminal_groundout_does_not_encode_earlier_steal():
    assert not narrative_capacity('Matt Chapman grounds out, shortstop to first baseman.')
    assert narrative_capacity('Danny Oh steals (4) 2nd base.')[('SB','2b')]==1
