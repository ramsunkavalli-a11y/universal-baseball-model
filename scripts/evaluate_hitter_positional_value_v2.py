#!/usr/bin/env python3
"""Attach confirmed position-role forecasts to the new hitter value model."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.historical_hitter_position import position_war_by_player_origin
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.player_value_positional_adjustment import (
    POSITIONAL_RUNS_PER_162,
)
from universal_baseball.position_role_profile import (
    BATTING_ROLE_POSITIONS,
    build_batting_role_profiles,
)
from universal_baseball.position_role_transition import (
    transition_smoothed_prediction,
    validate_role_vector,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


ROOT_OLD = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)
BATTING_PATH = Path(
    "reports/generated/hitter-model-finalist-tuning-v2/tables/"
    "finalist-ensemble-predictions.parquet"
)
WORKLOAD_PATH = Path(
    "reports/generated/hitter-workload-model-v2/chronological-predictions.parquet"
)
FIELDING_HISTORY_PATH = (
    ROOT_OLD
    / "position-capacity-source/historical/reports/generated/"
    "position-role-historical-source/tables/historical_fielding_usage.parquet"
)
MLB_FIELDING_PATH = (
    ROOT_OLD
    / "mlb-fielding-outcome-inventory-2004-2025/tables/"
    "mlb_fielding_usage_2004_2025.parquet"
)
PARAMETER_PATH = Path("docs/position-role-confirmation-parameters.json")
OUTPUT_ROOT = Path("reports/generated/hitter-positional-value-v2")
RUNS_PER_WIN = 10.0


def _load_parameters() -> tuple[float, dict[str, np.ndarray]]:
    payload = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
    parameters = payload["parameters"]
    if parameters["position_order"] != list(BATTING_ROLE_POSITIONS):
        raise ValueError("frozen position ordering changed")
    destination_means = {
        source: validate_role_vector(
            np.array(
                [
                    float(details["probabilities"][destination])
                    for destination in BATTING_ROLE_POSITIONS
                ]
            )
        )
        for source, details in parameters["destination_means"].items()
    }
    return float(parameters["primary_share_threshold"]), destination_means


def _role_maps(
    fielding: pl.DataFrame,
) -> tuple[dict[int, np.ndarray], dict[int, tuple[str, float]]]:
    built = build_batting_role_profiles(
        fielding.filter(pl.col("season") == 2024)
    )
    profiles: dict[int, np.ndarray] = {}
    for row in built.profile.select(
        "player_id", "position_abbreviation", "role_probability"
    ).iter_rows(named=True):
        vector = profiles.setdefault(
            int(row["player_id"]), np.zeros(len(BATTING_ROLE_POSITIONS))
        )
        vector[BATTING_ROLE_POSITIONS.index(str(row["position_abbreviation"]))] = float(
            row["role_probability"]
        )
    profiles = {
        player_id: validate_role_vector(vector)
        for player_id, vector in profiles.items()
    }
    summaries = {
        int(row["player_id"]): (
            str(row["primary_position"]),
            float(row["primary_role_share"]),
        )
        for row in built.player_season.select(
            "player_id", "primary_position", "primary_role_share"
        ).iter_rows(named=True)
    }
    return profiles, summaries


def _position_rate(profile: np.ndarray) -> float:
    return float(
        sum(
            profile[index] * POSITIONAL_RUNS_PER_162[position]
            for index, position in enumerate(BATTING_ROLE_POSITIONS)
        )
    )


def main() -> None:
    batting = pl.read_parquet(BATTING_PATH).filter(pl.col("origin_year") == 2024)
    workload = pl.read_parquet(WORKLOAD_PATH).filter(pl.col("origin_year") == 2024)
    threshold, destination_means = _load_parameters()
    profiles, summaries = _role_maps(pl.read_parquet(FIELDING_HISTORY_PATH))

    role_rows = []
    for player_id in batting["player_id"].to_list():
        player_id = int(player_id)
        current = profiles.get(player_id)
        summary = summaries.get(player_id)
        if current is None or summary is None:
            role_rows.append(
                {
                    "player_id": player_id,
                    "position_profile_available": 0,
                    "current_position_runs_per_600": 0.0,
                    "predicted_position_runs_per_600": 0.0,
                }
            )
            continue
        primary, share = summary
        predicted = (
            transition_smoothed_prediction(
                current,
                primary_share=share,
                destination_mean=destination_means[primary],
            )
            if share >= threshold
            else current
        )
        role_rows.append(
            {
                "player_id": player_id,
                "position_profile_available": 1,
                "current_position_runs_per_600": _position_rate(current),
                "predicted_position_runs_per_600": _position_rate(predicted),
            }
        )
    roles = pl.DataFrame(role_rows)
    actual_position = position_war_by_player_origin(
        pl.read_parquet(MLB_FIELDING_PATH),
        origin=2024,
        horizon=1,
        runs_per_win=RUNS_PER_WIN,
    )
    frame = (
        batting.select(
            "player_id",
            "actual_component_war",
            pl.col("prediction_candidate_equal_mean").alias(
                "prediction_batting_replacement_war"
            ),
            "player_stage",
        )
        .join(
            workload.select("player_id", "prediction_candidate_expected_pa"),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(roles, on="player_id", how="left", validate="1:1")
        .join(actual_position, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col("later_position_war").fill_null(0.0))
        .with_columns(
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("current_position_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_carry_position_war"),
            (
                pl.col("prediction_candidate_expected_pa")
                / 600.0
                * pl.col("predicted_position_runs_per_600")
                / RUNS_PER_WIN
            ).alias("prediction_transition_position_war"),
            (
                pl.col("actual_component_war") + pl.col("later_position_war")
            ).alias("actual_partial_war"),
        )
        .with_columns(
            pl.col("prediction_batting_replacement_war").alias(
                "prediction_batting_only_partial_war"
            ),
            (
                pl.col("prediction_batting_replacement_war")
                + pl.col("prediction_carry_position_war")
            ).alias("prediction_carry_position_partial_war"),
            (
                pl.col("prediction_batting_replacement_war")
                + pl.col("prediction_transition_position_war")
            ).alias("prediction_transition_position_partial_war"),
        )
        .sort("player_id")
    )
    actual = frame["actual_partial_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    methods = {
        "batting_only": frame["prediction_batting_only_partial_war"].to_numpy(),
        "carry_position": frame[
            "prediction_carry_position_partial_war"
        ].to_numpy(),
        "transition_position": frame[
            "prediction_transition_position_partial_war"
        ].to_numpy(),
    }
    by_stage = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        segment = frame.filter(pl.col("player_stage") == stage)
        segment_actual = segment["actual_partial_war"].to_numpy()
        by_stage[stage] = {
            name: regression_metrics(
                segment_actual,
                segment[f"prediction_{name}_partial_war"].to_numpy(),
            )
            for name in methods
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifact = write_canonical_parquet(
        frame,
        OUTPUT_ROOT / "predictions.parquet",
        table_name="hitter_positional_value_v2_predictions",
    )
    report = {
        "schema_version": "0.1",
        "status": "hitter_positional_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "2025 batting plus replacement plus positional WAR",
        "population_rows": frame.height,
        "position_profile_coverage": float(
            frame["position_profile_available"].mean()
        ),
        "metrics": {
            name: regression_metrics(actual, prediction)
            for name, prediction in methods.items()
        },
        "paired_comparisons": {
            "carry_position_minus_batting_only": paired_cluster_rmse_delta(
                actual, methods["carry_position"], methods["batting_only"], player_ids
            ),
            "transition_position_minus_batting_only": paired_cluster_rmse_delta(
                actual,
                methods["transition_position"],
                methods["batting_only"],
                player_ids,
            ),
            "transition_minus_carry_position": paired_cluster_rmse_delta(
                actual,
                methods["transition_position"],
                methods["carry_position"],
                player_ids,
            ),
        },
        "position_component_metrics": {
            "carry": regression_metrics(
                frame["later_position_war"].to_numpy(),
                frame["prediction_carry_position_war"].to_numpy(),
            ),
            "transition": regression_metrics(
                frame["later_position_war"].to_numpy(),
                frame["prediction_transition_position_war"].to_numpy(),
            ),
        },
        "by_player_stage": by_stage,
        "sources": {
            "fielding_history": {
                "path": str(FIELDING_HISTORY_PATH),
                "sha256": sha256_file(FIELDING_HISTORY_PATH),
            },
            "mlb_fielding_outcomes": {
                "path": str(MLB_FIELDING_PATH),
                "sha256": sha256_file(MLB_FIELDING_PATH),
            },
            "parameters": {
                "path": str(PARAMETER_PATH),
                "sha256": sha256_file(PARAMETER_PATH),
            },
        },
        "artifact": artifact.as_record(),
        "limitations": [
            "The positional schedule is a transparent public convention, not measured defense.",
            "Expected PA scales position value; defensive outs and DH starts are not separately projected.",
            "This is an already-exposed 2025 development test.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
