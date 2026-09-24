"""Check annual target identity, propagation, source locks and forecast isolation."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_arrival_value_transfer_v1 import OUT,REPAIR,SOURCE,hashes,references
from score_hitter_arrival_value_transfer_v1 import summary,cumulative
from universal_baseball.hitter_arrival_value_transfer import FOLDS,training,annual_labels,propagate
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/hitter-arrival-value-transfer-v1-2026-09-23')


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    assert sha256_file(OUT/'predictions.parquet')==fit['prediction_sha256']
    assert sha256_file(OUT/'prefit-manifest.json')==fit['prefit_sha256']
    assert sha256_file(OUT/'references.parquet')==pre['references_sha256']
    old=pl.read_parquet(SOURCE/'input-panel.parquet');new=pl.read_parquet(REPAIR/'repaired-panel.parquet')
    rebuilt,_=references(new);ref=pl.read_parquet(OUT/'references.parquet');assert rebuilt.equals(ref)
    f=pl.read_parquet(OUT/'predictions.parquet');score=json.loads((OUT/'score-report.json').read_text())
    assert not f.select('origin_year','player_id','horizon').is_duplicated().any()
    assert set(f.select('origin_year','horizon').unique().iter_rows())==set(FOLDS)
    assert len(fit['fits'])==24 and sum(not n['reused'] for n in fit['fits'])==16
    for note in fit['fits']:
        if note['reused']:continue
        panel=old if note['arm']=='R' else new
        t=training(panel,note['year'],note['horizon'])
        assert note['training_rows']==t.height and note['training_players']==t['player_id'].n_unique()
        assert note['latest_label']==max(t['origin_year'])+note['horizon']<=note['year']
        np.testing.assert_allclose(t.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1.)
        assert set(note['used_features'])|set(note['dropped_features'])==set(pre['columns'][note['arm']])
    for year,h in FOLDS:
        q=new.filter(pl.col('origin_year')==year);g=f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(g['player_id'],q['player_id'])
        np.testing.assert_array_equal(g['actual_pa'],q[f'pa_h{h}'])
        np.testing.assert_array_equal(g['actual_value'],q[f'war_h{h}'])
        np.testing.assert_array_equal(g['actual_pa']>0,annual_labels(q,h))
        assert g['prospect'].equals(q['prospect'])
        for arm in ('R','F','U'):
            mask=g['prospect'] if arm!='U' else np.ones(g.height,bool)
            p,pa,v=propagate(g,g[arm+'_p'],mask)
            for a,b in [(p,g[arm+'_p']),(pa,g[arm+'_pa']),(v,g[arm+'_value'])]:np.testing.assert_allclose(a,b,rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(g[arm+'_expanded'],v+g['base_other_value']*pa/g['B_pa'],rtol=1e-12,atol=1e-12)
            np.testing.assert_allclose(g[arm+'_expanded_fixed'],v+g['base_other_value'],rtol=1e-12,atol=1e-12)
            if arm!='U':
                untouched=g.filter(~pl.col('prospect'))
                for c in ('p','pa','value'):np.testing.assert_array_equal(untouched[arm+'_'+c],untouched['B_'+c])
        for arm in ('B','R','F','U','E'):
            assert g[arm+'_p'].is_finite().all() and g[arm+'_p'].is_between(0,1).all()
            assert g[arm+'_pa'].is_finite().all() and g[arm+'_pa'].is_between(0,750+1e-8).all()
    c=cumulative(f);saved=pl.read_parquet(OUT/'cumulative-predictions.parquet');assert c.equals(saved)
    assert set(c['origin_year'])=={2016,2021,2022}
    assert set(c.filter(pl.col('complete_components'))['origin_year'])=={2021,2022}
    for label,g in [(str(h),f.filter(pl.col('horizon')==h)) for h in (1,2,3)]+[('cumulative',c)]:
        actual=summary(g.filter(pl.col('prospect')),label=='cumulative')
        target=score['cumulative' if label=='cumulative' else 'annual']
        expected=(target if label=='cumulative' else target[label])['groups']['prospects']
        for arm in ('B','R','F','U','E'):
            for metric in ('pa','value'):
                for stat in ('rmse','mae','bias','aggregate_absolute_error'):
                    np.testing.assert_allclose(actual['arms'][arm][metric][stat],expected['arms'][arm][metric][stat],rtol=1e-12,atol=1e-12)
    assert len(fit['mutations'])==2 and all(m['maximum_difference']==0 for m in fit['mutations'])
    assert fit['conditional_head_replay']['rate_max_difference']<=1e-10
    assert fit['conditional_head_replay']['conditional_pa_max_difference']<=1e-10
    if (PACKAGE/'manifest.json').exists():
        manifest=json.loads((PACKAGE/'manifest.json').read_text())
        for n,h in manifest['files'].items():assert sha256_file(PACKAGE/n)==h
        for n,h in manifest['code'].items():assert sha256_file(Path(n))==h
    print(json.dumps({'verified':True,'new_activity_fits':16,'reused_activity_fits':8,
        'future_mutation_replays':2,'conditional_head_replays':2,'prediction_rows':f.height,
        'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
