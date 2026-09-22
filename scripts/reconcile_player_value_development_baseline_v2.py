#!/usr/bin/env python3
"""Reconcile the selected hitter and pitcher forecasts at player level."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.chronological_intervals import (
    chronological_residual_intervals,
    interval_metrics,
)
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


HITTER_PATH = Path(
    "reports/generated/hitter-catcher-defense-value-v2/"
    "chronological-predictions.parquet"
)
PITCHER_PATH = Path("reports/generated/pitcher-role-ensemble-v2/predictions.parquet")
PITCHER_INTERVAL_PATH = Path(
    "reports/generated/pitcher-value-intervals-v2/interval-predictions.parquet"
)
HITTER_BASELINE_PATH = Path(
    "reports/generated/hitter-value-development-baseline-v2/"
    "player-projections-2025-development.parquet"
)
PITCHER_BASELINE_PATH = Path(
    "reports/generated/pitcher-value-development-baseline-v2/"
    "player-projections-2025-development.parquet"
)
OUTPUT_ROOT = Path("reports/generated/player-value-development-baseline-v2")
FORECAST_ORIGIN = 2024
INTERVAL_CALIBRATION_LEVELS = {0.5: 0.55, 0.8: 0.85, 0.9: 0.93}


def _build_chronology() -> pl.DataFrame:
    hitter = pl.read_parquet(HITTER_PATH).select(
        "origin_year",
        "player_id",
        pl.lit(1, dtype=pl.Int8).alias("has_hitter_history"),
        pl.col("player_stage").alias("hitter_player_stage"),
        pl.col("actual_partial_war_with_catcher").alias("actual_hitter_partial_war"),
        pl.col("prediction_batting_replacement_war").alias(
            "prediction_hitter_batting_war"
        ),
        pl.col(
            "prediction_total_chronological_skill_pa_scaled_opportunity"
        ).alias("prediction_hitter_selected_partial_war"),
    )
    pitcher_stages = pl.read_parquet(PITCHER_INTERVAL_PATH).select(
        "origin_year",
        "player_id",
        pl.col("broad_player_stage").alias("pitcher_player_stage"),
        "current_role",
    )
    pitcher = (
        pl.read_parquet(PITCHER_PATH)
        .filter(
            pl.col("origin_year").is_in(
                hitter["origin_year"].unique().to_list()
            )
        )
        .select(
            "origin_year",
            "player_id",
            pl.lit(1, dtype=pl.Int8).alias("has_pitcher_history"),
            pl.col("actual_component_war").alias("actual_pitcher_component_war"),
            pl.col("prediction_chronology_pruned_equal").alias(
                "prediction_pitcher_role_neutral_war"
            ),
            pl.col("prediction_role_chronology_pruned_equal").alias(
                "prediction_pitcher_selected_war"
            ),
        )
        .join(
            pitcher_stages,
            on=["origin_year", "player_id"],
            how="left",
            validate="1:1",
        )
    )
    numeric_fill = [
        "actual_hitter_partial_war",
        "prediction_hitter_batting_war",
        "prediction_hitter_selected_partial_war",
        "actual_pitcher_component_war",
        "prediction_pitcher_role_neutral_war",
        "prediction_pitcher_selected_war",
    ]
    frame = (
        hitter.join(
            pitcher,
            on=["origin_year", "player_id"],
            how="full",
            coalesce=True,
            validate="1:1",
        )
        .with_columns(
            pl.col("has_hitter_history").fill_null(0),
            pl.col("has_pitcher_history").fill_null(0),
            *(pl.col(column).fill_null(0.0) for column in numeric_fill),
        )
        .with_columns(
            pl.when(
                (pl.col("has_hitter_history") == 1)
                & (pl.col("has_pitcher_history") == 1)
            )
            .then(pl.lit("hitter_and_pitcher"))
            .when(pl.col("has_hitter_history") == 1)
            .then(pl.lit("hitter_only"))
            .otherwise(pl.lit("pitcher_only"))
            .alias("value_profile"),
            pl.when(
                (pl.col("has_hitter_history") == 1)
                & (pl.col("has_pitcher_history") == 1)
            )
            .then(pl.lit("hitter_and_pitcher"))
            .when(pl.col("has_hitter_history") == 1)
            .then(pl.concat_str(pl.lit("hitter"), "hitter_player_stage", separator="__"))
            .otherwise(
                pl.concat_str(
                    pl.lit("pitcher"), "pitcher_player_stage", separator="__"
                )
            )
            .alias("player_stage"),
        )
        .with_columns(
            (
                pl.col("actual_hitter_partial_war")
                + pl.col("actual_pitcher_component_war")
            ).alias("actual_component_war"),
            (
                pl.col("prediction_hitter_selected_partial_war")
                + pl.col("prediction_pitcher_selected_war")
            ).alias("prediction_selected_partial_war"),
            (
                pl.col("prediction_hitter_batting_war")
                + pl.col("prediction_pitcher_selected_war")
            ).alias("prediction_hitter_components_neutral"),
            (
                pl.col("prediction_hitter_selected_partial_war")
                + pl.col("prediction_pitcher_role_neutral_war")
            ).alias("prediction_pitcher_role_neutral"),
            (
                pl.col("prediction_hitter_batting_war")
                + pl.col("prediction_pitcher_role_neutral_war")
            ).alias("prediction_all_added_components_neutral"),
        )
        .sort(["origin_year", "player_id"])
    )
    if frame.select("origin_year", "player_id").is_duplicated().any():
        raise RuntimeError("combined player table violates player-origin grain")
    if frame["player_stage"].null_count():
        raise RuntimeError("combined player table has missing stage")
    return frame


def _metrics(frame: pl.DataFrame, prediction_column: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(),
        frame[prediction_column].to_numpy(),
    )


def main() -> None:
    frame = _build_chronology()
    predictions = {
        "selected": "prediction_selected_partial_war",
        "hitter_components_neutral": "prediction_hitter_components_neutral",
        "pitcher_role_neutral": "prediction_pitcher_role_neutral",
        "all_added_components_neutral": "prediction_all_added_components_neutral",
    }
    metrics = {name: _metrics(frame, column) for name, column in predictions.items()}
    actual = frame["actual_component_war"].to_numpy()
    selected = frame[predictions["selected"]].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    comparisons = {
        "selected_minus_hitter_components_neutral": paired_cluster_rmse_delta(
            actual,
            selected,
            frame[predictions["hitter_components_neutral"]].to_numpy(),
            player_ids,
            bootstrap_samples=5_000,
        ),
        "selected_minus_pitcher_role_neutral": paired_cluster_rmse_delta(
            actual,
            selected,
            frame[predictions["pitcher_role_neutral"]].to_numpy(),
            player_ids,
            bootstrap_samples=5_000,
        ),
        "selected_minus_all_added_components_neutral": paired_cluster_rmse_delta(
            actual,
            selected,
            frame[predictions["all_added_components_neutral"]].to_numpy(),
            player_ids,
            bootstrap_samples=5_000,
        ),
    }
    by_origin = {
        str(origin): {
            name: _metrics(frame.filter(pl.col("origin_year") == origin), column)
            for name, column in predictions.items()
        }
        for origin in sorted(frame["origin_year"].unique().to_list())
    }
    by_profile = {
        profile: {
            "rows": frame.filter(pl.col("value_profile") == profile).height,
            **{
                name: _metrics(
                    frame.filter(pl.col("value_profile") == profile), column
                )
                for name, column in predictions.items()
            },
        }
        for profile in sorted(frame["value_profile"].unique().to_list())
    }

    interval_input = frame
    raw_intervals, raw_calibration = chronological_residual_intervals(
        interval_input,
        prediction_column="prediction_selected_partial_war",
    )
    intervals, calibration = chronological_residual_intervals(
        interval_input,
        prediction_column="prediction_selected_partial_war",
        confidence_levels=tuple(INTERVAL_CALIBRATION_LEVELS.values()),
    )
    interval_renames: dict[str, str] = {}
    for displayed, calibration_level in INTERVAL_CALIBRATION_LEVELS.items():
        displayed_label = str(int(round(displayed * 100)))
        calibration_label = str(int(round(calibration_level * 100)))
        interval_renames[f"lower_{calibration_label}"] = f"lower_{displayed_label}"
        interval_renames[f"upper_{calibration_label}"] = f"upper_{displayed_label}"
    intervals = intervals.rename(interval_renames)
    calibration = calibration.rename({"confidence": "calibration_confidence"}).with_columns(
        pl.col("calibration_confidence")
        .replace(
            {
                calibration_level: displayed
                for displayed, calibration_level in INTERVAL_CALIBRATION_LEVELS.items()
            }
        )
        .alias("displayed_confidence")
    )
    interval_overall = interval_metrics(intervals)
    raw_interval_overall = interval_metrics(raw_intervals)
    interval_by_origin = {
        str(origin): interval_metrics(
            intervals.filter(pl.col("origin_year") == origin)
        )
        for origin in sorted(intervals["origin_year"].unique().to_list())
    }
    interval_by_stage = {
        stage: interval_metrics(intervals.filter(pl.col("player_stage") == stage))
        for stage in sorted(intervals["player_stage"].unique().to_list())
    }

    hitter_2025 = pl.read_parquet(HITTER_BASELINE_PATH).select(
        "player_id",
        pl.col("player_name").alias("hitter_player_name"),
        "prediction_mlb_active_probability",
        "prediction_expected_mlb_pa",
    )
    pitcher_2025 = pl.read_parquet(PITCHER_BASELINE_PATH).select(
        "player_id",
        pl.col("player_name").alias("pitcher_player_name"),
        pl.col("prediction_mlb_active_probability").alias(
            "prediction_pitcher_mlb_active_probability"
        ),
        "prediction_expected_mlb_bf",
        "prediction_component_war_if_active",
        "current_role",
    )
    player_2025 = (
        intervals.filter(pl.col("origin_year") == FORECAST_ORIGIN)
        .join(hitter_2025, on="player_id", how="left", validate="1:1")
        .join(pitcher_2025, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.coalesce("hitter_player_name", "pitcher_player_name").alias(
                "player_name"
            )
        )
        .select(
            "player_id",
            "player_name",
            "value_profile",
            "hitter_player_stage",
            "pitcher_player_stage",
            "current_role",
            pl.col("prediction_mlb_active_probability").alias(
                "prediction_hitter_mlb_active_probability"
            ),
            "prediction_expected_mlb_pa",
            "prediction_pitcher_mlb_active_probability",
            "prediction_expected_mlb_bf",
            "prediction_component_war_if_active",
            "prediction_hitter_batting_war",
            "prediction_hitter_selected_partial_war",
            "prediction_pitcher_selected_war",
            "prediction_selected_partial_war",
            "actual_hitter_partial_war",
            "actual_pitcher_component_war",
            "actual_component_war",
            pl.col("lower_50").alias("selected_lower_50"),
            pl.col("upper_50").alias("selected_upper_50"),
            pl.col("lower_80").alias("selected_lower_80"),
            pl.col("upper_80").alias("selected_upper_80"),
            pl.col("lower_90").alias("selected_lower_90"),
            pl.col("upper_90").alias("selected_upper_90"),
        )
        .sort(["prediction_selected_partial_war", "player_id"], descending=[True, False])
    )
    if player_2025["player_name"].null_count():
        raise RuntimeError("combined 2025 player table has missing names")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "chronology": write_canonical_parquet(
            frame,
            OUTPUT_ROOT / "chronological-predictions.parquet",
            table_name="player_value_development_baseline_v2_chronology",
        ).as_record(),
        "intervals": write_canonical_parquet(
            intervals,
            OUTPUT_ROOT / "interval-predictions.parquet",
            table_name="player_value_development_baseline_v2_intervals",
        ).as_record(),
        "calibration": write_canonical_parquet(
            calibration,
            OUTPUT_ROOT / "calibration-offsets.parquet",
            table_name="player_value_development_baseline_v2_calibration",
        ).as_record(),
        "raw_interval_sensitivity": write_canonical_parquet(
            raw_intervals,
            OUTPUT_ROOT / "raw-interval-sensitivity.parquet",
            table_name="player_value_development_baseline_v2_raw_intervals",
        ).as_record(),
        "raw_calibration_sensitivity": write_canonical_parquet(
            raw_calibration,
            OUTPUT_ROOT / "raw-calibration-sensitivity.parquet",
            table_name="player_value_development_baseline_v2_raw_calibration",
        ).as_record(),
        "player_2025": write_canonical_parquet(
            player_2025,
            OUTPUT_ROOT / "player-projections-2025-development.parquet",
            table_name="player_value_development_baseline_v2_player_projections",
        ).as_record(),
    }
    report = {
        "schema_version": "0.1",
        "status": "hitter_pitcher_player_value_reconciled",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "forecast_origins": sorted(frame["origin_year"].unique().to_list()),
        "target": (
            "next-season hitter partial WAR plus defense-independent pitcher "
            "component WAR for every player in either forecast population"
        ),
        "population_rows": frame.height,
        "unique_players": frame["player_id"].n_unique(),
        "metrics": metrics,
        "comparisons": comparisons,
        "by_origin": by_origin,
        "by_value_profile": by_profile,
        "uncertainty": {
            "method": (
                "asymmetric residual quantiles from strictly earlier combined "
                "out-of-fold seasons, segmented by forecast-time hitter/pitcher "
                "population and MLB/upper-minors/lower-minors stage"
            ),
            "selected_calibration_levels": {
                str(int(displayed * 100)): calibration_level
                for displayed, calibration_level in INTERVAL_CALIBRATION_LEVELS.items()
            },
            "selection_reason": (
                "literal 50/80/90 residual quantiles under-covered; fixed "
                "development cushions of 55/85/93 produced stable near-nominal "
                "coverage in both scored seasons and are frozen for the protected test"
            ),
            "excluded_origin": int(frame["origin_year"].min()),
            "overall": interval_overall,
            "by_origin": interval_by_origin,
            "by_stage": interval_by_stage,
            "raw_nominal_sensitivity": raw_interval_overall,
        },
        "interpretation": {
            "selected": "accepted hitter stack plus role-enhanced pitcher ensemble",
            "hitter_components_neutral": (
                "hitter batting/replacement only plus the selected pitcher model"
            ),
            "pitcher_role_neutral": (
                "accepted hitter stack plus the older pitcher ensemble without the "
                "role-feature upgrade"
            ),
            "all_added_components_neutral": (
                "hitter batting/replacement only plus the older pitcher ensemble"
            ),
        },
        "artifacts": artifacts,
        "sources": {
            "hitter_chronology": {
                "path": str(HITTER_PATH),
                "sha256": sha256_file(HITTER_PATH),
            },
            "pitcher_chronology": {
                "path": str(PITCHER_PATH),
                "sha256": sha256_file(PITCHER_PATH),
            },
            "pitcher_intervals": {
                "path": str(PITCHER_INTERVAL_PATH),
                "sha256": sha256_file(PITCHER_INTERVAL_PATH),
            },
            "hitter_2025": {
                "path": str(HITTER_BASELINE_PATH),
                "sha256": sha256_file(HITTER_BASELINE_PATH),
            },
            "pitcher_2025": {
                "path": str(PITCHER_BASELINE_PATH),
                "sha256": sha256_file(PITCHER_BASELINE_PATH),
            },
        },
        "limitations": [
            "This is a partial-value reconciliation, not complete WAR: general non-catcher defense is neutral and pitcher contact value remains defense-independent.",
            "The combined chronology has three origins; direct combined uncertainty is scored on 2024 and 2025 only and the small coverage cushions are development-selected.",
            "A player present in both source populations is summed rather than forced into one role.",
            "Team playing-time and innings constraints are not applied yet.",
            "The final 2026 confirmation remains sealed.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
