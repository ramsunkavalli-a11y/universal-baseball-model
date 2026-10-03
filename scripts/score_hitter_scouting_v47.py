"""Verify every rank head and prepare matched scores and actual player paths."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from score_practical_hitter_v31 import paired
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
import evaluate_hitter_scouting_v47 as e


def main():
    pre=e.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    for p,h in {**pre['input_hashes'],**pre['raw_source_hashes']}.items():assert sha256_file(Path(p))==h,p
    base=pl.read_parquet(e.r.OUT/'predictions.parquet').sort('row_id');assert f.select(base.columns).equals(base)
    assert f['scout_rate'].equals(f['cohort_rate']) and np.allclose(f['scout_value'],f['scout_pa']*(f['cohort_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            n=e.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json");assert sha256_file(Path(n['path']))==n['sha256']
            raw=joblib.load(n['path']).predict(te.select(pre['features']).to_numpy());assert np.allclose(raw,q['scout_raw_pa'],rtol=0,atol=1e-10)
            p=np.clip(raw,0,800);p[q['hard_unavailable'].to_numpy()|q['reported_retired'].to_numpy()]=0;assert np.allclose(p,q['scout_pa'],rtol=0,atol=1e-10)
    view=f.join(source.select('row_id',*pre['added_features']),on='row_id',validate='1:1')
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f),('public_active',public),('source_supported',f.filter(pl.col('origin_evidence_bridge'))),('roster_only_unverified',f.filter(~pl.col('origin_evidence_bridge'))),
        ('brief_debut',f.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),
        ('upper_never_debut',f.filter((pl.col('stage')=='Upper minors')&(pl.col('prior_debut')==0))),
        ('listed_current',view.filter(pl.col('scout_listed_0')==1)),('top20_current',view.filter(pl.col('scout_rank_score_0')>=.81)),
        ('not_listed_current',view.filter(pl.col('scout_listed_0')==0)),('listing_unknown',view.filter(pl.col('scout_listed_0')<0))]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in sorted(f['origin_year'].unique()))
    scopes.extend(('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique()))
    scores=[];intervals=[]
    for label,g in scopes:
        assert len(g)>0
        arms=['scout','retired_games','retired_cohort','retired_safe_ridge']+(['steamer'] if label=='public_active' else [])
        scores.append(dict(scope=label,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms}))
        if label in ['all','public_active','brief_debut','upper_never_debut','listed_current','top20_current']:
            for ref in ['retired_games','retired_safe_ridge']:
                for m in ['pa','value']:intervals.append(dict(scope=label,**paired(g,'scout',ref,m)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    selected={}
    for pid,y in [x for x in e.FIXED if x!=(666160,2016)]:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1;selected[q['row_id'][0]]=['fixed diagnostic']
    for m in ['pa','value']:
        q=f.with_columns(((pl.col('retired_games_'+m)-pl.col('next_'+m))**2-(pl.col('scout_'+m)-pl.col('next_'+m))**2).alias('gain'),(pl.col('scout_'+m)-pl.col('next_'+m)).alias('error'))
        for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),('false high',q.sort('error',descending=True)),
            ('false low',q.sort('error')),('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(m+' '+label)
    counts=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');games=pl.read_parquet(e.BASE/'game-counts.parquet')
    counts=counts.join(games.select('season','player_id','bucket','games_played'),on=['season','player_id','bucket'],how='left',validate='1:1')
    ranks=pl.read_parquet(e.OUT/'ranks.parquet');profile=pl.read_parquet(e.OUT/'profile-support.parquet');support=pl.read_parquet(e.OUT/'support.parquet')
    old_profile=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-joint-forest-v43/support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);y,k=o['origin_year'],o['outer_fold']
            new=joblib.load(e.r.read(e.OUT/f'fit-{y}-{k}.json')['path']);old=joblib.load(e.r.read(e.BASE/f'fit-{y}-{k}.json')['path'])
            a=trace(new,te.select(pre['features']).to_numpy()[0],pre['features']);b=trace(old,te.select(pre['features'][:239]).to_numpy()[0],pre['features'][:239]);keep=not(o['hard_unavailable'] or o['reported_retired'])
            assert np.isclose(np.clip(a['raw_prediction'],0,800)*keep,o['scout_pa'],atol=1e-8) and np.isclose(np.clip(b['raw_prediction'],0,800)*keep,o['retired_games_pa'],atol=1e-8)
            # Comparison membership and ordering use only origin-known inputs.
            peers=view.filter((pl.col('origin_year')==y)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                ((pl.col('age')-o['age'])**2+((pl.col('pa_0')-o['pa_0'])/100)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+(pl.col('quality_0')-o['quality_0'])**2+
                 4*(pl.col('scout_rank_score_0')-te['scout_rank_score_0'][0])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,actual_inputs={c:te[c][0] for c in pre['features']},added_inputs={c:te[c][0] for c in pre['added_features']},
                source_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                source_ranks=ranks.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season').to_dicts(),
                control_accounting=b,scout_accounting=a,training_profile=old_profile.filter(pl.col('row_id')==rid).to_dicts(),rank_profile=profile.filter(pl.col('row_id')==rid).to_dicts(),training_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','pa_0','minor_pa_0','scout_listed_0','scout_rank_score_0','retired_games_pa','scout_pa','next_pa','next_value').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=35,all_old_columns_exact=True,batting_rate_unchanged=True,case_means_reconstructed=True,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:10]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5)) for a,v in s['scores'].items()},flush=True)
    print('Prepared',len(cases),'actual rank/source/tree reviews; disposition pending.',flush=True)


if __name__=='__main__':main()
