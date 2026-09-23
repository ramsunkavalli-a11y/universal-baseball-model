"""Verify weights, dates, targets and immutable experiment files."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_structural_missingness_v1 import OUT,SOURCE,PACKAGE,hashes
from universal_baseball.hitter_structural_missingness import augmented_rows,FLAGS
from universal_baseball.hitter_detail_arrival import eligible,target_values,TARGETS
from universal_baseball.storage import sha256_file
from score_hitter_detail_arrival_v1 import metrics


def main():
    meta=json.loads((PACKAGE/'manifest.json').read_text())
    for n,h in meta['files'].items():assert sha256_file(PACKAGE/n)==h
    for n,h in meta['code'].items():assert sha256_file(Path(n))==h
    pre=json.loads((PACKAGE/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((PACKAGE/'fit-manifest.json').read_text())
    assert fit['prefit_sha256']==sha256_file(PACKAGE/'prefit-manifest.json')
    assert fit['prediction_sha256']==sha256_file(PACKAGE/'predictions.parquet')
    p=pl.read_parquet(SOURCE/'input-panel.parquet');f=pl.read_parquet(PACKAGE/'predictions.parquet')
    assert not f.select('origin_year','player_id','target','arm').is_duplicated().any()
    assert f['probability'].is_finite().all() and f['probability'].min()>0 and f['probability'].max()<1
    for n in fit['fits']:
        assert n['latest_label']<=n['year'] and n['year']+TARGETS[n['target']]<=2025
        np.testing.assert_allclose(n['augmented_weight_sum'],n['original_weight_sum'])
        np.testing.assert_allclose(n['normalized_weight_sum'],n['training_rows'])
        assert set(n['used_features'])|set(n['dropped_constant_or_unobserved'])==set(pre['columns']+FLAGS)
    for (target,year),g in f.partition_by('target','origin_year',as_dict=True).items():
        test=p.filter(pl.col('origin_year')==year);train=eligible(p,year,target)
        # Recompute conservation on the actual full-size augmentation.
        augmented=augmented_rows(train,True)
        joined=train.select('origin_year','player_id','identity_weight').join(
            augmented.group_by('origin_year','player_id').agg(pl.col('fit_weight').sum()),
            on=['origin_year','player_id'],validate='1:1')
        assert joined.height==train.height
        np.testing.assert_allclose(joined['identity_weight'],joined['fit_weight'])
        base_y=target_values(train,target);aug_y=target_values(augmented,target)
        np.testing.assert_allclose(np.dot(base_y,train['identity_weight']),np.dot(aug_y,augmented['fit_weight']))
        for (arm,),q in g.partition_by('arm',as_dict=True).items():
            np.testing.assert_array_equal(q['player_id'],test['player_id'])
            np.testing.assert_array_equal(q['actual'],target_values(test,target))
    assert fit['future_mutation_max_difference']==0
    s=json.loads((PACKAGE/'score-report.json').read_text())
    for target,r in s['targets'].items():
        for arm,saved in r['prospects'].items():
            actual=metrics(f.filter((pl.col('target')==target)&(pl.col('arm')==arm)&pl.col('prospect')))
            for k in ('rows','observed','expected','brier','log_loss'):
                np.testing.assert_allclose(actual[k],saved[k],rtol=1e-12,atol=1e-12)
        if TARGETS[target]==3:assert not r['gates']['sufficient_origins']
    print(json.dumps({'verified':True,'fits':len(fit['fits']),'rows':f.height,'weight_conservation':True,
                      'future_mutation_difference':0.,'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
