"""Verify archive bytes, chronology, matched arms, weights and scoring totals."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_detail_arrival_v1 import OUT,assemble,hashes,FOLDS,TARGETS
from report_hitter_detail_arrival_v1 import PACKAGE
from score_hitter_detail_arrival_v1 import metrics
from universal_baseball.hitter_detail_arrival import eligible,target_values
from universal_baseball.storage import sha256_file


def main():
    meta=json.loads((PACKAGE/'manifest.json').read_text())
    for p,h in meta['files'].items():assert sha256_file(PACKAGE/p)==h,p
    for p,h in meta['report_code'].items():assert sha256_file(Path(p))==h,p
    pre=json.loads((PACKAGE/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((PACKAGE/'fit-manifest.json').read_text())
    assert fit['prefit_sha256']==sha256_file(PACKAGE/'prefit-manifest.json')
    for p,h in fit['files'].items():assert sha256_file(PACKAGE/p)==h
    panel,arms,_=assemble();assert panel.equals(pl.read_parquet(OUT/'input-panel.parquet'))
    assert sha256_file(OUT/'input-panel.parquet')==pre['panel_sha256']
    f=pl.read_parquet(PACKAGE/'predictions.parquet')
    assert not f.select('origin_year','player_id','target','cold','engine','arm').is_duplicated().any()
    assert f['probability'].is_finite().all() and f['probability'].min()>0 and f['probability'].max()<1
    for year,target,cold in FOLDS:
        test=panel.filter(pl.col('origin_year')==year)
        train=eligible(panel,year,target,test['player_id'].to_list() if cold else ())
        assert train['origin_year'].max()+TARGETS[target]<=year and year+TARGETS[target]<=2025
        np.testing.assert_allclose(train.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1)
        if cold:assert not set(train['player_id'])&set(test['player_id'])
        subset=f.filter((pl.col('origin_year')==year)&(pl.col('target')==target)&(pl.col('cold')==cold))
        for (_,arm),g in subset.partition_by('engine','arm',as_dict=True).items():
            np.testing.assert_array_equal(g['player_id'],test['player_id'])
            np.testing.assert_array_equal(g['actual'],target_values(test,target))
        assert subset.height==test.height*(2 if cold else 8)
    assert len(fit['fits'])==102 and fit['future_mutation_maximum_difference']==0
    for n in fit['fits']:
        assert n['latest_label']<=n['origin']
        assert set(n['used_features']).isdisjoint(n['dropped_constant_or_unobserved'])
        assert set(n['used_features'])|set(n['dropped_constant_or_unobserved'])==set(arms[n['arm']])
        if TARGETS[n['target']]==3:
            assert n['training_current_context_rows']==0
            assert not any(c.startswith('context') for c in n['used_features'])
    report=json.loads((PACKAGE/'score-report.json').read_text())
    for target,r in report['targets'].items():
        g=f.filter((pl.col('target')==target)&~pl.col('cold')&~pl.col('pandemic')&pl.col('prospect')&(pl.col('arm')=='R')&(pl.col('engine')=='lightgbm'))
        actual=metrics(g);saved=r['groups']['prospects']['lightgbm/R']
        for k in ('rows','players','origins','observed','expected','brier','log_loss'):
            np.testing.assert_allclose(actual[k],saved[k],rtol=1e-12,atol=1e-12)
        if TARGETS[target]==3:assert not r['gates']['support']
    print(json.dumps({'verified':True,'fits':102,'prediction_rows':f.height,
        'production_forecasts_changed':False,'protected_outcomes_used':False}))


if __name__=='__main__':main()
