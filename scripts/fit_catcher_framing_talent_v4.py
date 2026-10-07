"""Fixed native-rate catcher comparison with all preflights before first fit."""
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_catcher_framing_talent_v4 import ROOT,OUT,read,write
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections
from universal_baseball import catcher_framing_talent as talent
from universal_baseball.defense_native_range import paired_interval
from universal_baseball.storage import sha256_file


def group(rows):
    return dict(scores={a:talent.score(rows,a) for a in ('neutral','history','calibrated')},
                history_minus_neutral=paired_interval(rows,'history','neutral'),
                calibrated_minus_history=paired_interval(rows,'calibrated','history'),
                sparse_profile_rows=sum(r['profile_people']<20 for r in rows))


def main():
    protected=protections();audit=read(OUT/'support-review.json');verify(audit['hashes'])
    assert audit['player_walkthrough_status']=='complete' and audit['protections']==protected
    assert not (OUT/'report.json').exists()
    rows=pl.read_parquet(OUT/'labels.parquet').to_dicts()
    assert len(rows)==889
    cells=[];checks=[]
    for origin in sorted({r['origin_year'] for r in rows}):
        for fold in range(5):
            tr=[r for r in rows if r['window_end']<=origin and r['quality_rate'] is not None and r['player_id']%5!=fold]
            te=[r for r in rows if r['origin_year']==origin and r['player_id']%5==fold]
            c=talent.preflight(tr,te,origin,fold);checks.append(c);cells.append((tr,te,c))
    paths=[ROOT/'docs/catcher-framing-talent-v4-contract.md',ROOT/'src/universal_baseball/catcher_framing_talent.py',Path(__file__),OUT/'labels.parquet',OUT/'support-review.json']
    write('fit-preflight.json',dict(before_fitting=True,checks=checks,protections=protected,hashes={str(p):sha256_file(p) for p in paths}))
    forecasts=[];models=[]
    for tr,te,c in cells:
        m=talent.fit(tr) if c['fit_allowed'] else None
        pred=talent.predict(m,te) if m else np.array([r['history_rate'] for r in te])
        outside=((talent.matrix(te)<talent.matrix(tr).min(0))|(talent.matrix(te)>talent.matrix(tr).max(0))).sum(1) if m else [None]*len(te)
        models.append(dict(origin=c['origin'],fold=c['fold'],model=m))
        for r,p,n,e in zip(te,pred,c['profile_counts'],outside):
            forecasts.append({**r,'fold':c['fold'],'neutral':0.,'history':r['history_rate'],'calibrated':float(p),
                              'profile_people':n,'fit_allowed':c['fit_allowed'],'features_outside_training_range':int(e) if e is not None else None})
    assert len(forecasts)==len(rows)
    pl.DataFrame(forecasts,infer_schema_length=None).write_parquet(OUT/'predictions.parquet')
    write('models.json',dict(models=models))
    measured=[r for r in forecasts if r['quality_rate'] is not None]
    primary=[r for r in measured if r['origin_year']==2022]
    result=dict(player_walkthrough_status='pending',disposition='provisional',primary=group(primary),
                by_origin={str(y):group([r for r in measured if r['origin_year']==y]) for y in sorted({r['origin_year'] for r in measured})},
                by_profile={},all_predicted_origins=len(forecasts),protections=protected,full_value_forecast=False,deployment_approved=False,
                hashes={str(p):sha256_file(p) for p in (OUT/'predictions.parquet',OUT/'models.json',OUT/'fit-preflight.json')})
    for fn,prop in [('age',lambda r:talent.profile(r)[0]),('history_pitches',lambda r:talent.profile(r)[1])]:
        result['by_profile'][fn]={name:group([r for r in primary if prop(r)==name]) for name in sorted({prop(r) for r in primary})}
    write('report.json',result)
    print(json.dumps(dict(primary=result['primary'],groups=result['by_profile']),indent=2))


if __name__=='__main__':
    main()
