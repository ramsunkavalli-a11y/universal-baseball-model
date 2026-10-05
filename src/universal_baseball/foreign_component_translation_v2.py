"""Additive repair: calibrate on the same observed history pool used at prediction."""
from collections import Counter, defaultdict

import numpy as np
from scipy.optimize import lsq_linear

from .foreign_component_translation import EVENTS, LEAGUES, RIDGE, clr, events, probability, training_pairs


def histories(rows):
    lookup=defaultdict(lambda:np.zeros(8))
    for r in rows:
        if r['league'] in LEAGUES and r['player_id'] is not None and r['season']<=2024:
            lookup[r['player_id'],r['league'],r['season']]+=events(r)
    return dict(lookup)


def pooled_source(pid,league,origin,history,references,excluded):
    own=np.zeros(8); env=np.zeros(8); exposure=0.; raw_pa=0.; years=[]
    for lag,weight in enumerate([5.,4.,3.]):
        year=origin-lag; c=history.get((pid,league,year))
        if c is None or c.sum()<=0: continue
        n=weight*c.sum(); exposure+=n; raw_pa+=c.sum(); years.append(year)
        own+=n*probability(c); env+=n*references.get(league,year,excluded)
    if not exposure: raise ValueError('Calibration source history missing')
    own/=exposure; env/=exposure
    return clr(own)-clr(env),dict(observed_source_pa=raw_pa,recency_weighted_exposure=exposure,
        observed_source_years=sorted(years),pooled_probability=own.tolist(),pooled_reference=env.tolist())


def fit(pairs,references,cutoff,excluded,history):
    excluded=sorted(set(excluded)); selected=training_pairs(pairs,cutoff,excluded)
    repetitions=Counter(p['player_id'] for p in selected)
    weights=[]; xs=[]; ys=[]; source_notes=[]
    for p in selected:
        c=history.get((p['player_id'],p['a'],p['from_year']))
        if c is None or not np.array_equal(c,events(p['from_counts'])):
            raise ValueError('Primary source season differs from original pair')
        x,note=pooled_source(p['player_id'],p['a'],p['from_year'],history,references,excluded)
        assert max(note['observed_source_years'])<=p['from_year']<p['through_year']<=cutoff
        y=clr(probability(events(p['to_counts'])))-clr(references.get('MLB',p['through_year'],excluded))
        harmonic=2/(1/p['from_pa']+1/p['to_pa'])
        weights.append(min(harmonic/300,1)/repetitions[p['player_id']]); xs.append(x); ys.append(y); source_notes.append(note)
    x=np.asarray(xs).reshape((-1,8)); y=np.asarray(ys).reshape((-1,8)); w=np.asarray(weights)
    coef=np.zeros((8,3)); gradients=[]
    for j in range(8):
        d=np.array([[float(p['a']=='NPB'),float(p['a']=='KBO'),x[i,j]] for i,p in enumerate(selected)]).reshape((-1,3))
        a=np.vstack([d*np.sqrt(w)[:,None],np.eye(3)*np.sqrt(RIDGE)])
        b=np.r_[y[:,j]*np.sqrt(w),np.zeros(3)]
        fit_result=lsq_linear(a,b,bounds=([-np.inf,-np.inf,0],[np.inf,np.inf,2]),tol=1e-12,max_iter=200)
        if not fit_result.success: raise ValueError('Repaired translation optimizer failed')
        coef[j]=fit_result.x; g=a.T@(a@fit_result.x-b); gradients.append(g.tolist())
        assert np.max(np.abs(g[:2]))<1e-7
        s=coef[j,2]
        assert (g[2]>=-1e-7 if s<1e-6 else g[2]<=1e-7 if s>2-1e-6 else abs(g[2])<1e-7)
    return dict(cutoff=cutoff,excluded_folds=excluded,coefficients=coef.tolist(),people=len(repetitions),
        people_by_league={l:len({p['player_id'] for p in selected if p['a']==l}) for l in LEAGUES},
        max_target_year=max((p['through_year'] for p in selected),default=None),
        pairs=[dict(player_id=p['player_id'],league=p['a'],from_year=p['from_year'],target_year=p['through_year'],
             weight=weights[i],source_relative_clr=x[i].tolist(),target_relative_clr=y[i].tolist(),
             source_history=source_notes[i]) for i,p in enumerate(selected)],optimizer_gradients=gradients,
        slope_lower_bound_events=[EVENTS[j] for j in range(8) if coef[j,2]<1e-6],
        slope_upper_bound_events=[EVENTS[j] for j in range(8) if coef[j,2]>2-1e-6],
        calibration_history_matches_prediction=True,park_neutral=False,unbiased_league_strength=False)
