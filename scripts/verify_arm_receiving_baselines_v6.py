"""Verify all current research outputs independently of the prediction helper."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from evaluate_arm_receiving_talent_v6 import SOURCE,OUT,PUBLIC
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save


def main():
    protections()
    assert not (OUT/'baseline-verification.json').exists()
    note=json.loads((OUT/'baseline-preparation-review.json').read_text())
    for group in ('input_hashes','output_hashes'):
        for p,h in note[group].items():assert sha256_file(Path(p))==h,p
    sources=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual.parquet').to_dicts():sources[r['kind'],r['player_id']].append(r)
    actual={(r['kind'],r['player_id']):r for r in pl.read_parquet(OUT/'current-2025-quality-baselines.parquet').to_dicts()}
    expected=set()
    for (kind,pid),ss in sources.items():
        seen=[s for s in ss if 2023<=s['season']<=2025]
        if not seen or (kind=='arm' and not any(s['of_outs']>0 for s in seen)):continue
        expected.add((kind,pid));r=actual[kind,pid]
        good=[s for s in seen if s['isolated_outfield_quality_valid'] if kind=='arm'] if kind=='arm' else [s for s in seen if s['quality_valid']]
        n=sum(s['opportunities']*(1 if s['season']==2025 else .5 if s['season']==2024 else .25) for s in good)
        credit=sum(s['runs']*(1 if s['season']==2025 else .5 if s['season']==2024 else .25) for s in good)
        prior=300 if kind=='arm' else 600
        assert r['history_opportunities']==n and r['history_runs']==credit
        assert r['history']==100*credit/(n+prior) and r['reliability']==n/(n+prior)
        assert r['quality_evidence_observed']==(n>0)
        assert r['research_only'] and not r['deployment_allowed']
        assert r['awarded_future_runs'] is None and r['expected_future_opportunities'] is None
        assert r['origin_year']==2025 and not r['lower_minors_transport_validated'] and not r['age_adjustment_used']
    assert expected==set(actual) and len(actual)==note['rows']==752
    walk=json.loads((OUT/'current-quality-player-walkthrough.json').read_text())
    for w in walk['cases']:
        assert len(w['peers'])==3
        for case in [w['primary'],*w['peers']]:
            r=case['quality_output'];assert r==actual[r['kind'],r['player_id']]
            assert all(2023<=s['season']<=2025 for s in case['sources'])
    result=dict(all_current_rows_replayed=True,rows=len(actual),player_walkthrough_status='complete',
        no_future_opportunities_awarded=True,no_2026_outcomes=True,deployment_allowed=False,
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/'baseline-preparation-review.json',OUT/'current-2025-quality-baselines.parquet',SOURCE/'annual.parquet']})
    save(OUT/'baseline-verification.json',result);save(PUBLIC/'baseline-verification.json',result)
    print({k:v for k,v in result.items() if k!='input_hashes'})


if __name__=='__main__':main()
