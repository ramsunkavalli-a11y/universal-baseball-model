"""Decompose saved Year-2 opportunity errors; never fit or publish forecasts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_horizon_consistency import fixed_groups
from universal_baseball.hitter_opportunity_calendar import prepare_rows, score_rows, summarize
from universal_baseball.multiyear_hitter_followup import compare_losses
from universal_baseball.storage import sha256_file

V1 = Path("reports/generated/multiyear-hitter-v1")
V2 = Path("model_artifacts/multiyear-hitter-followup-v2-2026-09-22")
PREVIOUS = Path("model_artifacts/hitter-anchored-development-v1-2026-09-22")
PLAN = Path("docs/hitter-opportunity-calendar-v1-plan.md")
OUT = Path("model_artifacts/hitter-opportunity-calendar-v1-2026-09-22")
ORIGINS = [2016, 2017, 2018, 2019, 2021, 2022]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def verify():
    manifest = json.loads((OUT / "manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha256_file(OUT / name) == digest, name
    for name, digest in manifest["sources"].items():
        assert sha256_file(Path(name)) == digest, name
    frame = pl.read_parquet(OUT / "scored-rows.parquet")
    oracle = pl.read_parquet(OUT / "hindsight-exposure-rows.parquet")
    assert frame.height == 26571
    assert sorted(frame["origin_year"].unique().to_list()) == ORIGINS
    assert set(oracle["origin_year"]) == {2018}
    for rows in (frame, oracle):
        for target in ("pa", "value"):
            np.testing.assert_allclose(rows[f"{target}_activity_contribution"] + rows[f"{target}_conditional_contribution"],
                rows[f"{target}_loss_11"] - rows[f"{target}_loss_00"], rtol=1e-10, atol=1e-8)
    assert not manifest["protected_outcomes_used"] and not manifest["forecast_changed"]
    print(json.dumps({"status": "verified", "rows": frame.height, "sources": len(manifest["sources"]),
                      "forecast_changed": False, "protected_outcomes_used": False}, indent=2))


def main():
    old_manifest = json.loads((PREVIOUS / "manifest.json").read_text())
    for name, digest in old_manifest["files"].items():
        assert sha256_file(PREVIOUS / name) == digest, name
    contract = json.loads(Path("docs/multiyear-hitter-v1-contract.json").read_text())
    assert sha256_file(V1 / "schedules.parquet") == contract["source_hashes"][str(V1 / "schedules.parquet")]
    sources = [PLAN, Path(__file__).relative_to(Path.cwd()), Path("src/universal_baseball/hitter_opportunity_calendar.py"),
        Path("src/universal_baseball/hitter_horizon_consistency.py"), Path("src/universal_baseball/multiyear_hitter_followup.py"),
        V1 / "outer-predictions.parquet", V1 / "schedules.parquet", V1 / "manifest.json",
        V2 / "opportunity-predictions.parquet", V2 / "forecast-2026-2028.parquet",
        PREVIOUS / "historical-predictions.parquet", PREVIOUS / "manifest.json",
        Path("docs/multiyear-hitter-v1-contract.json")]
    source_hashes = {str(p): sha256_file(p) for p in sources}
    history = pl.read_parquet(PREVIOUS / "historical-predictions.parquet")
    assert sorted(history["origin_year"].unique().to_list()) == [*ORIGINS, 2023]
    base = pl.read_parquet(V1 / "outer-predictions.parquet")
    assert sorted(base["origin_year"].unique().to_list()) == ORIGINS
    updates = pl.read_parquet(V2 / "opportunity-predictions.parquet").filter(
        (pl.col("horizon") == 2) & pl.col("origin_year").is_in(ORIGINS))
    matched = prepare_rows(history.filter(pl.col("origin_year").is_in(ORIGINS)), base, updates)
    groups = {"overall": np.ones(matched.height, dtype=bool), **fixed_groups(matched)}
    group_columns = {name: f"group_{i}" for i, name in enumerate(groups)}
    matched = matched.with_columns([pl.Series(group_columns[name], mask) for name, mask in groups.items()])
    scored = score_rows(matched)
    scopes = {"all": scored, "ordinary": scored.filter(pl.col("regime").is_in(["ordinary_pre", "ordinary_post"]))}
    scopes.update({name: scored.filter(pl.col("regime") == name) for name in sorted(scored["regime"].unique())})
    results = {}
    for scope, rows in scopes.items():
        records = {}
        for name, col in group_columns.items():
            group = rows.filter(pl.col(col))
            if group.is_empty():
                continue
            record = summarize(group)
            record["supported_multiorigin"] = group.height >= 100 and group["origin_year"].n_unique() >= 3
            if scope in ("all", "ordinary") and name in ("overall", "Top50", "Top50 under26") and record["supported_multiorigin"]:
                record["paired_pa_mse"] = compare_losses(group, "pa_loss_11", "pa_loss_00")
            records[name] = record
        results[scope] = records
        print(f"Scored saved heads: {scope}", flush=True)
    schedules = pl.read_parquet(V1 / "schedules.parquet")
    assert schedules["season"].max() <= 2025
    schedule = schedules.filter(pl.col("season") == 2020).to_dicts()
    assert len(schedule) == 1
    exposure = 2 * schedule[0]["completed_games"] / (162 * schedule[0]["teams"])
    oracle = score_rows(matched.filter(pl.col("origin_year") == 2018), exposure)
    oracle_groups = {name: summarize(oracle.filter(pl.col(col))) for name, col in group_columns.items()
                     if oracle.filter(pl.col(col)).height}
    report = {"status": "diagnostic_complete_no_promotion", "forecast_changed": False, "protected_outcomes_used": False,
        "scope": "Year-2 opportunity; value diagnostics hold batting-plus-replacement rate fixed, not full WAR",
        "rows": scored.height, "origins": ORIGINS, "excluded_opportunity_origin": {"origin": 2023,
            "rows": history.filter(pl.col("origin_year") == 2023).height,
            "reason": "No archived accepted-v2 opportunity replay; retained in previous seven-origin value result"},
        "group_columns": group_columns, "calendar_scopes": results,
        "per_origin": {str(y): {name: summarize(scored.filter((pl.col("origin_year") == y) & pl.col(col)))
            for name, col in group_columns.items() if scored.filter((pl.col("origin_year") == y) & pl.col(col)).height} for y in ORIGINS},
        "hindsight_exposure": {"label": "Not a forecast; activity unchanged, target-2020 conditional PA scaled after the fact",
            "schedule": schedule[0], "fraction": exposure, "groups": oracle_groups},
        "interpretation_limits": ["No model selected from head swaps", "Small and single-shock groups descriptive",
            "Player-cluster intervals do not measure uncertainty over new calendar shocks",
            "Ordinary post-pandemic windows can retain pandemic-affected input history",
            "Conditional active-player PA errors are not unconditional value accuracy", "Historical folds already exposed"]}
    assert all(sha256_file(Path(p)) == digest for p, digest in source_hashes.items())
    OUT.mkdir(parents=True, exist_ok=True)
    scored.write_parquet(OUT / "scored-rows.parquet")
    oracle.write_parquet(OUT / "hindsight-exposure-rows.parquet")
    write_json(OUT / "report.json", report)
    write_json(OUT / "manifest.json", {"status": report["status"], "forecast_changed": False, "protected_outcomes_used": False,
        "sources": source_hashes, "files": {name: sha256_file(OUT / name) for name in
            ("scored-rows.parquet", "hindsight-exposure-rows.parquet", "report.json")}})
    print(json.dumps({name: {"rows": results[name]["Top50"]["rows"],
        "old_pa_rmse": results[name]["Top50"]["old"]["pa_rmse"], "new_pa_rmse": results[name]["Top50"]["new"]["pa_rmse"],
        "old_pa_bias": results[name]["Top50"]["old"]["pa_error"], "new_pa_bias": results[name]["Top50"]["new"]["pa_error"],
        "head_swap": results[name]["Top50"]["pa_head_swap"]} for name in scopes}, indent=2))
    verify()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    if parser.parse_args().verify:
        verify()
    else:
        main()
