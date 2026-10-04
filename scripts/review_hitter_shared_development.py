"""Actual inputs, saved linear fits and player comparisons before disposition."""
import json
from pathlib import Path
import shutil
import sys
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from universal_baseball.storage import sha256_file
from universal_baseball.hitter_shared_development import LEVEL_FEATURES,AGE_FEATURES,HORIZON_FEATURES
from universal_baseball.hitter_talent_bridge import PROFILE_FEATURES,SCOUT_FEATURES
from prepare_practical_hitter_v33 import safe_matrix
import evaluate_hitter_shared_development as e


def accounting(model,frame,names):
    x=safe_matrix(frame,names)[0];terms=x*model.coef_;groups={
        'original_age':[n for n in names if n in ['age_centered','age_squared']],
        'level_age':[n for n in names if n in AGE_FEATURES],
        'level_baseline':[n for n in names if n in LEVEL_FEATURES],
        'horizon':[n for n in names if n in HORIZON_FEATURES],
        'translated':[n for n in names if n in PROFILE_FEATURES],
        'pedigree':[n for n in names if n in SCOUT_FEATURES or n.startswith('draft_')]}
    assigned={n for group in groups.values() for n in group}
    groups['remaining']=[n for n in names if n not in assigned]
    grouped={g:float(sum(terms[names.index(n)] for n in group)) for g,group in groups.items()}
    result=dict(intercept=float(model.intercept_),terms=grouped,rate=float(model.intercept_+terms.sum()),
        actual_inputs=frame.select(names).row(0,named=True))
    assert np.isclose(result['rate'],model.predict(safe_matrix(frame,names))[0],atol=1e-10,rtol=0)
    return result


def prepare():
    assert not (e.OUT/'cases.json').exists(),'Preserve case traces'
    pre=e.read(e.OUT/'preflight.json');e.verify(pre['input_hashes']);e.verify(e.read(e.OUT/'fit-seal.json'))
    q=pl.read_parquet(e.OUT/'predictions.parquet').sort('row_id');selection=e.read(e.OUT/'selected-cases.json')
    source=pl.read_parquet(e.bridge.previous.OUT/'features.parquet')
    stints=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet')
    support=pl.read_parquet(e.FOLLOW/'support.parquet');cases=[];models={};contexts={}
    with threadpool_limits(limits=2):
        for s in selection:
            y,k,rid=s['origin_year'],s['outer_fold'],s['row_id']
            if k not in contexts:contexts[k]=e.context(k)[1]
            f=contexts[k];te=f.filter(pl.col('row_id')==rid)
            row=q.filter(pl.col('row_id')==rid).row(0,named=True);linear={}
            heads=e.read(e.OUT/f'fit-{y}-{k}.json')['heads']
            bh=next(h for h in e.read(e.bridge.OUT/f'fit-{y}-{k}.json')['heads'] if h['arm']=='translated_ridge')
            for arm,h,names in [*[ (h['arm'],h,pre['features'][h['arm']]) for h in heads],
                ('translated_ridge',bh,e.read(e.bridge.OUT/'preflight.json')['features']['translated_ridge'])]:
                e.verify({h['path']:h['sha256']})
                if h['path'] not in models:models[h['path']]=joblib.load(h['path'])
                linear[arm]=accounting(models[h['path']],te,names)
                assert np.isclose(linear[arm]['rate'],row[arm+'_all_rate'],atol=1e-10,rtol=0)
            origin=te.select('row_id','player_id','player_name','origin_year','outer_fold','age','age_unknown','prior_debut',
                'dominant_level','audit_age_band','source_position','minor_pa_0','pa_0','scout_listed_0','scout_rank_score_0','draft_known','draft_rank','on_40man').row(0,named=True)
            peers=f.filter((pl.col('origin_year')==y)&(pl.col('dominant_level')==origin['dominant_level'])&
                (pl.col('audit_age_band')==origin['audit_age_band'])&(pl.col('prior_debut')==origin['prior_debut'])&(pl.col('row_id')!=rid))
            peers=peers.with_columns((abs(pl.col('age')-origin['age'])+abs(pl.col('minor_pa_0')-origin['minor_pa_0'])/300+
                abs(pl.col('pa_0')-origin['pa_0'])/300+
                pl.when(pl.col('source_position')!=origin['source_position']).then(1.).otherwise(0.)+
                abs(pl.col('scout_rank_score_0')-origin['scout_rank_score_0'])+
                abs(pl.col('draft_rank')-origin['draft_rank'])).alias('peer_distance')).sort('peer_distance','player_id').head(4)
            peer_rows=[]
            for p in peers.iter_rows(named=True):
                saved=q.filter(pl.col('row_id')==p['row_id']).row(0,named=True)
                peer_rows.append({n:saved[n] for n in ['player_id','player_name','age','source_position','minor_pa_0','pa_0',
                    'scout_rank_score_0','draft_rank','preseason_pa','next_pa','next_value','translated_ridge_rate','level_age_rate','shared_development_rate']})
            stats=stints.filter((pl.col('player_id')==origin['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket','team_id')
            cases.append(dict(origin=origin,selection=s,dated_stats=stats.to_dicts(),linear_accounting=linear,
                actual_fold_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peer_rows,peer_selection='Same origin/dominant-level/age-band/debut; nearest age/PA/position/rank/draft without future outcomes',
                rates_are_selected_future_MLB_performance_not_latent_never_arrival_talent=True))
    e.write('cases.json',cases)
    paths=[Path(__file__),e.OUT/'cases.json',e.OUT/'selected-cases.json',e.OUT/'verification.json',e.OUT/'scores.json',e.OUT/'intervals.json',
        e.OUT/'predictions.parquet',e.OUT/'preflight.json',e.OUT/'fit-seal.json',e.OUT/'fits.json',
        e.ROOT/'reports/generated/practical-hitter-v31/dated-stints.parquet']
    e.write('review-preparation.json',dict(player_walkthrough_status='pending',case_count=len(cases),
        hashes={str(p):sha256_file(p) for p in paths},model_hashes={h['path']:h['sha256'] for n in e.read(e.OUT/'fits.json') for h in n['heads']}))
    for c in cases:
        print(c['origin'],c['selection'],{a:{k:v for k,v in t.items() if k!='actual_inputs'} for a,t in c['linear_accounting'].items()},
            'STATS',[(t['season'],t['bucket'],t['plate_appearances'],t['home_runs'],t['unintentional_walks'],t['strike_outs']) for t in c['dated_stats']],
            'PEERS',[(p['player_name'],p['next_pa'],p['next_value']) for p in c['peers']],flush=True)


def finalize():
    prep=e.read(e.OUT/'review-preparation.json');e.verify(prep['hashes']);e.verify(prep['model_hashes'])
    notes=e.read(e.ROOT/'config/hitter_shared_development_review.json');cases=e.read(e.OUT/'cases.json')
    assert set(notes)=={str(c['origin']['row_id']) for c in cases}
    assert all(n['review_status']=='complete' and n['assessment'] for n in notes.values())
    e.write('reviewed-cases.json',[dict(row_id=c['origin']['row_id'],player_id=c['origin']['player_id'],
        name=c['origin']['player_name'],**notes[str(c['origin']['row_id'])]) for c in cases])
    paths=[e.ROOT/'config/hitter_shared_development_review.json',e.ROOT/'docs/hitter-shared-development-result.md',e.OUT/'reviewed-cases.json']
    e.write('final-report.json',dict(player_walkthrough_status='complete',reviewed_cases=len(cases),new_heads_replayed=70,
        disposition='See reviewed result; no automatic promotion',protected_outcomes_used=False,frozen_forecast_changed=False,
        explorer_changed=False,deployment_approved=False,full_goal_complete=False,
        source_and_execution_hashes=e.read(e.OUT/'preflight.json')['input_hashes'],
        review_preparation_hashes=prep['hashes'],model_hashes=prep['model_hashes'],review_hashes={str(p):sha256_file(p) for p in paths}))
    evidence=e.ROOT/'reports/model-evidence/hitter-shared-development';evidence.mkdir(parents=True,exist_ok=True)
    for name in ['scores.json','intervals.json','selected-cases.json','cases.json','verification.json','reviewed-cases.json','final-report.json']:
        shutil.copyfile(e.OUT/name,evidence/name);assert sha256_file(e.OUT/name)==sha256_file(evidence/name)
    print('All actual player walks finalized:',len(cases))


if __name__=='__main__':{'prepare':prepare,'finalize':finalize}[sys.argv[1]]()
