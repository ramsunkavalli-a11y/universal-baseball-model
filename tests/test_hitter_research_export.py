import pytest
from universal_baseball.hitter_research_export import ARMS, branch, export_row


def example():
    r=dict(row_id=1,player_id=99,player_name='Test',origin_year=2024,target_year=2025,
        outer_fold=2,age=22.,source_position='6',stage='Upper minors',prior_debut=0,
        sc_tracked=False,msc_eligible=False,minimum_profile_people=0,
        origin_evidence_bridge=True,needs_availability_scenario=False,hard_unavailable=False,
        reported_retired=False,preseason_pa=20.,preseason_p=.2,preseason_conditional_pa=100.,
        preseason_raw_p=.2,preseason_raw_conditional_pa=100.,origin_replacement_rate=.003,
        next_pa=0,next_value=0.,actual_future_relative_rate=0.,pa_0=0,
        steamer_index=None,zips_index=None,steamer_pa=None,steamer_value=None,
        sc_own_ev_n=0,msc_own_ev_n=0,scout_listed_0=1,scout_rank_score_0=.8,
        draft_known=1,pick_number=10,draft_year=2023)
    for arm in ARMS:r[arm+'_rate']=.5;r[arm+'_value']=20*(.5/600+.003)
    c=dict(context_reason='known',context_parent='Giants',context_club='Sacramento',
        context_basis='origin',context_club_year=2024,context_rights_date=None)
    return r,c,dict(participation=30,conditional_pa=10)


def test_branch_does_not_use_future_results():
    r,_,_=example()
    for pa in [0,1,700]:
        r['next_pa']=pa;r['actual_future_relative_rate']=100-pa
        assert branch(r)=='Translated prospect Ridge'
    r.update(prior_debut=1,sc_tracked=True)
    assert branch(r)=='MLB Statcast Ridge'
    r['sc_tracked']=False
    assert branch(r)=='Current rate fallback'


def test_nonarrival_has_no_observed_rate_but_retains_forecast():
    r,c,s=example();o=export_row(r,c,s,'2025-01-24',{})
    assert o['next_rate'] is None and o['next_value']==0
    assert o['rates']['combined']==.5 and o['pa']==20
    assert any('eventual MLB' in f for f in o['flags'])


def test_observed_rate_is_future_relative_not_contribution_reference():
    r,c,s=example();r.update(next_pa=100,actual_future_relative_rate=1.,next_value=.9)
    o=export_row(r,c,s,'2025-01-24',{})
    assert o['next_rate']==1. and o['next_value']==.9
    assert o['next_value']!=100*(o['next_rate']/600+o['replacement_rate'])


def test_unknown_affiliation_does_not_reuse_club_or_future_owner():
    r,c,s=example();c['context_reason']='stale last observed club'
    assert export_row(r,c,s,'2025-01-24',{})['org']=='Unknown affiliation'


def test_bad_pa_or_value_recomposition_blocks_export():
    r,c,s=example();r['preseason_pa']=50.
    with pytest.raises(AssertionError):export_row(r,c,s,'2025-01-24',{})
    r,c,s=example();r['combined_value']+=1
    with pytest.raises(AssertionError):export_row(r,c,s,'2025-01-24',{})


def test_unproven_minor_overlay_is_not_default_main():
    r,c,s=example();r['precision_measurements_rate']=3.
    r['precision_measurements_value']=20*(3/600+.003)
    o=export_row(r,c,s,'2025-01-24',{})
    assert o['rates']['combined']==.5 and o['rates']['precision_measurements']==3.
    assert o['branch']=='Translated prospect Ridge'


def test_public_membership_requires_all_matched_conditions():
    r,c,s=example();r.update(pa_0=100,steamer_index=.3,zips_index=None)
    assert not export_row(r,c,s,'2025-01-24',{})['public_match']
    r['zips_index']=.31
    assert export_row(r,c,s,'2025-01-24',{})['public_match']
