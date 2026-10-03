"""One structural workload comparison; no hyperparameter/feature search."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball import practical_hitter_v30 as m
from universal_baseball.forecast_validation import preflight
from universal_baseball.storage import sha256_file

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/generated/practical-hitter-v30'
PANEL=ROOT/'model_artifacts/post-arrival-support-v17/panel.parquet'
COUNTS=ROOT/'model_artifacts/post-arrival-detailed-input-readiness/batting-component-counts-by-level.parquet'
BASE=ROOT/'reports/generated/opportunity-shrinkage-v24/predictions.parquet'
STATUS=ROOT/'reports/generated/availability-context-v29b/predictions.parquet'
PUBLIC=ROOT/'reports/generated/public-benchmark-v2/matched-public.parquet'
YEARS=[2016,2017,2018,2021,2022,2023,2024]

def read(p):return json.loads(p.read_text(encoding='utf8'))
def write(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False,default=str),encoding='utf8')
def check(hashes):
    for p,h in hashes.items():assert sha256_file(Path(p))==h,p

def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/'preflight.json').exists(),'Preserve experiment'
    assert read(ROOT/'reports/generated/availability-context-v29b/report.json')['player_walkthrough_status']=='complete'
    panel=pl.read_parquet(PANEL);counts=pl.read_parquet(COUNTS)
    f=m.materialize(panel,counts).with_columns(pl.lit(1).alias('horizon'),(pl.col('origin_year')+1).alias('target_year'))
    base=pl.read_parquet(BASE)
    # Independent aggregate reconciliation against the certified MLB target.
    targets=pl.read_parquet(ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet')
    mlb=counts.filter(pl.col('level_group')=='MLB').select('season','player_id','plate_appearances')
    joined=targets.join(mlb,on=['season','player_id'],validate='1:1')
    assert len(joined)==len(targets) and joined['mlb_pa'].equals(joined['plate_appearances'])
    nextlabels=f.select('row_id','player_id','target_year','next_pa','next_value').join(
        targets.select('player_id',pl.col('season').alias('target_year'),pl.col('mlb_pa').alias('_pa'),
            pl.col('component_war').alias('_value')),on=['player_id','target_year'],how='left',validate='m:1')
    assert nextlabels.filter((pl.col('next_pa')!=pl.col('_pa').fill_null(0))|(pl.col('next_value')!=pl.col('_value').fill_null(0))).height==0
    f.write_parquet(OUT/'features.parquet')
    status=pl.read_parquet(STATUS).select('row_id','hard_unavailable','hard_reason','needs_availability_scenario',
        'availability_state','rules_pa','rules_value')
    evaluate=base.join(status,on='row_id',validate='1:1')
    notes=[];supports=[]
    for year in YEARS:
        for fold in range(5):
            tr=f.filter((pl.col('target_year')<=year)&(pl.col('target_year')!=2020)&(pl.col('outer_fold')!=fold)).sort('row_id')
            te=evaluate.filter((pl.col('origin_year')==year)&(pl.col('outer_fold')==fold)).sort('player_id')
            raw=f.filter(pl.col('row_id').is_in(te['row_id'])).sort('player_id')
            assert te['row_id'].equals(raw['row_id'])
            for col in ['next_pa','next_value','next_state']:assert te[col].equals(raw[col])
            sp,note=preflight(tr,raw,cutoff=year,fold=fold,features=m.FEATURES,expected_keys=te.select('row_id','horizon').iter_rows())
            notes.append(dict(year=year,fold=fold,**note,training_row_ids=tr['row_id'].to_list()))
            supports.append(sp.with_columns(pl.lit(fold).alias('outer_fold')))
            tr.write_parquet(OUT/f'train-{year}-{fold}.parquet')
            te.join(raw.select('row_id',*[c for c in m.FEATURES if c not in te.columns]),on='row_id',validate='1:1').write_parquet(OUT/f'test-{year}-{fold}.parquet')
    pl.concat(supports).write_parquet(OUT/'support.parquet')
    paths=[PANEL,COUNTS,BASE,STATUS,PUBLIC,ROOT/'reports/generated/multiyear-hitter-v1/targets.parquet',
        ROOT/'docs/practical-hitter-model-v30-plan.md',Path(__file__),Path(m.__file__),OUT/'features.parquet',
        ROOT/'reports/generated/availability-context-v29b/report.json']
    paths+=list(OUT.glob('train-*.parquet'))+list(OUT.glob('test-*.parquet'))
    hashes={str(p):sha256_file(p) for p in paths}
    versions={n:importlib.metadata.version(n) for n in ['scikit-learn','xgboost','lightgbm','catboost','polars','numpy']}
    write('preflight.json',dict(input_hashes=hashes,before_fitting=True,cells=notes,features=m.FEATURES,
        source_rows=len(f),evaluation_rows=len(base),reconciled_target_rows=len(joined),versions=versions,
        explicit_scope='post-debut elapsed 0–5; not full hitter/prospect universe',learner_arms=m.ARMS))
    print(json.dumps(dict(features=len(m.FEATURES),source_rows=len(f),evaluation_rows=len(base),cells=len(notes),versions=versions)))

def fit():
    manifest=read(OUT/'preflight.json');check(manifest['input_hashes'])
    assert not (OUT/'report.json').exists(),'Preserve batch'
    frames=[];states=[]
    with threadpool_limits(limits=2):
        for c in manifest['cells']:
            year,fold=c['year'],c['fold'];tr=pl.read_parquet(OUT/f'train-{year}-{fold}.parquet');te=pl.read_parquet(OUT/f'test-{year}-{fold}.parquet')
            assert tr['row_id'].to_list()==c['training_row_ids']
            x,q=tr.select(m.FEATURES).to_numpy(),te.select(m.FEATURES).to_numpy()
            pa=tr['next_pa'].to_numpy();hard=te['hard_unavailable'].to_numpy()
            assert np.isfinite(x).all() and np.isfinite(q).all()
            yield_rate=te['v24_value'].to_numpy()/te['v24_pa'].to_numpy()
            assert np.isfinite(yield_rate).all()
            for arm in m.ARMS:
                model=m.fit(m.learner(arm),arm,x,pa,tr['origin_year'].to_numpy())
                raw=model.predict(q);pred=m.forecast(raw,hard)
                artifact=OUT/f'model-{arm}-{year}-{fold}.joblib';joblib.dump(model,artifact,compress=3)
                te=te.with_columns(pl.Series(arm+'_raw_pa',raw),pl.Series(arm+'_pa',pred),pl.Series(arm+'_value',pred*yield_rate))
                states.append(dict(arm=arm,year=year,fold=fold,artifact=str(artifact),sha256=sha256_file(artifact),
                    training_rows=len(tr),training_players=tr['player_id'].n_unique(),
                    clipped_low=int((raw<0).sum()),clipped_high=int((raw>800).sum())))
            frames.append(te)
            if fold==4:print(f'Completed six workload models for origin {year}',flush=True)
    f=pl.concat(frames).sort('origin_year','player_id');base=pl.read_parquet(BASE).sort('origin_year','player_id')
    assert len(f)==4396 and f.select(base.columns).equals(base)
    f.write_parquet(OUT/'predictions.parquet');write('fits.json',states)
    public=pl.read_parquet(PUBLIC).select('row_id','steamer_pa','steamer_value','zips_pa')
    f=f.join(public,on='row_id',how='left',validate='1:1')
    scopes=[('all',f),('public_active',f.filter((pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_pa').is_not_null()))]
    scopes += [('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in YEARS]
    scopes += [('current_zero',f.filter(pl.col('pa_0')==0)),('current_brief',f.filter(pl.col('pa_0').is_between(1,199))),
        ('current_partial',f.filter(pl.col('pa_0').is_between(200,399))),('current_regular',f.filter(pl.col('pa_0')>=400)),
        ('debut_brief',f.filter((pl.col('elapsed')==0)&pl.col('pa_0').is_between(1,199))),
        ('current600',f.filter(pl.col('pa_0')>=600)),('inactive_prior200',f.filter((pl.col('pa_0')==0)&(pl.col('pa_1')>=200)))]
    scores=[]
    for scope,g in scopes:
        if not len(g):continue
        prefixes=['v24','rules',*m.ARMS]+(['steamer'] if scope=='public_active' else [])
        scores.append(dict(scope=scope,rows=len(g),players=g['player_id'].n_unique(),
            actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={p:m.score(g,p) for p in prefixes}))
    check(manifest['input_hashes'])
    write('report.json',dict(input_hashes=manifest['input_hashes'],scores=scores,player_walkthrough_status='pending',
        new_fits=len(states),protected_2026_outcomes_used=False,frozen_forecast_changed=False,
        value_warning='Fixed old expected-yield multiplication; workload diagnostic, not newly validated joint talent/value.',
        output_hashes={str(OUT/p):sha256_file(OUT/p) for p in ['predictions.parquet','fits.json']}))
    print(json.dumps(scores[:2],indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','fit']);args=p.parse_args()
    {'prepare':prepare,'fit':fit}[args.phase]()
