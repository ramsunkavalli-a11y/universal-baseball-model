"""Recover historical marginal projection states without changing a live forecast."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from audit_player_path_population_v1 import panel_data, BASE, DEBUT, ANCHORS
from evaluate_multiyear_hitter_v1 import opportunity, ridge
from evaluate_multiyear_hitter_followup_v2 import established_features, p_matrix, SOURCE, fixed_mean
from evaluate_hitter_anchored_development_v1 import anchor_at_origin
from universal_baseball.multiyear_hitter_value import training_mask
from universal_baseball.multiyear_hitter_followup import opportunity_mask
from universal_baseball.six_year_hitter import mature_mask
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.hitter_arrival_coherence import cell_probability, scopes
from universal_baseball.historical_projection_state import conditional_workload, validate_states, residual_ledger
from universal_baseball.storage import sha256_file
from fit_hitter_arrival_coherence_v1 import save

OUT=Path('reports/generated/historical-projection-state-v1')
PLAN=Path('docs/historical-projection-state-v1-plan.md')
REFERENCE=Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23/predictions.parquet')
QUANTILES=Path('model_artifacts/multiyear-hitter-followup-v2-2026-09-22/raw-quantile-predictions.parquet')
EARLY=(2012,2013,2014,2015)
YEARS=(*EARLY,2016,2017,2018,2019,2021,2022,2025)
CHECKS=(2016,2022)


def hashes():
    paths=[PLAN,Path(__file__),Path('tests/test_historical_projection_state.py'),
        Path('src/universal_baseball/historical_projection_state.py'),BASE/'panel.parquet',BASE/'targets.parquet',BASE/'manifest.json',
        BASE/'outer-predictions.parquet',BASE/'current-candidates.parquet',DEBUT,ANCHORS,REFERENCE,QUANTILES,SOURCE,
        Path('scripts/evaluate_multiyear_hitter_v1.py'),Path('scripts/evaluate_multiyear_hitter_followup_v2.py'),
        Path('scripts/evaluate_hitter_anchored_development_v1.py'),Path('scripts/audit_established_hitter_opportunity.py')]
    paths += [Path('src/universal_baseball')/(name+'.py') for name in ('hitter_three_year_opportunity',
        'hitter_model_tournament','hitter_target_architecture','hitter_anchored_development','hitter_arrival_coherence',
        'multiyear_hitter_value','multiyear_hitter_followup','six_year_hitter','playing_time_model','opportunity_model_v2')]
    paths += [Path('scripts/audit_player_path_population_v1.py'),Path('scripts/fit_hitter_arrival_coherence_v1.py')]
    paths += [next((BASE/'fits').glob(f'*-{year}-returning.parquet')) for year in CHECKS if year>2016]
    return {str(p):sha256_file(p) for p in paths}


def raw_mean(panel,manifest,year,h):
    test=panel.filter(pl.col('origin_year')==year)
    features=manifest['base_features'] if h==1 else manifest['full_features']
    if year<=2016:
        # At 2016 there is still only one earlier rich-panel origin (2015).
        mask=training_mask(panel,year,h)
        values=ridge().fit(panel.select(features).to_numpy()[mask],panel[f'war_h{h}'].to_numpy()[mask]).predict(test.select(features).to_numpy())
        return test.select('player_id').with_columns(pl.Series('old_value',values))
    return fixed_mean(panel,manifest,year).select('player_id',pl.col(f'h{h}').alias('old_value'))


def replay(panel,epanel,manifest,year,h):
    if year not in (*EARLY,*CHECKS):raise ValueError('Undeclared replay')
    test=panel.filter(pl.col('origin_year')==year).sort('player_id')
    base=opportunity(panel,year,h,False).sort('player_id')
    np.testing.assert_array_equal(base['player_id'],test['player_id'])
    p=base['predicted_any_mlb_pa_probability'].to_numpy().copy()
    positive=base['predicted_positive_mlb_pa_mean'].to_numpy()
    established_train=epanel.filter(pl.Series(opportunity_mask(epanel,year,h)))
    established_test=epanel.filter((pl.col('origin_year')==year)&pl.col('established'))
    model=make_pipeline(StandardScaler(),LogisticRegression(C=1.,max_iter=2000,random_state=417))
    prob=model.fit(p_matrix(established_train,h),(established_train[f'pa_h{h}'].to_numpy()>0)).predict_proba(p_matrix(established_test,h))[:,1]
    lookup=dict(zip(established_test['player_id'],prob))
    established=np.array([i in lookup for i in test['player_id']])
    p=np.array([lookup.get(i,v) for i,v in zip(test['player_id'],p)])
    train=panel.filter(pl.Series(mature_mask(panel,year,h)))
    active=train[f'pa_h{h}'].to_numpy()>0
    x,tx=train.select(manifest['full_features']).to_numpy(),test.select(manifest['full_features']).to_numpy()
    pa,y=train[f'pa_h{h}'].to_numpy(),train[f'war_h{h}'].to_numpy()
    pa_model=make_engine_models('lightgbm',417,'balanced').regressor.set_params(n_jobs=4)
    rate_model=make_engine_models('lightgbm',427,'balanced').regressor.set_params(n_jobs=4)
    cp=np.clip(pa_model.fit(x[active],pa[active]).predict(tx),1,750)
    rate=np.clip(rate_model.fit(x[active],600*y[active]/pa[active],sample_weight=pa[active]/pa[active].mean()).predict(tx),-5,10)
    cell,supported,_=cell_probability(train,test,h)
    f=test.select('origin_year','player_id','age','level','stage','prospect','prior_debut').with_columns(
        pl.lit(h,dtype=pl.Int32).alias('horizon'),pl.Series('old_p',p),pl.Series('old_pa',p*positive),
        pl.Series('conditional_pa',cp),pl.Series('rate',rate),pl.Series('new_p',cell).fill_nan(None),
        pl.Series('cell_supported',supported),pl.Series('established_update',established))
    f=f.join(raw_mean(panel,manifest,year,h),on='player_id',how='left',validate='1:1',maintain_order='left')
    affected=scopes(f)['C2']
    f=f.with_columns(pl.Series('C2_affected',affected),
        pl.Series('C2_p',np.where(affected,cell,p)),pl.Series('C2_pa',np.where(affected,cell*cp,p*positive)),
        pl.Series('C2_value',np.where(affected,cell*cp*rate/600,f['old_value'].to_numpy())))
    note={'origin':year,'horizon':h,'training_origins':sorted(train['origin_year'].unique().to_list()),
        'training_rows':train.height,'active_training_rows':int(active.sum()),'latest_label':int(train['origin_year'].max())+h,
        'training_players':train['player_id'].n_unique(),'active_training_players':train.filter(pl.Series(active))['player_id'].n_unique(),
        'established_training_rows':established_train.height,'test_rows':test.height,
        'pa_clips':int(((cp==1)|(cp==750)).sum()),'rate_clips':int(((rate==-5)|(rate==10)).sum()),
        'value_recomputed':year<=2016,'old_value_recipe':'base Ridge H1 / full Ridge H2-H3' if year<=2016 else 'reused fixed mean archive'}
    return f,note


def compare(a,b,columns):
    keys=['origin_year','player_id','horizon'] if 'horizon' in a.columns else ['origin_year','player_id']
    a,b=a.sort(keys),b.sort(keys)
    assert a.select(keys).equals(b.select(keys)),'Key coverage differs'
    deltas={}
    for c in columns:
        aa,bb=a[c].to_numpy(),b[c].to_numpy()
        np.testing.assert_allclose(aa,bb,rtol=1e-7,atol=1e-7,equal_nan=True,err_msg=c)
        finite=np.isfinite(aa)&np.isfinite(bb)
        deltas[c]=float(np.max(abs(aa[finite]-bb[finite]))) if finite.any() else 0.
    return deltas


def mutate_future(frame,cutoff,features):
    out=frame
    for h in (1,2,3):
        for target in ('pa','war'):
            out=out.with_columns(pl.when(pl.col('origin_year')+h>cutoff).then(
                pl.lit(1234 if target=='pa' else 123.45)).otherwise(pl.col(f'{target}_h{h}')).alias(f'{target}_h{h}'))
    for c in features:
        out=out.with_columns(pl.when(pl.col('origin_year')>cutoff).then(987.).otherwise(pl.col(c)).alias(c))
    return out


def state_rows(f,panel,anchors,evidence,provenance):
    context=panel.select('origin_year','player_id','recent_debut','minor_returner','mlb_pa_lag0','pa_lag0','age_missing')
    f=f.join(context,on=['origin_year','player_id'],how='left',validate='m:1').join(
        anchors.select('origin_year','player_id',pl.col('performance_anchor').alias('h1_rate_anchor'),
            pl.col('latest_anchor_target').alias('anchor_latest_label')),on=['origin_year','player_id'],how='left',validate='m:1')
    f=f.join(evidence,on=['origin_year','player_id'],how='left',validate='m:1')
    cp=conditional_workload(f['C2_p'],f['C2_pa'])
    return f.select('origin_year','player_id','horizon','age','age_missing','level','stage','prospect','prior_debut',
        'recent_debut','minor_returner','mlb_pa_lag0','pa_lag0',
        pl.col('C2_p').alias('delivered_p'),pl.col('C2_pa').alias('delivered_pa'),
        pl.Series('delivered_conditional_pa',cp),pl.col('C2_value').alias('delivered_value'),
        pl.col('old_value').alias('unrepaired_value'),pl.col('old_p').alias('unrepaired_p'),pl.col('old_pa').alias('unrepaired_pa'),
        pl.col('rate').alias('research_conditional_rate'),pl.col('conditional_pa').alias('research_conditional_pa'),
        'h1_rate_anchor','anchor_latest_label','C2_affected','year1_evidence').with_columns(
        pl.lit(provenance).alias('provenance'),pl.col('origin_year').alias('source_cutoff'),
        pl.lit('batting_plus_replacement_not_whole_war').alias('target'),
        pl.lit('value_latest_label is a certified upper bound; reused rich-stack fits may end earlier').alias('value_vintage_provenance'),
        pl.lit('PA recovered from documented hurdle product; not a hitting-rate inference').alias('conditional_pa_provenance'),
        pl.when(pl.col('C2_affected')).then(pl.lit('C2 rookie conditional rate')).otherwise(pl.lit('research rate head; delivered value modeled separately')).alias('rate_role'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'fits').mkdir(exist_ok=True)
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'early':EARLY,'origins':YEARS,'overlap':CHECKS,
            'versions':{k:importlib.metadata.version(k) for k in ('numpy','polars','scikit-learn','lightgbm','statsmodels')},
            'protected_outcomes_used':False});print('Reconstruction contract frozen');return
    frozen=json.loads((OUT/'prefit-manifest.json').read_text());assert frozen['hashes']==hashes()
    panel=panel_data();raw=pl.read_parquet(BASE/'panel.parquet');epanel=established_features(raw)
    manifest=json.loads((BASE/'manifest.json').read_text());features=manifest['full_features']
    ref=pl.read_parquet(REFERENCE).filter(~pl.col('cold')&(pl.col('horizon')<=3)&pl.col('origin_year').is_in(YEARS))
    anchors=pl.read_parquet(ANCHORS)
    overlap=[];anchor_notes=[]
    # Run all declared reproduction gates before any missing-origin backfill.
    for year in CHECKS:
        a,note=anchor_at_origin(raw,features,year)
        adelta=compare(a,anchors.filter(pl.col('origin_year')==year),['performance_anchor'])
        anchor_notes.append({**note,'maximum_differences':adelta})
        for h in (1,2,3):
            print(f'Reproduce {year} H{h}',flush=True)
            f,note=replay(panel,epanel,manifest,year,h)
            delta=compare(f,ref.filter((pl.col('origin_year')==year)&(pl.col('horizon')==h)),
                ['old_p','old_pa','old_value','conditional_pa','rate','new_p','C2_p','C2_pa','C2_value'])
            overlap.append({**note,'maximum_differences':delta})
            f.write_parquet(OUT/'fits'/f'overlap-{year}-h{h}.parquet')
    save(OUT/'overlap-checks.json',{'opportunity':overlap,'anchors':anchor_notes,'passed':True})
    print('All overlap checks passed',flush=True)
    frames=[];notes=[]
    for year in EARLY:
        a,note=anchor_at_origin(raw,features,year)
        compare(a,anchors.filter(pl.col('origin_year')==year),['performance_anchor'])
        anchor_notes.append(note)
        for h in (1,2,3):
            print(f'Backfill {year} H{h}',flush=True)
            f,note=replay(panel,epanel,manifest,year,h)
            q=pl.read_parquet(QUANTILES).filter((pl.col('origin_year')==year)&(pl.col('horizon')==f'h{h}')).select(
                'origin_year','player_id',pl.col('mean').alias('old_value'),pl.lit(h,dtype=pl.Int32).alias('horizon'))
            note['mean_archive_maximum_difference']=compare(f,q,['old_value'])
            frames.append(f);notes.append(note);f.write_parquet(OUT/'fits'/f'backfill-{year}-h{h}.parquet')
    # Information after the origin is deliberately corrupted, including labels on earlier snapshots.
    mutated=mutate_future(panel,2016,features)
    me=mutate_future(epanel,2016,features)
    mf,_=replay(mutated,me,manifest,2016,3)
    original=pl.read_parquet(OUT/'fits'/'overlap-2016-h3.parquet')
    mutation=compare(mf,original,['old_p','old_pa','old_value','rate','conditional_pa','C2_p','C2_pa','C2_value'])
    ma,_=anchor_at_origin(mutate_future(raw,2016,features),features,2016)
    mutation.update(compare(ma,anchors.filter(pl.col('origin_year')==2016),['performance_anchor']))
    save(OUT/'future-mutation-check.json',{'passed':True,'cutoff':2016,'maximum_differences':mutation})
    evidence=pl.concat([pl.read_parquet(BASE/'outer-predictions.parquet'),pl.read_parquet(BASE/'current-candidates.parquet')],how='diagonal_relaxed').select(
        'origin_year','player_id','year1_evidence')
    early_context=panel.filter(pl.col('origin_year').is_in(EARLY)).select('origin_year','player_id').with_columns(
        pl.lit('B0 historical fallback; no two earlier rich origins').alias('year1_evidence'))
    evidence=pl.concat([evidence,early_context])
    early=state_rows(pl.concat(frames),panel,anchors,evidence,'reconstructed fixed recipe; not contemporaneously issued')
    reused=state_rows(ref,panel,anchors,evidence,'reused immutable historical/current-recipe archive')
    archive=pl.concat([early,reused],how='diagonal_relaxed')
    vintage=[]
    for year in YEARS:
        for h in (1,2,3):
            train=panel.filter(pl.Series(mature_mask(panel,year,h)))
            value_train=panel.filter(pl.Series(training_mask(panel,year,h)))
            vintage.append({'origin_year':year,'horizon':h,'opportunity_latest_label':int(train['origin_year'].max())+h,
                'rate_latest_label':int(train['origin_year'].max())+h,'value_latest_label':int(value_train['origin_year'].max())+h})
    archive=archive.join(pl.DataFrame(vintage).with_columns(pl.col('horizon').cast(pl.Int32)),on=['origin_year','horizon'],validate='m:1').sort('origin_year','player_id','horizon')
    validate_states(archive)
    archive.write_parquet(OUT/'states.parquet')
    residual_ledger(archive,panel).write_parquet(OUT/'residual-ledger.parquet')
    assert frozen['hashes']==hashes()
    save(OUT/'build-manifest.json',{'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),'backfill':notes,'anchor_fits':anchor_notes,
        'rows':archive.height,'origins':YEARS,'archived_later_rows':reused.height,'backfilled_rows':early.height,
        'production_forecasts_changed':False,'protected_outcomes_used':False,
        'semantics':'Independent marginal states, not joint career paths. Conditional rates are selected-MLB research estimates.',
        'files':{n:sha256_file(OUT/n) for n in ('states.parquet','residual-ledger.parquet','overlap-checks.json','future-mutation-check.json')}})
    print(json.dumps({'archive_rows':archive.height,'backfilled_rows':early.height,'overlap_passed':True,'future_mutation_passed':True}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
