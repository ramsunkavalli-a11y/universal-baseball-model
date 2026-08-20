"""Deterministic batting position/role profile construction.

Builds descriptive player-season role profiles from certified fielding usage.
This module does not project future positions or fit a statistical model.
"""

from __future__ import annotations

from dataclasses import dataclass

import polars as pl


BATTING_ROLE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH")
DEFENSIVE_ROLE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF")
POSITION_CODE_ORDER = {
    "C": 2,
    "1B": 3,
    "2B": 4,
    "3B": 5,
    "SS": 6,
    "LF": 7,
    "CF": 8,
    "RF": 9,
    "DH": 10,
}


@dataclass(frozen=True, slots=True)
class BattingRoleProfiles:
    profile: pl.DataFrame
    player_season: pl.DataFrame


def build_batting_role_profiles(fielding_usage: pl.DataFrame) -> BattingRoleProfiles:
    """Build observed batting-role and defensive-out profiles by player-season."""

    required = {
        "season",
        "player_id",
        "position_abbreviation",
        "games_played",
        "games_started",
        "fielding_outs",
    }
    missing = sorted(required - set(fielding_usage.columns))
    if missing:
        raise ValueError(f"fielding usage missing batting-role fields: {missing}")
    if fielding_usage.is_empty():
        raise ValueError("fielding usage must not be empty")

    filtered = fielding_usage.filter(
        pl.col("position_abbreviation").is_in(BATTING_ROLE_POSITIONS)
    )
    if filtered.is_empty():
        raise ValueError("fielding usage contains no batting-role positions")
    if filtered.filter(
        (pl.col("games_played") < 0)
        | (pl.col("games_started") < 0)
        | (pl.col("fielding_outs") < 0)
    ).height:
        raise ValueError("batting-role fielding usage contains negative counts")

    aggregated = (
        filtered.group_by(["season", "player_id", "position_abbreviation"])
        .agg(
            pl.col("games_played").sum().cast(pl.Int64).alias("games_played"),
            pl.col("games_started").sum().cast(pl.Int64).alias("games_started"),
            pl.col("fielding_outs").sum().cast(pl.Int64).alias("fielding_outs"),
        )
        .with_columns(
            pl.col("position_abbreviation")
            .replace_strict(POSITION_CODE_ORDER, return_dtype=pl.Int64)
            .alias("position_code_order")
        )
    )

    totals = aggregated.group_by(["season", "player_id"]).agg(
        pl.col("games_started").sum().alias("total_games_started"),
        pl.col("games_played").sum().alias("total_position_appearances"),
        pl.col("fielding_outs").sum().alias("total_defensive_outs"),
    )
    profile = aggregated.join(totals, on=["season", "player_id"], how="left").with_columns(
        pl.when(pl.col("total_games_started") > 0)
        .then(pl.lit("games_started"))
        .otherwise(pl.lit("games_played_fallback"))
        .alias("role_evidence_mode"),
        pl.when(pl.col("total_games_started") > 0)
        .then(pl.col("games_started"))
        .otherwise(pl.col("games_played"))
        .cast(pl.Int64)
        .alias("role_events"),
    )
    profile = profile.with_columns(
        pl.col("role_events").sum().over(["season", "player_id"]).alias("total_role_events")
    ).filter(pl.col("total_role_events") > 0)
    profile = profile.with_columns(
        (pl.col("role_events") / pl.col("total_role_events"))
        .cast(pl.Float64)
        .alias("role_probability"),
        pl.when(pl.col("total_defensive_outs") > 0)
        .then(pl.col("fielding_outs") / pl.col("total_defensive_outs"))
        .otherwise(pl.lit(None, dtype=pl.Float64))
        .alias("defensive_probability"),
    )

    sums = profile.group_by(["season", "player_id"]).agg(
        pl.col("role_probability").sum().alias("role_probability_sum")
    )
    if sums.filter((pl.col("role_probability_sum") - 1.0).abs() > 1e-12).height:
        raise RuntimeError("batting role probabilities do not sum to one")

    primary = (
        profile.sort(
            [
                "season",
                "player_id",
                "role_events",
                "games_started",
                "fielding_outs",
                "games_played",
                "position_code_order",
            ],
            descending=[False, False, True, True, True, True, False],
        )
        .unique(subset=["season", "player_id"], keep="first", maintain_order=True)
        .select(
            "season",
            "player_id",
            pl.col("position_abbreviation").alias("primary_position"),
            pl.col("role_probability").alias("primary_role_share"),
            "role_evidence_mode",
            "total_role_events",
            "total_games_started",
            "total_position_appearances",
            "total_defensive_outs",
        )
    )
    if primary.group_by(["season", "player_id"]).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("batting role primary-position summary violates player-season grain")

    return BattingRoleProfiles(
        profile=profile.sort(["season", "player_id", "position_code_order"]),
        player_season=primary.sort(["season", "player_id"]),
    )
