"""Matched repaired-cohort scores and fixed gates, not a new model selection."""
import json
from pathlib import Path
import polars as pl
from fit_hitter_arrival_coherence_v1 import save
from fit_hitter_arrival_source_repair_v1 import OUT,SOURCE,corrected_scoring
from score_hitter_detail_arrival_v1 import metrics,paired,GROUPS
from universal_baseball.storage import sha256_file


def summary(f):
    return {a:metrics(g) for (a,),g in f.partition_by('arm',as_dict=True).items()}


def compare(a,b):
    return {'candidate':metrics(a),'reference':metrics(b),'paired':paired(a,b)}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert sha256_file(OUT/'predictions.parquet')==fit['prediction_sha256']
    f=pl.read_parquet(OUT/'predictions.parquet');panel=pl.read_parquet(OUT/'repaired-panel.parquet')
    f=f.join(panel.select('origin_year','player_id','player_name','minor_returner','level','pa_lag0',
           'league_mexican_pa_share_lag0','league_known_pa_share_lag0','on_40man'),
           on=['origin_year','player_id'],how='left',validate='m:1')
    groups={**GROUPS,'returners':pl.col('minor_returner'),'mexican_exposure':pl.col('league_mexican_pa_share_lag0')>0,
        'prospects_known_no_mexican':pl.col('prospect')&(pl.col('league_mexican_pa_share_lag0')==0)&(pl.col('league_known_pa_share_lag0')==1),
        'prospects_under200pa':pl.col('prospect')&(pl.col('pa_lag0')<200),
        'prospects_200pluspa':pl.col('prospect')&(pl.col('pa_lag0')>=200),
        'prospects_age23orless':pl.col('prospect')&(pl.col('age')<=23),
        'prospects_age24plus':pl.col('prospect')&(pl.col('age')>23)}
    report={'targets':{},'primary':'F','protected_outcomes_used':False,'production_forecasts_changed':False}
    references=pl.read_parquet(SOURCE/'reference-predictions.parquet')
    for target in ('next_year','arrival_three','regular_three'):
        print('Scoring '+target,flush=True)
        t=f.filter(pl.col('target')==target);p=t.filter(pl.col('prospect'))
        s={'prospects':summary(p),'annual':{str(y):summary(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
           'groups':{name:summary(t.filter(expr)) for name,expr in groups.items()},'comparisons':{},'references':{}}
        for a,b in [('C','R'),('T','R'),('F','R'),('F','T'),('F','C')]:
            s['comparisons'][a+'/'+b]=compare(p.filter(pl.col('arm')==a),p.filter(pl.col('arm')==b))
        candidate=p.filter(pl.col('arm')=='F')
        for (name,),r in references.filter(pl.col('target')==target).partition_by('model',as_dict=True).items():
            j=candidate.join(r.select('origin_year','player_id',pl.col('probability').alias('ref_p')),
                on=['origin_year','player_id'],how='inner',validate='1:1')
            if j.height:s['references'][name]=compare(j,j.with_columns(pl.col('ref_p').alias('probability')))
        detail=pl.read_parquet(SOURCE/'predictions.parquet').filter(~pl.col('cold')&~pl.col('pandemic')&
               (pl.col('target')==target)&(pl.col('arm')=='B2'))
        for (engine,),r in detail.partition_by('engine',as_dict=True).items():
            j=candidate.join(r.select('origin_year','player_id',pl.col('probability').alias('ref_p')),
                on=['origin_year','player_id'],how='inner',validate='1:1')
            if j.height:s['references']['B2_'+engine]=compare(j,j.with_columns(pl.col('ref_p').alias('probability')))
        if target=='next_year':
            r=pl.read_parquet('model_artifacts/hitter-era-schedule-v1-2026-09-23/predictions.parquet').filter(pl.col('arm')=='AE')
            j=candidate.join(r.select('origin_year','player_id',pl.col('probability').alias('ref_p')),
                on=['origin_year','player_id'],how='inner',validate='1:1')
            s['references']['AE']=compare(j,j.with_columns(pl.col('ref_p').alias('probability')))
            guards={}
            for label,g in list(s['annual'].items())+[(k,s['groups'][k]) for k in ('upper_prospects','lower_prospects')]:
                if g['R']['rows']>=200 and g['R']['observed']>=30:
                    guards[label]=all(g['F'][k]<=1.1*g['R'][k] for k in ('brier','log_loss'))
            scores=s['comparisons']['F/R']['paired']
            gates={'both_intervals_below_zero':all(scores[k]['interval95'][1]<0 for k in ('brier','log_loss')),
                'four_of_six_origins':all(scores[k]['improving_origins']>=4 for k in ('brier','log_loss')),
                'harm_guards':all(guards.values()),
                'strong_references':all(s['references'][n]['candidate'][k]<s['references'][n]['reference'][k]
                    for n in ('earlier_ensemble','accepted_C2') for k in ('brier','log_loss'))}
            s['gates']=gates;s['harm_guards']=guards;s['promising_next_year_candidate']=all(gates.values())
        report['targets'][target]=s
    cases=f.filter((pl.col('target')=='next_year')&pl.col('player_id').is_in(
        [665161,677649,682928,671739,691718,701538,669461,660650,121252,425854]))
    report['illustrative_cases']=cases.select('origin_year','player_id','player_name','level','arm','probability','actual','prospect','on_40man').to_dicts()
    report['hashes']={n:sha256_file(OUT/n) for n in ('prefit-manifest.json','fit-manifest.json','predictions.parquet','source-audit.json')}
    save(OUT/'score-report.json',report)
    print(json.dumps({t:{a:{k:m[k] for k in ('rows','observed','expected','brier','log_loss')} for a,m in s['prospects'].items()}
                      for t,s in report['targets'].items()},indent=2))
    print(json.dumps(report['targets']['next_year']['gates'],indent=2))


if __name__=='__main__':main()
