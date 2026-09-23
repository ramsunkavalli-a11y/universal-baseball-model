import numpy as np
import polars as pl
from universal_baseball.hitter_structural_missingness import attach_outages,augmented_rows


def sample():
    return pl.DataFrame({'origin_year':[2018,2021,2022,2023],'player_id':[1,1,2,3],
        'prospect':[True,True,False,True],'missing_lag1':[1,1,1,0],'missing_lag2':[1,1,1,0],
        'identity_weight':[.5,.5,1.,1.],'ubb_rate_lag1':[None,None,None,.1],
        'ubb_rate_lag2':[None,None,None,.2],'ubb_rate_lag0':[.05,.15,.25,.35],
        'pa_h1':[0.,50.,600.,200.],'change__ubb_rate':[None,None,None,.2]})


def test_dated_flags_not_personal_absence():
    p=attach_outages(sample())
    assert p['structural_outage_lag1'].to_list()==[0,1,0,0]
    assert p['structural_outage_lag2'].to_list()==[0,0,0,0]


def test_snapshot_identity_and_outcome_mass_conserved():
    p=sample()
    for masked in (False,True):
        a=augmented_rows(p,masked)
        summed=a.group_by('origin_year','player_id').agg(pl.col('fit_weight').sum()).sort('origin_year')
        np.testing.assert_allclose(summed['fit_weight'],p['identity_weight'])
        np.testing.assert_allclose(a.group_by('player_id').agg(pl.col('fit_weight').sum()).sort('player_id')['fit_weight'],[1,1,1])
        np.testing.assert_allclose((a['pa_h1']*a['fit_weight']).sum(),(p['pa_h1']*p['identity_weight']).sum())
        assert a.group_by('origin_year','player_id').agg(pl.col('pa_h1').n_unique())['pa_h1'].max()==1
        assert a.group_by('origin_year','player_id').agg(pl.col('ubb_rate_lag0').n_unique())['ubb_rate_lag0'].max()==1


def test_duplicate_control_and_masked_changes():
    p=sample(); t=augmented_rows(p,False); a=augmented_rows(p,True)
    assert t.height==a.height==10
    assert t.filter(pl.col('origin_year')==2023)['ubb_rate_lag1'].null_count()==0
    assert a.filter(pl.col('origin_year')==2023)['ubb_rate_lag1'].null_count()==1
    assert a.filter(pl.col('origin_year')==2023)['ubb_rate_lag2'].null_count()==1
    assert a.filter(pl.col('origin_year')==2023)['change__ubb_rate'].null_count()==1
    assert a.filter(~pl.col('prospect')).height==1
