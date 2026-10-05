import numpy as np
import pytest

from universal_baseball.hitter_shared_events import profile, rebase, PROFILE


REF = np.array([.52,.22,.08,.01,.1,.04,.005,.025])


def fixtures():
    graph = dict(cutoff=2024, held_fold=0, max_source_year=2024, offsets={'MLB':[0.]*8,'DSL':[0.]*8},mlb_reference=REF.tolist())
    cal = dict(cutoff=2024,max_target_year=2024,excluded_folds=[0,1],domestic_people=100,
               domestic_intercepts=[0.]*8,domestic_slopes=[.7]*8)
    row = dict(season=2024,bucket='MLB',plate_appearances=600,strike_outs=120,
        unintentional_walks=60,hit_by_pitch=5,babip_hits=130,doubles=25,triples=5,home_runs=30)
    return graph,cal,row


def test_rebase_coherent_and_reference_neutral():
    new=REF.copy();new[0]-=.02;new[-1]+=.02
    assert np.allclose(rebase(REF,REF,new),new)
    assert np.allclose(rebase(new,new,REF),REF)


def test_zero_source_is_explicit_missing_and_not_future_dependent():
    g,c,r=fixtures()
    arms,n=profile([dict(r,season=2026)],g,c,None,None,origin=2024,outer_fold=0,own_fold=1)
    assert arms['foreign']['shared_missing']==1
    assert all(arms['foreign'][e]==0 for e in PROFILE[:8])
    assert n['US_supported_PA']==0


def test_tiny_source_cannot_dominate_pool_and_future_ignored():
    g,c,r=fixtures();tiny=dict(r,bucket='DSL',season=2022,plate_appearances=10,strike_outs=1,
        unintentional_walks=1,hit_by_pitch=0,babip_hits=2,doubles=0,triples=0,home_runs=1)
    _,n=profile([r,tiny],g,c,None,None,origin=2024,outer_fold=0,own_fold=1)
    _,base=profile([r],g,c,None,None,origin=2024,outer_fold=0,own_fold=1)
    assert n['US_supported_PA']==606
    assert np.max(abs(np.array(n['past_US_probability'])-base['past_US_probability'])) < 6/606
    assert np.isclose(sum(n['future_shared_probability']),1)


def test_reject_held_player_or_future_calibration():
    g,c,r=fixtures()
    with pytest.raises(ValueError):
        profile([r],g,dict(c,excluded_folds=[0]),None,None,origin=2024,outer_fold=0,own_fold=1)
    with pytest.raises(ValueError):
        profile([r],g,dict(c,max_target_year=2025),None,None,origin=2024,outer_fold=0,own_fold=1)


def test_foreign_production_is_shared_not_separate_and_precision_is_actual_pa():
    g,c,r=fixtures()
    hist={f'{l}_{lag}':dict(season=2024-lag,counts=dict(pa=100 if l=='NPB' and lag==0 else 0),
              player_identity_and_stat_observed=True) for l in ['NPB','KBO'] for lag in range(3)}
    s=dict(origin_year=2024,candidate_key='2024:1',foreign_history_counts=hist)
    p=dict(origin_year=2024,candidate_key='2024:1',outer_fold=0,excluded_folds=[0,1],MLB_reference=REF.tolist(),
           leagues=[dict(league='NPB',translated_probability=REF.tolist(),mover_people=3)])
    arms,n=profile([r],g,c,s,p,origin=2024,outer_fold=0,own_fold=1)
    assert n['foreign_supported_PA']==100 and np.isclose(n['foreign_share'],1/7)
    assert arms['domestic']['shared_reliability']==arms['foreign']['shared_reliability']
    for name in ['domestic','foreign']:
        assert np.isclose(sum(arms[name][k] for k in PROFILE[:8]),0)


def test_newer_mlb_exposure_reduces_old_foreign_weight():
    g,c,r=fixtures()
    hist={f'{l}_{lag}':dict(season=2024-lag,counts=dict(pa=100 if l=='NPB' and lag==2 else 0),
              player_identity_and_stat_observed=True) for l in ['NPB','KBO'] for lag in range(3)}
    s=dict(origin_year=2024,candidate_key='2024:1',foreign_history_counts=hist)
    p=dict(origin_year=2024,candidate_key='2024:1',outer_fold=0,excluded_folds=[0,1],MLB_reference=REF.tolist(),
           leagues=[dict(league='NPB',translated_probability=REF.tolist(),mover_people=3)])
    _,n=profile([r],g,c,s,p,origin=2024,outer_fold=0,own_fold=1)
    more={key:(v*2 if key not in ['season','bucket'] else v) for key,v in r.items()}
    _,large=profile([more],g,c,s,p,origin=2024,outer_fold=0,own_fold=1)
    assert n['foreign_supported_PA']==60
    assert np.isclose(n['foreign_share'],60/660)
    assert np.isclose(large['foreign_share'],60/1260)


def test_more_observed_power_increases_calibrated_hr_probability():
    g,c,r=fixtures()
    _,base=profile([r],g,c,None,None,origin=2024,outer_fold=0,own_fold=1)
    _,power=profile([dict(r,home_runs=40)],g,c,None,None,origin=2024,outer_fold=0,own_fold=1)
    assert power['future_US_probability'][-1]>base['future_US_probability'][-1]
