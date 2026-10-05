"""Append held-fold calculation checks and player traces; never fit or rescore."""
from collections import Counter
import json
import numpy as np
import polars as pl

from run_foreign_count_calibration import ROOT, GEN, OUT, PRIOR, read, save, verify, loaded
from universal_baseball.foreign_count_review import pooled_coordinate, loss_gradient, kkt_residual, peer_distance
from universal_baseball.foreign_component_translation import EVENTS, training_pairs, events
from universal_baseball.hitter_compatible_value import UNIT
from universal_baseball.mlb_event_logit import VALUES
from universal_baseball.storage import sha256_file


def equal(a,b):
    if not np.allclose(a,b,atol=1e-8,rtol=0):
        raise ValueError('Independent arithmetic disagrees')


def check_optimum(theta,x,target,env,w,expected,fixed=None):
    loss,g=loss_gradient(theta,x,target,env,w,fixed)
    equal(loss,expected['objective']); equal(g,expected['gradient'])
    equal(sum(w),expected['effective_PA'])
    ratio=kkt_residual(theta,g,fixed is None)/sum(w)
    if ratio>1e-7: raise ValueError('Nonstationary saved optimum')
    # Check every parameter numerically on the actual retained data, not mocks.
    errors=[]
    for j in range(len(theta)):
        h=np.zeros(len(theta)); h[j]=1e-5
        numeric=(loss_gradient(theta+h,x,target,env,w,fixed)[0]-loss_gradient(theta-h,x,target,env,w,fixed)[0])/2e-5
        errors.append(abs(numeric-g[j])/sum(w))
    if max(errors)>1e-8: raise ValueError('Saved-data numerical gradient failed')
    return dict(projected_gradient_per_PA=ratio,numerical_gradient_error_per_PA=max(errors),parameters=len(theta))


def main():
    if (OUT/'calculation-review.json').exists() or (OUT/'player-walks.json').exists():
        raise ValueError('Existing review; inspect rather than overwrite')
    pre=read(OUT/'preflight.json'); scores=read(OUT/'scores.json')
    verify(pre['source_hashes']); verify(scores['hashes']); verify(read(OUT/'fit-report.json')['hashes'])
    domestic, refs, history, pairs, source=loaded()
    checks=[]; models={}; cache={}
    for cell in pre['cells']:
        y,k=cell['origin'],cell['fold']; m=read(OUT/f'fit-{y}-{k}.json'); models[m['fit_key']]=m
        selected=[p for p in domestic if p['target_year']<=y and p['fold']!=k]
        if [[p['player_id'],p['source_year']] for p in selected]!=m['domestic_keys']:
            raise ValueError('Calibration membership changed')
        reps=Counter(p['player_id'] for p in selected); x=[]
        for p in selected:
            key=p['player_id'],p['source_year'],k
            if key not in cache:
                seasons=[dict(s,reference=refs.get('MLB',s['season'],[k])) for s in p['history']]
                cache[key]=pooled_coordinate(seasons)
            x.append(cache[key])
        x=np.asarray(x)
        t=np.array([np.asarray(p['target_counts'])/p['target_pa'] for p in selected])
        env=np.array([refs.get('MLB',p['target_year'],[k]) for p in selected])
        w=np.array([min(300,2*p['source_pa']*p['target_pa']/(p['source_pa']+p['target_pa']))/reps[p['player_id']] for p in selected])
        equal(x.min(0),m['domestic_x_min']); equal(x.max(0),m['domestic_x_max'])
        theta=np.r_[m['domestic_intercepts'],m['domestic_slopes']]
        checked=check_optimum(theta,x,t,env,w,m['domestic_optimum'])
        movers=training_pairs(pairs,y,[k]); reps=Counter(p['player_id'] for p in movers)
        bykey={(p['player_id'],p['a'],p['from_year'],p['through_year']):p for p in movers}
        foreign=[]
        for league in ['NPB','KBO']:
            group=[p for p in m['foreign_pairs'] if p['league']==league]
            if not group:
                if not m['foreign_optima'][league]['unsupported']: raise ValueError('Invented league support')
                continue
            xs=[]; ts=[]; es=[]; ws=[]
            for p in group:
                raw=bykey[p['player_id'],league,p['from_year'],p['target_year']]
                seasons=[]
                for lag in range(3):
                    c=history.get((p['player_id'],league,p['from_year']-lag))
                    if c is not None and sum(c)>0:
                        seasons.append(dict(season=p['from_year']-lag,counts=c,recency=5-lag,reference=refs.get(league,p['from_year']-lag,[k])))
                z=pooled_coordinate(seasons); target=events(raw['to_counts'])/raw['to_pa']
                weight=min(300,2*raw['from_pa']*raw['to_pa']/(raw['from_pa']+raw['to_pa']))/reps[raw['player_id']]
                equal(z,p['source_relative_clr']); equal(target,p['target_frequency']); equal(weight,p['weight'])
                xs.append(z); ts.append(target); es.append(refs.get('MLB',p['target_year'],[k])); ws.append(weight)
            foreign.append(dict(league=league,**check_optimum(np.array(m['foreign_offsets'][league]),np.array(xs),np.array(ts),np.array(es),np.array(ws),m['foreign_optima'][league],fixed=np.array([m['domestic_intercepts'],m['domestic_slopes']]))))
        checks.append(dict(fit_key=m['fit_key'],domestic=checked,foreign=foreign))
        print(f'Checked saved calibration {y}/{k}',flush=True)
    save('calculation-review.json',dict(cells=checks,independent_saved_data_gradients=True,no_new_fits=True,
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [ROOT/'scripts/review_foreign_count_calibration.py',ROOT/'src/universal_baseball/foreign_count_review.py']}))

    q=pl.read_parquet(OUT/'predictions.parquet'); rows={r['row_id']:r for r in q.to_dicts()}
    profiles={(p['candidate_key'],p['outer_fold']):p for p in read(OUT/'profiles.json')['profiles']}
    old={(p['candidate_key'],p['outer_fold']):p for p in read(PRIOR/'profiles.json')['profiles']}
    annual=pl.read_parquet(GEN/'practical-hitter-v31/counts.parquet')
    fixed=[(2016,519346),(2017,660271),(2021,673548),(2022,807799),(2023,808982),(2024,808975),(2022,592656)]
    reasons={}
    def add(r,reason): reasons.setdefault(r['row_id'],[]).append(reason)
    for y,pid in fixed:
        g=q.filter((pl.col('origin_year')==y)&(pl.col('player_id')==pid))
        if len(g)!=1: raise ValueError('Fixed case absent or duplicated')
        add(g.row(0,named=True),'predeclared_fixed')
    routed=q.filter(pl.col('route_used'))
    for r in routed.filter(pl.col('next_pa')>0).to_dicts(): add(r,'every_routed_actual_participant')
    ranked=routed.with_columns(((pl.col('candidate_value')-pl.col('actual_relative_value'))**2-(pl.col('baseline_value')-pl.col('actual_relative_value'))**2).alias('change'))
    add(ranked.sort('change').row(0,named=True),'largest_value_gain')
    add(ranked.sort('change',descending=True).row(0,named=True),'largest_value_harm')
    add(routed.sort('candidate_value',descending=True).row(0,named=True),'highest_predicted_value')
    add(routed.sort('candidate_value').row(0,named=True),'lowest_predicted_value')
    add(routed.filter(pl.col('next_pa')==0).sort(['player_id','origin_year']).row(0,named=True),'ordinary_nonarrival_smallest_stable_MLBAM_then_origin')
    add(rows[32412],'second_original_nonarrival_harm')
    for y,pid in [(2024,807799),(2024,808982),(2017,519346),(2018,660271)]:
        g=q.filter((pl.col('origin_year')==y)&(pl.col('player_id')==pid))
        if len(g)==1: add(g.row(0,named=True),'newer_MLB_evidence_unchanged_control')
    pool=[r for r in q.to_dicts() if r['source_present']]
    def known(r):
        s=source[r['profile_key']]
        return dict(age=s['age_at_information_date'],recent_foreign_pa=s['recent_foreign_pa'],prior_debut=r['prior_debut'],positive_MLB_context=s['positive_MLB_context'])
    def trace(r):
        p=profiles[r['profile_key'],r['outer_fold']]; prior=old[r['profile_key'],r['outer_fold']]; m=models[p['fit_key']]
        for piece in p['leagues']:
            equal(pooled_coordinate(piece['observed_seasons']),piece['source_relative_clr'])
        if r['route_used']:
            equal((np.array(p['translated_probability'])-p['MLB_reference'])@VALUES*UNIT,r['candidate_rate'])
        equal(r['fixed_p']*r['fixed_conditional_pa'],r['fixed_pa'])
        equal(r['fixed_pa']*(r['candidate_rate']/600+r['origin_replacement_rate']),r['candidate_value'])
        s=source[r['profile_key']]
        pieces=[]
        for piece in p['leagues']:
            latest=max(piece['observed_seasons'],key=lambda x:x['season']); c=latest['counts']; age=s['age_at_information_date']
            ageband='under25' if age<25 else '25to29' if age<30 else '30to34' if age<35 else '35plus'
            contact='lowK' if c[1]/sum(c)<.15 else 'middleK' if c[1]/sum(c)<.25 else 'highK'
            power='highHR' if c[7]/sum(c)>=.04 else 'lowerHR'
            same=[v for v in m['foreign_pairs'] if v['league']==piece['league'] and ('under25' if v['age']<25 else '25to29' if v['age']<30 else '30to34' if v['age']<35 else '35plus')==ageband and v['contact']==contact and v['power']==power]
            support=dict(age_band=ageband,contact=contact,power=power,distinct_movers_same_profile=len({v['player_id'] for v in same}),
                total_league_movers=piece['mover_people'],coordinate_extrapolation=piece['domestic_coordinate_extrapolation'],age_in_forecast_not_fit=True)
            pieces.append(dict(**piece,foreign_profile_support=support,domestic_intercepts=m['domestic_intercepts'],
                domestic_slopes=m['domestic_slopes'],foreign_offset=m['foreign_offsets'][piece['league']],
                logit_terms=(np.array(m['domestic_slopes'])*piece['source_relative_clr']).tolist()))
        domestic=annual.filter((pl.col('player_id')==r['player_id'])&(pl.col('season')<=r['origin_year'])).sort(['season','bucket'])
        return dict(forecast=r,source_context=s,domestic_annual=domestic.to_dicts(),count_profile=p,
            borrowed_profile=prior,coefficient_trace=pieces,event_value_terms=r['direct_terms'],
            actual_rate_observed=r['next_pa']>0,rate_target_missing_if_no_PA=True,
            park_or_opponent_neutralization=False,new_opportunity_head=False)
    walks=[]
    for rid,why in reasons.items():
        r=rows[rid]; a=known(r)
        peers=[b for b in pool if b['origin_year']==r['origin_year'] and b['player_id']!=r['player_id']]
        peers=sorted(peers,key=lambda b:(peer_distance(a,known(b)),b['player_id']))[:3]
        walks.append(dict(selection_reasons=why,trace=trace(r),peers=[dict(distance=peer_distance(a,known(b)),trace=trace(b)) for b in peers]))
    save('player-walks.json',dict(cases=walks,peer_rule='Same origin; distance age/5 + absolute log1p foreign-PA difference +2 debut mismatch +2 dated-job-hint mismatch; stable MLBAM tie break. No outcomes.',
        mechanical_trace_complete=True,human_review_status='pending',new_fits=0,target_year_maximum=2025))
    print(json.dumps(dict(cases=len(walks),traces=sum(1+len(w['peers']) for w in walks),calibration_cells=len(checks),human_review_status='pending')),flush=True)


if __name__=='__main__': main()
