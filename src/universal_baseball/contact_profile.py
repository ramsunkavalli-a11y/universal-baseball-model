"""Reusable-source contact classification for production Performance profiles.

The official-PA Performance mapper in :mod:`performance_events` remains the
canonical exhaustive PA representation. Historical player-season materialization
should not require an all-history official PBP replay merely to recover contact
shape. This module therefore classifies an already-resolved physical contact
row using the source fields that survived certification:

- trajectory from Gameday hitData-derived ``bb_type``;
- Pull/Center/Opposite from Gameday ``hc_x/hc_y`` and batter side;
- foul-air screening from the certified result-narrative phrase ``foul territory``;
- participant identity supplied by the caller after the ADR 020 source/default
  versus official-exception authority policy has been applied.

It does not decide whether a raw pitch is a contact and it does not repair a
participant. Those are upstream quality/authority decisions.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.batted_ball_direction import (
    batted_ball_direction_expr,
    field_spray_angle_expr,
)
from universal_baseball.performance_events import (
    FOUL_AIR_TRAJECTORY_FAMILIES,
    FOUL_TERRITORY_REGEX,
    TRAJECTORY_FAMILY,
)


CONTACT_PROFILE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    "batter_mlbam_id": pl.Int64,
    "participant_authority": pl.String,
    "result_description_authority": pl.String,
    "trajectory_family": pl.String,
    "spray_angle": pl.Float64,
    "direction": pl.String,
    "foul_air_status": pl.String,
    "is_foul_air_out": pl.Boolean,
    "core_bin": pl.String,
    "core_profile_eligible": pl.Boolean,
    "contact_profile_status": pl.String,
}


def _trajectory_family_expr(bb_type_column: str) -> pl.Expr:
    expression = pl.lit("UNKNOWN")
    for source_value, family in TRAJECTORY_FAMILY.items():
        expression = pl.when(pl.col(bb_type_column) == source_value).then(
            pl.lit(family)
        ).otherwise(expression)
    return expression.alias("trajectory_family")


def classify_contact_profile_events(frame: pl.DataFrame) -> pl.DataFrame:
    """Classify one resolved row per physical contact into the screened core view.

    Required input columns are intentionally canonical rather than tied to the
    raw armstjc names. ``result_description`` may be the certified reusable
    narrative mirror when official play-sequence data are not materialized.
    ``participant_authority`` must identify whether the batter is the reusable
    default or an official exception overlay; this function preserves but does
    not infer that authority.
    """

    required = {
        "season",
        "league_id",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "participant_authority",
        "result_description_authority",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"contact profile input missing columns: {missing}")
    if frame.is_empty():
        return pl.DataFrame(schema=CONTACT_PROFILE_SCHEMA)

    key = ["game_pk", "at_bat_index", "pitch_number"]
    duplicates = frame.group_by(key).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError("contact profile input must contain one row per physical contact key")

    working = (
        frame.with_columns(
            pl.col("season").cast(pl.Int64, strict=False),
            pl.col("league_id").cast(pl.Int64, strict=False),
            pl.col("game_pk").cast(pl.Int64, strict=False),
            pl.col("at_bat_index").cast(pl.Int64, strict=False),
            pl.col("pitch_number").cast(pl.Int64, strict=False),
            pl.col("batter_mlbam_id").cast(pl.Int64, strict=False),
            pl.col("participant_authority").cast(pl.String),
            pl.col("result_description_authority").cast(pl.String),
            pl.col("batter_side").cast(pl.String),
            pl.col("bb_type").cast(pl.String),
            pl.col("hc_x").cast(pl.Float64, strict=False),
            pl.col("hc_y").cast(pl.Float64, strict=False),
            pl.col("result_description").cast(pl.String),
        )
        .drop_nulls(["season", "league_id", *key, "batter_mlbam_id"])
        .with_columns(_trajectory_family_expr("bb_type"))
        .with_columns(
            field_spray_angle_expr(pl.col("hc_x"), pl.col("hc_y")).alias("spray_angle"),
            batted_ball_direction_expr(
                pl.col("hc_x"), pl.col("hc_y"), pl.col("batter_side")
            ).alias("direction"),
        )
    )

    trajectory = pl.col("trajectory_family")
    direction = pl.col("direction")
    candidate_foul_air = trajectory.is_in(sorted(FOUL_AIR_TRAJECTORY_FAMILIES))
    narrative_present = (
        pl.col("result_description").is_not_null()
        & (pl.col("result_description").str.strip_chars().str.len_chars() > 0)
    )
    explicit_foul_territory = (
        candidate_foul_air
        & narrative_present
        & pl.col("result_description").str.contains(FOUL_TERRITORY_REGEX)
    )

    foul_air_status = (
        pl.when(~candidate_foul_air)
        .then(pl.lit("not_foul_air_trajectory"))
        .when(~narrative_present)
        .then(pl.lit("unknown_missing_result_description"))
        .when(explicit_foul_territory)
        .then(pl.lit("foul_air_foul_territory"))
        .otherwise(pl.lit("not_foul_air_result_description"))
    )
    is_foul_air_out = (
        pl.when(~candidate_foul_air)
        .then(pl.lit(False))
        .when(~narrative_present)
        .then(pl.lit(None, dtype=pl.Boolean))
        .otherwise(explicit_foul_territory)
    )

    pre_screen_bin = (
        pl.when(trajectory == "IFFB")
        .then(pl.lit("IFFB"))
        .when((trajectory == "OFFB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("OFFB")], separator="_"))
        .when((trajectory == "LD") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("LD")], separator="_"))
        .when((trajectory == "GB") & direction.is_not_null())
        .then(pl.concat_str([direction.str.to_uppercase(), pl.lit("GB")], separator="_"))
        .otherwise(pl.lit(None, dtype=pl.String))
    )

    core_bin = (
        pl.when(
            pre_screen_bin.is_not_null()
            & (
                ~candidate_foul_air
                | ((is_foul_air_out == False) & narrative_present)  # noqa: E712
            )
        )
        .then(pre_screen_bin)
        .otherwise(pl.lit(None, dtype=pl.String))
    )

    profile_status = (
        pl.when(trajectory == "BUNT")
        .then(pl.lit("special_bunt"))
        .when(trajectory == "UNKNOWN")
        .then(pl.lit("unknown_missing_trajectory"))
        .when(trajectory.is_in(["OFFB", "LD", "GB"]) & direction.is_null())
        .then(pl.lit("unknown_missing_direction"))
        .when(candidate_foul_air & ~narrative_present)
        .then(pl.lit("unknown_missing_foul_narrative"))
        .when(explicit_foul_territory)
        .then(pl.lit("foul_air_excluded"))
        .when(core_bin.is_not_null())
        .then(pl.lit("core_contact"))
        .otherwise(pl.lit("unknown_unclassified_contact"))
    )

    return (
        working.with_columns(
            foul_air_status.alias("foul_air_status"),
            is_foul_air_out.alias("is_foul_air_out"),
            core_bin.alias("core_bin"),
            profile_status.alias("contact_profile_status"),
        )
        .with_columns(pl.col("core_bin").is_not_null().alias("core_profile_eligible"))
        .select(list(CONTACT_PROFILE_SCHEMA))
        .cast(CONTACT_PROFILE_SCHEMA, strict=True)
        .sort(key)
    )
