"""Fixed annual participation substitution with archived workload/value heads."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_arrival_value_transfer import FOLDS,fit_activity,propagate
from universal_baseball.hitter_arrival_source_repair import COHORTS,FEATURES
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.six_year_hitter import mature_mask
from universal_baseball.storage import sha256_file

OUT=Path('reports/generated/hitter-arrival-value-transfer-v1')
REPAIR=Path('reports/generated/hitter-arrival-source-repair-v1')
SOURCE=Path('reports/generated/hitter-detail-arrival-v1')
REF=Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23')
COMP=Path('model_artifacts/multiyear-hitter-components-v1-2026-09-22/integrated-predictions.parquet')
BASE=Path('reports/generated/multiyear-hitter-v1')
CODE=[Path('docs/hitter-arrival-value-transfer-v1-plan.md'),Path(__file__),
    Path('scripts/score_hitter_arrival_value_transfer_v1.py'),Path('tests/test_hitter_arrival_value_transfer.py'),
    *[Path('src/universal_baseball')/(n+'.py') for n in ('hitter_arrival_value_transfer','hitter_canceled_season',
        'hitter_model_tournament','hitter_arrival_source_repair','six_year_hitter','multiyear_hitter_followup')]]


def hashes():
    paths=[*CODE,REF/'predictions.parquet',REF/'fit-manifest.json',COMP,BASE/'manifest.json',
        SOURCE/'input-panel.parquet',SOURCE/'prefit-manifest.json',REPAIR/'repaired-panel.parquet',
        REPAIR/'prefit-manifest.json',REPAIR/'predictions.parquet',REPAIR/'fit-manifest.json']
    return {str(p):sha256_file(p) for p in paths}


def references(panel):
    old=pl.read_parquet(REF/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
         (pl.col('origin_year')<=2022)&(pl.col('horizon')<=3))
    assert set(old.select('origin_year','horizon').unique().iter_rows())==set(FOLDS)
    meta=panel.select('origin_year','player_id','player_name',*COHORTS,'mlb_pa_lag0')
    old=old.drop('prospect','prior_debut').join(meta,on=['origin_year','player_id'],how='left',validate='m:1')
    f=old.select('origin_year','player_id','player_name','horizon','age','level','stage',*COHORTS,'mlb_pa_lag0',
        'actual_pa','actual_value','rate','conditional_pa','old_pa','old_value',
        pl.col('C2_p').alias('B_p'),pl.col('C2_pa').alias('B_pa'),pl.col('C2_value').alias('B_value'),
        pl.col('ensemble').alias('E_pa'),pl.col('ensemble_p').alias('E_p'),pl.col('ensemble_product').alias('E_value'))
    component=pl.read_parquet(COMP).select('origin_year','player_id','horizon','complete_components',
        pl.col('actual').alias('actual_expanded'),pl.col('actual_batting').alias('component_actual_batting'),
        pl.col('batting').alias('component_old_batting'),pl.col('selected').alias('component_old_total'))
    f=f.join(component,on=['origin_year','player_id','horizon'],how='left',validate='1:1').sort('horizon','origin_year','player_id')
    np.testing.assert_array_equal(f['actual_value'],f['component_actual_batting'])
    np.testing.assert_allclose(f['old_value'],f['component_old_batting'],rtol=1e-12,atol=1e-12)
    assert f['complete_components'].null_count()==0 and (f['old_pa']>0).all()
    f=f.with_columns(((pl.col('component_old_total')-pl.col('old_value'))*pl.col('B_pa')/pl.col('old_pa')).alias('base_other_value'))
    f=f.with_columns((pl.col('B_value')+pl.col('base_other_value')).alias('B_expanded'))
    for year,h in FOLDS:
        q=panel.filter(pl.col('origin_year')==year);b=f.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(q['player_id'],b['player_id'])
        np.testing.assert_array_equal(q[f'pa_h{h}'],b['actual_pa'])
        np.testing.assert_array_equal(q[f'war_h{h}'],b['actual_value'])
    for c in ['B_p','B_pa','B_value','rate','base_other_value','E_pa','E_p','E_value']:
        assert f[c].is_finite().all(),c
    provenance=json.loads((REF/'fit-manifest.json').read_text())
    notes=[n for n in provenance['fits'] if not n['cold'] and (n['origin'],n['horizon']) in FOLDS]
    assert len(notes)==len(FOLDS) and all(n['latest_label']<=n['origin'] for n in notes)
    return f,notes


def head_replay(original,refs):
    year,h=2021,3
    columns=json.loads((BASE/'manifest.json').read_text())['full_features']
    t=original.filter(pl.Series(mature_mask(original,year,h)));q=original.filter(pl.col('origin_year')==year)
    active=t[f'pa_h{h}'].to_numpy()>0;x=t.select(columns).to_numpy();tx=q.select(columns).to_numpy()
    pa=t[f'pa_h{h}'].to_numpy();v=t[f'war_h{h}'].to_numpy()
    pm=make_engine_models('lightgbm',417,'balanced').regressor.set_params(n_jobs=4)
    rm=make_engine_models('lightgbm',427,'balanced').regressor.set_params(n_jobs=4)
    cp=np.clip(pm.fit(x[active],pa[active]).predict(tx),1,750)
    rate=np.clip(rm.fit(x[active],600*v[active]/pa[active],sample_weight=pa[active]/pa[active].mean()).predict(tx),-5,10)
    saved=refs.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h))
    np.testing.assert_array_equal(q['player_id'],saved['player_id'])
    np.testing.assert_allclose(cp,saved['conditional_pa'],rtol=1e-10,atol=1e-10)
    np.testing.assert_allclose(rate,saved['rate'],rtol=1e-10,atol=1e-10)
    return {'origin':year,'horizon':h,'conditional_pa_max_difference':float(np.max(abs(cp-saved['conditional_pa'].to_numpy()))),
        'rate_max_difference':float(np.max(abs(rate-saved['rate'].to_numpy())))}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');args=ap.parse_args()
    (OUT/'fits').mkdir(parents=True,exist_ok=True)
    original=pl.read_parquet(SOURCE/'input-panel.parquet');repaired=pl.read_parquet(REPAIR/'repaired-panel.parquet')
    cols=json.loads((SOURCE/'prefit-manifest.json').read_text())['arms']['R']
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        refs,notes=references(repaired);refs.write_parquet(OUT/'references.parquet')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'references_sha256':sha256_file(OUT/'references.parquet'),
            'folds':FOLDS,'columns':{'R':cols,'F':cols+FEATURES},'inherited_head_provenance':notes,
            'protected_outcomes_used':False,'production_forecasts_changed':False})
        print('Frozen before fits and scores');return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    refs=pl.read_parquet(OUT/'references.parquet');assert pre['references_sha256']==sha256_file(OUT/'references.parquet')
    archived=pl.read_parquet(REPAIR/'predictions.parquet').filter((pl.col('target')=='next_year')&pl.col('arm').is_in(['R','F']))
    frames=[];notes=[]
    for year,h in FOLDS:
        b=refs.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h));prob={}
        for arm,panel in [('R',original),('F',repaired)]:
            path=OUT/'fits'/f'{year}-h{h}-{arm}.parquet'
            saved=archived.filter((pl.col('origin_year')==year)&(pl.col('arm')==arm)) if h==1 else archived.head(0)
            if saved.height:
                np.testing.assert_array_equal(b['player_id'],saved['player_id']);p=saved['probability'].to_numpy()
                note={'year':year,'horizon':h,'arm':arm,'reused':True}
            elif path.exists() and path.with_suffix('.json').exists():
                note=json.loads(path.with_suffix('.json').read_text());assert sha256_file(path)==note['sha256']
                saved=pl.read_parquet(path);np.testing.assert_array_equal(b['player_id'],saved['player_id']);p=saved['probability'].to_numpy()
            else:
                print(f'Activity {year} H{h} {arm}',flush=True)
                p,note=fit_activity(panel,pre['columns'][arm],year,h)
                b.select('origin_year','player_id','horizon').with_columns(pl.Series('probability',p)).write_parquet(path)
                note.update(year=year,horizon=h,arm=arm,reused=False,sha256=sha256_file(path));save(path.with_suffix('.json'),note)
            prob[arm]=p;notes.append(note)
        for name,p,scope in [('R',prob['R'],b['prospect']),('F',prob['F'],b['prospect']),('U',prob['F'],np.ones(b.height,bool))]:
            pp,pa,v=propagate(b,p,scope)
            b=b.with_columns(pl.Series(name+'_p',pp),pl.Series(name+'_pa',pa),pl.Series(name+'_value',v))
            b=b.with_columns((pl.col(name+'_value')+pl.col('base_other_value')*pl.col(name+'_pa')/pl.col('B_pa')).alias(name+'_expanded'),
                             (pl.col(name+'_value')+pl.col('base_other_value')).alias(name+'_expanded_fixed'))
        frames.append(b)
    f=pl.concat(frames).sort('horizon','origin_year','player_id');f.write_parquet(OUT/'predictions.parquet')
    checks=[]
    for year,h in [(2022,2),(2021,3)]:
        changed=repaired.with_columns(pl.when(pl.col('origin_year')+h>year).then(9999.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
        changed=changed.with_columns(*[pl.when(pl.col('origin_year')>year).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in pre['columns']['F']])
        print(f'Future mutation {year} H{h}',flush=True)
        p,_=fit_activity(changed,pre['columns']['F'],year,h)
        b=pl.read_parquet(OUT/'fits'/f'{year}-h{h}-F.parquet');np.testing.assert_array_equal(p,b['probability'])
        checks.append({'year':year,'horizon':h,'maximum_difference':0.})
    print('Replay archived conditional heads 2021 H3',flush=True);replay=head_replay(original,refs)
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'fits':notes,'mutations':checks,'conditional_head_replay':replay,
        'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),'prediction_sha256':sha256_file(OUT/'predictions.parquet'),
        'protected_outcomes_used':False,'production_forecasts_changed':False})
    print('Fit and propagation complete',flush=True)


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
