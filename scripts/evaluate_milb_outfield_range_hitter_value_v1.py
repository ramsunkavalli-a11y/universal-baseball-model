#!/usr/bin/env python3
"""Test park-adjusted MiLB outfield range inside 2025 hitter value."""

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
INFIELD_EFFECT_PATH = Path(
    "reports/generated/pbp-infield-range-re24-v1/"
    "player-position-season-effects.parquet"
)
OUTFIELD_EFFECT_PATH = Path(
    "reports/generated/pbp-outfield-range-re24-v1/"
    "player-position-season-effects.parquet"
)
OUTPUT_ROOT = Path("reports/generated/milb-outfield-range-hitter-value-v1")
POSITION_MAP = {4: "2B", 5: "3B", 6: "SS", 7: "LF", 8: "CF", 9: "RF"}
INFIELD_POSITIONS = {"2B", "3B", "SS"}
OUTFIELD_POSITIONS = {"LF", "CF", "RF"}
TARGET_SEASON = 2025
ORIGIN_SEASON = 2024
REGRESSION_OPPORTUNITIES = {"infield": 2000.0, "outfield": 3000.0}
RUNS_PER_WIN = 10.0


def _opportunities_per_fielding_out(
    effects: pl.DataFrame, profiles: pl.DataFrame, positions: set[str]
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
        .filter(pl.col("position").is_in(sorted(positions)))
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
            ).alias("range_opportunities_per_fielding_out")
        )
    )


def _projection(
    effects: pl.DataFrame,
    profiles: pl.DataFrame,
    *,
    positions: set[str],
    regression: float,
    label: str,
) -> pl.DataFrame:
    ratios = _opportunities_per_fielding_out(effects, profiles, positions)
    projected = (
        project_player_fielding_run_rates(
            effects,
            target_season=TARGET_SEASON,
            regression_opportunities=regression,
        )
        .with_columns(
            pl.col("responsible_position")
            .replace_strict(POSITION_MAP, return_dtype=pl.String)
            .alias("position")
        )
        .filter(pl.col("position").is_in(sorted(positions)))
        .rename({"responsible_fielder_id": "player_id"})
        .join(ratios, on="position", how="left", validate="m:1")
        .with_columns(
            (
                pl.col("projected_range_runs_per_opportunity")
                * pl.col("range_opportunities_per_fielding_out")
            ).alias(f"{label}_runs_per_projected_out")
        )
    )
    return projected.select("player_id", "position", f"{label}_runs_per_projected_out")


def _report_variant(
    frame: pl.DataFrame, prediction_column: str
) -> dict[str, object]:
    actual = frame["actual_partial_war_with_general_defense"].to_numpy()
    neutral = frame["prediction_without_general_defense_war"].to_numpy()
    old = frame["prediction_with_challenger_defense_war"].to_numpy()
    candidate = frame[prediction_column].to_numpy()
    ids = frame["player_id"].to_numpy()
    return {
        "metrics": regression_metrics(actual, candidate),
        "minus_neutral": paired_cluster_rmse_delta(
            actual, candidate, neutral, ids, bootstrap_samples=5_000
        ),
        "minus_old": paired_cluster_rmse_delta(
            actual, candidate, old, ids, bootstrap_samples=5_000
        ),
    }


def _report_component_variant(
    frame: pl.DataFrame, prediction_column: str
) -> dict[str, object]:
    actual = frame["actual_general_defense_war"].to_numpy()
    neutral = pl.Series("neutral", [0.0] * frame.height).to_numpy()
    old = frame["prediction_general_defense_war"].to_numpy()
    candidate = frame[prediction_column].to_numpy()
    ids = frame["player_id"].to_numpy()
    return {
        "metrics": regression_metrics(actual, candidate),
        "minus_neutral": paired_cluster_rmse_delta(
            actual, candidate, neutral, ids, bootstrap_samples=5_000
        ),
        "minus_old": paired_cluster_rmse_delta(
            actual, candidate, old, ids, bootstrap_samples=5_000
        ),
    }


def main() -> int:
    base = pl.read_parquet(BASE_PATH)
    old_position = pl.read_parquet(OLD_POSITION_PATH)
    profiles = pl.read_parquet(PROFILE_PATH)
    infield = pl.read_parquet(INFIELD_EFFECT_PATH)
    outfield = pl.read_parquet(OUTFIELD_EFFECT_PATH)
    infield_projection = _projection(
        infield,
        profiles,
        positions=INFIELD_POSITIONS,
        regression=REGRESSION_OPPORTUNITIES["infield"],
        label="infield",
    )
    outfield_projection = _projection(
        outfield,
        profiles,
        positions=OUTFIELD_POSITIONS,
        regression=REGRESSION_OPPORTUNITIES["outfield"],
        label="outfield",
    )
    by_position = (
        old_position.join(
            infield_projection,
            on=["player_id", "position"],
            how="left",
            validate="1:1",
        )
        .join(
            outfield_projection,
            on=["player_id", "position"],
            how="left",
            validate="1:1",
        )
        .with_columns(
            (
                pl.col("outfield_runs_per_projected_out")
                * pl.col("predicted_general_outs")
            ).alias("prediction_milb_outfield_runs"),
            (
                pl.col("infield_runs_per_projected_out")
                * pl.col("predicted_general_outs")
            ).alias("prediction_milb_infield_runs"),
        )
        .with_columns(
            pl.when(
                pl.col("prediction_milb_outfield_runs").is_not_null()
                & (pl.col("share_source") != "prior_mlb_general_outs")
            )
            .then(pl.col("prediction_milb_outfield_runs"))
            .otherwise(pl.col("prediction_general_defense_runs"))
            .alias("prediction_outfield_rebuilt_runs"),
            pl.when(
                pl.col("prediction_milb_infield_runs").is_not_null()
                & (pl.col("share_source") != "prior_mlb_general_outs")
            )
            .then(pl.col("prediction_milb_infield_runs"))
            .when(
                pl.col("prediction_milb_outfield_runs").is_not_null()
                & (pl.col("share_source") != "prior_mlb_general_outs")
            )
            .then(pl.col("prediction_milb_outfield_runs"))
            .otherwise(pl.col("prediction_general_defense_runs"))
            .alias("prediction_combined_rebuilt_runs"),
        )
    )
    by_player = by_position.group_by("player_id").agg(
        pl.col("prediction_outfield_rebuilt_runs").sum(),
        pl.col("prediction_combined_rebuilt_runs").sum(),
        pl.col("prediction_milb_outfield_runs").is_not_null().sum().alias(
            "milb_outfield_positions"
        ),
    ).with_columns(
        (
            pl.col("prediction_outfield_rebuilt_runs") / RUNS_PER_WIN
        ).alias("prediction_outfield_rebuilt_war"),
        (
            pl.col("prediction_combined_rebuilt_runs") / RUNS_PER_WIN
        ).alias("prediction_combined_rebuilt_war"),
    )
    frame = (
        base.join(by_player, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.col("prediction_outfield_rebuilt_war").fill_null(0.0),
            pl.col("prediction_combined_rebuilt_war").fill_null(0.0),
            (
                pl.col("prediction_without_general_defense_war")
                + pl.col("prediction_outfield_rebuilt_war").fill_null(0.0)
            ).alias("prediction_with_outfield_rebuilt_war"),
            (
                pl.col("prediction_without_general_defense_war")
                + pl.col("prediction_combined_rebuilt_war").fill_null(0.0)
            ).alias("prediction_with_combined_rebuilt_war"),
        )
    )
    actual = frame["actual_partial_war_with_general_defense"].to_numpy()
    report = {
        "schema_version": "0.1",
        "status": "milb_outfield_range_hitter_value_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target_season": TARGET_SEASON,
        "population_rows": frame.height,
        "players_with_milb_outfield_projection": int(
            (frame["milb_outfield_positions"].fill_null(0) > 0).sum()
        ),
        "whole_value_baselines": {
            "neutral_general_defense": regression_metrics(
                actual, frame["prediction_without_general_defense_war"].to_numpy()
            ),
            "old_general_defense": regression_metrics(
                actual, frame["prediction_with_challenger_defense_war"].to_numpy()
            ),
        },
        "defense_component_baselines": {
            "neutral": regression_metrics(
                frame["actual_general_defense_war"].to_numpy(),
                pl.Series("neutral", [0.0] * frame.height).to_numpy(),
            ),
            "old_general_defense": regression_metrics(
                frame["actual_general_defense_war"].to_numpy(),
                frame["prediction_general_defense_war"].to_numpy(),
            ),
        },
        "outfield_only": _report_variant(
            frame, "prediction_with_outfield_rebuilt_war"
        ),
        "combined_infield_outfield": _report_variant(
            frame, "prediction_with_combined_rebuilt_war"
        ),
        "outfield_only_component": _report_component_variant(
            frame, "prediction_outfield_rebuilt_war"
        ),
        "combined_infield_outfield_component": _report_component_variant(
            frame, "prediction_combined_rebuilt_war"
        ),
    }
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    report["artifacts"] = {
        "predictions": write_canonical_parquet(
            frame,
            OUTPUT_ROOT / "predictions.parquet",
            table_name="milb_outfield_range_hitter_value_predictions",
        ).as_record(),
        "by_position": write_canonical_parquet(
            by_position,
            OUTPUT_ROOT / "predictions-by-position.parquet",
            table_name="milb_outfield_range_hitter_value_by_position",
        ).as_record(),
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
