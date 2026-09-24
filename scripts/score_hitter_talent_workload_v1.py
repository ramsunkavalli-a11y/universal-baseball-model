"""Fixed workload acceptance and diagnostics; no after-the-fact model rescue."""
import json
import numpy as np
import polars as pl
from fit_hitter_talent_workload_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from score_hitter_conditional_workload_v1 import GROUPS,errors
from universal_baseball.hitter_conditional_workload import paired_interval
from universal_baseball.storage import sha256_file

ARMS=('D','E','I','T','P','TP')


def summary(f):
    if not f.height:return None
    return {'rows':f.height,'active':int((f['actual_pa']>0).sum()),
            'arms':{a:errors(f,a+'_pa') for a in ARMS}}


def cumulative(f):
    return f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        *[pl.col(c).first() for c in ('player_name','age','stage','prospect','minor_returner','mlb_pa_lag0','pedigree_matched')],
        pl.col('actual_pa').sum(),*[pl.col(a+'_pa').sum() for a in ARMS])\
        .filter((pl.col('_n')==3)&(pl.col('_nh')==3)).sort('origin_year','player_id')


def decision(report):
    stats=report['cumulative']['groups']['prospects']['arms'];pair=report['cumulative']['paired']['TP']
    guards={}
    for h,s in report['annual'].items():
        for name,g in {**{n:s['groups'][n] for n in ('prospects','upper','lower','young_upper')},**s['by_origin_prospects']}.items():
            if g and g['rows']>=200 and g['active']>=10:
                guards[h+'/'+name]=g['arms']['TP']['mse']<=1.05*g['arms']['D']['mse']
    zero=report['cumulative']['no_mlb_pa']['arms']
    gates={'cumulative_intervals':all(pair[b]['interval975'][1]<0 for b in ('D','E')),
        'majority_origins':all(pair[b]['improving_origins']>=2 for b in ('D','E')),
        'each_horizon':all(s['groups']['prospects']['arms']['TP']['mse']<s['groups']['prospects']['arms'][b]['mse']
            for s in report['annual'].values() for b in ('D','E')),
        'cumulative_mae':stats['TP']['mae']<=stats['D']['mae'],
        'aggregate_pa_error':stats['TP']['aggregate_absolute_error']<=stats['D']['aggregate_absolute_error'],
        'no_mlb_optimism':zero['TP']['mean_predicted']<=1.05*zero['D']['mean_predicted'],
        'harm_guards':all(guards.values()),'nonprospects_unchanged':report['nonprospects_unchanged']}
    return {'passes':all(gates.values()),'gates':gates,'harm_guards':guards}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert sha256_file(OUT/'predictions.parquet')==fit['prediction_sha256']
    f=pl.read_parquet(OUT/'predictions.parquet');c=cumulative(f);c.write_parquet(OUT/'cumulative-predictions.parquet')
    report={'annual':{},'conditional':{},'future_regular':{},'talent_quintiles':{},
            'protected_outcomes_used':False,'production_forecasts_changed':False}
    groups={**GROUPS,'draft_matched':pl.col('prospect')&(pl.col('pedigree_matched')==1),
        'draft_unmatched':pl.col('prospect')&(pl.col('pedigree_matched')==0)}
    for h in (1,2,3):
        print(f'Scoring H{h}',flush=True);q=f.filter(pl.col('horizon')==h);p=q.filter(pl.col('prospect'))
        report['annual'][str(h)]={'groups':{n:summary(q.filter(e)) for n,e in groups.items()},
            'by_origin_prospects':{str(y):summary(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
            'paired':{b:paired_interval(p,'TP_pa',b+'_pa') for b in ('D','E')}}
        active=p.filter(pl.col('actual_pa')>0);regular=p.filter(pl.col('actual_pa')>=450)
        report['conditional'][str(h)]={a:errors(active,a+'_conditional') for a in ('I','D','T','P','TP')}
        report['future_regular'][str(h)]={'rows':regular.height,
            'conditional':{a:errors(regular,a+'_conditional') for a in ('I','D','T','P','TP')},
            'unconditional':summary(regular)}
        talent=p.filter(pl.col('talent_rate_h1').is_finite()).with_columns(
            (((pl.col('talent_rate_h1').rank('ordinal').over('origin_year')-1)*5/pl.len().over('origin_year')).floor()+1).cast(pl.Int8).alias('_quintile'))
        report['talent_quintiles'][str(h)]={str(k):summary(g) for (k,),g in talent.partition_by('_quintile',as_dict=True).items()}
    p=c.filter(pl.col('prospect'))
    report['cumulative']={'groups':{n:summary(c.filter(e)) for n,e in groups.items()},
        'paired':{a:{b:paired_interval(p,a+'_pa',b+'_pa') for b in ('D','E') if a!=b} for a in ('T','P','TP')},
        'by_origin_prospects':{str(y):summary(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
        'no_mlb_pa':summary(p.filter(pl.col('actual_pa')==0))}
    report['nonprospects_unchanged']=all(np.array_equal(f.filter(~pl.col('prospect'))[a+'_pa'],
        f.filter(~pl.col('prospect'))['B_pa']) for a in ('T','P','TP'))
    report['decision']=decision(report)
    report['hashes']={n:sha256_file(OUT/n) for n in ('prefit-manifest.json','fit-manifest.json','predictions.parquet','nested-talent.parquet')}
    save(OUT/'score-report.json',report)
    print(json.dumps({'decision':report['decision'],
        'annual_rmse':{h:{a:g['groups']['prospects']['arms'][a]['rmse'] for a in ARMS} for h,g in report['annual'].items()},
        'cumulative_rmse':{a:report['cumulative']['groups']['prospects']['arms'][a]['rmse'] for a in ARMS}},indent=2))


if __name__=='__main__':main()
