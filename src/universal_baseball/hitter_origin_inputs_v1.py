"""Explicit source-year boundary for pooled hitter inputs, never target outcomes.

This duplicates the sealed historical builder's arithmetic deliberately: old
builders and source seals must not change when the production boundary extends.
"""
import numpy as np
import polars as pl

from .hitter_numeric_history import BUCKETS
from .practical_hitter_v30 import EVENTS
from .hitter_talent_bridge import event_counts


def pooled_inputs(frame, counts, draft, *, source_cutoff):
    if not isinstance(source_cutoff,int) or not 2011<=source_cutoff<=2026:
        raise ValueError('Only declared predictor origins through 2026 permitted')
    required=['row_id','origin_year','player_id',*[f'{s}_{k}' for s in ['pa','quality'] for k in range(3)],
              *[f'{b}_{k}_pa' for b in BUCKETS for k in range(3)]]
    if set(required)-set(frame.columns):raise ValueError('Missing origin input fields')
    if frame['origin_year'].max()>source_cutoff or counts['season'].max()>source_cutoff or draft['draft_year'].max()>source_cutoff:
        raise ValueError('Future predictor source; filter explicitly before calling')
    if frame['row_id'].n_unique()!=frame.height or counts.unique(['player_id','season','bucket']).height!=counts.height:
        raise ValueError('Duplicate input identity')
    event_counts(counts)
    d=draft.filter(pl.col('drafted')&(pl.col('pick_number')>0)).select('player_id','draft_year','pick_number','school_class').unique()
    if d.unique(['player_id','draft_year']).height!=d.height:raise ValueError('Conflicting dated draft picks')
    picks={}
    for s in d.sort('draft_year').iter_rows(named=True):picks.setdefault(s['player_id'],[]).append(s)
    lut={(s['player_id'],s['season'],s['bucket']):s for s in counts.iter_rows(named=True)}
    rows=[]
    for o in frame.iter_rows(named=True):
        y,pid=o['origin_year'],o['player_id'];row={'row_id':o['row_id']}
        for bucket in BUCKETS:
            h=[(w,lut.get((pid,y-k,bucket))) for k,w in enumerate([1.,.8,.6])]
            row[f'pooled_{bucket}_pa']=sum(w*s['plate_appearances'] for w,s in h if s)
            for ev,(num,den,prior) in EVENTS.items():
                n=sum(w*s[num] for w,s in h if s);d0=sum(w*s[den] for w,s in h if s)
                row[f'pooled_{bucket}_{ev}']=(n+100*prior)/(d0+100)
        pa=sum(w*o[f'pa_{k}'] for k,w in enumerate([1.,.8,.6]))
        row['pooled_mlb_quality']=sum(w*o[f'quality_{k}']*(o[f'pa_{k}']+1200) for k,w in enumerate([1.,.8,.6]))/(pa+1200)
        eligible=[s for s in picks.get(pid,[]) if s['draft_year']<=y];pick=eligible[-1] if eligible else None
        rank=1-np.log(pick['pick_number'])/np.log(2000) if pick else 0
        school=(pick['school_class'] or '').strip().upper() if pick else ''
        row.update(draft_year=pick['draft_year'] if pick else None,pick_number=pick['pick_number'] if pick else None,
            draft_school_class=school,draft_known=int(pick is not None),draft_rank=float(np.clip(rank,0,1)),
            draft_elapsed=(y-pick['draft_year'])/10 if pick else 0,
            draft_hs=int(school.startswith('HS')),draft_jc=int(school.startswith('JC')),
            draft_college=int(school.startswith('4YR') or school in ['FR','SO','JR','SR']),
            draft_class_unknown=int(not school),draft_rank_low_exposure=float(np.clip(rank,0,1))*100/(100+sum(o[f'{b}_{k}_pa'] for b in BUCKETS for k in range(3))))
        rows.append(row)
    types={name:pl.Float64 for name in rows[0] if name.startswith('pooled_')}
    types.update(draft_year=pl.Int64,pick_number=pl.Int64,draft_elapsed=pl.Float64,
                 draft_rank=pl.Float64,draft_rank_low_exposure=pl.Float64)
    return pl.DataFrame(rows,schema_overrides=types)
