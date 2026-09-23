"""Rare-event level/age benchmark and explicitly linked opportunity/value."""
from __future__ import annotations

import numpy as np
import polars as pl

LEVELS=('AAA','AA','A+','A','A-','RK')


def age_band(age):
    if age is None or not np.isfinite(age): return 'unknown'
    return '<=18' if age<=18 else '19-20' if age<=20 else '21-22' if age<=22 else '23+'


def eligible(frame):
    return (frame['prospect'].to_numpy() & frame['level'].is_in(LEVELS).to_numpy()
            & np.isfinite(frame['age'].to_numpy()))


def cell_probability(train, test, horizon, strength=100.):
    """Fit probabilities from mature training labels only, never held-out rates.

    The caller enforces chronology and optionally player-disjointness. A zero
    event count is evidence of rarity, not certainty of impossible arrival.
    """
    if strength<=0: raise ValueError('Prior strength must be positive')
    data=train.filter(pl.Series(eligible(train)))
    if data[f'pa_h{horizon}'].null_count(): raise ValueError('Unobserved training label')
    levels={}; cells={}
    for r in data.select('level','age',f'pa_h{horizon}').iter_rows(named=True):
        active=int(r[f'pa_h{horizon}']>0); key=(r['level'],age_band(r['age']))
        for mapping,k in ((levels,r['level']),(cells,key)):
            n,s=mapping.get(k,(0,0)); mapping[k]=(n+1,s+active)
    values=[]; supported=[]
    for level,age in test.select('level','age').iter_rows():
        n,s=levels.get(level,(0,0)); band=age_band(age)
        ok=n>0 and band!='unknown'
        cn,cs=cells.get((level,band),(0,0))
        rate=(s+.5)/(n+1)
        values.append((cs+strength*rate)/(cn+strength) if ok else np.nan)
        supported.append(ok)
    notes=[{'level':l,'age_band':a,'n':n,'active':s,'level_n':levels[l][0],
            'level_active':levels[l][1]} for (l,a),(n,s) in sorted(cells.items())]
    return np.asarray(values),np.asarray(supported),notes


def linked_value(probability, conditional_pa, rate):
    p,pa,r=(np.asarray(x,dtype=float) for x in (probability,conditional_pa,rate))
    if not (np.isfinite(p).all() and np.isfinite(pa).all() and np.isfinite(r).all()):
        raise ValueError('Non-finite linked prediction')
    if ((p<0)|(p>1)).any() or ((pa<1)|(pa>750)).any(): raise ValueError('Invalid probability/PA')
    expected=p*pa
    return expected,expected*r/600


def scopes(frame):
    e=eligible(frame)&frame['cell_supported'].to_numpy()
    return {'C1':e,'C2':e&(frame['level'].to_numpy()=='RK')}
