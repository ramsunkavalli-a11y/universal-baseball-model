"""Independent current recipe, eligibility and source walk verification."""
from collections import defaultdict
import json
import math
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import PUBLIC
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.storage import sha256_file


def main():
    protections();pre=json.loads((OUT/'baseline-preparation-review.json').read_text(encoding='utf8'));verify(pre['hashes'])
    annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts();sources=defaultdict(list)
    for s in annual:
        if 2023<=s['season']<=2025 and s['measurement_valid']:sources[s['component'],s['player_id']].append(s)
    rows=pl.read_parquet(OUT/'current-2025-quality-baselines.parquet').to_dicts()
    assert {(r['component'],r['player_id']) for r in rows}==set(sources) and len(rows)==len(sources)
    bykey={(r['component'],r['player_id']):r for r in rows}
    for r in rows:
        k=r['component'];ss=sources[k,r['player_id']];n=sum(s['opportunities']*2**(s['season']-2025) for s in ss);runs=sum(s['runs']*2**(s['season']-2025) for s in ss)
        unit,prior=(100.,100.) if k=='throwing' else (1000.,3000.)
        for a,b in [(r['quality_rate'],unit*runs/(prior+n)),(r['history_runs'],runs),(r['history_opportunities'],n),(r['reliability'],n/(prior+n))]:assert math.isclose(a,b,abs_tol=1e-9)
        assert r['history_seasons']==len(ss) and r['origin_year']==2025 and r['quality_evidence_observed'] and r['research_only']
        assert not r['future_opportunity_forecast'] and not r['awarded_value_forecast']
    walk=json.loads((OUT/'current-quality-player-walkthrough.json').read_text(encoding='utf8'));assert walk['player_walkthrough_status']=='complete'
    for c in walk['cases']:
        r=c['primary']['quality'];rr=[s for s in rows if s['component']==r['component'] and s['player_id']!=r['player_id']]
        peers=sorted(rr,key=lambda s:(abs(s['history_opportunities']-r['history_opportunities']),s['player_id']))[:3]
        assert [s['player_id'] for s in peers]==[s['quality']['player_id'] for s in c['peers']]
        for a in (c['primary'],*c['peers']):
            r=a['quality'];assert r==bykey[r['component'],r['player_id']]
            assert a['weighted_sources']==[{**s,'weight':2**(s['season']-2025)} for s in sources[r['component'],r['player_id']]]
            assert math.isclose(a['rate_unit']*a['numerator']/a['denominator'],r['quality_rate'],abs_tol=1e-9)
    protected_paths=[ROOT/'model_artifacts/hitter-selected-2026-frozen-2026-10-05/freeze-manifest.json',ROOT/'reports/model-evidence/hitter-final-2026/report.json']
    paths=[OUT/'baseline-preparation-review.json',Path(__file__),*protected_paths]
    result=OUT/'baseline-verification.json';assert not result.exists()
    save(result,dict(execution_integrity='pass',current_channel_rows_replayed=len(rows),source_cases=len(walk['cases']),
        source_peers=sum(len(c['peers']) for c in walk['cases']),player_walkthrough_status='complete',no_2026_outcomes=True,
        frozen_and_final_evaluation_hashes_verified=True,no_awarded_value_forecast=True,deployment_approved=False,
        hashes={str(p):sha256_file(p) for p in paths}))
    (PUBLIC/result.name).write_bytes(result.read_bytes());print(json.dumps(json.loads(result.read_text(encoding='utf8')),indent=2))


if __name__=='__main__':main()
