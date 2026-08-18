"""Reproduce frozen Current Talent Baseline 2 at Projection snapshots.

Projection v1 starts from the already-frozen results-only Current Talent state.
This module packages the exact Baseline-2 construction used by the historical
Current Talent development/confirmation gates into a reusable October-snapshot
builder. It deliberately does not score future outcomes, fit a Projection age
curve, infer playing time, or access confirmation data.

Frozen Current Talent semantics preserved here:

- fit level translation only from the snapshot season's pre-cutoff evidence;
- build the Baseline-0 prior from that same current-season translated evidence;
- let only player-specific evidence cross season boundaries in Baseline 2;
- use the frozen 1,095-day cap, 180-day half-life, and 100-event prior strength;
- translate player x level evidence before pooling across levels.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from universal_baseball.current_talent_baseline2 import (
    BASELINE2_LOOKBACK_DAYS,
    BASELINE2_METHOD,
    FROZEN_BASELINE2_HALF_LIFE_DAYS,
    FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
    build_baseline2_profiles,
)
from universal_baseball.current_talent_baselines import (
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_evidence import EvidenceWindow, validate_player_game_evidence
from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
    fit_level_clr_translation,
)
from universal_baseball.projection_validation import ProjectionFold, require_development_fold


PROJECTION_FROZEN_B2_SNAPSHOT_METHOD = "projection_reproduce_frozen_current_talent_b2_v1"
FROZEN_B0_AGE_BAND_WIDTH_YEARS = 2.0
FROZEN_B0_MIN_AGE_LEVEL_PEERS = 12
FROZEN_TRANSLATION_MIN_CORE_EVENTS_PER_STINT = 20
FROZEN_TRANSLATION_MAX_GAP_DAYS = 365
NUMERIC_TOLERANCE = 1e-12

_CURRENT_SEASON_WINDOW = EvidenceWindow(
    label="projection_frozen_b0_current_season_180d",
    lookback_days=None,
    half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
)
_BASELINE2_WINDOW = EvidenceWindow(
    label="projection_frozen_b2_multiseason_1095d_180d",
    lookback_days=BASELINE2_LOOKBACK_DAYS,
    half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
)


@dataclass(frozen=True, slots=True)
class ProjectionFrozenB2Snapshot:
    """Frozen B2 latent profile plus the snapshot context used by Projection."""

    profile: pl.DataFrame
    player_context: pl.DataFrame
    translation_offsets: pl.DataFrame
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _require_current_season_only(frame: pl.DataFrame, *, season: int, label: str) -> None:
    if frame.is_empty():
        raise ValueError(f"{label} must not be empty")
    observed = {int(value) for value in frame.get_column("season").unique().to_list()}
    if observed != {int(season)}:
        raise ValueError(f"{label} must contain only snapshot season {season}: observed={sorted(observed)}")


def _require_no_future_history(frame: pl.DataFrame, *, fold: ProjectionFold, label: str) -> None:
    parsed = frame.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_projection_b2_date")
    )
    if parsed.filter(pl.col("_projection_b2_date").is_null()).height:
        raise ValueError(f"{label} contains unparseable game dates")
    if parsed.filter(pl.col("_projection_b2_date") >= pl.lit(fold.snapshot_date)).height:
        raise ValueError(f"{label} contains evidence at or after Projection snapshot {fold.snapshot_date}")


def build_projection_frozen_b2_snapshot_from_offsets(
    history_summary: pl.DataFrame,
    history_profile: pl.DataFrame,
    current_summary: pl.DataFrame,
    current_profile: pl.DataFrame,
    context: pl.DataFrame,
    translation_offsets: pl.DataFrame,
    *,
    fold: ProjectionFold,
) -> ProjectionFrozenB2Snapshot:
    """Build frozen B2 using already-fitted snapshot-season translation offsets.

    This lower-level entry point exists so deterministic tests can isolate B2
    reproduction from the independently tested translation fitter. Production
    callers should normally use :func:`build_projection_frozen_b2_snapshot`.
    """

    require_development_fold(fold)
    validate_player_game_evidence(history_summary, history_profile)
    validate_player_game_evidence(current_summary, current_profile)
    _require_current_season_only(current_summary, season=fold.snapshot_date.year, label="current summary")
    _require_current_season_only(current_profile, season=fold.snapshot_date.year, label="current profile")
    _require_no_future_history(history_summary, fold=fold, label="history summary")
    _require_no_future_history(current_summary, fold=fold, label="current summary")

    _require_columns(
        context,
        {
            "player_id",
            "age_years",
            "as_of_level_group",
            "as_of_environment_ambiguous",
            "prior_mlb_evidence",
        },
        "Projection B2 context",
    )
    if context.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection B2 context violates player_id grain")
    if context.filter(pl.col("age_years").is_null()).height:
        raise ValueError("Projection B2 context requires exact non-null age")

    current_translated = build_translated_player_evidence(
        current_summary,
        current_profile,
        translation_offsets,
        cutoff=fold.snapshot_date,
        window=_CURRENT_SEASON_WINDOW,
    )
    frozen_prior = fit_leave_one_out_age_level_prior(
        current_translated,
        context,
        age_band_width_years=FROZEN_B0_AGE_BAND_WIDTH_YEARS,
        min_age_level_peers=FROZEN_B0_MIN_AGE_LEVEL_PEERS,
    )
    multiseason_translated = build_translated_player_evidence(
        history_summary,
        history_profile,
        translation_offsets,
        cutoff=fold.snapshot_date,
        window=_BASELINE2_WINDOW,
    )
    baseline2 = build_baseline2_profiles(
        multiseason_translated,
        frozen_prior,
        prior_strength_core_events=FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
    )

    current_effective = current_translated.select(
        "player_id",
        pl.col("effective_core_events").alias("current_season_effective_core_events"),
    ).unique()
    baseline2_effective = baseline2.profile.select(
        "player_id",
        "baseline2_effective_core_events",
    ).unique()
    player_context = (
        context.join(current_effective, on="player_id", how="inner")
        .join(baseline2_effective, on="player_id", how="inner")
        .with_columns(
            (
                pl.col("baseline2_effective_core_events")
                - pl.col("current_season_effective_core_events")
            ).alias("prior_season_effective_core_events"),
            pl.lit(fold.snapshot_date).alias("as_of_date"),
        )
        .sort("player_id")
    )
    if player_context.filter(pl.col("prior_season_effective_core_events") < -NUMERIC_TOLERANCE).height:
        raise ValueError("frozen B2 effective evidence is below current-season evidence")

    profile_players = set(int(value) for value in baseline2.profile.get_column("player_id").unique().to_list())
    context_players = set(int(value) for value in player_context.get_column("player_id").to_list())
    if profile_players != context_players:
        raise ValueError("Projection frozen B2 profile/context coverage differs")

    profile = (
        baseline2.profile.with_columns(
            pl.lit(fold.snapshot_date).alias("as_of_date"),
            pl.lit(fold.label).alias("projection_fold"),
            pl.lit(PROJECTION_FROZEN_B2_SNAPSHOT_METHOD).alias("projection_snapshot_method"),
        )
        .sort(["player_id", "core_bin"])
    )
    metrics: dict[str, Any] = {
        "projection_snapshot_method": PROJECTION_FROZEN_B2_SNAPSHOT_METHOD,
        "current_talent_method": BASELINE2_METHOD,
        "fold": fold.label,
        "as_of_date": fold.snapshot_date.isoformat(),
        "player_count": len(profile_players),
        "profile_row_count": int(profile.height),
        "baseline2_lookback_days": BASELINE2_LOOKBACK_DAYS,
        "baseline2_half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
        "baseline2_prior_strength_core_events": FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
        "frozen_b0_age_band_width_years": FROZEN_B0_AGE_BAND_WIDTH_YEARS,
        "frozen_b0_min_age_level_peers": FROZEN_B0_MIN_AGE_LEVEL_PEERS,
        "translation_fit_from_snapshot_season_only": True,
        "player_history_crosses_certified_seasons": True,
        "future_outcomes_scored": False,
        "projection_model_fit": False,
        "playing_time_modeled": False,
        "confirmation_accessed": False,
    }
    return ProjectionFrozenB2Snapshot(
        profile=profile,
        player_context=player_context,
        translation_offsets=translation_offsets.sort(["level_group", "core_bin"]),
        metrics=metrics,
    )


def build_projection_frozen_b2_snapshot(
    history_summary: pl.DataFrame,
    history_profile: pl.DataFrame,
    current_summary: pl.DataFrame,
    current_profile: pl.DataFrame,
    context: pl.DataFrame,
    *,
    fold: ProjectionFold,
) -> ProjectionFrozenB2Snapshot:
    """Fit the frozen translation and reproduce Baseline 2 at one dev snapshot."""

    require_development_fold(fold)
    validate_player_game_evidence(current_summary, current_profile)
    _require_current_season_only(current_summary, season=fold.snapshot_date.year, label="current summary")
    _require_no_future_history(current_summary, fold=fold, label="current summary")

    transition_evidence = build_training_environment_transition_evidence(
        current_summary,
        current_profile,
        training_end=fold.snapshot_date,
        min_core_events_per_stint=FROZEN_TRANSLATION_MIN_CORE_EVENTS_PER_STINT,
        max_gap_days=FROZEN_TRANSLATION_MAX_GAP_DAYS,
    )
    translation_fit = fit_level_clr_translation(
        transition_evidence.pair_summary,
        transition_evidence.pair_profile,
        anchor_level="MLB",
    )
    built = build_projection_frozen_b2_snapshot_from_offsets(
        history_summary,
        history_profile,
        current_summary,
        current_profile,
        context,
        translation_fit.offsets,
        fold=fold,
    )
    metrics = {
        **built.metrics,
        "translation_evidence": transition_evidence.metrics,
        "translation_fit": translation_fit.metrics,
    }
    return ProjectionFrozenB2Snapshot(
        profile=built.profile,
        player_context=built.player_context,
        translation_offsets=built.translation_offsets,
        metrics=metrics,
    )
