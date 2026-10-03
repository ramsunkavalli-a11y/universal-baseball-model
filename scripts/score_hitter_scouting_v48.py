"""Verify the fallback, score fixed membership, then prepare full player walks."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from score_practical_hitter_v31 import paired
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
import evaluate_hitter_scouting_v48 as e


def main():
    pre=e.old.r.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.ROOT/p)==h,p
    f=pl.read_parquet(e.OUT/'predictions.parquet');old=pl.read_parquet(e.old.OUT/'predictions.parquet')
    assert f.select(old.columns).equals(old)
    g=pl.read_parquet(e.OUT/'gate-identities.parquet');assert f.select(g.columns).equals(g)
    source=pl.read_parquet(e.old.OUT/'features.parquet');assert f.select('row_id','scout_listed_0','scout_rank_score_0').equals(source.filter(pl.col('row_id').is_in(f['row_id'].to_list())).select('row_id','scout_listed_0','scout_rank_score_0').sort('row_id'))
    assert f.filter(~pl.col('positive_rank_gate'))['fallback_pa'].equals(f.filter(~pl.col('positive_rank_gate'))['retired_games_pa'])
    assert f.filter(pl.col('positive_rank_gate'))['fallback_pa'].equals(f.filter(pl.col('positive_rank_gate'))['scout_pa'])
    assert f['fallback_rate'].equals(f['cohort_rate']) and np.allclose(f['fallback_value'],f['fallback_pa']*(f['cohort_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f),('public_active',public),('upper_never_debut',f.filter((pl.col('stage')=='Upper minors')&(pl.col('prior_debut')==0))),
        ('brief_debut',f.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),
        ('listed_current',f.filter(pl.col('positive_rank_gate'))),('top20_current',f.filter(pl.col('scout_rank_score_0')>=.81))]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in sorted(f['origin_year'].unique()))
    scopes.extend(('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique()))
    scores=[];intervals=[]
    for label,rows in scopes:
        arms=['fallback','retired_games','scout','retired_safe_ridge']+(['steamer'] if label=='public_active' else [])
        scores.append(dict(scope=label,rows=len(rows),players=rows['player_id'].n_unique(),actual_pa=float(rows['next_pa'].sum()),actual_value=float(rows['next_value'].sum()),scores={a:score(rows,a) for a in arms}))
        if label in ['all','public_active','upper_never_debut','brief_debut']:
            for ref in ['retired_games','retired_safe_ridge']:
                for m in ['pa','value']:intervals.append(dict(scope=label,**paired(rows,'fallback',ref,m)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    prior=e.old.r.read(e.old.OUT/'cases.json');cases={c['origin']['row_id']:c for c in prior};selected={rid:list(c['selection'])+['carried previous review'] for rid,c in cases.items()}
    for m in ['pa','value']:
        q=f.with_columns(((pl.col('retired_games_'+m)-pl.col('next_'+m))**2-(pl.col('fallback_'+m)-pl.col('next_'+m))**2).alias('gain'),(pl.col('fallback_'+m)-pl.col('next_'+m)).alias('error'))
        for label,rows in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),('false high',q.sort('error',descending=True)),('false low',q.sort('error')),('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(rows['row_id'][0],[]).append('fallback '+m+' '+label)
        if m=='pa':
            # Outcome-selected follow-up of the observed lower-minor aggregate failure,
            # not a feature/parameter change or independent validation.
            lower=q.filter((pl.col('stage')=='Lower minors')&pl.col('positive_rank_gate'))
            for label,rows in [('lower ranked false high',lower.sort('error',descending=True)),('lower ranked gain',lower.sort('gain',descending=True))]:selected.setdefault(rows['row_id'][0],[]).append(label)
    counts=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');games=pl.read_parquet(e.old.BASE/'game-counts.parquet')
    counts=counts.join(games.select('season','player_id','bucket','games_played'),on=['season','player_id','bucket'],how='left',validate='1:1')
    ranks=pl.read_parquet(e.old.OUT/'ranks.parquet');profile=pl.read_parquet(e.old.OUT/'profile-support.parquet');support=pl.read_parquet(e.old.OUT/'support.parquet');oldprofile=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-joint-forest-v43/support.parquet')
    oldpre=e.old.r.read(e.old.OUT/'preflight.json');out=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);y,k=o['origin_year'],o['outer_fold']
            if rid in cases:c=cases[rid]
            else:
                new=joblib.load(e.old.r.read(e.old.OUT/f'fit-{y}-{k}.json')['path']);base=joblib.load(e.old.r.read(e.old.BASE/f'fit-{y}-{k}.json')['path'])
                peers=f.filter((pl.col('origin_year')==y)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                    ((pl.col('age')-o['age'])**2+((pl.col('pa_0')-o['pa_0'])/100)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+(pl.col('quality_0')-o['quality_0'])**2+4*(pl.col('scout_rank_score_0')-o['scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
                c=dict(actual_inputs={n:te[n][0] for n in oldpre['features']},added_inputs={n:te[n][0] for n in oldpre['added_features']},
                    source_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),source_ranks=ranks.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season').to_dicts(),
                    control_accounting=trace(base,te.select(oldpre['features'][:239]).to_numpy()[0],oldpre['features'][:239]),scout_accounting=trace(new,te.select(oldpre['features']).to_numpy()[0],oldpre['features']),
                    training_profile=oldprofile.filter(pl.col('row_id')==rid).to_dicts(),rank_profile=profile.filter(pl.col('row_id')==rid).to_dicts(),training_support=support.filter(pl.col('row_id')==rid).to_dicts(),peers=peers.select('player_id','player_name','age','pa_0','minor_pa_0','scout_listed_0','scout_rank_score_0','retired_games_pa','scout_pa','next_pa','next_value').to_dicts())
            c['origin']=o;c['selection']=reasons;c['selected_head']='scout' if o['positive_rank_gate'] else 'retired_games'
            t=c['scout_accounting'] if o['positive_rank_gate'] else c['control_accounting'];assert np.isclose(np.clip(t['raw_prediction'],0,800)*(not(o['reported_retired'] or o['hard_unavailable'])),o['fallback_pa'],atol=1e-8)
            out.append(c)
    e.write('cases.json',out);e.write('verification.json',dict(all_old_columns_exact=True,gate_origin_only=True,unlisted_and_unknown_pa_exact_games=True,listed_pa_exact_rank_head=True,rate_unchanged=True,case_means_reconstructed=True,prior_replayed_heads=35,refitted_heads=0,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:6]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Cases requiring complete fallback review:',len(out),'new:',len(out)-len(prior),flush=True)


if __name__=='__main__':main()
