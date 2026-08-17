"""Baseline 2: multi-season results-only Current Talent challenger.

This module deliberately adds no new baseball evidence family.  It reuses the
frozen Baseline 1 empirical-Bayes estimator with a longer *input history* and
keeps the Baseline 0 prior fixed to the comparator's prior.  The live validation
script is responsible for constructing the frozen season-to-date evidence and the
multi-season evidence under the predeclared chronological contract.

The existing scoring engine is pair-oriented and names its two probability
columns ``baseline0`` and ``baseline1``.  ``build_frozen_b1_vs_b2_scoring_pair``
therefore maps frozen B1 -> scoring baseline0 and B2 -> scoring baseline1 after
verifying that both models share the identical Baseline 0 prior and player/core
coverage.  Downstream reports must relabel those temporary scoring names.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from universal_baseball.current_talent_baselines import (
    BaselineProfiles,
    build_baseline_profiles,
)


BASELINE2_METHOD = "translated_multiseason_recency_empirical_bayes_v1"
BASELINE2_LOOKBACK_DAYS = 1095
FROZEN_BASELINE2_HALF_LIFE_DAYS = 180.0
FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS = 100.0


@dataclass(frozen=True, slots=True)
class Baseline2Profiles:
    """Latent Baseline 0 + Baseline 2 probabilities on the MLB reporting scale."""

    profile: pl.DataFrame
    metrics: dict[str, Any]


def build_baseline2_profiles(
    translated_multiseason: pl.DataFrame,
    frozen_baseline0_prior: pl.DataFrame,
    *,
    prior_strength_core_events: float = FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
) -> Baseline2Profiles:
    """Shrink multi-season translated evidence toward the frozen B0 prior.

    ``build_baseline_profiles`` contains the already-tested empirical-Bayes math.
    Reusing it here isolates the challenger to history depth rather than creating
    a second implementation of the same estimator.
    """

    built = build_baseline_profiles(
        translated_multiseason,
        frozen_baseline0_prior,
        prior_strength_core_events=prior_strength_core_events,
    )
    profile = (
        built.profile.rename(
            {
                "baseline1_latent_probability": "baseline2_latent_probability",
                "baseline1_method": "_baseline1_method_reused",
                "player_effective_core_events": "baseline2_effective_core_events",
            }
        )
        .with_columns(pl.lit(BASELINE2_METHOD).alias("baseline2_method"))
        .drop("_baseline1_method_reused")
        .sort(["player_id", "core_bin"])
    )
    metrics = {
        **built.metrics,
        "baseline2_method": BASELINE2_METHOD,
        "baseline2_lookback_days": BASELINE2_LOOKBACK_DAYS,
        "baseline2_half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
        "baseline2_prior_strength_core_events": float(prior_strength_core_events),
        "only_intended_change_vs_frozen_b1": "player_specific_history_depth",
    }
    metrics.pop("baseline1_method", None)
    metrics.pop("player_specific_translated_recent_performance_in_baseline1", None)
    return Baseline2Profiles(profile=profile, metrics=metrics)


def build_frozen_b1_vs_b2_scoring_pair(
    frozen_b1: BaselineProfiles,
    baseline2: Baseline2Profiles,
    *,
    tolerance: float = 1e-12,
) -> pl.DataFrame:
    """Return the temporary two-model surface required by the scoring engine.

    The returned column names follow the existing pair scorer:

    - ``baseline0_latent_probability`` = frozen Baseline 1 comparator;
    - ``baseline1_latent_probability`` = Baseline 2 challenger.

    Reports must relabel model rows accordingly.  The function fails if coverage
    or the shared Baseline 0 prior differs between comparator and challenger.
    """

    if tolerance < 0:
        raise ValueError("pairing tolerance must be nonnegative")

    required_frozen = {
        "player_id",
        "core_bin",
        "baseline0_latent_probability",
        "baseline1_latent_probability",
    }
    required_b2 = {
        "player_id",
        "core_bin",
        "baseline0_latent_probability",
        "baseline2_latent_probability",
    }
    missing_frozen = sorted(required_frozen - set(frozen_b1.profile.columns))
    missing_b2 = sorted(required_b2 - set(baseline2.profile.columns))
    if missing_frozen:
        raise ValueError(f"frozen Baseline 1 profile missing fields: {missing_frozen}")
    if missing_b2:
        raise ValueError(f"Baseline 2 profile missing fields: {missing_b2}")

    frozen = frozen_b1.profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline0_latent_probability").alias("_frozen_b0"),
        pl.col("baseline1_latent_probability").alias("_frozen_b1"),
    )
    challenger = baseline2.profile.select(
        "player_id",
        "core_bin",
        pl.col("baseline0_latent_probability").alias("_challenger_b0"),
        pl.col("baseline2_latent_probability").alias("_baseline2"),
    )

    paired = frozen.join(
        challenger,
        on=["player_id", "core_bin"],
        how="full",
        coalesce=True,
    )
    if paired.height != frozen.height or paired.height != challenger.height:
        raise ValueError("frozen Baseline 1 and Baseline 2 coverage differs")
    if paired.select(pl.any_horizontal(pl.all().is_null())).item():
        raise ValueError("frozen Baseline 1 and Baseline 2 keys do not match exactly")
    if paired.filter((pl.col("_frozen_b0") - pl.col("_challenger_b0")).abs() > tolerance).height:
        raise ValueError("Baseline 2 does not share the frozen Baseline 0 prior")

    result = paired.select(
        "player_id",
        "core_bin",
        pl.col("_frozen_b1").alias("baseline0_latent_probability"),
        pl.col("_baseline2").alias("baseline1_latent_probability"),
    ).sort(["player_id", "core_bin"])

    sums = result.group_by("player_id").agg(
        pl.col("baseline0_latent_probability").sum().alias("_frozen_b1_sum"),
        pl.col("baseline1_latent_probability").sum().alias("_baseline2_sum"),
    )
    if sums.filter(
        (pl.col("_frozen_b1_sum") - 1.0).abs() > tolerance
        | (pl.col("_baseline2_sum") - 1.0).abs() > tolerance
    ).height:
        raise ValueError("paired Baseline 1 / Baseline 2 profiles do not sum to one")
    return result


def relabel_pair_model(model: str) -> str:
    """Map temporary scorer labels to the actual challenger comparison names."""

    mapping = {
        "baseline0": "frozen_baseline1",
        "baseline1": "baseline2",
    }
    try:
        return mapping[str(model)]
    except KeyError as exc:
        raise ValueError(f"unsupported paired-scoring model label: {model}") from exc
