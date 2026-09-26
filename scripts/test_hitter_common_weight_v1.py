"""Locked replay, one weighting intervention, and matched diagnostics."""
import argparse
import json
from pathlib import Path
import warnings
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.hitter_arrival_value_transfer import FOLDS
from universal_baseball.hitter_conditional_workload import fit_head
from universal_baseball.hitter_common_weight import fit_common_weight, paired_mse
from universal_baseball.storage import sha256_file
from score_hitter_conditional_workload_v1 import errors

OUT=Path('model_artifacts/hitter-common-weight-v1-2026-09-25')
OLD=Path('model_artifacts/hitter-conditional-workload-v1-2026-09-23')
PANEL=Path('reports/generated/hitter-arrival-source-repair-v1/repaired-panel.parquet')
PLAN=Path('docs/hitter-workload-common-weight-v1-plan.md')
KEY=['origin_year','player_id','horizon']


def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')


def hashes():
    paths=[PLAN,PANEL,Path(__file__),OLD/'predictions.parquet',OLD/'prefit-manifest.json',OLD/'fit-manifest.json',
        Path('tests/test_hitter_common_weight.py'),Path('scripts/score_hitter_conditional_workload_v1.py')]
    paths += [Path('src/universal_baseball')/(n+'.py') for n in ('hitter_common_weight',
        'hitter_conditional_workload','hitter_arrival_value_transfer','hitter_canceled_season','hitter_model_tournament')]
    return {str(p):sha256_file(p) for p in paths}


def freeze():
    if (OUT/'prefit.json').exists():raise ValueError('Already frozen')
    manifest=json.loads((OLD/'manifest.json').read_text())
    for name,digest in manifest['files'].items():assert sha256_file(OLD/name)==digest
    pre=json.loads((OLD/'prefit-manifest.json').read_text())
    save(OUT/'prefit.json',{'hashes':hashes(),'columns':pre['columns']['D'],'folds':FOLDS,
        'production_changed':False,'protected_outcomes_used':False})
    print('Common-weight experiment frozen',flush=True)


def inputs():
    pre=json.loads((OUT/'prefit.json').read_text());expected=dict(pre['hashes'])
    amendment=OUT/'implementation-amendment.json'
    if amendment.exists():
        amend=json.loads(amendment.read_text())
        assert sha256_file(OUT/'prefit.json')==amend['prefit_sha256']
        assert expected[amend['path']]==amend['before']
        expected[amend['path']]=amend['after']
    assert expected==hashes()
    p=pl.read_parquet(PANEL);f=pl.read_parquet(OLD/'predictions.parquet').sort('horizon','origin_year','player_id')
    for y,h in FOLDS:
        q=p.filter(pl.col('origin_year')==y);b=f.filter((pl.col('origin_year')==y)&(pl.col('horizon')==h))
        np.testing.assert_array_equal(q['player_id'],b['player_id'])
        np.testing.assert_array_equal(q[f'pa_h{h}'],b['actual_pa'])
    assert max(f['origin_year']+f['horizon'])<=2025
    return pre,p,f


def run():
    pre,p,f=inputs();columns=pre['columns'];replays=[]
    # Every legacy replay completes before any intervention fit.
    for y,h in FOLDS:
        print(f'Replay D {y} H{h}',flush=True)
        b=f.filter((pl.col('origin_year')==y)&(pl.col('horizon')==h))
        q,_,note=fit_head(p,columns,y,h,'D')
        delta=float(np.max(np.abs(q-b['D_conditional'].to_numpy())))
        np.testing.assert_allclose(q,b['D_conditional'],atol=1e-9,rtol=0)
        replays.append({'origin':y,'horizon':h,'max_difference':delta})
    save(OUT/'replay.json',{'prefit_sha256':sha256_file(OUT/'prefit.json'),'checks':replays})
    frames=[];notes=[]
    oldfits=json.loads((OLD/'fit-manifest.json').read_text())['fits']
    for y,h in FOLDS:
        print(f'Common weights W {y} H{h}',flush=True)
        b=f.filter((pl.col('origin_year')==y)&(pl.col('horizon')==h))
        q,note=fit_common_weight(p,columns,y,h)
        old=next(n for n in oldfits if n['year']==y and n['horizon']==h and n['head']=='D')
        for key in ('training_rows','training_players','used_features','latest_label'):assert note[key]==old[key],key
        b=b.with_columns(pl.Series('W_conditional',q)).with_columns(
            pl.when(pl.col('prospect')).then(pl.col('fixed_p')*pl.col('W_conditional'))
            .otherwise(pl.col('D_pa')).alias('W_pa'))
        frames.append(b);notes.append(note)
    f=pl.concat(frames)
    y,h=2021,3
    changed=p.with_columns(pl.when(pl.col('origin_year')+h>y).then(99999.).otherwise(pl.col(f'pa_h{h}')).alias(f'pa_h{h}'),
        *[pl.when(pl.col('origin_year')>y).then(987.).otherwise(pl.col(c).cast(pl.Float64)).alias(c) for c in columns])
    q,_=fit_common_weight(changed,columns,y,h)
    np.testing.assert_array_equal(q,f.filter((pl.col('origin_year')==y)&(pl.col('horizon')==h))['W_conditional'])
    f=f.join(p.select('origin_year','player_id','pa_lag0'),on=['origin_year','player_id'],how='left',validate='m:1')
    # Existing entrants can lack prior workload; retain them in all primary
    # populations and report an explicit unknown diagnostic instead of dropping.
    f.write_parquet(OUT/'predictions.parquet')
    save(OUT/'fit-manifest.json',{'prefit_sha256':sha256_file(OUT/'prefit.json'),
        'replay_sha256':sha256_file(OUT/'replay.json'),'prediction_sha256':sha256_file(OUT/'predictions.parquet'),
        'fits':notes,'future_mutation':{'origin':2021,'horizon':3,'max_difference':0},
        'protected_outcomes_used':False,'production_changed':False})
    inputs()  # Verify the same frozen inputs and documented implementation hash.


def score():
    pre,_,_=inputs()
    manifest=json.loads((OUT/'fit-manifest.json').read_text())
    assert manifest['prediction_sha256']==sha256_file(OUT/'predictions.parquet')
    f=pl.read_parquet(OUT/'predictions.parquet')
    np.testing.assert_array_equal(f.filter(~pl.col('prospect'))['W_pa'],f.filter(~pl.col('prospect'))['D_pa'])
    c=f.group_by('origin_year','player_id').agg(pl.len().alias('_n'),pl.col('horizon').n_unique().alias('_nh'),
        *[pl.col(k).first() for k in ('player_name','age','stage','prospect','pa_lag0')],
        *[pl.col(k).sum() for k in ('actual_pa','W_pa','D_pa','E_pa')]).filter((pl.col('_n')==3)&(pl.col('_nh')==3)).sort('origin_year','player_id')
    cp=c.filter(pl.col('prospect'));assert cp.height==9833
    c.write_parquet(OUT/'cumulative.parquet')
    groups={'prospects':pl.col('prospect'),'lower':pl.col('prospect')&(pl.col('stage')=='Lower minors'),
        'upper':pl.col('prospect')&(pl.col('stage')=='Upper minors'),
        'young':pl.col('prospect')&(pl.col('age')<23),'older':pl.col('prospect')&(pl.col('age')>=23),
        'nonarrivers':pl.col('prospect')&(pl.col('actual_pa')==0),
        'prior_pa_under100':pl.col('prospect')&(pl.col('pa_lag0')<100),
        'prior_pa_100_299':pl.col('prospect')&pl.col('pa_lag0').is_between(100,299),
        'prior_pa_300plus':pl.col('prospect')&(pl.col('pa_lag0')>=300),
        'prior_pa_unknown':pl.col('prospect')&pl.col('pa_lag0').is_null()}
    def summarize(g):
        return {'rows':g.height,'unique_players':g['player_id'].n_unique(),'participants':int((g['actual_pa']>0).sum()),
            'arms':{a:errors(g,a+'_pa') for a in ('W','D','E')}}
    result={'primary':paired_mse(cp,'W_pa','D_pa','actual_pa'),
        'ensemble_reference':paired_mse(cp,'W_pa','E_pa','actual_pa'),
        'cumulative':summarize(cp),'annual':{},'cumulative_groups':{},'future_mutation':manifest['future_mutation'],
        'protected_outcomes_used':False,'production_changed':False}
    for h in (1,2,3):
        q=f.filter(pl.col('horizon')==h);pros=q.filter(pl.col('prospect'));active=pros.filter(pl.col('actual_pa')>0)
        result['annual'][str(h)]={'groups':{k:summarize(g) for k,e in groups.items() if (g:=q.filter(e)).height},
            'paired':paired_mse(pros,'W_pa','D_pa','actual_pa'),
            'conditional':{a:errors(active,a+'_conditional') for a in ('W','D')}}
    result['cumulative_groups']={k:summarize(g) for k,e in groups.items() if (g:=c.filter(e)).height}
    change=cp.with_columns((((pl.col('W_pa')-pl.col('actual_pa'))**2)-((pl.col('D_pa')-pl.col('actual_pa'))**2)).alias('error_change'))
    result['examples']={str(y):{'worse':g.sort('error_change',descending=True).head(10).to_dicts(),
        'better':g.sort('error_change').head(10).to_dicts()} for (y,),g in change.group_by('origin_year')}
    result['hashes']={n:sha256_file(OUT/n) for n in ('predictions.parquet','cumulative.parquet','prefit.json','fit-manifest.json','replay.json')}
    save(OUT/'scores.json',result)
    print(json.dumps({k:result[k] for k in ('primary','ensemble_reference','cumulative')},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','run','score']);args=ap.parse_args()
    warnings.filterwarnings('ignore',message='X does not have valid feature names')
    with threadpool_limits(limits=4):{'freeze':freeze,'run':run,'score':score}[args.mode]()
