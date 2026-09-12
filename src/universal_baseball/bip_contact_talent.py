"""Explainable full-profile BIP contact-talent primitives.

The existing Current Talent pipeline owns contact classification and profile
projection.  This module supplies the missing bridge to the active results-based
talent model: turn a complete projected BIP distribution into a neutral contact
value, then learn a bounded incremental blend on earlier forecast/target pairs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

import polars as pl

from universal_baseball.performance_season import CONTACT_CORE_BINS
from universal_baseball.hitter_v2_evaluation import NEUTRAL_WOBA_WEIGHTS


@dataclass(frozen=True, slots=True)
class BipResidualBlend:
    """One transparent weight joining BIP and results-based contact estimates."""

    weight: float
    training_players: int
    training_contacts: float
    unconstrained_weight: float


def estimate_neutral_bip_values(outcome_counts: pl.DataFrame) -> pl.DataFrame:
    """Estimate one context-neutral wOBA value per BIP bin from prior outcomes."""

    required = {"core_bin", "canonical_outcome", "occurrence_count"}
    if missing := sorted(required - set(outcome_counts.columns)):
        raise ValueError(f"BIP outcome counts missing columns: {missing}")
    if outcome_counts.is_empty():
        return pl.DataFrame(
            schema={
                "core_bin": pl.String,
                "neutral_run_value": pl.Float64,
                "value_events": pl.Int64,
            }
        )
    invalid_bins = outcome_counts.filter(
        ~pl.col("core_bin").is_in(list(CONTACT_CORE_BINS))
    )
    invalid_outcomes = outcome_counts.filter(
        ~pl.col("canonical_outcome").is_in(list(NEUTRAL_WOBA_WEIGHTS))
    )
    invalid_counts = outcome_counts.filter(pl.col("occurrence_count") <= 0)
    if invalid_bins.height or invalid_outcomes.height or invalid_counts.height:
        raise ValueError("BIP outcome counts contain unsupported values")
    weighted = outcome_counts.with_columns(
        pl.col("canonical_outcome")
        .replace_strict(NEUTRAL_WOBA_WEIGHTS, return_dtype=pl.Float64)
        .alias("_outcome_value")
    )
    result = (
        weighted.group_by("core_bin")
        .agg(
            (
                (pl.col("occurrence_count") * pl.col("_outcome_value")).sum()
                / pl.col("occurrence_count").sum()
            ).alias("neutral_run_value"),
            pl.col("occurrence_count").sum().cast(pl.Int64).alias("value_events"),
        )
        .sort("core_bin")
    )
    if set(result.get_column("core_bin").to_list()) != set(CONTACT_CORE_BINS):
        raise ValueError("BIP outcome counts must support all ten contact bins")
    return result


def score_projected_bip_profile(
    profile: pl.DataFrame,
    neutral_bin_values: pl.DataFrame,
    *,
    probability_column: str = "projected_bip_probability",
    value_column: str = "neutral_run_value",
) -> pl.DataFrame:
    """Reduce each complete ten-bin projected BIP profile to neutral run value.

    The caller must provide values learned strictly before the forecast cutoff.
    Actual player outcomes, parks, fielders, names, and public evaluations do not
    enter this calculation.
    """

    profile_required = {"player_id", "core_bin", probability_column}
    value_required = {"core_bin", value_column}
    if missing := sorted(profile_required - set(profile.columns)):
        raise ValueError(f"projected BIP profile missing columns: {missing}")
    if missing := sorted(value_required - set(neutral_bin_values.columns)):
        raise ValueError(f"neutral BIP values missing columns: {missing}")
    if profile.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "bip_contact_value": pl.Float64,
                "bip_profile_bins": pl.Int64,
            }
        )

    expected = set(CONTACT_CORE_BINS)
    observed_values = set(neutral_bin_values.get_column("core_bin").to_list())
    if observed_values != expected:
        raise ValueError("neutral BIP values must contain exactly the ten contact bins")
    if neutral_bin_values.group_by("core_bin").len().filter(pl.col("len") != 1).height:
        raise ValueError("neutral BIP values contain duplicate bins")
    if profile.group_by(["player_id", "core_bin"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("projected BIP profile violates player + bin grain")
    invalid = profile.filter(
        ~pl.col("core_bin").is_in(list(CONTACT_CORE_BINS))
        | pl.col(probability_column).is_null()
        | ~pl.col(probability_column).is_finite()
        | (pl.col(probability_column) < 0.0)
    )
    if invalid.height:
        raise ValueError("projected BIP profile contains invalid bins or probabilities")
    shape = profile.group_by("player_id").agg(
        pl.len().alias("_bins"),
        pl.col("core_bin").n_unique().alias("_unique_bins"),
        pl.col(probability_column).sum().alias("_probability_sum"),
    )
    if shape.filter(
        (pl.col("_bins") != len(CONTACT_CORE_BINS))
        | (pl.col("_unique_bins") != len(CONTACT_CORE_BINS))
        | ((pl.col("_probability_sum") - 1.0).abs() > 1e-9)
    ).height:
        raise ValueError("every projected BIP profile must contain ten bins summing to one")

    joined = profile.join(
        neutral_bin_values.select("core_bin", value_column),
        on="core_bin",
        how="left",
        validate="m:1",
    )
    if joined.get_column(value_column).null_count() or joined.filter(
        ~pl.col(value_column).is_finite()
    ).height:
        raise ValueError("neutral BIP values must be finite")
    return (
        joined.group_by("player_id")
        .agg(
            (pl.col(probability_column) * pl.col(value_column))
            .sum()
            .alias("bip_contact_value"),
            pl.len().cast(pl.Int64).alias("bip_profile_bins"),
        )
        .sort("player_id")
    )


def fit_bip_residual_blend(training: pl.DataFrame) -> BipResidualBlend:
    """Fit a contact-weighted, nonnegative blend using earlier origins only.

    ``bip_contact_value`` and ``baseline_contact_value`` are competing estimates
    of the same neutral run value per BIP.  Clipping the fitted weight to [0, 1]
    permits the BIP estimate to supplement or replace the baseline, but never to
    reverse its baseball meaning or extrapolate beyond it.
    """

    required = {
        "player_id",
        "baseline_contact_value",
        "bip_contact_value",
        "target_contact_value",
        "target_contacts",
    }
    if missing := sorted(required - set(training.columns)):
        raise ValueError(f"BIP residual training data missing columns: {missing}")
    if training.is_empty():
        return BipResidualBlend(0.0, 0, 0.0, 0.0)
    if training.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("BIP residual training data must have one row per player")

    rows = training.select(*required).to_dicts()
    numerator = 0.0
    denominator = 0.0
    contacts = 0.0
    for row in rows:
        values = [
            row["baseline_contact_value"],
            row["bip_contact_value"],
            row["target_contact_value"],
            row["target_contacts"],
        ]
        if any(value is None or not isfinite(float(value)) for value in values):
            raise ValueError("BIP residual training values must be finite")
        weight = float(row["target_contacts"])
        if weight <= 0.0:
            raise ValueError("target_contacts must be positive")
        residual_estimate = float(row["bip_contact_value"]) - float(
            row["baseline_contact_value"]
        )
        residual_target = float(row["target_contact_value"]) - float(
            row["baseline_contact_value"]
        )
        numerator += weight * residual_estimate * residual_target
        denominator += weight * residual_estimate * residual_estimate
        contacts += weight
    unconstrained = numerator / denominator if denominator > 0.0 else 0.0
    fitted = min(1.0, max(0.0, unconstrained))
    return BipResidualBlend(fitted, len(rows), contacts, unconstrained)


def apply_bip_residual_blend(
    estimates: pl.DataFrame,
    blend: BipResidualBlend,
) -> pl.DataFrame:
    """Apply the frozen blend with exact baseline fallback at weight zero."""

    required = {"player_id", "baseline_contact_value", "bip_contact_value"}
    if missing := sorted(required - set(estimates.columns)):
        raise ValueError(f"BIP contact estimates missing columns: {missing}")
    if not 0.0 <= blend.weight <= 1.0:
        raise ValueError("BIP residual blend weight must be between zero and one")
    return estimates.with_columns(
        (
            pl.col("baseline_contact_value")
            + pl.lit(blend.weight)
            * (pl.col("bip_contact_value") - pl.col("baseline_contact_value"))
        ).alias("blended_contact_value"),
        pl.lit(blend.weight).alias("bip_residual_weight"),
    )
