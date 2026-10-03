"""Replay identical folds; score practical workload and preserve player mechanics."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_games_v38 as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file


def main():
    pre=e.s.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.old.OUT/'predictions.parquet').sort('row_id')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert f.select(base.columns).equals(base) and f['games_rate'].equals(f['cohort_rate'])
    assert np.allclose(f['games_value'],f['games_pa']*(f['games_rate']/600+f['origin_replacement_rate']),atol=1e-10,rtol=0)
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert not set(tr['player_id'])&set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            n=e.s.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json");assert sha256_file(Path(n['path']))==n['sha256']
            model=joblib.load(n['path']);p=np.clip(model.predict(te.select(pre['features']).to_numpy()),0,800);p[te['hard_unavailable'].to_numpy()]=0
            assert np.allclose(p,q['games_pa'],atol=1e-10,rtol=0)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f,['cohort','safe_ridge']),('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),['cohort','safe_ridge','v24']),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),['cohort','legacy_n']),('public_active',public,['cohort','safe_ridge','steamer'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),['cohort']) for y in e.s.r.YEARS)
    scopes.extend(('stage_'+stage,f.filter(pl.col('stage')==stage),['cohort']) for stage in sorted(f['stage'].unique()))
    for name,cond in [('current_absent',pl.col('pa_0')==0),('current_partial',pl.col('pa_0').is_between(1,399)),('current_regular',pl.col('pa_0')>=400),
        ('brief_debut',pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300)),('thin_entry',pl.col('recent_all_pa')<100),
        ('dsl_current',pl.col('DSL_0_pa')>0)]:scopes.append((name,f.filter(cond),['cohort']))
    scores=[];intervals=[]
    for name,g,refs in scopes:
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ['games',*refs]},rate_scores={a:rate_score(g,a+'_rate') for a in ['games','cohort']}))
        if name in ['all','v24_matched','legacy_n_matched','public_active','brief_debut','current_regular']:
            for ref in ['cohort','safe_ridge'] if 'safe_ridge' in refs else ['cohort']:
                for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,'games',ref,metric)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    e.write('verification.json',dict(replayed_heads=35,baseline_fields_bit_exact=True,batting_head_bit_exact=True,source_hashes_unchanged=True,
        training_membership_unchanged=True,protected_outcomes_used=False,player_walkthrough_status='pending',predictive_certification=False))
    for g in scores[:4]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()},flush=True)
    selected={}
    for pid,y in e.s.FIXED:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1;selected[q['row_id'][0]]=['Fixed diagnostic']
    for metric in ['pa','value']:
        q=f.with_columns(((pl.col('cohort_'+metric)-pl.col('next_'+metric))**2-(pl.col('games_'+metric)-pl.col('next_'+metric))**2).alias('gain'),
            (pl.col('games_'+metric)-pl.col('next_'+metric)).alias('error'))
        for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),
            ('false high',q.sort('error',descending=True)),('false low',q.sort('error')),
            ('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(metric+' '+label)
    cases=[];raw=pl.read_parquet(e.s.r.OUT/'counts.parquet');games=pl.read_parquet(e.OUT/'game-counts.parquet')
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);new=te.to_dicts()[0];y,k=o['origin_year'],o['outer_fold']
            n=e.s.r.read(e.OUT/f'fit-{y}-{k}.json');model=joblib.load(n['path']);newtrace=trace(model,te.select(pre['features']).to_numpy()[0],pre['features'])
            previous=e.s.r.read(e.old.OUT/f'fits-{y}-{k}.json')['models']
            if not previous:previous=[n for n in e.s.r.read(e.old.BASE/f'fits-{y}-{k}.json')['models'] if n['arm']=='pedigree']
            oldpa=next(n for n in previous if n['metric']=='pa');oldmodel=joblib.load(oldpa['path'])
            oldtrace=trace(oldmodel,te.select(pre['old_features']).to_numpy()[0],pre['old_features'])
            assert np.isclose(np.clip(oldtrace['raw_prediction'],0,800)*(not o['hard_unavailable']),o['cohort_pa'],atol=1e-8)
            peers=source.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
            peers=peers.join(f.select('row_id','games_pa','cohort_pa','games_value'),on='row_id',validate='1:1')
            hist=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).join(games.select('season','player_id','bucket','games_played'),on=['season','player_id','bucket'],validate='1:1').sort('season','bucket')
            cases.append(dict(origin=o,selection=reasons,source_history=hist.to_dicts(),actual_new_inputs={c:new[c] for c in pre['features']},
                benchmark_model=oldpa,candidate_model=n,benchmark_path_accounting=oldtrace,candidate_path_accounting=newtrace,
                peers=peers.select('player_id','player_name','age','stage','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number',
                    'games_mlb_0','role_mlb_0','games_minor_0','role_minor_0','cohort_pa','games_pa','next_pa','next_value','distance').to_dicts()))
    e.write('cases.json',cases);print('Prepared',len(cases),'stats-to-forecast reviews.',flush=True)


if __name__=='__main__':main()
