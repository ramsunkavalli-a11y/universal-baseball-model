#!/usr/bin/env python3
"""Test the roster-improved workload inside the selected partial-value stack."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


COMPONENT_PATH = Path(
    "reports/generated/hitter-value-components-chronological-v2/"
    "chronological-predictions.parquet"
)
WORKLOAD_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "chronological-predictions.parquet"
)
OUTPUT_ROOT = Path("reports/generated/hitter-roster-workload-value-v2")
RUNS_PER_WIN = 10.0


def _segment(frame: pl.DataFrame) -> dict[str, object]:
    actual = frame["actual_partial_war"].to_numpy()
    baseline = frame["prediction_selected_partial_war"].to_numpy()
    challenger = frame["prediction_roster_workload_partial_war"].to_numpy()
    return {
        "rows": frame.height,
        "baseline": regression_metrics(actual, baseline),
        "roster_workload": regression_metrics(actual, challenger),
        "challenger_minus_baseline_rmse": (
            regression_metrics(actual, challenger)["rmse"]
            - regression_metrics(actual, baseline)["rmse"]
        ),
    }


def main() -> None:
    components = pl.read_parquet(COMPONENT_PATH)
    workload = pl.read_parquet(WORKLOAD_PATH).select(
        "origin_year",
        "player_id",
        "prediction_roster_expected_pa",
        "roster_lag0__on_40man",
    )
    frame = (
        components.join(
            workload,
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            (
                pl.col("prediction_roster_expected_pa")
                / 600.0
                * pl.col("predicted_position_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_roster_position_war"),
            (
                pl.col("prediction_roster_expected_pa")
                / 600.0
                * pl.col("steal_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_roster_steal_war"),
            (
                pl.col("prediction_roster_expected_pa")
                / 600.0
                * pl.col("advancement_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_roster_advancement_war"),
        )
        .with_columns(
            (
                pl.col("prediction_batting_replacement_war")
                + pl.col("prediction_roster_position_war")
                + pl.col("prediction_roster_steal_war")
                + pl.col("prediction_roster_advancement_war")
            ).alias("prediction_roster_workload_partial_war")
        )
        .sort("origin_year", "player_id")
    )
    if frame.filter(pl.col("prediction_roster_expected_pa").is_null()).height:
        raise ValueError("roster workload does not cover the component population")

    actual = frame["actual_partial_war"].to_numpy()
    baseline = frame["prediction_selected_partial_war"].to_numpy()
    challenger = frame["prediction_roster_workload_partial_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    by_origin = {
        str(origin + 1): _segment(frame.filter(pl.col("origin_year") == origin))
        for origin in sorted(frame["origin_year"].unique().to_list())
    }
    by_stage = {
        stage: _segment(frame.filter(pl.col("player_stage") == stage))
        for stage in ("current_mlb", "upper_minors", "lower_minors")
    }
    by_membership = {
        "on_40man": _segment(frame.filter(pl.col("roster_lag0__on_40man") == 1)),
        "not_on_40man": _segment(
            frame.filter(pl.col("roster_lag0__on_40man") == 0)
        ),
    }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "chronological-predictions.parquet",
        table_name="hitter_roster_workload_value_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_roster_workload_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "population_rows": frame.height,
        "target_seasons": [2022, 2023, 2024, 2025],
        "target": "next-season MLB batting plus replacement plus position plus baserunning WAR",
        "architecture": (
            "batting forecast remains roster-blind; roster-improved expected PA scales "
            "only position and baserunning"
        ),
        "metrics": {
            "baseline": regression_metrics(actual, baseline),
            "roster_workload": regression_metrics(actual, challenger),
        },
        "paired_challenger_minus_baseline": paired_cluster_rmse_delta(
            actual,
            challenger,
            baseline,
            player_ids,
        ),
        "by_target_season": by_origin,
        "by_player_stage": by_stage,
        "by_origin_40man_membership": by_membership,
        "sources": {
            "components": {
                "path": str(COMPONENT_PATH),
                "sha256": sha256_file(COMPONENT_PATH),
            },
            "roster_workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "The common position/baserunning history begins with the 2022 target season.",
            "General and catcher defense remain neutral.",
            "2026 outcomes remain sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
