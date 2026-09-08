#!/usr/bin/env python
"""Score the fixed pitcher component baseline on disclosed completed seasons."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import log
from pathlib import Path

import polars as pl

from universal_baseball.pitcher_baseline import (
    PITCHER_COMPONENTS,
    build_pitcher_component_baseline,
    score_pitcher_component_rates,
)


MAX_AUTHORIZED_TARGET_SEASON = 2024


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pitching",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory/tables/"
            "mlb_pitching_2015_2024.parquet"
        ),
    )
    parser.add_argument("--first-target", type=int, default=2018)
    parser.add_argument("--last-target", type=int, default=2024)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/generated/pitcher-component-baseline"),
    )
    return parser.parse_args()


def _global_prior_log_loss(history: pl.DataFrame, target: pl.DataFrame) -> float:
    totals = {
        "so": int(history.get_column("pitching_so").sum()),
        "ubb": int(history.get_column("pitching_ubb").sum()),
        "hbp": int(history.get_column("pitching_hbp").sum()),
        "hr": int(history.get_column("pitching_hr").sum()),
    }
    history_bf = int(history.get_column("pitching_bf").sum())
    totals["other"] = history_bf - sum(totals.values())
    probabilities = {component: totals[component] / history_bf for component in PITCHER_COMPONENTS}
    target_totals = {
        "so": int(target.get_column("pitching_so").sum()),
        "ubb": int(target.get_column("pitching_ubb").sum()),
        "hbp": int(target.get_column("pitching_hbp").sum()),
        "hr": int(target.get_column("pitching_hr").sum()),
    }
    target_bf = int(target.get_column("pitching_bf").sum())
    target_totals["other"] = target_bf - sum(target_totals.values())
    return -sum(target_totals[c] * log(probabilities[c]) for c in PITCHER_COMPONENTS) / target_bf


def score_history(
    pitching_path: Path,
    *,
    first_target: int,
    last_target: int,
    output_dir: Path,
) -> dict[str, object]:
    if first_target > last_target:
        raise ValueError("first-target cannot exceed last-target")
    if last_target > MAX_AUTHORIZED_TARGET_SEASON:
        raise ValueError("target season exceeds protected development boundary")
    pitching = pl.read_parquet(pitching_path)
    required = {
        "season",
        "player_id",
        "pitching_games",
        "pitching_starts",
        "pitching_bf",
        "pitching_so",
        "pitching_ubb",
        "pitching_hbp",
        "pitching_hr",
    }
    if missing := sorted(required - set(pitching.columns)):
        raise ValueError(f"pitching inventory missing baseline fields: {missing}")

    output_dir.mkdir(parents=True, exist_ok=True)
    folds: list[dict[str, object]] = []
    predictions: list[pl.DataFrame] = []
    for target_season in range(first_target, last_target + 1):
        history = pitching.filter(
            pl.col("season").is_between(target_season - 3, target_season - 1)
        )
        target = pitching.filter(
            (pl.col("season") == target_season) & (pl.col("pitching_bf") > 0)
        )
        if history.is_empty() or target.is_empty():
            raise ValueError(f"missing pitcher history or target for {target_season}")
        target_players = target.select("player_id").unique().sort("player_id")
        forecast = build_pitcher_component_baseline(
            target_players,
            history,
            forecast_season=target_season,
        )
        metrics = score_pitcher_component_rates(forecast, target)
        global_nll = _global_prior_log_loss(history, target)
        prior_ids = set(history.get_column("player_id").to_list())
        new_target_players = sum(
            int(player_id) not in prior_ids
            for player_id in target_players.get_column("player_id").to_list()
        )
        folds.append(
            {
                "target_season": target_season,
                **metrics,
                "global_population_log_loss": global_nll,
                "component_log_loss_improvement": global_nll
                - float(metrics["bf_weighted_component_log_loss"]),
                "target_pitchers_without_prior_three_year_bf": new_target_players,
            }
        )
        predictions.append(forecast)

    prediction_frame = pl.concat(predictions, how="vertical").sort(
        ["forecast_season", "player_id"]
    )
    prediction_path = output_dir / "predictions.parquet"
    prediction_frame.write_parquet(prediction_path)
    report: dict[str, object] = {
        "report_schema_version": 1,
        "status": "fixed_pitcher_component_baseline_development_score",
        "target_seasons": list(range(first_target, last_target + 1)),
        "protected_2026_accessed": False,
        "target_membership_used_as_predictor": False,
        "target_membership_used_for_rate_scoring_only": True,
        "opportunity_or_workload_claim": False,
        "regression_bf": 200.0,
        "role_regression_games": 20.0,
        "folds": folds,
        "equal_fold_mean_component_log_loss": sum(
            float(fold["bf_weighted_component_log_loss"]) for fold in folds
        )
        / len(folds),
        "equal_fold_mean_global_log_loss": sum(
            float(fold["global_population_log_loss"]) for fold in folds
        )
        / len(folds),
        "outputs": {
            "predictions": prediction_path.as_posix(),
            "predictions_sha256": sha256(prediction_path.read_bytes()).hexdigest(),
        },
        "limitations": [
            "Target-season pitcher membership is used only to define the rate-scoring cohort.",
            "This does not forecast MLB arrival, workload, role transition, WAR, or value.",
            "The 200 BF and 20 game prior strengths are transparent defaults, not selected optima.",
            "The 2020 shortened season is retained as real chronological evidence.",
        ],
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    args = _args()
    report = score_history(
        args.pitching,
        first_target=args.first_target,
        last_target=args.last_target,
        output_dir=args.output_dir,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "equal_fold_mean_component_log_loss": report[
                    "equal_fold_mean_component_log_loss"
                ],
                "equal_fold_mean_global_log_loss": report["equal_fold_mean_global_log_loss"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
