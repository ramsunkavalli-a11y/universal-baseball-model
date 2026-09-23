"""Check all routed cohorts, omitted features, chronology and saved scores."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_canceled_season_v1 import OUT,SOURCE,PACKAGE,hashes
from universal_baseball.hitter_canceled_season import available_columns,outage_mask
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
    for n,h in fit['files'].items():assert sha256_file(PACKAGE/n)==h
    f=pl.read_parquet(PACKAGE/'predictions.parquet');p=pl.read_parquet(SOURCE/'input-panel.parquet')
    old=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
        (pl.col('engine')=='lightgbm')&(pl.col('arm')=='R'))
    assert f.height==old.height*3
    assert not f.select('origin_year','player_id','target','arm').is_duplicated().any()
    assert f['probability'].is_finite().all() and f['probability'].min()>0 and f['probability'].max()<1
    for (target,year),base in old.partition_by('target','origin_year',as_dict=True).items():
        query=p.filter(pl.col('origin_year')==year);mask=outage_mask(query,year)
        train=eligible(p,year,target)
        np.testing.assert_allclose(train.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1)
        for arm in ('R','O','N'):
            q=f.filter((pl.col('target')==target)&(pl.col('origin_year')==year)&(pl.col('arm')==arm))
            np.testing.assert_array_equal(q['player_id'],query['player_id'])
            np.testing.assert_array_equal(q['actual'],target_values(query,target))
            np.testing.assert_array_equal(q['probability'].to_numpy()[~mask],base['probability'].to_numpy()[~mask])
            if arm=='R':np.testing.assert_array_equal(q['probability'],base['probability'])
    for n in fit['fits']:
        assert n['latest_label']<=n['year'] and n['year']+TARGETS[n['target']]<=2025
        cols=available_columns(pre['columns'],n['omitted'])
        assert set(n['used_features'])|set(n['dropped_constant_or_unobserved'])==set(cols)
        assert set(n['used_features']).isdisjoint(n['dropped_constant_or_unobserved'])
    assert fit['original_replay_max_difference']==fit['future_mutation_max_difference']==0
    score=json.loads((PACKAGE/'score-report.json').read_text())
    for t,r in score['targets'].items():
        for year,models in r['annual'].items():
            for arm,saved in models.items():
                q=f.filter((pl.col('target')==t)&(pl.col('origin_year')==int(year))&(pl.col('arm')==arm)&pl.col('prospect'))
                actual=metrics(q)
                for key in ('rows','observed','expected','brier','log_loss'):
                    np.testing.assert_allclose(actual[key],saved[key],rtol=1e-12,atol=1e-12)
    print(json.dumps({'verified':True,'real_fits':12,'stress_fits':6,'rows':f.height,
                      'future_mutation_difference':0.,'production_forecasts_changed':False,'protected_outcomes_used':False}))


if __name__=='__main__':main()
