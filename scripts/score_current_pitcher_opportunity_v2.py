#!/usr/bin/env python3
"""Score the current universal pitcher set with the provisional v2 package."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_history_source import build_opportunity_snapshots
from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_predictors,
)
from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.playing_time_model import (
    build_playing_time_design,
    predict_playing_time_hurdle,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--current-source-root", type=Path, required=True)
    parser.add_argument("--membership-root", type=Path, required=True)
    parser.add_argument(
        "--package-root",
        type=Path,
        default=Path("model_artifacts/pitcher-opportunity-v2-development-2026-09-09"),
    )
    parser.add_argument(
        "--fallback-path",
        type=Path,
        default=Path(
            "reports/generated/current-opportunity-paths/2026-09-08/tables/"
            "pitcher_opportunity_paths.parquet"
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-pitcher-opportunity-v2"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    current_tables = args.current_source_root / "tables" / str(args.as_of_date.year)
    roster_path = current_tables / "full_roster_details.parquet"
    stats_path = current_tables / "affiliated_season_stats.parquet"
    membership_path = (
        args.membership_root / "tables" / "historical_40man_membership.parquet"
    )
    stats = pl.read_parquet(stats_path)
    _hitters, pitchers = build_opportunity_snapshots(pl.read_parquet(roster_path), stats)
    predictors = build_universal_pitcher_opportunity_predictors(
        pitchers,
        stats,
        pl.read_parquet(membership_path),
        snapshot_year=args.as_of_date.year,
    )
    package_report = json.loads(
        (args.package_root / "report.json").read_text(encoding="utf-8")
    )
    coefficients_path = args.package_root / "tables" / "selected_coefficients.parquet"
    standardization_path = (
        args.package_root / "tables" / "selected_standardization.parquet"
    )
    fit = load_frozen_playing_time_fit(
        pl.read_parquet(coefficients_path),
        pl.read_parquet(standardization_path),
        form=str(package_report["selected_form"]),
        expected_nb_alpha=float(package_report["selected_nb_alpha"]),
        participation_training_players=int(package_report["final_training_players"]),
        positive_training_players=int(package_report["final_positive_players"]),
    )
    raw = predict_playing_time_hurdle(
        fit, build_playing_time_design(predictors, form=fit.form)
    )
    predictions = raw.rename(
        {
            "predicted_any_mlb_pa_probability": "predicted_any_mlb_bf_probability",
            "predicted_positive_mlb_pa_mean": "predicted_positive_mlb_bf_mean",
            "predicted_expected_mlb_pa": "predicted_expected_mlb_bf",
        }
    ).with_columns(
        pl.lit(fit.form).alias("model_id"),
        pl.lit(fit.nb_alpha).alias("model_nb_alpha"),
        pl.lit("provisional_development_candidate_not_2026_confirmed").alias(
            "model_status"
        ),
    )
    fallback = pl.read_parquet(args.fallback_path).filter(pl.col("horizon") == 1)
    comparison = predictions.join(
        fallback.select(
            "player_id",
            pl.col("mlb_active_probability").alias("fallback_active_probability"),
            pl.col("conditional_mlb_bf").alias("fallback_positive_mlb_bf"),
            pl.col("expected_mlb_bf").alias("fallback_expected_mlb_bf"),
            pl.col("coverage_tier").alias("fallback_coverage_tier"),
        ),
        on="player_id",
        how="left",
        validate="1:1",
    ).with_columns(
        (pl.col("predicted_expected_mlb_bf") - pl.col("fallback_expected_mlb_bf")).alias(
            "expected_mlb_bf_difference"
        )
    )
    if comparison.get_column("fallback_expected_mlb_bf").null_count():
        raise ValueError("v2/fallback current pitcher coverage differs")

    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "predictors": write_canonical_parquet(
            predictors,
            output / "predictors.parquet",
            table_name="current_pitcher_opportunity_v2_predictors",
        ).as_record(),
        "predictions": write_canonical_parquet(
            predictions,
            output / "predictions.parquet",
            table_name="current_pitcher_opportunity_v2_predictions",
        ).as_record(),
        "fallback_comparison": write_canonical_parquet(
            comparison,
            output / "fallback-comparison.parquet",
            table_name="current_pitcher_opportunity_v2_fallback_comparison",
        ).as_record(),
    }
    difference = comparison.get_column("expected_mlb_bf_difference")
    report = {
        "report_schema_version": "0.1",
        "gate": "current_pitcher_opportunity_v2_provisional_score",
        "as_of_date": args.as_of_date.isoformat(),
        "forecast_season": args.as_of_date.year + 1,
        "model_id": fit.form,
        "model_status": "provisional_development_candidate_not_2026_confirmed",
        "players": predictions.height,
        "inactive_players": predictors.filter(
            pl.col("as_of_level_group") == "INACTIVE"
        ).height,
        "unknown_role_players": predictors.filter(
            pl.col("as_of_role") == "unknown"
        ).height,
        "missing_age_players": predictors.filter(pl.col("age_years").is_null()).height,
        "on_40man_players": int(predictors.get_column("on_40man").sum()),
        "means": {
            "v2_active_probability": float(
                predictions.get_column("predicted_any_mlb_bf_probability").mean()
            ),
            "v2_conditional_positive_bf": float(
                predictions.get_column("predicted_positive_mlb_bf_mean").mean()
            ),
            "v2_expected_bf": float(
                predictions.get_column("predicted_expected_mlb_bf").mean()
            ),
            "fallback_expected_bf": float(
                comparison.get_column("fallback_expected_mlb_bf").mean()
            ),
        },
        "expected_bf_difference": {
            "mean": float(difference.mean()),
            "median": float(difference.median()),
            "p05": float(difference.quantile(0.05, interpolation="linear")),
            "p95": float(difference.quantile(0.95, interpolation="linear")),
        },
        "source_hashes": {
            "roster": sha256_file(roster_path),
            "stats": sha256_file(stats_path),
            "membership": sha256_file(membership_path),
            "coefficients": sha256_file(coefficients_path),
            "standardization": sha256_file(standardization_path),
            "fallback": sha256_file(args.fallback_path),
        },
        "boundary": {
            "protected_2026_outcomes_used_for_evaluation": False,
            "current_2026_evidence_used_as_predictor": True,
            "team_depth_used": False,
            "historical_role_transition_retained": True,
            "production_promotion": False,
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

