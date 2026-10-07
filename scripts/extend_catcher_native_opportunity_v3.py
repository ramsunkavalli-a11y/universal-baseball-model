"""Extend reviewed modern framing capture, never manufacture pre-2018 quality."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import shutil

import polars as pl
import requests

from audit_defensive_talent_support import verify
from audit_catcher_native_opportunity_v3 import ROOT, OUT as PILOT
from review_catcher_native_opportunity_v3 import decode
from run_hitter_finite_return_baseline import protections, save
from universal_baseball.storage import sha256_file

OUT=ROOT/"reports/generated/catcher-native-opportunity-v3/modern"
PUBLIC=ROOT/"reports/model-evidence/catcher-native-opportunity-v3"


def capture(year):
    assert 2018<=year<=2025
    path=OUT/f"framing-{year}.response"
    params=dict(type="catcher",seasonStart=year,seasonEnd=year,minPitches=1,
                min=1,team="",sortColumn="rv_tot",sortDirection="desc")
    if not path.exists():
        if year in (2019,2025):
            shutil.copyfile(PILOT/f"framing-{year}-all.response",path)
        else:
            r=requests.get("https://baseballsavant.mlb.com/leaderboard/catcher-framing",params=params,timeout=45)
            r.raise_for_status()
            path.write_bytes(r.content)
    data,observed=decode(path,year,True)
    assert any(abs(r["rv_tot"])>1e-12 for r in data), "Do not count a degenerate all-zero season as quality"
    return year,data,dict(year=year,requested=params,observed=observed,path=str(path),sha256=sha256_file(path),rows=len(data))


def main():
    protected=protections()
    review=json.loads((PILOT/"source-review.json").read_text(encoding="utf8"))
    verify(review["hashes"])
    assert review["player_walkthrough_status"]=="complete"
    assert (ROOT/"docs/catcher-native-opportunity-v3-result.md").exists()
    OUT.mkdir(parents=True,exist_ok=True)
    assert not (OUT/"source-review.json").exists()
    ledger=pl.read_parquet(ROOT/"reports/generated/defense-native-range-v3/component-ledger.parquet")
    native={(r["season"],r["player_id"]):r for r in ledger.filter(pl.col("position")==2).iter_rows(named=True)}
    annual,captures,traces,gaps=[],[],[],[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(capture,range(2018,2026)))
    for year,data,cap in results:
        captures.append(cap)
        for r in data:
            n=native.get((year,r["id"]))
            assert n is not None and n["framing_runs"] is not None
            assert abs(r["rv_tot"]-n["framing_runs"])<1e-8
            annual.append(dict(season=year,player_id=r["id"],player_name=r["name"],pitches=r["pitches"],
                               shadow_pitches=r["pitches_shadow"],framing_runs=r["rv_tot"],
                               native_catcher_outs=n["native_outs"],exposure_valid=n["exposure_valid"],
                               framing_measurement_valid=True,rate_per_1000=1000*r["rv_tot"]/r["pitches"]))
        pids={r["id"] for r in data}
        gaps.extend(r for (s,pid),r in native.items() if s==year and r["framing_runs"] is not None and pid not in pids)
        # Origin-only source player review for every newly captured year; a
        # fixed star and two smallest measured pitch exposures, not winner picks.
        fixed=[r for r in data if r["id"] in (595978,592663,596142,672275)]
        small=sorted(data,key=lambda r:(r["pitches"],r["id"]))[:2]
        for r in {r["id"]:r for r in fixed+small}.values():
            peers=sorted([p for p in data if p["id"]!=r["id"]],key=lambda p:(abs(p["pitches"]-r["pitches"]),p["id"]))[:3]
            traces.append(dict(season=year,player=r,rate_per_1000=1000*r["rv_tot"]/r["pitches"],
                               selection="fixed identity or two smallest pitch exposures, no quality/outcome selection",
                               peers=peers,model_fit=False))
    frame=pl.DataFrame(annual,infer_schema_length=None).sort(["season","player_id"])
    assert frame.select("season","player_id").unique().height==frame.height
    frame.write_parquet(OUT/"framing-annual.parquet")
    save(OUT/"source-player-walkthrough.json",dict(player_walkthrough_status="complete",cases=traces))
    hashes={c["path"]:c["sha256"] for c in captures}
    hashes.update({str(p):sha256_file(p) for p in (OUT/"framing-annual.parquet",OUT/"source-player-walkthrough.json",
                                               ROOT/"scripts/extend_catcher_native_opportunity_v3.py")})
    report=dict(player_walkthrough_status="complete",captures=captures,rows=frame.height,
                people=frame["player_id"].n_unique(),missing_native_pitch_samples=gaps,
                modern_measurement_years=list(range(2018,2026)),pre2018_framing_quarantined=True,
                protections=protected,hashes=hashes,model_fit=False,projection_improvement_claim=False,
                next="Lock future-MLB framing quality window/support before testing any learner; don't relabel qualified-only old comparisons as all-catcher tests.")
    save(OUT/"source-review.json",report)
    save(PUBLIC/"modern-source-review.json",report)
    save(PUBLIC/"modern-source-player-walkthrough.json",dict(player_walkthrough_status="complete",cases=traces))
    print(json.dumps(dict(rows=frame.height,people=frame["player_id"].n_unique(),source_cases=len(traces),
                          years={y:frame.filter(pl.col("season")==y).height for y in range(2018,2026)},gaps=len(gaps)),indent=2))


if __name__=="__main__":
    main()
