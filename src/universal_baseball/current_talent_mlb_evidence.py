"""Build MLB player-game Performance evidence for Current Talent snapshots.

Baseball Savant already carries official MLB participant identities, true-PA
terminal outcomes, game dates, and contact evidence. This adapter projects that
certified source into the same player-game contract used by affiliated MiLB so
chronological snapshot code is source-agnostic.

ADR 024 preserves true-PA/result opportunities separately from physical
contact/profile observations.  No season-end totals are used here. Every count is
derived from game-grain Savant evidence that occurred before a future validation
cutoff.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import validate_player_game_evidence
from universal_baseball.mlb_performance import MLB_LEAGUE_IDS
from universal_baseball.mlb_performance_materialization import classify_mlb_savant_contacts
from universal_baseball.performance_events import (
    BB_HBP_EVENT_TYPES,
    STRIKEOUT_EVENT_TYPES,
)


MLB_LEVEL_GROUP = "MLB"
MLB_CAPABILITY_TIER = "mlb_savant_result_contact_profile_v2"
MLB_PARTICIPANT_AUTHORITY = "savant_official"

# True PA terminal events that are neither the two outcome core families nor a
# contact family are explicit known special non-contact outcomes. Any remaining
# PA identity residual stays signed and visible rather than being imputed.
KNOWN_SPECIAL_NONCONTACT_EVENT_TYPES = frozenset(
    {
        "catcher_interf",
        "batter_interference",
        "os_ruling_pending_primary",
    }
)


def build_mlb_current_talent_player_game_evidence(
    savant: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Project assigned Savant rows to the universal player-game evidence contract."""

    required = {
        "game_date",
        "game_year",
        "game_pk",
        "league_id",
        "batter_mlbam_id",
        "events",
        "is_plate_appearance_terminal",
        "is_contact",
        "at_bat_index",
        "pitch_number",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
        "result_description",
    }
    missing = sorted(required - set(savant.columns))
    if missing:
        raise ValueError(f"MLB Current Talent Savant input missing fields: {missing}")
    if savant.is_empty():
        raise ValueError("MLB Current Talent Savant input must not be empty")

    observed_leagues = {
        int(value)
        for value in savant.get_column("league_id")
        .cast(pl.Int64, strict=False)
        .drop_nulls()
        .unique()
        .to_list()
    }
    unknown_leagues = sorted(observed_leagues - set(MLB_LEAGUE_IDS))
    if unknown_leagues:
        raise ValueError(f"MLB Current Talent input contains non-MLB league IDs: {unknown_leagues}")

    terminal = savant.filter(pl.col("is_plate_appearance_terminal"))
    if terminal.is_empty():
        raise ValueError("MLB Current Talent input contains no true PA terminal rows")
    if terminal.filter(pl.col("batter_mlbam_id").is_null()).height:
        raise ValueError("MLB true PA terminal rows contain null batter identity")
    duplicate_pa = terminal.group_by(["game_pk", "at_bat_index"]).len().filter(pl.col("len") > 1)
    if not duplicate_pa.is_empty():
        raise ValueError("MLB Savant contains duplicate true PA terminal sequences")

    terminal_games = terminal.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_game_date"),
        pl.col("game_year").cast(pl.Int64).alias("season"),
        pl.col("league_id").cast(pl.Int64),
        pl.col("game_pk").cast(pl.Int64),
        pl.col("batter_mlbam_id").cast(pl.Int64).alias("player_id"),
        pl.col("events").cast(pl.String),
        pl.col("is_contact").cast(pl.Boolean),
    )
    if terminal_games.filter(pl.col("_game_date").is_null()).height:
        raise ValueError("MLB true PA terminal rows contain unparseable game dates")

    outcome = (
        terminal_games.group_by(
            ["season", "_game_date", "game_pk", "league_id", "player_id"]
        )
        .agg(
            pl.len().cast(pl.Int64).alias("batting_plate_appearances"),
            pl.col("events")
            .is_in(sorted(BB_HBP_EVENT_TYPES))
            .sum()
            .cast(pl.Int64)
            .alias("bb_hbp_count"),
            pl.col("events")
            .is_in(sorted(STRIKEOUT_EVENT_TYPES))
            .sum()
            .cast(pl.Int64)
            .alias("strikeout_count"),
            pl.col("is_contact").sum().cast(pl.Int64).alias("expected_contact_count"),
            pl.col("events")
            .is_in(sorted(KNOWN_SPECIAL_NONCONTACT_EVENT_TYPES))
            .sum()
            .cast(pl.Int64)
            .alias("special_noncontact_count"),
        )
        .with_columns(
            (
                pl.col("batting_plate_appearances")
                - pl.col("expected_contact_count")
                - pl.col("special_noncontact_count")
                - pl.col("bb_hbp_count")
                - pl.col("strikeout_count")
            )
            .cast(pl.Int64)
            .alias("pa_accounting_residual")
        )
    )

    contacts = classify_mlb_savant_contacts(savant)
    contact_games = (
        contacts.group_by(["season", "league_id", "game_pk", "batter_mlbam_id"])
        .agg(
            pl.len().cast(pl.Int64).alias("contact_event_count"),
            pl.col("core_bin").is_not_null().sum().cast(pl.Int64).alias("core_contact_count"),
            (pl.col("contact_profile_status") == "special_bunt")
            .sum()
            .cast(pl.Int64)
            .alias("bunt_contact_count"),
            (pl.col("contact_profile_status") == "foul_air_excluded")
            .sum()
            .cast(pl.Int64)
            .alias("foul_air_excluded_count"),
            pl.col("contact_profile_status")
            .str.starts_with("unknown")
            .sum()
            .cast(pl.Int64)
            .alias("unknown_contact_count"),
        )
        .rename({"batter_mlbam_id": "player_id"})
    )

    joined = (
        outcome.join(
            contact_games,
            on=["season", "league_id", "game_pk", "player_id"],
            how="left",
        )
        .with_columns(
            *[
                pl.col(column).fill_null(0).cast(pl.Int64)
                for column in (
                    "contact_event_count",
                    "core_contact_count",
                    "bunt_contact_count",
                    "foul_air_excluded_count",
                    "unknown_contact_count",
                )
            ]
        )
        .with_columns(
            pl.col("contact_event_count").alias("observed_contact_count"),
            (
                pl.col("contact_event_count") - pl.col("expected_contact_count")
            ).alias("contact_count_residual"),
            (
                pl.col("bb_hbp_count")
                + pl.col("strikeout_count")
                + pl.col("core_contact_count")
            ).alias("core_profile_event_count"),
        )
    )

    summary = joined.select(
        pl.col("season").cast(pl.Int64),
        pl.col("_game_date").cast(pl.Date).alias("game_date"),
        pl.col("game_pk").cast(pl.Int64),
        pl.col("league_id").cast(pl.Int64),
        pl.col("player_id").cast(pl.Int64),
        pl.lit(MLB_LEVEL_GROUP).alias("level_group"),
        pl.col("batting_plate_appearances").cast(pl.Int64),
        pl.col("expected_contact_count").cast(pl.Int64),
        pl.col("observed_contact_count").cast(pl.Int64),
        pl.col("contact_count_residual").cast(pl.Int64),
        pl.col("core_profile_event_count").cast(pl.Int64),
        pl.col("bunt_contact_count").cast(pl.Int64),
        pl.col("foul_air_excluded_count").cast(pl.Int64),
        pl.col("unknown_contact_count").cast(pl.Int64),
        pl.col("special_noncontact_count").cast(pl.Int64),
        pl.col("pa_accounting_residual").cast(pl.Int64),
        pl.lit(MLB_PARTICIPANT_AUTHORITY).alias("participant_authority_status"),
        pl.lit(MLB_CAPABILITY_TIER).alias("source_capability_tier"),
    )

    outcome_profile = pl.concat(
        [
            outcome.filter(pl.col("bb_hbp_count") > 0).select(
                "season",
                pl.col("_game_date").cast(pl.Date).alias("game_date"),
                "game_pk",
                "league_id",
                "player_id",
                pl.lit(MLB_LEVEL_GROUP).alias("level_group"),
                pl.lit("BB_HBP").alias("core_bin"),
                pl.col("bb_hbp_count").cast(pl.Int64).alias("occurrence_count"),
            ),
            outcome.filter(pl.col("strikeout_count") > 0).select(
                "season",
                pl.col("_game_date").cast(pl.Date).alias("game_date"),
                "game_pk",
                "league_id",
                "player_id",
                pl.lit(MLB_LEVEL_GROUP).alias("level_group"),
                pl.lit("K").alias("core_bin"),
                pl.col("strikeout_count").cast(pl.Int64).alias("occurrence_count"),
            ),
        ],
        how="vertical_relaxed",
    )

    contact_profile = (
        contacts.filter(pl.col("core_bin").is_not_null())
        .group_by(["season", "league_id", "game_pk", "batter_mlbam_id", "core_bin"])
        .agg(pl.len().cast(pl.Int64).alias("occurrence_count"))
        .rename({"batter_mlbam_id": "player_id"})
    )
    contact_profile = (
        contact_profile.join(
            summary.select(
                "season", "game_date", "game_pk", "league_id", "player_id", "level_group"
            ),
            on=["season", "game_pk", "league_id", "player_id"],
            how="inner",
        )
        .select(
            "season",
            "game_date",
            "game_pk",
            "league_id",
            "player_id",
            "level_group",
            "core_bin",
            pl.col("occurrence_count").cast(pl.Int64),
        )
    )

    profile = pl.concat([outcome_profile, contact_profile], how="vertical_relaxed").sort(
        ["game_date", "game_pk", "player_id", "core_bin"]
    )
    contract = validate_player_game_evidence(summary, profile)
    return (
        summary.sort(["game_date", "game_pk", "player_id"]),
        profile,
        {
            **contract,
            "true_pa_terminal_count": terminal.height,
            "contact_event_count": contacts.height,
            "participant_authority": MLB_PARTICIPANT_AUTHORITY,
            "source_capability_tier": MLB_CAPABILITY_TIER,
            "evidence_denominator_policy": "separate_pa_expected_contact_observed_contact_v2",
        },
    )
