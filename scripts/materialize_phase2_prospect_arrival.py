#!/usr/bin/env python3
"""Fit, evaluate and score the Phase 2 cumulative prospect-arrival model."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_arrival import (
    ARRIVAL_MODEL_ID,
    build_arrival_cohort,
    build_current_arrival_predictors,
    fit_arrival_model,
    predict_arrival,
    probability_metrics,
    six_year_probability,
)
from universal_baseball.storage import write_canonical_parquet


TRAINING_YEARS = (2018, 2021, 2022, 2023)
EVALUATION_SPECS = ((2021, (2018,)), (2022, (2018,)), (2023, (2018, 2021)))


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--membership-path", type=Path,
        default=Path(
            "reports/generated/opportunity-40man-history/tables/"
            "historical_40man_membership.parquet"
        ),
    )
    parser.add_argument(
        "--skill-root", type=Path,
        default=Path("reports/generated/phase2-arrival-skill-source/tables"),
    )
    parser.add_argument(
        "--current-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--control-root", type=Path, default=Path("reports/generated/league-control"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-prospect-arrival"),
    )
    return parser.parse_args()


def _history_stats(root: Path) -> pl.DataFrame:
    paths = sorted(root.glob("*/affiliated_season_stats.parquet"))
    if not paths:
        raise FileNotFoundError("no affiliated history tables")
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _evaluate(
    cohorts: dict[int, pl.DataFrame], *, player_type: str,
    target_column: str = "arrived_within_horizon", outcome_name: str = "arrival",
) -> tuple[dict[str, object], bool]:
    scores = []
    fold_rows = []
    for evaluation_year, training_years in EVALUATION_SPECS:
        training = pl.concat([cohorts[year] for year in training_years])
        fit = fit_arrival_model(
            training, player_type=player_type,
            target_column=target_column, outcome_name=outcome_name,
        )
        scored = predict_arrival(fit, cohorts[evaluation_year]).with_columns(
            pl.lit(evaluation_year).alias("snapshot_year")
        )
        scores.append(scored)
        fold_rows.append(
            {
                "snapshot_year": evaluation_year,
                "training_years": list(training_years),
                "players": scored.height,
                "model": probability_metrics(
                    scored, f"predicted_two_year_{outcome_name}_probability",
                    observed_column=target_column,
                ),
                "baseline": probability_metrics(
                    scored, f"baseline_two_year_{outcome_name}_probability",
                    observed_column=target_column,
                ),
            }
        )
    pooled = pl.concat(scores)
    model = probability_metrics(
        pooled, f"predicted_two_year_{outcome_name}_probability",
        observed_column=target_column,
    )
    baseline = probability_metrics(
        pooled, f"baseline_two_year_{outcome_name}_probability",
        observed_column=target_column,
    )
    fold_wins = all(
        row["model"]["brier"] < row["baseline"]["brier"]
        and row["model"]["log_loss"] < row["baseline"]["log_loss"]
        for row in fold_rows
    )
    passed = (
        model["brier"] < baseline["brier"]
        and model["log_loss"] < baseline["log_loss"]
        and fold_wins
    )
    return {"folds": fold_rows, "pooled_model": model, "pooled_baseline": baseline}, passed


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    stats = _history_stats(args.history_root)
    hitter_skill = pl.read_parquet(
        args.skill_root / "affiliated_hitting_components.parquet"
    )
    pitcher_skill = pl.read_parquet(
        args.skill_root / "affiliated_pitching_components.parquet"
    )
    membership = pl.read_parquet(args.membership_path)
    current_stats = pl.read_parquet(args.current_root / "affiliated_season_stats.parquet")
    control = pl.read_parquet(
        args.control_root / dated / "league-control-snapshot.parquet"
    )
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    reports: dict[str, object] = {}
    storage: dict[str, object] = {}
    for player_type in ("hitter", "pitcher"):
        snapshots = pl.read_parquet(
            args.history_root / f"{player_type}_snapshots.parquet"
        )
        skill = hitter_skill if player_type == "hitter" else pitcher_skill
        cohorts = {
            year: build_arrival_cohort(
                snapshots, stats, membership, skill,
                snapshot_year=year, horizon=2,
                player_type=player_type,
            )
            for year in TRAINING_YEARS
        }
        evaluation, passed = _evaluate(cohorts, player_type=player_type)
        role_evaluation, role_passed = _evaluate(
            cohorts, player_type=player_type,
            target_column="meaningful_role_within_horizon",
            outcome_name="meaningful_role",
        )
        fit = fit_arrival_model(
            pl.concat([cohorts[year] for year in TRAINING_YEARS]),
            player_type=player_type,
        )
        current_snapshot = pl.read_parquet(
            args.current_root / f"{player_type}_snapshot.parquet"
        )
        predictors = build_current_arrival_predictors(
            current_snapshot, current_stats, control, skill, player_type=player_type
        )
        scored = predict_arrival(fit, predictors)
        role_fit = fit_arrival_model(
            pl.concat([cohorts[year] for year in TRAINING_YEARS]),
            player_type=player_type,
            target_column="meaningful_role_within_horizon",
            outcome_name="meaningful_role",
        )
        scored = predict_arrival(role_fit, scored)
        selected = (
            "predicted_two_year_arrival_probability"
            if passed else "baseline_two_year_arrival_probability"
        )
        selected_role = (
            "predicted_two_year_meaningful_role_probability"
            if role_passed else "baseline_two_year_meaningful_role_probability"
        )
        scored = scored.with_columns(
            pl.col(selected).map_elements(
                six_year_probability, return_dtype=pl.Float64
            ).alias("predicted_six_year_arrival_probability"),
            pl.col(selected_role).map_elements(
                six_year_probability, return_dtype=pl.Float64
            ).alias("predicted_six_year_meaningful_role_probability"),
            pl.lit("logistic" if passed else "level_baseline").alias("selected_form"),
            pl.lit(ARRIVAL_MODEL_ID).alias("arrival_model_id"),
        )
        path = output / f"{player_type}-arrival-probabilities.parquet"
        storage[player_type] = write_canonical_parquet(
            scored, path, table_name=f"phase2_{player_type}_arrival_probabilities"
        ).as_record()
        reports[player_type] = {
            "selected_form": "logistic" if passed else "level_baseline",
            "gate_passed": passed, "training_cohorts": list(TRAINING_YEARS),
            "training_players": sum(cohorts[year].height for year in TRAINING_YEARS),
            "current_players": scored.height, "evaluation": evaluation,
            "meaningful_role_gate_passed": role_passed,
            "meaningful_role_evaluation": role_evaluation,
            "mean_current_six_year_probability": float(
                scored.get_column("predicted_six_year_arrival_probability").mean()
            ),
            "mean_current_six_year_meaningful_role_probability": float(
                scored.get_column(
                    "predicted_six_year_meaningful_role_probability"
                ).mean()
            ),
        }
    report = {
        "report_schema_version": "0.1", "gate": "phase2_pre_mlb_arrival",
        "as_of_date": dated, "model_id": ARRIVAL_MODEL_ID,
        "hitter": reports["hitter"], "pitcher": reports["pitcher"],
        "method": (
            "two-year cumulative MLB debut probability from age, broad level, position "
            "or pitching role, current production, workload, playing history and 40-man "
            "status; separately models any debut and a meaningful 200 PA/BF MLB season, "
            "then extrapolates each to three two-year windows"
        ),
        "boundaries": {
            "publication_grades_used": False, "future_team_depth_used": False,
            "organization_feature_used": False,
            "features": (
                "age, broad level, position/role, current and prior workload, "
                "playing-history length, current production rates, and 40-man status"
            ),
            "2018_prior_mlb_history_left_censored": True,
            "six_year_extrapolation_is_constant_two_year_hazard": True,
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
