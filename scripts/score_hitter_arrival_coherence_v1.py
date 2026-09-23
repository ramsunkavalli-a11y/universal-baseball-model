"""Score the frozen arrival repair including population totals and actual delivery."""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import polars as pl

from fit_hitter_arrival_coherence_v1 import OUT,save
from universal_baseball.hitter_arrival_coherence import age_band
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file


def loss_frame(f, prefix):
    y=f['actual_value'].to_numpy(); pa=f['actual_pa'].to_numpy(); active=(pa>0).astype(float)
    v=f[prefix+'_value'].to_numpy(); workload=f[prefix+'_pa'].to_numpy(); prob=np.clip(f[prefix+'_p'].to_numpy(),1e-10,1-1e-10)
    return f.with_columns(pl.Series('value_mse',(v-y)**2),pl.Series('value_mae',abs(v-y)),pl.Series('pa_mse',(workload-pa)**2),
        pl.Series('brier',(prob-active)**2),pl.Series('log_loss',-active*np.log(prob)-(1-active)*np.log1p(-prob)))


def means(f,prefix):
    if f.is_empty(): return None
    losses=loss_frame(f,prefix)
    out={'rows':f.height,'origins':sorted(f['origin_year'].unique().to_list()),'active':int((f['actual_pa']>0).sum())}
    out.update(losses.group_by('origin_year').agg(*[pl.col(c).mean() for c in ['value_mse','value_mae','pa_mse','brier','log_loss']]).select(pl.exclude('origin_year').mean()).to_dicts()[0])
    out['value_rmse']=out['value_mse']**.5;out['pa_rmse']=out['pa_mse']**.5
    return out


def totals(f,prefix):
    return f.group_by('origin_year','horizon').agg(pl.len(),pl.col('actual_pa').sum(),pl.col('actual_value').sum(),
        (pl.col('actual_pa')>0).sum().alias('actual_active'),pl.col(prefix+'_pa').sum().alias('predicted_pa'),
        pl.col(prefix+'_value').sum().alias('predicted_value'),pl.col(prefix+'_p').sum().alias('predicted_active')).sort('origin_year','horizon')


def aggregate_error(f,prefix):
    g=totals(f,prefix)
    return {'pa':float((g['predicted_pa']-g['actual_pa']).abs().mean()),'value':float((g['predicted_value']-g['actual_value']).abs().mean())}


def cumulative(f):
    g=f.group_by('origin_year','player_id').agg(pl.len().alias('n'),pl.col('horizon').n_unique().alias('nh'),pl.col('pandemic').any(),
        pl.col('C1_affected').any(),pl.col('C2_affected').any(),pl.col('level').first(),pl.col('age_band').first(),
        *[pl.col(c).sum().alias(c) for c in ['actual_value','old_value','C1_value','C2_value','actual_pa','old_pa','C1_pa','C2_pa']])
    return g.filter((pl.col('n')==3)&(pl.col('nh')==3)&~pl.col('pandemic'))


def cum_compare(f,prefix):
    if f.is_empty(): return None
    f=f.with_columns(((pl.col(prefix+'_value')-pl.col('actual_value'))**2).alias('loss1'),
        ((pl.col('old_value')-pl.col('actual_value'))**2).alias('loss0'),
        (pl.col(prefix+'_value')-pl.col('actual_value')).abs().alias('mae1'),
        (pl.col('old_value')-pl.col('actual_value')).abs().alias('mae0'))
    return {'paired':compare_losses(f,'loss1','loss0'),
        'mae_old':float(f.group_by('origin_year').agg(pl.col('mae0').mean())['mae0'].mean()),
        'mae_new':float(f.group_by('origin_year').agg(pl.col('mae1').mean())['mae1'].mean()),
        'rows':f.height,'origins':sorted(f['origin_year'].unique().to_list())}


def main():
    raw=pl.read_parquet(OUT/'predictions.parquet').with_columns(pl.col('age').map_elements(age_band,return_dtype=pl.String,skip_nulls=False).alias('age_band'))
    hist=raw.filter((pl.col('origin_year')<2025)&~pl.col('cold'))
    early=hist.filter(pl.col('horizon')<=3);normal=early.filter(~pl.col('pandemic'))
    cum=cumulative(early)
    report={'protected_outcomes_used':False,'development_only':True,'historical_prediction_sha256':sha256_file(OUT/'predictions.parquet'),'scopes':{}}
    aggregate_rows=[]
    for prefix in ['C1','C2']:
        affected=normal.filter(pl.col(prefix+'_affected'))
        annual={}
        for h in (1,2,3):
            f=affected.filter(pl.col('horizon')==h)
            annual[str(h)]={'old':means(f,'old'),'new':means(f,prefix)}
        cells=[]
        for (h,level,band),f in affected.partition_by('horizon','level','age_band',as_dict=True).items():
            old,new=means(f,'old'),means(f,prefix)
            supported=f.height>=100 and f['origin_year'].n_unique()>=3 and old['active']>=10
            cells.append({'horizon':h,'level':level,'age_band':band,'supported':supported,'old':old,'new':new})
        ac=cum_compare(cum.filter(pl.col(prefix+'_affected')),prefix); overall=cum_compare(cum,prefix)
        agg_old,agg_new=aggregate_error(affected,'old'),aggregate_error(affected,prefix)
        gates={'cumulative_affected_interval':ac['paired']['interval95'][1]<0,'cumulative_affected_mae':ac['mae_new']<=ac['mae_old'],
            'annual_value_guard':all(r['new']['value_mse']<=1.05*r['old']['value_mse'] for r in annual.values()),
            'annual_pa_probability_guards':all(r['new'][k]<=1.05*r['old'][k] for r in annual.values() for k in ['pa_mse','brier','log_loss']),
            'supported_cell_value_guards':all(r['new']['value_mse']<=1.05*r['old']['value_mse'] for r in cells if r['supported']),
            'aggregate_pa_improves':agg_new['pa']<=agg_old['pa'],'aggregate_value_improves':agg_new['value']<=agg_old['value'],
            'overall_cumulative_not_worse':overall['paired']['delta']<=0}
        # The harmonized prior ensemble is a secondary comparator, not the delivered forecast.
        secondary=affected.with_columns(pl.col('ensemble').alias('ens_pa'),pl.col('ensemble_p').alias('ens_p'),pl.col('ensemble_product').alias('ens_value'))
        cold=raw.filter(pl.col('cold')&pl.col(prefix+'_affected')&~pl.col('pandemic'))
        sensitive={}
        for strength in (50,200):
            fs=affected.with_columns(pl.col(f'pa{strength}').alias('s_pa'),pl.col(f'p{strength}').alias('s_p'),pl.col(f'value{strength}').alias('s_value'))
            sensitive[str(strength)]=means(fs,'s')
        report['scopes'][prefix]={'passes':all(gates.values()),'gates':gates,'annual':annual,'cells':cells,
            'cumulative_affected':ac,'cumulative_overall':overall,'aggregate_old':agg_old,'aggregate_new':agg_new,
            'secondary_ensemble':means(secondary,'ens'),'pooled_candidate':means(affected,prefix),
            'cold_start':{'old':means(cold,'old'),'new':means(cold,prefix)},'prior_sensitivity':sensitive}
        for label,subset in [('all',normal),('affected',affected),('rookie',normal.filter(pl.col('level')=='RK'))]:
            for method in ['old',prefix]:
                aggregate_rows.append(totals(subset,method).with_columns(pl.lit(prefix).alias('scope'),pl.lit(label).alias('population'),pl.lit(method).alias('method')))
    report['selected_scope']=next((s for s in ['C1','C2'] if report['scopes'][s]['passes']),None)
    # Diagnostics for later horizons cannot authorize broadening H1–3 adoption.
    report['long_horizons']={}
    for h in (4,5,6):
        f=hist.filter(pl.col('horizon')==h)
        report['long_horizons'][str(h)]={s:{'old':means(f.filter(pl.col(s+'_affected')),'old'),'new':means(f.filter(pl.col(s+'_affected')),s)} for s in ['C1','C2']}
    report['expanded_target']={}
    ledger=pl.read_parquet('model_artifacts/multiyear-hitter-components-v1-2026-09-22/integrated-predictions.parquet')
    e=early.join(ledger.select('origin_year','player_id','horizon','actual','selected','complete_components'),on=['origin_year','player_id','horizon'],validate='1:1')
    for s in ['C1','C2']:
        e=e.with_columns((pl.col('selected')-pl.col('old_value')).alias('old_components'))
        ratio=pl.when(pl.col('old_pa')>0).then(pl.col(s+'_pa')/pl.col('old_pa')).otherwise(1.)
        e=e.with_columns((pl.col(s+'_value')+pl.col('old_components')*ratio).alias('expanded_new'))
        q=e.group_by('origin_year','player_id').agg(pl.len().alias('n'),pl.col('pandemic').any(),pl.col('complete_components').all(),
            pl.col(s+'_affected').any(),pl.col('actual').sum().alias('actual_value'),pl.col('selected').sum().alias('old_value'),pl.col('expanded_new').sum().alias(s+'_value'))
        q=q.filter((pl.col('n')==3)&~pl.col('pandemic')&pl.col('complete_components'))
        report['expanded_target'][s]={'overall':cum_compare(q,s),'affected':cum_compare(q.filter(pl.col(s+'_affected')),s)}
    selected=report['selected_scope']
    report['combined_update_allowed']=bool(selected and report['expanded_target'][selected]['overall']['paired']['delta']<=0)
    report['later_horizons_update_allowed']=False
    pl.concat(aggregate_rows).write_parquet(OUT/'aggregate-checks.parquet')
    save(OUT/'score-report.json',report)
    print(json.dumps({'selected_scope':selected,'combined_update_allowed':report['combined_update_allowed'],
        'gates':{s:r['gates'] for s,r in report['scopes'].items()},'cumulative':{s:r['cumulative_affected'] for s,r in report['scopes'].items()}},indent=2))


if __name__=='__main__': main()
