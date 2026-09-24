"""Score fixed workload candidates without fitting another model or selecting a scope."""
import json
import numpy as np
import polars as pl
from fit_hitter_conditional_workload_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_conditional_workload import paired_interval,roles
from universal_baseball.storage import sha256_file

GROUPS={'all':pl.lit(True),'prospects':pl.col('prospect'),'upper':pl.col('prospect')&(pl.col('stage')=='Upper minors'),
    'lower':pl.col('prospect')&(pl.col('stage')=='Lower minors'),
    'young_upper':pl.col('prospect')&(pl.col('stage')=='Upper minors')&(pl.col('age')<23),
    'returners':pl.col('minor_returner'),'established':(pl.col('stage')=='Current MLB')&(pl.col('mlb_pa_lag0')>=200)}
ARMS=('B','I','A','D','M','E')


def mean(f,col):return float(f.group_by('origin_year').agg(pl.col(col).mean())[col].mean())


def errors(f,column):
    q=f.with_columns(((pl.col(column)-pl.col('actual_pa'))**2).alias('_sq'),
        (pl.col(column)-pl.col('actual_pa')).abs().alias('_abs'),(pl.col(column)-pl.col('actual_pa')).alias('_bias'))
    totals=q.group_by('origin_year').agg(pl.col(column).sum().alias('predicted'),pl.col('actual_pa').sum().alias('actual')).sort('origin_year')
    mse=mean(q,'_sq')
    return {'mse':mse,'rmse':mse**.5,'mae':mean(q,'_abs'),'bias':mean(q,'_bias'),
        'mean_predicted':mean(q,column),'mean_actual':mean(q,'actual_pa'),
        'aggregate_absolute_error':float((totals['predicted']-totals['actual']).abs().mean()),'totals':totals.to_dicts()}


def summary(f):
    if not f.height:return None
    return {'rows':f.height,'active':int((f['actual_pa']>0).sum()),'origins':sorted(f['origin_year'].unique()),
        'arms':{a:errors(f,a+'_pa') for a in ARMS}}


def conditional(f):
    f=f.filter(pl.col('actual_pa')>0)
    if not f.height:return None
    return {'rows':f.height,'arms':{a:errors(f,a+'_conditional') for a in ('I','A','D','M')}}


def cumulative(f):
    return f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        *[pl.col(c).first() for c in ('player_name','age','stage','prospect','minor_returner','mlb_pa_lag0')],
        pl.col('actual_pa').sum(),*[pl.col(a+'_pa').sum() for a in ARMS],
        *[pl.col(a+'_universal_pa').sum() for a in ('A','D','M')]).filter((pl.col('_n')==3)&(pl.col('_nh')==3)).sort('origin_year','player_id')


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert fit['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    f=pl.read_parquet(OUT/'predictions.parquet');c=cumulative(f);c.write_parquet(OUT/'cumulative-predictions.parquet')
    report={'annual':{},'cumulative':{},'conditional':{},'universal_diagnostic':{},'role_diagnostics':{},
            'protected_outcomes_used':False,'production_forecasts_changed':False}
    for h in (1,2,3):
        print(f'Scoring H{h}',flush=True);q=f.filter(pl.col('horizon')==h);p=q.filter(pl.col('prospect'))
        report['annual'][str(h)]={'groups':{n:summary(q.filter(e)) for n,e in GROUPS.items()},
            'by_origin_prospects':{str(y):summary(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
            'paired':{a:{b:paired_interval(p,a+'_pa',b+'_pa') for b in ('I','E')} for a in ('D','M')}}
        report['conditional'][str(h)]={n:conditional(q.filter(e)) for n,e in GROUPS.items()}
        report['universal_diagnostic'][str(h)]={n:{a:errors(q.filter(e),a+'_universal_pa') for a in ('A','D','M')}
                                              for n,e in GROUPS.items() if q.filter(e).height}
        active=p.filter(pl.col('actual_pa')>0);r=roles(active['actual_pa'])
        pp=np.clip(active.select('role_0','role_1','role_2').to_numpy(),1e-9,1)
        loss=-np.log(pp[np.arange(len(r)),r])
        z=active.with_columns(pl.Series('_role_loss',loss))
        report['role_diagnostics'][str(h)]={'conditional_log_loss':mean(z,'_role_loss'),
            'annual_regular_counts':p.group_by('origin_year').agg((pl.col('actual_pa')>=450).sum().alias('actual_regular'),
                pl.col('M_regular_probability').sum().alias('expected_regular')).sort('origin_year').to_dicts()}
    print('Scoring three-year workload',flush=True)
    cp=c.filter(pl.col('prospect'))
    report['cumulative']={'groups':{n:summary(c.filter(e)) for n,e in GROUPS.items()},
        'paired':{a:{b:paired_interval(cp,a+'_pa',b+'_pa') for b in ('I','E','A')} for a in ('D','M')},
        'by_origin_prospects':{str(y):summary(g) for (y,),g in cp.partition_by('origin_year',as_dict=True).items()}}
    decisions={}
    for a in ('D','M'):
        guards={}
        for h,s in report['annual'].items():
            for name in ('prospects','upper','lower','young_upper'):
                g=s['groups'][name]
                if g and g['rows']>=200 and g['active']>=10:guards[h+'/'+name]=g['arms'][a]['mse']<=1.05*g['arms']['I']['mse']
            for year,g in s['by_origin_prospects'].items():
                if g['rows']>=200 and g['active']>=10:guards[h+'/'+year]=g['arms'][a]['mse']<=1.05*g['arms']['I']['mse']
        stats=report['cumulative']['groups']['prospects']['arms'];pair=report['cumulative']['paired'][a]
        gates={'cumulative_intervals':all(pair[b]['interval975'][1]<0 for b in ('I','E')),
            'majority_origins':all(pair[b]['improving_origins']>=2 for b in ('I','E')),
            'ensemble_each_horizon':all(s['groups']['prospects']['arms'][a]['mse']<s['groups']['prospects']['arms']['E']['mse'] for s in report['annual'].values()),
            'cumulative_mae':stats[a]['mae']<=stats['I']['mae'],
            'aggregate_pa_error':stats[a]['aggregate_absolute_error']<=stats['I']['aggregate_absolute_error'],
            'harm_guards':all(guards.values())}
        decisions[a]={'passes':all(gates.values()),'gates':gates,'harm_guards':guards}
    report['decisions']=decisions;report['selected_research_head']=next((a for a in ('D','M') if decisions[a]['passes']),None)
    report['future_regular_diagnostic']={str(h):{a:errors(q,a+'_conditional') for a in ('I','A','D','M')}
        for h in (1,2,3) for q in [f.filter((pl.col('horizon')==h)&pl.col('prospect')&(pl.col('actual_pa')>=450))] if q.height}
    report['hashes']={n:sha256_file(OUT/n) for n in ('predictions.parquet','prefit-manifest.json','fit-manifest.json','references.parquet')}
    save(OUT/'score-report.json',report)
    print(json.dumps({'decisions':decisions,'selected':report['selected_research_head'],
        'annual_prospect_rmse':{h:{a:g['groups']['prospects']['arms'][a]['rmse'] for a in ARMS} for h,g in report['annual'].items()},
        'cumulative_prospect_rmse':{a:report['cumulative']['groups']['prospects']['arms'][a]['rmse'] for a in ARMS}},indent=2))


if __name__=='__main__':main()
