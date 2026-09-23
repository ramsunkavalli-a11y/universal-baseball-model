"""Evaluate the predeclared era/schedule diagnostics without selecting a route."""
import json
import polars as pl
from audit_hitter_schedule_opportunity_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from score_hitter_detail_arrival_v1 import metrics,paired,GROUPS
from universal_baseball.storage import sha256_file


def summarize(f):
    return {a:metrics(g) for (a,),g in f.partition_by('arm',as_dict=True).items()}


def comparison(f,candidate,reference):
    a=f.filter(pl.col('arm')==candidate);b=f.filter(pl.col('arm')==reference)
    years=sorted(set(a['origin_year'])&set(b['origin_year']))
    a=a.filter(pl.col('origin_year').is_in(years));b=b.filter(pl.col('origin_year').is_in(years))
    return {'candidate':metrics(a),'reference':metrics(b),'paired':paired(a,b)}


def guards(f,candidate,reference):
    years=sorted(set(f.filter(pl.col('arm')==candidate)['origin_year'])&set(f.filter(pl.col('arm')==reference)['origin_year']))
    f=f.filter(pl.col('origin_year').is_in(years));checks={}
    for label,expr in [(str(y),pl.col('origin_year')==y) for y in years]+[
            (stage,pl.col('stage')==stage) for stage in ('Upper minors','Lower minors')]:
        m=summarize(f.filter(expr));a=m[candidate];b=m[reference]
        if a['rows']>=200 and a['observed']>=30:
            checks[label]=all(a[s]<=1.1*b[s] for s in ('brier','log_loss'))
    return checks


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text());assert fit['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    f=pl.read_parquet(OUT/'predictions.parquet');p=f.filter(pl.col('prospect'))
    report={'annual':{str(y):summarize(g) for (y,),g in p.partition_by('origin_year',as_dict=True).items()},
            'prospects':summarize(p),'comparisons':{},'groups':{n:summarize(f.filter(e)) for n,e in GROUPS.items()},
            'protected_outcomes_used':False,'production_forecasts_changed':False}
    for candidate,reference in [('E','R'),('AE','A'),('AE','R'),('S1','S0'),('S1','R')]:
        print(f'Score {candidate}/{reference}',flush=True)
        report['comparisons'][candidate+'/'+reference]=comparison(p,candidate,reference)
    y=report['annual']['2022'];ae,a=y['AE'],y['A']
    report['era_hypothesis_support']=all(ae[s]<a[s] for s in ('brier','log_loss')) and abs(ae['expected']-ae['observed'])<abs(a['expected']-a['observed'])
    sc=report['comparisons']['S1/S0']; practical=report['comparisons']['S1/R']
    sg=guards(p,'S1','S0');rg=guards(p,'S1','R')
    gates={'pooled_intervals':all(sc['paired'][s]['interval95'][1]<0 for s in ('brier','log_loss')),
           'majority_origins':all(sc['paired'][s]['improving_origins']>=3 for s in ('brier','log_loss')),
           'schedule_harm_guards':all(sg.values())}
    report['schedule_evidence']={'gates':gates,'harm_guards':sg,'supported':all(gates.values()),
        'broader_candidate':all(gates.values()) and all(rg.values()) and all(practical['candidate'][s]<practical['reference'][s] for s in ('brier','log_loss')),
        'R_harm_guards':rg}
    report['hashes']={n:sha256_file(OUT/n) for n in ('predictions.parquet','fit-manifest.json','prefit-manifest.json','schedule-audit.json')}
    save(OUT/'score-report.json',report)
    print(json.dumps({'annual':{y:{a:{k:m[k] for k in ('expected','observed','brier','log_loss')} for a,m in g.items()}
                              for y,g in report['annual'].items()},'era_hypothesis_support':report['era_hypothesis_support'],
                      'schedule_evidence':report['schedule_evidence']},indent=2))


if __name__=='__main__':main()
