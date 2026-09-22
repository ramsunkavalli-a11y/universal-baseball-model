"""Convert historical range outs above expectation into contextual run value."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import polars as pl


def add_terminal_re24_change(
    terminal: pl.DataFrame, run_expectancy: pl.DataFrame
) -> pl.DataFrame:
    """Add the batting team's observed RE24 change to each terminal play."""

    required = {
        "season",
        "level",
        "game_pk",
        "inning",
        "inning_top_bot",
        "at_bat_index",
        "outs_when_up",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
        "bat_score",
        "post_bat_score",
    }
    if missing := sorted(required - set(terminal.columns)):
        raise ValueError(f"terminal plays missing RE24 change fields: {missing}")
    half = ["game_pk", "inning", "inning_top_bot"]
    lookup = run_expectancy.select(
        "season", "level", "outs_when_up", "base_state", "run_expectancy"
    )
    work = (
        terminal.sort(*half, "at_bat_index")
        .with_columns(
            (
                pl.col("start_runner_1b").is_not_null().cast(pl.Int8)
                + 2 * pl.col("start_runner_2b").is_not_null().cast(pl.Int8)
                + 4 * pl.col("start_runner_3b").is_not_null().cast(pl.Int8)
            ).alias("base_state"),
        )
        .with_columns(
            pl.col("outs_when_up").shift(-1).over(half).alias("next_outs"),
            pl.col("base_state").shift(-1).over(half).alias("next_base_state"),
            (pl.col("post_bat_score") - pl.col("bat_score"))
            .cast(pl.Float64)
            .alias("runs_scored"),
        )
    )
    return (
        work.join(lookup, on=["season", "level", "outs_when_up", "base_state"], how="left", validate="m:1")
        .join(
            lookup.rename(
                {
                    "outs_when_up": "next_outs",
                    "base_state": "next_base_state",
                    "run_expectancy": "next_run_expectancy",
                }
            ),
            on=["season", "level", "next_outs", "next_base_state"],
            how="left",
            validate="m:1",
        )
        .with_columns(pl.col("next_run_expectancy").fill_null(0.0))
        .with_columns(
            (
                pl.col("runs_scored")
                + pl.col("next_run_expectancy")
                - pl.col("run_expectancy")
            ).alias("batting_re24_change")
        )
    )


def add_contextual_fielding_runs(
    scored_fielding: pl.DataFrame,
    terminal_values: pl.DataFrame,
    *,
    context_prior: float = 100.0,
) -> pl.DataFrame:
    """Value an out residual by the local RE24 difference between an out and a hit."""

    if context_prior <= 0:
        raise ValueError("context prior must be positive")
    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "responsible_position",
        "actual_out",
        "fielding_out_residual",
        "outs_when_up",
        "start_runner_1b",
        "start_runner_2b",
        "start_runner_3b",
    }
    if missing := sorted(required - set(scored_fielding.columns)):
        raise ValueError(f"scored fielding plays missing run-value fields: {missing}")
    value_lookup = terminal_values.select(
        "season", "level", "game_pk", "at_bat_index", "batting_re24_change"
    )
    plays = scored_fielding.join(
        value_lookup,
        on=["season", "level", "game_pk", "at_bat_index"],
        how="left",
        validate="m:1",
    ).with_columns(
        (
            pl.col("start_runner_1b").is_not_null().cast(pl.Int8)
            + 2 * pl.col("start_runner_2b").is_not_null().cast(pl.Int8)
            + 4 * pl.col("start_runner_3b").is_not_null().cast(pl.Int8)
        ).alias("base_state")
    ).filter(pl.col("batting_re24_change").is_not_null())

    broad_keys = ["season", "level", "responsible_position", "actual_out"]
    context_keys = [
        "season",
        "level",
        "responsible_position",
        "outs_when_up",
        "base_state",
    ]
    broad = plays.group_by(broad_keys).agg(
        pl.col("batting_re24_change").mean().alias("broad_outcome_value")
    )
    context = (
        plays.group_by(*context_keys, "actual_out")
        .agg(
            pl.col("batting_re24_change").sum().alias("context_value_sum"),
            pl.len().alias("context_value_n"),
        )
        .join(broad, on=broad_keys, validate="m:1")
        .with_columns(
            (
                (
                    pl.col("context_value_sum")
                    + context_prior * pl.col("broad_outcome_value")
                )
                / (pl.col("context_value_n") + context_prior)
            ).alias("context_outcome_value")
        )
    )
    outs = context.filter(pl.col("actual_out") == 1).select(
        *context_keys,
        pl.col("context_outcome_value").alias("context_out_value"),
    )
    nonouts = context.filter(pl.col("actual_out") == 0).select(
        *context_keys,
        pl.col("context_outcome_value").alias("context_nonout_value"),
    )
    broad_wide = broad.group_by("season", "level", "responsible_position").agg(
        pl.col("broad_outcome_value")
        .filter(pl.col("actual_out") == 1)
        .first()
        .alias("broad_out_value"),
        pl.col("broad_outcome_value")
        .filter(pl.col("actual_out") == 0)
        .first()
        .alias("broad_nonout_value"),
    )
    return (
        plays.join(outs, on=context_keys, how="left", validate="m:1")
        .join(nonouts, on=context_keys, how="left", validate="m:1")
        .join(
            broad_wide,
            on=["season", "level", "responsible_position"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.coalesce("context_out_value", "broad_out_value").alias(
                "context_out_value"
            ),
            pl.coalesce("context_nonout_value", "broad_nonout_value").alias(
                "context_nonout_value"
            ),
        )
        .with_columns(
            (pl.col("context_nonout_value") - pl.col("context_out_value"))
            .clip(0.0, 3.0)
            .alias("out_run_swing")
        )
        .with_columns(
            (pl.col("fielding_out_residual") * pl.col("out_run_swing")).alias(
                "fielding_runs_above_expected"
            )
        )
    )


def aggregate_player_fielding_run_seasons(scored: pl.DataFrame) -> pl.DataFrame:
    """Aggregate contextual range runs to player-position seasons."""

    return (
        scored.group_by("season", "responsible_fielder_id", "responsible_position")
        .agg(
            pl.len().alias("fielding_opportunities"),
            pl.col("fielding_runs_above_expected").sum(),
            pl.col("out_run_swing").mean().alias("mean_out_run_swing"),
        )
        .with_columns(
            (
                pl.col("fielding_runs_above_expected")
                / pl.col("fielding_opportunities")
            ).alias("fielding_runs_above_expected_rate")
        )
        .sort("season", "responsible_fielder_id", "responsible_position")
    )


def project_player_fielding_run_rates(
    player_seasons: pl.DataFrame,
    *,
    target_season: int,
    recency_weights: Sequence[float] = (5.0, 4.0, 3.0),
    regression_opportunities: float = 1200.0,
) -> pl.DataFrame:
    """Project a later contextual range-run rate from strictly prior seasons."""

    if regression_opportunities < 0 or not recency_weights:
        raise ValueError("invalid fielding-run projection settings")
    history = player_seasons.filter(
        pl.col("season").is_between(
            target_season - len(recency_weights), target_season - 1
        )
    ).with_columns(
        pl.col("season")
        .replace_strict(
            {
                target_season - lag: float(weight)
                for lag, weight in enumerate(recency_weights, start=1)
            },
            default=0.0,
        )
        .cast(pl.Float64)
        .alias("recency_weight")
    )
    return (
        history.group_by("responsible_fielder_id", "responsible_position")
        .agg(
            (
                pl.col("fielding_runs_above_expected") * pl.col("recency_weight")
            ).sum().alias("weighted_history_runs"),
            (
                pl.col("fielding_opportunities") * pl.col("recency_weight")
            ).sum().alias("weighted_history_opportunities"),
        )
        .with_columns(
            (
                pl.col("weighted_history_runs")
                / (
                    pl.col("weighted_history_opportunities")
                    + regression_opportunities
                )
            ).alias("projected_range_runs_per_opportunity"),
            pl.lit(target_season).alias("target_season"),
        )
    )


def evaluate_fielding_run_projection(
    player_seasons: pl.DataFrame,
    *,
    target_season: int,
    regression_opportunities: float,
    minimum_target_opportunities: int = 25,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Score a chronological run-rate projection against neutral range value."""

    projected = project_player_fielding_run_rates(
        player_seasons,
        target_season=target_season,
        regression_opportunities=regression_opportunities,
    )
    target = player_seasons.filter(
        (pl.col("season") == target_season)
        & (pl.col("fielding_opportunities") >= minimum_target_opportunities)
    ).select(
        "responsible_fielder_id",
        "responsible_position",
        pl.col("fielding_opportunities").alias("target_opportunities"),
        pl.col("fielding_runs_above_expected_rate").alias("actual_run_rate"),
    )
    paired = target.join(
        projected,
        on=["responsible_fielder_id", "responsible_position"],
        how="inner",
        validate="1:1",
    ).with_columns(
        (
            pl.col("projected_range_runs_per_opportunity")
            - pl.col("actual_run_rate")
        ).alias("candidate_error"),
        (-pl.col("actual_run_rate")).alias("neutral_error"),
    )
    if paired.is_empty():
        return paired, {"target_season": target_season, "player_position_count": 0}
    row = paired.select(
        pl.len().alias("player_position_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_range_runs_per_opportunity", "actual_run_rate").alias(
            "correlation"
        ),
    ).row(0, named=True)
    return paired, {
        "target_season": target_season,
        "regression_opportunities": regression_opportunities,
        **row,
        "rmse_change": float(row["candidate_rmse"] - row["neutral_rmse"]),
    }
