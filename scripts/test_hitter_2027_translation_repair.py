"""One fixed reliability repair on saved chronological/player-held folds."""
from pathlib import Path
import json

import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_translation_reliability import reliable_translation
from universal_baseball.storage import sha256_file
from prepare_practical_hitter_v33 import safe_matrix
from fit_practical_hitter_v31 import weights
from capture_hitter_2027_origin_counts import ROOT, write_once

OLD=ROOT/'reports/generated/hitter-talent-bridge-v74'
OUT=ROOT/'reports/generated/hitter-2027-translation-repair'
PUBLIC=ROOT/'reports/model-evidence/hitter-2027-v1'
CONTRACT=ROOT/'docs/hitter-2027-small-sample-repair-contract.md'


def read(p):
    return json.loads(p.read_text(encoding='utf8'))


def profile(f):
    return f.with_columns((pl.col('age')//5).cast(pl.Int64).alias('age_band'),
        pl.when(pl.col('translation_supported_pa')<50).then(0)
          .when(pl.col('translation_supported_pa')<200).then(1)
          .when(pl.col('translation_supported_pa')<600).then(2).otherwise(3).alias('exposure_band'))


def check_sources(pre):
    for k in range(5):
        path=OLD/f'features-{k}.parquet'
        assert sha256_file(path)==pre['input_hashes'][str(path)]
        note=read(OLD/f'translation-{k}.json')
        assert note['features_sha256']==sha256_file(path)
        assert all(g['held_fold']==k and g['max_source_year']<=g['cutoff'] for g in note['graphs'])


def prepare(pre,names):
    checks=[];supports=[]
    for k in range(5):
        f=pl.read_parquet(OLD/f'features-{k}.parquet');candidate=reliable_translation(f)
        for cell in [c for c in pre['cells'] if c['fold']==k]:
            tr=candidate.filter(pl.col('row_id').is_in(cell['training_row_ids'])&(pl.col('next_pa')>0))
            te=candidate.filter(pl.col('row_id').is_in(cell['test_row_ids']))
            support,note=preflight(tr,te,cutoff=cell['year'],fold=k,features=names,
                expected_keys=te.select('row_id','horizon').iter_rows())
            keys=['stage','prior_debut','age_band','exposure_band']
            tally=profile(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_people'))
            extra=profile(te).select('row_id',*keys).join(tally,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_people').fill_null(0))
            supports.append(support.join(extra,on='row_id',how='left',validate='1:1',suffix='_reliability').with_columns(pl.lit(k).alias('fold')))
            x=safe_matrix(tr,names); tx=safe_matrix(te,names)
            checks.append(dict(year=cell['year'],fold=k,**note,
                exposure_profile_unseen=int((extra['profile_people']==0).sum()),
                exposure_profile_sparse=int((extra['profile_people']<20).sum()),
                active_training_rows=tr.height,active_training_people=tr['player_id'].n_unique(),
                feature_outside_training={n:int(((tx[:,i]<x[:,i].min())|(tx[:,i]>x[:,i].max())).sum()) for i,n in enumerate(names)},
                training_row_ids=tr.sort('row_id')['row_id'].to_list(),test_row_ids=te.sort('row_id')['row_id'].to_list()))
        print(f'Preflight: held-player fold {k}',flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    path=OUT/'support.parquet'
    assert not path.exists()
    pl.concat(supports,how='diagonal_relaxed').write_parquet(path)
    write_once(OUT/'preflight.json',dict(before_fitting=True,contract_sha256=sha256_file(CONTRACT),
        runner_sha256=sha256_file(Path(__file__)),module_sha256=sha256_file(ROOT/'src/universal_baseball/hitter_translation_reliability.py'),
        old_preflight_sha256=sha256_file(OLD/'preflight.json'),support_sha256=sha256_file(path),
        features=names,cells=checks,source_2026_used=False))


def error_metrics(actual,predicted,w):
    if not len(actual) or np.sum(w)<=0:
        return None
    err=predicted-actual
    return dict(rmse=float(np.sqrt(np.average(err*err,weights=w))),
                mae=float(np.average(np.abs(err),weights=w)),bias=float(np.average(err,weights=w)))


def score(q):
    scopes=[('all',q),('never_debut',q.filter(pl.col('prior_debut')==0))]
    never=scopes[-1][1]
    scopes.extend((stage,never.filter(pl.col('stage')==stage)) for stage in sorted(never['stage'].unique()))
    scopes.extend((f'never_origin_{year}',never.filter(pl.col('origin_year')==year)) for year in sorted(never['origin_year'].unique()))
    scopes.extend((f'never_exposure_{b}',never.filter(pl.col('exposure_band')==b)) for b in range(4))
    results=[]
    for name,f in scopes:
        if f.is_empty():continue
        active=f.filter(pl.col('next_pa')>0); rows={}
        for arm in ['baseline','candidate']:
            rows[arm]=dict(
                relative_rate_pa_weighted=error_metrics(active['actual_relative_rate'].to_numpy(),active[arm+'_rate'].to_numpy(),active['next_pa'].to_numpy()),
                relative_rate_unweighted=error_metrics(active['actual_relative_rate'].to_numpy(),active[arm+'_rate'].to_numpy(),np.ones(len(active))),
                common_origin_rate_sensitivity=error_metrics(active['actual_common_rate'].to_numpy(),active[arm+'_rate'].to_numpy(),active['next_pa'].to_numpy()),
                delivered_value=error_metrics(f['next_value'].to_numpy(),f[arm+'_value'].to_numpy(),np.ones(len(f))),
                forecast_value_total=float(f[arm+'_value'].sum()))
        results.append(dict(scope=name,rows=len(f),measured_rate_rows=len(active),actual_value_total=float(f['next_value'].sum()),scores=rows))
    # Fixed-seed player-cluster uncertainty, descriptive development evidence.
    active=never.filter(pl.col('next_pa')>0)
    people=active.group_by('player_id').agg(pl.col('next_pa').sum().alias('w'),
        *[((pl.col(arm+'_rate')-pl.col('actual_relative_rate'))**2*pl.col('next_pa')).sum().alias(arm+'_sse') for arm in ['baseline','candidate']])
    rng=np.random.default_rng(20271008);differences=[]
    arrays=people.select('w','baseline_sse','candidate_sse').to_numpy()
    for _ in range(1000):
        totals=arrays[rng.integers(0,len(arrays),len(arrays))].sum(0)
        differences.append(float(np.sqrt(totals[2]/totals[0])-np.sqrt(totals[1]/totals[0])))
    return dict(scopes=results,paired_rate_rmse_delta_interval_95=np.quantile(differences,[.025,.975]).tolist(),
                bootstrap_people=len(people),bootstrap_replicates=1000)


def main():
    pre=read(OLD/'preflight.json'); names=pre['features']['translated_ridge'];check_sources(pre)
    if (OUT/'predictions.parquet').exists():raise ValueError('Preserve completed comparison')
    if not (OUT/'preflight.json').exists():prepare(pre,names)
    locked=read(OUT/'preflight.json')
    assert locked['contract_sha256']==sha256_file(CONTRACT)
    assert locked['runner_sha256']==sha256_file(Path(__file__))
    assert locked['module_sha256']==sha256_file(ROOT/'src/universal_baseball/hitter_translation_reliability.py')
    assert locked['old_preflight_sha256']==sha256_file(OLD/'preflight.json')
    anchor=pl.read_parquet(OLD/'scored-predictions.parquet');predictions=[];receipts=[]
    columns=['row_id','player_id','player_name','origin_year','target_year','outer_fold','prior_debut','stage',
             'age','pa_0','minor_pa_0','next_pa','next_value','preseason_pa','origin_replacement_rate',
             'translated_ridge_rate','translated_ridge_all_rate','translated_ridge_value']
    with threadpool_limits(limits=2):
        for k in range(5):
            f=pl.read_parquet(OLD/f'features-{k}.parquet');candidate=reliable_translation(f)
            for cell in [c for c in locked['cells'] if c['fold']==k]:
                y=cell['year'];tr=candidate.filter(pl.col('row_id').is_in(cell['training_row_ids'])).sort('row_id')
                te=f.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
                tc=candidate.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
                q=anchor.filter(pl.col('row_id').is_in(cell['test_row_ids'])).sort('row_id')
                assert q['row_id'].equals(te['row_id'])
                old_head=next(h for h in read(OLD/f'fit-{y}-{k}.json')['heads'] if h['arm']=='translated_ridge')
                assert sha256_file(Path(old_head['path']))==old_head['sha256']
                old_model=joblib.load(old_head['path'])
                assert np.allclose(old_model.predict(safe_matrix(te,names)),q['translated_ridge_all_rate'],atol=1e-10,rtol=0)
                w=weights(tr)*tr['next_pa'].to_numpy(); w*=len(w)/w.sum()
                model=Ridge(alpha=100).fit(safe_matrix(tr,names),tr['next_batting_rate'].to_numpy(),sample_weight=w)
                raw=model.predict(safe_matrix(tc,names));assert np.isfinite(raw).all()
                pred=np.where(q['prior_debut'].to_numpy()==0,raw,q['translated_ridge_rate'].to_numpy())
                result=q.select(columns).with_columns(
                    pl.col('translated_ridge_rate').alias('baseline_rate'),pl.col('translated_ridge_value').alias('baseline_value'),
                    pl.Series('candidate_rate',pred),pl.Series('candidate_raw_rate',raw),
                    pl.Series('actual_relative_rate',te['next_batting_rate'].to_numpy()),
                    pl.Series('actual_common_rate',q['next_batting_rate'].to_numpy()),
                    pl.Series('translation_supported_pa',te['translation_supported_pa'].to_numpy()),
                    pl.Series('translated_reliability',te['translated_reliability'].to_numpy()))
                result=result.with_columns((pl.col('preseason_pa')*(pl.col('candidate_rate')/600+pl.col('origin_replacement_rate'))).alias('candidate_value'))
                path=OUT/f'ridge-{y}-{k}.joblib';assert not path.exists();joblib.dump(model,path,compress=3)
                receipts.append(dict(year=y,fold=k,model_path=str(path),sha256=sha256_file(path),baseline_replayed=True,
                    training_rows=len(tr),training_people=tr['player_id'].n_unique(),coefficient_norm=float(np.linalg.norm(model.coef_))))
                predictions.append(profile(result))
            print(f'Fitted/replayed historical fold {k}',flush=True)
    result=pl.concat(predictions).sort('row_id')
    assert len(result)==len(anchor) and result['row_id'].equals(anchor.sort('row_id')['row_id'])
    result.write_parquet(OUT/'predictions.parquet')
    write_once(OUT/'fits.json',dict(heads=receipts,predictions_sha256=sha256_file(OUT/'predictions.parquet')))
    write_once(PUBLIC/'translation-repair-provisional-scores.json',dict(**score(result),
        status='provisional_pending_player_walkthrough',predictive_disposition=None,
        source_2026_used=False,forecast_changed=False,contract_sha256=sha256_file(CONTRACT),
        preflight_sha256=sha256_file(OUT/'preflight.json')))
    print('35 fixed fits complete; no disposition before player walkthrough',flush=True)


if __name__=='__main__':main()
