"""One declared expected-PA objective contrast with exact inherited membership."""
from pathlib import Path
import json
import joblib
import numpy as np
import polars as pl
import sklearn
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
import evaluate_hitter_retirement_v44 as r

ROOT=r.ROOT;OUT=ROOT/'reports/generated/practical-hitter-poisson-v45';BASE=ROOT/'reports/generated/practical-hitter-v38'
FIXED=[(701762,2024),(683011,2022),(592450,2016),(592450,2024),(667670,2022),(405395,2021)]


def write(n,o):(OUT/n).write_text(json.dumps(o,indent=2,default=str,allow_nan=False),encoding='utf8')


def prepare():
    assert r.read(r.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists();OUT.mkdir(parents=True,exist_ok=True)
    old=r.read(BASE/'preflight.json');source=pl.read_parquet(BASE/'features.parquet');pred=pl.read_parquet(r.OUT/'predictions.parquet')
    cells=[];supports=[]
    for c in old['cells']:
        tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids']))
        sp,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=old['features'],expected_keys=te.select('row_id','horizon').iter_rows())
        supports.append(sp.with_columns(pl.lit(c['year']).alias('fit_year'),pl.lit(c['fold']).alias('fit_fold')))
        assert tr['next_pa'].min()>=0 and tr['next_pa'].sum()>0 and tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
        assert not set(tr['player_id'])&set(te['player_id']) and np.isfinite(tr.select(old['features']).to_numpy()).all()
        cells.append(dict(**c,objective_preflight=note))
    for pid,y in FIXED:assert len(pred.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)))==1
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    profile_path=ROOT/'reports/generated/practical-hitter-joint-forest-v43/support.parquet'
    paths=[BASE/'preflight.json',BASE/'features.parquet',profile_path,OUT/'support.parquet',BASE/'predictions.parquet',r.OUT/'predictions.parquet',r.OUT/'report.json',
        Path(__file__),ROOT/'docs/practical-hitter-poisson-v45-contract.md',ROOT/'scripts/fit_practical_hitter_v31.py',ROOT/'src/universal_baseball/histogram_log_prediction_trace.py']
    settings=dict(loss='poisson',max_iter=250,max_depth=3,min_samples_leaf=30,learning_rate=.05,l2_regularization=10,
        early_stopping=False,random_state=31)
    write('preflight.json',dict(before_fitting=True,features=old['features'],cells=cells,settings=settings,
        sklearn_version=sklearn.__version__,input_hashes={str(p):sha256_file(p) for p in paths},
        support_path=str(OUT/'support.parquet'),source_profile_support_path=str(profile_path),source_eligibility_qualified=True,protected_outcomes_used=False))
    print('35 exact cells ready; fixed 239 game/count inputs and existing retirement policy.',flush=True)


def fit():
    pre=r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(BASE/'features.parquet');base=pl.read_parquet(r.OUT/'predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];forecast=OUT/f'forecast-{y}-{k}.parquet';note=OUT/f'fit-{y}-{k}.json'
            if forecast.exists():
                n=r.read(note);assert sha256_file(forecast)==n['prediction_sha256'] and sha256_file(Path(n['path']))==n['sha256'];fits.append(n);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id'])
            old_model=joblib.load(r.read(BASE/f'fit-{y}-{k}.json')['path']);assert old_model.loss=='squared_error'
            old_params=old_model.get_params();assert all(old_params[a]==v for a,v in pre['settings'].items() if a!='loss')
            model=HistGradientBoostingRegressor(**pre['settings']);model.fit(tr.select(pre['features']).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
            raw=model.predict(te.select(pre['features']).to_numpy());p=np.clip(raw,0,800)
            p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
            assert np.isfinite(raw).all() and (raw>=0).all()
            q=q.with_columns(pl.Series('poisson_raw_pa',raw),pl.Series('poisson_pa',p),pl.col('cohort_rate').alias('poisson_rate'))
            q=q.with_columns((pl.col('poisson_pa')*(pl.col('poisson_rate')/600+pl.col('origin_replacement_rate'))).alias('poisson_value'))
            path=OUT/f'poisson-{y}-{k}.joblib';joblib.dump(model,path,compress=3);q.write_parquet(forecast)
            n=dict(year=y,fold=k,path=str(path),sha256=sha256_file(path),prediction_sha256=sha256_file(forecast),
                training_rows=len(tr),training_players=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max()),
                clipped_over_800=int((raw>800).sum()),retirement_overrides=int(q['reported_retired'].sum()),pa_model_only=True)
            write(note.name,n);fits.append(n);print(f'Fitted count objective {y}/{k}',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert q.select(base.columns).equals(base.sort('row_id')) and len(q)==30506 and q['poisson_rate'].equals(q['cohort_rate'])
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=35,player_walkthrough_status='pending',clipped_over_800=sum(n['clipped_over_800'] for n in fits),
        all_old_columns_exact=True,rate_model_unchanged=True,probability_model_fitted=False,protected_outcomes_used=False))


if __name__=='__main__':
    import sys
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='fit':fit()
    else:raise ValueError('Choose prepare or fit')
