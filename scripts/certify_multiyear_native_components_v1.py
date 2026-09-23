"""Validate native defensive/run labels against independent dated workload history."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_multiyear_hitter_components_v1 import OUT, SOURCES
from source_multiyear_native_components_v1 import OUT as RAW
from universal_baseball.player_value_positional_adjustment import POSITIONAL_RUNS_PER_162
from universal_baseball.storage import sha256_file

NATIVE = ["range_runs", "arm_runs", "dp_runs", "fielding_runs_prevented_on_rec1b",
          "framing_runs", "throwing_runs", "blocking_runs"]
POSITIONS = {"C":2,"1B":3,"2B":4,"3B":5,"SS":6,"LF":7,"CF":8,"RF":9}


def official_annual(fielding):
    """Calendar exposure: do not inflate 2020 innings to a full season."""
    fielding = fielding.filter(pl.col("position_abbreviation").is_in([*POSITIONS, "DH"]))
    if fielding["season"].max() > 2025:
        raise ValueError("Protected season")
    return fielding.group_by("season", "player_id").agg(
        pl.col("fielding_outs").sum().alias("official_outs"),
        *[pl.col("fielding_outs").filter(pl.col("position_abbreviation")==p).sum().alias(f"outs_{n}") for p,n in POSITIONS.items()],
        pl.col("games_started").filter(pl.col("position_abbreviation")=="DH").sum().alias("dh_starts"),
    ).with_columns(
        (pl.sum_horizontal([pl.col(f"outs_{n}")*POSITIONAL_RUNS_PER_162[p]/4374 for p,n in POSITIONS.items()])
         +pl.col("dh_starts")*POSITIONAL_RUNS_PER_162["DH"]/162).alias("position_runs"))


def main():
    fielding = pl.read_parquet(SOURCES["mlb_fielding"])
    official = official_annual(fielding)
    notes, tables, fingerprints = [], [], []
    for year in range(2016,2026):
        path = RAW/f"fielding-{year}.parquet"
        f = pl.read_parquet(path).rename({"id":"player_id"}).with_columns(
            *[pl.col(c).cast(pl.Float64, strict=False) for c in [*NATIVE,"total_runs","inf_of_runs","catching_runs"]])
        if f.unique("player_id").height != f.height:
            raise ValueError("Duplicate fielding identity")
        np.testing.assert_allclose(f["total_runs"], f.select(pl.sum_horizontal([pl.col(c).fill_null(0) for c in NATIVE])).to_series(), atol=1e-8)
        # The endpoint has no embedded year: independent identity/exposure fingerprints
        # must identify the requested season, not merely a changing HTML response.
        distances = []
        for other in range(2016,2026):
            j = official.filter(pl.col("season")==other).join(f.select("player_id","outs_total"),on="player_id")
            distances.append((other,float(j.select((pl.col("official_outs")-pl.col("outs_total")).abs().median()).item())))
        distances.sort(key=lambda t:t[1])
        if distances[0] != (year,0.0) or distances[1][1] < 100:
            raise ValueError(f"Uncertified requested year {year}: {distances}")
        fingerprints.append(sha256_file(path))
        j = official.filter(pl.col("season")==year).join(f.select("player_id","outs_total"),on="player_id",how="left")
        missing = j.filter((pl.col("official_outs")>0)&pl.col("outs_total").is_null())
        mismatch = j.filter(pl.col("outs_total").is_not_null() & (pl.col("outs_total") != pl.col("official_outs")))
        notes.append({"season":year,"native_rows":f.height,"closest_years":distances[:2],
            "source_sha256":sha256_file(path),"missing_positive_exposure":missing.select("player_id","official_outs").to_dicts(),
            "exposure_differences":mismatch.height,"max_absolute_exposure_difference":mismatch.select((pl.col("official_outs")-pl.col("outs_total")).abs().max()).item(),
            "missing_outs":int(missing["official_outs"].sum()),"official_outs":int(j["official_outs"].sum()),
            "blocking_available":year>=2018,"first_base_receiving_available":year>=2021})
        # Raw published sums recompose exactly. Preserve structural component-year
        # missingness rather than filling absent blocking/receiving eras with zero.
        f = f.with_columns(pl.lit(year).alias("season"),
            *[pl.col(c).fill_null(0).alias(c) for c in NATIVE if c not in {"blocking_runs","fielding_runs_prevented_on_rec1b"}],
            (pl.col("blocking_runs").fill_null(0) if year>=2018 else pl.lit(None,dtype=pl.Float64)).alias("blocking_runs"),
            (pl.col("fielding_runs_prevented_on_rec1b").fill_null(0) if year>=2021 else pl.lit(None,dtype=pl.Float64)).alias("receiving_runs"))
        tables.append(f.select("season","player_id",*NATIVE[:-1],"blocking_runs","receiving_runs","total_runs","outs_total","tot_pa"))
    if len(set(fingerprints)) != 10:
        raise ValueError("Repeated annual fielding payload")
    native = pl.concat(tables,how="vertical_relaxed")
    run_tables = []
    for year in range(2016,2026):
        f = pl.read_parquet(RAW/f"running-{year}.parquet")
        if set(f["start_year"]) != {year} or set(f["end_year"]) != {year} or f.unique("player_id").height != f.height:
            raise ValueError("Running year/identity failure")
        np.testing.assert_allclose(f["runner_runs_tot"], f["runner_runs_XB"]+f["runner_runs_SBX"], atol=.002)
        run_tables.append(f.select(pl.lit(year).alias("season"),"player_id",pl.col("runner_runs_XB").alias("advancement_runs"),
                                   pl.col("N_runner_moved_XB").alias("advancement_opportunities")))
    running = pl.concat(run_tables)
    OUT.mkdir(parents=True,exist_ok=True)
    native.write_parquet(OUT/"native-fielding-history.parquet")
    running.write_parquet(OUT/"native-advancement-history.parquet")
    official.write_parquet(OUT/"official-position-history.parquet")
    report = {"status":"source_certified_with_explicit_coverage_limits","fielding":notes,
        "raw_hashes":{str(p):sha256_file(p) for p in sorted(RAW.glob("*.parquet"))},
        "upstream_hashes":{str(SOURCES["mlb_fielding"]):sha256_file(SOURCES["mlb_fielding"])},
        "rules":["No 2026 requests","Missing active fielding label is unknown, not zero",
                 "No inflation of 2020 exposure","Native fielding sums independently checked",
                 "Published retrospective metrics, not archived historical publication vintages",
                 "Full blocker history starts 2018; receiving starts 2021",
                 "Official fielding exposure used for position; Savant exposure retained for native rate denominators",
                 "Small exposure discrepancies are documented, not silently repaired"]}
    (OUT/"native-source-certification.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"fielding_rows":native.height,"running_rows":running.height,
                      "missing_outs_by_year":{r["season"]:r["missing_outs"] for r in notes}}))


if __name__=="__main__":
    main()
