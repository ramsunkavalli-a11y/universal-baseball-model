"""Training-only standardization for batted-ball-quality Current Talent features.

The richer challenger must not derive centering/scaling parameters from evaluation
folds. This module therefore makes the fitted standardization state explicit and
reusable across later chronological folds. When the source feature surface carries
an ``as_of_date``, standardization preserves it so downstream fitting can fail
closed on cutoff mismatches rather than relying on caller convention alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import polars as pl


FEATURE_COLUMNS = (
    "recency_weighted_mean_exit_velocity",
    "recency_weighted_sweet_spot_share",
)


@dataclass(frozen=True, slots=True)
class BattedBallFeatureStandardization:
    mean_exit_velocity: float
    scale_exit_velocity: float
    mean_sweet_spot_share: float
    scale_sweet_spot_share: float
    fitted_player_count: int

    def __post_init__(self) -> None:
        if self.fitted_player_count < 2:
            raise ValueError("feature standardization requires at least two eligible training players")
        if self.scale_exit_velocity <= 0 or self.scale_sweet_spot_share <= 0:
            raise ValueError("feature standardization scales must be positive")


def _eligible_training_rows(features: pl.DataFrame) -> pl.DataFrame:
    required = {"player_id", "tracked_bbe_eligible", *FEATURE_COLUMNS}
    missing = sorted(required - set(features.columns))
    if missing:
        raise ValueError(f"batted-ball features missing fields: {missing}")
    duplicate = features.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("batted-ball features violate player_id grain")
    return features.filter(
        pl.col("tracked_bbe_eligible")
        & pl.col("recency_weighted_mean_exit_velocity").is_not_null()
        & pl.col("recency_weighted_sweet_spot_share").is_not_null()
    )


def fit_batted_ball_feature_standardization(
    training_features: pl.DataFrame,
) -> BattedBallFeatureStandardization:
    """Fit population mean/SD using eligible training rows only."""

    eligible = _eligible_training_rows(training_features)
    if eligible.height < 2:
        raise ValueError("feature standardization requires at least two eligible training players")

    ev_values = [float(value) for value in eligible.get_column(FEATURE_COLUMNS[0]).to_list()]
    ss_values = [float(value) for value in eligible.get_column(FEATURE_COLUMNS[1]).to_list()]

    def mean_scale(values: list[float], label: str) -> tuple[float, float]:
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        scale = sqrt(variance)
        if scale <= 0:
            raise ValueError(f"training {label} has zero variance")
        return mean, scale

    mean_ev, scale_ev = mean_scale(ev_values, "mean exit velocity")
    mean_ss, scale_ss = mean_scale(ss_values, "sweet-spot share")
    return BattedBallFeatureStandardization(
        mean_exit_velocity=mean_ev,
        scale_exit_velocity=scale_ev,
        mean_sweet_spot_share=mean_ss,
        scale_sweet_spot_share=scale_ss,
        fitted_player_count=eligible.height,
    )


def standardize_batted_ball_quality_features(
    features: pl.DataFrame,
    fitted: BattedBallFeatureStandardization,
) -> pl.DataFrame:
    """Apply fixed training-only parameters without refitting evaluation rows.

    ``as_of_date`` is optional for compatibility with small deterministic callers,
    but when present it is preserved unchanged for downstream chronology checks.
    """

    required = {"player_id", "tracked_bbe_eligible", *FEATURE_COLUMNS}
    missing = sorted(required - set(features.columns))
    if missing:
        raise ValueError(f"batted-ball features missing fields: {missing}")
    duplicate = features.group_by("player_id").len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("batted-ball features violate player_id grain")

    passthrough = ["as_of_date"] if "as_of_date" in features.columns else []
    return (
        features.select(*passthrough, "player_id", "tracked_bbe_eligible", *FEATURE_COLUMNS)
        .with_columns(
            pl.when(
                pl.col("tracked_bbe_eligible")
                & pl.col(FEATURE_COLUMNS[0]).is_not_null()
                & pl.col(FEATURE_COLUMNS[1]).is_not_null()
            )
            .then(
                (pl.col(FEATURE_COLUMNS[0]) - fitted.mean_exit_velocity)
                / fitted.scale_exit_velocity
            )
            .otherwise(None)
            .cast(pl.Float64)
            .alias("z_mean_exit_velocity"),
            pl.when(
                pl.col("tracked_bbe_eligible")
                & pl.col(FEATURE_COLUMNS[0]).is_not_null()
                & pl.col(FEATURE_COLUMNS[1]).is_not_null()
            )
            .then(
                (pl.col(FEATURE_COLUMNS[1]) - fitted.mean_sweet_spot_share)
                / fitted.scale_sweet_spot_share
            )
            .otherwise(None)
            .cast(pl.Float64)
            .alias("z_sweet_spot_share"),
        )
        .select(
            *passthrough,
            "player_id",
            "tracked_bbe_eligible",
            "z_mean_exit_velocity",
            "z_sweet_spot_share",
        )
        .sort("player_id")
    )
