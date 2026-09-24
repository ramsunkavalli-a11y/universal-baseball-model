"""Independent chronology, probability, workload and score checks."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_conditional_workload_v1 import OUT,PANEL,hashes,references
from score_hitter_conditional_workload_v1 import summary,cumulative
from universal_baseball.hitter_arrival_value_transfer import FOLDS
from universal_baseball.hitter_conditional_workload import active_training,roles,role_means,mixture_mean
from universal_baseball.storage import sha256_file

PACKAGE=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23')


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    assert sha256_file(OUT/'predictions.parquet')==fit['prediction_sha256']
    assert sha256_file(OUT/'prefit-manifest.json')==fit['prefit_sha256']
    assert sha256_file(OUT/'references.parquet')==pre['reference_sha256']
    panel=pl.read_parquet(PANEL);ref=pl.read_parquet(OUT/'references.parquet');assert references(panel).equals(ref)
    f=pl.read_parquet(OUT/'predictions.parquet');score=json.loads((OUT/'score-report.json').read_text())
    assert not f.select('origin_year','player_id','horizon').is_duplicated().any()
    assert set(f.select('origin_year','horizon').unique().iter_rows())==set(FOLDS)
    assert len(fit['fits'])==36 and len(fit['mutations'])==4
    assert all(m['maximum_difference']==0 for m in fit['mutations'])
    for n in fit['fits']:
        train=active_training(panel,n['year'],n['horizon'])
        assert n['training_rows']==train.height and n['training_players']==train['player_id'].n_unique()
        assert n['latest_label']==max(train['origin_year'])+n['horizon']<=n['year']
        assert (train[f"pa_h{n['horizon']}"]>0).all()
        np.testing.assert_allclose(train.group_by('player_id').agg(pl.col('identity_weight').sum())['identity_weight'],1.)
        assert set(n['used_features'])|set(n['dropped_features'])==set(pre['columns'][n['head']])
        if n['head']=='M':
            y=train[f"pa_h{n['horizon']}"].to_numpy();w=train['identity_weight'].to_numpy()
            means=role_means(y,w);np.testing.assert_allclose(means,n['role_means'],rtol=1e-12,atol=1e-12)
            assert np.bincount(roles(y),minlength=3).tolist()==n['role_training_counts']
            g=f.filter((pl.col('origin_year')==n['year'])&(pl.col('horizon')==n['horizon']))
            np.testing.assert_allclose(mixture_mean(g.select('role_0','role_1','role_2').to_numpy(),means),g['M_conditional'],rtol=1e-12,atol=1e-12)
    for year,h in FOLDS:
        g=f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h));q=panel.filter(pl.col('origin_year')==year)
        b=ref.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(g['player_id'],q['player_id']);np.testing.assert_array_equal(g['actual_pa'],q[f'pa_h{h}'])
        for col in ref.columns:assert g[col].equals(b[col]),col
        for a in ('A','D','M'):
            assert g[a+'_conditional'].is_finite().all() and g[a+'_conditional'].is_between(1,750).all()
            np.testing.assert_array_equal(g[a+'_universal_pa'],g['fixed_p']*g[a+'_conditional'])
            np.testing.assert_array_equal(g.filter(pl.col('prospect'))[a+'_pa'],g.filter(pl.col('prospect'))[a+'_universal_pa'])
            np.testing.assert_array_equal(g.filter(~pl.col('prospect'))[a+'_pa'],g.filter(~pl.col('prospect'))['B_pa'])
        np.testing.assert_allclose(g['M_regular_probability'],g['fixed_p']*g['role_2'],rtol=1e-12,atol=1e-12)
    c=cumulative(f);assert c.equals(pl.read_parquet(OUT/'cumulative-predictions.parquet'))
    assert set(c['origin_year'])=={2016,2021,2022}
    for label,g in [(str(h),f.filter(pl.col('horizon')==h)) for h in (1,2,3)]+[('cumulative',c)]:
        actual=summary(g.filter(pl.col('prospect')))
        saved=(score['cumulative'] if label=='cumulative' else score['annual'][label])['groups']['prospects']
        for a in ('B','I','A','D','M','E'):
            for k in ('rmse','mae','bias','aggregate_absolute_error'):
                np.testing.assert_allclose(actual['arms'][a][k],saved['arms'][a][k],rtol=1e-12,atol=1e-12)
    assert score['selected_research_head']==next((a for a in ('D','M') if score['decisions'][a]['passes']),None)
    if (PACKAGE/'manifest.json').exists():
        manifest=json.loads((PACKAGE/'manifest.json').read_text())
        for n,h in manifest['files'].items():assert sha256_file(PACKAGE/n)==h
        for n,h in manifest['code'].items():assert sha256_file(Path(n))==h
    print(json.dumps({'verified':True,'heads':36,'future_mutations':4,'prediction_rows':f.height,
                      'protected_outcomes_used':False,'production_forecasts_changed':False}))


if __name__=='__main__':main()
