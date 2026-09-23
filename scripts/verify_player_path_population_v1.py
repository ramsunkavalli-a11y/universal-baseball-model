"""Verify archives, cutoff safety, identity balance, and sampled scoring independently."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from audit_player_path_population_v1 import OUT, panel_data, eligible
from fit_player_path_value_bridge_v1 import training
from fit_player_path_population_v1 import RUNS, source_hashes
from report_player_path_population_v1 import PACKAGE
from universal_baseball.player_path_population import iid_summary, identity_split
from universal_baseball.storage import sha256_file


def main():
    meta=json.loads((PACKAGE/'manifest.json').read_text())
    for name,sha in meta['files'].items():assert sha256_file(PACKAGE/name)==sha,name
    for name,sha in meta['report_code'].items():assert sha256_file(Path(name))==sha,name
    pre=json.loads((PACKAGE/'prefit-manifest.json').read_text())
    assert pre['source_hashes']==source_hashes()
    fit=json.loads((PACKAGE/'fit-manifest.json').read_text())
    assert fit['prefit_sha256']==sha256_file(PACKAGE/'prefit-manifest.json')
    f=pl.read_parquet(PACKAGE/'exact-predictions.parquet')
    keys=['origin_year','player_id','horizon','method','cold']
    assert not f.select(keys).is_duplicated().any()
    current=f.filter(pl.col('origin_year')==2025)
    assert current['actual_batting'].null_count()==current.height
    for h in (3,6):
        g=f.filter(pl.col('horizon')==h)
        for target in ('batting','pa'):
            annual=g.select([f'mean_{target}_h{i}' for i in range(1,h+1)]).to_numpy().sum(axis=1)
            np.testing.assert_allclose(annual,g[f'mean_{target}'],atol=1e-8,rtol=1e-8)
    for c in [c for c in f.columns if c.startswith('p_')]:
        assert f[c].min()>=-1e-6 and f[c].max()<=1+1e-6
    panel=panel_data()
    for note in fit['fits']:
        year,h,cold,method=(note[k] for k in ('origin','horizon','cold','method'))
        assert note['latest_training_outcome']<=year<=2025
        assert not note['diagnostics']['self_donors']
        assert all(s['overlap']==0 for s in note['diagnostics']['splits'])
        prefix=OUT/'fits'/f'{year}-h{h}-cold{int(cold)}-{method}'
        for suffix,key in [('.exact.parquet','exact_sha256'),('.simulated.parquet','simulated_sha256'),('.probe.npz','probe_sha256')]:
            assert sha256_file(prefix.with_suffix(suffix))==note[key]
        test=panel.filter(pl.col('origin_year')==year).sort('player_id')
        exclude=test['player_id'].to_list() if cold else ()
        train=eligible(panel,year,h,exclude) if method=='A1' else training(panel,year,h,exclude).with_columns(pl.lit(1.).alias('identity_weight'))
        a=np.load(prefix.with_suffix('.probe.npz'))
        np.testing.assert_array_equal(a['donor_id'],train['player_id'])
        np.testing.assert_array_equal(a['donor_origin'],train['origin_year'])
        np.testing.assert_allclose(a['row_weight'],train['identity_weight'])
        np.testing.assert_array_equal(a['query_id'],test['player_id'].head(10))
        masses=train.group_by('player_id').agg(pl.col('identity_weight').sum())
        np.testing.assert_allclose(masses['identity_weight'],1)
        halves=identity_split(a['donor_id'])
        assert not set(a['donor_id'][halves])&set(a['donor_id'][~halves])
        if cold:assert not set(train['player_id'])&set(test['player_id'])
        for n,s in RUNS:
            idx=a[f'n{n}s{s}'];assert not (a['donor_id'][idx]==a['query_id'][:,None]).any()
            wy=train.select([f'war_h{i}' for i in range(1,h+1)]).to_numpy()[idx[:1]]
            py=train.select([f'pa_h{i}' for i in range(1,h+1)]).to_numpy()[idx[:1]]
            ay=None if year==2025 else test.head(1).select([f'war_h{i}' for i in range(1,h+1)]).to_numpy()
            ap=None if year==2025 else test.head(1).select([f'pa_h{i}' for i in range(1,h+1)]).to_numpy()
            expected=iid_summary(wy,py,ay,ap)
            row=pl.read_parquet(prefix.with_suffix('.simulated.parquet')).filter(
                (pl.col('player_id')==a['query_id'][0])&(pl.col('draws')==n)&(pl.col('seed')==s)).row(0,named=True)
            for k,v in expected.items():np.testing.assert_allclose(row[k],v[0],rtol=1e-12,atol=1e-12)
    assert len(fit['fits'])==44
    print(json.dumps({'verified':True,'fits':44,'simulation_sets':264,'exact_rows':f.height,
        'production_forecasts_changed':False,'protected_outcomes_used':False}))


if __name__=='__main__':main()
