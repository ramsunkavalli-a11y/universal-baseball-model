"""Current research skill outputs, never future opportunities or awarded runs."""
from collections import defaultdict
from pathlib import Path
import json
import polars as pl
from evaluate_arm_receiving_talent_v6 import ROOT,SOURCE,OUT,PUBLIC
from review_arm_receiving_pilot_v6 import FIXED
from universal_baseball.arm_receiving_baseline import history,PRIOR
from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save


def main():
    protections()
    assert not (OUT/'current-2025-quality-baselines.parquet').exists()
    final=json.loads((OUT/'final-review.json').read_text())
    assert final['player_walkthrough_status']=='complete' and not final['deployment_allowed']
    for p,h in final['input_hashes'].items():assert sha256_file(Path(p))==h,p
    histories=defaultdict(list)
    for r in pl.read_parquet(SOURCE/'annual.parquet').to_dicts():histories[r['kind'],r['player_id']].append(r)
    rows=[];walks=[]
    for (kind,pid),ss in sorted(histories.items()):
        seen=[s for s in ss if 2023<=s['season']<=2025]
        if not seen or (kind=='arm' and not any(s['of_outs']>0 for s in seen)):continue
        r=dict(kind=kind,player_id=pid,player_name=seen[-1]['player_name'],origin_year=2025,
               **history(kind,ss,2025),prior_opportunities=PRIOR[kind],units='runs_per_100_actual_channel_opportunities',
               position_scope='outfield_only_skill' if kind=='arm' else 'first_base_received_throws',
               expected_future_opportunities=None,awarded_future_runs=None,deployment_allowed=False,
               lower_minors_transport_validated=False,age_adjustment_used=False)
        # Separate arithmetic replay, not a second fitted model.
        key='isolated_outfield_quality_valid' if kind=='arm' else 'quality_valid'
        good=[s for s in seen if s[key]]
        n=sum(s['opportunities']*2.**(s['season']-2025) for s in good)
        runs=sum(s['runs']*2.**(s['season']-2025) for s in good)
        assert r['history']==100*runs/(n+PRIOR[kind]) and r['history_opportunities']==n
        assert r['quality_evidence_observed']==(n>0)
        rows.append(r)
    for kind in ('arm','receiving'):
        cohort=[r for r in rows if r['kind']==kind];by_id={r['player_id']:r for r in cohort}
        selected=set(FIXED[kind])|{r['player_id'] for r in sorted(cohort,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]}
        def trace(r):
            return dict(quality_output=r,sources=[{**s,'weight':2.**(s['season']-2025)}
                for s in histories[kind,r['player_id']] if 2023<=s['season']<=2025],
                interpretation='Neutral is a fallback when evidence is unknown, not a measured average grade. Quality does not award runs without future role and opportunities.')
        for pid in sorted(selected):
            if pid not in by_id:continue
            focal=by_id[pid]
            peers=sorted((r for r in cohort if r['player_id']!=pid),
                key=lambda r:(abs(r['history_opportunities']-focal['history_opportunities']),r['player_id']))[:3]
            walks.append(dict(primary=trace(focal),peers=[trace(r) for r in peers],
                selection='Fixed diagnostic cases/two smallest histories; opportunity/ID-selected peers.'))
    table=OUT/'current-2025-quality-baselines.parquet';pl.DataFrame(rows,infer_schema_length=None).write_parquet(table)
    walk_path=OUT/'current-quality-player-walkthrough.json'
    walk=dict(cases=walks,player_walkthrough_status='complete',no_future_result_access=True)
    save(walk_path,walk);save(PUBLIC/walk_path.name,walk)
    report=dict(rows=len(rows),arm_rows=sum(r['kind']=='arm' for r in rows),receiving_rows=sum(r['kind']=='receiving' for r in rows),
        unknown_quality_rows=sum(not r['quality_evidence_observed'] for r in rows),all_current_arithmetic_replayed=True,
        player_walkthrough_status='complete',focal_cases=len(walks),peer_cases=3*len(walks),
        frozen_forecasts_unchanged=True,deployment_allowed=False,no_2026_outcomes=True,
        input_hashes={str(p):sha256_file(p) for p in [Path(__file__),SOURCE/'annual.parquet',OUT/'final-review.json',ROOT/'src/universal_baseball/arm_receiving_baseline.py']},
        output_hashes={str(p):sha256_file(p) for p in [table,walk_path]})
    save(OUT/'baseline-preparation-review.json',report);save(PUBLIC/'baseline-preparation-review.json',report)
    print({k:v for k,v in report.items() if k not in ('input_hashes','output_hashes')})


if __name__=='__main__':main()
