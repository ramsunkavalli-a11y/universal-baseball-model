import copy
import pytest
from universal_baseball.arm_receiving_source import normalize_arm, normalize_receiving, arm_metadata


def arm():
    return dict(start_year=2022,end_year=2022,timeframe=2022,entity_code='Fld',entity_id=1,
                entity_name='Test',n_opp_xb=10,n_att_xb=2,n_out=1,n_safe=1,rate_att_xb=.2,
                fielder_runs=.3,fielder_runs_swipe=-.2,fielder_runs_snipe=.4,fielder_runs_freeze=.1)


def native(pos=9, arm_runs=.3, rec=None):
    return dict(position=pos,native_outs=100,arm_runs=arm_runs,fielding_runs_prevented_on_rec1b=rec)


def test_holds_are_opportunities():
    r=normalize_arm(arm(),[native()],2022)
    assert r['opportunities']==10 and r['holds']==8 and r['runs_per_100']==3
    assert r['isolated_outfield_quality_valid']


def test_mixed_positions_do_not_become_isolated_outfield_skill():
    r=normalize_arm(arm(),[native(9,.2),native(4,.1)],2022)
    assert r['all_position_quality_valid'] and not r['isolated_outfield_quality_valid']
    assert r['non_outfield_arm_runs']==.1


def test_native_gap_quarantines_rate_not_raw_credit():
    r=normalize_arm(arm(),[native(9,.1)],2022)
    assert not r['all_position_quality_valid'] and r['runs']==.3
    assert not normalize_arm(arm(),[],2022)['all_position_quality_valid']


def test_bad_counts_or_identity_stop():
    r=arm();r['n_safe']=2
    with pytest.raises(AssertionError):normalize_arm(r,[native()],2022)
    with pytest.raises(AssertionError):normalize_arm(arm(),[native()],2025)


def receiver():
    r=dict(year=2022,player_id=1,name='Test',n_plays=10,n_outs=9,
           avg_expected_rate_out=.8,total_oaa=1.,avg_oaa=.1)
    for k in ('on_target','low','high','scoop','wide','bounce'):
        r['n_'+k]=10 if k=='on_target' else 0
        r['outs_'+k]=9 if k=='on_target' else 0
        r['oaa_'+k]=1. if k=='on_target' else 0.
    return r


def test_receiver_difficulty_adjustment_and_conversion():
    r=normalize_receiving(receiver(),[native(3,None,.75)],2022)
    assert r['expected_outs']==8 and r['runs']==.75 and r['quality_valid']


def test_receiver_inconsistent_throw_categories_stop():
    r=receiver();r['n_scoop']=1
    with pytest.raises(AssertionError):normalize_receiving(r,[native(3,None,.75)],2022)
    r=receiver();r['avg_expected_rate_out']=.9
    with pytest.raises(AssertionError):normalize_receiving(r,[native(3,None,.75)],2022)


def test_receiver_missing_is_unknown_not_neutral():
    r=normalize_receiving(receiver(),[],2022)
    assert not r['quality_valid'] and r['native_runs'] is None


def test_metadata_cannot_open_2026():
    with pytest.raises(AssertionError):arm_metadata({},2026,False)


def test_null_adjustment_preserves_opportunity_not_zero_talent():
    from universal_baseball.arm_receiving_coverage import arm_record
    r=arm()
    for k in ('fielder_runs','fielder_runs_swipe','fielder_runs_snipe','fielder_runs_freeze'):r[k]=None
    out=arm_record(r,[native()],2022)
    assert out['opportunities']==10 and out['runs'] is None
    assert not out['adjustment_measured'] and not out['all_position_quality_valid']
