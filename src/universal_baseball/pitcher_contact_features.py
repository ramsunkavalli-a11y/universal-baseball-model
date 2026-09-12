"""Compact, pitcher-keyed contact features from certified PBP observations."""

from __future__ import annotations

import polars as pl

from universal_baseball.batted_ball_direction import batted_ball_direction_expr
from universal_baseball.contact_profile import classify_contact_profile_events
from universal_baseball.hitter_v2_event_labels import classify_terminal_pa


GROUND_TYPES = frozenset({"ground_ball", "bunt_grounder"})
AIRBORNE_TYPES = frozenset({"fly_ball", "line_drive", "popup", "bunt_popup"})
CONTACT_OUTCOMES = frozenset(
    {"HR", "3B", "2B", "1B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT"}
)


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


def build_pitcher_full_bip_profile_events(contacts: pl.DataFrame) -> pl.DataFrame:
    """Return classified event rows used by both profile and outcome reducers."""

    required = {
        "game_date", "league_id", "source_level", "game_pk", "at_bat_index",
        "pitch_number", "source_batter_id", "source_pitcher_id", "batter_side",
        "bb_type", "hc_x", "hc_y", "structured_event", "result_description",
        "source_is_in_play",
    }
    if missing := sorted(required - set(contacts.columns)):
        raise ValueError(f"contacts missing full pitcher BIP columns: {missing}")
    eligible = contacts.filter(
        (pl.col("source_is_in_play") == True)  # noqa: E712
        & pl.col("source_pitcher_id").is_not_null()
    )
    if eligible.is_empty():
        return pl.DataFrame()
    canonical = eligible.select(
        pl.col("game_date").str.slice(0, 4).cast(pl.Int64).alias("season"),
        pl.col("league_id").cast(pl.Int64), "source_level", "game_pk",
        "at_bat_index", "pitch_number",
        pl.col("source_batter_id").alias("batter_mlbam_id"), "source_pitcher_id",
        pl.lit("source_default").alias("participant_authority"),
        pl.lit("source_certified_mirror").alias("result_description_authority"),
        "batter_side", "bb_type", "hc_x", "hc_y", "structured_event",
        "result_description",
    )
    sidecar = canonical.select(
        "game_pk", "at_bat_index", "pitch_number", "source_pitcher_id",
        "source_level", "structured_event", "result_description",
    )
    return (
        classify_contact_profile_events(
            canonical.drop(
                "source_pitcher_id", "source_level", "structured_event"
            )
        )
        .join(
            sidecar,
            on=["game_pk", "at_bat_index", "pitch_number"],
            how="left",
            validate="1:1",
        )
        .filter(pl.col("core_profile_eligible"))
        .select(
            "season", "source_level",
            pl.col("source_pitcher_id").alias("player_id"), "core_bin",
            "structured_event", "result_description",
        )
    )


def build_pitcher_full_bip_profile(contacts: pl.DataFrame) -> pl.DataFrame:
    """Build the same screened ten-bin BIP counts used for hitter profiles.

    Direction remains batter-relative because pull/opposite describes the contact
    the pitcher allowed. Pitcher identity is restored after the shared classifier;
    the hitter and pitcher views therefore cannot silently use different BIP rules.
    """

    events = build_pitcher_full_bip_profile_events(contacts)
    if events.is_empty():
        return pl.DataFrame(
            schema={
                "season": pl.Int64,
                "source_level": pl.String,
                "player_id": pl.Int64,
                "core_bin": pl.String,
                "occurrence_count": pl.Int64,
            }
        )
    return (
        events.group_by("season", "source_level", "player_id", "core_bin")
        .len(name="occurrence_count")
        .cast({"player_id": pl.Int64, "occurrence_count": pl.Int64})
        .sort("season", "source_level", "player_id", "core_bin")
    )


def build_pitcher_full_bip_outcomes(contacts: pl.DataFrame) -> pl.DataFrame:
    """Count context-neutral terminal outcomes inside each screened pitcher BIP bin."""

    profile = build_pitcher_full_bip_profile_events(contacts)
    schema = {
        "season": pl.Int64,
        "source_level": pl.String,
        "player_id": pl.Int64,
        "core_bin": pl.String,
        "canonical_outcome": pl.String,
        "occurrence_count": pl.Int64,
    }
    if profile.is_empty():
        return pl.DataFrame(schema=schema)
    rows = []
    for row in profile.iter_rows(named=True):
        label = classify_terminal_pa(
            event_type=row["structured_event"],
            description=row["result_description"],
        )
        if label.outcome not in CONTACT_OUTCOMES:
            continue
        rows.append({**row, "canonical_outcome": label.outcome})
    if not rows:
        return pl.DataFrame(schema=schema)
    return (
        pl.DataFrame(rows)
        .group_by(
            "season", "source_level", "player_id", "core_bin", "canonical_outcome"
        )
        .len(name="occurrence_count")
        .select(*schema)
        .cast(schema)
        .sort("season", "source_level", "player_id", "core_bin", "canonical_outcome")
    )
