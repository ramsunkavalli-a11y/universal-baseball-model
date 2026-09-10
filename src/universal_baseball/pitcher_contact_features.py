"""Compact, pitcher-keyed contact features from certified PBP observations."""

from __future__ import annotations

import polars as pl

from universal_baseball.batted_ball_direction import batted_ball_direction_expr


GROUND_TYPES = frozenset({"ground_ball", "bunt_grounder"})
AIRBORNE_TYPES = frozenset({"fly_ball", "line_drive", "popup", "bunt_popup"})


def add_contact_classes(contacts: pl.DataFrame) -> pl.DataFrame:
    """Classify only directly observed trajectory and coordinate evidence."""

    required = {"bb_type", "hc_x", "hc_y", "batter_side"}
    missing = sorted(required - set(contacts.columns))
    if missing:
        raise ValueError(f"contacts missing classification columns: {missing}")
    trajectory = pl.col("bb_type").cast(pl.String).str.strip_chars().str.to_lowercase()
    return contacts.with_columns(
        trajectory.alias("trajectory"),
        pl.when(trajectory.is_in(sorted(GROUND_TYPES)))
        .then(pl.lit("ground"))
        .when(trajectory.is_in(sorted(AIRBORNE_TYPES)))
        .then(pl.lit("airborne"))
        .otherwise(pl.lit(None, dtype=pl.String))
        .alias("contact_plane"),
        batted_ball_direction_expr(
            pl.col("hc_x"), pl.col("hc_y"), pl.col("batter_side")
        ).alias("contact_direction"),
    )


def build_pitcher_contact_panel(contacts: pl.DataFrame) -> pl.DataFrame:
    """Aggregate one resolved physical-contact row set to pitcher-season-level."""

    required = {
        "game_date",
        "source_level",
        "source_pitcher_id",
        "source_is_in_play",
        "conflict_field_count",
        "bb_type",
        "hc_x",
        "hc_y",
        "batter_side",
    }
    missing = sorted(required - set(contacts.columns))
    if missing:
        raise ValueError(f"contacts missing pitcher-panel columns: {missing}")
    classified = add_contact_classes(
        contacts.filter(
            (pl.col("source_is_in_play") == True)  # noqa: E712
            & pl.col("source_pitcher_id").is_not_null()
        )
    ).with_columns(
        pl.col("game_date").str.slice(0, 4).cast(pl.Int64).alias("season")
    )
    return (
        classified.group_by(["season", "source_level", "source_pitcher_id"])
        .agg(
            pl.len().alias("contact_count"),
            pl.col("contact_plane").is_not_null().sum().alias("trajectory_known_count"),
            (pl.col("contact_plane") == "ground").sum().alias("ground_count"),
            (pl.col("contact_plane") == "airborne").sum().alias("airborne_count"),
            (pl.col("trajectory") == "popup").sum().alias("popup_count"),
            pl.col("contact_direction").is_not_null().sum().alias("direction_known_count"),
            (pl.col("contact_direction") == "pull").sum().alias("pull_count"),
            (
                (pl.col("contact_direction") == "pull")
                & (pl.col("contact_plane") == "airborne")
            ).sum().alias("pulled_air_count"),
            (
                (pl.col("contact_direction") == "pull")
                & (pl.col("contact_plane") == "ground")
            ).sum().alias("pulled_ground_count"),
            pl.col("conflict_field_count").gt(0).sum().alias("conflicted_contact_count"),
        )
        .rename({"source_pitcher_id": "player_id"})
        .sort(["season", "source_level", "player_id"])
    )
