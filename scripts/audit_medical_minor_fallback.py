"""Append an outcome-blind DSL control without altering the fixed comparison."""

from pathlib import Path

import numpy as np
import polars as pl

import test_repaired_medical_opportunity as run
from universal_baseball.storage import sha256_file


def main():
    run.verify(run.read(run.OUT / "preflight.json")["hashes"])
    run.verify(run.read(run.PUBLIC / "player-walks.json")["hashes"])
    selection = run.PUBLIC / "minor-fallback-selection.json"
    receipt = run.PUBLIC / "minor-fallback-review.json"
    assert not selection.exists() and not receipt.exists()
    f = pl.read_parquet(run.OUT / "features-0.parquet")
    # Project only origin evidence before selecting; no target or prediction access.
    candidates = f.select(
        "row_id", "player_id", "origin_year", "prior_debut", "DSL_0_pa", "age"
    ).filter(
        (pl.col("origin_year") == 2024)
        & (pl.col("prior_debut") == 0)
        & (pl.col("DSL_0_pa") > 0)
    )
    focal = candidates.sort("row_id").row(0, named=True)
    peers = candidates.filter(pl.col("row_id") != focal["row_id"]).with_columns(
        (
            ((pl.col("age") - focal["age"]) / 5) ** 2
            + ((pl.col("DSL_0_pa") - focal["DSL_0_pa"]) / 300) ** 2
        ).alias("distance")
    ).sort("distance", "row_id").head(3)
    ids = [focal["row_id"], *peers["row_id"].to_list()]
    run.save(selection, dict(
        rule="2024 no-debut DSL: smallest row ID, three nearest age/DSL-PA peers",
        selected_before_prediction_and_outcome_access=True,
        row_ids=ids,
        replaces_original_cases=False,
        hashes={str(run.OUT / "features-0.parquet"): sha256_file(run.OUT / "features-0.parquet")},
    ))
    q = pl.read_parquet(run.OUT / "predictions.parquet")
    minor = q.filter(pl.col("prior_debut") == 0)
    assert not minor["med_eligible"].any() and not minor["medical_applied"].any()
    for arm in run.ARMS:
        for field in ["p", "conditional_pa", "pa", "value"]:
            assert np.array_equal(minor[arm + "_" + field], minor["observation_" + field])
    dated = run.GEN / "practical-hitter-v31/dated-stints.parquet"
    stats = pl.read_parquet(dated)
    cases = []
    for row_id in ids:
        r = q.filter(pl.col("row_id") == row_id).row(0, named=True)
        source = pl.read_parquet(run.OUT / f"features-{r['outer_fold']}.parquet").filter(
            pl.col("row_id") == row_id
        )
        assert not source["med_eligible"].item()
        history = stats.filter(
            (pl.col("player_id") == r["player_id"])
            & pl.col("season").is_between(r["origin_year"] - 2, r["origin_year"])
        ).select("season", "bucket", "plate_appearances", "home_runs", "strike_outs", "base_on_balls")
        cases.append(dict(
            row={k: r[k] for k in ["row_id", "player_id", "player_name", "origin_year", "ctx_information_date", "age", "stage", "next_pa", "actual_relative_value"]},
            stats=history.sort("season", "bucket").to_dicts(),
            source=source.select("observation_state", "recent_history_coverage_complete", "recent_episode_count", "med_eligible").to_dicts(),
            forecasts={arm: {field: r[arm + "_" + field] for field in ["p", "conditional_pa", "pa", "value"]} for arm in ["observation", *run.ARMS]},
            healthy_state_inferred=False,
        ))
    run.protections()
    run.save(receipt, dict(
        cases=cases,
        no_debut_forecasts=minor.height,
        exact_fallback_all_no_debut_forecasts=True,
        new_fits=0,
        hashes={str(p): sha256_file(p) for p in [Path(__file__), selection, dated, run.OUT / "predictions.parquet", *[run.OUT / f"features-{k}.parquet" for k in range(5)]]},
    ))
    print(f"DSL fallback traced for {cases[0]['row']['player_name']}; all {minor.height} no-debut forecasts unchanged")


if __name__ == "__main__":
    main()
