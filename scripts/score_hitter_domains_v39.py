"""Score dedicated origin-current MLB work and preserve individual tree paths."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_hitter_domains_v39 as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file

FIXED=[(592450,2016),(592450,2024),(691026,2023),(668715,2022),(668901,2022),(614177,2021),(680574,2023),(666158,2023),(701762,2024)]


def main():
    r=e.previous.s.r;pre=r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(pre['source_features'])
    old=pl.read_parquet(e.previous.OUT/'predictions.parquet').sort('row_id')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert f.select(old.columns).equals(old) and f['domain_rate'].equals(f['cohort_rate'])
    assert np.allclose(f['domain_value'],f['domain_pa']*(f['domain_rate']/600+f['origin_replacement_rate']),atol=1e-10,rtol=0)
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert (tr['pa_0']>0).all() and (te['pa_0']>0).all() and not set(tr['player_id'])&set(te['player_id'])
            assert tr['target_year'].max()<=c['year'] and (tr['target_year']!=2020).all()
            assert tr.filter(pl.col('next_pa')==0).height==c['training_future_zero_rows']
            n=r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json");assert sha256_file(Path(n['path']))==n['sha256']
            model=joblib.load(n['path']);p=np.clip(model.predict(te.select(pre['features']).to_numpy()),0,800);p[te['hard_unavailable'].to_numpy()]=0
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');assert np.allclose(p,q['domain_pa'],atol=1e-10,rtol=0)
    absent=f.filter(pl.col('pa_0')==0);assert absent['domain_pa'].equals(absent['games_pa']) and absent['domain_value'].equals(absent['games_value'])
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f,['games','cohort','safe_ridge']),('public_active',public,['games','cohort','safe_ridge','steamer']),
        ('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),['games','cohort','safe_ridge','v24']),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),['games','cohort','legacy_n'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),['games','cohort']) for y in r.YEARS)
    scopes.extend(('stage_'+stage,f.filter(pl.col('stage')==stage),['games']) for stage in sorted(f['stage'].unique()))
    for name,cond in [('current_absent',pl.col('pa_0')==0),('current_partial',pl.col('pa_0').is_between(1,399)),('current_regular',pl.col('pa_0')>=400),
        ('brief_debut',pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300)),('current_mlb_future_zero',(pl.col('pa_0')>0)&(pl.col('next_pa')==0))]:
        scopes.append((name,f.filter(cond),['games','cohort']))
    scores=[];intervals=[]
    for name,g,refs in scopes:
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ['domain',*refs]},rate_scores={a:rate_score(g,a+'_rate') for a in ['domain','cohort']}))
        if name in ['all','public_active','v24_matched','brief_debut','current_regular']:
            for ref in ['games','safe_ridge'] if 'safe_ridge' in refs else ['games']:
                for metric in ['pa','value']:intervals.append(dict(scope=name,**paired(g,'domain',ref,metric)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    e.write('verification.json',dict(replayed_heads=35,all_old_fields_bit_exact=True,noncurrent_mlb_bit_exact=True,rate_bit_exact=True,
        subset_chronology_support_checked=True,future_exit_rows_retained=True,protected_outcomes_used=False,player_walkthrough_status='pending'))
    for g in scores[:4]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()},flush=True)
    selected={}
    for pid,y in FIXED:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1,(pid,y);selected[q['row_id'][0]]=['Fixed diagnostic']
    for metric in ['pa','value']:
        q=f.with_columns(((pl.col('games_'+metric)-pl.col('next_'+metric))**2-(pl.col('domain_'+metric)-pl.col('next_'+metric))**2).alias('gain'),
            (pl.col('domain_'+metric)-pl.col('next_'+metric)).alias('error'))
        for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),
            ('false high',q.sort('error',descending=True)),('false low',q.sort('error')),
            ('ordinary',q.filter((pl.col('pa_0')>0)&pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(metric+' '+label)
    raw=pl.read_parquet(r.OUT/'counts.parquet');games=pl.read_parquet(e.previous.OUT/'game-counts.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);new=te.to_dicts()[0];y,k=o['origin_year'],o['outer_fold']
            oldnote=r.read(e.previous.OUT/f'fit-{y}-{k}.json');oldmodel=joblib.load(oldnote['path'])
            benchmark=trace(oldmodel,te.select(pre['features']).to_numpy()[0],pre['features'])
            n=r.read(e.OUT/f'fit-{y}-{k}.json') if o['pa_0']>0 else oldnote
            model=joblib.load(n['path']);candidate=trace(model,te.select(pre['features']).to_numpy()[0],pre['features'])
            assert np.isclose(np.clip(candidate['raw_prediction'],0,800)*(not o['hard_unavailable']),o['domain_pa'],atol=1e-8)
            peers=source.filter((pl.col('origin_year')==y)&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
            distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3).join(f.select('row_id','games_pa','domain_pa'),on='row_id',validate='1:1')
            history=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).join(games.select('season','player_id','bucket','games_played'),on=['season','player_id','bucket'],validate='1:1').sort('season','bucket')
            cases.append(dict(origin=o,selection=reasons,source_history=history.to_dicts(),actual_features={c:new[c] for c in pre['features']},
                benchmark_model=oldnote,candidate_model=n,benchmark_path_accounting=benchmark,candidate_path_accounting=candidate,
                candidate_head='dedicated origin-current MLB' if o['pa_0']>0 else 'unchanged shared non-MLB',
                peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','games_pa','domain_pa','next_pa','next_value','distance').to_dicts()))
    e.write('cases.json',cases);print('Prepared',len(cases),'full player reviews.',flush=True)


if __name__=='__main__':main()
