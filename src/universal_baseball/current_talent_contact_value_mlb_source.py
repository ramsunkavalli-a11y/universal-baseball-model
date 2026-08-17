"""MLB source adapter for frozen Current Talent contact-value challenger 2.

This module is deliberately thin.  It reuses the already-certified historical
Baseball Savant projection and the shared frozen contact-profile classifier, then
adds only the challenger-specific event target:

- a row must be a true PA-terminal physical contact;
- the shared ten-bin contact profile must mark it core-eligible;
- bunts and special/interference outcomes remain outside the target;
- Savant's structured terminal ``events`` field maps to the frozen nine groups;
- only 2021-2022 development-source seasons are accepted here.

No terminal values, environment baseline, richer residual, development score, or
2023 evidence is accessed or fitted by this module.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value_source import (
    SUPPORTED_TERMINAL_GROUPS,
    terminal_group_from_structured_event_type,
)
from universal_baseball.current_talent_mlb_evidence import (
    KNOWN_SPECIAL_NONCONTACT_EVENT_TYPES,
    MLB_LEVEL_GROUP,
)
from universal_baseball.mlb_performance import MLB_LEAGUE_IDS
from universal_baseball.mlb_performance_materialization import classify_mlb_savant_contacts


DEVELOPMENT_SOURCE_SEASONS = frozenset({2021, 2022})
CONTACT_KEY = ("game_pk", "at_bat_index", "pitch_number")
MLB_TERMINAL_OUTCOME_STATUS = "supported_structured_savant_event"
BUNT_TERMINAL_EVENT_TYPES = frozenset({"sac_bunt", "sac_bunt_double_play"})


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _validate_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    duplicates = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} contains duplicate canonical pitch keys")


def _normalized_event_type(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _is_field_error_interference(event_type: object, description: object) -> bool:
    """Mirror the already-certified narrow MLB special-outcome exception.

    A normal fielder's-choice contact can mention a later interference error, so
    the narrative alone is insufficient.  Only terminal ``field_error`` plus the
    explicit ``interference error`` wording is excluded as a special outcome.
    """

    event = _normalized_event_type(event_type)
    text = "" if description is None else str(description).strip().lower()
    return event == "field_error" and "interference error" in text


def materialize_mlb_contact_value_target_contacts(
    savant: pl.DataFrame,
    *,
    allowed_seasons: frozenset[int] = DEVELOPMENT_SOURCE_SEASONS,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Return one frozen-schema Challenger-2 target row per supported MLB BBE.

    ``savant`` must already be the certified projected/league-assigned historical
    Savant surface.  The returned columns intentionally match the accepted MiLB
    contact-value target table so downstream chronology/value attachment is
    source-agnostic.
    """

    required = {
        "game_date",
        "game_year",
        "game_pk",
        "league_id",
        "at_bat_index",
        "pitch_number",
        "batter_mlbam_id",
        "events",
        "result_description",
        "is_plate_appearance_terminal",
        "is_contact",
        "batter_side",
        "bb_type",
        "hc_x",
        "hc_y",
    }
    _require_columns(savant, required, "MLB contact-value Savant input")
    if savant.is_empty():
        raise ValueError("MLB contact-value Savant input must not be empty")
    _validate_unique(savant, CONTACT_KEY, "MLB contact-value Savant input")

    years = {
        int(value)
        for value in savant.get_column("game_year")
        .cast(pl.Int64, strict=False)
        .drop_nulls()
        .unique()
        .to_list()
    }
    if not years:
        raise ValueError("MLB contact-value Savant input has no parseable season")
    unauthorized = sorted(years - set(int(value) for value in allowed_seasons))
    if unauthorized:
        raise ValueError(
            "MLB contact-value source is development-only and rejects unauthorized seasons: "
            f"{unauthorized}"
        )

    leagues = {
        int(value)
        for value in savant.get_column("league_id")
        .cast(pl.Int64, strict=False)
        .drop_nulls()
        .unique()
        .to_list()
    }
    unknown_leagues = sorted(leagues - set(MLB_LEAGUE_IDS))
    if unknown_leagues:
        raise ValueError(f"MLB contact-value input contains non-MLB league IDs: {unknown_leagues}")

    classified = classify_mlb_savant_contacts(savant)
    _validate_unique(classified, CONTACT_KEY, "classified MLB contact profile")

    terminal_source = savant.filter(pl.col("is_plate_appearance_terminal")).select(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("event_date"),
        pl.col("game_year").cast(pl.Int64).alias("season"),
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("league_id").cast(pl.Int64),
        pl.col("batter_mlbam_id").cast(pl.Int64).alias("source_player_id"),
        pl.col("events").cast(pl.String).alias("terminal_event_type"),
        pl.col("result_description").cast(pl.String).alias("terminal_result_description"),
        pl.col("is_contact").cast(pl.Boolean).alias("terminal_is_contact"),
    )
    _validate_unique(terminal_source, ("game_pk", "at_bat_index"), "MLB terminal PA source")
    if terminal_source.filter(pl.col("event_date").is_null()).height:
        raise ValueError("MLB terminal PA source contains unparseable game dates")
    if terminal_source.filter(pl.col("source_player_id").is_null()).height:
        raise ValueError("MLB terminal PA source contains missing batter identity")

    profile = classified.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("league_id").cast(pl.Int64),
        pl.col("batter_mlbam_id").cast(pl.Int64).alias("player_id"),
        pl.col("participant_authority").cast(pl.String),
        pl.col("core_bin").cast(pl.String).alias("contact_bin"),
        pl.col("core_profile_eligible").cast(pl.Boolean),
        pl.col("contact_profile_status").cast(pl.String),
    )

    joined = profile.join(
        terminal_source,
        on=["game_pk", "at_bat_index", "pitch_number", "league_id"],
        how="inner",
        validate="1:1",
    )
    if joined.filter(pl.col("player_id") != pl.col("source_player_id")).height:
        raise ValueError("MLB contact-value terminal join disagrees on batter identity")

    rows: list[dict[str, Any]] = []
    unsupported_status_counts: dict[str, int] = {}
    structured_group_counts: dict[str, int] = {}
    for row in joined.iter_rows(named=True):
        event_type = _normalized_event_type(row.get("terminal_event_type"))
        bunt = event_type in BUNT_TERMINAL_EVENT_TYPES
        special = (
            event_type in KNOWN_SPECIAL_NONCONTACT_EVENT_TYPES
            or _is_field_error_interference(
                event_type, row.get("terminal_result_description")
            )
        )
        group = (
            None
            if (bunt or special)
            else terminal_group_from_structured_event_type(event_type)
        )

        if bunt:
            source_status = "unsupported_bunt"
        elif special:
            source_status = "unsupported_special_result"
        elif group is None:
            source_status = "unsupported_structured_event"
        else:
            source_status = MLB_TERMINAL_OUTCOME_STATUS

        if group is None:
            unsupported_status_counts[source_status] = unsupported_status_counts.get(source_status, 0) + 1
        else:
            structured_group_counts[group] = structured_group_counts.get(group, 0) + 1

        if not bool(row.get("terminal_is_contact")):
            continue
        if not bool(row.get("core_profile_eligible")):
            continue
        if group not in SUPPORTED_TERMINAL_GROUPS:
            continue

        rows.append(
            {
                "event_date": row["event_date"],
                "game_pk": int(row["game_pk"]),
                "at_bat_index": int(row["at_bat_index"]),
                "pitch_number": int(row["pitch_number"]),
                "league_id": int(row["league_id"]),
                "level_group": MLB_LEVEL_GROUP,
                "player_id": int(row["player_id"]),
                "participant_authority": str(row["participant_authority"]),
                "contact_bin": str(row["contact_bin"]),
                "terminal_outcome_group": str(group),
                "terminal_outcome_status": MLB_TERMINAL_OUTCOME_STATUS,
            }
        )

    schema = {
        "event_date": pl.Date,
        "game_pk": pl.Int64,
        "at_bat_index": pl.Int64,
        "pitch_number": pl.Int64,
        "league_id": pl.Int64,
        "level_group": pl.String,
        "player_id": pl.Int64,
        "participant_authority": pl.String,
        "contact_bin": pl.String,
        "terminal_outcome_group": pl.String,
        "terminal_outcome_status": pl.String,
    }
    output = (
        pl.DataFrame(rows, schema=schema)
        if rows
        else pl.DataFrame(schema=schema)
    ).sort(["event_date", "game_pk", "at_bat_index", "pitch_number"])

    terminal_physical = joined.filter(pl.col("terminal_is_contact"))
    terminal_core = terminal_physical.filter(pl.col("core_profile_eligible"))
    metrics: dict[str, Any] = {
        "input_pitch_count": int(savant.height),
        "classified_physical_contact_count": int(classified.height),
        "terminal_physical_contact_count": int(terminal_physical.height),
        "core_terminal_contact_count": int(terminal_core.height),
        "supported_target_contact_count": int(output.height),
        "unsupported_core_terminal_contact_count": int(terminal_core.height - output.height),
        "unsupported_terminal_status_counts_all_terminal_contacts": unsupported_status_counts,
        "structured_terminal_group_counts_all_terminal_contacts": structured_group_counts,
        "observed_seasons": sorted(years),
        "level_group": MLB_LEVEL_GROUP,
        "model_scoring": False,
        "accessed_2023": False,
        "terminal_values_attached": False,
        "baseline_fitted": False,
        "richer_residual_fitted": False,
        "target_contract": "terminal_core_contact_nine_group_v1",
        "structured_result_authority": "baseball_savant_events",
    }
    return output, metrics
