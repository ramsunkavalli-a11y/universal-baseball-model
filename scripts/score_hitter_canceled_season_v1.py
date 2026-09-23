"""Evaluate canceled-block routing and predeclared missing-input stress tests."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from fit_hitter_canceled_season_v1 import OUT,SOURCE,HISTORY
from fit_hitter_arrival_coherence_v1 import save
from score_hitter_detail_arrival_v1 import metrics,paired
from score_hitter_history_calibration_v1 import ranks,matched,SLICES
from universal_baseball.storage import sha256_file


def summarize(f):
    return {a:metrics(g) for (a,),g in f.partition_by('arm',as_dict=True).items()}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    for n,h in fit['files'].items():assert sha256_file(OUT/n)==h
    f=pl.read_parquet(OUT/'predictions.parquet')
    p=pl.read_parquet(SOURCE/'input-panel.parquet').select('origin_year','player_id','pa_lag0',
        *['path0__level_path__'+s for s in ('primary_level_change','prior_seasons_at_primary','substantial_same_level_repeat','returned_after_partial_promotion')])
    f=f.join(p,on=['origin_year','player_id'],how='left',validate='m:1')
    stress=pl.read_parquet(OUT/'outage-stress.parquet').filter(pl.col('prospect'))
    stress_report=[]
    for (year,lag),g in stress.partition_by('origin_year','hidden_lag',as_dict=True).items():
        stress_report.append({'year':year,'hidden_lag':lag,'metrics':summarize(g),
            'recovery_minus_masked':paired(g.filter(pl.col('arm')=='available_O'),g.filter(pl.col('arm')=='masked_R'))})
    recovery_wins=sum(all(r['metrics']['available_O'][s]<r['metrics']['masked_R'][s] for s in ('brier','log_loss')) for r in stress_report)
    old=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold') & ~pl.col('pandemic'))
    history=pl.read_parquet(HISTORY).filter(~pl.col('pandemic') & (pl.col('arm')=='H'))
    refs=pl.read_parquet(SOURCE/'reference-predictions.parquet')
    report={'targets':{},'outage_stress':stress_report,'recovery_wins':recovery_wins,
            'protected_outcomes_used':False,'production_forecasts_changed':False}
    for (target,),g in f.filter(pl.col('prospect')).partition_by('target',as_dict=True).items():
        print('Scoring '+target,flush=True)
        comparisons={}; annual={}
        for year in (2021,2022):
            q=g.filter(pl.col('origin_year')==year)
            annual[str(year)]=summarize(q)
            comparisons[str(year)]=paired(q.filter(pl.col('arm')=='O'),q.filter(pl.col('arm')=='R'))
        candidate=g.filter(pl.col('arm')=='O')
        controls={}
        references=[('history_H',history.filter(pl.col('target')==target))]
        for engine in ('lightgbm','logistic'):
            references.append((engine+'_B2',old.filter((pl.col('target')==target)&(pl.col('engine')==engine)&(pl.col('arm')=='B2'))))
        references += [(name,r) for (name,),r in refs.filter(pl.col('target')==target).partition_by('model',as_dict=True).items()]
        for name,r in references: controls[name]=matched(candidate,r)
        slices={}
        for year in (2021,2022):
            slices[str(year)]={name:summarize(g.filter((pl.col('origin_year')==year)&expr)) for name,expr in SLICES.items()}
        a,b=annual['2021']['O'],annual['2021']['R']
        improvement=1-abs(a['expected']-a['observed'])/abs(b['expected']-b['observed'])
        guard_groups=[annual['2022']]+[slices[str(y)][stage] for y in (2021,2022) for stage in ('upper','lower')]
        gates={'2021_both_intervals':all(comparisons['2021'][s]['interval95'][1]<0 for s in ('brier','log_loss')),
               '2021_count_error_reduction_25pct':improvement>=.25,
               '2022_and_stage_guard':all(v['O'][s]<=1.1*v['R'][s] for v in guard_groups
                   if v['O']['rows']>=200 and v['O']['observed']>=30 for s in ('brier','log_loss')),
               'historical_recovery':recovery_wins>=3,
               'three_year_confirmation':target=='next_year'}
        status='mechanism_supported_targeted_development_repair' if all(gates.values()) else 'partial_or_unsupported_repair_no_promotion'
        report['targets'][target]={'status':status,'gates':gates,'2021_count_error_reduction':improvement,
            'all_origins':summarize(g),'annual':annual,'O_minus_R':comparisons,
            'pooled_O_minus_R':paired(candidate,g.filter(pl.col('arm')=='R')),
            'slices':slices,'controls':controls,
            'ranking':{str(y):{arm:ranks(g.filter((pl.col('origin_year')==y)&(pl.col('arm')==arm))) for arm in ('R','O','N')} for y in (2021,2022)}}
    report['hashes']={n:sha256_file(OUT/n) for n in ('prefit-manifest.json','fit-manifest.json','predictions.parquet','outage-stress.parquet')}
    report['score_code_sha256']=sha256_file(Path(__file__))
    save(OUT/'score-report.json',report)
    print(json.dumps({'stress_wins':recovery_wins,'targets':{t:{'status':r['status'],'gates':r['gates'],
        'annual':{y:{a:{k:v[k] for k in ('observed','expected','brier','log_loss')} for a,v in m.items()} for y,m in r['annual'].items()}}
        for t,r in report['targets'].items()}},indent=2))


if __name__=='__main__':main()
