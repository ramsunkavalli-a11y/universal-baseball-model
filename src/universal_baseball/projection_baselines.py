"""Simple batting Projection baselines built on frozen Current Talent.

Projection Baseline 0 is intentionally boring: carry the frozen Baseline-2
Current Talent probability profile forward unchanged to the next calendar-year
rate target.  It is the comparator that any age/development model must beat.

This module does not infer playing time, future level, or future role.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.projection_validation import ProjectionFold


PROJECTION_BASELINE0_METHOD = "frozen_current_talent_carry_forward_v1"


def build_projection_baseline0(
    current_talent_profile: pl.DataFrame,
    *,
    fold: ProjectionFold,
    allow_confirmation: bool = False,
    probability_column: str = "baseline2_latent_probability",
    tolerance: float = 1e-12,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Carry frozen Current Talent probabilities forward unchanged.

    Required grain is one row per ``player_id + core_bin``.  The function fails
    closed on duplicate keys, null/invalid probabilities, or profiles that do
    not sum to one per player.  Confirmation-fold materialization is blocked by
    default so 2025 cannot be touched accidentally while development is active.
    """

    if fold.confirmation and not allow_confirmation:
        raise ValueError("2025 Projection confirmation is quarantined")
    if tolerance < 0:
        raise ValueError("projection probability tolerance must be nonnegative")

    required = {"player_id", "core_bin", probability_column}
    missing = sorted(required - set(current_talent_profile.columns))
    if missing:
        raise ValueError(f"Current Talent projection input missing fields: {missing}")
    if current_talent_profile.is_empty():
        raise ValueError("Current Talent projection input must not be empty")

    keys = ["player_id", "core_bin"]
    if current_talent_profile.group_by(keys).len().filter(pl.col("len") != 1).height:
        raise ValueError("Current Talent projection input has duplicate player/core-bin keys")

    probability = pl.col(probability_column).cast(pl.Float64)
    invalid = current_talent_profile.filter(
        probability.is_null()
        | ~probability.is_finite()
        | (probability < 0.0)
        | (probability > 1.0)
    )
    if not invalid.is_empty():
        raise ValueError("Current Talent projection input has invalid probabilities")

    sums = current_talent_profile.group_by("player_id").agg(
        probability.sum().alias("_probability_sum")
    )
    if sums.filter((pl.col("_probability_sum") - 1.0).abs() > tolerance).height:
        raise ValueError("Current Talent projection probabilities do not sum to one per player")

    output = (
        current_talent_profile.select(
            "player_id",
            "core_bin",
            probability.alias("projection_probability"),
        )
        .with_columns(
            pl.lit(PROJECTION_BASELINE0_METHOD).alias("projection_method"),
            pl.lit(fold.snapshot_date).alias("as_of_date"),
            pl.lit(fold.target_start).alias("projection_target_start"),
            pl.lit(fold.target_end).alias("projection_target_end"),
            pl.lit(fold.confirmation).alias("projection_confirmation_fold"),
        )
        .sort(keys)
    )

    metrics: dict[str, Any] = {
        "projection_method": PROJECTION_BASELINE0_METHOD,
        "fold": fold.label,
        "as_of_date": fold.snapshot_date.isoformat(),
        "projection_target_start": fold.target_start.isoformat(),
        "projection_target_end": fold.target_end.isoformat(),
        "player_count": int(output.get_column("player_id").n_unique()),
        "profile_row_count": int(output.height),
        "probabilities_changed_from_current_talent": False,
        "playing_time_modeled": False,
        "future_level_used": False,
        "confirmation": fold.confirmation,
        "confirmation_access_explicitly_authorized": bool(fold.confirmation and allow_confirmation),
    }
    return output, metrics
