"""Independent replay, conditional/component/value scores and concrete cases."""
from pathlib import Path
import joblib
import numpy as np
import polars as pl
from threadpoolctl import threadpool_limits
import evaluate_mlb_event_logit as e
from score_practical_hitter_v31 import paired,rate_score
from universal_baseball.practical_hitter_v30 import score
from universal_baseball.mlb_event_logit import EVENTS,VALUES,probabilities,batting_rate
from universal_baseball.storage import sha256_file


def rate_interval(frame):
    g=frame.filter(pl.col('next_pa')>0)
    error=((g['event_rate']-g['next_batting_rate'])**2-(g['cohort_rate']-g['next_batting_rate'])**2).to_numpy()
    _,ids=np.unique(g['player_id'],return_inverse=True);_,years=np.unique(g['target_year'],return_inverse=True)
    n=np.zeros((ids.max()+1,years.max()+1));d=np.zeros_like(n);w=g['next_pa'].to_numpy()
    np.add.at(n,(ids,years),w*error);np.add.at(d,(ids,years),w)
    rng=np.random.default_rng(36);draw=[]
    for _ in range(1000):
        z=np.bincount(rng.integers(0,len(n),len(n)),minlength=len(n));den=z@d
        if (den>0).all():draw.append(float(np.mean((z@n)/den)))
    return dict(metric='actual_PA_weighted_conditional_rate_mse',difference=float(np.mean(n.sum(0)/d.sum(0))),
        lower=float(np.quantile(draw,.025)),upper=float(np.quantile(draw,.975)),repeats=1000,nominal_development_interval=True)


def components(g,source):
    ids=g['row_id'].to_list();raw=source.filter(pl.col('row_id').is_in(ids)).sort('row_id');g=g.sort('row_id')
    assert raw['row_id'].equals(g['row_id'])
    active=g['next_pa'].to_numpy()>0;p=g.select([f'event_p_{ev}' for ev in EVENTS]).to_numpy()[active]
    c=raw.select([f'count_{ev}' for ev in EVENTS]).to_numpy()[active];null=raw.select([f'origin_env_{ev}' for ev in EVENTS]).to_numpy()[active]
    pa=c.sum(1);year=g['target_year'].to_numpy()[active];loss=[]
    for y in np.unique(year):
        z=year==y;loss.append([-float(np.sum(c[z]*np.log(np.clip(p[z],1e-15,1)))/pa[z].sum()),
            -float(np.sum(c[z]*np.log(np.clip(null[z],1e-15,1)))/pa[z].sum())])
    return dict(equal_year_PA_count_log_loss=float(np.mean(loss,axis=0)[0]),
        origin_environment_only_log_loss=float(np.mean(loss,axis=0)[1]),
        calibration_with_actual_PA={ev:dict(expected=float((p[:,i]*pa).sum()),actual=float(c[:,i].sum())) for i,ev in enumerate(EVENTS)},
        interpretation='Conditional MLB event diagnostics use observed target PA, not forecast workload or arrival accuracy.')


def main():
    pre=e.old.r.read(e.OUT/'preflight.json');f=pl.read_parquet(e.OUT/'predictions.parquet');source=pl.read_parquet(e.OUT/'features.parquet')
    base=pl.read_parquet(e.old.OUT/'predictions.parquet').sort('row_id')
    for p,h in pre['input_hashes'].items():assert sha256_file(Path(p))==h,p
    assert f.select(base.columns).equals(base);assert f['event_pa'].equals(f['cohort_pa']);replay=0
    with threadpool_limits(limits=2):
        for c in pre['cells']:
            y,k=c['year'],c['fold'];n=e.old.r.read(e.OUT/f'fits-{y}-{k}.json')
            assert sha256_file(Path(n['path']))==n['sha256'];model=joblib.load(n['path'])
            tr=source.filter(pl.col('row_id').is_in(c['training_row_ids']));te=source.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            q=f.filter(pl.col('row_id').is_in(c['test_row_ids'])).sort('player_id')
            assert not set(tr['player_id']) & set(te['player_id'])
            assert tr['target_year'].max()<=y and (tr['target_year']!=2020).all()
            assert q.select('row_id','next_pa','next_value').equals(te.select('row_id','next_pa','next_value'))
            env=te.select([f'origin_env_{ev}' for ev in EVENTS]).to_numpy()
            p=probabilities(model['beta'],e.s.safe_matrix(te,pre['features']),env)
            assert np.allclose(p,q.select([f'event_p_{ev}' for ev in EVENTS]),rtol=0,atol=1e-12)
            assert np.allclose(batting_rate(p,env),q['event_rate'],rtol=0,atol=1e-10);replay+=1
    assert np.allclose(f['event_value'],f['event_pa']*(f['event_rate']/600+f['origin_replacement_rate']),rtol=0,atol=1e-10)
    public=f.filter(pl.col('v24_pa').is_not_null()&(pl.col('pa_0')>0)&pl.col('steamer_pa').is_not_null()&pl.col('zips_rate').is_not_null());assert len(public)==1789
    scopes=[('all',f,['cohort','safe_ridge']),('v24_matched',f.filter(pl.col('v24_pa').is_not_null()),['cohort','safe_ridge','v24']),
        ('legacy_n_matched',f.filter(pl.col('legacy_n_pa').is_not_null()),['cohort','legacy_n']),('public_active',public,['cohort','safe_ridge','steamer'])]
    scopes.extend(('origin_'+str(y),f.filter(pl.col('origin_year')==y),['cohort']) for y in e.old.r.YEARS)
    scopes.extend(('stage_'+stage,f.filter(pl.col('stage')==stage),['cohort']) for stage in sorted(f['stage'].unique()))
    for name,cond in [('current_absent',pl.col('pa_0')==0),('current_partial',pl.col('pa_0').is_between(1,399)),
        ('current_regular',pl.col('pa_0')>=400),('brief_debut',pl.col('pa_0').is_between(1,199)&(pl.col('career_mlb_observed_pa')<300)),
        ('thin_entry',pl.col('recent_all_pa')<100)]:scopes.append((name,f.filter(cond),['cohort']))
    scores=[];intervals=[]
    for name,g,refs in scopes:
        scores.append(dict(scope=name,rows=len(g),players=g['player_id'].n_unique(),actual_pa=float(g['next_pa'].sum()),actual_value=float(g['next_value'].sum()),
            scores={a:score(g,a) for a in ['event']+refs},rate_scores={a:rate_score(g,a+'_rate') for a in ['event','cohort']+(['steamer','zips'] if name=='public_active' else [])},
            components=components(g,source)))
        if name in ['all','v24_matched','legacy_n_matched','public_active','brief_debut']:
            intervals.append(dict(scope=name,**paired(g,'event','cohort','value')))
            intervals.append(dict(scope=name,**rate_interval(g)))
    e.write('scores.json',scores);e.write('intervals.json',intervals)
    e.write('verification.json',dict(saved_heads_replayed=replay,baseline_fields_bit_exact=True,workload_unchanged=True,
        source_hashes_unchanged=True,all_training_membership_checked=True,protected_outcomes_used=False,
        player_walkthrough_status='pending',predictive_certification=False))
    for g in scores[:4]:print(g['scope'],g['rows'],{a:(round(v['pa_rmse'],3),round(v['value_rmse'],5)) for a,v in g['scores'].items()},g['rate_scores'],flush=True)
    fixed=[(643446,2018),(668715,2022),(691026,2023),(701762,2024),(592450,2016),(592450,2024),
        (621566,2022),(666158,2023),(680574,2024),(665487,2022)];selected={}
    for pid,y in fixed:
        q=f.filter((pl.col('player_id')==pid)&(pl.col('origin_year')==y));assert len(q)==1
        selected[q['row_id'][0]]=['Predeclared diagnostic']
    q=f.with_columns(((pl.col('cohort_value')-pl.col('next_value'))**2-(pl.col('event_value')-pl.col('next_value'))**2).alias('gain'),
        (pl.col('event_value')-pl.col('next_value')).alias('error'))
    for label,g in [('largest gain',q.sort('gain',descending=True)),('largest harm',q.sort('gain')),
        ('false high',q.sort('error',descending=True)),('false low',q.sort('error')),
        ('ordinary',q.filter(pl.col('next_pa').is_between(200,600)).sort(pl.col('error').abs()))]:selected.setdefault(g['row_id'][0],[]).append(label)
    raw=pl.read_parquet(e.old.r.OUT/'counts.parquet');cases=[];cols=pre['features']
    for rid,selection in selected.items():
        o=f.filter(pl.col('row_id')==rid).to_dicts()[0];row=source.filter(pl.col('row_id')==rid);v=row.to_dicts()[0]
        n=e.old.r.read(e.OUT/f"fits-{o['origin_year']}-{o['outer_fold']}.json");model=joblib.load(n['path'])
        x=np.r_[1.,e.s.safe_matrix(row,cols)[0]];z=x@model['beta'];assert len(z)==7
        contributions=x[:,None]*model['beta'];idx=np.argsort(-np.max(abs(contributions),axis=1))[:12]
        peers=f.filter((pl.col('origin_year')==o['origin_year'])&(pl.col('player_id')!=o['player_id'])&(pl.col('stage')==o['stage'])&(pl.col('prior_debut')==o['prior_debut']))
        distance=sum(((pl.col(c)-o[c])/scale)**2 for c,scale in [('age',5),('pa_0',200),('AAA_0_pa',200),('AA_0_pa',200),('pooled_mlb_quality',1),('draft_rank',.25),('draft_known',1),('draft_college',1)])
        peers=peers.with_columns(distance.alias('distance')).sort('distance','player_id').head(3)
        cases.append(dict(origin=o,selection=selection,actual_features={c:v[c] for c in cols},saved_fit=n,
            source_history=raw.filter((pl.col('player_id')==o['player_id'])&pl.col('season').is_between(o['origin_year']-2,o['origin_year'])).sort('season','bucket').to_dicts(),
            events=[dict(event=ev,predicted=o['event_p_'+ev],origin_environment=v['origin_env_'+ev],
                actual_target_count=v['count_'+ev],linear_odds_effect=0. if i==0 else float(z[i-1]),
                batting_wins_per600_contribution=float((o['event_p_'+ev]-v['origin_env_'+ev])*VALUES[i]*600/__import__('universal_baseball.mlb_event_logit',fromlist=['NEUTRAL_WOBA_SCALE']).NEUTRAL_WOBA_SCALE/10)) for i,ev in enumerate(EVENTS)],
            top_log_odds_terms=[dict(feature='intercept' if i==0 else cols[i-1],fixed_scaled=float(x[i]),
                effects={ev:float(contributions[i,j]) for j,ev in enumerate(EVENTS[1:])}) for i in idx],
            peers=peers.select('player_id','player_name','age','pa_0','AAA_0_pa','AA_0_pa','draft_known','pick_number','draft_school_class','next_pa','next_value','distance').to_dicts()))
    e.write('cases.json',cases);print('Prepared',len(cases),'case reviews.',flush=True)


if __name__=='__main__':main()
