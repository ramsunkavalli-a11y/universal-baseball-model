"""Center observed OF evidence before an unchanged fixed reliability prior."""
from collections import defaultdict
import math

OUTFIELD=(7,8,9)


def annual_references(records):
    """All qualified exposure for each held-person reference group."""
    sums=defaultdict(lambda:[0.,0.,set()])
    for r in records:
        if not r['range_valid'] or r['position'] not in OUTFIELD:continue
        assert r['native_outs']>0 and r['range_runs'] is not None and math.isfinite(r['range_runs'])
        for fold in range(5):
            if r['player_id']%5==fold:continue
            v=sums[r['season'],r['position'],fold]
            v[0]+=r['range_runs'];v[1]+=r['native_outs'];v[2].add(r['player_id'])
    return {k:dict(runs=v[0],outs=v[1],people=len(v[2]),rate=1500*v[0]/v[1]) for k,v in sums.items()}


def history(records, origin, position, fold, references):
    past=[];weighted_outs=raw=centered=0.
    for r in records:
        if not (origin-2<=r['season']<=origin and r['position']==position and r['range_valid']):continue
        n=r['native_outs'];v=r['range_runs'];w=2.**(r['season']-origin)
        ref=references[r['season'],position,fold]['rate'] if position in OUTFIELD else 0.
        weighted_outs+=w*n;raw+=w*v;centered+=w*(v-ref*n/1500.)
        past.append(dict(season=r['season'],player_id=r['player_id'],position=position,
            native_outs=n,raw_runs=v,reference_rate=ref,relative_runs=v-ref*n/1500.,
            weight=w,weighted_outs=w*n,weighted_raw_runs=w*v,weighted_relative_runs=w*(v-ref*n/1500.)))
    rate=1500*centered/(weighted_outs+3000.)
    return dict(history_outs=weighted_outs,weighted_raw_runs=raw,weighted_relative_runs=centered,
                legacy_raw=1500*raw/(weighted_outs+3000.),centered=rate,
                reliability=weighted_outs/(weighted_outs+3000.),
                talent_known=weighted_outs>0,prior_relative_mean=0.,history_sources=past)


def origin_reference(origin, position, fold, references):
    if position not in OUTFIELD:return 0.
    rows=[(2.**(y-origin),references[y,position,fold]) for y in range(origin-2,origin+1)
          if (y,position,fold) in references]
    assert rows,'Missing reference must not become zero'
    return 1500*sum(w*r['runs'] for w,r in rows)/sum(w*r['outs'] for w,r in rows)


def measured_quality(records, origin, position, references):
    assert position in OUTFIELD
    rows=[r for r in records if origin<r['season']<=origin+3 and r['position']==position and r['range_valid']]
    n=sum(r['native_outs'] for r in rows)
    if n==0:return None
    return 1500*sum(r['range_runs']-references[r['season'],position]*r['native_outs']/1500 for r in rows)/n
