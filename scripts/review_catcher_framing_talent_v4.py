"""Source-to-fitted-calculation walkthrough including small samples and misses."""
from collections import defaultdict
import math

import numpy as np
import polars as pl

from audit_catcher_framing_talent_v4 import ROOT,SOURCE,OUT,FIXED,read,write
from universal_baseball import catcher_framing_talent as talent
from universal_baseball.storage import sha256_file
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections


def main():
    report=read(OUT/'report.json');verify(report['hashes']);assert report['protections']==protections()
    rows=pl.read_parquet(OUT/'predictions.parquet').to_dicts()
    native=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'framing-annual.parquet').to_dicts():
        native[r['player_id']].append(r)
    models={(m['origin'],m['fold']):m['model'] for m in read(OUT/'models.json')['models']}
    primary=[r for r in rows if r['origin_year']==2022]
    measured=[r for r in primary if r['quality_rate'] is not None]
    selected=defaultdict(list)
    for pid in (*FIXED,668670):
        r=next((s for s in primary if s['player_id']==pid),None)
        if r:
            selected[pid].append('fixed source case' if pid in FIXED else 'missing-age diagnostic')
    for r in sorted(primary,key=lambda r:(r['history_pitches'],r['player_id']))[:2]:
        selected[r['player_id']].append('two smallest origin pitch samples')
    gain=lambda r:abs(r['history']-r['quality_rate'])-abs(r['calibrated']-r['quality_rate'])
    for name,r in [('largest gain',max(measured,key=gain)),('largest deterioration',min(measured,key=gain)),
                   ('false high',max(measured,key=lambda r:r['calibrated']-r['quality_rate'])),
                   ('false low',min(measured,key=lambda r:r['calibrated']-r['quality_rate'])),
                   ('ordinary median error',sorted(measured,key=lambda r:abs(r['calibrated']-r['quality_rate']))[len(measured)//2])]:
        selected[r['player_id']].append(name)
    def describe(r):
        year,pid=r['origin_year'],r['player_id'];m=models[year,r['fold']]
        source=[s for s in native[pid] if year-2<=s['season']<=year]
        n=sum(s['pitches']*2.**(s['season']-year) for s in source)
        runs=sum(s['framing_runs']*2.**(s['season']-year) for s in source)
        assert math.isclose(n,r['history_pitches'],abs_tol=1e-10)
        assert math.isclose(1000*runs/(6000+n),r['history'],abs_tol=1e-10)
        if m:
            z=(talent.matrix([r])[0]-m['mean'])/m['scale']
            terms=dict(zip(talent.FEATURES,(z*np.array(m['coef'])).tolist()))
            assert math.isclose(m['intercept']+sum(terms.values()),r['calibrated'],abs_tol=1e-10)
            blank={**r,'history_rate':0.,'reliability':0.}
            probe=float(talent.predict(m,[blank])[0])
        else:
            terms={};probe=None
        future=[s for s in native[pid] if year<s['season']<=r['window_end']]
        if r['quality_rate'] is not None:
            assert math.isclose(1000*sum(s['framing_runs'] for s in future)/sum(s['pitches'] for s in future),r['quality_rate'],abs_tol=1e-10)
        return dict(forecast=r,weighted_origin_sources=[{**s,'recency_weight':2.**(s['season']-year)} for s in source],
                    actual_inputs=talent.features(r),fitted_intercept=None if m is None else m['intercept'],fitted_terms=terms,
                    zero_history_and_reliability_fixed_fit_probe=probe,future_annual_path=future,
                    probe_scope='All history and derived reliability terms zeroed together; explanation only, not causal or validated replacement')
    cases=[]
    for pid,reasons in sorted(selected.items()):
        r=next(s for s in primary if s['player_id']==pid)
        peers=sorted([p for p in primary if p['player_id']!=pid],key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),abs(p['history_pitches']-r['history_pitches']),p['player_id']))[:3]
        cases.append(dict(selection=reasons,primary=describe(r),peers=[describe(p) for p in peers]))
    path=write('player-walkthrough.json',dict(cases=cases,player_walkthrough_status='complete',missing_fixed_case_ids=[pid for pid in FIXED if not any(r['player_id']==pid for r in primary)],
        selection='Fixed source cases and missing-age diagnostic, two smallest samples, largest absolute-error gain/loss, signed errors and median; origin-only peers',
        units='native framing runs per 1000 received non-swing pitches; three-year future quality pool',full_value_forecast=False))
    write('walk-review.json',dict(cases=len(cases),fully_replayed_peers=sum(len(c['peers']) for c in cases),
        unknown_quality_peers=sum(p['forecast']['quality_rate'] is None for c in cases for p in c['peers']),
        all_case_source_math_and_fitted_sums_verified=True,hash=sha256_file(path)))
    for c in cases:
        r=c['primary']['forecast']
        print(dict(name=r['player_name'],selection=c['selection'],age=r['age'],history_pitches=r['history_pitches'],
                   history=r['history'],calibrated=r['calibrated'],actual=r['quality_rate'],support=r['profile_people'],terms=c['primary']['fitted_terms']))


if __name__=='__main__':
    main()
