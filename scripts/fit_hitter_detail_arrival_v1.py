"""Freeze and run matched basic-versus-detail future MLB probability tests."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from audit_player_path_population_v1 import panel_data,BASE,DEBUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_detail_arrival import join_lags,eligible,target_values,fit_probability,TARGETS
from universal_baseball.hitter_context_features import CONTEXT_COLUMNS
from universal_baseball.hitter_level_path_features import COMPACT_LEVEL_PATH_FEATURES
from universal_baseball.multiyear_hitter_value import CORE_RATES
from universal_baseball.storage import sha256_file

ROOT=Path('reports/generated')
OUT=ROOT/'hitter-detail-arrival-v1'
PLAN=Path('docs/hitter-detail-arrival-v1-plan.md')
SOURCES={
    'raw':ROOT/'hitter-value-panel-v2/tables/hitter-contact-features.parquet',
    'park':ROOT/'hitter-contact-neutralization-v2/tables/player-season-features.parquet',
    'pitch':ROOT/'hitter-pitch-game-features-v1/tables/player-season-features.parquet',
    'path':ROOT/'hitter-level-path-compact-ablation-v2/tables/level-path-features.parquet',
    'context':ROOT/'hitter-gradient-dataset-v1/tables/player-season-features.parquet'}
PITCH_REPORT=ROOT/'hitter-pitch-game-features-v1/report.json'
REFERENCES={
    'annual':Path('model_artifacts/hitter-arrival-coherence-v1-2026-09-23/predictions.parquet'),
    'ensemble':Path('model_artifacts/hitter-three-year-opportunity-v1-2026-09-22/predictions.parquet'),
    'paths':Path('model_artifacts/player-path-population-v1-2026-09-23/exact-predictions.parquet')}
FOLDS=[(y,'next_year',False) for y in (2017,2018,2021,2022,2023,2024)]+[
    (y,t,False) for t in ('arrival_three','regular_three') for y in (2019,2021,2022)]+[
    (2022,t,True) for t in TARGETS]


def hashes():
    files=[PLAN,Path(__file__),Path('src/universal_baseball/hitter_detail_arrival.py'),
        Path('tests/test_hitter_detail_arrival.py'),BASE/'panel.parquet',BASE/'targets.parquet',BASE/'manifest.json',DEBUT,
        PITCH_REPORT,ROOT/'hitter-contact-neutralization-v2/report.json',*SOURCES.values(),*REFERENCES.values(),
        Path('scripts/audit_player_path_population_v1.py')]
    files += [Path('src/universal_baseball')/(s+'.py') for s in ('hitter_model_tournament','hitter_three_year_opportunity',
        'hitter_level_path_features','hitter_context_features','multiyear_hitter_value','six_year_hitter')]
    return {str(p):sha256_file(p) for p in files}


def assemble():
    p=panel_data().filter(pl.col('origin_year')<=2024)
    manifest=json.loads((BASE/'manifest.json').read_text())
    b0=manifest['base_features']+['prior_debut'];b1=manifest['full_features']+['prior_debut']
    blocks=json.loads(PITCH_REPORT.read_text())['feature_blocks']
    seq=[c for c in blocks['sequence'] if not (c.endswith('_count') or c in ('pitch_count','pa_count','game_count') or c.startswith('split_pitches_'))]
    availability=[];detail=[];development=[];sources={}
    for name,path in SOURCES.items():
        a=pl.read_parquet(path).filter(pl.col('season')<=2024)
        if name=='raw':cols=[c for c in a.columns if c.startswith('contact_cell_rate__')]+['contact_events']
        elif name=='park':cols=[c for c in a.columns if c not in ('season','player_id')]
        elif name=='pitch':cols=seq+['pitch_count','pa_count','game_count']
        elif name=='path':cols=list(COMPACT_LEVEL_PATH_FEATURES)
        else:cols=list(CONTEXT_COLUMNS)
        p,added=join_lags(p,a,cols,name,(0,) if name=='path' else (0,1,2))
        controls=[c for c in added if c.endswith(('__available','__contact_events','__neutral_contact_events',
            '__neutral_contact_levels','__pitch_count','__pa_count','__game_count','__materialized_contacts',
            '_known_rate','_denominator','__mean_park_factor_reliability','__mean_park_training_seasons'))]
        availability.extend(controls)
        (development if name=='path' else detail).extend(c for c in added if c not in controls)
        sources[name]={'path':str(path),'seasons':sorted(a['season'].unique().to_list()),'columns':cols,
            'coverage':p.group_by('origin_year').agg(pl.col(f'{name}0__available').sum().alias('current_rows'),pl.len().alias('population')).sort('origin_year').to_dicts()}
    for rate in CORE_RATES:
        col='change__'+rate
        p=p.with_columns(pl.when((pl.col('missing_lag0')==0)&(pl.col('missing_lag1')==0))
            .then(pl.col(rate+'_lag0')-pl.col(rate+'_lag1')).otherwise(None).alias(col))
        development.append(col)
    b2=b1+availability
    arms={'B0':b0,'B1':b1,'B2':b2,'D':b2+development,'C':b2+detail,'R':b2+development+detail}
    assert all(len(v)==len(set(v)) for v in arms.values())
    return p.sort('origin_year','player_id'),arms,sources


def references():
    rows=[]
    a=pl.read_parquet(REFERENCES['annual']).filter(~pl.col('cold')&(pl.col('horizon')==1)&(pl.col('origin_year')<=2024))
    rows.append(a.select('origin_year','player_id',pl.col('C2_p').alias('probability')).with_columns(pl.lit('next_year').alias('target'),pl.lit('accepted_C2').alias('model')))
    a=pl.read_parquet(REFERENCES['ensemble']).filter(pl.col('horizon')==1)
    rows.append(a.select('origin_year','player_id',pl.col('ensemble_p').alias('probability')).with_columns(pl.lit('next_year').alias('target'),pl.lit('earlier_ensemble').alias('model')))
    a=pl.read_parquet(REFERENCES['paths']).filter(~pl.col('cold')&(pl.col('horizon')==3)&(pl.col('origin_year')<=2022)&pl.col('method').is_in(['A1','F1']))
    for target,col in [('arrival_three','p_no_mlb'),('regular_three','p_regular_workload')]:
        rows.append(a.select('origin_year','player_id',pl.col('method').alias('model'),
            ((1-pl.col(col)) if target=='arrival_three' else pl.col(col)).alias('probability')).with_columns(pl.lit(target).alias('target')))
    return pl.concat(rows,how='diagonal_relaxed')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'fits').mkdir(exist_ok=True)
    panel,arms,sources=assemble()
    if args.freeze:
        if (OUT/'prefit-manifest.json').exists():raise ValueError('Already frozen')
        panel.write_parquet(OUT/'input-panel.parquet')
        save(OUT/'prefit-manifest.json',{'hashes':hashes(),'arms':arms,'sources':sources,'folds':FOLDS,
            'panel_sha256':sha256_file(OUT/'input-panel.parquet'),'versions':{k:importlib.metadata.version(k) for k in ('numpy','polars','scikit-learn','lightgbm')},
            'protected_outcomes_used':False})
        print(json.dumps({'frozen':True,'features':{k:len(v) for k,v in arms.items()}}));return
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes() and pre['arms']==arms
    assert sha256_file(OUT/'input-panel.parquet')==pre['panel_sha256']
    assert panel.equals(pl.read_parquet(OUT/'input-panel.parquet'))
    frames=[];notes=[]
    for year,target,cold in FOLDS:
        test=panel.filter(pl.col('origin_year')==year)
        train=eligible(panel,year,target,test['player_id'].to_list() if cold else ())
        if cold:assert not set(train['player_id'])&set(test['player_id'])
        for engine in (('lightgbm',) if cold else ('lightgbm','logistic')):
            for arm in (('B2','R') if cold or engine=='logistic' else arms):
                path=OUT/'fits'/f'{year}-{target}-{int(cold)}-{engine}-{arm}.parquet'
                if path.exists() and path.with_suffix('.json').exists():
                    f=pl.read_parquet(path);note=json.loads(path.with_suffix('.json').read_text())
                    assert note['prediction_sha256']==sha256_file(path)
                else:
                    print(f'{year} {target} cold={cold} {engine} {arm}',flush=True)
                    prob,note=fit_probability(train,test,arms[arm],target,engine)
                    f=test.select('origin_year','player_id','age','stage','prospect','recent_debut','prior_debut','mlb_pa_lag0').with_columns(
                        pl.Series('actual',target_values(test,target)),pl.Series('probability',prob),
                        pl.lit(target).alias('target'),pl.lit(arm).alias('arm'),pl.lit(engine).alias('engine'),
                        pl.lit(cold).alias('cold'),pl.lit(year<2020<=year+TARGETS[target]).alias('pandemic'))
                    f.write_parquet(path)
                    note.update({'origin':year,'target':target,'cold':cold,'arm':arm,'engine':engine,
                        'test_rows':test.height,'prediction_sha256':sha256_file(path),
                        'training_current_park_rows':int(train['park0__available'].sum()),
                        'training_current_context_rows':int(train['context0__available'].sum()),
                        'training_current_raw_rows':int(train['raw0__available'].sum())})
                    save(path.with_suffix('.json'),note)
                frames.append(f);notes.append(note)
    combined=pl.concat(frames);combined.write_parquet(OUT/'predictions.parquet')
    references().write_parquet(OUT/'reference-predictions.parquet')
    # Only unavailable future information is changed; test features at cutoff stay intact.
    m=panel
    for h in (1,2,3):
        m=m.with_columns(pl.when(pl.col('origin_year')+h>2022).then(9999.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'))
    m=m.with_columns(*[pl.when(pl.col('origin_year')>2022).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in arms['R']])
    mp,_=fit_probability(eligible(m,2022,'regular_three'),m.filter(pl.col('origin_year')==2022),arms['R'],'regular_three')
    old=combined.filter((pl.col('origin_year')==2022)&(pl.col('target')=='regular_three')&~pl.col('cold')&(pl.col('engine')=='lightgbm')&(pl.col('arm')=='R'))
    np.testing.assert_array_equal(mp,old['probability'])
    assert hashes()==pre['hashes']
    save(OUT/'fit-manifest.json',{'fits':notes,'future_mutation_maximum_difference':float(np.max(abs(mp-old['probability'].to_numpy()))),
        'prefit_sha256':sha256_file(OUT/'prefit-manifest.json'),
        'files':{n:sha256_file(OUT/n) for n in ('predictions.parquet','reference-predictions.parquet')},
        'production_forecasts_changed':False,'protected_outcomes_used':False})
    print(json.dumps({'fits':len(notes),'rows':combined.height,'future_mutation_passed':True}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
