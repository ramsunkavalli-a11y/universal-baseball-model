#!/usr/bin/env python3
"""Test historical MiLB position as a general prospect-value component."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        _deduplicate,
        _sources,
    )
    from scripts.audit_prospect_position_adjusted_outcomes import (
        _cohort,
        _metrics,
        _score_outcome,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import (
        HORIZON,
        REFERENCE_ORIGINS,
        _deduplicate,
        _sources,
    )
    from audit_prospect_position_adjusted_outcomes import (
        _cohort,
        _metrics,
        _score_outcome,
    )
from universal_baseball.historical_hitter_position import origin_position_profiles


TARGET_ORIGINS = (2013, 2018, 2021)
GROUP_PRIOR_PLAYERS = 25.0


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--origin-fielding-path",
        type=Path,
        default=Path(
            "reports/generated/milb-fielding-origin-inventory/tables/"
            "milb_fielding_usage_at_origins.parquet"
        ),
    )
    parser.add_argument(
        "--mlb-fielding-path",
        type=Path,
        default=Path(
            "reports/generated/mlb-fielding-outcome-inventory-2004-2025/tables/"
            "mlb_fielding_usage_2004_2025.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-position-history-challenger-result.json"),
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=Path("docs/prospect-position-history-challenger-result.md"),
    )
    return parser.parse_args()


def _attach_origins(
    cohort: pl.DataFrame, fielding: pl.DataFrame, *, origin: int
) -> pl.DataFrame:
    return cohort.join(
        origin_position_profiles(fielding, season=origin),
        on="player_id",
        how="left",
        validate="1:1",
    )


def _position_predictions(reference: pl.DataFrame, target: pl.DataFrame) -> pl.DataFrame:
    reference = reference.filter(
        pl.col("origin_position").is_not_null()
        & (pl.col("later_mlb_workload") > 0)
    )
    if reference.is_empty():
        raise ValueError("position reference cannot be empty")
    overall = float(reference["later_position_war"].mean())
    levels = reference.group_by("primary_level_group").agg(
            pl.col("later_position_war").mean().alias("conditional_level_mean")
    )
    groups = reference.group_by("primary_level_group", "origin_position").agg(
        pl.len().alias("group_players"),
        pl.col("later_position_war").mean().alias("conditional_group_mean"),
    )
    return (
        target.select(
            "player_id",
            "primary_level_group",
            "origin_position",
            "historical_arrival_rate_4y",
        )
        .join(levels, on="primary_level_group", how="left", validate="m:1")
        .join(
            groups,
            on=["primary_level_group", "origin_position"],
            how="left",
            validate="m:1",
        )
        .with_columns(pl.col("conditional_level_mean").fill_null(overall))
        .with_columns(
            pl.when(pl.col("group_players").is_not_null())
            .then(
                (
                    pl.col("group_players") * pl.col("conditional_group_mean")
                    + GROUP_PRIOR_PLAYERS * pl.col("conditional_level_mean")
                )
                / (pl.col("group_players") + GROUP_PRIOR_PLAYERS)
            )
            .otherwise(pl.col("conditional_level_mean"))
            .alias("conditional_position_war")
        )
        .with_columns(
            (
                pl.col("historical_arrival_rate_4y")
                * pl.col("conditional_level_mean")
            ).alias("baseline_position_war"),
            (
                pl.col("historical_arrival_rate_4y")
                * pl.col("conditional_position_war")
            ).alias("predicted_position_war"),
        )
        .select(
            "player_id",
            "baseline_position_war",
            "predicted_position_war",
            pl.col("group_players").fill_null(0),
        )
    )


def _fold(reference: pl.DataFrame, target: pl.DataFrame) -> dict[str, object]:
    covered = target.drop_nulls(["origin_position"])
    batting = _score_outcome(reference, covered, "later_component_war").select(
        "player_id",
        pl.col("historical_component_war_4y").alias("predicted_batting_war"),
        "historical_arrival_rate_4y",
    )
    predictions = _position_predictions(
        reference,
        covered.join(
            batting.select("player_id", "historical_arrival_rate_4y"),
            on="player_id",
            validate="1:1",
        ),
    )
    scored = (
        covered.select(
            "player_id", "later_position_war", "later_position_adjusted_partial_war"
        )
        .join(batting, on="player_id", validate="1:1")
        .join(predictions, on="player_id", validate="1:1")
        .with_columns(
            (pl.col("predicted_batting_war") + pl.col("baseline_position_war")).alias(
                "baseline_combined_war"
            ),
            (pl.col("predicted_batting_war") + pl.col("predicted_position_war")).alias(
                "candidate_combined_war"
            ),
        )
    )
    actual_position = scored["later_position_war"].to_numpy()
    actual_combined = scored["later_position_adjusted_partial_war"].to_numpy()
    position_baseline = _metrics(
        actual_position, scored["baseline_position_war"].to_numpy()
    )
    position_candidate = _metrics(
        actual_position, scored["predicted_position_war"].to_numpy()
    )
    combined_baseline = _metrics(
        actual_combined, scored["baseline_combined_war"].to_numpy()
    )
    combined_candidate = _metrics(
        actual_combined, scored["candidate_combined_war"].to_numpy()
    )
    passed = bool(
        position_candidate["mae"] < position_baseline["mae"]
        and position_candidate["rmse"] < position_baseline["rmse"]
        and combined_candidate["mae"] < combined_baseline["mae"]
        and combined_candidate["rmse"] < combined_baseline["rmse"]
    )
    return {
        "reference_players": reference.height,
        "reference_position_coverage": float(
            reference["origin_position"].is_not_null().mean()
        ),
        "target_players": target.height,
        "target_position_players": covered.height,
        "target_position_coverage": covered.height / target.height,
        "position_component": {
            "level_baseline": position_baseline,
            "position_history_candidate": position_candidate,
        },
        "position_adjusted_partial_war": {
            "level_baseline": combined_baseline,
            "position_history_candidate": combined_candidate,
        },
        "passed": passed,
    }


def _markdown(report: dict[str, object]) -> str:
    lines = [
        "# Prospect position-history challenger",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        "A player's most-used official MiLB position is compared only with earlier MLB arrivals at the same level and position. Small groups shrink toward the level average, then conditional position value is multiplied by the separately estimated arrival probability.",
        "",
        "| Target | Coverage | Position MAE vs baseline | Combined MAE vs baseline | Pass |",
        "|---:|---:|---:|---:|---:|",
    ]
    for origin, fold in report["folds"].items():
        position = fold["position_component"]
        combined = fold["position_adjusted_partial_war"]
        lines.append(
            f"| {origin} | {fold['target_position_coverage']:.1%} | "
            f"{position['position_history_candidate']['mae']:.3f} vs {position['level_baseline']['mae']:.3f} | "
            f"{combined['position_history_candidate']['mae']:.3f} vs {combined['level_baseline']['mae']:.3f} | {fold['passed']} |"
        )
    lines += [
        "",
        "The 2008 target is excluded because StatsAPI has no 2003 MiLB fielding source. "
        "FV, public ranks, names and current-player results were not used.",
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
    origin_fielding = pl.read_parquet(args.origin_fielding_path)
    mlb_fielding = pl.read_parquet(args.mlb_fielding_path)
    cohorts = {
        origin: _attach_origins(
            _cohort(
                snapshots,
                skill,
                hitting,
                debut,
                mlb_fielding,
                origin=origin,
                runs_per_win=runs_per_win,
            ),
            origin_fielding,
            origin=origin,
        )
        for origin in REFERENCE_ORIGINS
        if origin != 2003
    }
    folds: dict[str, object] = {}
    for target_origin in TARGET_ORIGINS:
        reference_origins = tuple(
            origin
            for origin in cohorts
            if origin + HORIZON < target_origin
        )
        reference = _deduplicate([cohorts[origin] for origin in reference_origins])
        folds[str(target_origin)] = {
            "reference_origins": list(reference_origins),
            **_fold(reference, cohorts[target_origin]),
        }
    passed = all(bool(fold["passed"]) for fold in folds.values())
    report = {
        "status": "prospect_position_history_challenger_audited",
        "as_of_date": args.as_of_date.isoformat(),
        "target_origins": list(TARGET_ORIGINS),
        "group_prior_players": GROUP_PRIOR_PLAYERS,
        "decision": "promote_position_history" if passed else "withhold_position_history",
        "outside_fv_used": False,
        "folds": folds,
    }
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.output_md.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
