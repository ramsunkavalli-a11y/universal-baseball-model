"""Replay skill shrinkage, score real MLB talent/value and prepare actual cases."""
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.mlb_event_logit import EVENTS,VALUES,batting_rate,NEUTRAL_WOBA_SCALE
from universal_baseball.mlb_predictive_reliability import predict
from universal_baseball.storage import sha256_file
import evaluate_hitter_reliability_v50 as e


def rate_interval(g,a,ref):
    g=g.filter(pl.col('next_pa')>0);error=((g[a+'_rate']-g['next_batting_rate'])**2-(g[ref+'_rate']-g['next_batting_rate'])**2).to_numpy()
    _,people=np.unique(g['player_id'],return_inverse=True);_,years=np.unique(g['target_year'],return_inverse=True)
    n=np.zeros((people.max()+1,years.max()+1));d=np.zeros_like(n);w=g['next_pa'].to_numpy()
    np.add.at(n,(people,years),w*error);np.add.at(d,(people,years),w);rng=np.random.default_rng(50);draw=[]
    for _ in range(1000):
        z=np.bincount(rng.integers(0,len(n),len(n)),minlength=len(n));den=z@d
        if (den>0).all():draw.append(float(np.mean((z@n)/den)))
    return dict(arm=a,reference=ref,metric='actual_PA_weighted_conditional_rate_mse',difference=float(np.mean(n.sum(0)/d.sum(0))),
        lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),repeats=1000,nominal_development_interval=True)


def event_score(g,source,arm):
    raw=source.filter(pl.col('row_id').is_in(g['row_id'])).sort('row_id');g=g.sort('row_id');assert raw['row_id'].equals(g['row_id'])
    active=g['next_pa'].to_numpy()>0;p=g.select([arm+'_p_'+ev for ev in EVENTS]).to_numpy()[active]
    c=raw.select(['count_'+ev for ev in EVENTS]).to_numpy()[active];pa=c.sum(1);years=g['origin_year'].to_numpy()[active]
    loss=[-float((c[years==y]*np.log(p[years==y])).sum()/pa[years==y].sum()) for y in np.unique(years)]
    return dict(equal_origin_PA_count_log_loss=float(np.mean(loss)),calibration_actual_PA={ev:dict(expected=float((p[:,j]*pa).sum()),actual=float(c[:,j].sum())) for j,ev in enumerate(EVENTS)})


def main():
    pre=e.prior.old.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.prior.OUT/'predictions.parquet');assert f.select(base.columns).equals(base.sort('row_id'))
    for p,h in pre['input_hashes'].items():assert sha256_file(e.Path(p))==h,p
    replay=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id');q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            x,own,env=e.arrays(te);note=e.prior.old.r.read(e.OUT/f"fits-{c['year']}-{c['fold']}.json")
            for n in note['heads']:
                a=n['arm'];assert sha256_file(e.Path(n['path']))==n['sha256'];model=joblib.load(n['path'])
                p=predict(model['beta'],model['alpha'],x,own,env)['probabilities']
                assert np.allclose(p,q.select([a+'_p_'+ev for ev in EVENTS]),rtol=0,atol=1e-12)
                assert np.allclose(batting_rate(p,env),q[a+'_rate'],rtol=0,atol=1e-10)
                assert q[a+'_pa'].equals(q['binary_scout_pa']) and np.allclose(q[a+'_value'],q[a+'_pa']*(q[a+'_rate']/600+q['origin_replacement_rate']))
                replay+=1
    f=f.with_columns(pl.col('learned_reliability_rate').alias('learned_working_rate'),pl.col('retired_safe_ridge_pa').alias('learned_working_pa')).with_columns(
        (pl.col('learned_working_pa')*(pl.col('learned_working_rate')/600+pl.col('origin_replacement_rate'))).alias('learned_working_value'))
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f),('public_active',public),('upper_never_debut',f.filter((pl.col('stage')=='Upper minors')&(pl.col('prior_debut')==0))),
        ('brief_debut',f.filter(pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300))),
        ('current_regular',f.filter(pl.col('pa_0')>=400)),('listed_current',f.filter(pl.col('positive_rank_gate'))),('top20_current',f.filter(pl.col('scout_rank_score_0')>=.81)),
        ('no_own_MLB',f.filter(pl.col('pooled_MLB_pa')==0)),('substantial_own_MLB',f.filter(pl.col('pooled_MLB_pa')>=1000))]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y)) for y in sorted(f['origin_year'].unique()))
    scopes.extend(('stage_'+s,f.filter(pl.col('stage')==s)) for s in sorted(f['stage'].unique()))
    scores=[];intervals=[]
    for label,g in scopes:
        arms=pre['arms']+['binary_scout','retired_safe_ridge','learned_working']+(['steamer'] if label=='public_active' else [])
        scores.append(dict(scope=label,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in arms},rate_scores={a:rate_score(g,a+'_rate') for a in pre['arms']+['binary_scout','safe_ridge']+(['steamer','zips'] if label=='public_active' else [])},
            components={a:event_score(g,source,a) for a in pre['arms']}))
        if label in ['all','public_active','brief_debut','no_own_MLB','substantial_own_MLB']:
            for a,ref in [('fixed_reliability','binary_scout'),('learned_reliability','binary_scout'),('learned_reliability','fixed_reliability')]:
                intervals.extend([dict(scope=label,**paired(g,a,ref,'value')),dict(scope=label,**rate_interval(g,a,ref))])
    e.write('scores.json',scores);e.write('intervals.json',intervals);f.write_parquet(e.OUT/'scored-predictions.parquet')
    fixed=[(592450,2016),(592450,2024),(691026,2023),(668715,2022),(458015,2016),(641355,2016),(624413,2018),(683011,2022),(701762,2024),(806956,2024),(808393,2024)]
    selected={}
    for pid,y in fixed:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1;selected[q['row_id'][0]]=['fixed diagnostic']
    for a in pre['arms']:
        for metric in ['rate','value']:
            g=f.filter(pl.col('next_pa')>0) if metric=='rate' else f
            truth='next_batting_rate' if metric=='rate' else 'next_value'
            g=g.with_columns(((pl.col('binary_scout_'+metric)-pl.col(truth))**2-(pl.col(a+'_'+metric)-pl.col(truth))**2).alias('gain'),(pl.col(a+'_'+metric)-pl.col(truth)).alias('error'))
            for label,q in [('largest gain',g.sort('gain',descending=True)),('largest harm',g.sort('gain')),('false high',g.sort('error',descending=True)),('false low',g.sort('error')),('ordinary',g.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:
                selected.setdefault(q['row_id'][0],[]).append(a+' '+metric+' '+label)
    raw=pl.read_parquet(e.ROOT/'reports/generated/practical-hitter-v31/counts.parquet');profile=pl.read_parquet(e.OUT/'profile-support.parquet');cases=[]
    with threadpool_limits(limits=2):
        for rid,reasons in selected.items():
            o=f.filter(pl.col('row_id')==rid).to_dicts()[0];row=source.filter(pl.col('row_id')==rid);x,own,env=e.arrays(row)
            note=e.prior.old.r.read(e.OUT/f"fits-{o['origin_year']}-{o['outer_fold']}.json");heads={}
            for n in note['heads']:
                a=n['arm'];m=joblib.load(n['path']);detail=predict(m['beta'],m['alpha'],x,own,env)
                assert np.allclose(detail['probabilities'][0],[o[a+'_p_'+ev] for ev in EVENTS],atol=1e-12)
                terms=np.r_[1,x[0]][:,None]*m['beta'];idx=np.argsort(-np.max(abs(terms),axis=1))[:10]
                heads[a]=dict(alpha_by_event=n['alpha_by_event'],optimizer=n['optimizer'],
                    events=[dict(event=ev,source_pooled_count=float(own[0,j]),origin_environment=float(env[0,j]),prior=float(detail['prior'][0,j]),
                        pre_normalization_blend=float(detail['blend'][0,j]),own_influence_before_normalization=float(detail['pre_normalization_own_influence'][0,j]),
                        predicted=float(detail['probabilities'][0,j]),actual_count=float(row['count_'+ev][0]),
                        wins_per600=float((detail['probabilities'][0,j]-env[0,j])*VALUES[j]*600/NEUTRAL_WOBA_SCALE/10)) for j,ev in enumerate(EVENTS)],
                    top_prior_log_odds_terms=[dict(feature='intercept' if i==0 else e.FEATURES[i-1],scaled_input=float(np.r_[1,x[0]][i]),effects=dict(zip(EVENTS[1:],terms[i].tolist()))) for i in idx])
            peers=f.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut'])&(pl.col('player_id')!=o['player_id']))
            distance=sum(((pl.col(name)-o[name])/scale)**2 for name,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('draft_rank',.25),('draft_known',1),('draft_college',1),('scout_rank_score_0',.5)])
            peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(4)
            cases.append(dict(origin=o,selection=reasons,actual_prior_inputs=row.select(e.FEATURES).to_dicts()[0],scaled_prior_inputs=dict(zip(e.FEATURES,x[0].tolist())),
                source_MLB_history=row.select(e.HISTORY+e.HISTORY_ENV).to_dicts()[0],source_history=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
                weighted_MLB_PA=float(own.sum()),heads=heads,active_profile=profile.filter(pl.col('row_id')==rid).to_dicts(),saved_training=note['heads'],
                peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number','draft_college','scout_rank_score_0','binary_scout_rate','learned_reliability_rate','binary_scout_pa','learned_reliability_value','next_pa','next_batting_rate','next_value','distance').to_dicts()))
    e.write('cases.json',cases);e.write('verification.json',dict(saved_heads_replayed=replay,old_columns_exact=True,workload_exact=True,event_probabilities_coherent=True,
        source_hashes_exact=True,player_walkthrough_status='pending',case_count=len(cases),protected_outcomes_used=False,frozen_forecast_changed=False))
    for s in scores[:9]:print(s['scope'],{a:(round(s['rate_scores'][a]['rmse'],5),round(s['scores'][a]['value_rmse'],5)) for a in pre['arms']+['binary_scout']},flush=True)
    print('Actual cases prepared:',len(cases),'disposition pending.',flush=True)


if __name__=='__main__':main()
