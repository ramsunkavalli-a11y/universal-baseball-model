"""Score a single predeclared hybrid against mandatory strong comparators."""
import json

import numpy as np
import polars as pl

from build_hitter_integrated_opportunity_value_v1 import OUT, hashes
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_integrated_opportunity_value import ARMS, cumulative, profiles
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

TARGETS=('pa','value','expanded')


def eligible(f,target):
    return f.filter(pl.col('complete_components') & pl.col('actual_expanded').is_finite()) if target=='expanded' else f


def metrics(f,target):
    f=eligible(f,target)
    if not f.height:return None
    rows=[]
    for (year,),g in f.partition_by('origin_year',as_dict=True).items():
        actual=g['actual_'+target].to_numpy()
        arms={}
        for a in ARMS:
            pred=g[a+'_'+target].to_numpy();err=pred-actual
            arms[a]={'mse':float(np.mean(err**2)),'mae':float(np.mean(abs(err))),
                'bias':float(err.mean()),'predicted_total':float(pred.sum()),
                'aggregate_absolute_error':float(abs(err.sum()))}
        rows.append({'origin':year,'rows':g.height,'actual_total':float(actual.sum()),'arms':arms})
    pooled={a:{k:float(np.mean([r['arms'][a][k] for r in rows]))
               for k in ('mse','mae','bias','aggregate_absolute_error')} for a in ARMS}
    for m in pooled.values():m['rmse']=m['mse']**.5
    return {'rows':f.height,'players':f['player_id'].n_unique(),'origins':len(rows),
            'active':int((f['actual_pa']>0).sum()),'arms':pooled,'by_origin':sorted(rows,key=lambda r:r['origin'])}


def probability(f):
    result={}
    for a in ('B','D','E','H'):
        values=[]
        for g in f.partition_by('origin_year'):
            p=np.clip(g[a+'_p'].to_numpy(),1e-6,1-1e-6);y=(g['actual_pa'].to_numpy()>0).astype(float)
            values.append({'brier':float(np.mean((p-y)**2)),
                'log_loss':float(np.mean(-y*np.log(p)-(1-y)*np.log1p(-p))),
                'expected_participants':float(p.sum()),'actual_participants':int(y.sum())})
        result[a]={k:float(np.mean([r[k] for r in values])) for k in values[0]}
    return result


def summarize(f,annual):
    if not f.height:return None
    return {**{t:metrics(f,t) for t in TARGETS}, **({'probability':probability(f)} if annual else {})}


def paired(f,target,ref):
    f=eligible(f,target)
    f=f.with_columns(((pl.col('H_'+target)-pl.col('actual_'+target))**2).alias('_h'),
                     ((pl.col(ref+'_'+target)-pl.col('actual_'+target))**2).alias('_ref'))
    return compare_losses(f,'_h','_ref',draws=2000)


def decisions(report):
    cp=report['paired_cumulative'];cs=report['cumulative']['all'];guard_pa={};guard_v={}
    for h,groups in report['annual'].items():
        for name,s in groups.items():
            if s is None:continue
            for t in TARGETS:
                m=s[t]
                if m is None or m['rows']<200 or m['active']<10:continue
                for ref in (('D','E') if t=='pa' else ('D','N')):
                    ok=m['arms']['H']['mse']<=1.05*m['arms'][ref]['mse']
                    (guard_pa if t=='pa' else guard_v)[f'{h}/{name}/{t}/{ref}']=ok
    p={'cumulative_intervals':all(cp['pa'][r]['interval95'][1]<0 for r in ('D','E')),
       'cumulative_majority':all(cp['pa'][r]['improving_origins']>=2 for r in ('D','E')),
       'mae_and_totals':all(cs['pa']['arms']['H'][k]<=cs['pa']['arms'][r][k]
           for r in ('D','E') for k in ('mae','aggregate_absolute_error')),
       'annual_strong_reference':all(g['all']['pa']['arms']['H']['mse']<=g['all']['pa']['arms']['E']['mse']
           for g in report['annual'].values()),'profile_guards':all(guard_pa.values()),
       'probability_guards':all(g['all']['probability']['H'][k]<=1.05*g['all']['probability'][r][k]
           for g in report['annual'].values() for r in ('D','E') for k in ('brier','log_loss'))}
    v={'opportunity_passes':all(p.values()),
       'cumulative_intervals':all(cp[t][r]['interval95'][1]<0 for t in ('value','expanded') for r in ('B','D','N')),
       'cumulative_majority':all(cp[t][r]['improving_origins']>cs[t]['origins']/2
           for t in ('value','expanded') for r in ('B','D','N')),
       'original_expanded_better':cs['expanded']['arms']['H']['mse']<cs['expanded']['arms']['L']['mse'],
       'mae_and_totals':all(cs[t]['arms']['H'][k]<=cs[t]['arms'][r][k]
           for t in ('value','expanded') for r in ('D','N') for k in ('mae','aggregate_absolute_error')),
       'profile_guards':all(guard_v.values())}
    return {'opportunity':p,'value':v,'opportunity_passes':all(p.values()),'value_passes':all(v.values()),
        'pa_profile_guards':guard_pa,'value_profile_guards':guard_v}


def main():
    pre=json.loads((OUT/'prefit-manifest.json').read_text());assert pre['hashes']==hashes()
    build=json.loads((OUT/'build-manifest.json').read_text())
    for n,h in build['files'].items():assert sha256_file(OUT/n)==h
    f=pl.read_parquet(OUT/'predictions.parquet');c=cumulative(f)
    report={'annual':{},'cumulative':{},'paired_cumulative':{},'periods':{},
            'protected_outcomes_used':False,'production_forecasts_changed':False,'new_fits':0}
    for h in (1,2,3):
        print(f'Scoring Year {h}',flush=True)
        q=f.filter(pl.col('horizon')==h)
        report['annual'][str(h)]={n:summarize(q.filter(e),True) for n,e in profiles().items()}
    report['cumulative']={n:summarize(c.filter(e),False) for n,e in profiles().items()}
    for t in TARGETS:
        print(f'Paired whole-player intervals: {t}',flush=True)
        refs=('D','E') if t=='pa' else ('B','D','N')
        report['paired_cumulative'][t]={r:paired(c,t,r) for r in refs}
    # Exposed pandemic-origin diagnostic remains separate, never a new routing rule.
    for label,expr in [('origin2021',pl.col('origin_year')==2021),('other_origins',pl.col('origin_year')!=2021)]:
        report['periods'][label]={'annual':{str(h):summarize(f.filter(expr&(pl.col('horizon')==h)),True) for h in (1,2,3)},
                                  'cumulative':summarize(c.filter(expr),False)}
    report['decisions']=decisions(report)
    comp=pl.read_parquet(OUT/'component-predictions.parquet')
    direct=comp.filter(pl.col('selected_model')=='direct')
    report['direct_total_audit']={'component_rows':direct.height,
        'below_one_expected_PA_rows':direct.filter(pl.col('H_pa')<1).height,
        'max_abs_direct_runs_below_one_PA':float(direct.filter(pl.col('H_pa')<1)['direct'].abs().max() or 0),
        'by_component':direct.group_by('component').agg(pl.len().alias('rows'),
             (pl.col('H_pa')<1).sum().alias('below_one_PA'),pl.col('direct').abs().max().alias('max_abs_runs')).to_dicts()}
    # No conditional E workload is inferred. Check the compatibility envelope only.
    report['opportunity_coherence']={a:{'PA_exceeds_750_times_probability':f.filter(pl.col(a+'_pa')>750*pl.col(a+'_p')+1e-8).height}
        for a in ('D','E','H')}
    cols=['origin_year','player_id','player_name','horizon','stage','age','route','actual_pa','actual_value',
          *[a+'_'+t for a in ('D','N','H') for t in ('pa','value','expanded')]]
    examples=f.with_columns((pl.col('H_pa')-pl.col('D_pa')).alias('pa_change'),
        (pl.col('H_expanded')-pl.col('D_expanded')).alias('value_change'))
    report['largest_changes']={k:examples.sort(k,descending=True).select(*cols,k).head(15).to_dicts()
        for k in ('pa_change','value_change')}
    save(OUT/'score-report.json',report);c.write_parquet(OUT/'cumulative-predictions.parquet')
    print(json.dumps({'decisions':{k:v for k,v in report['decisions'].items() if 'profile_guards' not in k},
        'cumulative_rmse':{t:{a:cs['arms'][a]['rmse'] for a in ARMS} for t,cs in report['cumulative']['all'].items()}},indent=2))


if __name__=='__main__':main()
