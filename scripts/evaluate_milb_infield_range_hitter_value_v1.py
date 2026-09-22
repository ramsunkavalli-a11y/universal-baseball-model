#!/usr/bin/env python3
"""Test the park-adjusted MiLB infield range model inside 2025 hitter value."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_fielding_value import (
    project_player_fielding_run_rates,
)
from universal_baseball.hitter_target_architecture import (
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.storage import write_canonical_parquet


BASE_PATH = Path(
    "reports/generated/hitter-general-defense-challenger-v2/predictions.parquet"
)
OLD_POSITION_PATH = Path(
    "reports/generated/hitter-general-defense-challenger-v2/"
    "predicted-defense-by-position.parquet"
)
PROFILE_PATH = Path(
    "reports/generated/hitter-general-defense-value-v2/origin-fielding-profiles.parquet"
)
EFFECT_PATH = Path(
    "reports/generated/pbp-infield-range-re24-v1/"
    "player-position-season-effects.parquet"
)
OUTPUT_ROOT = Path("reports/generated/milb-infield-range-hitter-value-v1")
POSITION_MAP = {4: "2B", 5: "3B", 6: "SS"}
TARGET_SEASON = 2025
ORIGIN_SEASON = 2024
REGRESSION_OPPORTUNITIES = 2000.0
RUNS_PER_WIN = 10.0


def _opportunities_per_fielding_out(
    effects: pl.DataFrame, profiles: pl.DataFrame
) -> pl.DataFrame:
    profile = profiles.filter(pl.col("season") == ORIGIN_SEASON).with_columns(
        (pl.col("fielding_outs") - pl.col("mlb_fielding_outs"))
        .clip(lower_bound=0)
        .alias("milb_fielding_outs")
    )
    return (
        effects.filter(pl.col("season") == ORIGIN_SEASON)
        .with_columns(
            pl.col("responsible_position")
            .replace_strict(POSITION_MAP, return_dtype=pl.String)
            .alias("position")
        )
        .join(
            profile.select("player_id", "position", "milb_fielding_outs"),
            left_on=["responsible_fielder_id", "position"],
            right_on=["player_id", "position"],
            how="inner",
            validate="m:1",
        )
        .filter(pl.col("milb_fielding_outs") > 0)
        .group_by("position")
        .agg(
            pl.col("fielding_opportunities").sum(),
            pl.col("milb_fielding_outs").sum(),
        )
        .with_columns(
            (
                pl.col("fielding_opportunities") / pl.col("milb_fielding_outs")
            ).alias("ground_ball_opportunities_per_fielding_out")
        )
    )


def main() -> int:
    base = pl.read_parquet(BASE_PATH)
    old_position = pl.read_parquet(OLD_POSITION_PATH)
    profiles = pl.read_parquet(PROFILE_PATH)
    effects = pl.read_parquet(EFFECT_PATH)
    ratios = _opportunities_per_fielding_out(effects, profiles)
    projection = (
        project_player_fielding_run_rates(
            effects,
            target_season=TARGET_SEASON,
            regression_opportunities=REGRESSION_OPPORTUNITIES,
        )
        .with_columns(
            pl.col("responsible_position")
            .replace_strict(POSITION_MAP, return_dtype=pl.String)
            .alias("position")
        )
        .rename({"responsible_fielder_id": "player_id"})
    )
    by_position = (
        old_position.join(
            projection.select(
                "player_id", "position", "projected_range_runs_per_opportunity"
            ),
            on=["player_id", "position"],
            how="left",
            validate="1:1",
        )
        .join(ratios, on="position", how="left", validate="m:1")
        .with_columns(
            (
                pl.col("projected_range_runs_per_opportunity")
                * pl.col("predicted_general_outs")
                * pl.col("ground_ball_opportunities_per_fielding_out")
            ).alias("prediction_milb_infield_runs")
        )
        .with_columns(
            pl.when(
                pl.col("prediction_milb_infield_runs").is_not_null()
                & (pl.col("share_source") != "prior_mlb_general_outs")
            )
            .then(pl.col("prediction_milb_infield_runs"))
            .otherwise(pl.col("prediction_general_defense_runs"))
            .alias("prediction_rebuilt_position_defense_runs"),
            (
                pl.col("prediction_milb_infield_runs").is_not_null()
                & (pl.col("share_source") != "prior_mlb_general_outs")
            ).alias("milb_infield_replaced"),
        )
    )
    by_player = by_position.group_by("player_id").agg(
        pl.col("prediction_rebuilt_position_defense_runs").sum().alias(
            "prediction_rebuilt_general_defense_runs"
        ),
        pl.col("milb_infield_replaced").sum().alias("milb_infield_positions"),
    ).with_columns(
        (
            pl.col("prediction_rebuilt_general_defense_runs") / RUNS_PER_WIN
        ).alias("prediction_rebuilt_general_defense_war")
    )
    frame = (
        base.join(by_player, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("prediction_rebuilt_general_defense_war").fill_null(
                pl.col("prediction_general_defense_war")
            ),
            pl.col("milb_infield_positions").fill_null(0),
        )
        .with_columns(
            (
                pl.col("prediction_without_general_defense_war")
                + pl.col("prediction_rebuilt_general_defense_war")
            ).alias("prediction_with_rebuilt_defense_war")
        )
    )
    actual = frame["actual_partial_war_with_general_defense"].to_numpy()
    actual_component = frame["actual_general_defense_war"].to_numpy()
    player_ids = frame["player_id"].to_numpy()
    neutral = frame["prediction_without_general_defense_war"].to_numpy()
    old = frame["prediction_with_challenger_defense_war"].to_numpy()
    rebuilt = frame["prediction_with_rebuilt_defense_war"].to_numpy()
    old_component = frame["prediction_general_defense_war"].to_numpy()
    rebuilt_component = frame["prediction_rebuilt_general_defense_war"].to_numpy()

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": "0.1",
        "status": "milb_infield_range_hitter_value_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target_season": TARGET_SEASON,
        "population_rows": frame.height,
        "players_with_milb_infield_replacement": int(
            (frame["milb_infield_positions"] > 0).sum()
        ),
        "opportunity_conversion": ratios.to_dicts(),
        "model": (
            "use the MiLB RE24 2B/3B/SS projection only when the player has no "
            "prior MLB general-defense exposure; retain MLB-informed and all other "
            "position forecasts"
        ),
        "whole_value": {
            "neutral_general_defense": regression_metrics(actual, neutral),
            "old_general_defense": regression_metrics(actual, old),
            "rebuilt_general_defense": regression_metrics(actual, rebuilt),
            "rebuilt_minus_neutral": paired_cluster_rmse_delta(
                actual, rebuilt, neutral, player_ids, bootstrap_samples=5_000
            ),
            "rebuilt_minus_old": paired_cluster_rmse_delta(
                actual, rebuilt, old, player_ids, bootstrap_samples=5_000
            ),
        },
        "defense_component": {
            "neutral": regression_metrics(
                actual_component, pl.Series([0.0] * frame.height).to_numpy()
            ),
            "old": regression_metrics(actual_component, old_component),
            "rebuilt": regression_metrics(actual_component, rebuilt_component),
            "rebuilt_minus_neutral": paired_cluster_rmse_delta(
                actual_component,
                rebuilt_component,
                pl.Series([0.0] * frame.height).to_numpy(),
                player_ids,
                bootstrap_samples=5_000,
            ),
            "rebuilt_minus_old": paired_cluster_rmse_delta(
                actual_component,
                rebuilt_component,
                old_component,
                player_ids,
                bootstrap_samples=5_000,
            ),
        },
    }
    report["artifacts"] = {
        "predictions": write_canonical_parquet(
            frame,
            OUTPUT_ROOT / "predictions.parquet",
            table_name="milb_infield_range_hitter_value_predictions",
        ).as_record(),
        "by_position": write_canonical_parquet(
            by_position,
            OUTPUT_ROOT / "predictions-by-position.parquet",
            table_name="milb_infield_range_hitter_value_by_position",
        ).as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
