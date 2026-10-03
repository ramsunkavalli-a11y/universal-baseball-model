"""Same candidate and folds, explicitly repaired numeric source inputs."""
from pathlib import Path
import json
import sys
import joblib
import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from prepare_practical_hitter_v33 import safe_matrix
from universal_baseball.forecast_validation import preflight
from universal_baseball.hitter_numeric_history import repair, BUCKETS
from universal_baseball.storage import sha256_file
import evaluate_hitter_readiness_v49 as previous

ROOT=previous.ROOT
OUT=ROOT/'reports/generated/practical-hitter-numeric-repair-v53'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def write(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf8')


def profile(g):
    return g.with_columns((pl.col('age')//5).alias('age_group'),
        (pl.sum_horizontal([pl.col(f'{b}_{lag}_pa') for b in BUCKETS for lag in range(3)])<100).alias('thin_exposure'),
        pl.when(pl.col('draft_known')==0).then(pl.lit('unknown')).when(pl.col('draft_elapsed')==0).then(pl.lit('draft_year')).when(pl.col('draft_elapsed')<=.3).then(pl.lit('1_to_3')).otherwise(pl.lit('4plus')).alias('draft_age_group'))


def prepare():
    assert read(previous.OUT/'report.json')['player_walkthrough_status']=='complete'
    assert not (OUT/'preflight.json').exists(), 'Preserve existing preflight'
    old=pl.read_parquet(previous.OUT/'features.parquet')
    counts_path=ROOT/'reports/generated/practical-hitter-v31/counts.parquet'
    counts=pl.read_parquet(counts_path).filter(pl.col('season')<=2024)
    source,changes=repair(old,counts)
    assert len(source)==63282
    allowed={'draft_elapsed','pooled_DSL_pa','pooled_RK120_pa','pooled_RK128_pa','pooled_RK134_pa'}
    assert {c['feature'] for c in changes}<=allowed, changes
    OUT.mkdir(parents=True,exist_ok=True);source.write_parquet(OUT/'features.parquet')
    fixed=[(701762,2024),(694671,2023),(641355,2016),(624413,2018),(806956,2024)]
    fixed_source=[]
    for pid,y in fixed:
        row=source.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y)).row(0,named=True)
        o=old.filter(pl.col('row_id')==row['row_id']).row(0,named=True)
        fixed_source.append(dict(player_id=pid,origin_year=y,name=row['player_name'],
            old_inputs={c['feature']:o[c['feature']] for c in changes},
            new_inputs={c['feature']:row[c['feature']] for c in changes},
            draft_year=row['draft_year'],draft_pick=row['pick_number'],school=row['draft_school_class'],
            origin_history=counts.filter((pl.col('player_id')==pid)&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts()))
    write('source-reconciliation.json',dict(changes=changes,source_rows=len(source),fixed_diagnostics=fixed_source,
        only_declared_numeric_inputs_changed=True,labels_and_membership_unchanged=True))
    pre=read(previous.OUT/'preflight.json')
    rate_names=read(ROOT/'reports/generated/practical-hitter-v34/preflight.json')['features']
    pa_names=pre['arms']['binary_scout'];supports=[];profiles=[];cells=[]
    keys=['stage','prior_debut','age_group','draft_known','thin_exposure','draft_age_group']
    for c in pre['cells']:
        tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
        te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
        active=tr.filter(pl.col('next_pa')>0);checks={}
        for head,sub,names in [('participation',tr,pa_names),('conditional_pa',active,pa_names),('rate',active,rate_names)]:
            support,note=preflight(sub,te,cutoff=c['year'],fold=c['fold'],features=names,expected_keys=te.select('row_id','horizon').iter_rows())
            supports.append(support.with_columns(pl.lit(head).alias('head')));checks[head]=note
            n=profile(sub).group_by(keys).agg(pl.col('player_id').n_unique().alias('profile_players'))
            profiles.append(profile(te).select('row_id',*keys).join(n,on=keys,how='left',validate='m:1').with_columns(pl.col('profile_players').fill_null(0),pl.lit(head).alias('head')))
        cells.append(dict(**c,repair_preflight=checks))
    pl.concat(supports).write_parquet(OUT/'support.parquet');pl.concat(profiles).write_parquet(OUT/'profile-support.parquet')
    paths=[previous.OUT/'features.parquet',previous.OUT/'predictions.parquet',previous.OUT/'preflight.json',previous.OUT/'report.json',counts_path,
        OUT/'features.parquet',OUT/'source-reconciliation.json',OUT/'support.parquet',OUT/'profile-support.parquet',Path(__file__),
        ROOT/'src/universal_baseball/hitter_numeric_history.py',ROOT/'docs/practical-hitter-numeric-repair-v53-contract.md',
        ROOT/'scripts/prepare_practical_hitter_v33.py',ROOT/'scripts/fit_practical_hitter_v31.py']
    write('preflight.json',dict(before_fitting=True,cells=cells,rate_features=rate_names,pa_features=pa_names,
        settings=pre['settings'],ridge_alpha=100,source_changes=changes,input_hashes={str(p):sha256_file(p) for p in paths},
        all_evaluation_rows_retained=True,protected_outcomes_used=False))
    print('Source reconstruction and all 105 head/subset preflights saved.',changes,flush=True)


def fit():
    pre=read(OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    source=pl.read_parquet(OUT/'features.parquet');base=pl.read_parquet(previous.OUT/'predictions.parquet');fits=[]
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];path=OUT/f'forecast-{y}-{k}.parquet'
            if path.exists():
                note=read(OUT/f'fit-{y}-{k}.json');assert sha256_file(path)==note['prediction_sha256']
                for h in note['heads']:assert sha256_file(Path(h['path']))==h['sha256']
                fits.append(note);continue
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids'])).sort('row_id')
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');active=tr.filter(pl.col('next_pa')>0)
            q=base.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert te['row_id'].equals(q['row_id'])
            heads=[];pred={}
            for head,sub,names,model in [('participation',tr,pre['pa_features'],HistGradientBoostingClassifier(**pre['settings'])),
                ('conditional_pa',active,pre['pa_features'],HistGradientBoostingRegressor(**pre['settings'])),
                ('rate',active,pre['rate_features'],Ridge(alpha=pre['ridge_alpha']))]:
                target='next_batting_rate' if head=='rate' else ('next_active' if head=='participation' else 'next_pa')
                w=weights(sub)
                if head=='rate':w*=sub['next_pa'].to_numpy();w*=len(w)/w.sum()
                x=safe_matrix(sub,names) if head=='rate' else sub.select(names).to_numpy()
                tx=safe_matrix(te,names) if head=='rate' else te.select(names).to_numpy()
                model.fit(x,sub[target].to_numpy(),sample_weight=w)
                pred[head]=model.predict_proba(tx)[:,1] if head=='participation' else model.predict(tx)
                assert np.isfinite(pred[head]).all()
                mp=OUT/f'{head}-{y}-{k}.joblib';joblib.dump(model,mp,compress=3)
                heads.append(dict(head=head,path=str(mp),sha256=sha256_file(mp),training_rows=len(sub),training_players=sub['player_id'].n_unique(),max_target_year=int(sub['target_year'].max())))
            p=pred['participation'].copy();p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0
            cond=np.clip(pred['conditional_pa'],1,800);pa=p*cond
            q=q.with_columns(pl.Series('repaired_raw_p',pred['participation']),pl.Series('repaired_p',p),
                pl.Series('repaired_raw_conditional_pa',pred['conditional_pa']),pl.Series('repaired_conditional_pa',cond),
                pl.Series('repaired_pa',pa),pl.Series('repaired_rate',pred['rate']),
                pl.Series('pa_only_pa',pa),pl.col('cohort_rate').alias('pa_only_rate'),
                pl.col('binary_scout_pa').alias('rate_only_pa'),pl.Series('rate_only_rate',pred['rate']))
            for arm in ['repaired','pa_only','rate_only']:
                q=q.with_columns((pl.col(arm+'_pa')*(pl.col(arm+'_rate')/600+pl.col('origin_replacement_rate'))).alias(arm+'_value'))
            q.write_parquet(path);note=dict(year=y,fold=k,heads=heads,prediction_sha256=sha256_file(path));write(f'fit-{y}-{k}.json',note);fits.append(note)
            print(f'Repaired candidate {y}/{k}: three saved heads.',flush=True)
    q=pl.concat([pl.read_parquet(OUT/f"forecast-{c['year']}-{c['fold']}.parquet") for c in pre['cells']]).sort('row_id')
    assert len(q)==30506 and q.select(base.columns).equals(base.sort('row_id'))
    q.write_parquet(OUT/'predictions.parquet');write('fits.json',fits)
    write('fit-report.json',dict(heads=105,old_columns_exact=True,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))


if __name__=='__main__':
    {'prepare':prepare,'fit':fit}[sys.argv[1]]()
