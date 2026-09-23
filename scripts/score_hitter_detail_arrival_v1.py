"""Score the predeclared detail ablation; never tune or deploy from this report."""
import json
from pathlib import Path
import numpy as np
import polars as pl
from sklearn.metrics import roc_auc_score,average_precision_score
from fit_hitter_detail_arrival_v1 import OUT,TARGETS
from fit_hitter_arrival_coherence_v1 import save
from universal_baseball.hitter_detail_arrival import losses
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

GROUPS={'all':pl.lit(True),'prospects':pl.col('prospect'),
    'upper_prospects':pl.col('prospect')&(pl.col('stage')=='Upper minors'),
    'lower_prospects':pl.col('prospect')&(pl.col('stage')=='Lower minors'),
    'recent_debut':pl.col('recent_debut'),
    'young_brief_mlb':(pl.col('age')<=23)&pl.col('mlb_pa_lag0').is_between(1,99)}


def metrics(f):
    if not f.height:return None
    b,l=losses(f['actual'],f['probability'])
    q=f.with_columns(pl.Series('brier',b),pl.Series('log_loss',l))
    means=q.group_by('origin_year').agg(pl.col('brier').mean(),pl.col('log_loss').mean())
    positives=int(f['actual'].sum());pred=float(f['probability'].sum())
    annual=[]
    for y,g in q.partition_by('origin_year',as_dict=True).items():
        actual=g['actual'].to_numpy();p=g['probability'].to_numpy()
        annual.append({'origin':int(y[0]),'rows':g.height,'observed':int(actual.sum()),'expected':float(p.sum()),
            'brier':float(g['brier'].mean()),'log_loss':float(g['log_loss'].mean()),
            'auc':float(roc_auc_score(actual,p)) if len(np.unique(actual))==2 else None,
            'average_precision':float(average_precision_score(actual,p)) if actual.sum()>0 else None})
    calibration=q.with_columns((pl.col('probability')*10).floor().clip(0,9).cast(pl.Int32).alias('bin')).group_by('bin').agg(
        pl.len().alias('rows'),pl.col('actual').sum().alias('observed'),pl.col('probability').sum().alias('expected'),
        pl.col('probability').mean().alias('mean_probability')).sort('bin').to_dicts()
    return {'rows':f.height,'players':f['player_id'].n_unique(),'origins':means.height,
        'observed':positives,'expected':pred,'ratio':pred/positives if positives else None,
        'brier':float(means['brier'].mean()),'log_loss':float(means['log_loss'].mean()),
        'annual':sorted(annual,key=lambda r:r['origin']),'calibration':calibration}


def paired(a,b):
    keys=['origin_year','player_id','target']
    j=a.select(*keys,'actual',pl.col('probability').alias('p')).join(
        b.select(*keys,pl.col('probability').alias('q')),on=keys,how='inner',validate='1:1')
    assert j.height==a.height==b.height and j.height>0
    out={}
    for name,la,lb in zip(('brier','log_loss'),losses(j['actual'],j['p']),losses(j['actual'],j['q'])):
        f=j.with_columns(pl.Series('candidate',la),pl.Series('baseline',lb))
        out[name]=compare_losses(f,'candidate','baseline',draws=2000)
    return out


def models(f):
    return {f'{engine}/{arm}':metrics(g) for (engine,arm),g in f.partition_by('engine','arm',as_dict=True).items()}


def assess(f):
    groups={name:models(f.filter(expr)) for name,expr in GROUPS.items()}
    p=f.filter(pl.col('prospect'));m=groups['prospects'];r=m['lightgbm/R']
    comparisons={}
    for engine,ref in [('lightgbm','B1'),('lightgbm','B2'),('logistic','B2')]:
        comparisons[f'{engine}/R_minus_{ref}']=paired(p.filter((pl.col('engine')==engine)&(pl.col('arm')=='R')),
            p.filter((pl.col('engine')==engine)&(pl.col('arm')==ref)))
    gates={'support':r['origins']>=3 and r['observed']>=30,
        'brier_and_log_intervals':all(comparisons[f'lightgbm/R_minus_{ref}'][s]['interval95'][1]<0 for ref in ('B1','B2') for s in ('brier','log_loss')),
        'majority_origins':all(comparisons[f'lightgbm/R_minus_{ref}'][s]['improving_origins']>r['origins']/2 for ref in ('B1','B2') for s in ('brier','log_loss')),
        'calibration':r['ratio'] is not None and .75<=r['ratio']<=1.25,
        'logistic_direction':all(comparisons['logistic/R_minus_B2'][s]['delta']<0 for s in ('brier','log_loss')),
        'stage_guards':all(g['lightgbm/R'][s]<=1.1*g[f'lightgbm/{ref}'][s]
            for name,g in groups.items() if name in ('upper_prospects','lower_prospects') and g['lightgbm/R']['rows']>=200 and g['lightgbm/R']['observed']>=30
            for ref in ('B1','B2') for s in ('brier','log_loss'))}
    favorable=all(r[s]<m['lightgbm/'+ref][s] for ref in ('B1','B2') for s in ('brier','log_loss'))
    status='development_probability_evidence_only' if all(gates.values()) else ('promising_not_confirmed' if favorable else 'richer_bundle_not_supported')
    return {'status':status,'groups':groups,'paired_prospect_comparisons':comparisons,'gates':gates}


def main():
    fit=json.loads((OUT/'fit-manifest.json').read_text())
    for n,h in fit['files'].items():assert sha256_file(OUT/n)==h
    f=pl.read_parquet(OUT/'predictions.parquet')
    normal=f.filter(~pl.col('cold')&~pl.col('pandemic'))
    report={'targets':{},'stress':{},'cold':{},'practical_references':{},'nonoverlap_2021':{},
        'production_forecasts_changed':False,'protected_outcomes_used':False,
        'scope':'Probability feature ablation, not delivered value or career-path validation'}
    refs=pl.read_parquet(OUT/'reference-predictions.parquet')
    for target in TARGETS:
        print('Scoring '+target,flush=True)
        t=normal.filter(pl.col('target')==target)
        report['targets'][target]=assess(t)
        report['stress'][target]=models(f.filter((pl.col('target')==target)&pl.col('pandemic')&~pl.col('cold')&pl.col('prospect')))
        report['cold'][target]=models(f.filter((pl.col('target')==target)&pl.col('cold')&pl.col('prospect')))
        report['nonoverlap_2021'][target]=models(t.filter((pl.col('origin_year')==2021)&pl.col('prospect')))
        candidate=t.filter((pl.col('engine')=='lightgbm')&(pl.col('arm')=='R')&pl.col('prospect'))
        comparisons={}
        for (name,),r in refs.filter(pl.col('target')==target).partition_by('model',as_dict=True).items():
            j=candidate.join(r.select('origin_year','player_id',pl.col('probability').alias('reference_probability')),
                on=['origin_year','player_id'],how='inner',validate='1:1')
            if not j.height:continue
            b=j.with_columns(pl.col('reference_probability').alias('probability'))
            comparisons[name]={'challenger':metrics(j),'reference':metrics(b),'paired':paired(j,b)}
        report['practical_references'][target]=comparisons
    report['hashes']={p.name:sha256_file(p) for p in [OUT/'predictions.parquet',OUT/'prefit-manifest.json',OUT/'fit-manifest.json']}
    report['score_code_sha256']=sha256_file(Path(__file__))
    save(OUT/'score-report.json',report)
    print(json.dumps({t:{'status':a['status'],'gates':a['gates'],
        'prospects':{name:{k:m[k] for k in ('rows','observed','expected','brier','log_loss')} for name,m in a['groups']['prospects'].items()}}
        for t,a in report['targets'].items()},indent=2))


if __name__=='__main__':main()
