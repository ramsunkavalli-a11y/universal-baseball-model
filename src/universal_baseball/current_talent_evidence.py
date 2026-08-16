"""Leakage-safe player-game evidence and snapshot aggregation for Current Talent.

This module freezes the intermediate surface between observed Performance and
future Current Talent baselines.  It does not estimate talent and deliberately
contains no age, environment translation, projection, or run-value fitting.

Inputs remain at actual-league player-game grain.  Predictor snapshots use only
games strictly before the cutoff and expose both raw and recency-weighted evidence.
The 12-bin profile is normalized only over eligible core evidence; coverage and
non-core/unknown evidence remain explicit separate channels.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from math import log
from typing import Any

import polars as pl

from universal_baseball.performance_season import ALL_CORE_BINS


PLAYER_GAME_KEY = ("season", "game_date", "game_pk", "league_id", "player_id")
PLAYER_GAME_PROFILE_KEY = (*PLAYER_GAME_KEY, "core_bin")

PLAYER_GAME_SUMMARY_REQUIRED = frozenset(
    {
        *PLAYER_GAME_KEY,
        "level_group",
        "batting_plate_appearances",
        "core_profile_event_count",
        "non_core_event_count",
        "unknown_event_count",
        "participant_authority_status",
        "source_capability_tier",
    }
)
PLAYER_GAME_PROFILE_REQUIRED = frozenset(
    {
        *PLAYER_GAME_PROFILE_KEY,
        "level_group",
        "occurrence_count",
    }
)

LEVEL_ORDINAL: dict[str, int] = {
    "ROOKIE_COMPLEX": 1,
    "SINGLE_A": 2,
    "HIGH_A": 3,
    "AA": 4,
    "AAA": 5,
    "MLB": 6,
}
ORDINAL_LEVEL = {value: key for key, value in LEVEL_ORDINAL.items()}


@dataclass(frozen=True, slots=True)
class EvidenceWindow:
    """One predictor evidence window chosen inside chronological validation."""

    label: str
    lookback_days: int | None = None
    half_life_days: float | None = None

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("evidence window label must be nonblank")
        if self.lookback_days is not None and self.lookback_days <= 0:
            raise ValueError("lookback_days must be positive when supplied")
        if self.half_life_days is not None and self.half_life_days <= 0:
            raise ValueError("half_life_days must be positive when supplied")


def _require_columns(frame: pl.DataFrame, required: frozenset[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing Current Talent evidence fields: {missing}")


def _require_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    duplicate = frame.group_by(list(key)).len().filter(pl.col("len") > 1)
    if not duplicate.is_empty():
        raise ValueError(f"{label} violates canonical grain: {list(key)}")


def _parsed_game_date() -> pl.Expr:
    return pl.col("game_date").cast(pl.String).str.to_date(strict=False)


def validate_player_game_evidence(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
) -> dict[str, Any]:
    """Validate player-game Performance evidence before snapshot construction."""

    _require_columns(summary, PLAYER_GAME_SUMMARY_REQUIRED, "player-game summary")
    _require_columns(profile, PLAYER_GAME_PROFILE_REQUIRED, "player-game profile")
    _require_unique(summary, PLAYER_GAME_KEY, "player-game summary")
    _require_unique(profile, PLAYER_GAME_PROFILE_KEY, "player-game profile")

    if summary.is_empty():
        raise ValueError("player-game summary must not be empty")

    summary_working = summary.with_columns(_parsed_game_date().alias("_parsed_game_date"))
    if summary_working.filter(pl.col("_parsed_game_date").is_null()).height:
        raise ValueError("player-game summary contains unparseable game dates")

    invalid_level = summary_working.filter(~pl.col("level_group").is_in(list(LEVEL_ORDINAL)))
    if not invalid_level.is_empty():
        observed = sorted(str(v) for v in invalid_level.get_column("level_group").unique().to_list())
        raise ValueError(f"player-game summary contains unsupported level groups: {observed}")

    invalid_counts = summary_working.filter(
        (pl.col("batting_plate_appearances") < 0)
        | (pl.col("core_profile_event_count") < 0)
        | (pl.col("non_core_event_count") < 0)
        | (pl.col("unknown_event_count") < 0)
        | (pl.col("core_profile_event_count") > pl.col("batting_plate_appearances"))
        | (
            pl.col("core_profile_event_count")
            + pl.col("non_core_event_count")
            + pl.col("unknown_event_count")
            > pl.col("batting_plate_appearances")
        )
    )
    if not invalid_counts.is_empty():
        raise ValueError("player-game summary contains invalid evidence accounting")

    invalid_profile = profile.filter(
        (~pl.col("core_bin").is_in(list(ALL_CORE_BINS)))
        | (pl.col("occurrence_count") <= 0)
    )
    if not invalid_profile.is_empty():
        raise ValueError("player-game profile contains invalid core bins/counts")

    summary_keys = summary.select(list(PLAYER_GAME_KEY))
    orphan_profile = profile.select(list(PLAYER_GAME_KEY)).unique().join(
        summary_keys,
        on=list(PLAYER_GAME_KEY),
        how="anti",
    )
    if not orphan_profile.is_empty():
        raise ValueError("player-game profile contains keys absent from summary")

    profile_counts = profile.group_by(list(PLAYER_GAME_KEY)).agg(
        pl.col("occurrence_count").sum().alias("_profile_core_event_count")
    )
    accounting = summary.select(*PLAYER_GAME_KEY, "core_profile_event_count").join(
        profile_counts,
        on=list(PLAYER_GAME_KEY),
        how="left",
    ).with_columns(pl.col("_profile_core_event_count").fill_null(0))
    mismatch = accounting.filter(
        pl.col("_profile_core_event_count") != pl.col("core_profile_event_count")
    )
    if not mismatch.is_empty():
        raise ValueError("player-game profile counts do not reconcile to summary")

    return {
        "player_game_count": summary.height,
        "profile_row_count": profile.height,
        "player_count": summary.get_column("player_id").n_unique(),
        "actual_league_count": summary.get_column("league_id").n_unique(),
        "season_count": summary.get_column("season").n_unique(),
        "total_plate_appearances": int(summary.get_column("batting_plate_appearances").sum() or 0),
        "total_core_events": int(summary.get_column("core_profile_event_count").sum() or 0),
    }


def _windowed_summary(
    summary: pl.DataFrame,
    *,
    cutoff: date,
    window: EvidenceWindow,
) -> pl.DataFrame:
    parsed = summary.with_columns(_parsed_game_date().alias("_evidence_date"))
    predicate = pl.col("_evidence_date") < pl.lit(cutoff)
    if window.lookback_days is not None:
        start = cutoff - timedelta(days=int(window.lookback_days))
        predicate = predicate & (pl.col("_evidence_date") >= pl.lit(start))

    filtered = parsed.filter(predicate)
    if filtered.is_empty():
        return filtered.with_columns(pl.lit(None, dtype=pl.Float64).alias("_recency_weight"))

    days_old = (pl.lit(cutoff) - pl.col("_evidence_date")).dt.total_days().cast(pl.Float64)
    if window.half_life_days is None:
        weight = pl.lit(1.0)
    else:
        weight = (-days_old * (log(2.0) / float(window.half_life_days))).exp()
    return filtered.with_columns(weight.alias("_recency_weight"))


def build_predictor_snapshot(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    cutoff: date,
    window: EvidenceWindow,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Aggregate pre-cutoff player-game evidence to one leakage-safe snapshot.

    Returns ``(snapshot_summary, snapshot_profile)``.  The summary is one row per
    player.  The profile is long-form ``player_id + core_bin`` so component models
    can be fit without repeatedly widening the taxonomy.
    """

    validate_player_game_evidence(summary, profile)
    windowed = _windowed_summary(summary, cutoff=cutoff, window=window)

    summary_schema = {
        "as_of_date": pl.Date,
        "window_label": pl.String,
        "player_id": pl.Int64,
        "raw_plate_appearances": pl.Int64,
        "effective_plate_appearances": pl.Float64,
        "raw_core_events": pl.Int64,
        "effective_core_events": pl.Float64,
        "raw_non_core_events": pl.Int64,
        "effective_non_core_events": pl.Float64,
        "raw_unknown_events": pl.Int64,
        "effective_unknown_events": pl.Float64,
        "raw_core_coverage_rate": pl.Float64,
        "effective_core_coverage_rate": pl.Float64,
        "game_count": pl.Int64,
        "league_count": pl.Int64,
        "level_count": pl.Int64,
        "min_level_ordinal": pl.Int64,
        "max_level_ordinal": pl.Int64,
        "min_level_group": pl.String,
        "max_level_group": pl.String,
        "first_evidence_date": pl.Date,
        "last_evidence_date": pl.Date,
        "participant_authority_status_count": pl.Int64,
        "source_capability_tier_count": pl.Int64,
    }
    profile_schema = {
        "as_of_date": pl.Date,
        "window_label": pl.String,
        "player_id": pl.Int64,
        "core_bin": pl.String,
        "raw_occurrence_count": pl.Int64,
        "effective_occurrence_count": pl.Float64,
        "raw_core_profile_rate": pl.Float64,
        "effective_core_profile_rate": pl.Float64,
    }
    if windowed.is_empty():
        return pl.DataFrame(schema=summary_schema), pl.DataFrame(schema=profile_schema)

    windowed = windowed.with_columns(
        pl.col("level_group")
        .replace_strict(LEVEL_ORDINAL, default=None, return_dtype=pl.Int64)
        .alias("_level_ordinal")
    )
    snapshot_summary = (
        windowed.group_by("player_id")
        .agg(
            pl.col("batting_plate_appearances").sum().alias("raw_plate_appearances"),
            (pl.col("batting_plate_appearances") * pl.col("_recency_weight"))
            .sum()
            .alias("effective_plate_appearances"),
            pl.col("core_profile_event_count").sum().alias("raw_core_events"),
            (pl.col("core_profile_event_count") * pl.col("_recency_weight"))
            .sum()
            .alias("effective_core_events"),
            pl.col("non_core_event_count").sum().alias("raw_non_core_events"),
            (pl.col("non_core_event_count") * pl.col("_recency_weight"))
            .sum()
            .alias("effective_non_core_events"),
            pl.col("unknown_event_count").sum().alias("raw_unknown_events"),
            (pl.col("unknown_event_count") * pl.col("_recency_weight"))
            .sum()
            .alias("effective_unknown_events"),
            pl.col("game_pk").n_unique().alias("game_count"),
            pl.col("league_id").n_unique().alias("league_count"),
            pl.col("level_group").n_unique().alias("level_count"),
            pl.col("_level_ordinal").min().alias("min_level_ordinal"),
            pl.col("_level_ordinal").max().alias("max_level_ordinal"),
            pl.col("_evidence_date").min().alias("first_evidence_date"),
            pl.col("_evidence_date").max().alias("last_evidence_date"),
            pl.col("participant_authority_status").n_unique().alias("participant_authority_status_count"),
            pl.col("source_capability_tier").n_unique().alias("source_capability_tier_count"),
        )
        .with_columns(
            pl.when(pl.col("raw_plate_appearances") > 0)
            .then(pl.col("raw_core_events") / pl.col("raw_plate_appearances"))
            .otherwise(None)
            .alias("raw_core_coverage_rate"),
            pl.when(pl.col("effective_plate_appearances") > 0)
            .then(pl.col("effective_core_events") / pl.col("effective_plate_appearances"))
            .otherwise(None)
            .alias("effective_core_coverage_rate"),
            pl.col("min_level_ordinal")
            .replace_strict(ORDINAL_LEVEL, default=None, return_dtype=pl.String)
            .alias("min_level_group"),
            pl.col("max_level_ordinal")
            .replace_strict(ORDINAL_LEVEL, default=None, return_dtype=pl.String)
            .alias("max_level_group"),
            pl.lit(cutoff).alias("as_of_date"),
            pl.lit(window.label).alias("window_label"),
        )
        .select(list(summary_schema))
        .cast(summary_schema, strict=True)
        .sort("player_id")
    )

    weight_lookup = windowed.select(*PLAYER_GAME_KEY, "_recency_weight")
    profile_window = profile.join(weight_lookup, on=list(PLAYER_GAME_KEY), how="inner")
    snapshot_profile = (
        profile_window.group_by(["player_id", "core_bin"])
        .agg(
            pl.col("occurrence_count").sum().alias("raw_occurrence_count"),
            (pl.col("occurrence_count") * pl.col("_recency_weight"))
            .sum()
            .alias("effective_occurrence_count"),
        )
        .join(
            snapshot_summary.select("player_id", "raw_core_events", "effective_core_events"),
            on="player_id",
            how="left",
        )
        .with_columns(
            pl.when(pl.col("raw_core_events") > 0)
            .then(pl.col("raw_occurrence_count") / pl.col("raw_core_events"))
            .otherwise(None)
            .alias("raw_core_profile_rate"),
            pl.when(pl.col("effective_core_events") > 0)
            .then(pl.col("effective_occurrence_count") / pl.col("effective_core_events"))
            .otherwise(None)
            .alias("effective_core_profile_rate"),
            pl.lit(cutoff).alias("as_of_date"),
            pl.lit(window.label).alias("window_label"),
        )
        .select(list(profile_schema))
        .cast(profile_schema, strict=True)
        .sort(["player_id", "core_bin"])
    )

    raw_check = snapshot_profile.group_by("player_id").agg(
        pl.col("raw_occurrence_count").sum().alias("_profile_raw")
    ).join(snapshot_summary.select("player_id", "raw_core_events"), on="player_id")
    if raw_check.filter(pl.col("_profile_raw") != pl.col("raw_core_events")).height:
        raise ValueError("snapshot profile raw counts do not reconcile to snapshot summary")

    effective_check = snapshot_profile.group_by("player_id").agg(
        pl.col("effective_occurrence_count").sum().alias("_profile_effective")
    ).join(snapshot_summary.select("player_id", "effective_core_events"), on="player_id")
    if effective_check.filter(
        (pl.col("_profile_effective") - pl.col("effective_core_events")).abs() > 1e-9
    ).height:
        raise ValueError("snapshot profile effective counts do not reconcile to snapshot summary")

    return snapshot_summary, snapshot_profile
