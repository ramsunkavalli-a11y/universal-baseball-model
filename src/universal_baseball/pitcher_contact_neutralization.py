"""Pitcher-owned contact value after event-level context neutralization."""

from __future__ import annotations

import math

import numpy as np
import polars as pl

from universal_baseball.current_talent_contact_value import (
    FROZEN_TERMINAL_OUTCOME_VALUES,
)
from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES


OUTCOME_VALUES = {
    outcome: FROZEN_TERMINAL_OUTCOME_VALUES[
        "OUT" if outcome == "OTHER_OUT" else outcome
    ]
    for outcome in CONTACT_OUTCOMES
}


def aggregate_pitcher_contact_value(
    events: pl.DataFrame,
    context_probability: np.ndarray,
    *,
    prior_contacts: float = 250.0,
) -> pl.DataFrame:
    """Aggregate actual-minus-expected contact value to pitcher seasons.

    Positive residual value is bad for the pitcher: the observed contact outcome was
    more valuable to the batter than the held-out context model expected.
    """

    required = {"season", "player_id", "level", "canonical_outcome"}
    if missing := sorted(required - set(events.columns)):
        raise ValueError(f"pitcher contact events missing fields: {missing}")
    if not math.isfinite(prior_contacts) or prior_contacts <= 0:
        raise ValueError("prior contacts must be finite and positive")
    if context_probability.shape != (events.height, len(CONTACT_OUTCOMES)):
        raise ValueError("probability shape does not match pitcher contact events")
    if not np.isfinite(context_probability).all():
        raise ValueError("pitcher contact probabilities contain non-finite values")

    value_vector = np.array(
        [OUTCOME_VALUES[outcome] for outcome in CONTACT_OUTCOMES], dtype=np.float64
    )
    actual_value = np.array(
        [OUTCOME_VALUES[outcome] for outcome in events["canonical_outcome"].to_list()],
        dtype=np.float64,
    )
    expected_value = context_probability.astype(np.float64) @ value_vector
    residual = actual_value - expected_value
    return (
        events.select("season", "player_id", "level")
        .with_columns(
            pl.Series("actual_contact_value", actual_value),
            pl.Series("expected_contact_value", expected_value),
            pl.Series("contact_value_residual", residual),
        )
        .group_by("season", "player_id")
        .agg(
            pl.len().alias("contact_events"),
            pl.col("level").n_unique().alias("contact_levels"),
            pl.col("actual_contact_value").mean(),
            pl.col("expected_contact_value").mean(),
            pl.col("contact_value_residual").sum().alias("contact_value_residual_sum"),
        )
        .with_columns(
            (
                pl.col("contact_value_residual_sum")
                / (pl.col("contact_events") + prior_contacts)
            ).alias("contact_value_residual_rate")
        )
        .sort("season", "player_id")
    )


def attach_pitcher_contact_value_lags(
    panel: pl.DataFrame,
    annual_features: pl.DataFrame,
    *,
    prefix: str,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Attach pitcher contact-value evidence without filling missing rows favorably."""

    if not prefix:
        raise ValueError("feature prefix cannot be empty")
    panel_required = {"origin_year", "target_season", "player_id"}
    annual_required = {"season", "player_id", "contact_value_residual_rate"}
    if missing := sorted(panel_required - set(panel.columns)):
        raise ValueError(f"pitcher panel missing fields: {missing}")
    if missing := sorted(annual_required - set(annual_features.columns)):
        raise ValueError(f"annual pitcher contact features missing fields: {missing}")
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 target rows are not allowed")

    result = panel
    feature_columns = [
        column for column in annual_features.columns if column not in {"season", "player_id"}
    ]
    for lag in lags:
        renamed = (
            annual_features.rename(
                {column: f"{prefix}_lag{lag}__{column}" for column in feature_columns}
            )
            .with_columns((pl.col("season") + lag).alias("origin_year"))
            .drop("season")
        )
        result = result.join(
            renamed,
            on=["origin_year", "player_id"],
            how="left",
            validate="m:1",
        ).with_columns(
            pl.col(f"{prefix}_lag{lag}__contact_events")
            .is_not_null()
            .cast(pl.Int8)
            .alias(f"{prefix}_lag{lag}__available")
        )
    return result.sort("origin_year", "player_id")
