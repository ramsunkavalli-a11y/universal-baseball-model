"""Reconstruct source history, domestic optima, foreign offsets and fixed scores."""
from collections import Counter,defaultdict
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import polars as pl

from prepare_foreign_borrowed_stability import ROOT,OUT,OLD,INPUTS,DOMESTIC,read,save,verify
from prepare_foreign_component_translation import NPB,KBO
from review_foreign_component_translation import independent_counts,prob,logcenter
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.storage import sha256_file


def average(rows,field,weighted=False):
    origins=sorted({r['origin_year'] for r in rows})
    return float(np.mean([np.average([r[field] for r in rows if r['origin_year']==y],
        weights=[r['next_pa'] if weighted else 1 for r in rows if r['origin_year']==y]) for y in origins]))


def score(rows):
    if not rows:return dict(rows=0)
    d=dict(rows=len(rows),people=len({r['player_id'] for r in rows}),actual_pa=sum(r['next_pa'] for r in rows))
    for arm in ['affine','borrowed']:
        d[arm]={loss:average(rows,arm+'_'+loss) for loss in ['logloss','brier']}
        d[arm].update({event+'_rmse':np.sqrt(average(rows,arm+'_'+event+'_sq')) for event in ['K','HR']})
        d[arm]['pa_weighted_logloss']=average(rows,arm+'_logloss',True)
    return d


def save_verified_partial(path,obj):
    # Resume a terminal review failure without overwriting its completed scores.
    if path.exists():
        assert read(path)==obj,'Existing partial review differs from reconstruction'
    else:save(path,obj)


def main():
    assert not (OUT/'independent-review.json').exists(),'Preserve completed review'
    receipt=read(OUT/'fit-receipt.json');verify(receipt['source_hashes']);verify(receipt['artifact_hashes'])
    previous=read(OLD/'fit-receipt.json');verify(previous['artifact_hashes'])
    frame=pl.read_parquet(DOMESTIC).filter((pl.col('season')<=2025)&(pl.col('bucket')=='MLB'))
    all_rows=frame.to_dicts();all_counts=independent_counts(all_rows,True)
    annual=defaultdict(lambda:np.zeros(8));role=defaultdict(set);age=defaultdict(list)
    actual={};totals=defaultdict(lambda:np.zeros(8));byfold=defaultdict(lambda:np.zeros(8));history=defaultdict(lambda:np.zeros(8))
    for r,c in zip(all_rows,all_counts):
        key=r['player_id'],r['season'];annual[key]+=c
        if c.sum()>0:role[key].add(r['position']);age[key].append((r['reported_age'],c.sum()))
        if r['season']<=2024:
            totals['MLB',r['season']]+=c;byfold[('MLB',r['season']),player_fold(r['player_id'])]+=c
    for l,path in [('NPB',NPB),('KBO',KBO)]:
        rows=pl.read_parquet(path).to_dicts();counts=independent_counts(rows)
        for r,c in zip(rows,counts):
            totals[l,r['season']]+=c
            if r['player_id'] is not None:
                byfold[(l,r['season']),player_fold(r['player_id'])]+=c;history[r['player_id'],l,r['season']]+=c
    cache={}
    def ref(l,y,k):
        assert y<=2024
        key=l,y,tuple(k)
        if key not in cache:cache[key]=prob(totals[l,y]-sum((byfold[(l,y),fold] for fold in k),np.zeros(8)))
        return cache[key]
    domestic=read(OUT/'domestic-calibration.json')['pairs'];keys=[]
    hitter_codes={str(x) for x in range(2,11)}|{'O','I','Y'}
    for (pid,y),c in sorted(annual.items()):
        if y>=2024 or y in [2019,2020]:continue
        t=annual.get((pid,y+1))
        if c.sum()<30 or t is None or t.sum()<30 or not (role[pid,y]&hitter_codes):continue
        keys.append([pid,y])
    assert keys==[[p['player_id'],p['source_year']] for p in domestic]
    for p in domestic:
        pid,y=p['player_id'],p['source_year']
        assert np.array_equal(annual[pid,y],p['source_counts']) and np.array_equal(annual[pid,y+1],p['target_counts'])
        assert p['fold']==player_fold(pid) and p['source_positions']==sorted(role[pid,y])
        assert abs(p['source_age']-sum(a*n for a,n in age[pid,y])/sum(n for a,n in age[pid,y]))<1e-12
        expected=[dict(season=y-lag,recency=5-lag,counts=annual[pid,y-lag].tolist()) for lag in range(3) if (pid,y-lag) in annual and annual[pid,y-lag].sum()>0]
        assert expected==p['history']
    xcache={}
    def coordinates(pid,l,y,k):
        key=pid,l,y,tuple(k)
        if key not in xcache:
            own=np.zeros(8);env=np.zeros(8);n=0.
            for lag,w in enumerate([5,4,3]):
                c=annual.get((pid,y-lag)) if l=='MLB' else history.get((pid,l,y-lag))
                if c is None or c.sum()<=0:continue
                mass=w*c.sum();own+=mass*prob(c);env+=mass*ref(l,y-lag,k);n+=mass
            assert n>0
            xcache[key]=logcenter(own/n)-logcenter(env/n)
        return xcache[key]
    models=read(OUT/'fits.json')['fits'];profiles=read(OUT/'profiles.json')['profiles']
    previous_models={m['fit_key']:m for m in read(OLD/'fits.json')['fits']};checked=0
    for m in models:
        y=m['cutoff'];k=m['excluded_folds'];pool=[p for p in domestic if p['target_year']<=y and p['fold'] not in k]
        assert [[p['player_id'],p['source_year']] for p in pool]==m['domestic_keys']
        reps=Counter(p['player_id'] for p in pool)
        assert len(pool)==m['domestic_pairs'] and len(reps)==m['domestic_people']
        x=np.array([coordinates(p['player_id'],'MLB',p['source_year'],k) for p in pool])
        t=np.array([logcenter(prob(np.array(p['target_counts'])))-logcenter(ref('MLB',p['target_year'],k)) for p in pool])
        w=np.array([min(2*p['source_pa']*p['target_pa']/(p['source_pa']+p['target_pa'])/300,1)/reps[p['player_id']] for p in pool])
        assert np.allclose(x.min(0),m['domestic_x_min']) and np.allclose(x.max(0),m['domestic_x_max'])
        for j in range(8):
            c=np.array([m['domestic_intercepts'][j],m['domestic_slopes'][j]])
            d=np.c_[np.ones(len(x)),x[:,j]];g=d.T@(w*(d@c-t[:,j]))+2*c
            assert abs(g[0])<1e-7 and 0<=c[1]<=2
            assert (g[1]>=-1e-7 if c[1]<1e-8 else g[1]<=1e-7 if c[1]>2-1e-8 else abs(g[1])<1e-7)
            checked+=1
        old=previous_models[m['fit_key']]
        assert len(old['pairs'])==len(m['foreign_pairs'])
        for p,q in zip(m['foreign_pairs'],old['pairs']):
            assert all(p[f]==q[f] for f in ['player_id','league','from_year','target_year','source_relative_clr','target_relative_clr','source_history'])
            # Equivalent harmonic formulas can differ by floating-point roundoff.
            assert abs(p['weight']-q['weight'])<1e-12
            residual=np.array(p['target_relative_clr'])-np.array(m['domestic_intercepts'])-np.array(m['domestic_slopes'])*np.array(p['source_relative_clr'])
            assert np.allclose(residual,p['offset_residual'],rtol=0,atol=1e-12)
        for col,l in enumerate(['NPB','KBO']):
            foreign=[p for p in m['foreign_pairs'] if p['league']==l]
            offset=sum((p['weight']*np.array(p['offset_residual']) for p in foreign),np.zeros(8))/(sum(p['weight'] for p in foreign)+2)
            assert np.allclose(offset,m['foreign_offsets'][l],rtol=0,atol=1e-12)
            assert np.allclose(np.array(m['coefficients'])[:,col],np.array(m['domestic_intercepts'])+offset,rtol=0,atol=1e-12)
    mlut={m['fit_key']:m for m in models};prior_profiles={(p['candidate_key'],p['outer_fold']):p for p in read(OLD/'profiles.json')['profiles']}
    for p in profiles:
        old=prior_profiles[p['candidate_key'],p['outer_fold']];m=mlut[p['fit_key']];k=p['excluded_folds']
        assert p['missing_translation']==old['missing_translation'] and k==sorted({p['outer_fold'],player_fold(p['player_id'])})
        weighted=np.zeros(8);n=0.
        for piece,previous_piece in zip(p['leagues'],old['leagues']):
            for f in ['league','recency_weighted_exposure','mover_people','own_pooled_probability','pooled_reference','source_relative_clr','observed_seasons']:assert piece[f]==previous_piece[f]
            if piece['mover_people']:
                l=piece['league'];z=logcenter(ref('MLB',p['origin_year'],k))+np.array(m['domestic_intercepts'])+np.array(m['foreign_offsets'][l])+np.array(m['domestic_slopes'])*np.array(piece['source_relative_clr'])
                q=np.exp(z-z.max());q/=q.sum();mass=piece['recency_weighted_exposure'];n+=mass;weighted+=mass*q
                assert np.allclose(q,piece['translated_probability'],rtol=0,atol=1e-12)
        if n:assert np.allclose(weighted/n,p['translated_probability'],rtol=0,atol=1e-12)
        else:assert p['translated_probability'] is None
    anchor=pl.read_parquet(ROOT/'reports/generated/hitter-minor-statcast-precision/scored-predictions.parquet')
    lookup={(p['player_id'],p['origin_year']):p for p in profiles if p['outer_fold']==player_fold(p['player_id'])}
    scored=[];cohort=[]
    for r in anchor.iter_rows(named=True):
        p=lookup.get((r['player_id'],r['origin_year']))
        if p is None:continue
        c=annual.get((r['player_id'],r['target_year']),np.zeros(8));assert c.sum()==r['next_pa']
        old=prior_profiles[p['candidate_key'],p['outer_fold']]
        record=dict(row_id=r['row_id'],player_id=r['player_id'],player_name=r['player_name'],origin_year=r['origin_year'],next_pa=int(c.sum()),
            source_role='two_way_or_hitter_conflict' if r['source_position'] in ['1','Y'] else 'original_hitter_forecast',
            supported=not p['missing_translation'],borrowed_profile=p,affine_profile=old,
            actual_counts=c.tolist(),actual_probability=(c/c.sum()).tolist() if c.sum()>0 else None,
            unchanged_current_pa=r['preseason_pa'],unchanged_current_batting_rate=r['combined_rate'])
        cohort.append(record)
        if c.sum()==0 or p['missing_translation'] or old['missing_translation']:continue
        observed=c/c.sum()
        for arm,q in [('affine',old['translated_probability']),('borrowed',p['translated_probability'])]:
            q=np.array(q);record[arm+'_logloss']=float(-observed@np.log(q));record[arm+'_brier']=float(1+q@q-2*q@observed)
            for j,e in [(1,'K'),(7,'HR')]:record[arm+'_'+e+'_sq']=float((q[j]-observed[j])**2)
        scored.append(record)
    assert len(cohort)==253
    save_verified_partial(OUT/'scored-component-cohort.json',dict(rows=cohort,fixed_source_forecasts=253,nonarrival_rates_unobserved=True))
    save_verified_partial(OUT/'scores.json',dict(all_supported_active=score(scored),origins=[dict(origin=y,**score([r for r in scored if r['origin_year']==y])) for y in sorted({r['origin_year'] for r in cohort})],
        fixed_cohort_rows=len(cohort),actual_active_rows=sum(r['next_pa']>0 for r in cohort),nonarrival_rows=sum(r['next_pa']==0 for r in cohort),
        unsupported_active_rows=sum(r['next_pa']>0 and not r['supported'] for r in cohort),full_hitter_forecasts_changed=False))
    rng=np.random.default_rng(84);people=sorted({r['player_id'] for r in scored});intervals={}
    for loss in ['logloss','brier','K_sq','HR_sq']:
        differences=[]
        for _ in range(2000):
            counts=Counter(rng.choice(people,len(people),replace=True).tolist());byyear=[]
            for y in sorted({r['origin_year'] for r in scored}):
                rows=[r for r in scored if r['origin_year']==y and counts[r['player_id']]>0]
                if rows:byyear.append(np.average([r['borrowed_'+loss]-r['affine_'+loss] for r in rows],weights=[counts[r['player_id']] for r in rows]))
            differences.append(np.mean(byyear))
        intervals[loss]=dict(delta=average(scored,'borrowed_'+loss)-average(scored,'affine_'+loss),nominal_player_interval=np.quantile(differences,[.025,.975]).tolist(),shared_season_and_selection_uncertainty_not_covered=True)
    save_verified_partial(OUT/'intervals.json',intervals)
    fixed=read(OLD/'reviewed-cases.json')['cases'];cases=[]
    for c in fixed:
        p=lookup.get((c['player_id'],c['origin_year']))
        # Fixed absent-forecast source cases have profiles even though no saved forecast.
        if p is None:p=next((p for p in profiles if p['player_id']==c['player_id'] and p['origin_year']==c['origin_year'] and p['outer_fold']==player_fold(c['player_id'])),None)
        cases.append(dict(c,borrowed_profile=p,borrowed_model=mlut[p['fit_key']] if p else None,
            new_MLB_PA_forecast=None,new_full_value_forecast=None))
    selected_cases={}
    for kind,key,reverse in [('largest_gain',lambda r:r['borrowed_logloss']-r['affine_logloss'],False),
        ('largest_harm',lambda r:r['borrowed_logloss']-r['affine_logloss'],True),
        ('largest_K_false_high',lambda r:r['borrowed_profile']['translated_probability'][1]-r['actual_probability'][1],True),
        ('largest_K_false_low',lambda r:r['borrowed_profile']['translated_probability'][1]-r['actual_probability'][1],False),
        ('ordinary',lambda r:abs(r['borrowed_logloss']-r['affine_logloss']),False)]:
        r=sorted(scored,key=lambda q:(key(q),q['row_id']),reverse=reverse)[0]
        selected_cases[kind]=r
    save(OUT/'reviewed-cases.json',dict(fixed_cases=cases,score_selected_cases=selected_cases,ordinary_unresolved_controls=read(OLD/'reviewed-cases.json')['ordinary_unresolved_controls'],
        player_walkthrough_status='arithmetic_complete_manual_pending'))
    tests=subprocess.run([sys.executable,'-m','pytest','tests/test_foreign_borrowed_stability.py','tests/test_foreign_component_translation.py','tests/test_foreign_component_translation_v2.py','-q','-p','no:cacheprovider'],cwd=ROOT,capture_output=True,text=True)
    assert tests.returncode==0,tests.stdout+tests.stderr
    freeze=subprocess.run([sys.executable,'scripts/verify_hitter_full_2026_freeze.py'],cwd=ROOT,capture_output=True,text=True)
    assert freeze.returncode==0,freeze.stdout+freeze.stderr
    save(OUT/'independent-review.json',dict(status='arithmetic_complete_manual_pending',domestic_source_pairs_reconstructed=len(domestic),
        domestic_optima_checked=checked,foreign_offset_estimates_checked=len(models)*16,profiles_reconstructed=len(profiles),
        fixed_cases=14,score_selected_cases=list(selected_cases),tests=tests.stdout,protected_freeze=json.loads(freeze.stdout),
        hashes={str(p.relative_to(ROOT)):sha256_file(p) for p in [OUT/'preflight.json',OUT/'fits.json',OUT/'profiles.json',OUT/'fit-receipt.json',
        OUT/'scores.json',OUT/'intervals.json',OUT/'scored-component-cohort.json',OUT/'reviewed-cases.json',Path(__file__)]}))
    print(json.dumps(dict(scores=score(scored),intervals=intervals,manual_review='pending')),flush=True)


if __name__=='__main__':main()
