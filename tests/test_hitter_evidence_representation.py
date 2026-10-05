from copy import deepcopy

import numpy as np
import pytest

from universal_baseball.hitter_evidence_representation import (
    information_share, minor_evidence, foreign_precision, foreign_evidence,
    job_evidence, check_cutoff,
)


def foreign_source():
    return dict(candidate_key='2024:1', origin_year=2024, information_date='2025-01-24',
        roster_hitter_codes=['O'], foreign_history_counts={f'{l}_{k}':
        dict(season=2024-k, counts={'pa':2 if l=='NPB' and k==0 else 0},
             player_identity_and_stat_observed=l=='NPB' and k==0)
        for l in ['NPB','KBO'] for k in range(3)})


def profile():
    return dict(candidate_key='2024:1', origin_year=2024, outer_fold=2, excluded_folds=[2,3],
                MLB_reference=[.5,.2,.08,.01,.15,.025,.005,.03],
                leagues=[dict(league='NPB', mover_people=5,
                              translated_probability=[.48,.18,.1,.01,.16,.035,.005,.03])])


def count_row(season=2024, bucket='DSL', pa=57):
    return dict(season=season, bucket=bucket, plate_appearances=pa,
                strike_outs=7, unintentional_walks=12, hit_by_pitch=1,
                babip_hits=12, doubles=2, triples=0, home_runs=1)


def graph():
    return dict(cutoff=2024, max_source_year=2024,
                mlb_reference=[.5,.2,.08,.01,.15,.025,.005,.03], offsets={'DSL':np.zeros(8)})


def job_row():
    return dict(origin_year=2024, target_year=2025, ctx_information_date='2025-01-24',
                work_0=0.,work_1=546.,work_2=700.,quality_0=0.,quality_1=1.3,quality_2=.6,
                last_stat_gap=5,pa_0=0,on_40man=0,status_major_link=1,status_agreement_unspecified=0)


def test_information_share_fades_with_newer_MLB_evidence():
    shares=[information_share(34.2,m) for m in [0,100,600,1800,6000]]
    assert all(a>b for a,b in zip(shares,shares[1:]))
    assert shares[0] < .03 and shares[-1] < .005
    with pytest.raises(ValueError):
        information_share(3,-1)


def test_small_DSL_has_small_bounded_effect_and_future_rows_are_ignored():
    old=count_row(2022)
    x,note=minor_evidence([old],graph(),origin=2024,mlb_exposure=0.)
    assert note['supported_precision_PA']==pytest.approx(34.2)
    expected_share=34.2/(34.2+1200)
    expected_walk=expected_share*((12+.5)/(57+4)-.08)/.1
    assert x['evidence_minor_UBB']==pytest.approx(expected_walk)
    assert max(abs(x[f'evidence_minor_{e}']) for e in ['K','UBB','HBP','1B','2B','3B','HR']) <= 10*expected_share
    augmented=[old,count_row(2025,pa=1000)]
    assert minor_evidence(augmented,graph(),origin=2024,mlb_exposure=0.)== (x,note)


def test_missing_translation_is_not_bad_talent():
    g=graph();g['offsets']={}
    x,note=minor_evidence([count_row()],g,origin=2024,mlb_exposure=500.)
    assert x['evidence_minor_missing']==1 and note['observed_precision_PA']==57
    assert all(v==0 for k,v in x.items() if k.startswith('evidence_minor_') and k!='evidence_minor_missing')


def test_foreign_recency_units_are_not_actual_precision():
    s=foreign_source();s['foreign_history_counts']['NPB_1']['counts']['pa']=100
    s['foreign_history_counts']['NPB_1']['player_identity_and_stat_observed']=True
    total,by=foreign_precision(s,origin=2024)
    assert total==82 and by['NPB']==82  # Not 5*2 + 4*100 = 410.
    s['foreign_history_counts']['NPB_2']['season']=2025
    with pytest.raises(ValueError,match='Future'):
        foreign_precision(s,origin=2024)


def test_foreign_production_fades_without_raw_feature_bypass():
    s,p=foreign_source(),profile()
    a,na=foreign_evidence(s,p,origin=2024,outer_fold=2,own_fold=3,mlb_exposure=0,minor_exposure=0)
    b,nb=foreign_evidence(s,p,origin=2024,outer_fold=2,own_fold=3,mlb_exposure=1800,minor_exposure=0)
    assert abs(b['evidence_foreign_K']) < abs(a['evidence_foreign_K'])
    assert na['observed_precision_PA']==2 and na['information_share'] < .002
    assert all('clr' not in k and 'mover_people' not in k for k in a)
    p['excluded_folds']=[2]
    with pytest.raises(ValueError,match='contamination'):
        foreign_evidence(s,p,origin=2024,outer_fold=2,own_fold=3,mlb_exposure=0,minor_exposure=0)


def test_missing_foreign_and_unknown_source_are_distinct():
    a,_=foreign_evidence(None,None,origin=2024,outer_fold=2,own_fold=3,mlb_exposure=0,minor_exposure=0)
    p=profile();p['leagues']=[]
    b,_=foreign_evidence(foreign_source(),p,origin=2024,outer_fold=2,own_fold=3,mlb_exposure=0,minor_exposure=0)
    assert not any(a.values()) and b['evidence_foreign_missing']==b['evidence_foreign_source_present']==1


def test_professional_activity_and_broad_OF_remain_known_without_MLB_fiction():
    row=job_row();row['status_major_link']=0;row['status_agreement_unspecified']=1
    s=foreign_source();s['foreign_history_counts']['NPB_0']['counts']['pa']=600
    result=job_evidence(row,s)
    assert result['professional_work_0']==1 and result['professional_stat_gap']==0
    assert result['position_outfield_unspecified']==1 and result['last_MLB_work']==546/600
    assert result['returner_MLB_work']==546/600 and result['signed_first_team_work']==1
    assert row['pa_0']==0 and row['work_0']==0  # Never relabel NPB as MLB.
    original=deepcopy(result);row['future_injury']='unavailable';row['next_pa']=0
    assert job_evidence(row,s)==original
    check_cutoff(row,s)
    s['information_date']='2026-01-24'
    with pytest.raises(ValueError,match='information date'):
        check_cutoff(row,s)
