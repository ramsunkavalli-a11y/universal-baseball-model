#!/usr/bin/env python3
"""Diagnose the frozen position-role challenger failure without fitting a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.position_role_profile import BATTING_ROLE_POSITIONS


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {filename!r} below {root}, found {len(matches)}")
    return matches[0]


def _metric_summary(frame: pl.DataFrame, by: list[str]) -> list[dict[str, object]]:
    return (
        frame.group_by(by)
        .agg(
            pl.len().alias("player_count"),
            pl.col("baseline_tv").mean().alias("baseline_mean_tv"),
            pl.col("candidate_tv").mean().alias("candidate_mean_tv"),
            pl.col("tv_delta").mean().alias("mean_tv_delta_candidate_minus_baseline"),
            pl.col("baseline_sse").mean().alias("baseline_mean_sse"),
            pl.col("candidate_sse").mean().alias("candidate_mean_sse"),
            pl.col("sse_delta").mean().alias("mean_sse_delta_candidate_minus_baseline"),
            pl.col("candidate_tv_improved").mean().alias("candidate_tv_improved_rate"),
            pl.col("candidate_sse_improved").mean().alias("candidate_sse_improved_rate"),
            pl.col("candidate_movement_tv").mean().alias("mean_candidate_movement_tv"),
            pl.col("current_primary_share").mean().alias("mean_current_primary_share"),
        )
        .sort(by)
        .to_dicts()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/position-role-transition-diagnostic"),
    )
    args = parser.parse_args()

    predictions = pl.read_parquet(_find_one(args.source_root, "predictions.parquet"))
    means = pl.read_parquet(_find_one(args.source_root, "transition_means.parquet"))

    current_cols = [f"current_{position}" for position in BATTING_ROLE_POSITIONS]
    candidate_cols = [f"candidate_{position}" for position in BATTING_ROLE_POSITIONS]
    predictions = predictions.with_columns(
        (pl.col("candidate_tv") - pl.col("baseline_tv")).alias("tv_delta"),
        (pl.col("candidate_sse") - pl.col("baseline_sse")).alias("sse_delta"),
        (pl.col("candidate_tv") < pl.col("baseline_tv")).alias("candidate_tv_improved"),
        (pl.col("candidate_sse") < pl.col("baseline_sse")).alias("candidate_sse_improved"),
        (pl.col("current_primary_position") != pl.col("observed_primary_position")).alias(
            "observed_primary_changed"
        ),
        (
            0.5
            * sum(
                (pl.col(candidate) - pl.col(current)).abs()
                for candidate, current in zip(candidate_cols, current_cols, strict=True)
            )
        ).alias("candidate_movement_tv"),
        pl.when(pl.col("current_primary_share") < 0.50)
        .then(pl.lit("lt_0.50"))
        .when(pl.col("current_primary_share") < 0.65)
        .then(pl.lit("0.50_to_0.65"))
        .when(pl.col("current_primary_share") < 0.75)
        .then(pl.lit("0.65_to_0.75"))
        .when(pl.col("current_primary_share") < 0.85)
        .then(pl.lit("0.75_to_0.85"))
        .otherwise(pl.lit("ge_0.85"))
        .alias("primary_share_bin"),
    )

    mean_rows: list[dict[str, object]] = []
    for row in means.iter_rows(named=True):
        values = sorted(
            (
                (position, float(row[f"mean_next_{position}"]))
                for position in BATTING_ROLE_POSITIONS
            ),
            key=lambda item: item[1],
            reverse=True,
        )
        mean_rows.append(
            {
                "evaluation_current_season": int(row["evaluation_current_season"]),
                "evaluation_next_season": int(row["evaluation_next_season"]),
                "current_primary_position": str(row["current_primary_position"]),
                "training_transition_count": int(row["training_transition_count"]),
                "top1_destination": values[0][0],
                "top1_probability": values[0][1],
                "top2_destination": values[1][0],
                "top2_probability": values[1][1],
                "top3_destination": values[2][0],
                "top3_probability": values[2][1],
                "top3_probability_mass": sum(value for _, value in values[:3]),
                "outside_top3_probability_mass": 1.0 - sum(value for _, value in values[:3]),
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "position_role_transition_challenger_postmortem",
        "source_run_id": 32152125644,
        "source_artifact_digest": "sha256:4e98081cb1800d45f3668595e4e61a169dbce68a8b565aa1e8f60d7dcd1417e5",
        "boundary": {
            "2025_position_source_accessed": False,
            "new_candidate_scored": False,
            "hyperparameter_selected": False,
            "model_fit": False,
        },
        "by_fold_and_primary_position": _metric_summary(
            predictions, ["current_season", "next_season", "current_primary_position"]
        ),
        "by_fold_and_primary_share_bin": _metric_summary(
            predictions, ["current_season", "next_season", "primary_share_bin"]
        ),
        "by_fold_and_observed_primary_changed": _metric_summary(
            predictions, ["current_season", "next_season", "observed_primary_changed"]
        ),
        "transition_mean_sparsity": mean_rows,
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
