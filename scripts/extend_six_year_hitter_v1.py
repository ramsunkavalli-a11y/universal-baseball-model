"""Fit the predeclared long-horizon extension; protected 2026 outcomes forbidden."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits

from evaluate_multiyear_hitter_v1 import ridge
from fit_multiyear_hitter_components_v1 import load_sources, running_history, reference, benchmark_rates, ROLE, OLD
from universal_baseball.six_year_hitter import extend_labels, mature_mask
from universal_baseball.multiyear_hitter_components import COMPONENTS, START
from universal_baseball.opportunity_model_v2 import OpportunityFold, fit_universal_hitter_opportunity_form
from universal_baseball.playing_time_model import PT_FORM_U, build_playing_time_design, predict_playing_time_hurdle
from universal_baseball.storage import sha256_file

BASE=Path('reports/generated/multiyear-hitter-v1')
COMP=Path('reports/generated/multiyear-hitter-components-v1')
OLD_PACKAGE=Path('model_artifacts/multiyear-hitter-components-v1-2026-09-22')
OUT=Path('reports/generated/six-year-hitter-v1')
PLAN=Path('docs/six-year-hitter-extension-v1-plan.md')


def save(path, data):
    path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def opportunity(panel, cutoff, h):
    train=panel.filter(pl.Series(mature_mask(panel,cutoff,h)))
    test=panel.filter(pl.col('origin_year')==cutoff)
    def predictors(f):
        return f.select('player_id',pl.col('age').alias('age_years'),'as_of_level_group','on_40man',
            pl.col('mlb_pa_lag0').fill_null(0).alias('current_season_mlb_pa'),
            (pl.col('pa_lag0').fill_null(0)-pl.col('mlb_pa_lag0').fill_null(0)).alias('current_season_milb_pa'))
    folds=[OpportunityFold(y,y+h,predictors(f),f.select('player_id',pl.col(f'pa_h{h}').cast(pl.Int64).alias('next_year_mlb_pa')))
        for y in sorted(train['origin_year'].unique()) for f in [train.filter(pl.col('origin_year')==y)]]
    fit=fit_universal_hitter_opportunity_form(folds,form=PT_FORM_U)
    return test.select('player_id').join(predict_playing_time_hurdle(fit,build_playing_time_design(predictors(test),form=PT_FORM_U)),
        on='player_id',validate='1:1',maintain_order='left')


def metrics(f, target, columns):
    f=f.filter(pl.col(target).is_not_null())
    if f.is_empty(): return {'rows':0,'origins':[]}
    result={'rows':f.height,'origins':sorted(f['origin_year'].unique().to_list())}
    y=f[target].to_numpy()
    for c in columns:
        g=f.with_columns(pl.Series('sq',(f[c].to_numpy()-y)**2),pl.Series('err',f[c].to_numpy()-y))
        means=g.group_by('origin_year').agg(pl.col('sq').mean(),pl.col('err').mean())
        result[c]={'rmse':float(np.sqrt(means['sq'].mean())),'bias':float(means['err'].mean())}
    return result


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    panel=extend_labels(pl.read_parquet(COMP/'component-panel.parquet'),pl.read_parquet(BASE/'targets.parquet'))
    manifest=json.loads((BASE/'manifest.json').read_text())
    annual=pl.read_parquet(COMP/'annual-component-labels.parquet')
    stats,roles,hashes=load_sources()
    advancement=pl.read_parquet(COMP/'native-advancement-history.parquet')
    steals,advances,_=running_history(stats,advancement)
    sources=[PLAN,Path(__file__),Path('src/universal_baseball/six_year_hitter.py'),BASE/'manifest.json',BASE/'targets.parquet',
        COMP/'component-panel.parquet',COMP/'annual-component-labels.parquet',COMP/'native-advancement-history.parquet',
        OLD_PACKAGE/'forecast-2026-2028.parquet',OLD_PACKAGE/'integrated-predictions.parquet']
    hashes.update({str(p):sha256_file(p) for p in sources})
    save(OUT/'input-manifest.json',{'hashes':hashes,'protected_outcomes_used':False,'plan_frozen_before_scores':True})
    rows=[]; notes=[]
    # Include earlier available folds, but do not attempt fits without >=2 mature origins.
    for year in [*range(2014,2020),2021,2025]:
        test=panel.filter(pl.col('origin_year')==year)
        ref=reference(stats,advancement,year)
        carry_mask=mature_mask(panel,year,3)
        carry=ridge().fit(panel.select(manifest['full_features']).to_numpy()[carry_mask],panel['war_h3'].to_numpy()[carry_mask]).predict(test.select(manifest['full_features']).to_numpy())
        for h in (4,5,6):
            mask=mature_mask(panel,year,h)
            origins=sorted(panel.filter(pl.Series(mask))['origin_year'].unique().to_list())
            if len(origins)<2 or (year!=2025 and year+h>2025): continue
            predictions={}
            for name,features in [('base',manifest['base_features']),('direct',manifest['full_features'])]:
                x=panel.select(features).to_numpy(); tx=test.select(features).to_numpy()
                predictions[name]=ridge().fit(x[mask],panel[f'war_h{h}'].to_numpy()[mask]).predict(tx)
                if year!=2025:
                    dm=mature_mask(panel,year,h,test['player_id'].to_numpy())
                    predictions[name+'_disjoint']=ridge().fit(x[dm],panel[f'war_h{h}'].to_numpy()[dm]).predict(tx)
            pt=opportunity(panel,year,h)
            if pt['player_id'].to_list()!=test['player_id'].to_list(): raise ValueError('PA row order changed')
            rates=benchmark_rates(test,roles,year,h,steals,advances,ref)
            f=test.select('origin_year','player_id','stage','age',pl.col(f'war_h{h}').alias('actual_batting'),pl.col(f'pa_h{h}').alias('actual_pa')).with_columns(
                pl.lit(h).alias('horizon'),pl.lit(year<2020<=year+h).alias('pandemic'),pl.Series('carry_h3',carry),
                pl.Series('activity',pt['predicted_any_mlb_pa_probability']),pl.Series('expected_pa',pt['predicted_expected_mlb_pa']),
                *[pl.Series(k,v) for k,v in predictions.items()])
            labels=annual.filter(pl.col('season')==year+h).select('player_id',pl.lit(True).alias('present'),*[pl.col(c).alias(c+'_actual') for c in COMPONENTS])
            f=f.join(labels,on='player_id',how='left',validate='1:1',maintain_order='left')
            for c in COMPONENTS:
                f=f.with_columns(pl.Series(c+'_runs',rates[c]*pt['predicted_expected_mlb_pa'].to_numpy()/600),
                    pl.when(pl.lit(START[c]<=year+h<=2025)).then(pl.when(pl.col('present').is_null()).then(0.).otherwise(pl.col(c+'_actual')))
                    .otherwise(None).alias(c+'_actual'))
            f=f.drop('present').with_columns((pl.col('direct')+sum(pl.col(c+'_runs') for c in COMPONENTS)/10).alias('integrated'),
                (pl.col('actual_batting')+sum(pl.col(c+'_actual') for c in COMPONENTS)/10).alias('actual_integrated'))
            rows.append(f)
            notes.append({'origin':year,'horizon':h,'train_origins':origins,'train_rows':int(mask.sum()),
                'latest_label':int(panel.filter(pl.Series(mask))['origin_year'].max())+h,'test_rows':test.height,
                'disjoint_train_rows':int(mature_mask(panel,year,h,test['player_id'].to_numpy()).sum()) if year!=2025 else None})
            print(f'Completed origin {year}, year {h}',flush=True)
    pred=pl.concat(rows,how='diagonal_relaxed'); pred.write_parquet(OUT/'predictions.parquet')
    save(OUT/'fit-notes.json',notes)
    historical=pred.filter(pl.col('origin_year')<2025)
    report={}
    for h in (4,5,6):
        f=historical.filter(pl.col('horizon')==h)
        cols=['base','direct','carry_h3','base_disjoint','direct_disjoint']
        report[str(h)]={'batting':metrics(f,'actual_batting',cols),
            'normal_paths':metrics(f.filter(~pl.col('pandemic')),'actual_batting',cols),
            'stages':{s:metrics(g,'actual_batting',cols) for (s,),g in f.partition_by('stage',as_dict=True).items()},
            'pa':metrics(f,'actual_pa',['expected_pa']),
            'expanded_value':metrics(f,'actual_integrated',['direct','integrated']),
            'components':{c:metrics(f.with_columns(pl.lit(0.).alias('neutral')),c+'_actual',['neutral',c+'_runs']) for c in COMPONENTS}}
    # Cumulative extension comparison shares the EXACT same earlier-year forecasts.
    early=pl.read_parquet(OLD_PACKAGE/'integrated-predictions.parquet').filter(pl.col('horizon')<=3).group_by('origin_year','player_id').agg(
        pl.len().alias('n_early'),pl.col('batting').sum().alias('early_bat'),pl.col('actual_batting').sum().alias('early_actual_bat'),
        pl.col('selected').sum().alias('early_integrated'),pl.col('actual').sum().alias('early_actual'),
        ((~pl.col('complete_components'))|pl.col('actual').is_null()).sum().alias('early_missing'))
    later=historical.group_by('origin_year','player_id').agg(pl.len().alias('n_later'),
        *[pl.col(c).sum().alias(c) for c in ['direct','base','carry_h3','actual_batting','integrated','actual_integrated']],
        pl.col('actual_integrated').null_count().alias('late_missing'))
    joined=early.join(later,on=['origin_year','player_id'],how='inner',validate='1:1').filter((pl.col('n_early')==3)&(pl.col('n_later')==3))
    joined=joined.with_columns((pl.col('direct')+pl.col('early_integrated')).alias('neutral_tail'),
        *[(pl.col(c)+pl.col('early_bat')).alias(c) for c in ['direct','base','carry_h3']],
        (pl.col('actual_batting')+pl.col('early_actual_bat')).alias('actual_batting'),
        (pl.col('integrated')+pl.col('early_integrated')).alias('integrated'),
        pl.when((pl.col('early_missing')==0)&(pl.col('late_missing')==0)).then(pl.col('actual_integrated')+pl.col('early_actual')).alias('actual_integrated'))
    joined.write_parquet(OUT/'cumulative-predictions.parquet')
    report['cumulative_six_calendar_years']={'batting':metrics(joined,'actual_batting',['base','direct','carry_h3']),
        'expanded':metrics(joined,'actual_integrated',['direct','neutral_tail','integrated']), 'all_paths_cross_2020':True}
    report['status']='development_extension_not_controlled_value_or_confirmation'
    report['no_2026_outcomes']=True
    save(OUT/'score-report.json',report)
    current=pl.read_parquet(OLD_PACKAGE/'forecast-2026-2028.parquet')
    for h in (4,5,6):
        right=pred.filter((pl.col('origin_year')==2025)&(pl.col('horizon')==h)).select('player_id',
            pl.col('direct').alias(f'value_{2025+h}'),pl.col('base').alias(f'base_h{h}'),
            pl.col('integrated').alias(f'integrated_h{h}'),pl.col('expected_pa').alias(f'expected_pa_h{h}'),
            pl.col('activity').alias(f'activity_h{h}'),*[pl.col(c+'_runs').alias(f'{c}_runs_h{h}') for c in COMPONENTS])
        current=current.join(right,on='player_id',how='left',validate='1:1',maintain_order='left')
    current=current.with_columns(sum(pl.col(f'value_{2025+h}') for h in range(1,7)).alias('batting_c6'),
        sum(pl.col(f'integrated_h{h}') for h in range(1,7)).alias('integrated_c6'),
        pl.lit(None,dtype=pl.Float64).alias('full_control_value'),pl.lit('joint_service_path_and_tail_not_validated').alias('control_value_status'))
    current.write_parquet(OUT/'forecast-2026-2031.parquet')
    print(json.dumps({'players':current.height,'fits':len(notes),'report':str(OUT/'score-report.json')},indent=2))


if __name__=='__main__':
    with threadpool_limits(limits=4): main()
