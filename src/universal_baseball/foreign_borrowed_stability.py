"""Borrow domestic conditional persistence; learn foreign offsets separately."""
from collections import Counter,defaultdict

import numpy as np

from .foreign_component_translation import EVENTS, LEAGUES, clr, events, probability, training_pairs
from .foreign_component_translation_v2 import pooled_source
from .foreign_mover_support import HITTER_CODES
from .post_arrival_history import player_fold


def domestic_pairs(rows):
    annual=defaultdict(lambda:np.zeros(8));roles=defaultdict(set);ages=defaultdict(list)
    for r in rows:
        if r['league']!='MLB' or r['season']>2024:continue
        key=r['player_id'],r['season'];annual[key]+=events(r)
        if r['pa']>0:
            roles[key].add(r['position']);ages[key].append((r['reported_age'],r['pa']))
    result=[]
    for (pid,year),c in sorted(annual.items()):
        target=annual.get((pid,year+1))
        if c.sum()<30 or target is None or target.sum()<30 or not (roles[pid,year]&HITTER_CODES):continue
        if year==2020 or year+1==2020:continue
        history=[dict(season=year-lag,recency=5-lag,counts=annual[pid,year-lag].tolist())
                 for lag in range(3) if (pid,year-lag) in annual and annual[pid,year-lag].sum()>0]
        age=sum(a*n for a,n in ages[pid,year])/sum(n for a,n in ages[pid,year])
        result.append(dict(player_id=pid,fold=player_fold(pid),source_year=year,target_year=year+1,
            source_counts=c.tolist(),target_counts=target.tolist(),history=history,source_age=age,
            source_positions=sorted(roles[pid,year]),source_pa=float(c.sum()),target_pa=float(target.sum()),
            source_k_rate=float(c[1]/c.sum()),source_hr_rate=float(c[7]/c.sum())))
    return result


def source_coordinates(pair,references,excluded):
    own=np.zeros(8);env=np.zeros(8);n=0.
    for s in pair['history']:
        if s['season']>pair['source_year'] or s['season']<pair['source_year']-2:
            raise ValueError('Future or out of window calibration history')
        c=np.array(s['counts']);mass=s['recency']*c.sum()
        own+=mass*probability(c);env+=mass*references.get('MLB',s['season'],excluded);n+=mass
    if not n:raise ValueError('Missing domestic calibration history')
    return clr(own/n)-clr(env/n)


def solve_stability(x,y,weights):
    x=np.asarray(x).reshape((-1,8));y=np.asarray(y).reshape((-1,8));w=np.asarray(weights)
    if not len(w) or len(w)!=len(x) or len(x)!=len(y) or (w<=0).any():
        raise ValueError('Missing or invalid domestic calibration support')
    if not np.isfinite(x).all() or not np.isfinite(y).all() or not np.isfinite(w).all():raise ValueError('Nonfinite calibration')
    s0=w.sum()+2; sx=(w[:,None]*x).sum(0);sy=(w[:,None]*y).sum(0)
    sxx=(w[:,None]*x*x).sum(0)+2;sxy=(w[:,None]*x*y).sum(0)
    b=np.clip((sxy-sx*sy/s0)/(sxx-sx*sx/s0),0,2);a=(sy-sx*b)/s0
    return a,b


def fit(domestic,pairs,history,references,cutoff,excluded,coordinate_cache=None):
    excluded=sorted(set(excluded))
    selected=[p for p in domestic if p['target_year']<=cutoff and p['fold'] not in excluded]
    if any(p['target_year']!=p['source_year']+1 or p['fold']!=player_fold(p['player_id']) for p in selected):
        raise ValueError('Bad domestic chronology or player fold')
    reps=Counter(p['player_id'] for p in selected)
    coordinate_cache={} if coordinate_cache is None else coordinate_cache
    xs=[]
    for p in selected:
        key=p['player_id'],p['source_year'],tuple(excluded)
        if key not in coordinate_cache:coordinate_cache[key]=source_coordinates(p,references,excluded)
        xs.append(coordinate_cache[key])
    x=np.array(xs).reshape((-1,8))
    y=np.array([clr(probability(np.array(p['target_counts'])))-clr(references.get('MLB',p['target_year'],excluded)) for p in selected]).reshape((-1,8))
    w=np.array([min(2*p['source_pa']*p['target_pa']/(p['source_pa']+p['target_pa'])/300,1)/reps[p['player_id']] for p in selected])
    a,b=solve_stability(x,y,w)
    gradients=[]
    for j in range(8):
        d=np.c_[np.ones(len(x)),x[:,j]];c=np.array([a[j],b[j]])
        g=d.T@(w*(d@c-y[:,j]))+2*c
        assert abs(g[0])<1e-7 and (g[1]>=-1e-7 if b[j]<1e-8 else g[1]<=1e-7 if b[j]>2-1e-8 else abs(g[1])<1e-7)
        gradients.append(g.tolist())
    movers=training_pairs(pairs,cutoff,excluded);mreps=Counter(p['player_id'] for p in movers)
    foreign=[];offset={};coefs=np.zeros((8,3));coefs[:,2]=b
    for p in movers:
        if not np.array_equal(history[p['player_id'],p['a'],p['from_year']],events(p['from_counts'])):
            raise ValueError('Foreign primary history mismatch')
        z,note=pooled_source(p['player_id'],p['a'],p['from_year'],history,references,excluded)
        t=clr(probability(events(p['to_counts'])))-clr(references.get('MLB',p['through_year'],excluded))
        weight=min(2*p['from_pa']*p['to_pa']/(p['from_pa']+p['to_pa'])/300,1)/mreps[p['player_id']]
        foreign.append(dict(player_id=p['player_id'],league=p['a'],from_year=p['from_year'],target_year=p['through_year'],
            weight=weight,source_relative_clr=z.tolist(),target_relative_clr=t.tolist(),source_history=note,
            offset_residual=(t-a-b*z).tolist()))
    for k,l in enumerate(LEAGUES):
        group=[p for p in foreign if p['league']==l]
        d=sum((p['weight']*np.array(p['offset_residual']) for p in group),np.zeros(8))/(sum(p['weight'] for p in group)+2)
        offset[l]=d.tolist();coefs[:,k]=a+d
    groups=defaultdict(list)
    for p in selected:
        key=('under25' if p['source_age']<25 else '25to29' if p['source_age']<30 else '30to34' if p['source_age']<35 else '35plus',
            '30to99' if p['source_pa']<100 else '100to299' if p['source_pa']<300 else '300plus',
            'lowK' if p['source_k_rate']<.15 else 'middleK' if p['source_k_rate']<.25 else 'highK',
            'highHR' if p['source_hr_rate']>=.04 else 'lowerHR')
        groups[key].append(p['player_id'])
    support=[dict(age_band=k[0],exposure=k[1],contact=k[2],power=k[3],people=len(set(ids)),pairs=len(ids))
             for k,ids in sorted(groups.items())]
    return dict(cutoff=cutoff,excluded_folds=excluded,coefficients=coefs.tolist(),
        domestic_intercepts=a.tolist(),domestic_slopes=b.tolist(),foreign_offsets=offset,
        people_by_league={l:len({p['player_id'] for p in movers if p['a']==l}) for l in LEAGUES},
        foreign_pairs=foreign,domestic_people=len(reps),domestic_pairs=len(selected),
        domestic_keys=[[p['player_id'],p['source_year']] for p in selected],domestic_weight_sum=float(w.sum()),
        domestic_x_min=x.min(0).tolist(),domestic_x_max=x.max(0).tolist(),domestic_profile_support=support,
        domestic_gradients=gradients,max_target_year=max(p['target_year'] for p in selected),
        slope_lower_bound_events=[EVENTS[j] for j in range(8) if b[j]<1e-8],
        slope_upper_bound_events=[EVENTS[j] for j in range(8) if b[j]>2-1e-8],
        foreign_stability_portability_assumption=True,park_neutral=False,unbiased_league_strength=False)
