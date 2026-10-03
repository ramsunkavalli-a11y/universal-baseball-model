"""Same historical PA fit, with verified within-season role trajectories."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file
import prepare_hitter_late_role_v46 as s

ROOT=s.ROOT;OUT=s.OUT;BASE=s.e.BASE;r=s.e.r;FIXED=s.FIXED;write=s.write


def tag(f):
    return f.with_columns((pl.col('age')/5).floor().alias('age_band'),
        pl.when(pl.col('late_usage_0_late_pa')==0).then(pl.lit('absent')).when(pl.col('late_usage_0_late_pa')<50).then(pl.lit('1-49')).when(pl.col('late_usage_0_late_pa')<100).then(pl.lit('50-99')).otherwise(pl.lit('100plus')).alias('late_band'))


def prepare():
    review=r.read(OUT/'source-review.json');assert review['player_walkthrough_status']=='complete' and review['source_usable']
    assert not (OUT/'preflight.json').exists()
    old=r.read(BASE/'preflight.json');source=pl.read_parquet(OUT/'features.parquet');added=r.read(OUT/'features.json')['added'];names=old['features']+added
    cells=[];supports=[];profiles=[];keys=['stage','prior_debut','age_band','late_band']
    for c in old['cells']:
        tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids']))
        sp,note=preflight(tr,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows());supports.append(sp)
        n=tag(tr).group_by(keys).agg(pl.col('player_id').n_unique().alias('late_profile_players'))
        profiles.append(tag(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(pl.col('late_profile_players').fill_null(0)))
        assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all() and not set(tr['player_id'])&set(te['player_id'])
        cells.append(dict(**c,late_usage_preflight=note))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).sort('row_id').write_parquet(OUT/'profile-support.parquet')
    paths=[OUT/'features.parquet',OUT/'windows.parquet',OUT/'source-manifest.json',OUT/'source-review.json',OUT/'source-walkthrough.md',OUT/'source-cases.json',
        r.OUT/'predictions.parquet',BASE/'preflight.json',ROOT/'docs/practical-hitter-late-role-v46-contract.md',Path(__file__),Path(s.__file__),
        ROOT/'config/practical_hitter_late_role_v46_source_notes.json',ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(before_fitting=True,features=names,added_features=added,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},source_eligibility_qualified=True,protected_outcomes_used=False,
        settings=dict(loss='squared_error',max_iter=250,max_depth=3,min_samples_leaf=30,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=31)))
    print('35 actual cells checked; 249 inputs, no tuning; player-held late-role support persisted.',flush=True)


def fit():
    pre=r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    for n in r.read(OUT/'source-manifest.json')['sources']:assert sha256_file(Path(n['path']))==n['sha256']
    for n in r.read(OUT/'source-manifest.json')['checks']:assert sha256_file(Path(n['schedule_path']))==n['schedule_sha256']
    source=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(r.OUT/'predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];forecast=OUT/f'forecast-{y}-{k}.parquet';note=OUT/f'fit-{y}-{k}.json'
            if forecast.exists():
                n=r.read(note);assert sha256_file(forecast)==n['prediction_sha256'] and sha256_file(Path(n['path']))==n['sha256'];fits.append(n);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id'])
            old=joblib.load(r.read(BASE/f'fit-{y}-{k}.json')['path']);assert all(old.get_params()[a]==v for a,v in pre['settings'].items())
            model=HistGradientBoostingRegressor(**pre['settings']);model.fit(tr.select(pre['features']).to_numpy(),tr['next_pa'].to_numpy(),sample_weight=weights(tr))
            raw=model.predict(te.select(pre['features']).to_numpy());p=np.clip(raw,0,800);p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
            q=q.with_columns(pl.Series('late_raw_pa',raw),pl.Series('late_pa',p),pl.col('cohort_rate').alias('late_rate'))
            q=q.with_columns((pl.col('late_pa')*(pl.col('late_rate')/600+pl.col('origin_replacement_rate'))).alias('late_value'))
            path=OUT/f'late-{y}-{k}.joblib';joblib.dump(model,path,compress=3);q.write_parquet(forecast)
            n=dict(year=y,fold=k,path=str(path),sha256=sha256_file(path),prediction_sha256=sha256_file(forecast),training_rows=len(tr),training_players=tr['player_id'].n_unique(),max_target_year=int(tr['target_year'].max()),clipped_over_800=int((raw>800).sum()),clipped_under_zero=int((raw<0).sum()))
            write(note.name,n);fits.append(n);print(f'Fitted late role {y}/{k}',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id');assert q.select(base.columns).equals(base.sort('row_id')) and len(q)==30506
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits);write('fit-report.json',dict(heads=35,player_walkthrough_status='pending',all_old_columns_exact=True,rate_model_unchanged=True,protected_outcomes_used=False))


if __name__=='__main__':
    import sys
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='fit':fit()
    else:raise ValueError('Choose prepare or fit')
