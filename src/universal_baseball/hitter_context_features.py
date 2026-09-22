"""Optional chronology-safe park and opponent context for hitter value models."""

from __future__ import annotations

import polars as pl


CONTEXT_COLUMNS = (
    "materialized_contacts",
    "opponent_context_known_rate",
    "venue_known_rate",
    "contact_share_vs_lhp",
    "contact_share_vs_rhp",
    "mean__K_prior_pitcher_log_odds_residual",
    "mean__UBB_prior_pitcher_log_odds_residual",
    "mean__HBP_prior_pitcher_log_odds_residual",
    "mean__HR_prior_pitcher_log_odds_residual",
    "mean__NON_HR_REACH_prior_pitcher_log_odds_residual",
    "mean__HIT_COMPOSITION_prior_pitcher_alr_residual_1B",
    "mean__HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
    "mean__HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
    "mean__K_prior_pitcher_denominator",
    "mean__UBB_prior_pitcher_denominator",
    "mean__HBP_prior_pitcher_denominator",
    "mean__HR_prior_pitcher_denominator",
    "mean__NON_HR_REACH_prior_pitcher_denominator",
    "mean__HIT_COMPOSITION_prior_pitcher_denominator",
    "park_factor_known_rate",
    "mean_park_factor_reliability",
    "mean_park_training_seasons",
    "park_effect__ubb",
    "park_effect__hbp",
    "park_effect__single",
    "park_effect__double",
    "park_effect__triple",
    "park_effect__hr",
    "park_effect__other",
)


def add_context_history(
    panel: pl.DataFrame,
    context: pl.DataFrame,
    *,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Join exact-season context without manufacturing pre-coverage values."""
    required_panel = {"origin_year", "player_id"}
    required_context = {"season", "player_id", *CONTEXT_COLUMNS}
    if missing := sorted(required_panel - set(panel.columns)):
        raise ValueError(f"panel missing fields: {missing}")
    if missing := sorted(required_context - set(context.columns)):
        raise ValueError(f"context missing fields: {missing}")
    if context.group_by(["season", "player_id"]).len().filter(pl.col("len") > 1).height:
        raise ValueError("context must be unique by season and player")

    result = panel
    for lag in lags:
        renamed = {
            column: f"lag{lag}__context__{column}" for column in CONTEXT_COLUMNS
        }
        history = (
            context.select("season", "player_id", *CONTEXT_COLUMNS)
            .with_columns(
                (pl.col("season") + lag).alias("origin_year"),
                pl.lit(1).cast(pl.Int8).alias(f"lag{lag}__context__available"),
            )
            .drop("season")
            .rename(renamed)
        )
        result = result.join(history, on=["origin_year", "player_id"], how="left")
        result = result.with_columns(
            pl.col(f"lag{lag}__context__available").fill_null(0)
        )
    if result.height != panel.height:
        raise ValueError("context join changed panel row count")
    return result
