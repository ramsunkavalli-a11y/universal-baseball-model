"""Score the single structural-outage augmentation without retuning."""
import json
from pathlib import Path
import polars as pl
from fit_hitter_structural_missingness_v1 import OUT,SOURCE
from fit_hitter_arrival_coherence_v1 import save
from score_hitter_detail_arrival_v1 import metrics,paired,GROUPS
from score_hitter_history_calibration_v1 import matched,ranks,SLICES
from universal_baseball.storage import sha256_file


def summarize(f):
    return {a:metrics(g) for (a,),g in f.partition_by('arm',as_dict=True).items()}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert fit['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    f=pl.read_parquet(OUT/'predictions.parquet')
    panel=pl.read_parquet(SOURCE/'input-panel.parquet').select('origin_year','player_id','pa_lag0',
        *['path0__level_path__'+s for s in ('primary_level_change','prior_seasons_at_primary','substantial_same_level_repeat','returned_after_partial_promotion')])
    f=f.join(panel,on=['origin_year','player_id'],how='left',validate='m:1')
    old=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic'))
    refs=pl.read_parquet(SOURCE/'reference-predictions.parquet')
    report={'targets':{},'protected_outcomes_used':False,'production_forecasts_changed':False}
    for (target,),allrows in f.partition_by('target',as_dict=True).items():
        print('Scoring '+target,flush=True)
        g=allrows.filter(pl.col('prospect'));m=summarize(g)
        comp={arm:paired(g.filter(pl.col('arm')=='A'),g.filter(pl.col('arm')==arm)) for arm in ('R','T')}
        focus=g.filter(pl.col('origin_year')==2021);c2021=paired(focus.filter(pl.col('arm')=='A'),focus.filter(pl.col('arm')=='R'))
        annual={str(year):summarize(q) for (year,),q in g.partition_by('origin_year',as_dict=True).items()}
        slices={str(y):{name:summarize(g.filter((pl.col('origin_year')==y)&expr)) for name,expr in SLICES.items()} for y in (2021,2022)}
        a,b=annual['2021']['A'],annual['2021']['R'];reduction=1-abs(a['expected']-a['observed'])/abs(b['expected']-b['observed'])
        controls={}
        for engine in ('lightgbm','logistic'):
            r=old.filter((pl.col('target')==target)&(pl.col('arm')=='B2')&(pl.col('engine')==engine))
            controls[engine+'_B2']=matched(g.filter(pl.col('arm')=='A'),r)
        for (name,),r in refs.filter(pl.col('target')==target).partition_by('model',as_dict=True).items():
            controls[name]=matched(g.filter(pl.col('arm')=='A'),r)
        guard=[v for y,v in annual.items() if y!='2021']
        guard += [summarize(g.filter(pl.col('stage')==stage)) for stage in ('Upper minors','Lower minors')]
        gates={'2021_intervals':all(c2021[s]['interval95'][1]<0 for s in ('brier','log_loss')),
               '2021_count_error_reduction_25pct':reduction>=.25,
               'pooled_R_T_intervals':all(comp[ref][s]['interval95'][1]<0 for ref in ('R','T') for s in ('brier','log_loss')),
               'other_origins_stage_guards':all(v['A'][s]<=1.1*v['R'][s] for v in guard
                   if v['A']['rows']>=200 and v['A']['observed']>=30 for s in ('brier','log_loss')),
               'stronger_ensemble_points':all(controls['earlier_ensemble']['candidate'][s]<controls['earlier_ensemble']['reference'][s]
                   for s in ('brier','log_loss')) if 'earlier_ensemble' in controls else None,
               'sufficient_origins':m['A']['origins']>=3}
        status='targeted_annual_development_candidate' if all(gates.values()) else 'not_confirmed_no_upgrade'
        report['targets'][target]={'status':status,'gates':gates,'prospects':m,'annual':annual,'comparisons':comp,
            '2021_comparison':c2021,'2021_count_error_reduction':reduction,'slices':slices,'controls':controls,
            'ranking':{a:ranks(g.filter(pl.col('arm')==a)) for a in ('R','T','A')},
            'other_cohorts':{name:summarize(allrows.filter(expr)) for name,expr in GROUPS.items() if name!='prospects'}}
    report['hashes']={n:sha256_file(OUT/n) for n in ('prefit-manifest.json','fit-manifest.json','predictions.parquet')}
    report['score_code_sha256']=sha256_file(Path(__file__))
    save(OUT/'score-report.json',report)
    print(json.dumps({t:{'status':r['status'],'gates':r['gates'],'annual':{y:{a:{k:v[k] for k in ('observed','expected','brier','log_loss')}
             for a,v in m.items()} for y,m in r['annual'].items()}} for t,r in report['targets'].items()},indent=2))


if __name__=='__main__':main()
