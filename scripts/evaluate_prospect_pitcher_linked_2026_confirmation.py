#!/usr/bin/env python3
"""Evaluate the frozen prospect-pitcher linked path after final 2026 totals."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)
from universal_baseball.player_value_uncertainty import (
    sample_hurdle_plate_appearances,
)
from universal_baseball.prospect_workload_validation import empirical_crps
from universal_baseball.storage import sha256_file


PACKAGE = Path(
    "model_artifacts/prospect-pitcher-linked-2026-confirmation-forecast-2026-09-10"
)
DRAWS = 4096
BOOTSTRAPS = 2000
MASTER_SEED = 20260910


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-stats", type=Path, required=True)
    parser.add_argument("--schedule-report", type=Path, required=True)
    parser.add_argument("--package", type=Path, default=PACKAGE)
    parser.add_argument(
        "--output", type=Path,
        default=Path("reports/generated/prospect-pitcher-linked-2026-confirmation-result.json"),
    )
    return parser.parse_args()


def _verify_package(root: Path) -> dict[str, object]:
    report = json.loads((root / "report.json").read_text(encoding="utf-8"))
    if report["2026_outcomes_read"] is not False:
        raise ValueError("forecast package contains 2026 outcomes")
    for record in report["storage"].values():
        path = Path(str(record["path"]))
        if path.stat().st_size != record["file_size_bytes"] or sha256_file(path) != record["file_sha256"]:
            raise ValueError(f"forecast package hash mismatch: {path}")
    if sha256_file(Path(str(report["contract_path"]))) != report["contract_sha256"]:
        raise ValueError("confirmation contract hash mismatch")
    if sha256_file(Path(str(report["runner_path"]))) != report["runner_sha256"]:
        raise ValueError("forecast runner hash mismatch")
    return report


def _require_final_schedule(path: Path) -> None:
    report = json.loads(path.read_text(encoding="utf-8"))
    schedule = report.get("schedule")
    if not isinstance(schedule, dict):
        raise ValueError("schedule report lacks schedule evidence")
    if (
        int(schedule["completed_league_games"])
        != int(schedule["scheduled_league_games"])
        or abs(float(schedule["remaining_fraction"])) > 1e-12
    ):
        raise ValueError("2026 regular season is not complete")


def _observed_war(
    stats: pl.DataFrame, prospects: pl.DataFrame, *, runs_per_win: float
) -> pl.DataFrame:
    required = {
        "season", "player_id", "pitching_bf", "pitching_so", "pitching_ubb",
        "pitching_hbp", "pitching_hr",
    }
    if missing := sorted(required - set(stats.columns)):
        raise ValueError(f"target stats missing fields: {missing}")
    if stats.is_empty():
        raise ValueError("target stats are empty")
    if int(stats.get_column("season").max()) != 2026:
        raise ValueError("target stats must end in 2026")
    totals = stats.filter(pl.col("season") == 2026).group_by("player_id").agg(
        pl.col("pitching_bf").sum().alias("adjusted_workload")
    )
    paths = (
        prospects.select("player_id")
        .join(totals, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col("adjusted_workload").fill_null(0.0))
        .select(
            pl.col("player_id").alias("path_player_id"),
            pl.lit("pitcher").alias("player_type"),
            pl.lit("unknown").alias("outcome_tier_v2"),
            pl.lit("unknown").alias("career_role"),
            pl.lit(1).alias("path_year"),
            pl.lit(2026).alias("source_season"),
            "adjusted_workload",
            pl.when(pl.col("adjusted_workload") > 0)
            .then(pl.lit("unknown"))
            .otherwise(pl.lit("inactive"))
            .alias("annual_role"),
        )
    )
    return build_historical_pitcher_performance_paths(
        paths, stats, runs_per_win=runs_per_win
    ).select(
        pl.col("path_player_id").alias("player_id"),
        "observed_component_war",
    )


def _loss_rows(
    prospects: pl.DataFrame,
    linked_positive_war: np.ndarray,
    observed: pl.DataFrame,
    *,
    runs_per_win: float,
) -> pl.DataFrame:
    rows = []
    for row in prospects.join(observed, on="player_id", validate="1:1").iter_rows(named=True):
        player_id = int(row["player_id"])
        probability = float(row["predicted_any_mlb_bf_probability"])
        target = float(row["observed_component_war"])
        linked_values = np.concatenate(([0.0], linked_positive_war))
        linked_weights = np.concatenate(
            ([1.0 - probability], np.full(linked_positive_war.size, probability / linked_positive_war.size))
        )
        rng = np.random.default_rng(MASTER_SEED + player_id)
        workload = sample_hurdle_plate_appearances(
            rng,
            draws=DRAWS,
            participation_probability=probability,
            positive_truncated_mean=row["predicted_positive_mlb_bf_mean"],
            alpha=row["model_nb_alpha"],
        )
        mean = workload * float(row["conditional_war_per_800_bf"]) / 800.0
        run_variance = (
            workload * float(row["event_run_variance"])
            + np.maximum(0.0, workload**2 - workload)
            * float(row["posterior_run_rate_variance"])
        )
        incumbent_values = mean + rng.normal(size=DRAWS) * np.sqrt(run_variance) / runs_per_win
        linked_mean = float(np.sum(linked_values * linked_weights))
        incumbent_mean = float(row["expected_war"])
        rows.append(
            {
                "player_id": player_id,
                "observed_component_war": target,
                "linked_crps": empirical_crps(linked_values, linked_weights, target),
                "incumbent_crps": empirical_crps(
                    incumbent_values, np.ones(DRAWS), target
                ),
                "linked_squared_error": (linked_mean - target) ** 2,
                "incumbent_squared_error": (incumbent_mean - target) ** 2,
                "linked_error": linked_mean - target,
                "incumbent_error": incumbent_mean - target,
            }
        )
    return pl.DataFrame(rows)


def _paired(frame: pl.DataFrame, candidate: str, incumbent: str, seed: int) -> dict[str, float]:
    delta = (frame[candidate] - frame[incumbent]).to_numpy()
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, delta.size, size=(BOOTSTRAPS, delta.size))
    means = delta[indices].mean(axis=1)
    return {
        "difference": float(delta.mean()),
        "ci_low": float(np.quantile(means, 0.025)),
        "ci_high": float(np.quantile(means, 0.975)),
    }


def main() -> int:
    args = _args()
    report = _verify_package(args.package)
    _require_final_schedule(args.schedule_report)
    prospects = pl.read_parquet(args.package / "prospect-forecast-inputs.parquet")
    linked = pl.read_parquet(args.package / "linked-positive-paths.parquet")
    stats = pl.read_parquet(args.target_stats)
    observed = _observed_war(stats, prospects, runs_per_win=float(report["runs_per_win"]))
    losses = _loss_rows(
        prospects,
        linked["observed_component_war"].to_numpy(),
        observed,
        runs_per_win=float(report["runs_per_win"]),
    )
    crps = _paired(losses, "linked_crps", "incumbent_crps", MASTER_SEED + 1)
    mse = _paired(
        losses, "linked_squared_error", "incumbent_squared_error", MASTER_SEED + 2
    )
    linked_bias = float(losses["linked_error"].mean())
    incumbent_bias = float(losses["incumbent_error"].mean())
    subgroup = (
        losses.join(
            prospects.select("player_id", "as_of_level_group"),
            on="player_id",
            validate="1:1",
        )
        .group_by("as_of_level_group")
        .agg(
            pl.len().alias("players"),
            pl.col("linked_crps").mean(),
            pl.col("incumbent_crps").mean(),
        )
        .filter(pl.col("players") >= 100)
        .sort("as_of_level_group")
    )
    subgroup_passed = subgroup.filter(
        pl.col("linked_crps") > pl.col("incumbent_crps") * 1.05
    ).is_empty()
    gates = {
        "paired_crps_upper_below_zero": crps["ci_high"] < 0,
        "paired_mse_upper_below_zero": mse["ci_high"] < 0,
        "absolute_bias_no_worse": abs(linked_bias) <= abs(incumbent_bias),
        "supported_subgroups_passed": subgroup_passed,
    }
    result = {
        "report_schema_version": "0.1",
        "status": "confirmed" if all(gates.values()) else "not_confirmed",
        "players": losses.height,
        "simulation_draws": DRAWS,
        "bootstrap_draws": BOOTSTRAPS,
        "crps": crps,
        "squared_error": mse,
        "linked_bias": linked_bias,
        "incumbent_bias": incumbent_bias,
        "gates": gates,
        "supported_level_groups": subgroup.to_dicts(),
        "production_changed": False,
        "target_stats_sha256": sha256_file(args.target_stats),
        "schedule_report_sha256": sha256_file(args.schedule_report),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
