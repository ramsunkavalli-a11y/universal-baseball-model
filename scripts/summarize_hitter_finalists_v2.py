#!/usr/bin/env python3
"""Summarize corrected-population finalists and the fixed research ensemble."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import (
    classification_metrics,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


KEY = ["origin_year", "target_season", "player_id"]
ROOT = Path("reports/generated/hitter-model-finalist-tuning-v2")
SCREEN_ROOT = Path("reports/generated/hitter-model-engine-tournament-v2")
ARCHITECTURE_PATH = Path(
    "reports/generated/hitter-target-architecture-v1/tables/"
    "chronological_predictions.parquet"
)
PANEL_PATH = Path(
    "reports/generated/hitter-value-panel-v2/tables/modeling-panel.parquet"
)
ENGINE_MEMBERS = ("lightgbm", "xgboost", "catboost", "ebm", "ridge")
CANDIDATE_MEMBERS = (
    "direct_lightgbm",
    "three_part_lightgbm",
    "two_part_xgboost",
    "two_part_ebm",
    "two_part_ridge",
)


def _load(path: Path) -> pl.DataFrame:
    return pl.read_parquet(path).sort(KEY)


def main() -> None:
    architecture = _load(ARCHITECTURE_PATH)
    engines = {
        engine: _load(SCREEN_ROOT / "tables" / f"{engine}-predictions.parquet")
        for engine in ENGINE_MEMBERS
    }
    tuned = {
        engine: _load(ROOT / "tables" / f"{engine}-predictions.parquet")
        for engine in ("ebm", "lightgbm", "xgboost", "catboost")
    }
    actual = architecture["actual_component_war"].to_numpy()
    player_ids = architecture["player_id"].to_numpy()
    members = {
        "direct_lightgbm": architecture["prediction_direct"].to_numpy(),
        "three_part_lightgbm": architecture["prediction_three_part"].to_numpy(),
        **{
            f"two_part_{engine}": frame["predicted_component_war"].to_numpy()
            for engine, frame in engines.items()
        },
    }
    ensemble_definitions = {
        "all_seven": tuple(members),
        "without_catboost_six": tuple(
            name for name in members if name != "two_part_catboost"
        ),
        "architecture_and_engine_diversity_five": CANDIDATE_MEMBERS,
    }
    ensemble_predictions = {
        label: np.mean(
            np.column_stack([members[name] for name in names]), axis=1
        )
        for label, names in ensemble_definitions.items()
    }
    candidate = ensemble_predictions["architecture_and_engine_diversity_five"]
    candidate_active_probability = np.mean(
        np.column_stack(
            [
                architecture["active_probability"].to_numpy(),
                engines["xgboost"]["active_probability"].to_numpy(),
                engines["ebm"]["active_probability"].to_numpy(),
                engines["ridge"]["active_probability"].to_numpy(),
            ]
        ),
        axis=1,
    )
    architecture_mean = np.mean(
        np.column_stack(
            [
                members["direct_lightgbm"],
                members["three_part_lightgbm"],
                members["two_part_lightgbm"],
            ]
        ),
        axis=1,
    )
    member_metrics = {
        name: regression_metrics(actual, prediction)
        for name, prediction in members.items()
    }
    tuned_metrics = {
        engine: regression_metrics(
            actual, frame["predicted_component_war"].to_numpy()
        )
        for engine, frame in tuned.items()
    }
    leave_one_out = {
        f"without_{omitted}": regression_metrics(
            actual,
            np.mean(
                np.column_stack(
                    [members[name] for name in CANDIDATE_MEMBERS if name != omitted]
                ),
                axis=1,
            ),
        )
        for omitted in CANDIDATE_MEMBERS
    }
    candidate_metrics = regression_metrics(actual, candidate)
    alternative_ensemble_metrics = {
        label: {
            "members": list(ensemble_definitions[label]),
            "metrics": regression_metrics(actual, prediction),
        }
        for label, prediction in ensemble_predictions.items()
    }
    comparisons = {
        "candidate_minus_best_single_lightgbm": paired_cluster_rmse_delta(
            actual,
            candidate,
            members["two_part_lightgbm"],
            player_ids,
        ),
        "candidate_minus_three_part": paired_cluster_rmse_delta(
            actual,
            candidate,
            members["three_part_lightgbm"],
            player_ids,
        ),
        "candidate_minus_architecture_mean": paired_cluster_rmse_delta(
            actual, candidate, architecture_mean, player_ids
        ),
        "candidate_minus_all_seven": paired_cluster_rmse_delta(
            actual,
            candidate,
            ensemble_predictions["all_seven"],
            player_ids,
        ),
        "candidate_minus_without_catboost_six": paired_cluster_rmse_delta(
            actual,
            candidate,
            ensemble_predictions["without_catboost_six"],
            player_ids,
        ),
    }
    origin_values = architecture["origin_year"].to_numpy()
    folds = {}
    for origin in sorted(architecture["origin_year"].unique().to_list()):
        mask = origin_values == origin
        folds[str(origin)] = {
            "players": int(mask.sum()),
            "candidate": regression_metrics(actual[mask], candidate[mask]),
            "all_seven": regression_metrics(
                actual[mask], ensemble_predictions["all_seven"][mask]
            ),
            "without_catboost_six": regression_metrics(
                actual[mask],
                ensemble_predictions["without_catboost_six"][mask],
            ),
            "best_single_lightgbm": regression_metrics(
                actual[mask], members["two_part_lightgbm"][mask]
            ),
            "three_part": regression_metrics(
                actual[mask], members["three_part_lightgbm"][mask]
            ),
        }

    panel = pl.read_parquet(PANEL_PATH).select(
        "origin_year",
        "player_id",
        pl.col("lag0__highest_level").alias("current_highest_level"),
        pl.col("lag0__pa_level__MLB").alias("current_mlb_pa"),
        pl.col("lag0__contact_feature_available").alias(
            "current_contact_feature_available"
        ),
    )
    predictions = architecture.select(
        KEY + ["actual_active", "actual_component_war"]
    ).with_columns(
        pl.Series("prediction_candidate_equal_mean", candidate),
        pl.Series(
            "prediction_candidate_mlb_active_probability",
            candidate_active_probability,
        ),
        pl.Series("prediction_architecture_equal_mean", architecture_mean),
        pl.Series(
            "prediction_best_single_lightgbm", members["two_part_lightgbm"]
        ),
        *[
            pl.Series(f"prediction_member__{name}", prediction)
            for name, prediction in members.items()
        ],
    ).join(panel, on=["origin_year", "player_id"], how="left")
    predictions = predictions.with_columns(
        pl.when(pl.col("current_mlb_pa") > 0)
        .then(pl.lit("current_mlb"))
        .when(pl.col("current_highest_level").is_in(["AA", "AAA"]))
        .then(pl.lit("upper_minors"))
        .otherwise(pl.lit("lower_minors"))
        .alias("player_stage")
    )
    subgroup_metrics = {}
    for label, expression in {
        "current_mlb": pl.col("player_stage") == "current_mlb",
        "upper_minors": pl.col("player_stage") == "upper_minors",
        "lower_minors": pl.col("player_stage") == "lower_minors",
        "contact_available": pl.col("current_contact_feature_available") == 1,
        "contact_unavailable": pl.col("current_contact_feature_available") == 0,
    }.items():
        subgroup = predictions.filter(expression)
        subgroup_metrics[label] = {
            "rows": subgroup.height,
            "active_rate": float(subgroup["actual_active"].mean()),
            "metrics": regression_metrics(
                subgroup["actual_component_war"].to_numpy(),
                subgroup["prediction_candidate_equal_mean"].to_numpy(),
            ),
        }

    artifact = write_canonical_parquet(
        predictions,
        ROOT / "tables" / "finalist-ensemble-predictions.parquet",
        table_name="hitter_model_finalist_v2_ensemble_predictions",
    )
    report = {
        "schema_version": "0.3",
        "status": "offensive_value_development_baseline_selected",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "primary_target": "next-season zero-inclusive MLB batting-plus-replacement WAR",
        "population_rows": architecture.height,
        "candidate_equal_mean": {
            "members": list(CANDIDATE_MEMBERS),
            "metrics": candidate_metrics,
            "mlb_active_probability_metrics": classification_metrics(
                architecture["actual_active"].to_numpy(),
                candidate_active_probability,
            ),
            "selection_rule": (
                "retain both target decompositions, one representative boosted-tree "
                "engine, the interpretable nonlinear engine, and the linear engine; "
                "remove CatBoost because it worsened leave-one-out RMSE and remove "
                "two-part LightGBM because the candidate already contains two "
                "LightGBM architectures"
            ),
            "development_status": (
                "recommended research baseline; 2026 remains protected confirmation"
            ),
        },
        "alternative_ensemble_metrics": alternative_ensemble_metrics,
        "member_metrics": member_metrics,
        "nested_tuned_metrics": tuned_metrics,
        "architecture_equal_mean": regression_metrics(actual, architecture_mean),
        "leave_one_member_out": leave_one_out,
        "paired_player_cluster_comparisons": comparisons,
        "fold_metrics": folds,
        "subgroup_metrics": subgroup_metrics,
        "artifact": artifact.as_record(),
        "interpretation": [
            "No single target decomposition dominates every player group.",
            "Fixed settings match or beat limited nested tuning for every finalist.",
            "The five-member equal mean is more accurate than any single member.",
            "Removing redundant CatBoost and two-part LightGBM reduces complexity and improves pooled development RMSE.",
            "The linear member is weak alone but contributes different errors to the mean.",
            "Chronology-learned global and player-stage weights failed to improve the equal mean.",
            "Modern park and opponent context was not retained because its small pooled gain reversed in one of two seasons.",
            "The prior contact-outcome ensemble is not a like-for-like total-WAR benchmark.",
        ],
        "remaining_before_production": [
            "Add defense, baserunning, and positional value as separate modules.",
            "Audit and complete 2025 source PBP before fitting a 2026 forecast.",
            "Score the protected 2026 season only after its outcomes are complete.",
        ],
    }
    (ROOT / "finalist-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
