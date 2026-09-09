"""Phase 2 workload correction for players with established MLB usage."""

from __future__ import annotations

import polars as pl


WORKLOAD_MODEL_ID = "phase2_prior_mlb_workload_anchor_v1"


def anchor_workload_paths(
    paths: pl.DataFrame,
    current_workload: pl.DataFrame,
    *,
    conditional_column: str,
    expected_column: str,
    current_column: str,
    variance_column: str,
    workload_cap: float,
    reliability_exposure: float,
    anchor_strength: float = 0.75,
    annual_decay: float = 0.75,
) -> pl.DataFrame:
    """Blend the hurdle estimate with recent MLB workload and fade the anchor.

    The probability of appearing in MLB is unchanged. Only workload conditional on
    appearing is corrected. This targets the documented high-workload tail bias
    without granting MLB opportunity to players who have not reached MLB.
    """

    required = {
        "player_id",
        "horizon",
        "mlb_active_probability",
        conditional_column,
        expected_column,
        variance_column,
    }
    if missing := sorted(required - set(paths.columns)):
        raise ValueError(f"workload paths missing fields: {missing}")
    if {"player_id", current_column} - set(current_workload.columns):
        raise ValueError("current workload has an unexpected schema")
    if not 0 <= anchor_strength <= 1 or not 0 <= annual_decay <= 1:
        raise ValueError("anchor strength and annual decay must be between zero and one")
    if reliability_exposure <= 0 or workload_cap <= 0:
        raise ValueError("workload cap and reliability exposure must be positive")

    current = current_workload.select("player_id", current_column).with_columns(
        pl.col(current_column).fill_null(0.0).cast(pl.Float64).clip(0.0, workload_cap)
    )
    return (
        paths.join(current, on="player_id", how="left", validate="m:1")
        .with_columns(pl.col(current_column).fill_null(0.0))
        .with_columns(
            (
                pl.lit(anchor_strength)
                * (
                    pl.col(current_column)
                    / (pl.col(current_column) + pl.lit(reliability_exposure))
                )
                * pl.lit(annual_decay).pow(pl.col("horizon") - 1)
            ).alias("workload_anchor_weight")
        )
        .with_columns(
            (
                pl.col(conditional_column)
                + pl.col("workload_anchor_weight")
                * (pl.col(current_column) - pl.col(conditional_column))
            )
            .clip(0.0, workload_cap)
            .alias(conditional_column)
        )
        .with_columns(
            (pl.col("mlb_active_probability") * pl.col(conditional_column)).alias(
                expected_column
            ),
            # Preserve the original conditional coefficient of variation. The
            # later uncertainty stage therefore remains conservative and smooth.
            (
                pl.col(variance_column)
                * (
                    pl.col(conditional_column)
                    / pl.when(pl.col(expected_column) > 0)
                    .then(pl.col(expected_column) / pl.col("mlb_active_probability"))
                    .otherwise(pl.col(conditional_column))
                ).pow(2)
            ).alias(variance_column),
            pl.lit(WORKLOAD_MODEL_ID).alias("workload_model_id"),
        )
    )
