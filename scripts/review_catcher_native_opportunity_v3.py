"""Certify framing source coverage and exclude all-zero historical placeholders."""
import json
import math
from pathlib import Path

import polars as pl

from audit_catcher_native_opportunity_v3 import OUT, ROOT
from source_defensive_positions_v2 import embedded
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

PUBLIC=ROOT/"reports/model-evidence/catcher-native-opportunity-v3"
FIXED=(595978,592663,518735,596142,672275,672386,663728)


def decode(path,year,all_pitches):
    content=path.read_text(encoding="utf8")
    params=embedded(content,"serverParams")
    assert int(params["seasonStart"])==int(params["seasonEnd"])==year<=2025
    assert params["minPitches"]==(1 if all_pitches else "q")
    data=embedded(content,"data")
    assert len({r["id"] for r in data})==len(data)
    assert all(r["pitches"]>0 and math.isfinite(r["rv_tot"]) for r in data)
    return data,params


def main():
    protected=protections()
    assert not (OUT/"source-review.json").exists()
    PUBLIC.mkdir(parents=True,exist_ok=True)
    ledger_path=ROOT/"reports/generated/defense-native-range-v3/component-ledger.parquet"
    ledger=pl.read_parquet(ledger_path).to_dicts()
    native={(r["season"],r["player_id"]):r for r in ledger if r["position"]==2}
    hashes={str(ledger_path):sha256_file(ledger_path)}
    coverage,cases,annual=[],[],[]
    for year in (2016,2019,2025):
        qualified_path=OUT/f"framing-{year}.response"
        all_path=OUT/f"framing-{year}-all.response"
        qualified,qp=decode(qualified_path,year,False)
        all_rows,ap=decode(all_path,year,True)
        for p in (qualified_path,all_path,OUT/f"inspection-{year}.json",OUT/f"inspection-{year}-all.json"):
            hashes[str(p)]=sha256_file(p)
        q={r["id"]:r for r in qualified}
        a={r["id"]:r for r in all_rows}
        assert set(q)<=set(a)
        for pid,r in q.items():
            assert r["pitches"]==a[pid]["pitches"] and r["rv_tot"]==a[pid]["rv_tot"]
        meaningful=any(abs(r["rv_tot"])>1e-12 for r in all_rows)
        discrepancies=[]
        for r in all_rows:
            n=native.get((year,r["id"]))
            assert n is not None and n["framing_runs"] is not None
            difference=abs(r["rv_tot"]-n["framing_runs"])
            assert difference<1e-8
            discrepancies.append(difference)
            annual.append(dict(season=year,player_id=r["id"],player_name=r["name"],
                               pitches=r["pitches"],shadow_pitches=r["pitches_shadow"],
                               framing_runs_raw=r["rv_tot"],framing_runs=r["rv_tot"] if meaningful else None,
                               framing_measurement_valid=meaningful, exposure_valid=n["exposure_valid"],
                               source_qualified=r["id"] in q,
                               rate_per_1000=1000*r["rv_tot"]/r["pitches"] if meaningful else None,
                               native_catcher_outs=n["native_outs"]))
        absent=[r for r in native.values() if r["season"]==year and r["framing_runs"] is not None and r["player_id"] not in a]
        recovered=[r for r in all_rows if r["id"] not in q and r["pitches"]>=1000]
        coverage.append(dict(season=year,qualified_rows=len(q),all_rows=len(a),
                             qualified_min_pitches=min(r["pitches"] for r in qualified),
                             all_min_pitches=min(r["pitches"] for r in all_rows),
                             recovered_at_least_1000_pitches=len(recovered),
                             all_at_least_1000_pitches=sum(r["pitches"]>=1000 for r in all_rows),
                             framing_measurement_valid=meaningful,
                             all_zero_run_placeholder=not meaningful,
                             max_native_run_difference=max(discrepancies),
                             absent_from_pitch_source=absent,observed_qualified_params=qp,observed_all_params=ap))
        selected={pid:["fixed identity"] for pid in FIXED if pid in a}
        for r in sorted(recovered,key=lambda r:r["id"])[:3]:
            selected.setdefault(r["id"],[]).append("first three recovered >=1000-pitch catchers by ID; no run-value selection")
        for pid,reasons in selected.items():
            r=a[pid]; n=native[year,pid]
            peers=sorted([p for p in all_rows if p["id"]!=pid],key=lambda p:(abs(p["pitches"]-r["pitches"]),p["id"]))[:3]
            cases.append(dict(season=year,selection=reasons,player_id=pid,player_name=r["name"],
                              pitches=r["pitches"],shadow_pitches=r["pitches_shadow"],raw_framing_runs=r["rv_tot"],
                              framing_quality_known=meaningful,framing_rate_per_1000=1000*r["rv_tot"]/r["pitches"] if meaningful else None,
                              qualified_source_present=pid in q,
                              native_catcher_outs=n["native_outs"],native_framing_runs=n["framing_runs"],
                              implications="modern table all-zero placeholders; legacy measurement required" if not meaningful else "formerly omitted eligible source evidence; not automatically a reliable talent grade" if pid not in q else "same measured value under both source settings",
                              source_player=r, peers=[dict(player_id=p["id"],player_name=p["name"],pitches=p["pitches"],raw_framing_runs=p["rv_tot"],
                                                           framing_rate_per_1000=1000*p["rv_tot"]/p["pitches"] if meaningful else None,
                                                           qualified_source_present=p["id"] in q) for p in peers]))
    pl.DataFrame(annual,infer_schema_length=None).write_parquet(OUT/"framing-pilot.parquet")
    for y in (2016,2017):
        values=[r["framing_runs"] for r in native.values() if r["season"]==y and r["framing_runs"] is not None]
        assert values and all(v==0 for v in values)
    for p in (ROOT/"docs/catcher-native-opportunity-v3-contract.md",ROOT/"scripts/audit_catcher_native_opportunity_v3.py",
              ROOT/"scripts/review_catcher_native_opportunity_v3.py",OUT/"framing-pilot.parquet"):
        hashes[str(p)]=sha256_file(p)
    walk=dict(player_walkthrough_status="complete",selection="fixed IDs plus recovered >=1000-pitch input-selected cases; peers nearest pitch exposure/ID, no future selection",cases=cases,
              no_model_fit=True,no_future_quality_scoring=True)
    for root in (OUT,PUBLIC):
        save(root/"player-walkthrough.json",walk)
    hashes[str(OUT/"player-walkthrough.json")]=sha256_file(OUT/"player-walkthrough.json")
    report=dict(player_walkthrough_status="complete",coverage=coverage,hashes=hashes,protections=protected,
                execution_integrity="pass",sources_repaired=True,
                corrected_parameter="minPitches=1, not min=1",modern_framing_2016_2017_usable=False,
                modern_framing_starts=2018,old_confirmations_restricted_to_qualified_sources=True,
                no_projection_improvement_claim=True,model_fit=False,deployment_approved=False,
                next="Same certified all-pitch semantics for 2018–2025; investigate separate legacy 2016–2017 rather than treating zero placeholders as observed quality; throwing/blocking source audits remain separate.")
    for root in (OUT,PUBLIC):
        save(root/"source-review.json",report)
    print(json.dumps(coverage,indent=2))
    print('reviewed player source cases',len(cases))


if __name__=="__main__":
    main()
