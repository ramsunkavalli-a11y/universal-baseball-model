#!/usr/bin/env python3
"""Assemble the selected pitcher development baseline into one player table."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_target_architecture import regression_metrics
from universal_baseball.storage import sha256_file, write_canonical_parquet


OLD_ROOT = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
PREDICTION_PATH = Path(
    "reports/generated/pitcher-role-ensemble-v2/predictions.parquet"
)
INTERVAL_PATH = Path(
    "reports/generated/pitcher-value-intervals-v2/interval-predictions.parquet"
)
WORKLOAD_PATH = Path("reports/generated/pitcher-workload-v2/predictions.parquet")
PANEL_PATH = Path(
    "reports/generated/pitcher-value-panel-v2/tables/modeling-panel.parquet"
)
NAME_PATH = (
    OLD_ROOT
    / "affiliated-skill-source/tables/affiliated_pitching_components.parquet"
)
REPORT_PATHS = {
    "target_architecture": Path(
        "reports/generated/pitcher-target-architectures-v2/report.json"
    ),
    "engine_tournament": Path(
        "reports/generated/pitcher-model-engine-tournament-v2/report.json"
    ),
    "base_ensemble": Path(
        "reports/generated/pitcher-model-ensemble-v2/report.json"
    ),
    "role_block": Path("reports/generated/pitcher-role-block-v2/report.json"),
    "role_ensemble": Path("reports/generated/pitcher-role-ensemble-v2/report.json"),
    "intervals": Path("reports/generated/pitcher-value-intervals-v2/report.json"),
    "workload": Path("reports/generated/pitcher-workload-v2/report.json"),
}
OUTPUT_ROOT = Path("reports/generated/pitcher-value-development-baseline-v2")
FORECAST_ORIGIN = 2024


def main() -> None:
    predictions = pl.read_parquet(PREDICTION_PATH).filter(
        pl.col("origin_year") == FORECAST_ORIGIN
    )
    intervals = pl.read_parquet(INTERVAL_PATH).filter(
        pl.col("origin_year") == FORECAST_ORIGIN
    )
    workload = pl.read_parquet(WORKLOAD_PATH).filter(
        pl.col("origin_year") == FORECAST_ORIGIN
    )
    panel = pl.read_parquet(PANEL_PATH).filter(
        pl.col("origin_year") == FORECAST_ORIGIN
    )
    names = (
        pl.read_parquet(NAME_PATH)
        .filter(pl.col("season") == FORECAST_ORIGIN)
        .sort(["player_id", "batters_faced"], descending=[False, True])
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "player_name")
    )

    frame = (
        predictions.select(
            "player_id",
            "actual_active",
            "actual_component_war",
            pl.col("probability_role_chronology_pruned_equal").alias(
                "prediction_mlb_active_probability"
            ),
            pl.col("conditional_role_chronology_pruned_equal").alias(
                "prediction_component_war_if_active"
            ),
            pl.col("prediction_role_chronology_pruned_equal").alias(
                "prediction_selected_component_war"
            ),
        )
        .join(names, on="player_id", how="left", validate="1:1")
        .join(
            workload.select(
                "player_id",
                pl.col("probability_all_equal").alias(
                    "prediction_workload_mlb_active_probability"
                ),
                pl.col("conditional_bf_all_equal").alias(
                    "prediction_mlb_bf_if_active"
                ),
                pl.col("prediction_selected_expected_bf").alias(
                    "prediction_expected_mlb_bf"
                ),
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            panel.select(
                "player_id",
                pl.col("lag0__highest_level").alias("current_highest_level"),
                pl.col("lag0__reported_age").alias("current_reported_age"),
                pl.col("lag0__batters_faced").alias("current_batters_faced"),
                pl.col("lag0__games").alias("current_games"),
                pl.col("lag0__starts").alias("current_starts"),
                pl.col("lag0__start_share").alias("current_start_share"),
                pl.col("target_mlb_bf").alias("actual_mlb_batters_faced"),
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            intervals.select(
                "player_id",
                "broad_player_stage",
                "current_role",
                "lower_50",
                "upper_50",
                "lower_80",
                "upper_80",
                "lower_90",
                "upper_90",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .rename(
            {
                "broad_player_stage": "player_stage",
                "lower_50": "selected_lower_50",
                "upper_50": "selected_upper_50",
                "lower_80": "selected_lower_80",
                "upper_80": "selected_upper_80",
                "lower_90": "selected_lower_90",
                "upper_90": "selected_upper_90",
            }
        )
        .select(
            "player_id",
            "player_name",
            "player_stage",
            "current_highest_level",
            "current_role",
            "current_reported_age",
            "current_batters_faced",
            "current_games",
            "current_starts",
            "current_start_share",
            "prediction_mlb_active_probability",
            "prediction_workload_mlb_active_probability",
            "prediction_mlb_bf_if_active",
            "prediction_expected_mlb_bf",
            "prediction_component_war_if_active",
            "prediction_selected_component_war",
            "actual_active",
            "actual_mlb_batters_faced",
            "actual_component_war",
            "selected_lower_50",
            "selected_upper_50",
            "selected_lower_80",
            "selected_upper_80",
            "selected_lower_90",
            "selected_upper_90",
        )
        .sort(
            ["prediction_selected_component_war", "player_id"],
            descending=[True, False],
        )
    )
    if frame["player_name"].null_count():
        raise RuntimeError("selected pitcher table has missing names")
    required_complete = [
        "player_stage",
        "current_role",
        "prediction_mlb_active_probability",
        "prediction_expected_mlb_bf",
        "prediction_component_war_if_active",
        "prediction_selected_component_war",
        "selected_lower_80",
        "selected_upper_80",
        "actual_component_war",
    ]
    if any(frame[column].null_count() for column in required_complete):
        raise RuntimeError("selected pitcher table has missing required values")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "player-projections-2025-development.parquet",
        table_name="pitcher_value_development_baseline_v2_player_projections",
    )
    metrics = regression_metrics(
        frame["actual_component_war"].to_numpy(),
        frame["prediction_selected_component_war"].to_numpy(),
    )
    report = {
        "schema_version": "0.1",
        "status": "pitcher_value_development_baseline_selected",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "forecast_origin": FORECAST_ORIGIN,
        "target_season": FORECAST_ORIGIN + 1,
        "target": "next-season defense-independent pitcher component WAR",
        "population_rows": frame.height,
        "metrics": metrics,
        "selected_model": (
            "chronology-pruned equal ensemble with role and workload transition "
            "features in Ridge, CatBoost, and LightGBM"
        ),
        "forecast_decomposition": {
            "arrival": "ensemble probability of pitching in MLB next season",
            "conditional_value": "ensemble component WAR among active MLB pitchers",
            "expected_value": (
                "mean of each selected member's arrival probability multiplied by "
                "that member's conditional value"
            ),
            "workload": (
                "separate four-model arrival-times-conditional-BF ensemble used for "
                "opportunity accounting, not multiplied into the selected value forecast"
            ),
            "uncertainty": (
                "earlier-fold residual ranges grouped by player stage and recent "
                "starter/reliever role"
            ),
        },
        "excluded_components": {
            "exact_opponent_quality": (
                "descriptively useful but flat to worse in future-value tests"
            ),
            "raw_hit_type_detail": "worsened all three tested engines",
            "context_neutral_contact_value": (
                "event-level signal did not improve final pitcher-value reconciliation"
            ),
        },
        "artifact": artifact.as_record(),
        "sources": {
            "predictions": {
                "path": str(PREDICTION_PATH),
                "sha256": sha256_file(PREDICTION_PATH),
            },
            "intervals": {
                "path": str(INTERVAL_PATH),
                "sha256": sha256_file(INTERVAL_PATH),
            },
            "workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "panel": {"path": str(PANEL_PATH), "sha256": sha256_file(PANEL_PATH)},
            "names": {"path": str(NAME_PATH), "sha256": sha256_file(NAME_PATH)},
            "reports": {
                name: {"path": str(path), "sha256": sha256_file(path)}
                for name, path in REPORT_PATHS.items()
            },
        },
        "limitations": [
            "This is an exposed 2025 development artifact, not a live forecast.",
            "The value target is defense-independent and still treats non-home-run contact at league-average value.",
            "Expected batters faced are separately validated for opportunity accounting and are not multiplied into the better total-value forecast.",
            "The final 2026 forecast must be rebuilt from the 2025 cutoff without opening 2026 outcomes.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
