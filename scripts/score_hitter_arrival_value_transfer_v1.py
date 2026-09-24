"""Fixed PA/value transfer gates with equal-origin, whole-player comparisons."""
import json
import numpy as np
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_arrival_value_transfer_v1 import OUT
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

GROUPS={'all':pl.lit(True),'prospects':pl.col('prospect'),
    'upper_prospects':pl.col('prospect')&(pl.col('stage')=='Upper minors'),
    'lower_prospects':pl.col('prospect')&(pl.col('stage')=='Lower minors'),
    'upper_under23':pl.col('prospect')&(pl.col('stage')=='Upper minors')&(pl.col('age')<23),
    'returners':pl.col('minor_returner'),'recent_debut':pl.col('recent_debut'),
    'established_200pa':(pl.col('stage')=='Current MLB')&(pl.col('mlb_pa_lag0')>=200)}
ARMS=('B','R','F','U','E')


def average(f,c):
    return float(f.group_by('origin_year').agg(pl.col(c).mean())[c].mean())


def errors(f,arm,target):
    c=arm+'_'+target;actual='actual_'+target
    g=f.with_columns(((pl.col(c)-pl.col(actual))**2).alias('_sq'),
        (pl.col(c)-pl.col(actual)).abs().alias('_abs'),(pl.col(c)-pl.col(actual)).alias('_bias'))
    mse=average(g,'_sq')
    totals=g.group_by('origin_year').agg(pl.col(c).sum().alias('predicted'),pl.col(actual).sum().alias('actual')).sort('origin_year')
    return {'mse':mse,'rmse':mse**.5,'mae':average(g,'_abs'),'bias':average(g,'_bias'),
        'mean_predicted':average(g,c),'mean_actual':average(g,actual),
        'aggregate_absolute_error':float((totals['predicted']-totals['actual']).abs().mean()),'totals':totals.to_dicts()}


def probability(f,arm):
    p=np.clip(f[arm+'_p'].to_numpy(),1e-6,1-1e-6);y=(f['actual_pa'].to_numpy()>0).astype(float)
    g=f.with_columns(pl.Series('_brier',(p-y)**2),pl.Series('_log',-y*np.log(p)-(1-y)*np.log1p(-p)))
    return {'brier':average(g,'_brier'),'log_loss':average(g,'_log'),'expected':float(p.sum()),'observed':int(y.sum())}


def summary(f,cumulative=False):
    if not f.height:return None
    return {'rows':f.height,'players':f['player_id'].n_unique(),'origins':sorted(f['origin_year'].unique().to_list()),
        'active':int((f['actual_pa']>0).sum()),'arms':{a:{'pa':errors(f,a,'pa'),'value':errors(f,a,'value'),
        **({} if cumulative else {'probability':probability(f,a)})} for a in ARMS}}


def paired(f,candidate,reference,target):
    a=candidate+'_'+target;b=reference+'_'+target;y='actual_'+target
    g=f.with_columns(((pl.col(a)-pl.col(y))**2).alias('_a'),((pl.col(b)-pl.col(y))**2).alias('_b'))
    return compare_losses(g,'_a','_b',draws=2000)


def cumulative(f):
    fields=['actual_pa','actual_value','actual_expanded','B_expanded',
            *[a+'_'+t for a in ARMS for t in ('pa','value')],
            *[a+'_'+t for a in ('R','F','U') for t in ('expanded','expanded_fixed')]]
    return f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        pl.col('complete_components').all(),*[pl.col(c).first() for c in ('player_name','age','stage','prospect','prior_debut','minor_returner','recent_debut','mlb_pa_lag0')],
        *[pl.col(c).sum() for c in fields]).filter((pl.col('_n')==3)&(pl.col('_nh')==3)).sort('origin_year','player_id')


def expanded(f):
    f=f.filter(pl.col('complete_components')&pl.col('actual_expanded').is_finite())
    if not f.height:return None
    arms={a:errors(f,a,'expanded') for a in ('B','R','F','U')}
    fixed=f.with_columns(pl.col('F_expanded_fixed').alias('F_expanded'))
    return {'rows':f.height,'origins':sorted(f['origin_year'].unique().to_list()),'active':int((f['actual_pa']>0).sum()),
        'arms':arms,'F_fixed_other_components':errors(fixed,'F','expanded')}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert sha256_file(OUT/'predictions.parquet')==fit['prediction_sha256']
    f=pl.read_parquet(OUT/'predictions.parquet');c=cumulative(f)
    report={'annual':{},'cumulative':{},'expanded':{},'protected_outcomes_used':False,'production_forecasts_changed':False}
    for h in (1,2,3):
        print(f'Score Year {h}',flush=True);q=f.filter(pl.col('horizon')==h);p=q.filter(pl.col('prospect'))
        report['annual'][str(h)]={'groups':{n:summary(q.filter(e)) for n,e in GROUPS.items()},
            'by_origin_prospects':{str(y):summary(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
            'paired_prospects':{t:{r:paired(p,'F',r,t) for r in ('B','R','E')} for t in ('pa','value')},
            'expanded':{n:expanded(q.filter(GROUPS[n])) for n in ('all','prospects','upper_prospects','lower_prospects','upper_under23')}}
    print('Score cumulative three-year totals',flush=True)
    report['cumulative']={'groups':{n:summary(c.filter(e),True) for n,e in GROUPS.items()},
        'by_origin_prospects':{str(y):summary(g,True) for (y,),g in c.filter(pl.col('prospect')).partition_by('origin_year',as_dict=True).items()},
        'paired_prospects':{t:{r:paired(c.filter(pl.col('prospect')),'F',r,t) for r in ('B','R','E')} for t in ('pa','value')},
        'paired_all_value':paired(c,'F','B','value')}
    for name in ('all','prospects'):
        q=c.filter(GROUPS[name]&pl.col('complete_components')&pl.col('actual_expanded').is_finite())
        report['expanded'][name]={**expanded(q),'paired_F_B':paired(q,'F','B','expanded')}
    cs=report['cumulative']['groups']['prospects']['arms'];cp=report['cumulative']['paired_prospects'];guard={}
    for h,record in report['annual'].items():
        for name in ('prospects','upper_prospects','lower_prospects','upper_under23'):
            s=record['groups'][name]
            if s['rows']>=200 and s['active']>=10:
                guard[h+'/'+name]=all(s['arms']['F'][t]['mse']<=1.05*s['arms']['B'][t]['mse'] for t in ('pa','value'))
    gates={'cumulative_intervals':all(cp[t][r]['interval95'][1]<0 for t in ('pa','value') for r in ('B','R')),
        'cumulative_mae':all(cs['F'][t]['mae']<=cs['B'][t]['mae'] for t in ('pa','value')),
        'cumulative_majority':all(cp[t][r]['improving_origins']>=2 for t in ('pa','value') for r in ('B','R')),
        'annual_and_slice_harm_guards':all(guard.values()),
        'annual_probability_guards':all(s['groups']['prospects']['arms']['F']['probability'][k]<=1.05*s['groups']['prospects']['arms']['B']['probability'][k]
            for s in report['annual'].values() for k in ('brier','log_loss')),
        'ensemble_pa_each_horizon':all(s['groups']['prospects']['arms']['F']['pa']['mse']<s['groups']['prospects']['arms']['E']['pa']['mse'] for s in report['annual'].values()),
        'aggregate_totals':all(cs['F'][t]['aggregate_absolute_error']<=cs['B'][t]['aggregate_absolute_error'] for t in ('pa','value')),
        'all_player_cumulative_value':report['cumulative']['paired_all_value']['delta']<=0,
        'expanded_cumulative_no_harm':all(s['paired_F_B']['delta']<=0 for s in report['expanded'].values()),
        'expanded_annual_guards':all(s['arms']['F']['mse']<=1.05*s['arms']['B']['mse']
            for a in report['annual'].values() for s in a['expanded'].values() if s and s['rows']>=200 and s['active']>=10)}
    report['gates']=gates;report['slice_guards']=guard;report['research_transfer_supported']=all(gates.values())
    report['scaling_audit']={a:{'min_ratio':float((f[a+'_pa']/f['B_pa']).min()),'max_ratio':float((f[a+'_pa']/f['B_pa']).max()),
        'ratio_over10_rows':int((f[a+'_pa']/f['B_pa']>10).sum())} for a in ('R','F','U')}
    # Descriptive only: never use future participation to select or fit an arm.
    report['future_selected_diagnostics']={str(h):{str(active):summary(f.filter((pl.col('horizon')==h)&pl.col('prospect')&((pl.col('actual_pa')>0)==active))) for active in (False,True)} for h in (1,2,3)}
    report['hashes']={n:sha256_file(OUT/n) for n in ('predictions.parquet','fit-manifest.json','prefit-manifest.json','references.parquet')}
    save(OUT/'score-report.json',report)
    c.write_parquet(OUT/'cumulative-predictions.parquet')
    print(json.dumps({'gates':gates,'prospect_annual_rmse':{h:{a:{t:s['groups']['prospects']['arms'][a][t]['rmse'] for t in ('pa','value')} for a in ARMS} for h,s in report['annual'].items()},
        'cumulative_prospect_rmse':{a:{t:cs[a][t]['rmse'] for t in ('pa','value')} for a in ARMS}},indent=2))


if __name__=='__main__':main()
