"""Apply reviewed recipes as separate quality evidence, never awarded WAR."""
from collections import defaultdict
import json
from pathlib import Path

import polars as pl

from source_catcher_throw_block_v5 import ROOT,OUT
from review_catcher_throw_block_source_v5 import FIXED,PUBLIC
from audit_defensive_talent_support import verify
from run_hitter_finite_return_baseline import protections,save
from universal_baseball.catcher_throw_block_baseline import history
from universal_baseball.storage import sha256_file


def main():
    protected=protections();final=json.loads((OUT/'talent-final-review.json').read_text(encoding='utf8'));verify(final['hashes'])
    assert final['execution_integrity']=='pass' and final['player_walkthrough_status']=='complete'
    annual=pl.read_parquet(OUT/'extension-annual.parquet').to_dicts();by=defaultdict(list)
    for s in annual:by[s['component'],s['player_id']].append(s)
    rows=[];walks=[]
    for (kind,pid),ss in sorted(by.items()):
        past=[s for s in ss if 2023<=s['season']<=2025 and s['measurement_valid']]
        if not past:continue
        h=history(kind,ss,2025)
        rows.append(dict(component=kind,player_id=pid,player_name=past[-1]['player_name'],origin_year=2025,
                quality_rate=h['history'],**h,history_seasons=len(past),research_only=True,
                future_opportunity_forecast=False,awarded_value_forecast=False))
    for kind in ('throwing','blocking'):
        rr=[r for r in rows if r['component']==kind]
        selected=set(FIXED)|{r['player_id'] for r in sorted(rr,key=lambda r:(r['history_opportunities'],r['player_id']))[:2]}
        for pid in sorted(selected):
            r=next((s for s in rr if s['player_id']==pid),None)
            if not r:continue
            def describe(a):
                ss=[s for s in by[kind,a['player_id']] if 2023<=s['season']<=2025 and s['measurement_valid']]
                # Arithmetic independent of the recipe helper.
                n=sum(s['opportunities']*2**(s['season']-2025) for s in ss);runs=sum(s['runs']*2**(s['season']-2025) for s in ss)
                unit,prior=(100,100) if kind=='throwing' else (1000,3000)
                assert abs(a['quality_rate']-unit*runs/(prior+n))<1e-9
                return dict(quality=a,weighted_sources=[{**s,'weight':2**(s['season']-2025)} for s in ss],
                    denominator=prior+n,numerator=runs,rate_unit=unit)
            peers=sorted([s for s in rr if s['player_id']!=pid],key=lambda p:(abs(p['history_opportunities']-r['history_opportunities']),p['player_id']))[:3]
            walks.append(dict(selection='fixed cases/two smallest source samples; peers by exposure and ID',primary=describe(r),peers=[describe(p) for p in peers]))
    table=OUT/'current-2025-quality-baselines.parquet';assert not table.exists();pl.DataFrame(rows).write_parquet(table)
    walk=OUT/'current-quality-player-walkthrough.json';assert not walk.exists();save(walk,dict(player_walkthrough_status='complete',cases=walks))
    paths=[OUT/'talent-final-review.json',OUT/'extension-annual.parquet',table,walk,ROOT/'src/universal_baseball/catcher_throw_block_baseline.py',Path(__file__)]
    report=OUT/'baseline-preparation-review.json';assert not report.exists()
    save(report,dict(player_walkthrough_status='complete',channel_people={k:sum(r['component']==k for r in rows) for k in ('throwing','blocking')},
        source_cases=len(walks),research_only=True,population='positive valid 2023–2025 MLB channel evidence only',
        missing_history_rule='neutral uncertain prior with quality_evidence_observed false; not a measured neutral defender',
        no_future_exposure_or_value_forecast=True,no_2026_outcomes=True,deployment_approved=False,protections=protected,
        hashes={str(p):sha256_file(p) for p in paths}))
    for p in (walk,report):(PUBLIC/p.name).write_bytes(p.read_bytes())
    print(json.dumps(dict(people={k:sum(r['component']==k for r in rows) for k in ('throwing','blocking')},
        fixed=[r for r in rows if r['player_id'] in FIXED]),indent=2))


if __name__=='__main__':main()
