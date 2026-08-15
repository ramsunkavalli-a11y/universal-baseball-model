"""Temporal eligibility helpers with explicit retrospective/vintage semantics."""

from __future__ import annotations

from datetime import date, datetime

import polars as pl


def _cutoff_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def validate_resolved_game_dates(games: pl.DataFrame) -> pl.DataFrame:
    required = {"game_pk", "official_date"}
    missing = sorted(required - set(games.columns))
    if missing:
        raise ValueError(f"resolved game view missing columns: {missing}")
    result = games.select(["game_pk", "official_date"]).cast(
        {"game_pk": pl.Int64, "official_date": pl.Date}, strict=True
    )
    nulls = result.filter(
        pl.col("game_pk").is_null() | pl.col("official_date").is_null()
    )
    if not nulls.is_empty():
        raise ValueError("resolved game view contains null game_pk/official_date")
    duplicates = result.group_by("game_pk").len().filter(pl.col("len") > 1)
    if not duplicates.is_empty():
        raise ValueError(
            "resolved game view must contain exactly one official_date per game_pk"
        )
    return result


def retrospective_event_cutoff(
    observations: pl.DataFrame,
    resolved_games: pl.DataFrame,
    *,
    cutoff: date | datetime,
) -> pl.DataFrame:
    """Keep current/certified historical observations whose games occurred by cutoff.

    This prevents future baseball performance from entering predictors but makes
    no claim that the underlying source representation was the exact historical
    public vintage available at the cutoff.
    """

    if "game_pk" not in observations.columns:
        raise ValueError("observation table missing game_pk for event cutoff")
    games = validate_resolved_game_dates(resolved_games)
    cutoff_value = _cutoff_date(cutoff)
    with_dates = observations.join(games, on="game_pk", how="left")
    missing_games = with_dates.filter(pl.col("official_date").is_null())
    if not missing_games.is_empty():
        raise ValueError(
            f"event cutoff cannot classify {missing_games.height} observations with unknown game date"
        )
    return (
        with_dates.filter(pl.col("official_date") <= pl.lit(cutoff_value))
        .drop("official_date")
    )


def vintage_information_set(
    observations: pl.DataFrame,
    resolved_games: pl.DataFrame,
    source_snapshots: pl.DataFrame,
    *,
    cutoff: datetime,
) -> pl.DataFrame:
    """Keep only event-eligible observations whose exact source vintage is proven.

    ``knowledge_available_at_utc`` must be non-null and <= cutoff. A null value
    means the exact public availability of that representation is not established
    and the observation is therefore ineligible for a strict vintage backtest.
    """

    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("vintage cutoff must be timezone-aware")
    if cutoff.utcoffset().total_seconds() != 0:
        raise ValueError("vintage cutoff must be normalized to UTC")
    required = {"source_snapshot_id", "knowledge_available_at_utc"}
    missing = sorted(required - set(source_snapshots.columns))
    if missing:
        raise ValueError(f"source snapshot table missing vintage columns: {missing}")
    if "source_snapshot_id" not in observations.columns:
        raise ValueError("observation table missing source_snapshot_id for vintage cutoff")

    event_eligible = retrospective_event_cutoff(
        observations,
        resolved_games,
        cutoff=cutoff,
    )
    source_knowledge = source_snapshots.select(
        ["source_snapshot_id", "knowledge_available_at_utc"]
    )
    duplicates = (
        source_knowledge.group_by("source_snapshot_id")
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("source snapshot table contains duplicate source_snapshot_id")

    joined = event_eligible.join(
        source_knowledge,
        on="source_snapshot_id",
        how="left",
    )
    return (
        joined.filter(
            pl.col("knowledge_available_at_utc").is_not_null()
            & (pl.col("knowledge_available_at_utc") <= pl.lit(cutoff))
        )
        .drop("knowledge_available_at_utc")
    )
