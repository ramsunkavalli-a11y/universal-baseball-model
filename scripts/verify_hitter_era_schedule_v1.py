"""Verify locked sources, correct folds, targets, scores and schedule attachment."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_era_schedule_v1 import OUT,PACKAGE,SOURCE,hashes
from universal_baseball.hitter_detail_arrival import eligible,target_values
from universal_baseball.hitter_schedule_opportunity import attach_schedule,restrict_training,FEATURES
from universal_baseball.storage import sha256_file
from score_hitter_detail_arrival_v1 import metrics


def main():
    meta=json.loads((PACKAGE/'manifest.json').read_text())
    for n,h in meta['files'].items(): assert sha256_file(PACKAGE/n)==h
    for n,h in meta['code'].items(): assert sha256_file(Path(n))==h
    pre=json.loads((PACKAGE/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((PACKAGE/'fit-manifest.json').read_text())
    assert fit['prediction_sha256']==sha256_file(PACKAGE/'predictions.parquet')
    assert fit['prefit_sha256']==sha256_file(PACKAGE/'prefit-manifest.json')
    audit=json.loads((PACKAGE/'schedule-audit.json').read_text())
    for n,h in audit['sources'].items():assert sha256_file(Path(n))==h
    assert audit['feature_hash']==sha256_file(PACKAGE/'schedule-features.parquet')
    assert audit['team_hash']==sha256_file(PACKAGE/'team-schedules.parquet')
    sf=pl.read_parquet(PACKAGE/'schedule-features.parquet')
    assert sf['season'].max()<=2024
    assert sf[FEATURES[0]].is_between(0.,1.).all()
    partial=sf.filter(pl.col(FEATURES[0])<1)
    assert partial[FEATURES[1]].null_count()==partial.height
    assert partial[FEATURES[2]].null_count()==partial.height
    p=attach_schedule(pl.read_parquet(SOURCE/'input-panel.parquet'),sf)
    f=pl.read_parquet(PACKAGE/'predictions.parquet')
    assert not f.select('origin_year','player_id','target','arm').is_duplicated().any()
    assert f['probability'].is_finite().all() and f['probability'].is_between(1e-6,1-1e-6).all()
    assert f['origin_year'].max()<=2024 and set(f['target'])=={'next_year'}
    for note in fit['fits']:
        train=eligible(p,note['year'],'next_year')
        if note['arm'] in ('S0','S1'):train=restrict_training(train)
        assert note['training_rows']==train.height
        assert note['training_origins']==sorted(train['origin_year'].unique().to_list())
        assert max(note['training_origins'])+1<=note['year']
        used=note['used_features'];assert 'reorganization_era' not in used
        if note['arm'] in ('S0','S1'):
            assert min(note['training_origins'])>=2015
            np.testing.assert_allclose(train.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1.)
        if note['arm']=='S0':assert not set(used)&set(FEATURES)
        if note['arm']=='S1':assert set(used)&set(FEATURES)
    for (year,arm),g in f.partition_by('origin_year','arm',as_dict=True).items():
        query=p.filter(pl.col('origin_year')==year)
        np.testing.assert_array_equal(g['player_id'],query['player_id'])
        np.testing.assert_array_equal(g['actual'],target_values(query,'next_year'))
    # Before any mature modern origin, the era field is constant and was already
    # dropped by the original fit. Removing it must therefore be an exact replay.
    for year in (2017,2018,2021):
        for new,old in [('E','R'),('AE','A')]:
            a=f.filter((pl.col('origin_year')==year)&(pl.col('arm')==new))
            b=f.filter((pl.col('origin_year')==year)&(pl.col('arm')==old))
            np.testing.assert_array_equal(a['player_id'],b['player_id'])
            np.testing.assert_array_equal(a['probability'],b['probability'])
    assert len(fit['fits'])==20 and len(fit['mutations'])==2
    assert all(x['max_difference']==0 for x in fit['mutations'])
    score=json.loads((PACKAGE/'score-report.json').read_text())
    for year,arms in score['annual'].items():
        for arm,saved in arms.items():
            actual=metrics(f.filter((pl.col('origin_year')==int(year))&(pl.col('arm')==arm)&pl.col('prospect')))
            for k in ('rows','observed','expected','brier','log_loss'):
                np.testing.assert_allclose(actual[k],saved[k],rtol=1e-12,atol=1e-12)
    print(json.dumps({'verified':True,'fits':20,'mutation_replays':2,'rows':f.height,
                      'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
