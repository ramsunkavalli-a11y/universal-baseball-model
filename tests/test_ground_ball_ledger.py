import polars as pl
from universal_baseball.ground_ball_ledger import add_benchmark, reconcile_ground_balls, FIELDS


def ball(location=7,outcome='1B',**kwargs):
    row={'hit_location':location,'terminal_outcome_group':outcome,'has_source_conflict':False,
         'any_bunt':False,**{f'fielder_{p}':100+p for p in range(1,10)},**kwargs}
    return add_benchmark(pl.DataFrame([row])).to_dicts()[0]


def test_singles_and_extra_base_hits_are_not_same_allocation():
    a=ball();b=ball(outcome='2B')
    assert (a['candidate_position_a'],a['candidate_position_b'],a['share_a'])==(5,6,.5)
    assert (b['candidate_position_a'],b['candidate_position_b'],b['share_a'])==(5,None,1)
    assert a['unassigned_sensitivity_share']==b['unassigned_sensitivity_share']==1


def test_unknown_center_extra_base_and_outfield_error_not_fake_range():
    for loc,out in [(8,'2B'),(8,'3B'),(7,'ROE'),(7,'OUT'),(5,'FC_REACH'),(None,'1B'),(5,None)]:
        assert ball(loc,out)['unassigned_share']==1


def test_pitcher_first_base_and_catcher_stay_present():
    for p in (1,2,3):
        a=ball(p,'OUT');assert a['candidate_fielder_a']==100+p and a['share_a']==1


def test_conflict_bunt_missing_id_are_not_silent_drops():
    assert ball(has_source_conflict=True)['unassigned_share']==1
    assert ball(any_bunt=True)['unassigned_share']==1
    a=ball(fielder_5=None)
    assert a['unknown_candidate_identity'] and a['share_a']+a['share_b']==1


def test_conservation_for_all_known_combinations():
    for p in [None,*range(1,10)]:
        for out in [None,'OUT','MULTI_OUT','FC_REACH','1B','2B','3B','HR','ROE']:
            a=ball(p,out)
            assert a['share_a']+a['share_b']+a['unassigned_share']==1


def source(**kwargs):
    return {**dict.fromkeys(FIELDS), 'game_pk':1,'at_bat_index':2,'source_asset':'a',
        'season':2024,'level':'a','game_type':'R','bb_type':'ground_ball',
        'terminal_outcome_group':'OUT','batted_ball_out':True,'hit_location':6,
        'responsible_position':6,'responsible_fielder_id':106,'fielder_6':106,
        'on_1b':None,'on_2b':None,'on_3b':None,**kwargs}


def test_conflicting_non_groundball_version_kept_and_blocked():
    r=reconcile_ground_balls([pl.DataFrame([source(),source(source_asset='b',bb_type='fly_ball')])])
    a=r.to_dicts()[0]
    assert r.height==1 and a['bb_type'] is None and a['has_source_conflict']
    assert 'bb_type' in a['conflicting_fields']
    assert add_benchmark(r)['unassigned_share'][0]==1


def test_null_plus_known_consensus_not_first_copy_or_conflict():
    r=reconcile_ground_balls([pl.DataFrame([source(fielder_6=None),source(source_asset='b')])])
    assert r['fielder_6'][0]==106 and not r['has_source_conflict'][0]


def test_duplicate_snapshots_not_duplicate_balls():
    r=reconcile_ground_balls([pl.DataFrame([source(),source(),source(source_asset='b')])])
    assert r.height==1 and r['source_row_count'][0]==3
