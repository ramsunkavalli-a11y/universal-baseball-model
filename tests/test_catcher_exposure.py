import pytest
from universal_baseball.catcher_exposure import apply_movements, ExposureError, runner_timeline, attach_exposures, battery_timeline


def move(rid,start,end,out=False,number=None):
    return {'movement':{'start':start,'end':end,'isOut':out,'outNumber':number},
        'details':{'runner':{'id':rid},'playIndex':0}}


def test_forced_advances_simultaneous_not_order_dependent():
    rows=[move(10,None,'1B'),move(11,'1B','2B'),move(12,'2B','3B')]
    assert apply_movements({1:11,2:12},0,rows)==({1:10,2:11,3:12},0)
    assert apply_movements({1:11,2:12},0,list(reversed(rows)))==({1:10,2:11,3:12},0)


def test_double_steal_and_duplicate_movement():
    r=move(11,'1B','2B')
    assert apply_movements({1:11,2:12},0,[r,r,move(12,'2B','3B')])==({2:11,3:12},0)


def test_safe_on_error_cs_not_out_and_no_future_runner_insertion():
    assert apply_movements({1:11},1,[move(11,'1B','2B')])==({2:11},1)
    with pytest.raises(ExposureError):apply_movements({},1,[move(11,'1B','2B')])


def test_multiple_outs_counted_once_each():
    rows=[move(10,None,None,True,2),move(11,'1B',None,True,1)]
    assert apply_movements({1:11},0,rows)==({},2)
    with pytest.raises(ExposureError):apply_movements({1:11},1,rows)


def test_two_moves_same_runner_chain():
    assert apply_movements({1:11},0,[move(11,'2B','3B'),move(11,'1B','2B')])==({3:11},0)


def test_return_to_base_scoring_legs_have_one_final_state():
    assert apply_movements({1:11},0,[move(11,'1B','2B'),move(11,'2B','1B'),move(11,'1B','score')])==({},0)
    assert apply_movements({2:11},0,[move(11,'2B','2B'),move(11,'2B','score')])==({},0)


def test_third_out_force_does_not_invent_unrecorded_safe_advances():
    rows=[move(12,'3B',None,True,3),move(10,None,'1B')]
    assert apply_movements({1:11,3:12},2,rows)==({},3)
    with pytest.raises(ExposureError):apply_movements({1:11,3:12},1,[move(12,'3B',None,True,2),move(10,None,'1B')])


def fixture(events,rows=(),post=None,outs=0):
    matchup={f'postOn{n}':{'id':rid} for n,rid in (post or {}).items()}
    return {'liveData':{'plays':{'allPlays':[{'about':{'atBatIndex':0,'inning':1,'isTopInning':True},
        'playEvents':events,'runners':list(rows),'matchup':matchup,'count':{'outs':outs}}]}}}


def test_automatic_runner_placed_before_pitch_and_post_checked():
    p=fixture([{'index':0,'details':{'eventType':'runner_placed'},'base':2,'player':{'id':11}},
        {'index':1,'isPitch':True}],post={'Second':11})
    t=runner_timeline(p);assert t['snapshots'][(0,1)]['bases']=={2:11}
    p['liveData']['plays']['allPlays'][0]['matchup']={}
    with pytest.raises(ExposureError):runner_timeline(p)


def test_runner_state_before_movement_not_after():
    r=move(11,None,'1B');p=fixture([{'index':0,'isPitch':True}],rows=[r],post={'First':11})
    assert runner_timeline(p)['snapshots'][(0,0)]['bases']=={}


def test_blocking_risk_includes_empty_bases_two_strikes():
    p=fixture([{'index':0,'isPitch':True,'playId':'p'},
        {'index':1,'details':{'eventType':'wild_pitch'},'actionPlayId':'p'}])
    pitch={'at_bat_index':0,'event_index':0,'pitcher_id':1,'catcher_id':2}
    battery={'pitches':[pitch],'snapshots':{(0,0):{1:1,2:2},(0,1):{1:1,2:2}}}
    state={'bases':{},'outs':0,'balls':0,'strikes':2}
    ev={'at_bat_index':0,'event_index':1,'family':'WP'}
    a=attach_exposures(p,[ev],battery,{'snapshots':{(0,0):state,(0,1):state}})
    assert a['pitches'][0]['blocking_at_risk']
    assert a['events'][0]['pitch_link']=='exact_actionPlayId'
    assert a['events'][0]['linked_pitch_index']==0
    state['bases']={1:11}
    assert len(attach_exposures(p,[ev],battery,{'snapshots':{(0,0):state}})['runner_pitches'])==1


def test_never_guess_previous_pitch_when_link_absent_or_duplicate():
    p=fixture([{'index':0,'isPitch':True,'playId':'p'},
        {'index':1,'details':{'eventType':'wild_pitch'}}])
    battery={'pitches':[{'at_bat_index':0,'event_index':0,'pitcher_id':1,'catcher_id':2}],
        'snapshots':{(0,0):{1:1,2:2},(0,1):{1:1,2:2}}}
    ev={'at_bat_index':0,'event_index':1,'family':'WP'}
    assert attach_exposures(p,[ev],battery,None)['events'][0]['pitch_link']=='unlinked'
    plays=p['liveData']['plays']['allPlays'][0]['playEvents']
    plays[1]['actionPlayId']='p'
    plays.append({'index':2,'isPitch':True,'playId':'p'})
    assert attach_exposures(p,[ev],battery,None)['events'][0]['pitch_link']=='unlinked'


def test_action_after_substitution_does_not_silently_change_linked_battery():
    p=fixture([{'index':0,'isPitch':True,'playId':'p'},
        {'index':1,'actionPlayId':'p'}])
    battery={'pitches':[{'at_bat_index':0,'event_index':0,'pitcher_id':1,'catcher_id':2}],
        'snapshots':{(0,0):{1:1,2:2},(0,1):{1:1,2:3}}}
    a=attach_exposures(p,[{'at_bat_index':0,'event_index':1,'family':'WP'}],battery,None)
    assert a['events'][0]['link_battery_match'] is False


def test_inning_ending_cs_retained_even_when_no_batter_result():
    r=move(11,'2B',None,True,3);r['details']['playIndex']=1
    # Two preceding outs are represented as real movements, not a seeded future state.
    p=fixture([{'index':0,'isPitch':True}],rows=[move(10,None,None,True,1)],outs=1)
    a=p['liveData']['plays']['allPlays'][0]
    b={'about':{'atBatIndex':1,'inning':1,'isTopInning':True},'matchup':{},'count':{'outs':2},
       'playEvents':[{'index':0,'isPitch':True}],'runners':[move(12,None,None,True,2)]}
    c={'about':{'atBatIndex':2,'inning':1,'isTopInning':True},'matchup':{},'count':{'outs':3},
       'playEvents':[{'index':0,'details':{'eventType':'runner_placed'},'base':2,'player':{'id':11}},
                     {'index':1,'details':{'eventType':'caught_stealing_3b'}}],'runners':[r]}
    p['liveData']['plays']['allPlays']=[a,b,c]
    t=runner_timeline(p)
    assert t['snapshots'][(2,1)]['outs']==2 and t['snapshots'][(2,1)]['bases']=={2:11}
    assert t['checks'][-1]['outs']==3


def test_pinch_runner_replaces_identity_before_next_pitch():
    p=fixture([{'index':0,'details':{'eventType':'runner_placed'},'base':1,'player':{'id':11}},
        {'index':1,'details':{'eventType':'offensive_substitution'},'position':{'code':'12'},
         'player':{'id':12},'replacedPlayer':{'id':11}}, {'index':2,'isPitch':True}],post={'First':12})
    assert runner_timeline(p)['snapshots'][(0,2)]['bases']=={1:12}


def test_occupied_next_base_does_not_erase_double_steal_risk():
    p=fixture([{'index':0,'isPitch':True,'playId':'p'}])
    battery={'pitches':[{'at_bat_index':0,'event_index':0,'pitcher_id':1,'catcher_id':2}],
        'snapshots':{(0,0):{1:1,2:2}}}
    r={'snapshots':{(0,0):{'bases':{1:11,2:12},'outs':1,'balls':0,'strikes':0}}}
    rows=attach_exposures(p,[],battery,r)['runner_pitches']
    assert len(rows)==2 and rows[0]['next_base_occupied'] and not rows[1]['next_base_occupied']


def test_cp_certification_does_not_pretend_unknown_left_field_is_known():
    p=fixture([{'index':0,'isPitch':True}]);teams={}
    for side,offset in [('home',0),('away',100)]:
        teams[side]={'players':{str(offset+i):{'person':{'id':offset+i},'allPositions':[{'code':str(i)}],
            'stats':{'fielding':{'gamesStarted':1}}} for i in range(1,10) if i!=7}}
    p['liveData']['boxscore']={'teams':teams}
    p['liveData']['plays']['allPlays'][0]['matchup']['pitcher']={'id':1}
    t=battery_timeline(p)
    assert t['pitches'][0]['catcher_id']==2 and not t['pitches'][0]['full_lineup_known']
    del teams['home']['players']['2']
    with pytest.raises(ExposureError):battery_timeline(p)


def test_half_inning_reset_does_not_keep_left_on_base_runner():
    p=fixture([{'index':0,'details':{'eventType':'runner_placed'},'base':2,'player':{'id':11}}],post={'Second':11})
    p['liveData']['plays']['allPlays'].append({'about':{'atBatIndex':1,'inning':1,'isTopInning':False},
        'playEvents':[{'index':0,'isPitch':True}],'runners':[],'matchup':{},'count':{'outs':0}})
    assert runner_timeline(p)['snapshots'][(1,0)]['bases']=={}
