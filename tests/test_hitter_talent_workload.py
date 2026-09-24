import numpy as np
import polars as pl
import pytest
from universal_baseball.hitter_talent_workload import pedigree_features,talent_training,fit_talent,PEDIGREE


def test_draft_cutoff_latest_and_unmatched():
    p=pl.DataFrame({'origin_year':[2010,2010,2014],'player_id':[1,2,1]})
    d=pl.DataFrame({'draft_year':[2009,2013,2026],'player_id':[1,1,2],
                    'pick_number':[10,20,1],'school_class':['HS','JR','HS']})
    f=pedigree_features(p,d)
    assert f['pedigree_matched'].to_list()==[1,0,1]
    assert f['pedigree_high_school'].to_list()==[1,None,0]
    assert f['pedigree_years_since'].to_list()==[1,None,1]
    assert f.equals(pedigree_features(p,d.filter(pl.col('draft_year')<2026)))
    assert f.filter(pl.col('player_id')==2)['pedigree_pick_quality'][0] is None


def test_no_draft_records():
    p=pl.DataFrame({'origin_year':[2009],'player_id':[1]})
    d=pl.DataFrame({'draft_year':[2025],'player_id':[1],'pick_number':[1],'school_class':['HS']})
    f=pedigree_features(p,d)
    assert f['pedigree_matched'][0]==0
    assert f[PEDIGREE[-1]][0] is None


def test_talent_maturity_and_canceled_window():
    p=pl.DataFrame({'origin_year':[2009,2010,2011,2017,2021], 'player_id':[1,1,1,2,3],
                    'pa_h3':[0.,100.,200.,50.,100.],'war_h3':[0.,1.,2.,1.,None]})
    f=talent_training(p,2021,3)
    assert f['origin_year'].to_list()==[2010,2011]
    assert f['identity_weight'].to_list()==[.5,.5]
    r,n=fit_talent(p,[],2021,3)
    assert np.isnan(r).all() and not n['supported'] and n['latest_label']==2014


def test_recursive_features_rejected():
    with pytest.raises(ValueError):fit_talent(pl.DataFrame(),['talent_rate_h1'],2021,1)
    with pytest.raises(ValueError):fit_talent(pl.DataFrame(),['war_h1'],2021,1)


def test_same_snapshot_label_not_training():
    p=pl.DataFrame({'origin_year':[2010,2011,2012], 'player_id':[1,1,1],
                    'pa_h1':[100.,200.,300.],'war_h1':[1.,2.,3.]})
    a=talent_training(p,2012,1)
    b=talent_training(p.with_columns(pl.when(pl.col('origin_year')==2012).then(999.).otherwise(pl.col('war_h1')).alias('war_h1')),2012,1)
    assert a.equals(b)
