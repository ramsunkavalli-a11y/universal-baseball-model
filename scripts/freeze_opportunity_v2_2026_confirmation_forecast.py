#!/usr/bin/env python3
"""Freeze the pre-2026 forecasts used by the protected confirmation gate."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_opportunity_paths import (
    HITTER_OPPORTUNITY_HISTORY_SCHEMA,
    fit_hitter_opportunity_fallbacks,
    score_hitter_opportunity_paths,
)
from universal_baseball.opportunity_model_v2 import (
    OpportunityFold,
    build_universal_hitter_opportunity_fold,
    build_universal_hitter_opportunity_predictors,
)
from universal_baseball.pitcher_opportunity_model_v2 import (
    PitcherOpportunityFold,
    build_universal_pitcher_opportunity_fold,
    build_universal_pitcher_opportunity_predictors,
)
from universal_baseball.pitcher_opportunity_paths import (
    PITCHER_OPPORTUNITY_HISTORY_SCHEMA,
    fit_pitcher_opportunity_fallbacks,
    score_pitcher_opportunity_paths,
)
from universal_baseball.playing_time_confirmation import load_frozen_playing_time_fit
from universal_baseball.playing_time_model import (
    PT_FORM_P0,
    PT_FORM_U0,
    build_playing_time_design,
    fit_playing_time_hurdle,
    predict_playing_time_hurdle,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


TRAINING_SNAPSHOT_YEARS = (2018, 2021, 2022, 2023, 2024)
FORECAST_SNAPSHOT_YEAR = 2025
FORECAST_TARGET_YEAR = 2026
ROW_KEY_MULTIPLIER = 10_000_000
CONTRACT = Path("docs/opportunity-v2-2026-confirmation-contract.md")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2"),
    )
    parser.add_argument(
        "--membership-root",
        type=Path,
        default=Path("reports/generated/opportunity-40man-history"),
    )
    parser.add_argument(
        "--hitter-package",
        type=Path,
        default=Path("model_artifacts/hitter-opportunity-v2-development-2026-09-09"),
    )
    parser.add_argument(
        "--pitcher-package",
        type=Path,
        default=Path("model_artifacts/pitcher-opportunity-v2-development-2026-09-09"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-v2-2026-confirmation-forecast"),
    )
    return parser.parse_args()


def _combined_training(folds: list, *, form: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    designs = []
    targets = []
    for index, fold in enumerate(folds, start=1):
        offset = index * ROW_KEY_MULTIPLIER
        designs.append(
            build_playing_time_design(fold.predictors, form=form).with_columns(
                (pl.col("player_id") + offset).alias("player_id")
            )
        )
        targets.append(
            fold.targets.select("player_id", "next_year_mlb_pa").with_columns(
                (pl.col("player_id") + offset).alias("player_id")
            )
        )
    return pl.concat(designs), pl.concat(targets)


def _hitter_history(folds: list[OpportunityFold]) -> pl.DataFrame:
    return pl.concat(
        [
            fold.predictors.select(
                pl.lit(fold.snapshot_year).alias("snapshot_year"),
                "player_id",
                "age_years",
                "as_of_level_group",
            ).join(fold.targets, on="player_id", validate="1:1").select(
                "snapshot_year",
                "player_id",
                "age_years",
                "as_of_level_group",
                pl.lit(1).alias("horizon"),
                pl.col("next_year_mlb_pa").cast(pl.Float64).alias("future_mlb_pa"),
            )
            for fold in folds
        ]
    ).cast(HITTER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)


def _pitcher_history(folds: list[PitcherOpportunityFold]) -> pl.DataFrame:
    return pl.concat(
        [
            fold.predictors.select(
                pl.lit(fold.snapshot_year).alias("snapshot_year"),
                "player_id",
                "age_years",
                "as_of_level_group",
                "as_of_role",
            ).join(fold.targets, on="player_id", validate="1:1").select(
                "snapshot_year",
                "player_id",
                "age_years",
                "as_of_level_group",
                "as_of_role",
                pl.lit(1).alias("horizon"),
                pl.col("next_year_mlb_pa").cast(pl.Float64).alias("future_mlb_bf"),
                pl.col("next_year_mlb_games").alias("future_mlb_games"),
                pl.col("next_year_mlb_starts").alias("future_mlb_starts"),
            )
            for fold in folds
        ]
    ).cast(PITCHER_OPPORTUNITY_HISTORY_SCHEMA, strict=True)


def _load_selected(package: Path):
    report = json.loads((package / "report.json").read_text(encoding="utf-8"))
    return load_frozen_playing_time_fit(
        pl.read_parquet(package / "tables/selected_coefficients.parquet"),
        pl.read_parquet(package / "tables/selected_standardization.parquet"),
        form=str(report["selected_form"]),
        expected_nb_alpha=float(report["selected_nb_alpha"]),
        participation_training_players=int(report["final_training_players"]),
        positive_training_players=int(report["final_positive_players"]),
    )


def _prediction(fit, predictors: pl.DataFrame, *, model_id: str) -> pl.DataFrame:
    return predict_playing_time_hurdle(
        fit, build_playing_time_design(predictors, form=fit.form)
    ).with_columns(
        pl.lit(model_id).alias("model_id"),
        pl.lit(fit.nb_alpha).alias("model_nb_alpha"),
    )


def _pitcher_columns(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.rename(
        {
            "predicted_any_mlb_pa_probability": "predicted_any_mlb_bf_probability",
            "predicted_positive_mlb_pa_mean": "predicted_positive_mlb_bf_mean",
            "predicted_expected_mlb_pa": "predicted_expected_mlb_bf",
        }
    )


def main() -> int:
    args = _args()
    tables = args.source_root / "tables"
    membership_path = (
        args.membership_root / "tables/historical_40man_membership.parquet"
    )
    membership = pl.read_parquet(membership_path)
    hitter_snapshots = pl.read_parquet(tables / "hitter_snapshots.parquet")
    pitcher_snapshots = pl.read_parquet(tables / "pitcher_snapshots.parquet")
    hitter_folds = []
    pitcher_folds = []
    for year in TRAINING_SNAPSHOT_YEARS:
        current = pl.read_parquet(tables / str(year) / "affiliated_season_stats.parquet")
        future = pl.read_parquet(
            tables / str(year + 1) / "affiliated_season_stats.parquet"
        )
        hitter_folds.append(
            build_universal_hitter_opportunity_fold(
                hitter_snapshots, current, future, membership, snapshot_year=year
            )
        )
        pitcher_folds.append(
            build_universal_pitcher_opportunity_fold(
                pitcher_snapshots, current, future, membership, snapshot_year=year
            )
        )
    stats_2025_path = tables / "2025/affiliated_season_stats.parquet"
    stats_2025 = pl.read_parquet(stats_2025_path)
    hitter_predictors = build_universal_hitter_opportunity_predictors(
        hitter_snapshots,
        stats_2025,
        membership,
        snapshot_year=FORECAST_SNAPSHOT_YEAR,
    )
    pitcher_predictors = build_universal_pitcher_opportunity_predictors(
        pitcher_snapshots,
        stats_2025,
        membership,
        snapshot_year=FORECAST_SNAPSHOT_YEAR,
    )

    hitter_selected_fit = _load_selected(args.hitter_package)
    pitcher_selected_fit = _load_selected(args.pitcher_package)
    hitter_u0_design, hitter_targets = _combined_training(hitter_folds, form=PT_FORM_U0)
    pitcher_p0_design, pitcher_targets = _combined_training(
        pitcher_folds, form=PT_FORM_P0
    )
    hitter_u0_fit = fit_playing_time_hurdle(
        hitter_u0_design, hitter_targets, form=PT_FORM_U0
    )
    pitcher_p0_fit = fit_playing_time_hurdle(
        pitcher_p0_design, pitcher_targets, form=PT_FORM_P0
    )
    hitter_selected = _prediction(
        hitter_selected_fit, hitter_predictors, model_id=hitter_selected_fit.form
    )
    hitter_baseline = _prediction(
        hitter_u0_fit, hitter_predictors, model_id=hitter_u0_fit.form
    )
    pitcher_selected = _pitcher_columns(
        _prediction(
            pitcher_selected_fit,
            pitcher_predictors,
            model_id=pitcher_selected_fit.form,
        )
    )
    pitcher_baseline = _pitcher_columns(
        _prediction(pitcher_p0_fit, pitcher_predictors, model_id=pitcher_p0_fit.form)
    )
    hitter_incumbent_fit = fit_hitter_opportunity_fallbacks(
        _hitter_history(hitter_folds), forecast_year=FORECAST_TARGET_YEAR, horizons=[1]
    )
    pitcher_incumbent_fit = fit_pitcher_opportunity_fallbacks(
        _pitcher_history(pitcher_folds),
        forecast_year=FORECAST_TARGET_YEAR,
        horizons=[1],
    )
    hitter_incumbent = score_hitter_opportunity_paths(
        hitter_predictors.select("player_id", "age_years", "as_of_level_group"),
        hitter_incumbent_fit,
        as_of_date=date(FORECAST_SNAPSHOT_YEAR, 10, 15),
        forecast_year=FORECAST_TARGET_YEAR,
    ).select(
        "player_id",
        pl.col("mlb_active_probability").alias("predicted_any_mlb_pa_probability"),
        pl.col("conditional_mlb_pa").alias("predicted_positive_mlb_pa_mean"),
        pl.col("expected_mlb_pa").alias("predicted_expected_mlb_pa"),
        pl.lit("historical_cohort_fallback_v1").alias("model_id"),
    )
    pitcher_incumbent = score_pitcher_opportunity_paths(
        pitcher_predictors.select(
            "player_id", "age_years", "as_of_level_group", "as_of_role"
        ),
        pitcher_incumbent_fit,
        as_of_date=date(FORECAST_SNAPSHOT_YEAR, 10, 15),
        forecast_year=FORECAST_TARGET_YEAR,
    ).select(
        "player_id",
        pl.col("mlb_active_probability").alias("predicted_any_mlb_bf_probability"),
        pl.col("conditional_mlb_bf").alias("predicted_positive_mlb_bf_mean"),
        pl.col("expected_mlb_bf").alias("predicted_expected_mlb_bf"),
        pl.lit("historical_cohort_fallback_v1").alias("model_id"),
    )

    output = args.output_root
    output.mkdir(parents=True, exist_ok=True)
    storage = {}
    frames = {
        "hitter_selected": hitter_selected,
        "hitter_parametric_baseline": hitter_baseline,
        "hitter_incumbent": hitter_incumbent,
        "pitcher_selected": pitcher_selected,
        "pitcher_parametric_baseline": pitcher_baseline,
        "pitcher_incumbent": pitcher_incumbent,
    }
    for name, frame in frames.items():
        storage[name] = write_canonical_parquet(
            frame,
            output / f"{name.replace('_', '-')}.parquet",
            table_name=f"opportunity_v2_2026_confirmation_{name}",
        ).as_record()
    for component, fit in (("hitter_u0", hitter_u0_fit), ("pitcher_p0", pitcher_p0_fit)):
        storage[f"{component}_coefficients"] = write_canonical_parquet(
            fit.coefficient_frame(),
            output / f"{component.replace('_', '-')}-coefficients.parquet",
            table_name=f"opportunity_v2_2026_confirmation_{component}_coefficients",
        ).as_record()
        storage[f"{component}_standardization"] = write_canonical_parquet(
            fit.standardization_frame(),
            output / f"{component.replace('_', '-')}-standardization.parquet",
            table_name=f"opportunity_v2_2026_confirmation_{component}_standardization",
        ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_v2_2026_protected_confirmation_forecast_freeze",
        "contract": CONTRACT.as_posix(),
        "contract_sha256": sha256_file(CONTRACT),
        "snapshot_date": "2025-10-15",
        "target_season": 2026,
        "target_status": "not_read_waiting_for_completed_regular_season",
        "hitter_players": hitter_predictors.height,
        "pitcher_players": pitcher_predictors.height,
        "training_snapshot_years": list(TRAINING_SNAPSHOT_YEARS),
        "selected_models": {
            "hitter": hitter_selected_fit.form,
            "pitcher": pitcher_selected_fit.form,
        },
        "parametric_baselines": {"hitter": PT_FORM_U0, "pitcher": PT_FORM_P0},
        "source_hashes": {
            "hitter_snapshots": sha256_file(tables / "hitter_snapshots.parquet"),
            "pitcher_snapshots": sha256_file(tables / "pitcher_snapshots.parquet"),
            "affiliated_stats_2025": sha256_file(stats_2025_path),
            "membership": sha256_file(membership_path),
            "hitter_package_report": sha256_file(args.hitter_package / "report.json"),
            "pitcher_package_report": sha256_file(args.pitcher_package / "report.json"),
        },
        "boundary": {
            "any_2026_outcome_file_read": False,
            "team_depth_or_future_team_used": False,
            "names_used": False,
            "forecast_rows_are_immutable_confirmation_inputs": True,
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
