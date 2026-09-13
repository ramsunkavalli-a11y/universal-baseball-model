#!/usr/bin/env python3
"""Test whether historical comparables support adding MLB positional value."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        VALIDATION_ORIGINS,
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from scripts.materialize_prospect_hitter_comparables import _outcomes
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        VALIDATION_ORIGINS,
        _cohort_features,
        _deduplicate,
        _sources,
    )
    from materialize_prospect_hitter_comparables import _outcomes
from universal_baseball.player_value_positional_adjustment import (
    SCHEDULE_ID,
)
from universal_baseball.historical_hitter_position import (
    position_war_by_player_origin,
)
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    score_hitter_comparables,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--fielding-path",
        type=Path,
        default=Path(
            "reports/generated/mlb-fielding-outcome-inventory-2004-2025/tables/"
            "mlb_fielding_usage_2004_2025.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-position-adjusted-outcome-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-position-adjusted-outcome-result.md"),
    )
    return parser.parse_args()


def _metrics(actual: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    error = prediction - actual
    return {
        "bias": float(error.mean()),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.square(error).mean())),
    }


def _cohort(
    snapshots: pl.DataFrame,
    skill: pl.DataFrame,
    hitting: pl.DataFrame,
    debut: pl.DataFrame,
    fielding: pl.DataFrame,
    *,
    origin: int,
    runs_per_win: float,
) -> pl.DataFrame:
    players = _cohort_features(
        snapshots, skill, debut, origin=origin, player_type="hitter"
    )
    batting = _outcomes(
        players,
        hitting,
        origin=origin,
        runs_per_win=runs_per_win,
        horizon=HORIZON,
    )
    position = position_war_by_player_origin(
        fielding,
        origin=origin,
        horizon=HORIZON,
        runs_per_win=runs_per_win,
    )
    return (
        players.join(batting, on="player_id", how="left", validate="1:1")
        .join(position, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("later_component_war").fill_null(0.0),
            pl.col("later_mlb_workload").fill_null(0.0),
            pl.col("later_position_runs").fill_null(0.0),
            pl.col("later_position_war").fill_null(0.0),
            pl.lit(origin).alias("origin_year"),
        )
        .with_columns(
            (pl.col("later_component_war") + pl.col("later_position_war")).alias(
                "later_position_adjusted_partial_war"
            )
        )
    )


def _score_outcome(reference: pl.DataFrame, target: pl.DataFrame, column: str) -> pl.DataFrame:
    scored_reference = reference.with_columns(
        pl.col(column).alias("later_component_war")
    )
    return score_hitter_comparables(
        scored_reference,
        target,
        comparable_count=DEFAULT_COMPARABLES,
    )


def _fold(reference: pl.DataFrame, target: pl.DataFrame) -> dict[str, object]:
    batting = _score_outcome(reference, target, "later_component_war").select(
        "player_id",
        pl.col("historical_component_war_4y").alias("predicted_batting_war"),
        "historical_arrival_rate_4y",
    )
    position = _score_outcome(reference, target, "later_position_war").select(
        "player_id",
        pl.col("historical_component_war_4y").alias("predicted_local_position_war"),
    )
    arrived = reference.filter(pl.col("later_mlb_workload") > 0)
    global_position_war_per_arrival = float(arrived["later_position_war"].mean())
    scored = (
        target.select(
            "player_id",
            "later_position_war",
            "later_position_adjusted_partial_war",
        )
        .join(batting, on="player_id", validate="1:1")
        .join(position, on="player_id", validate="1:1")
        .with_columns(
            (
                pl.col("historical_arrival_rate_4y")
                * global_position_war_per_arrival
            ).alias("predicted_global_position_war")
        )
        .with_columns(
            (
                pl.col("predicted_batting_war")
                + pl.col("predicted_local_position_war")
            ).alias("predicted_local_combined_war"),
            (
                pl.col("predicted_batting_war")
                + pl.col("predicted_global_position_war")
            ).alias("predicted_global_combined_war"),
        )
    )
    actual_position = scored["later_position_war"].to_numpy()
    actual_combined = scored["later_position_adjusted_partial_war"].to_numpy()
    position_local = _metrics(
        actual_position, scored["predicted_local_position_war"].to_numpy()
    )
    position_global = _metrics(
        actual_position, scored["predicted_global_position_war"].to_numpy()
    )
    combined_local = _metrics(
        actual_combined, scored["predicted_local_combined_war"].to_numpy()
    )
    combined_global = _metrics(
        actual_combined, scored["predicted_global_combined_war"].to_numpy()
    )
    passed = bool(
        position_local["mae"] < position_global["mae"]
        and position_local["rmse"] < position_global["rmse"]
        and combined_local["mae"] < combined_global["mae"]
        and combined_local["rmse"] < combined_global["rmse"]
    )
    return {
        "target_players": target.height,
        "reference_players": reference.height,
        "global_position_war_per_arrival": global_position_war_per_arrival,
        "position_component": {
            "global_baseline": position_global,
            "local_comparables": position_local,
        },
        "position_adjusted_partial_war": {
            "global_position_baseline": combined_global,
            "local_position_comparables": combined_local,
        },
        "passed": passed,
    }


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect position-adjusted outcome audit",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "Actual MLB position usage was converted with the repo's fixed positional schedule. "
        "The local candidate and global baseline use the same batting forecast and arrival "
        "probability; only the source of expected position value differs.",
        "",
        "| Target year | Position MAE | Baseline | Combined MAE | Baseline | Pass |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for origin, fold in report["folds"].items():
        position = fold["position_component"]
        combined = fold["position_adjusted_partial_war"]
        lines.append(
            f"| {origin} | {position['local_comparables']['mae']:.3f} | "
            f"{position['global_baseline']['mae']:.3f} | "
            f"{combined['local_position_comparables']['mae']:.3f} | "
            f"{combined['global_position_baseline']['mae']:.3f} | {fold['passed']} |"
        )
    lines += [
        "",
        "This remains partial value: defense quality and non-steal baserunning are absent. "
        "No public FV, rank, player name, or current-player result was used.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = _args()
    root = Path("reports/generated")
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    snapshots, skill, hitting, debut = _sources(root, "hitter")
    fielding = pl.read_parquet(args.fielding_path)
    cohorts = {
        origin: _cohort(
            snapshots,
            skill,
            hitting,
            debut,
            fielding,
            origin=origin,
            runs_per_win=runs_per_win,
        )
        for origin in REFERENCE_ORIGINS
    }
    folds: dict[str, object] = {}
    for target_origin in VALIDATION_ORIGINS:
        reference_origins = tuple(
            origin
            for origin in REFERENCE_ORIGINS
            if origin + HORIZON < target_origin
        )
        reference = _deduplicate([cohorts[origin] for origin in reference_origins])
        folds[str(target_origin)] = {
            "reference_origins": list(reference_origins),
            **_fold(reference, cohorts[target_origin]),
        }
    passed = all(bool(fold["passed"]) for fold in folds.values())
    report = {
        "status": "prospect_position_adjusted_outcome_audited",
        "as_of_date": args.as_of_date.isoformat(),
        "horizon_calendar_years": HORIZON,
        "position_schedule": SCHEDULE_ID,
        "shortened_2020_scale": 2.7,
        "outside_fv_used": False,
        "decision": "retain_position_component" if passed else "withhold_position_component",
        "folds": folds,
        "boundaries": {
            "position_usage_only": True,
            "defensive_quality_included": False,
            "baserunning_included": False,
            "player_specific_rules": False,
        },
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"decision": report["decision"], "folds": folds}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
