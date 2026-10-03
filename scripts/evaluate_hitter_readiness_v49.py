"""Binary MLB participation and conditional PA on the audited full panel."""
from pathlib import Path
from types import SimpleNamespace
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier,HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from universal_baseball.forecast_validation import preflight
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
import evaluate_hitter_scouting_v48 as prior

ROOT=prior.ROOT
OUT=ROOT/'reports/generated/practical-hitter-readiness-v49'
old=prior.old


def write(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')


def logit_trace(model,x,names):
    # The existing exact node-path accountant asserts the response-scale predict
    # value. For this binary classifier its additive trees are on log-odds scale.
    proxy=SimpleNamespace(_baseline_prediction=model._baseline_prediction,_predictors=model._predictors,predict=model.decision_function)
    result=trace(proxy,x,names);z=result['raw_prediction'];p=1/(1+np.exp(-z))
    assert np.isclose(p,model.predict_proba(np.asarray(x)[None,:])[0,1],atol=1e-10)
    result.update(raw_log_odds=z,linked_probability=float(p),units='log_odds_not_PA')
    return result


def prepare():
    assert old.r.read(prior.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists()
    oldpre=old.r.read(old.OUT/'preflight.json');source=pl.read_parquet(old.OUT/'features.parquet')
    source=source.with_columns((pl.col('next_pa')>0).cast(pl.Int64).alias('next_active'))
    source.write_parquet(OUT/'features.parquet') if OUT.exists() else None
    arms=dict(binary_count=oldpre['features'][:239],binary_scout=oldpre['features'])
    cells=[];supports=[];profiles=[];keys=['stage','prior_debut','age_band','rank_band']
    for c in oldpre['cells']:
        tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids']));active=tr.filter(pl.col('next_active')==1)
        assert set(tr['next_active'].unique())=={0,1} and len(active)>100
        checks={}
        for arm,names in arms.items():
            for head,rows in [('participation',tr),('conditional_pa',active)]:
                support,note=preflight(rows,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
                checks[arm+'_'+head]=note;supports.append(support.with_columns(pl.lit(arm).alias('arm'),pl.lit(head).alias('head')))
        n=old.tag(active).group_by(keys).agg(pl.col('player_id').n_unique().alias('conditional_rank_profile_players'))
        profiles.append(old.tag(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(pl.col('conditional_rank_profile_players').fill_null(0)))
        cells.append(dict(**c,binary_preflight=checks,conditional_training_rows=len(active),conditional_training_players=active['player_id'].n_unique()))
    OUT.mkdir(parents=True,exist_ok=True);source.write_parquet(OUT/'features.parquet');pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).sort('row_id').write_parquet(OUT/'conditional-profile.parquet')
    paths=[OUT/'features.parquet',old.OUT/'preflight.json',old.OUT/'ranks.parquet',old.OUT/'source-review.json',prior.OUT/'predictions.parquet',prior.OUT/'verification.json',prior.OUT/'report.json',
        ROOT/'docs/practical-hitter-readiness-v49-contract.md',Path(__file__),ROOT/'src/universal_baseball/histogram_prediction_trace.py',ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(before_fitting=True,arms=arms,cells=cells,input_hashes={str(p):sha256_file(p) for p in paths},
        settings=dict(max_iter=250,max_depth=3,min_samples_leaf=30,learning_rate=.05,l2_regularization=10,early_stopping=False,random_state=31),
        prior_review_complete=True,all_evaluation_rows_retained=True,protected_outcomes_used=False))
    print('All 35 cells and 140 full/conditional subset checks saved before fits.',flush=True)


def fit():
    pre=old.r.read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(prior.OUT/'predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];forecast=OUT/f'forecast-{y}-{k}.parquet';note=OUT/f'fit-{y}-{k}.json'
            if forecast.exists():
                n=old.r.read(note);assert sha256_file(forecast)==n['prediction_sha256']
                for h in n['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(n);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');active=tr.filter(pl.col('next_active')==1)
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert q['row_id'].equals(te['row_id']);heads=[]
            for arm,names in pre['arms'].items():
                cls=HistGradientBoostingClassifier(**pre['settings']);cls.fit(tr.select(names).to_numpy(),tr['next_active'].to_numpy(),sample_weight=weights(tr));assert cls.classes_.tolist()==[0,1]
                reg=HistGradientBoostingRegressor(**pre['settings']);reg.fit(active.select(names).to_numpy(),active['next_pa'].to_numpy(),sample_weight=weights(active))
                x=te.select(names).to_numpy();raw_p=cls.predict_proba(x)[:,1];raw_cond=reg.predict(x);cond=np.clip(raw_cond,1,800);p=raw_p.copy()
                p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0;pa=p*cond
                assert np.isfinite(pa).all()
                q=q.with_columns(pl.Series(arm+'_raw_p',raw_p),pl.Series(arm+'_p',p),pl.Series(arm+'_raw_conditional_pa',raw_cond),pl.Series(arm+'_conditional_pa',cond),pl.Series(arm+'_pa',pa),pl.col('cohort_rate').alias(arm+'_rate'))
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col('cohort_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
                for head,model,rows in [('participation',cls,tr),('conditional_pa',reg,active)]:
                    path=OUT/f'{arm}-{head}-{y}-{k}.joblib';joblib.dump(model,path,compress=3);heads.append(dict(arm=arm,head=head,path=str(path),sha256=sha256_file(path),training_rows=len(rows),training_players=rows['player_id'].n_unique(),max_target_year=int(rows['target_year'].max())))
            q.write_parquet(forecast);n=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(forecast));write(note.name,n);fits.append(n);print(f'Fitted binary readiness {y}/{k}: four heads',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id');assert q.select(base.columns).equals(base) and len(q)==30506
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits);write('fit-report.json',dict(heads=140,player_walkthrough_status='pending',all_old_columns_exact=True,rate_model_unchanged=True,protected_outcomes_used=False))


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1]=='fit':fit()
    else:raise ValueError('Choose prepare or fit')
