"""Origin-only relative-exposure encoding; no learned/future population means."""
import numpy as np
import polars as pl
from universal_baseball.practical_hitter_v30 import EVENTS


def shared_deviation(n, d, total, prior):
    """One prior shared across competing evidence, not twice-shrunk rates."""
    if d < 0 or total < d or n < 0 or n > d:
        raise ValueError('Invalid event/exposure counts')
    return (n - d * prior) / (total + 100)


def materialize(frame, counts, buckets):
    keys=['player_id','season','bucket']
    if counts.unique(keys).height!=len(counts):raise ValueError('Duplicate count keys')
    if frame['origin_year'].max()>2024:raise ValueError('Protected origins excluded')
    lut={(h['player_id'],h['season'],h['bucket']):h for h in counts.filter(pl.col('season')<=2024).iter_rows(named=True)}
    rows=[]
    for o in frame.iter_rows(named=True):
        row={'row_id':o['row_id']};by={}
        for bucket in buckets:
            history=[(w,lut.get((o['player_id'],o['origin_year']-lag,bucket))) for lag,w in enumerate([1.,.8,.6])]
            by[bucket]={ev:(sum(w*h[num] for w,h in history if h),sum(w*h[den] for w,h in history if h)) for ev,(num,den,_) in EVENTS.items()}
            for ev,(n,d) in by[bucket].items():
                prior=EVENTS[ev][2]
                assert np.isclose(o[f'pooled_{bucket}_{ev}'],(n+100*prior)/(d+100),atol=1e-12)
        for ev,(_,_,prior) in EVENTS.items():
            total=sum(by[b][ev][1] for b in buckets)
            for bucket in buckets:
                n,d=by[bucket][ev];row[f'pooled_{bucket}_{ev}']=prior+shared_deviation(n,d,total,prior)
            assert np.isclose(sum(row[f'pooled_{b}_{ev}']-prior for b in buckets),
                (sum(by[b][ev][0] for b in buckets)-total*prior)/(total+100),atol=1e-12)
        rows.append(row)
    changed=pl.DataFrame(rows);columns=changed.columns[1:]
    out=frame.drop(columns).join(changed,on='row_id',validate='1:1').select(frame.columns)
    assert out.select([c for c in frame.columns if c not in columns]).equals(frame.select([c for c in frame.columns if c not in columns]))
    return out
