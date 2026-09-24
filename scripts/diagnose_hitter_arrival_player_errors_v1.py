"""Descriptive player-error audit; exact replays only, no revised forecasts."""
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from scipy.special import expit
from threadpoolctl import threadpool_limits
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_detail_arrival import eligible,target_values
from universal_baseball.hitter_canceled_season import matrix
from universal_baseball.hitter_structural_missingness import augmented_rows,attach_outages,FLAGS
from universal_baseball.hitter_model_tournament import make_engine_models
from universal_baseball.storage import sha256_file

ROOT=Path('reports/generated')
OUT=ROOT/'hitter-arrival-player-errors-v1'
OLD=Path('C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/universal-baseball-model/reports/generated')
PANEL=ROOT/'hitter-detail-arrival-v1/input-panel.parquet'
PRED=Path('model_artifacts/hitter-era-schedule-v1-2026-09-23/predictions.parquet')
FIELD=OLD/'position-capacity-source/historical/reports/generated/position-role-historical-source/tables/historical_fielding_usage.parquet'
PATH='path0__level_path__'


def assemble():
    panel=pl.read_parquet(PANEL)
    q=pl.read_parquet(PRED).filter(pl.col('prospect')&pl.col('arm').is_in(['R','AE']))
    q=q.pivot(on='arm',index=['origin_year','player_id'],values='probability')
    f=panel.join(q,on=['origin_year','player_id'],how='inner',validate='1:1')
    field=pl.read_parquet(FIELD).filter((pl.col('season')<=2024)&(pl.col('position_abbreviation')!='P'))
    pos=field.group_by('season','player_id','position_abbreviation').agg(pl.col('fielding_outs').sum(),pl.col('games_started').sum())
    pos=pos.sort(['season','player_id','fielding_outs','games_started','position_abbreviation'],descending=[False,False,True,True,False])
    pos=pos.unique(['season','player_id'],keep='first',maintain_order=True).select(
        pl.col('season').alias('origin_year'),'player_id',pl.col('position_abbreviation').alias('historical_position'))
    f=f.join(pos,on=['origin_year','player_id'],how='left',validate='1:1').with_columns(
        (pl.col('pa_h1')>0).cast(pl.Int8).alias('arrived'),
        pl.col('historical_position').fill_null('Unknown'),
        pl.when(pl.col('pa_lag0')<200).then(pl.lit('<200')).when(pl.col('pa_lag0')<400).then(pl.lit('200-399')).otherwise(pl.lit('400+')).alias('pa_band'),
        pl.when(pl.col('age')<=23).then(pl.lit('23 or younger')).otherwise(pl.lit('24+')).alias('age_band'),
        pl.when(pl.col('AE')<.1).then(pl.lit('<10%')).when(pl.col('AE')<.5).then(pl.lit('10-49%')).otherwise(pl.lit('50%+')).alias('probability_band'),
    ).with_columns(((pl.col('AE')-pl.col('arrived'))**2-(pl.col('R')-pl.col('arrived'))**2).alias('brier_change'))
    assert f.height==q.height and f['origin_year'].max()==2024
    assert f['pa_h1'].is_not_null().all()
    return panel,f


def summaries(f,columns):
    return f.group_by(*columns).agg(pl.len().alias('players'),pl.col('arrived').sum().alias('arrivals'),
        pl.col('R').sum().alias('R_expected'),pl.col('AE').sum().alias('AE_expected'),
        ((pl.col('AE')<.1)&(pl.col('pa_h1')>0)).sum().alias('low_probability_arrivals'),
        ((pl.col('AE')<.1)&(pl.col('pa_h1')>=200)).sum().alias('low_probability_200pa'),
        ((pl.col('AE')>=.5)&(pl.col('pa_h1')==0)).sum().alias('high_probability_nonarrivals'),
        (pl.col('AE')-pl.col('arrived')).mean().alias('mean_calibration_error'),
        pl.col('brier_change').mean()).sort(columns).to_dicts()


CASE_COLS=['origin_year','player_id','player_name','age','level','historical_position','pa_lag0','pa_lag1','pa_lag2',
    'on_40man','R','AE','pa_h1','pa_h2','pa_h3','strikeout_rate_lag0','ubb_rate_lag0','home_run_rate_lag0',
    PATH+'primary_level_change',PATH+'terminal_level_rank',PATH+'terminal_level_share',
    PATH+'returned_after_partial_promotion',PATH+'substantial_same_level_repeat','raw0__available','brier_change']


def casebooks(f):
    return {
        'low_probability_200pa':f.filter(pl.col('pa_h1')>=200).sort('AE').head(30).select(CASE_COLS).to_dicts(),
        'highest_probability_nonarrivals':f.filter(pl.col('pa_h1')==0).sort('AE',descending=True).head(30).select(CASE_COLS).to_dicts(),
        'largest_help':f.sort('brier_change').head(20).select(CASE_COLS).to_dicts(),
        'largest_harm':f.sort('brier_change',descending=True).head(20).select(CASE_COLS).to_dicts(),
        '2021_low_probability_arrivals':f.filter((pl.col('origin_year')==2021)&(pl.col('pa_h1')>0)).sort('AE').head(30).select(CASE_COLS).to_dicts(),
    }


def family(c):
    if c=='on_40man':return 'October 15 roster membership'
    if c in FLAGS or c.startswith('missing_'):return 'Missing annual history / outage'
    if c.startswith('age'):return 'Age'
    if c.startswith('path'):return 'Progression / level tenure'
    if c.startswith(('level_','share_','log_pa_','log_mlb_pa_')):return 'Level and workload'
    if c.startswith(('raw','park','pitch','context')):return 'Detailed contact / context'
    return 'Other aggregate history'


def explain(panel,f,cases):
    columns=json.loads((ROOT/'hitter-detail-arrival-v1/prefit-manifest.json').read_text())['arms']['R']
    columns=[c for c in columns if c!='reorganization_era']+FLAGS
    output=[]
    for year in (2021,2022):
        print(f'Exact AE replay and selected-case contributions {year}',flush=True)
        train=eligible(panel,year,'next_year'); aug=augmented_rows(train,True)
        query=attach_outages(panel.filter(pl.col('origin_year')==year))
        x=matrix(aug,columns);keep=np.array([len(np.unique(x[np.isfinite(x[:,j]),j]))>1 for j in range(x.shape[1])])
        used=[c for c,k in zip(columns,keep) if k]
        model=make_engine_models('lightgbm',417,'balanced').classifier.set_params(n_jobs=4)
        model.fit(x[:,keep],target_values(aug,'next_year'),sample_weight=aug['fit_weight'].to_numpy()/float(train['identity_weight'].mean()))
        actual=np.clip(model.predict_proba(matrix(query,used))[:,1],1e-6,1-1e-6)
        saved=pl.read_parquet(PRED).filter((pl.col('origin_year')==year)&(pl.col('arm')=='AE'))
        np.testing.assert_array_equal(query['player_id'],saved['player_id']);np.testing.assert_array_equal(actual,saved['probability'])
        ids={r['player_id'] for group in cases.values() for r in group if r['origin_year']==year}
        q=query.filter(pl.col('player_id').is_in(sorted(ids)));tx=matrix(q,used)
        contributions=model.booster_.predict(tx,pred_contrib=True)
        base_p=model.predict_proba(tx)[:,1]
        np.testing.assert_allclose(expit(contributions.sum(axis=1)),base_p,rtol=1e-10,atol=1e-12)
        # Diagnostic sensitivity only. Do not treat flipping a flag as a causal
        # intervention or a validated December-31 reforecast.
        flipped=q.with_columns((1-pl.col('on_40man')).alias('on_40man'))
        flip_p=model.predict_proba(matrix(flipped,used))[:,1]
        for i,row in enumerate(q.select('origin_year','player_id','player_name','on_40man').to_dicts()):
            byfamily={}
            for c,v in zip(used,contributions[i,:-1]):byfamily[family(c)]=byfamily.get(family(c),0.)+float(v)
            order=np.argsort(contributions[i,:-1])
            terms=lambda ix:[{'feature':used[j],'value':None if not np.isfinite(tx[i,j]) else float(tx[i,j]),
                             'log_odds_contribution':float(contributions[i,j])} for j in ix]
            output.append({**row,'probability':float(base_p[i]),'roster_flag_flip_probability':float(flip_p[i]),
                'base_log_odds':float(contributions[i,-1]),'family_log_odds':byfamily,
                'largest_downward':terms(order[:8]),'largest_upward':terms(order[-8:][::-1]),'exact_replay':True})
    return output


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    panel,f=assemble();cases=casebooks(f)
    groups={k:summaries(f,['origin_year',k]) for k in ['level','stage','age_band','pa_band','on_40man','historical_position','probability_band',
        PATH+'substantial_same_level_repeat',PATH+'returned_after_partial_promotion']}
    timing=[]
    for year in (2021,2022):
        q=f.filter((pl.col('origin_year')==year)&(pl.col('AE')>=.5)&(pl.col('pa_h1')==0))
        assert q['pa_h2'].is_not_null().all() and q['pa_h3'].is_not_null().all()
        timing.append({'origin':year,'high_probability_nonarrivals':q.height,
           'arrived_in_year_2_or_3':q.filter((pl.col('pa_h2')>0)|(pl.col('pa_h3')>0)).height,
           'no_mlb_pa_through_year_3':q.filter((pl.col('pa_h2')==0)&(pl.col('pa_h3')==0)).height})
    explanations=explain(panel,f,cases)
    roster=[]
    for folder in ('opportunity-40man-pre2020','opportunity-40man-history'):
        path=OLD/folder/'tables/historical_40man_membership.parquet'
        roster.extend(pl.read_parquet(path).filter(pl.col('season')<=2024).group_by('season','as_of_date').len().sort('season').to_dicts())
    sources={str(p):sha256_file(p) for p in [PANEL,PRED,FIELD,Path(__file__)]}
    f.select(CASE_COLS+['stage','arrived','pa_band','age_band','probability_band']).write_parquet(OUT/'player-cases.parquet')
    report={'scope':'Descriptive out-of-sample next-year arrival errors; AE research candidate, not live forecast',
        'sources':sources,'groups':groups,'cases':cases,'timing':timing,'explanations':explanations,
        'roster_source_dates':[{**r,'as_of_date':str(r['as_of_date'])} for r in roster],
        'thresholds':{'low_probability':.1,'high_probability':.5,'substantial_future_pa':200},
        'limits':['Outcome-selected examples are not evidence of systematic bias by themselves',
                  'Descriptive slices overlap and are not independent tests or causal attribution',
                  'Tree contributions allocate model log odds, not true baseball causes',
                  'A roster-flag flip is sensitivity, not a validated revised forecast',
                  'Only 2021/2022 used for three-year delay accounting; no protected outcomes',
                  'Historical position is a diagnostic join, not an arrival-model input'],
        'production_changed':False,'protected_outcomes_used':False}
    save(OUT/'report.json',report)
    lines=['# Which players slip through the arrival model?','',report['scope'],
        '', 'Probabilities below are the AE research model: outage-aware, no explicit era flag.',
        'They concern any MLB PA next year, not batting ability, WAR or eventual career success.',
        'Original R probabilities and diagnostic features are retained in the JSON and player-case table.',
        '', '## Examples','']
    for name,rows in cases.items():
        lines += ['### '+name,'','| Origin | Player | Level | Age | Current PA | Predicted arrival | Next MLB PA | Year 2 PA | Year 3 PA |',
                  '|---|---|---|---:|---:|---:|---:|---:|---:|']
        for r in rows:
            value=lambda k:'—' if r[k] is None else str(r[k])
            lines.append(f"| {r['origin_year']} | {r['player_name']} | {r['level']} | {r['age']:.0f} | {value('pa_lag0')} | {r['AE']:.1%} | {value('pa_h1')} | {value('pa_h2')} | {value('pa_h3')} |")
        lines.append('')
    lines += ['## Timing rather than ultimate failure','',json.dumps(timing,indent=2),'',
              '## Limits','',*['- '+s for s in report['limits']],'']
    (OUT/'casebook.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
    print(json.dumps({'case_rows':f.height,'explained':len(explanations),'timing':timing,'exact_replays':2,'production_changed':False}))


if __name__=='__main__':
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):main()
