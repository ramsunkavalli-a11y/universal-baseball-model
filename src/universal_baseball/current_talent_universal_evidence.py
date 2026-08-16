"""Combine MLB and affiliated player-game evidence for Current Talent snapshots.

This is a contract/materialization layer only.  It concatenates already-validated
source-specific game evidence and enforces universal canonical grains.  Level
translation, age priors, recency selection, talent inference, and future scoring
remain downstream model concerns.
"""

from __future__ import annotations

from typing import Any, Iterable

import polars as pl

from universal_baseball.current_talent_evidence import (
    PLAYER_GAME_KEY,
    PLAYER_GAME_PROFILE_KEY,
    validate_player_game_evidence,
)
from universal_baseball.universal_performance import (
    UNIVERSAL_LEAGUE_IDS,
    UNIVERSAL_LEVEL_GROUP,
)


def _concat(frames: Iterable[pl.DataFrame], label: str) -> pl.DataFrame:
    materialized = list(frames)
    if not materialized:
        raise ValueError(f"no {label} Current Talent evidence frames supplied")
    if any(frame.is_empty() for frame in materialized):
        raise ValueError(f"{label} Current Talent evidence contains an empty component")
    return pl.concat(materialized, how="vertical_relaxed")


def combine_universal_player_game_evidence(
    summaries: Iterable[pl.DataFrame],
    profiles: Iterable[pl.DataFrame],
    *,
    expected_seasons: set[int] | None = None,
    require_all_universal_leagues: bool = False,
) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    """Combine source-specific player-game evidence on one stable surface."""

    summary = _concat(summaries, "summary")
    profile = _concat(profiles, "profile")

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
    }
    return (
        summary.sort(["game_date", "game_pk", "league_id", "player_id"]),
        profile.sort(["game_date", "game_pk", "league_id", "player_id", "core_bin"]),
        metrics,
    )
