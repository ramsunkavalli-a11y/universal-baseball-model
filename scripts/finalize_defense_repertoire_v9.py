"""Independently check uncertainty and close the failed youth-profile review."""

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.storage import sha256_file
from run_hitter_finite_return_baseline import protections,save

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/generated/defense-repertoire-v9"
PUBLIC=ROOT/"reports/model-evidence/defense-repertoire-v9"


def read(p):return json.loads(p.read_text(encoding="utf8"))


def main():
    protections();assert not (OUT/"final-review.json").exists()
    report=read(OUT/"fit-report.json");verify=read(OUT/"independent-verification.json")
    walk=read(OUT/"player-walkthrough.json");young=read(OUT/"young-profile-diagnosis.json")
    assert verify["integrity_pass"] and verify["all_forecasts_replayed"]==12432
    for receipt in (report,verify,young):
        for p,h in receipt["hashes"].items():assert sha256_file(Path(p))==h
    assert len(walk["cases"])==16 and sum(len(c["records"])-1 for c in walk["cases"])==48
    assert len(young["cases"])==4 and sum(len(c["records"])-1 for c in young["cases"])==12
    q=pl.read_parquet(OUT/"predictions.parquet");people=q["player_id"].unique().sort().to_list()
    idx={p:i for i,p in enumerate(people)};loss=np.zeros((len(people),3,2));present=np.zeros((len(people),3))
    for r in q.to_dicts():
        i,j=idx[r["player_id"]],r["origin_year"]-2022;present[i,j]=1
        for a,arm in enumerate(("repair","ratio")):
            loss[i,j,a]=np.mean([(r[f"{arm}_{p}"]-r[f"actual_{p}"])**2 for p in range(2,10)])
    rng=np.random.default_rng(708007);differences=[]
    for _ in range(40):
        counts=rng.multinomial(len(people),np.full(len(people),1/len(people)),size=50)
        rates=np.sqrt(np.einsum("bi,ija->bja",counts,loss)/(counts@present)[:,:,None])
        differences.extend((rates[:,:,0]-rates[:,:,1]).mean(axis=1))
    interval=np.quantile(differences,[.025,.975]).tolist()
    assert np.allclose(interval,report["interval"]["interval_95"],atol=1e-8,rtol=0)
    group_checks=[]
    for g in report["groups"]:
        if g["arm"]!="repair" or g["rows"]<100 or g["origin"] not in (2022,2023):continue
        ref=next(r for r in report["groups"] if (r["origin"],r["field"],r["value"],r["arm"])==(g["origin"],g["field"],g["value"],"ratio"))
        group_checks.append(dict(origin=g["origin"],field=g["field"],value=g["value"],rows=g["rows"],
            reference_rmse=ref["cell_rmse"],repair_rmse=g["cell_rmse"],ratio=g["cell_rmse"]/ref["cell_rmse"],
            tolerance_pass=g["cell_rmse"]<=1.1*ref["cell_rmse"]))
    means={a:np.mean([s["cell_rmse"] for s in report["overall"] if s["arm"]==a]) for a in ("ratio","repair")}
    totals=[r for r in report["overall"] if r["arm"]=="repair" and r["origin"] in (2022,2023)]
    unique_focal={(c["player_id"],c["origin"]) for c in [*walk["cases"],*young["cases"]]}
    result=dict(date="2026-10-07",integrity_pass=True,player_walkthrough_status="complete",independent_interval_replayed=True,
        independent_interval_95=interval,equal_origin_rmse=means,relative_error_improvement=1-means["repair"]/means["ratio"],
        primary_tolerance_pass=means["repair"]<=1.02*means["ratio"],groups_pass=all(g["tolerance_pass"] for g in group_checks),
        dev_totals_pass=all(abs(r["predicted_total_outs"]/r["actual_total_outs"]-1)<=.2 for r in totals),group_checks=group_checks,
        no_donated_position_mechanics_pass=True,full_population_reasonability_pass=False,
        focal_walks=16,peer_walks=48,extra_young_walks=4,extra_young_peer_walks=12,unique_focal_player_origins=len(unique_focal),
        disposition="retain_research_mechanics_not_full_allocator_young_position_transition_repair_required",
        defects=["Prospect repertoire concentration misses CF-to-corner and SS-to-2B MLB transitions.",
                 "Some young prospect losses are excessive fixed PA, not incorrect position ability.",
                 "Dated planned assignments are not represented; older cache still misses finite returns.",
                 "Legacy batting cohort contains pitcher-only/unknown-repertoire rows; zero nonpitcher assignments are not a new talent discovery."],
        gains=["No role-group donation of catcher innings to unrelated first basemen/outfielders.",
               "Tiny MLB fielding/PA ratios lean toward a supported group while using fuller minor position evidence.",
               "Established-player and measured positive native-opportunity errors improve across all three origins."],
        next="Predeclare one experienced-player/potential-position transition bridge, preserve no-donated-C constraint and anchors, then complete matched delivered-runs/value integration.",
        no_threshold_sweep_or_named_override=True,forecast_or_explorer_changed=False,protected_outcomes_used=False,
        value_integration_complete=False,eventual_minor_quality_validated=False,deployment_approved=False,
        old_walkthrough_date_wording_correction="The v8 source trace uses each origin's preceding three calendar years, not every year from 2020 through later origins.",
        hashes={str(p):sha256_file(p) for p in [Path(__file__),OUT/"preflight.json",OUT/"fit-report.json",OUT/"independent-verification.json",
            OUT/"player-walkthrough.json",OUT/"young-profile-diagnosis.json",ROOT/"docs/defense-repertoire-v9-player-review.md",ROOT/"docs/defense-repertoire-v9-result.md"]})
    assert not result["groups_pass"] and result["primary_tolerance_pass"] and result["dev_totals_pass"]
    save(OUT/"final-review.json",result);save(PUBLIC/"final-review.json",result)
    protections();print(json.dumps({k:result[k] for k in ["player_walkthrough_status","relative_error_improvement","groups_pass","disposition"]}))


if __name__=="__main__":main()
