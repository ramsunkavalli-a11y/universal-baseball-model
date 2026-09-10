#!/usr/bin/env python3
"""Validate prospect transition-weighted positional runs on an outer cohort."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_prospect_position_transition import _cohort
from materialize_prospect_position_value_sensitivity import _group_position_runs
from universal_baseball.player_value_positional_adjustment import POSITIONAL_RUNS_PER_162


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--transition-result", type=Path,
        default=Path("docs/prospect-position-transition-result.json"),
    )
    parser.add_argument(
        "--historical-path", type=Path,
        default=Path(
            "reports/generated/position-capacity-source/historical/reports/generated/"
            "position-role-historical-source/tables/historical_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-path", type=Path,
        default=Path(
            "reports/generated/position-capacity-source/2025/reports/generated/"
            "position-role-2025-confirmation-source/tables/"
            "position_role_2025_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-positional-runs-validation-result.json"),
    )
    return parser.parse_args()


def _weighted_runs(frame: pl.DataFrame, *, output: str) -> pl.DataFrame:
    return (
        frame.filter(
            pl.col("position_abbreviation").is_in(list(POSITIONAL_RUNS_PER_162))
        )
        .with_columns(
            pl.when(pl.col("games_started") > 0)
            .then(pl.col("games_started"))
            .otherwise(pl.col("games_played"))
            .alias("exposure"),
            pl.col("position_abbreviation")
            .replace_strict(dict(POSITIONAL_RUNS_PER_162), return_dtype=pl.Float64)
            .alias("runs"),
        )
        .group_by("player_id")
        .agg(
            ((pl.col("runs") * pl.col("exposure")).sum() / pl.col("exposure").sum())
            .alias(output)
        )
    )


def _scores(target: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = prediction - target
    return {
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
        "bias": float(error.mean()),
    }


def _bootstrap(
    target: np.ndarray, baseline: np.ndarray, candidate: np.ndarray
) -> dict[str, object]:
    rng = np.random.default_rng(20260909)
    indices = rng.integers(0, len(target), size=(2_000, len(target)))
    baseline_error = baseline[indices] - target[indices]
    candidate_error = candidate[indices] - target[indices]
    mae = np.abs(candidate_error).mean(axis=1) - np.abs(baseline_error).mean(axis=1)
    rmse = np.sqrt(np.square(candidate_error).mean(axis=1)) - np.sqrt(
        np.square(baseline_error).mean(axis=1)
    )

    def summary(values: np.ndarray, estimate: float) -> dict[str, float]:
        return {
            "difference": estimate,
            "ci_low": float(np.quantile(values, 0.025)),
            "ci_high": float(np.quantile(values, 0.975)),
            "probability_candidate_better": float(np.mean(values < 0)),
        }

    baseline_score = _scores(target, baseline)
    candidate_score = _scores(target, candidate)
    return {
        "resamples": 2_000,
        "mae": summary(mae, candidate_score["mae"] - baseline_score["mae"]),
        "rmse": summary(rmse, candidate_score["rmse"] - baseline_score["rmse"]),
    }


def main() -> int:
    args = _args()
    usage = pl.concat(
        [pl.read_parquet(args.historical_path), pl.read_parquet(args.confirmation_path)],
        how="vertical_relaxed",
    )
    cohort = _cohort(usage, 2023).select("player_id", "origin_group")
    origin = _weighted_runs(
        usage.filter(
            (pl.col("season") == 2023) & (pl.col("level_group") != "MLB")
        ),
        output="baseline_runs",
    )
    target = _weighted_runs(
        usage.filter(
            pl.col("season").is_between(2024, 2025)
            & (pl.col("level_group") == "MLB")
        ),
        output="target_runs",
    )
    transition = json.loads(args.transition_result.read_text(encoding="utf-8"))
    probabilities = transition["outer"]["transition_probabilities"]
    group_runs = _group_position_runs(usage)
    rows = cohort.join(origin, on="player_id", how="inner").join(
        target, on="player_id", how="inner"
    ).with_columns(
        pl.col("origin_group").map_elements(
            lambda origin_group: sum(
                probabilities[origin_group][destination] * group_runs[destination]
                for destination in probabilities[origin_group]
            ),
            return_dtype=pl.Float64,
        ).alias("candidate_runs")
    ).sort("player_id")
    actual = rows.get_column("target_runs").to_numpy()
    baseline = rows.get_column("baseline_runs").to_numpy()
    candidate = rows.get_column("candidate_runs").to_numpy()
    by_group = []
    for group in sorted(rows.get_column("origin_group").unique().to_list()):
        cell = rows.filter(pl.col("origin_group") == group)
        y = cell.get_column("target_runs").to_numpy()
        base = cell.get_column("baseline_runs").to_numpy()
        challenge = cell.get_column("candidate_runs").to_numpy()
        by_group.append(
            {
                "origin_group": group,
                "players": cell.height,
                "baseline": _scores(y, base),
                "candidate": _scores(y, challenge),
            }
        )
    baseline_scores = _scores(actual, baseline)
    candidate_scores = _scores(actual, candidate)
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "prospect_positional_runs_outer_validation_complete",
        "contract": "docs/prospect-positional-runs-validation-plan.md",
        "players": rows.height,
        "baseline": baseline_scores,
        "candidate": candidate_scores,
        "paired_bootstrap": _bootstrap(actual, baseline, candidate),
        "by_origin_group": by_group,
        "decision": {
            "positional_run_component_passed": (
                candidate_scores["mae"] < baseline_scores["mae"]
                and candidate_scores["rmse"] < baseline_scores["rmse"]
            ),
            "full_value_change_authorized": False,
        },
        "boundaries": {
            "outside_fv_used": False,
            "current_values_used": False,
            "organization_or_depth_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
