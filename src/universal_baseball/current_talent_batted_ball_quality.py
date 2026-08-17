"""Deterministic batted-ball-quality evidence for richer Current Talent challengers.

This module projects complete observed, result-producing Savant batted balls to a
small canonical surface, builds leakage-safe player features at an as-of cutoff,
and applies already-fitted contact-shape residual coefficients to frozen Baseline
2.

Savant may report launch metrics on non-result contact pitches such as fouls. The
richer feature family intentionally follows Baseball Savant's BBE semantics: only
an in-play contact row that produces a plate-appearance result is a tracked BBE.
Missing tracking is never imputed. Capability-tier assignment remains external so
source coverage can be certified at game/league/venue grain before these features
are used by a richer model.
"""

from __future__ import annotations

from datetime import date
from math import exp, log

import polars as pl

from universal_baseball.performance_season import CONTACT_CORE_BINS


TRACKED_BBE_HALF_LIFE_DAYS = 180.0
PRIMARY_MIN_COMPLETE_TRACKED_BBE = 20
SWEET_SPOT_MIN_DEGREES = 8.0
SWEET_SPOT_MAX_DEGREES = 32.0
RICHER_BATTED_BALL_METHOD = "baseline2_plus_ev_sweet_spot_contact_residual_v1"

TRACKED_BBE_KEY = ("game_pk", "player_id", "at_bat_number", "pitch_number")
TRACKED_BBE_PA_KEY = ("game_pk", "player_id", "at_bat_number")
TRACKED_BBE_SCHEMA: dict[str, pl.DataType] = {
    "game_date": pl.Date,
    "game_pk": pl.Int64,
    "player_id": pl.Int64,
    "at_bat_number": pl.Int64,
    "pitch_number": pl.Int64,
    "launch_speed": pl.Float64,
    "launch_angle": pl.Float64,
    "sweet_spot": pl.Boolean,
}

TRACKED_FEATURE_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "raw_complete_tracked_bbe": pl.Int64,
    "effective_complete_tracked_bbe": pl.Float64,
    "recency_weighted_mean_exit_velocity": pl.Float64,
    "recency_weighted_sweet_spot_share": pl.Float64,
    "first_tracked_bbe_date": pl.Date,
    "last_tracked_bbe_date": pl.Date,
    "tracked_bbe_eligible": pl.Boolean,
}

RICHER_STANDARDIZED_FEATURE_REQUIRED = frozenset(
    {
        "player_id",
        "tracked_bbe_eligible",
        "z_mean_exit_velocity",
        "z_sweet_spot_share",
    }
)
RICHER_COEFFICIENT_REQUIRED = frozenset(
    {
        "core_bin",
        "beta_mean_exit_velocity",
        "beta_sweet_spot_share",
    }
)


def _integer_like(column: str, alias: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def project_complete_tracked_bbe(raw: pl.DataFrame) -> pl.DataFrame:
    """Project complete observed result-producing Savant BBE to pitch grain.

    Complete EV/LA alone is not enough: Savant also exposes launch measurements
    on foul contacts. A canonical BBE must therefore be an in-play ``type == X``
    row with a nonblank terminal ``events`` value and complete EV + launch angle.

    The canonical key includes ``pitch_number`` so source contacts are never
    silently collapsed. A second result-producing BBE inside the same player/PA
    is source-semantic ambiguity and fails closed.
    """

    required = {
        "game_date",
        "game_pk",
        "batter",
        "at_bat_number",
        "pitch_number",
        "events",
        "type",
        "launch_speed",
        "launch_angle",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"tracked batted-ball source missing fields: {missing}")
    if raw.is_empty():
        return pl.DataFrame(schema=TRACKED_BBE_SCHEMA)

    projected = (
        raw.select(
            pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("game_date"),
            _integer_like("game_pk", "game_pk"),
            _integer_like("batter", "player_id"),
            _integer_like("at_bat_number", "at_bat_number"),
            _integer_like("pitch_number", "pitch_number"),
            pl.col("events").cast(pl.String).alias("events"),
            pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase().alias("_pitch_result_type"),
            pl.col("launch_speed").cast(pl.Float64, strict=False),
            pl.col("launch_angle").cast(pl.Float64, strict=False),
        )
        .filter(
            pl.col("game_date").is_not_null()
            & pl.col("game_pk").is_not_null()
            & pl.col("player_id").is_not_null()
            & pl.col("at_bat_number").is_not_null()
            & pl.col("pitch_number").is_not_null()
            & (pl.col("_pitch_result_type") == "X")
            & _nonblank("events")
            & pl.col("launch_speed").is_not_null()
            & pl.col("launch_angle").is_not_null()
        )
        .select(
            "game_date",
            "game_pk",
            "player_id",
            "at_bat_number",
            "pitch_number",
            "launch_speed",
            "launch_angle",
        )
        .with_columns(
            pl.col("launch_angle")
            .is_between(SWEET_SPOT_MIN_DEGREES, SWEET_SPOT_MAX_DEGREES, closed="both")
            .alias("sweet_spot")
        )
        .cast(TRACKED_BBE_SCHEMA, strict=True)
    )

    duplicate = projected.group_by(list(TRACKED_BBE_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError(
            "tracked batted-ball source has duplicate result-producing EV+LA rows at "
            "game_pk + player_id + at_bat_number + pitch_number"
        )
    multiple_results = projected.group_by(list(TRACKED_BBE_PA_KEY)).len().filter(pl.col("len") != 1)
    if not multiple_results.is_empty():
        raise ValueError(
            "tracked batted-ball source has multiple result-producing BBE for one "
            "game_pk + player_id + at_bat_number"
        )

    return projected.sort(["game_date", *TRACKED_BBE_KEY])


def build_batted_ball_quality_features(
    tracked_bbe: pl.DataFrame,
    *,
    cutoff: date,
    half_life_days: float = TRACKED_BBE_HALF_LIFE_DAYS,
    min_complete_tracked_bbe: int = PRIMARY_MIN_COMPLETE_TRACKED_BBE,
) -> pl.DataFrame:
    """Build leakage-safe EV/LA player features using only BBE before cutoff."""

    if half_life_days <= 0:
        raise ValueError("tracked-BBE half-life must be positive")
    if min_complete_tracked_bbe < 1:
        raise ValueError("minimum complete tracked BBE must be at least one")
    missing = sorted(set(TRACKED_BBE_SCHEMA) - set(tracked_bbe.columns))
    if missing:
        raise ValueError(f"canonical tracked batted-ball evidence missing fields: {missing}")
    if tracked_bbe.is_empty():
        return pl.DataFrame(schema=TRACKED_FEATURE_SCHEMA)

    duplicate = tracked_bbe.group_by(list(TRACKED_BBE_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("canonical tracked batted-ball evidence violates canonical grain")
    multiple_results = tracked_bbe.group_by(list(TRACKED_BBE_PA_KEY)).len().filter(pl.col("len") != 1)
    if not multiple_results.is_empty():
        raise ValueError("canonical tracked batted-ball evidence has multiple BBE in one PA")

    working = tracked_bbe.with_columns(
        pl.col("game_date").cast(pl.Date, strict=False).alias("game_date")
    ).filter(pl.col("game_date") < pl.lit(cutoff))
    if working.is_empty():
        return pl.DataFrame(schema=TRACKED_FEATURE_SCHEMA)

    days_old = (pl.lit(cutoff) - pl.col("game_date")).dt.total_days().cast(pl.Float64)
    weight = (-days_old * (log(2.0) / float(half_life_days))).exp()
    weighted = working.with_columns(weight.alias("_recency_weight"))

    features = (
        weighted.group_by("player_id")
        .agg(
            pl.len().cast(pl.Int64).alias("raw_complete_tracked_bbe"),
            pl.col("_recency_weight").sum().alias("effective_complete_tracked_bbe"),
            (
                (pl.col("launch_speed") * pl.col("_recency_weight")).sum()
                / pl.col("_recency_weight").sum()
            ).alias("recency_weighted_mean_exit_velocity"),
            (
                (pl.col("sweet_spot").cast(pl.Float64) * pl.col("_recency_weight")).sum()
                / pl.col("_recency_weight").sum()
            ).alias("recency_weighted_sweet_spot_share"),
            pl.col("game_date").min().alias("first_tracked_bbe_date"),
            pl.col("game_date").max().alias("last_tracked_bbe_date"),
        )
        .with_columns(
            pl.lit(cutoff).alias("as_of_date"),
            (pl.col("raw_complete_tracked_bbe") >= min_complete_tracked_bbe).alias(
                "tracked_bbe_eligible"
            ),
        )
        .select(*TRACKED_FEATURE_SCHEMA)
        .cast(TRACKED_FEATURE_SCHEMA, strict=True)
        .sort("player_id")
    )
    return features


def apply_batted_ball_quality_residual(
    baseline2_profile: pl.DataFrame,
    standardized_features: pl.DataFrame,
    coefficients: pl.DataFrame,
    *,
    probability_tolerance: float = 1e-12,
) -> pl.DataFrame:
    """Apply fitted EV/LA residuals to B2's conditional contact distribution.

    ``BB_HBP`` and ``K`` are copied exactly from Baseline 2. Only the ten contact
    bins are adjusted, and their total probability mass is held exactly at the B2
    contact mass. Players without an eligible standardized feature row fall back
    to B2 without imputation.

    The coefficient table contains one no-intercept residual pair per contact bin;
    coefficient fitting and feature standardization are deliberately separate,
    training-only steps.
    """

    if probability_tolerance < 0:
        raise ValueError("probability tolerance must be nonnegative")
    required_profile = {"player_id", "core_bin", "baseline2_latent_probability"}
    missing_profile = sorted(required_profile - set(baseline2_profile.columns))
    missing_features = sorted(RICHER_STANDARDIZED_FEATURE_REQUIRED - set(standardized_features.columns))
    missing_coefficients = sorted(RICHER_COEFFICIENT_REQUIRED - set(coefficients.columns))
    if missing_profile:
        raise ValueError(f"Baseline 2 profile missing fields: {missing_profile}")
    if missing_features:
        raise ValueError(f"standardized richer features missing fields: {missing_features}")
    if missing_coefficients:
        raise ValueError(f"batted-ball residual coefficients missing fields: {missing_coefficients}")

    duplicate_profile = baseline2_profile.group_by(["player_id", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate_profile.is_empty():
        raise ValueError("Baseline 2 profile violates player_id + core_bin grain")
    duplicate_features = standardized_features.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicate_features.is_empty():
        raise ValueError("standardized richer features violate player_id grain")
    duplicate_coefficients = coefficients.group_by("core_bin").len().filter(pl.col("len") != 1)
    if not duplicate_coefficients.is_empty():
        raise ValueError("batted-ball residual coefficients violate core_bin grain")

    coefficient_bins = set(str(value) for value in coefficients.get_column("core_bin").to_list())
    if coefficient_bins != set(CONTACT_CORE_BINS):
        raise ValueError("batted-ball residual coefficients must contain exactly the ten contact bins")

    coefficient_lookup = {
        str(row["core_bin"]): (
            float(row["beta_mean_exit_velocity"]),
            float(row["beta_sweet_spot_share"]),
        )
        for row in coefficients.iter_rows(named=True)
    }
    feature_lookup = {
        int(row["player_id"]): row
        for row in standardized_features.iter_rows(named=True)
        if bool(row["tracked_bbe_eligible"])
        and row["z_mean_exit_velocity"] is not None
        and row["z_sweet_spot_share"] is not None
    }

    rows: list[dict[str, object]] = []
    for key, group in baseline2_profile.group_by("player_id", maintain_order=True):
        player_id = int(key[0]) if isinstance(key, tuple) else int(key)
        probabilities = {
            str(row["core_bin"]): float(row["baseline2_latent_probability"])
            for row in group.iter_rows(named=True)
        }
        expected_bins = {"BB_HBP", "K", *CONTACT_CORE_BINS}
        if set(probabilities) != expected_bins:
            raise ValueError(f"Baseline 2 player {player_id} does not contain the full 12-bin profile")
        if any(value <= 0 or value >= 1 for value in probabilities.values()):
            raise ValueError("Baseline 2 latent probabilities must be strictly between zero and one")
        if abs(sum(probabilities.values()) - 1.0) > probability_tolerance:
            raise ValueError("Baseline 2 latent probabilities must sum to one")

        feature = feature_lookup.get(player_id)
        adjusted = dict(probabilities)
        applied = feature is not None
        if applied:
            z_ev = float(feature["z_mean_exit_velocity"])
            z_ss = float(feature["z_sweet_spot_share"])
            contact_mass = sum(probabilities[core_bin] for core_bin in CONTACT_CORE_BINS)
            logits: dict[str, float] = {}
            for core_bin in CONTACT_CORE_BINS:
                conditional = probabilities[core_bin] / contact_mass
                beta_ev, beta_ss = coefficient_lookup[core_bin]
                logits[core_bin] = log(conditional) + beta_ev * z_ev + beta_ss * z_ss
            max_logit = max(logits.values())
            denominator = sum(exp(value - max_logit) for value in logits.values())
            if denominator <= 0:
                raise ValueError("batted-ball residual softmax denominator must be positive")
            for core_bin in CONTACT_CORE_BINS:
                adjusted[core_bin] = (
                    exp(logits[core_bin] - max_logit) / denominator * contact_mass
                )

        for core_bin in ["BB_HBP", "K", *CONTACT_CORE_BINS]:
            rows.append(
                {
                    "player_id": player_id,
                    "core_bin": core_bin,
                    "baseline2_latent_probability": probabilities[core_bin],
                    "richer_latent_probability": adjusted[core_bin],
                    "richer_adjustment_applied": applied,
                    "richer_method": RICHER_BATTED_BALL_METHOD if applied else "baseline2_fallback",
                }
            )

    result = pl.DataFrame(rows).sort(["player_id", "core_bin"])
    sums = result.group_by("player_id").agg(
        pl.col("baseline2_latent_probability").sum().alias("_b2_sum"),
        pl.col("richer_latent_probability").sum().alias("_richer_sum"),
    )
    if sums.filter(
        ((pl.col("_b2_sum") - 1.0).abs() > probability_tolerance)
        | ((pl.col("_richer_sum") - 1.0).abs() > probability_tolerance)
    ).height:
        raise ValueError("Baseline 2 / richer profiles do not sum to one")
    return result
