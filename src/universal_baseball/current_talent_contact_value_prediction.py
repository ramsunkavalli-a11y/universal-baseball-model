"""Prediction-geometry contract for frozen Current Talent challenger 2.

This module may be used only after the additive contact baseline and two-feature
player residual fits are frozen.  It applies those fixed fits to one already-
paired future target surface and proves that comparator and richer predictions
share exactly the same canonical event rows.

It deliberately does **not** calculate squared error, absolute error, calibration,
transport gates, fold wins, or any promotion decision.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from universal_baseball.current_talent_contact_value import (
    ContactValueBaselineFit,
    ContactValueResidualFit,
    apply_contact_value_baseline,
    apply_contact_value_residual,
)
from universal_baseball.current_talent_contact_value_evidence import (
    CONTACT_VALUE_TARGET_KEY,
)


def materialize_contact_value_prediction_geometry(
    paired_future_contacts: pl.DataFrame,
    *,
    baseline_fit: ContactValueBaselineFit,
    residual_fit: ContactValueResidualFit,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Apply frozen comparator/richer fits without looking at prediction loss."""

    required = {
        "event_date",
        "player_id",
        "contact_bin",
        "level_group",
        "terminal_value",
        "contact_value_residual_applies",
        "z_mean_exit_velocity",
        "z_sweet_spot_share",
        *CONTACT_VALUE_TARGET_KEY,
    }
    missing = sorted(required - set(paired_future_contacts.columns))
    if missing:
        raise ValueError(f"paired contact-value prediction surface missing fields: {missing}")
    if paired_future_contacts.is_empty():
        raise ValueError("paired contact-value prediction surface must not be empty")

    key_columns = list(CONTACT_VALUE_TARGET_KEY)
    if paired_future_contacts.group_by(key_columns).len().filter(pl.col("len") != 1).height:
        raise ValueError("paired contact-value prediction surface has duplicate event keys")
    if paired_future_contacts.filter(~pl.col("contact_value_residual_applies")).height:
        raise ValueError("paired contact-value prediction surface contains fallback rows")

    expected_keys = paired_future_contacts.select(key_columns).sort(key_columns)
    scored = apply_contact_value_baseline(
        paired_future_contacts,
        baseline_fit,
        output_column="comparator_contact_value_prediction",
    )
    scored = apply_contact_value_residual(
        scored,
        residual_fit,
        output_column="player_contact_value_residual_prediction",
        applies_column="contact_value_residual_applies",
    ).with_columns(
        (
            pl.col("comparator_contact_value_prediction")
            + pl.col("player_contact_value_residual_prediction")
        )
        .cast(pl.Float64)
        .alias("richer_contact_value_prediction")
    )

    actual_keys = scored.select(key_columns).sort(key_columns)
    if scored.height != paired_future_contacts.height or not actual_keys.equals(expected_keys):
        raise ValueError("contact-value prediction geometry changed paired event coverage")
    if scored.group_by(key_columns).len().filter(pl.col("len") != 1).height:
        raise ValueError("contact-value prediction geometry duplicated event keys")

    invalid = scored.filter(
        pl.col("comparator_contact_value_prediction").is_null()
        | ~pl.col("comparator_contact_value_prediction").is_finite()
        | pl.col("player_contact_value_residual_prediction").is_null()
        | ~pl.col("player_contact_value_residual_prediction").is_finite()
        | pl.col("richer_contact_value_prediction").is_null()
        | ~pl.col("richer_contact_value_prediction").is_finite()
    )
    if not invalid.is_empty():
        raise ValueError("contact-value prediction geometry contains invalid predictions")

    # Explicitly never materialize loss columns in this pre-scoring contract.
    forbidden = {
        "comparator_squared_error",
        "richer_squared_error",
        "comparator_absolute_error",
        "richer_absolute_error",
        "mse",
        "mae",
    }
    present_forbidden = sorted(forbidden & set(scored.columns))
    if present_forbidden:
        raise ValueError(f"pre-scoring prediction surface contains loss columns: {present_forbidden}")

    metrics: dict[str, Any] = {
        "paired_event_count": int(scored.height),
        "paired_player_count": int(scored.get_column("player_id").n_unique()),
        "event_keys_unchanged": True,
        "comparator_richer_event_keys_identical": True,
        "prediction_values_finite": True,
        "losses_computed": False,
        "calibration_computed": False,
        "model_scoring": False,
        "accessed_2023": False,
    }
    return scored, metrics
