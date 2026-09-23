"""Common exact and finite-draw scores for the fixed population repair."""
import json
import numpy as np
import polars as pl
from audit_player_path_population_v1 import OUT
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.player_path_distribution import EVENTS
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

METHODS=('B0','F0','F1','A1')
LOSSES=['crps','mse','delivered_mse']+[p+e for p in ('brier_','log_') for e in EVENTS]
GROUPS={'Never-debuted minors':pl.col('prospect'),'Recent debut':pl.col('recent_debut'),
    'Current MLB':pl.col('stage')=='Current MLB','Upper minors':pl.col('stage')=='Upper minors',
    'Lower minors':pl.col('stage')=='Lower minors','Age under 23':pl.col('age')<23,
    'Age 23+':pl.col('age')>=23,'Young brief MLB':(pl.col('age')<=23)&pl.col('mlb_pa_lag0').is_between(1,99)}


def mean(f,col):
    return float(f.group_by('origin_year').agg(pl.col(col).mean())[col].mean())


def metric(f):
    if not f.height:return None
    out={'rows':f.height,'origins':f['origin_year'].n_unique(),**{c:mean(f,c) for c in LOSSES}}
    out['rmse']=float(np.sqrt(max(0,out['mse'])))
    out['delivered_rmse']=float(np.sqrt(out['delivered_mse']))
    for c in ('energy','coverage80','width80'):
        if c in f.columns:out[c]=mean(f,c)
    out['events']={e:{'observed':int(f['actual_'+e].sum()),'predicted':float(f['p_'+e].sum()),
        'ratio':float(f['p_'+e].sum()/f['actual_'+e].sum()) if f['actual_'+e].sum() else None} for e in EVENTS}
    return out


def methods(f):
    return {m:metric(f.filter(pl.col('method')==m)) for m in METHODS}


def assess(f,bootstrap=True):
    m=methods(f);a=m['A1']
    annual={str(y):methods(f.filter(pl.col('origin_year')==y)) for y in sorted(f['origin_year'].unique())}
    groups={name:methods(f.filter(mask)) for name,mask in GROUPS.items()}
    paired={}
    for ref in METHODS[:-1]:
        keys=['origin_year','player_id']
        j=f.filter(pl.col('method')=='A1').select(*keys,pl.col('crps').alias('candidate')).join(
            f.filter(pl.col('method')==ref).select(*keys,pl.col('crps').alias('baseline')),on=keys,validate='1:1')
        assert j.height==a['rows']
        paired[ref]=compare_losses(j,'candidate','baseline') if bootstrap else {'delta':mean(j.with_columns(
            (pl.col('candidate')-pl.col('baseline')).alias('delta')),'delta')}
    tail={}
    for label,g in {'All players':m,**{k:groups[k] for k in ('Never-debuted minors','Recent debut','Young brief MLB')}}.items():
        tail[label]={}
        for e in EVENTS[1:]:
            obs=g['A1']['events'][e]
            supported=obs['observed']>=30
            passed=supported and .75<=obs['ratio']<=1.25 and all(
                g['A1'][score+e]<=g[r][score+e] for r in ('F1','F0') for score in ('brier_','log_'))
            tail[label][e]={**obs,'supported':supported,'passed':passed}
    gates={'three_normal_origins':a['origins']>=3,
        'crps_improvement':all(p['interval95'][1]<0 if bootstrap else p['delta']<0 for p in paired.values()),
        'majority_origins':all(sum(v['A1']['crps']<v[r]['crps'] for v in annual.values())>len(annual)/2 for r in METHODS[:-1]),
        'mean_error':a['mse']<=1.05*a['delivered_mse'] and all(a['mse']<=1.05*m[r]['mse'] for r in METHODS[:-1]),
        'event_scores':all(a[s+e]<=1.05*m[r][s+e] for s in ('brier_','log_') for e in EVENTS for r in METHODS[:-1]),
        'starting_group_crps':all(g['A1']['crps']<=1.1*g[r]['crps'] for g in groups.values() if g['A1']
            and g['A1']['rows']>=200 and g['A1']['origins']>=3 for r in METHODS[:-1]),
        'supported_success_checks':all(v['passed'] for t in tail.values() for v in t.values() if v['supported']),
        'broad_success_support':all(v['supported'] for t in tail.values() for v in t.values())}
    return {'methods':m,'annual':annual,'groups':groups,'paired':paired,'tail':tail,'gates':gates}


def normal(f):
    return f.filter((pl.col('origin_year')<2025)&(pl.col('horizon')==3)&~pl.col('pandemic')&~pl.col('cold'))


def main():
    exact=pl.read_parquet(OUT/'exact-predictions.parquet')
    simulated=pl.read_parquet(OUT/'simulated-predictions.parquet')
    primary=assess(normal(exact))
    repeats={}
    for (n,s),f in normal(simulated).partition_by('draws','seed',as_dict=True).items():
        r=assess(f,False)
        repeats[f'{n}-{s}']={k:r[k] for k in ('methods','paired','gates')}
    changing=[g for g in primary['gates'] if len({r['gates'][g] for r in repeats.values()})>1]
    signs={ref:sorted(set(int(np.sign(r['paired'][ref]['delta'])) for r in repeats.values())) for ref in METHODS[:-1]}
    stable=not changing and all(len(s)==1 for s in signs.values())
    report={'status':'development_supported_not_promoted' if all(primary['gates'].values()) and stable else 'reject_population_repair_as_replacement',
        'primary':primary,'simulation':repeats,'numerical_stability':{'stable':stable,'changing_gates':changing,'delta_signs':signs},
        'nonoverlap':methods(normal(exact).filter(pl.col('origin_year').is_in([2016,2021]))),
        'cold':methods(exact.filter(pl.col('cold'))),
        'stress':{str(h):methods(exact.filter((pl.col('origin_year')<2025)&pl.col('pandemic')&(pl.col('horizon')==h))) for h in (3,6)},
        'production_forecasts_changed':False,'protected_outcomes_used':False,
        'target':'batting_plus_replacement_not_whole_war',
        'hashes':{p.name:sha256_file(p) for p in [OUT/'exact-predictions.parquet',OUT/'simulated-predictions.parquet',OUT/'prefit-manifest.json']}}
    save(OUT/'score-report.json',report)
    print(json.dumps({'status':report['status'],'gates':primary['gates'],'stability':report['numerical_stability'],
        'methods':primary['methods'],'paired':primary['paired']},indent=2))


if __name__=='__main__':main()
