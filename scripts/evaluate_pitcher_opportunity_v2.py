#!/usr/bin/env python3
"""Run the frozen universal pitcher-opportunity v2 development gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl
import sklearn
import statsmodels

from universal_baseball.pitcher_opportunity_model_v2 import (
    build_universal_pitcher_opportunity_fold,
    evaluate_universal_pitcher_opportunity_forms,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


SNAPSHOT_YEARS = (2018, 2021, 2022, 2023, 2024)
BF_METRIC_NAMES = {
    "unconditional_mlb_pa_mae": "unconditional_mlb_bf_mae",
    "unconditional_mlb_pa_rmse": "unconditional_mlb_bf_rmse",
    "observed_mean_mlb_pa": "observed_mean_mlb_bf",
    "predicted_mean_mlb_pa": "predicted_mean_mlb_bf",
}


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
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-opportunity-v2-development"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    source_tables = args.source_root / "tables"
    snapshot_path = source_tables / "pitcher_snapshots.parquet"
    membership_path = (
        args.membership_root / "tables" / "historical_40man_membership.parquet"
    )
    snapshots = pl.read_parquet(snapshot_path)
    membership = pl.read_parquet(membership_path)
    folds = []
    source_files = {
        "pitcher_snapshots": {
            "path": str(snapshot_path),
            "sha256": sha256_file(snapshot_path),
        },
        "historical_40man_membership": {
            "path": str(membership_path),
            "sha256": sha256_file(membership_path),
        },
    }
    for year in SNAPSHOT_YEARS:
        current_path = source_tables / str(year) / "affiliated_season_stats.parquet"
        next_path = source_tables / str(year + 1) / "affiliated_season_stats.parquet"
        source_files[f"affiliated_stats_{year}"] = {
            "path": str(current_path),
            "sha256": sha256_file(current_path),
        }
        source_files[f"affiliated_stats_{year + 1}"] = {
            "path": str(next_path),
            "sha256": sha256_file(next_path),
        }
        folds.append(
            build_universal_pitcher_opportunity_fold(
                snapshots,
                pl.read_parquet(current_path),
                pl.read_parquet(next_path),
                membership,
                snapshot_year=year,
            )
        )

    evaluation = evaluate_universal_pitcher_opportunity_forms(folds)
    fold_metrics = evaluation.fold_metrics.rename(BF_METRIC_NAMES)
    pooled_metrics = evaluation.pooled_metrics.rename(BF_METRIC_NAMES)
    args.output_root.mkdir(parents=True, exist_ok=True)
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "fold_metrics": write_canonical_parquet(
            fold_metrics,
            tables / "fold_metrics.parquet",
            table_name="pitcher_opportunity_v2_fold_metrics",
        ).as_record(),
        "pooled_metrics": write_canonical_parquet(
            pooled_metrics,
            tables / "pooled_metrics.parquet",
            table_name="pitcher_opportunity_v2_pooled_metrics",
        ).as_record(),
        "selected_coefficients": write_canonical_parquet(
            evaluation.final_fit.coefficient_frame(),
            tables / "selected_coefficients.parquet",
            table_name="pitcher_opportunity_v2_selected_coefficients",
        ).as_record(),
        "selected_standardization": write_canonical_parquet(
            evaluation.final_fit.standardization_frame(),
            tables / "selected_standardization.parquet",
            table_name="pitcher_opportunity_v2_selected_standardization",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "pitcher_opportunity_v2_rolling_development",
        "status": "development_selected_not_production_confirmed",
        "contract": "docs/pitcher-opportunity-v2-development-contract.md",
        "snapshot_years": list(SNAPSHOT_YEARS),
        "evaluation_target_years": [2022, 2023, 2024, 2025],
        "excluded_pairs": ["2019_to_2020", "2020_to_2021"],
        "fold_population": [
            {
                "snapshot_year": fold.snapshot_year,
                "target_year": fold.target_year,
                "players": fold.predictors.height,
                "positive_target_players": fold.targets.filter(
                    pl.col("next_year_mlb_pa") > 0
                ).height,
                "inactive_players": fold.predictors.filter(
                    pl.col("as_of_level_group") == "INACTIVE"
                ).height,
                "unknown_role_players": fold.predictors.filter(
                    pl.col("as_of_role") == "unknown"
                ).height,
                "missing_age_players": fold.predictors.filter(
                    pl.col("age_years").is_null()
                ).height,
                "on_40man_players": int(fold.predictors.get_column("on_40man").sum()),
            }
            for fold in folds
        ],
        "selection": evaluation.selection,
        "selected_form": evaluation.selected_form,
        "final_training_players": evaluation.final_fit.participation_training_players,
        "final_positive_players": evaluation.final_fit.positive_training_players,
        "selected_nb_alpha": evaluation.final_fit.nb_alpha,
        "metric_unit": "batters_faced",
        "package_versions": {
            "numpy": np.__version__,
            "polars": pl.__version__,
            "scikit_learn": sklearn.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "source_files": source_files,
        "storage": storage,
        "boundary": {
            "protected_2026_outcomes_used": False,
            "future_team_depth_or_role_used": False,
            "pitch_quality_used": False,
            "inactive_unknown_role_or_missing_age_players_dropped": False,
            "historical_role_transition_retained_separately": True,
            "production_promotion": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

