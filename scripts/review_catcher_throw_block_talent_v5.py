"""Every talent comparison gets annual source-to-prediction player calculations."""
from collections import defaultdict
import json
import math
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import FIXED,PUBLIC
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball import catcher_throw_block_baseline as baseline
from universal_baseball.storage import sha256_file


def main():
    report=json.loads((OUT/'talent-report.json').read_text(encoding='utf8'));verify(report['hashes']);assert report['protections']==protections()
    rows=pl.read_parquet(OUT/'talent-predictions.parquet').to_dicts();annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts()
    bypid=defaultdict(list)
    for s in annual:bypid[s['component'],s['player_id']].append(s)
    cases=[];missing=[]
    def describe(r):
        k,y,pid=r['component'],r['origin_year'],r['player_id'];past=[s for s in bypid[k,pid] if y-2<=s['season']<=y]
        h=baseline.history(k,past,y)
        for key in ('history','history_runs','history_opportunities','reliability'):assert math.isclose(h[key],r[key],abs_tol=1e-9)
        unshrunk=baseline.UNIT[k]*r['history_runs']/r['history_opportunities'] if r['history_opportunities'] else None
        if unshrunk is not None:assert math.isclose(unshrunk*r['reliability'],r['history'],abs_tol=1e-9)
        future=[s for s in bypid[k,pid] if y<s['season']<=r['window_end']]
        if r['quality_rate'] is not None:
            assert all(s['measurement_valid'] for s in future) and r['missing_native_outs']==0
            assert math.isclose(baseline.UNIT[k]*sum(s['runs'] for s in future)/sum(s['opportunities'] for s in future),r['quality_rate'],abs_tol=1e-9)
        return dict(forecast=r,weighted_origin_sources=[{**s,'weight':2.**(s['season']-y)} for s in past],
            intermediate=dict(unshrunk_rate=unshrunk,neutral_prior_opportunities=baseline.PRIOR[k],
                weighted_numerator=r['history_runs'],denominator=r['history_opportunities']+baseline.PRIOR[k],reliability=r['reliability'],
                neutral_forecast=0.,history_forecast=r['history']),future_annual_path=future,
            scope='MLB talent quality per source opportunity; no fitted age curve or future workload/value forecast')
    for kind in ('throwing','blocking'):
        primary=[r for r in rows if r['component']==kind and r['origin_year']==2022];measured=[r for r in primary if r['quality_rate'] is not None]
        selected=defaultdict(list)
        for pid in FIXED:
            r=next((s for s in primary if s['player_id']==pid),None)
            if r:selected[pid].append('fixed diagnostic')
            else:missing.append(dict(component=kind,player_id=pid,reason='no eligible MLB channel history by origin'))
        for r in sorted(primary,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]:selected[r['player_id']].append('two smallest origin samples')
        gain=lambda r:abs(r['quality_rate'])-abs(r['history']-r['quality_rate'])
        for reason,r in [('largest gain',max(measured,key=gain)),('largest deterioration',min(measured,key=gain)),
            ('false high',max(measured,key=lambda r:r['history']-r['quality_rate'])),('false low',min(measured,key=lambda r:r['history']-r['quality_rate'])),
            ('ordinary median error',sorted(measured,key=lambda r:abs(r['history']-r['quality_rate']))[len(measured)//2])]:selected[r['player_id']].append(reason)
        for pid,reasons in sorted(selected.items()):
            r=next(s for s in primary if s['player_id']==pid)
            peers=sorted([p for p in primary if p['player_id']!=pid],key=lambda p:(abs((p['age'] or 27)-(r['age'] or 27)),abs(p['history_opportunities']-r['history_opportunities']),p['player_id']))[:3]
            cases.append(dict(selection=reasons,primary=describe(r),peers=[describe(p) for p in peers]))
    path=OUT/'talent-player-walkthrough.json'
    payload=dict(player_walkthrough_status='complete',cases=cases,missing_fixed=missing,
        selection='fixed source cases, smallest samples, signed misses, median and largest gain/loss; peers by origin-known age/exposure/ID',
        no_value_forecast=True,no_learned_fit=True)
    # Resume after a reporting-only failure without replacing an existing walk.
    if path.exists():assert json.loads(path.read_text(encoding='utf8'))==payload
    else:save(path,payload)
    walk=OUT/'talent-walk-review.json';assert not walk.exists()
    save(walk,dict(player_walkthrough_status='complete',cases=len(cases),peers=sum(len(c['peers']) for c in cases),
        unknown_quality_peers=sum(p['forecast']['quality_rate'] is None for c in cases for p in c['peers']),
        source_and_prediction_calculations_replayed=True,hashes={str(path):sha256_file(path),str(__file__):sha256_file(Path(__file__))}))
    for p in (path,walk):(PUBLIC/p.name).write_bytes(p.read_bytes())
    for c in cases:
        r=c['primary']['forecast'];print(dict(component=r['component'],name=r['player_name'],selection=c['selection'],age=r['age'],
            n=r['history_opportunities'],runs=r['history_runs'],history=r['history'],future=r['quality_rate'],profile=r['profile_people']))
    print(dict(cases=len(cases),missing=missing))


if __name__=='__main__':main()
