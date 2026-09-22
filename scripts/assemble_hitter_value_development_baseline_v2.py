#!/usr/bin/env python3
"""Assemble the selected hitter development baseline into one player table."""

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
BASE_PATH = Path(
    "reports/generated/hitter-value-components-chronological-v2/"
    "chronological-predictions.parquet"
)
WORKLOAD_PATH = Path(
    "reports/generated/hitter-roster-feature-challenger-v2/"
    "chronological-predictions.parquet"
)
CATCHER_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/"
    "chronological-predictions.parquet"
)
INTERVAL_PATH = Path(
    "reports/generated/hitter-value-intervals-v2/interval-predictions.parquet"
)
FULL_INTERVAL_PATH = Path(
    "reports/generated/hitter-full-stack-intervals-v2/interval-predictions.parquet"
)
NAME_PATH = (
    OLD_ROOT
    / "affiliated-skill-source/tables/affiliated_hitting_components.parquet"
)
REPORT_PATHS = {
    "offensive": Path(
        "reports/generated/hitter-model-finalist-tuning-v2/finalist-report.json"
    ),
    "workload": Path("reports/generated/hitter-workload-model-v2/report.json"),
    "position": Path("reports/generated/hitter-positional-value-v2/report.json"),
    "baserunning": Path("reports/generated/hitter-baserunning-value-v2/report.json"),
    "catcher_defense": Path(
        "reports/generated/hitter-catcher-defense-value-v2/report.json"
    ),
    "roster_workload": Path(
        "reports/generated/hitter-roster-feature-challenger-v2/report.json"
    ),
    "defense_test": Path(
        "reports/generated/hitter-general-defense-value-v2/report.json"
    ),
    "defense_exposure": Path(
        "reports/generated/hitter-defense-exposure-v2/report.json"
    ),
    "defense_challenger": Path(
        "reports/generated/hitter-general-defense-challenger-v2/report.json"
    ),
}
OUTPUT_ROOT = Path("reports/generated/hitter-value-development-baseline-v2")


def main() -> None:
    base = pl.read_parquet(BASE_PATH).filter(pl.col("origin_year") == 2024)
    workload = pl.read_parquet(WORKLOAD_PATH).filter(pl.col("origin_year") == 2024)
    catcher = pl.read_parquet(CATCHER_PATH).filter(pl.col("origin_year") == 2024)
    intervals = pl.read_parquet(INTERVAL_PATH).filter(pl.col("origin_year") == 2024)
    full_intervals = pl.read_parquet(FULL_INTERVAL_PATH).filter(
        pl.col("origin_year") == 2024
    )
    names = (
        pl.read_parquet(NAME_PATH)
        .filter(pl.col("season") == 2024)
        .sort(["player_id", "plate_appearances"], descending=[False, True])
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "player_name")
    )
    frame = (
        base.join(names, on="player_id", how="left", validate="1:1")
        .join(
            workload.select(
                "player_id",
                "prediction_roster_active_probability",
                "prediction_roster_expected_pa",
                "roster_lag0__on_40man",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            intervals.select(
                "player_id",
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
        .join(
            full_intervals.select(
                "player_id",
                pl.col("lower_50").alias("selected_lower_50"),
                pl.col("upper_50").alias("selected_upper_50"),
                pl.col("lower_80").alias("selected_lower_80"),
                pl.col("upper_80").alias("selected_upper_80"),
                pl.col("lower_90").alias("selected_lower_90"),
                pl.col("upper_90").alias("selected_upper_90"),
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            catcher.select(
                "player_id",
                "actual_catcher_war",
                "prediction_catcher_war_chronological_skill_pa_scaled_opportunity",
                "actual_partial_war_with_catcher",
                "prediction_total_chronological_skill_pa_scaled_opportunity",
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .select(
            "player_id",
            "player_name",
            "player_stage",
            pl.col("prediction_roster_active_probability").alias(
                "prediction_mlb_active_probability"
            ),
            pl.col("prediction_roster_expected_pa").alias(
                "prediction_expected_mlb_pa"
            ),
            pl.col("prediction_candidate_expected_pa").alias(
                "prediction_component_scaling_expected_mlb_pa"
            ),
            pl.col("prediction_batting_replacement_war"),
            pl.col("prediction_transition_position_war").alias(
                "prediction_position_war"
            ),
            "prediction_steal_war",
            "prediction_advancement_war",
            "prediction_baserunning_war",
            pl.col(
                "prediction_catcher_war_chronological_skill_pa_scaled_opportunity"
            ).alias("prediction_catcher_defense_war"),
            pl.col(
                "prediction_total_chronological_skill_pa_scaled_opportunity"
            ).alias(
                "prediction_selected_partial_war"
            ),
            "actual_component_war",
            "later_position_war",
            "later_steal_war",
            "later_advancement_war",
            "actual_baserunning_war",
            "actual_catcher_war",
            pl.col("actual_partial_war_with_catcher").alias(
                "actual_selected_partial_war"
            ),
            pl.col("lower_50").alias("offensive_lower_50"),
            pl.col("upper_50").alias("offensive_upper_50"),
            pl.col("lower_80").alias("offensive_lower_80"),
            pl.col("upper_80").alias("offensive_upper_80"),
            pl.col("lower_90").alias("offensive_lower_90"),
            pl.col("upper_90").alias("offensive_upper_90"),
            "selected_lower_50",
            "selected_upper_50",
            "selected_lower_80",
            "selected_upper_80",
            "selected_lower_90",
            "selected_upper_90",
            "position_profile_available",
            "baserunning_evidence_tier",
            "roster_lag0__on_40man",
        )
        .sort(
            ["prediction_selected_partial_war", "player_id"],
            descending=[True, False],
        )
    )
    if frame["player_name"].null_count():
        raise RuntimeError("selected player table has missing names")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "player-projections-2025-development.parquet",
        table_name="hitter_value_development_baseline_v2_player_projections",
    )
    metrics = regression_metrics(
        frame["actual_selected_partial_war"].to_numpy(),
        frame["prediction_selected_partial_war"].to_numpy(),
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_value_development_baseline_selected",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "forecast_origin": 2024,
        "target_season": 2025,
        "target": (
            "batting plus replacement plus position plus baserunning plus "
            "catcher-defense WAR"
        ),
        "population_rows": frame.height,
        "metrics": metrics,
        "selected_components": {
            "batting_and_replacement": (
                "equal mean of direct LightGBM, three-part LightGBM, two-part "
                "XGBoost, two-part EBM, and two-part Ridge"
            ),
            "workload": (
                "roster-aware equal mean of direct LightGBM PA and hurdle LightGBM, "
                "XGBoost, EBM, and Ridge; 40-man evidence affects arrival/workload only"
            ),
            "position": "confirmed role-transition model scaled by expected MLB PA",
            "baserunning": "B2_k5 attempts, B2_k45 success, A2_k25 advancement",
            "catcher_defense": (
                "chronologically shrunk public throwing, blocking, and framing skill "
                "with native opportunities scaled by the roster-blind component PA forecast"
            ),
        },
        "excluded_components": {
            "park_opponent_context": (
                "small inconsistent gain with uncertainty spanning help and harm"
            ),
            "general_defense": (
                "improved exposure forecast passed, but the complete general-defense "
                "layer still slightly worsened whole-value RMSE"
            ),
        },
        "interval_note": (
            "Selected ranges cover the combined partial-value stack and are calibrated "
            "from the immediately preceding comparable season. Offensive-only ranges "
            "are retained as diagnostics."
        ),
        "artifact": artifact.as_record(),
        "sources": {
            "base": {"path": str(BASE_PATH), "sha256": sha256_file(BASE_PATH)},
            "workload": {
                "path": str(WORKLOAD_PATH),
                "sha256": sha256_file(WORKLOAD_PATH),
            },
            "catcher": {
                "path": str(CATCHER_PATH),
                "sha256": sha256_file(CATCHER_PATH),
            },
            "intervals": {
                "path": str(INTERVAL_PATH),
                "sha256": sha256_file(INTERVAL_PATH),
            },
            "full_stack_intervals": {
                "path": str(FULL_INTERVAL_PATH),
                "sha256": sha256_file(FULL_INTERVAL_PATH),
            },
            "names": {"path": str(NAME_PATH), "sha256": sha256_file(NAME_PATH)},
            "reports": {
                name: {"path": str(path), "sha256": sha256_file(path)}
                for name, path in REPORT_PATHS.items()
            },
        },
        "limitations": [
            "This is an exposed 2025 development artifact, not a live forecast.",
            "General-position defense remains neutral, so the target and prediction are still partial WAR.",
            "The displayed roster-aware workload improves PA and arrival scores, but component scaling remains roster-blind because roster scaling did not improve partial-WAR RMSE.",
            "Only the sealed 2026 outcome can provide final confirmation.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
