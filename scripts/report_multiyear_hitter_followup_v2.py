"""Deliver accepted v2 fields without modifying any v1 mean or frozen package."""
from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
import shutil

import numpy as np
import polars as pl

from evaluate_multiyear_hitter_followup_v2 import OUT, V1, PLAN, save_json
from universal_baseball.storage import sha256_file

PACKAGE = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22")
MEANS = ["value_2026","value_2027","value_2028","value_three_years"]


def deliver(original, opportunities, intervals, report):
    current = original.sort("player_id")
    selected = report["opportunity"]["selected"]
    established_ids = opportunities.filter(pl.col("origin_year")==2025)["player_id"].unique().to_list()
    current = current.with_columns(pl.col("player_id").is_in(established_ids).alias("established_opportunity_eligible"))
    for h in (1,2,3):
        probability, pa = f"activity_h{h}",f"expected_pa_h{h}"
        current = current.with_columns(pl.col(probability).alias(probability+"_v1"),pl.col(pa).alias(pa+"_v1"))
        if selected!="P0":
            updates = opportunities.filter((pl.col("origin_year")==2025)&(pl.col("horizon")==h)).select("player_id",
                pl.col("p1").alias("new_probability"),pl.col("pa2" if selected=="P2" else "pa1").alias("new_pa"))
            current = current.join(updates,on="player_id",how="left",validate="1:1",maintain_order="left").with_columns(
                pl.coalesce("new_probability",probability).alias(probability),pl.coalesce("new_pa",pa).alias(pa)).drop("new_probability","new_pa")
        other = current.filter(~pl.col("established_opportunity_eligible"))
        for field in (probability,pa):
            np.testing.assert_array_equal(other[field].to_numpy(),other[field+"_v1"].to_numpy())
        if selected=="P1":
            np.testing.assert_allclose((current[pa]/current[probability]).to_numpy(),
                                      (current[pa+"_v1"]/current[probability+"_v1"]).to_numpy(),rtol=1e-12)
    for key,mean in zip(("h1","h2","h3","c3"),MEANS):
        # Only the predeclared accepted candidate is publishable.
        if report["uncertainty"][key]["accepted"]:
            update = intervals.filter((pl.col("origin_year")==2025)&(pl.col("horizon")==key)).select(
                "player_id",pl.col("q2_lo").alias("new_lo"),pl.col("q2_hi").alias("new_hi"))
            current = current.join(update,on="player_id",how="left",validate="1:1",maintain_order="left").with_columns(
                pl.col("new_lo").alias(mean+"_lower80"),pl.col("new_hi").alias(mean+"_upper80")).drop("new_lo","new_hi")
        else:
            current = current.with_columns(pl.lit(None,dtype=pl.Float64).alias(mean+"_lower80"),
                                          pl.lit(None,dtype=pl.Float64).alias(mean+"_upper80"))
    current = current.with_columns(
        pl.when(pl.col("established_opportunity_eligible") & pl.lit(selected!="P0"))
        .then(pl.lit("recent MLB history + batting quality; original conditional PA" if selected=="P1" else "recent MLB history + batting quality; Poisson conditional PA"))
        .otherwise(pl.lit("existing age/level/workload/roster opportunity model")).alias("opportunity_source"),
        pl.lit("withheld_after_v2_subgroup_check" if not any(r["accepted"] for r in report["uncertainty"].values()) else "see_horizon_specific_ranges").alias("interval_status"))
    reference = original.sort("player_id")
    for col in MEANS:
        if current[col].to_numpy().tobytes()!=reference[col].to_numpy().tobytes():
            raise ValueError("Mean forecast changed: "+col)
    if current.height!=3907 or current["player_id"].n_unique()!=3907:
        raise ValueError("Fixed population changed")
    if any(current[c].null_count()!=3907 for c in ("war_h1","war_h2","war_h3","war_c3","pa_h1","pa_h2","pa_h3")):
        raise ValueError("Future outcome guard failed")
    return current


def explorer(current):
    template = Path("templates/multiyear-hitter-followup-v2-explorer.html").read_text(encoding="utf-8")
    return template.replace("__PLAYER_DATA__",json.dumps(current.to_dicts(),allow_nan=False).replace("</","<\\/"))


def main():
    report = json.loads((OUT/"report.json").read_text())
    for filename, expected in report["source_manifest"]["hashes"].items():
        if sha256_file(Path(filename))!=expected:
            raise ValueError("Scored input or implementation changed: "+filename)
    original = pl.read_parquet(V1/"player-forecast-2026-2028.parquet")
    opportunities = pl.read_parquet(OUT/"opportunity-predictions.parquet")
    intervals = pl.read_parquet(OUT/"calibrated-predictions.parquet")
    current = deliver(original,opportunities,intervals,report)
    report["delivery"] = {"rows":current.height,"established_players":int(current["established_opportunity_eligible"].sum()),
        "mean_arrays_byte_identical_to_v1":True,"original_packages_untouched":True,
        "scope":"MLB batting + replacement only; not full WAR. Workload and value not jointly reconciled.",
        "historical_source_issue":"Alonso absent in raw historical roster endpoint; no manual repair. New established probability does not use membership.",
        "intervals":"withheld: all four horizons fail upper-minors high-value coverage guard",
        "implementation_audit":"Caught current forecast row-order mismatch in first candidate build before delivery. Attached arrays to player IDs before joining and reran. Historical scores unchanged; model/parameters unchanged.",
        "legacy_audit":"Old established-hitter rolling validation did not embargo immature multi-year labels; those validation claims are withdrawn. Original legacy artifact preserved. V2 replaces that evidence for Years 1-3 only.",
        "examples":current.filter(pl.col("player_id").is_in([592450,624413,665742,691422])).select("player_id","player_name",
            "value_three_years","activity_h1_v1","activity_h1","activity_h3_v1","activity_h3","expected_pa_h1","expected_pa_h3").to_dicts()}
    report["package_versions"] = {n:importlib.metadata.version(n) for n in ("numpy","polars","scikit-learn","lightgbm")}
    report["supplemental_code_hashes"] = {p:sha256_file(Path(p)) for p in [
        "scripts/audit_established_hitter_opportunity.py","scripts/audit_multiyear_hitter_rosters_v2.py",str(Path(__file__)),
        "templates/multiyear-hitter-followup-v2-explorer.html","src/universal_baseball/multiyear_hitter_value.py",
        "scripts/evaluate_multiyear_hitter_v1.py"]}
    current.write_parquet(OUT/"forecast-2026-2028.parquet")
    (OUT/"index.html").write_text(explorer(current),encoding="utf-8",newline="\n")
    save_json(OUT/"delivery-report.json",report)
    PACKAGE.mkdir(parents=True,exist_ok=True)
    names = ["forecast-2026-2028.parquet","opportunity-predictions.parquet","opportunity-fits.json","calibrated-predictions.parquet",
        "raw-quantile-predictions.parquet","quantile-fit-notes.json","delivery-report.json","source-manifest.json","roster-audit.json"]
    for name in names:
        shutil.copyfile(OUT/name,PACKAGE/name)
    (PACKAGE/"roster-captures").mkdir(exist_ok=True)
    for path in (OUT/"roster-captures").glob("*.json"):
        shutil.copyfile(path,PACKAGE/"roster-captures"/path.name)
    save_json(PACKAGE/"manifest.json",{"version":"multiyear-hitter-followup-v2-2026-09-22","cutoff":"2025-12-31",
        "forecast_seasons":[2026,2027,2028],"status":"development_probability_only","protected_outcomes_used":False,
        "plan_sha256":sha256_file(PLAN),"files":{p.relative_to(PACKAGE).as_posix():sha256_file(p) for p in sorted(PACKAGE.rglob("*")) if p.is_file() and p.name!="manifest.json"}})
    print(json.dumps(report["delivery"],indent=2),flush=True)


if __name__=="__main__":
    main()
