"""Replay binary heads and prepare probability/workload/value player evidence."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from fit_practical_hitter_v31 import weights
from score_practical_hitter_v31 import paired
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.histogram_prediction_trace import trace
from universal_baseball.storage import sha256_file
import evaluate_hitter_readiness_v49 as e


def probability_score(g,arm):
    truth=(g['next_pa'].to_numpy()>0).astype(float);p=g[arm+'_p'].to_numpy();w=weights(g);w=w/w.sum();clipped=np.clip(p,1e-15,1-1e-15)
    return dict(brier=float(np.sum(w*(p-truth)**2)),log_loss=float(-np.sum(w*(truth*np.log(clipped)+(1-truth)*np.log1p(-clipped)))),
        actual_participants=int(truth.sum()),expected_participants=float(p.sum()),weighted_actual_probability=float(w@truth),weighted_expected_probability=float(w@p))


def main():
    pre=e.old.r.read(e.OUT/'preflight.json')
    for p,h in pre['input_hashes'].items():assert sha256_file(e.ROOT/p)==h,p
    f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet');base=pl.read_parquet(e.prior.OUT/'predictions.parquet');assert f.select(base.columns).equals(base)
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');note=e.old.r.read(e.OUT/f"fit-{c['year']}-{c['fold']}.json")
            for arm,names in pre['arms'].items():
                for head in ['participation','conditional_pa']:
                    n=next(h for h in note['heads'] if h['arm']==arm and h['head']==head);assert sha256_file(e.ROOT/n['path'])==n['sha256'];model=joblib.load(n['path'])
                    raw=model.predict_proba(te.select(names).to_numpy())[:,1] if head=='participation' else model.predict(te.select(names).to_numpy())
                    assert np.allclose(raw,q[arm+('_raw_p' if head=='participation' else '_raw_conditional_pa')],rtol=0,atol=1e-10)
                assert np.allclose(q[arm+'_pa'],q[arm+'_p']*q[arm+'_conditional_pa'],rtol=0,atol=1e-10)
                assert q[arm+'_rate'].equals(q['cohort_rate']) and np.allclose(q[arm+'_value'],q[arm+'_pa']*(q['cohort_rate']/600+q['origin_replacement_rate']),rtol=0,atol=1e-10)
                unavailable=q['reported_retired']|q['hard_unavailable'];assert (q.filter(unavailable)[arm+'_p']==0).all()
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f),('public_active',public),('upper_never_debut',f.filter((pl.col('stage')=='Upper minors')&(pl.col('prior_debut')==0))),
        ('brief_debut',f.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),('listed_current',f.filter(pl.col('positive_rank_gate'))),
        ('top20_current',f.filter(pl.col('scout_rank_score_0')>=.81)),('lower_ranked',f.filter((pl.col('stage')=='Lower minors')&pl.col('positive_rank_gate')))]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in sorted(f['origin_year'].unique()))
    scopes.extend(('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique()))
    scores=[];prob=[];intervals=[]
    for label,g in scopes:
        arms=['binary_count','binary_scout','retired_games','scout','fallback','retired_safe_ridge']+(['steamer'] if label=='public_active' else [])
        scores.append(dict(scope=label,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),scores={a:score(g,a) for a in arms}))
        prob.append(dict(scope=label,rows=len(g),scores={a:probability_score(g,a) for a in pre['arms']}))
        if label in ['all','public_active','upper_never_debut','lower_ranked']:
            for a,refs in [('binary_count',['retired_games']),('binary_scout',['binary_count','scout','fallback'])]:
                for ref in refs:
                    for m in ['pa','value']:intervals.append(dict(scope=label,**paired(g,a,ref,m)))
    e.write('scores.json',scores);e.write('probability-scores.json',prob);e.write('intervals.json',intervals)
    previous=e.old.r.read(e.prior.OUT/'cases.json');selected={c['origin']['row_id']:list(c['selection'])+['fixed previous diagnostic'] for c in previous}
    for arm in pre['arms']:
        for m in ['pa','value']:
            q=f.with_columns(((pl.col('retired_games_'+m)-pl.col('next_'+m))**2-(pl.col(arm+'_'+m)-pl.col('next_'+m))**2).alias('gain'),(pl.col(arm+'_'+m)-pl.col('next_'+m)).alias('error'))
            for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),('false high',q.sort('error',descending=True)),('false low',q.sort('error')),('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(arm+' '+m+' '+label)
    counts=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');games=pl.read_parquet(e.old.BASE/'game-counts.parquet');counts=counts.join(games.select('season','player_id','bucket','games_played'),on=['season','player_id','bucket'],how='left',validate='1:1')
    ranks=pl.read_parquet(e.old.OUT/'ranks.parquet');rankprofile=pl.read_parquet(e.old.OUT/'profile-support.parquet');conditionalprofile=pl.read_parquet(e.OUT/'conditional-profile.parquet');support=pl.read_parquet(e.OUT/'support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];te=source.filter(pl.col('row_id')==rid);y,k=o['origin_year'],o['outer_fold'];note=e.old.r.read(e.OUT/f'fit-{y}-{k}.json');heads={}
            for arm,names in pre['arms'].items():
                cls=joblib.load(next(h['path'] for h in note['heads'] if h['arm']==arm and h['head']=='participation'));reg=joblib.load(next(h['path'] for h in note['heads'] if h['arm']==arm and h['head']=='conditional_pa'))
                heads[arm]=dict(participation=e.logit_trace(cls,te.select(names).to_numpy()[0],names),conditional_pa=trace(reg,te.select(names).to_numpy()[0],names))
                assert np.isclose(heads[arm]['participation']['linked_probability'],o[arm+'_raw_p'],atol=1e-10) and np.isclose(heads[arm]['conditional_pa']['raw_prediction'],o[arm+'_raw_conditional_pa'],atol=1e-8)
            peers=f.filter((pl.col('origin_year')==y)&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id'])).with_columns(
                ((pl.col('age')-o['age'])**2+((pl.col('pa_0')-o['pa_0'])/100)**2+((pl.col('minor_pa_0')-o['minor_pa_0'])/250)**2+(pl.col('quality_0')-o['quality_0'])**2+4*(pl.col('scout_rank_score_0')-o['scout_rank_score_0'])**2).alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,actual_inputs={n:te[n][0] for n in pre['arms']['binary_scout']},source_history=counts.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season','bucket').to_dicts(),
                source_ranks=ranks.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(y-2,y)).sort('season').to_dicts(),heads=heads,
                broad_rank_profile=rankprofile.filter(pl.col('row_id')==rid).to_dicts(),conditional_rank_profile=conditionalprofile.filter(pl.col('row_id')==rid).to_dicts(),training_support=support.filter(pl.col('row_id')==rid).to_dicts(),
                peers=peers.select('player_id','player_name','age','pa_0','minor_pa_0','scout_rank_score_0','binary_count_p','binary_scout_p','binary_count_conditional_pa','binary_scout_conditional_pa','retired_games_pa','binary_count_pa','binary_scout_pa','next_pa','next_value').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(replayed_heads=140,all_old_columns_exact=True,rate_unchanged=True,expected_pa_product_verified=True,logit_and_conditional_case_paths_reconstructed=True,player_walkthrough_status='pending',protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:7]:print(s['scope'],{a:(round(v['pa_rmse'],3),round(v['pa_mae'],3),round(v['value_rmse'],5),round(v['pa_total'])) for a,v in s['scores'].items()},flush=True)
    print('Actual readiness reviews prepared:',len(cases),'disposition pending.',flush=True)


if __name__=='__main__':main()
