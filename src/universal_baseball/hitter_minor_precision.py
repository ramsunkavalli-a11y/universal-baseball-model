"""Contact noise shrinkage and a bounded minor information-share guard."""
import math
import numpy as np
import polars as pl
from universal_baseball.post_arrival_history import player_fold
from universal_baseball.hitter_minor_statcast_forecast import LEAGUES, best_half

METRICS={'mean_ev':('ev',10.),'best_half_ev':('ev',10.),
         'mean_la':('la',20.),'hard_air_fraction':('pair',1.)}


def variance_components(means, sizes, within_ss=None, noise_variance=None):
    x=np.asarray(means,dtype=float);n=np.asarray(sizes,dtype=float)
    if len(x)<2 or (n<=0).any() or not np.isfinite(x).all(): return None
    total=float(n.sum());j=len(n);mu=float(np.average(x,weights=n))
    if noise_variance is None:
        if total<=j: return None
        noise_variance=float(np.asarray(within_ss,dtype=float).sum()/(total-j))
    effective=float((total-(n@n)/total)/(j-1))
    between_ms=float(np.sum(n*(x-mu)**2)/(j-1))
    tau=max((between_ms-noise_variance)/effective,0.)
    return dict(mean=mu,within_variance=float(noise_variance),between_ms=between_ms,
        effective_group_size=effective,between_variance=tau,
        prior_contacts=float(noise_variance/tau) if tau>0 else None,
        observations=int(total),people=j)


def bootstrap_best_half(values, seed):
    a=np.asarray(values,dtype=float);n=len(a)
    if n<2:return None
    rng=np.random.default_rng(seed)
    samples=a[rng.integers(0,n,size=(128,n))]
    top=math.ceil(n/2);draws=np.partition(samples,n-top,axis=1)[:,n-top:].mean(axis=1)
    return float(np.var(draws,ddof=1))


def moments(annual, ledgers):
    lookup={}
    for ledger in ledgers:
        for g in ledger.partition_by('player_id','season','league_id'):
            pid,season,league=[int(g[n][0]) for n in ['player_id','season','league_id']]
            ev=g.filter(pl.col('valid_ev'))['launch_speed'].to_numpy()
            la=g.filter(pl.col('valid_la'))['launch_angle'].to_numpy()
            pair=g.filter(pl.col('complete_pair'))
            air=pair.select(((pl.col('launch_speed')>=95)&pl.col('launch_angle').is_between(8,50)).cast(pl.Float64)).to_numpy().ravel()
            lookup[pid,season,league]=dict(ev_n=len(ev),la_n=len(la),pair_n=len(air),
                ev_ss=float(np.sum((ev-ev.mean())**2)) if len(ev) else 0.,
                la_ss=float(np.sum((la-la.mean())**2)) if len(la) else 0.,
                pair_ss=float(np.sum((air-air.mean())**2)) if len(air) else 0.,
                bootstrap_best_half_variance=bootstrap_best_half(ev,(pid*17+season*101+league)%2**32),
                checked_mean_ev=float(ev.mean()) if len(ev) else None,
                checked_mean_la=float(la.mean()) if len(la) else None,
                checked_best_half=best_half(ev),checked_hard_air=float(air.mean()) if len(air) else None)
    rows=[]
    for r in annual.iter_rows(named=True):
        z=lookup.get((r['player_id'],r['season'],r['league_id']))
        # Official-source additions with no returned measurement remain missing.
        if z is None:z=dict(ev_n=0,la_n=0,pair_n=0,ev_ss=0.,la_ss=0.,pair_ss=0.,
            bootstrap_best_half_variance=None,checked_mean_ev=None,checked_mean_la=None,checked_best_half=None,checked_hard_air=None)
        for kind in ['ev','la','pair']:assert z[kind+'_n']==r['measured_'+kind+'_contacts']
        for name,check in [('mean_ev','checked_mean_ev'),('mean_la','checked_mean_la'),('best_half_ev','checked_best_half'),('hard_air_fraction','checked_hard_air')]:
            assert (r[name] is None and z[check] is None) or np.isclose(r[name],z[check],atol=1e-10)
        rows.append(dict(**r,**z))
    return pl.DataFrame(rows)


def references(annual, fold):
    a=annual.with_columns(pl.Series('_fold',[player_fold(p) for p in annual['player_id']])).filter(pl.col('_fold')!=fold)
    refs=[]
    for g in a.partition_by('season','league_id'):
        record=dict(season=int(g['season'][0]),league_id=int(g['league_id'][0]),held_fold=fold,metrics={})
        for m,(kind,_) in METRICS.items():
            known=g.filter(pl.col(m).is_not_null()&(pl.col(kind+'_n')>0))
            if m=='best_half_ev':
                known=known.filter((pl.col('ev_n')>=20)&pl.col('bootstrap_best_half_variance').is_not_null())
                noise=float(np.average(known['ev_n']*known['bootstrap_best_half_variance'],weights=known['ev_n'])) if len(known) else None
                stat=variance_components(known[m],known['ev_n'],noise_variance=noise) if len(known) else None
            else:stat=variance_components(known[m],known[kind+'_n'],known[kind+'_ss'])
            record['metrics'][m]=dict(components=stat,reference_ids=sorted(known['player_id'].to_list()))
        refs.append(record)
    return refs


def information_share(n, minor_total, mlb_total, prior_contacts):
    if prior_contacts is None or n<=0:return 0.
    if n>minor_total or min(minor_total,mlb_total,prior_contacts)<0:raise ValueError('Invalid precision exposure')
    return float(n/(minor_total+mlb_total+prior_contacts))


def names():
    control=[f'msp_{l}_{lag}_exposure' for lag in range(3) for l in LEAGUES]
    values=[f'msp_{l}_{lag}_{m}' for lag in range(3) for l in LEAGUES for m in METRICS]
    return control,values


def materialize(f, annual, fold):
    assert annual['season'].max()<=2024 and annual.unique(['player_id','season','league_id']).height==len(annual)
    refs=references(annual,fold);refmap={(r['season'],r['league_id']):r for r in refs}
    lut={(r['player_id'],r['season'],r['league_id']):r for r in annual.iter_rows(named=True)}
    control,values=names();rows=[]
    for o in f.iter_rows(named=True):
        own=[lut.get((o['player_id'],o['origin_year']-lag,l)) for lag in range(3) for l in LEAGUES]
        totals={kind:sum(r[kind+'_n'] for r in own if r) for kind in ['ev','la','pair']}
        mlb=dict(ev=o['sc_own_ev_n'],pair=o['sc_own_pair_n'],
            la=sum(round(np.expm1(o[f'sc_{lag}_la_sample']*np.log(601))) for lag in range(3)))
        z={'row_id':o['row_id']}
        for lag in range(3):
            for league in LEAGUES:
                r=lut.get((o['player_id'],o['origin_year']-lag,league));ref=refmap.get((o['origin_year']-lag,league))
                prefix=f'msp_{league}_{lag}_';shares={}
                for m,(kind,scale) in METRICS.items():
                    stat=ref['metrics'][m]['components'] if ref else None
                    share=information_share(r[kind+'_n'],totals[kind],mlb[kind],stat['prior_contacts']) if r and stat and r[m] is not None else 0.
                    shares[m]=share
                    z[prefix+m]=share*(r[m]-stat['mean'])/scale if share else 0.
                    z[prefix+m+'_share']=share
                z[prefix+'exposure']=shares['mean_ev']
        rows.append(z)
    q=f.join(pl.DataFrame(rows),on='row_id',validate='1:1')
    assert q.select(f.columns).equals(f) and np.isfinite(q.select(control+values).to_numpy()).all()
    return q,refs
