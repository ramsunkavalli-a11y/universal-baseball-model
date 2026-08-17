"""Deterministic source materialization for Current Talent challenger 2.

This module joins three already-controlled historical surfaces without fitting or
scoring a model:

- participant-authorized reusable MiLB physical contacts (for event date);
- the frozen shared contact-profile classification (for contact bin/player/level);
- source-reconciled terminal PA outcome groups (for the nine-group target).

Only a physical contact whose pitch key is exactly the terminal pitch of its PA is
eligible. Bunts, unsupported/special outcomes, non-core contact shapes, missing
league identity, and key disagreements remain excluded or fail closed. No 2023
input, environment fitting, residual fitting, or player score is accessed here.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.bin_value_policy import LEAGUE_LEVEL_GROUP
from universal_baseball.current_talent_contact_value_source import SUPPORTED_TERMINAL_GROUPS


CONTACT_KEY = ("game_pk", "at_bat_index", "pitch_number")


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _validate_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    duplicates = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(f"{label} contains duplicate physical contact keys")


def materialize_contact_value_target_contacts(
    authorized_contacts: pl.DataFrame,
    contact_profile: pl.DataFrame,
    terminal_pas: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Build one deterministic Challenger-2 target row per supported core BBE.

    ``terminal_pas`` must already carry the conservative/source-reconciled
    ``terminal_outcome_group`` produced by
    :func:`attach_narrative_terminal_groups`. Unsupported terminal outcomes are
    retained in diagnostics but never enter the returned target table.
    """

    _require_columns(
        authorized_contacts,
        {"game_date", *CONTACT_KEY},
        "authorized historical contacts",
    )
    _require_columns(
        contact_profile,
        {
            *CONTACT_KEY,
            "league_id",
            "batter_mlbam_id",
            "participant_authority",
            "core_bin",
            "core_profile_eligible",
        },
        "historical contact profile",
    )
    _require_columns(
        terminal_pas,
        {
            "game_pk",
            "at_bat_index",
            "terminal_pitch_number",
            "terminal_outcome_group",
            "terminal_outcome_status",
        },
        "terminal PA outcomes",
    )

    _validate_unique(authorized_contacts, CONTACT_KEY, "authorized historical contacts")
    _validate_unique(contact_profile, CONTACT_KEY, "historical contact profile")
    terminal_duplicates = (
        terminal_pas.group_by(["game_pk", "at_bat_index"]).len().filter(pl.col("len") > 1)
    )
    if not terminal_duplicates.is_empty():
        raise ValueError("terminal PA outcomes contain duplicate PA keys")

    dates = authorized_contacts.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("game_date").cast(pl.Date, strict=False).alias("event_date"),
    )
    if dates.filter(pl.col("event_date").is_null()).height:
        raise ValueError("authorized historical contacts contain unparseable game dates")

    profile = contact_profile.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("pitch_number").cast(pl.Int64),
        pl.col("league_id").cast(pl.Int64, strict=False),
        pl.col("batter_mlbam_id").cast(pl.Int64, strict=False).alias("player_id"),
        pl.col("participant_authority").cast(pl.String),
        pl.col("core_bin").cast(pl.String).alias("contact_bin"),
        pl.col("core_profile_eligible").cast(pl.Boolean),
    )
    invalid_profile = profile.filter(
        pl.col("league_id").is_null() | pl.col("player_id").is_null()
    )
    if not invalid_profile.is_empty():
        raise ValueError("historical contact profile has missing league/player identity")

    terminal = terminal_pas.select(
        pl.col("game_pk").cast(pl.Int64),
        pl.col("at_bat_index").cast(pl.Int64),
        pl.col("terminal_pitch_number").cast(pl.Int64),
        pl.col("terminal_outcome_group").cast(pl.String),
        pl.col("terminal_outcome_status").cast(pl.String),
    )

    joined = (
        profile.join(dates, on=list(CONTACT_KEY), how="inner", validate="1:1")
        .join(terminal, on=["game_pk", "at_bat_index"], how="left", validate="m:1")
        .with_columns(
            (pl.col("pitch_number") == pl.col("terminal_pitch_number")).alias(
                "is_terminal_contact"
            ),
            pl.col("league_id")
            .replace_strict(
                {int(k): str(v) for k, v in LEAGUE_LEVEL_GROUP.items()},
                default=None,
                return_dtype=pl.String,
            )
            .alias("level_group"),
        )
    )
    if joined.height != contact_profile.height:
        raise ValueError(
            "authorized-contact/date join changed contact-profile row count: "
            f"{joined.height} vs {contact_profile.height}"
        )
    if joined.filter(pl.col("level_group").is_null()).height:
        raise ValueError("contact-value materialization contains uncertified league IDs")

    supported_terminal = pl.col("terminal_outcome_group").is_in(
        sorted(SUPPORTED_TERMINAL_GROUPS)
    )
    eligible = joined.filter(
        pl.col("is_terminal_contact")
        & pl.col("core_profile_eligible")
        & supported_terminal
    )

    output = eligible.select(
        "event_date",
        "game_pk",
        "at_bat_index",
        "pitch_number",
        "league_id",
        "level_group",
        "player_id",
        "participant_authority",
        "contact_bin",
        "terminal_outcome_group",
        "terminal_outcome_status",
    ).sort(["event_date", "game_pk", "at_bat_index", "pitch_number"])

    metrics: dict[str, Any] = {
        "physical_contact_count": int(joined.height),
        "terminal_physical_contact_count": int(joined.filter(pl.col("is_terminal_contact")).height),
        "core_terminal_contact_count": int(
            joined.filter(pl.col("is_terminal_contact") & pl.col("core_profile_eligible")).height
        ),
        "supported_target_contact_count": int(output.height),
        "unsupported_terminal_group_count": int(
            joined.filter(
                pl.col("is_terminal_contact")
                & pl.col("core_profile_eligible")
                & ~supported_terminal.fill_null(False)
            ).height
        ),
        "nonterminal_contact_count": int(joined.filter(~pl.col("is_terminal_contact").fill_null(False)).height),
        "model_scoring": False,
        "accessed_2023": False,
        "target_contract": "terminal_core_contact_nine_group_v1",
    }
    return output, metrics
