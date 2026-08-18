"""Combine MLB and affiliated player-game evidence for Current Talent snapshots.

This is a contract/materialization layer only. It concatenates already-validated
source-specific game evidence and enforces universal canonical grains. Level
translation, age priors, recency selection, talent inference, and future scoring
remain downstream model concerns.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import polars as pl

from universal_baseball.current_talent_evidence import (
    PLAYER_GAME_KEY,
    PLAYER_GAME_PROFILE_KEY,
    PLAYER_GAME_PROFILE_REQUIRED,
    PLAYER_GAME_SUMMARY_REQUIRED,
    validate_player_game_evidence,
)
from universal_baseball.universal_performance import (
    UNIVERSAL_LEAGUE_IDS,
    UNIVERSAL_LEVEL_GROUP,
)


SUMMARY_CANONICAL_COLUMNS: tuple[str, ...] = (
    *PLAYER_GAME_KEY,
    "level_group",
    "batting_plate_appearances",
    "expected_contact_count",
    "observed_contact_count",
    "contact_count_residual",
    "core_profile_event_count",
    "bunt_contact_count",
    "foul_air_excluded_count",
    "unknown_contact_count",
    "special_noncontact_count",
    "pa_accounting_residual",
    "participant_authority_status",
    "source_capability_tier",
)
PROFILE_CANONICAL_COLUMNS: tuple[str, ...] = (
    *PLAYER_GAME_PROFILE_KEY,
    "level_group",
    "occurrence_count",
)


def _concat(
    frames: Iterable[pl.DataFrame],
    label: str,
    canonical_columns: Sequence[str],
) -> pl.DataFrame:
    materialized = list(frames)
    if not materialized:
        raise ValueError(f"no {label} Current Talent evidence frames supplied")
    if any(frame.is_empty() for frame in materialized):
        raise ValueError(f"{label} Current Talent evidence contains an empty component")

    required = set(canonical_columns)
    for index, frame in enumerate(materialized):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(
                f"{label} Current Talent evidence component {index} missing canonical fields: {missing}"
            )

    # Certified source-specific artifacts can carry extra provenance/diagnostic
    # fields and can serialize the same canonical columns in different orders.
    # The universal surface is deliberately narrower: project every component to
    # the frozen model-facing contract before concatenation rather than asking
    # Polars to reconcile source-specific schemas implicitly.
    projected = [frame.select(list(canonical_columns)) for frame in materialized]
    return pl.concat(projected, how="vertical_relaxed")


def combine_universal_player_game_evidence(
    summaries: Iterable[pl.DataFrame],
    profiles: Iterable[pl.DataFrame],
    *,
    expected_seasons: set[int] | None = None,
    require_all_universal_leagues: bool = False,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Combine source-specific player-game evidence on one stable surface."""

    # Keep these assertions tied directly to the generic Current Talent
    # validator so a future required-field change cannot silently leave this
    # canonical projection stale.
    if set(SUMMARY_CANONICAL_COLUMNS) != set(PLAYER_GAME_SUMMARY_REQUIRED):
        raise RuntimeError("universal summary canonical fields drifted from Current Talent contract")
    if set(PROFILE_CANONICAL_COLUMNS) != set(PLAYER_GAME_PROFILE_REQUIRED):
        raise RuntimeError("universal profile canonical fields drifted from Current Talent contract")

    summary = _concat(summaries, "summary", SUMMARY_CANONICAL_COLUMNS)
    profile = _concat(profiles, "profile", PROFILE_CANONICAL_COLUMNS)

    # Source-specific adapters should already supply the normalized level label.
    # Validate it against the frozen universal league map rather than overwriting
    # source output silently.
    observed_leagues = {
        int(value)
        for value in summary.get_column("league_id").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    unknown = sorted(observed_leagues - set(UNIVERSAL_LEAGUE_IDS))
    if unknown:
        raise ValueError(f"universal player-game evidence contains unknown league IDs: {unknown}")

    inconsistent = summary.filter(
        pl.col("level_group")
        != pl.col("league_id")
        .cast(pl.Int64)
        .replace_strict(
            {int(k): str(v) for k, v in UNIVERSAL_LEVEL_GROUP.items()},
            default=None,
            return_dtype=pl.String,
        )
    )
    if not inconsistent.is_empty():
        raise ValueError("universal player-game evidence has league/level context mismatch")

    if require_all_universal_leagues and observed_leagues != set(UNIVERSAL_LEAGUE_IDS):
        raise ValueError(
            "universal player-game league coverage mismatch: "
            f"missing={sorted(set(UNIVERSAL_LEAGUE_IDS) - observed_leagues)}, "
            f"extra={sorted(observed_leagues - set(UNIVERSAL_LEAGUE_IDS))}"
        )

    if expected_seasons is not None:
        observed_seasons = {
            int(value) for value in summary.get_column("season").cast(pl.Int64).unique().to_list()
        }
        if observed_seasons != {int(value) for value in expected_seasons}:
            raise ValueError(
                f"universal player-game season coverage mismatch: observed={sorted(observed_seasons)}, "
                f"expected={sorted(int(value) for value in expected_seasons)}"
            )

    contract = validate_player_game_evidence(summary, profile)

    # The generic validator checks profile orphans; explicitly freeze uniqueness
    # after concatenation so a player/game cannot enter through two source paths.
    summary_dupes = summary.group_by(list(PLAYER_GAME_KEY)).len().filter(pl.col("len") > 1)
    profile_dupes = profile.group_by(list(PLAYER_GAME_PROFILE_KEY)).len().filter(pl.col("len") > 1)
    if not summary_dupes.is_empty() or not profile_dupes.is_empty():
        raise ValueError("universal Current Talent evidence duplicates canonical player-game keys")

    metrics: dict[str, Any] = {
        **contract,
        "actual_league_count": len(observed_leagues),
        "level_group_count": summary.get_column("level_group").n_unique(),
        "level_groups": sorted(str(v) for v in summary.get_column("level_group").unique().to_list()),
        "participant_authority_statuses": sorted(
            str(v) for v in summary.get_column("participant_authority_status").unique().to_list()
        ),
        "source_capability_tiers": sorted(
            str(v) for v in summary.get_column("source_capability_tier").unique().to_list()
        ),
        "universal_schema_policy": "project_required_current_talent_fields_before_concat_v1",
    }
    return (
        summary.sort(["game_date", "game_pk", "league_id", "player_id"]),
        profile.sort(["game_date", "game_pk", "league_id", "player_id", "core_bin"]),
        metrics,
    )
