import numpy as np
import pytest
from universal_baseball.minor_range_correction import audit,fit,profile_table,predict


def row(pid,y=2017):
    return dict(origin_year=y,window_end=y+3,player_id=pid,position=6,level='AA',age_band='20-22',
                sample_band='1500+',quality_rate=1.)


def test_no_intercept_preserves_baseline_at_zero_signal():
    rows=[row(i) for i in range(20)];signals=np.zeros((20,4));model=fit(signals,np.ones(20)*9,rows)
    profiles=profile_table(rows,signals);r=predict(model,2.3,row(101),[0]*4,profiles)
    assert r['candidate']==2.3 and r['applied'] and r['correction']==0


def test_missing_profile_really_falls_back():
    rows=[row(i) for i in range(20)];s=np.ones((20,4));m=fit(s,np.ones(20),rows);t=row(101);t['level']='DSL'
    r=predict(m,1.2,t,[1]*4,profile_table(rows,s))
    assert r['candidate']==1.2 and not r['applied']


def test_extreme_signal_is_not_only_flagged():
    rows=[row(i) for i in range(20)];s=np.ones((20,4));m=fit(s,np.ones(20),rows)
    r=predict(m,.9,row(101),[25]*4,profile_table(rows,s))
    assert r['candidate']==.9 and r['correction']==0 and 'count_signal_outside_position_level_range' in r['reasons']


def test_sparse_joint_profile_falls_back_even_with_many_stage_people():
    rows=[row(i) for i in range(20)];s=np.ones((20,4));m=fit(s,np.ones(20),rows);t=row(101);t['sample_band']='25-299'
    assert predict(m,.5,t,[1]*4,profile_table(rows,s))['candidate']==.5


def test_future_evaluation_outcome_cannot_change_support_or_prediction():
    rows=[row(i) for i in range(20)];s=np.ones((20,4));m=fit(s,np.ones(20),rows);profiles=profile_table(rows,s)
    a=row(101);b=dict(a,quality_rate=1000.,window_end=2100)
    assert predict(m,.2,a,[1]*4,profiles)==predict(m,.2,b,[1]*4,profiles)


@pytest.mark.parametrize('kind',['held','immature','unknown','duplicate','overlap'])
def test_bad_residual_training_stops(kind):
    a=row(11);test=[row(20,2022)]
    rows=[a]
    if kind=='held':excluded=[1]
    else:excluded=[]
    if kind=='immature':rows=[dict(a,window_end=2026)]
    if kind=='unknown':rows=[dict(a,quality_rate=None)]
    if kind=='duplicate':rows=[a,a.copy()]
    if kind=='overlap':test=[dict(a,origin_year=2022)]
    with pytest.raises(ValueError):audit(rows,test,2022,excluded)


def test_repeated_rows_do_not_inflate_support_people():
    rows=[row(11,2016),row(11,2017)]
    r=audit(rows,[],2022,[],min_people=2)
    assert r['people']==1 and not r['fit_supported']


@pytest.mark.parametrize('signal',[[1,2],[1,float('nan'),2,3]])
def test_bad_signal_really_falls_back(signal):
    rows=[row(i) for i in range(20)];s=np.ones((20,4));m=fit(s,np.ones(20),rows)
    r=predict(m,1.,row(101),signal,profile_table(rows,s))
    assert r['candidate']==1. and 'missing_count_signal' in r['reasons']
