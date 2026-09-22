#!/usr/bin/env python3
"""Combine the rebuilt defense exposure bridge with frozen U1 skill."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.player_value_defense_projection import (
    GENERAL_POSITIONS,
    predict_general_range_skill,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


BASE_PATH = Path("reports/generated/hitter-baserunning-value-v2/predictions.parquet")
EXPOSURE_PATH = Path(
    "reports/generated/hitter-defense-exposure-v2/chronological-predictions.parquet"
)
EXPOSURE_REPORT_PATH = Path("reports/generated/hitter-defense-exposure-v2/report.json")
PROFILE_PATH = Path(
    "reports/generated/hitter-general-defense-value-v2/origin-fielding-profiles.parquet"
)
ACTUAL_POSITION_PATH = Path(
    "reports/generated/hitter-general-defense-value-v2/actual-defense-by-position.parquet"
)
OLD_BRIDGE_PATH = Path(
    "reports/generated/hitter-general-defense-value-v2/predictions.parquet"
)
GENERAL_PARAMETER_PATH = Path("docs/defense-v1-confirmation-parameters.json")
CONVERSION_PARAMETER_PATH = Path(
    "docs/player-value-v1-defense-native-run-conversion-parameters.json"
)
OUTPUT_ROOT = Path("reports/generated/hitter-general-defense-challenger-v2")
RUNS_PER_WIN = 10.0


def _skill_rows(
    players: pl.DataFrame,
    profiles: pl.DataFrame,
    *,
    exposure_column: str,
    general_parameters: dict[str, Any],
    conversion: dict[str, Any],
) -> tuple[pl.DataFrame, pl.DataFrame]:
    profile_lookup = {
        (int(row["player_id"]), str(row["position"])): row
        for row in profiles.filter(pl.col("season") == 2024).iter_rows(named=True)
    }
    rows = []
    player_audit = []
    for player in players.iter_rows(named=True):
        player_id = int(player["player_id"])
        predicted_total = float(player[exposure_column])
        position_profiles = [
            profile_lookup[(player_id, position)]
            for position in sorted(GENERAL_POSITIONS)
            if (player_id, position) in profile_lookup
        ]
        mlb_total = sum(float(row["mlb_fielding_outs"]) for row in position_profiles)
        affiliated_total = sum(float(row["fielding_outs"]) for row in position_profiles)
        share_source = (
            "prior_mlb_general_outs"
            if mlb_total > 0
            else "prior_affiliated_general_outs"
            if affiliated_total > 0
            else "neutral_no_position_profile"
        )
        share_denominator = mlb_total if mlb_total > 0 else affiliated_total
        eligible_positions = 0
        allocated = 0.0
        for profile in position_profiles:
            position = str(profile["position"])
            share_numerator = float(
                profile[
                    "mlb_fielding_outs"
                    if mlb_total > 0
                    else "fielding_outs"
                ]
            )
            share = share_numerator / share_denominator if share_denominator > 0 else 0.0
            predicted_outs = predicted_total * share
            skill, family = predict_general_range_skill(
                profile,
                tracked_z=None,
                parameters=general_parameters,
            )
            if family == "U1":
                eligible_positions += 1
            allocated += predicted_outs
            rows.append(
                {
                    "player_id": player_id,
                    "position": position,
                    "predicted_general_outs": predicted_outs,
                    "general_range_skill": skill,
                    "general_range_family": family,
                    "share_source": share_source,
                    "run_rate_per_z_out": float(
                        conversion["parameters_by_position"][position][
                            "run_rate_per_z_opportunity"
                        ]
                    ),
                }
            )
        player_audit.append(
            {
                "player_id": player_id,
                "predicted_general_outs": predicted_total,
                "allocated_general_outs": allocated,
                "general_position_share_source": share_source,
                "eligible_general_positions": eligible_positions,
            }
        )
    by_position = pl.DataFrame(rows)
    centers = (
        by_position.filter(
            (pl.col("general_range_family") == "U1")
            & (pl.col("predicted_general_outs") > 0)
        )
        .group_by("position")
        .agg(
            (
                (
                    pl.col("general_range_skill")
                    * pl.col("predicted_general_outs")
                ).sum()
                / pl.col("predicted_general_outs").sum()
            ).alias("exposure_weighted_skill_center")
        )
    )
    by_position = (
        by_position.join(centers, on="position", how="left", validate="m:1")
        .with_columns(
            pl.col("exposure_weighted_skill_center").fill_null(0.0)
        )
        .with_columns(
            pl.when(pl.col("general_range_family") == "U1")
            .then(
                (
                    pl.col("general_range_skill")
                    - pl.col("exposure_weighted_skill_center")
                )
                * pl.col("predicted_general_outs")
                * pl.col("run_rate_per_z_out")
            )
            .otherwise(0.0)
            .alias("prediction_general_defense_runs")
        )
        .sort(["player_id", "position"])
    )
    by_player = (
        pl.DataFrame(player_audit)
        .join(
            by_position.group_by("player_id").agg(
                pl.col("prediction_general_defense_runs").sum()
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("prediction_general_defense_runs").fill_null(0.0)
        )
        .with_columns(
            (pl.col("prediction_general_defense_runs") / RUNS_PER_WIN).alias(
                "prediction_general_defense_war"
            )
        )
        .sort("player_id")
    )
    return by_player, by_position


def main() -> None:
    exposure_report = json.loads(EXPOSURE_REPORT_PATH.read_text(encoding="utf-8"))
    if not exposure_report["confirmation_passed"]:
        raise RuntimeError("defense exposure challenger did not pass confirmation")
    selected_exposure = str(exposure_report["selected_challenger"])
    exposure_column = f"prediction__{selected_exposure}"
    exposure = pl.read_parquet(EXPOSURE_PATH).filter(pl.col("origin_year") == 2024)
    profiles = pl.read_parquet(PROFILE_PATH)
    general_parameters = json.loads(
        GENERAL_PARAMETER_PATH.read_text(encoding="utf-8")
    )["parameters"]["general"]
    conversion = json.loads(
        CONVERSION_PARAMETER_PATH.read_text(encoding="utf-8")
    )["general_range"]
    predicted_by_player, predicted_by_position = _skill_rows(
        exposure.select("player_id", exposure_column),
        profiles,
        exposure_column=exposure_column,
        general_parameters=general_parameters,
        conversion=conversion,
    )
    actual_by_position = pl.read_parquet(ACTUAL_POSITION_PATH)
    actual_by_player = (
        actual_by_position.group_by("player_id")
        .agg(pl.col("actual_general_defense_runs").sum())
        .with_columns(
            (pl.col("actual_general_defense_runs") / RUNS_PER_WIN).alias(
                "actual_general_defense_war"
            )
        )
    )
    old_bridge = pl.read_parquet(OLD_BRIDGE_PATH).select(
        "player_id",
        pl.col("prediction_general_defense_war").alias(
            "prediction_old_bridge_defense_war"
        ),
    )
    frame = (
        pl.read_parquet(BASE_PATH)
        .join(
            exposure.select(
                "player_id",
                pl.col(exposure_column).alias("prediction_general_defensive_outs"),
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(predicted_by_player, on="player_id", how="left", validate="1:1")
        .join(actual_by_player, on="player_id", how="left", validate="1:1")
        .join(old_bridge, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("prediction_general_defense_war").fill_null(0.0),
            pl.col("prediction_general_defense_runs").fill_null(0.0),
            pl.col("actual_general_defense_war").fill_null(0.0),
            pl.col("actual_general_defense_runs").fill_null(0.0),
        )
        .with_columns(
            (
                pl.col("actual_batting_position_baserunning_war")
                + pl.col("actual_general_defense_war")
            ).alias("actual_partial_war_with_general_defense"),
            pl.col("prediction_position_plus_baserunning_war").alias(
                "prediction_without_general_defense_war"
            ),
            (
                pl.col("prediction_position_plus_baserunning_war")
                + pl.col("prediction_general_defense_war")
            ).alias("prediction_with_challenger_defense_war"),
            (
                pl.col("prediction_position_plus_baserunning_war")
                + pl.col("prediction_old_bridge_defense_war")
            ).alias("prediction_with_old_bridge_defense_war"),
        )
        .sort("player_id")
    )
    actual = frame["actual_partial_war_with_general_defense"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    methods = {
        "neutral_defense": "prediction_without_general_defense_war",
        "old_bridge_defense": "prediction_with_old_bridge_defense_war",
        "challenger_defense": "prediction_with_challenger_defense_war",
    }
    metrics = {
        name: regression_metrics(actual, frame[column].to_numpy())
        for name, column in methods.items()
    }
    paired = {
        f"{name}_minus_neutral": paired_cluster_rmse_delta(
            actual,
            frame[column].to_numpy(),
            frame[methods["neutral_defense"]].to_numpy(),
            player_ids,
        )
        for name, column in methods.items()
        if name != "neutral_defense"
    }
    actual_component = frame["actual_general_defense_war"].to_numpy()
    candidate_component = frame["prediction_general_defense_war"].to_numpy()
    old_component = frame["prediction_old_bridge_defense_war"].to_numpy()
    zero_component = candidate_component * 0.0
    component_metrics = {
        "neutral_zero": regression_metrics(actual_component, zero_component),
        "old_bridge": regression_metrics(actual_component, old_component),
        "challenger": regression_metrics(actual_component, candidate_component),
    }

    by_stage = {}
    for stage in ("current_mlb", "upper_minors", "lower_minors"):
        segment = frame.filter(pl.col("player_stage") == stage)
        target = segment["actual_partial_war_with_general_defense"].to_numpy()
        by_stage[stage] = {
            name: regression_metrics(target, segment[column].to_numpy())
            for name, column in methods.items()
        }

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "predictions": write_canonical_parquet(
            frame,
            OUTPUT_ROOT / "predictions.parquet",
            table_name="hitter_general_defense_challenger_v2_predictions",
        ).as_record(),
        "predicted_by_position": write_canonical_parquet(
            predicted_by_position,
            OUTPUT_ROOT / "predicted-defense-by-position.parquet",
            table_name="hitter_general_defense_challenger_v2_by_position",
        ).as_record(),
    }
    report = {
        "schema_version": "0.1",
        "status": "hitter_general_defense_challenger_value_test_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": (
            "2025 batting plus replacement plus position plus baserunning plus "
            "general defense WAR"
        ),
        "selected_exposure_model": selected_exposure,
        "position_share_rule": (
            "prior MLB general-position out shares when available; otherwise prior "
            "affiliated general-position out shares"
        ),
        "skill_model": "frozen U1 general range with neutral B0 fallback",
        "metrics": metrics,
        "paired_comparisons": paired,
        "component_metrics": component_metrics,
        "component_paired_comparisons": {
            "challenger_minus_neutral": paired_cluster_rmse_delta(
                actual_component,
                candidate_component,
                zero_component,
                player_ids,
            ),
            "challenger_minus_old_bridge": paired_cluster_rmse_delta(
                actual_component,
                candidate_component,
                old_component,
                player_ids,
            ),
        },
        "by_player_stage": by_stage,
        "coverage": predicted_by_player.group_by(
            "general_position_share_source"
        )
        .agg(
            pl.len().alias("players"),
            (pl.col("eligible_general_positions") > 0).sum().alias(
                "players_with_eligible_u1_skill"
            ),
        )
        .sort("general_position_share_source")
        .to_dicts(),
        "artifacts": artifacts,
        "sources": {
            "base": {"path": str(BASE_PATH), "sha256": sha256_file(BASE_PATH)},
            "exposure": {
                "path": str(EXPOSURE_PATH),
                "sha256": sha256_file(EXPOSURE_PATH),
            },
            "exposure_report": {
                "path": str(EXPOSURE_REPORT_PATH),
                "sha256": sha256_file(EXPOSURE_REPORT_PATH),
            },
            "profiles": {
                "path": str(PROFILE_PATH),
                "sha256": sha256_file(PROFILE_PATH),
            },
            "actual_by_position": {
                "path": str(ACTUAL_POSITION_PATH),
                "sha256": sha256_file(ACTUAL_POSITION_PATH),
            },
            "general_parameters": {
                "path": str(GENERAL_PARAMETER_PATH),
                "sha256": sha256_file(GENERAL_PARAMETER_PATH),
            },
            "conversion_parameters": {
                "path": str(CONVERSION_PARAMETER_PATH),
                "sha256": sha256_file(CONVERSION_PARAMETER_PATH),
            },
        },
        "limitations": [
            "This is an already-exposed 2025 development confirmation.",
            "Catcher throwing, blocking, and framing remain neutral.",
            "Affiliated position shares improve entrant coverage but are not a direct forecast of MLB defensive alignment.",
        ],
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
