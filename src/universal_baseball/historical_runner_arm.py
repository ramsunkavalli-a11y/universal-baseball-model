"""Historical non-steal advancement and joint runner/outfielder effects."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import polars as pl


OUTFIELD_OPPORTUNITY_TYPES = (
    "first_on_single",
    "first_on_double",
    "second_on_single",
    "tag_on_air_out",
)


def add_advancement_value(opportunities: pl.DataFrame) -> pl.DataFrame:
    """Map a clean runner movement to an ordinal extra-base value.

    Zero is the ordinary/held destination for the opportunity, one or two is
    useful extra advancement, and minus one is an advancement out.  A later
    production model will replace this transparent pilot target with RE24.
    """

    required = {"opportunity_type", "origin_base", "destination_base"}
    missing = sorted(required - set(opportunities.columns))
    if missing:
        raise ValueError(f"runner opportunities missing value fields: {missing}")
    destination = pl.col("destination_base")
    opportunity = pl.col("opportunity_type")
    value = (
        pl.when(destination == 0)
        .then(-1.0)
        .when(opportunity == "first_on_single")
        .then(
            pl.when(destination == 4)
            .then(2.0)
            .when(destination >= 3)
            .then(1.0)
            .otherwise(0.0)
        )
        .when(opportunity == "first_on_double")
        .then(pl.when(destination == 4).then(1.0).otherwise(0.0))
        .when(opportunity == "second_on_single")
        .then(pl.when(destination == 4).then(1.0).otherwise(0.0))
        .when(opportunity.is_in(["tag_on_air_out", "second_on_ground_out"]))
        .then(
            pl.when(destination > pl.col("origin_base"))
            .then(1.0)
            .otherwise(0.0)
        )
        .otherwise(None)
    )
    return opportunities.with_columns(value.alias("advancement_value"))


def score_contextual_advancement_residuals(
    opportunities: pl.DataFrame,
    *,
    context_prior: float = 40.0,
    park_prior: float = 80.0,
) -> pl.DataFrame:
    """Score runner outcomes against leave-one-out level/park expectations."""

    if context_prior <= 0 or park_prior <= 0:
        raise ValueError("runner context priors must be positive")
    valued = add_advancement_value(opportunities).filter(
        pl.col("advancement_value").is_not_null()
        & pl.col("destination_base").is_not_null()
    ).with_columns(
        pl.col("stand").fill_null("U").alias("stand_context"),
        pl.col("p_throws").fill_null("U").alias("pitcher_hand_context"),
        pl.col("park_key").fill_null("unknown_park").alias("park_context"),
    )
    if valued.is_empty():
        return valued.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("expected_advancement_value"),
            pl.lit(None, dtype=pl.Float64).alias("advancement_residual"),
        )
    broad_keys = ["season", "level", "opportunity_type", "origin_base"]
    context_keys = [
        *broad_keys,
        "outs_when_up",
        "bb_type",
        "hit_location",
        "stand_context",
        "pitcher_hand_context",
    ]
    park_keys = [*context_keys, "park_context"]
    broad = valued.group_by(broad_keys).agg(
        pl.col("advancement_value").sum().alias("broad_value_sum"),
        pl.len().alias("broad_opportunities"),
    ).with_columns(
        (pl.col("broad_value_sum") / pl.col("broad_opportunities")).alias(
            "broad_advancement_rate"
        )
    )
    context = valued.group_by(context_keys).agg(
        pl.col("advancement_value").sum().alias("context_value_sum"),
        pl.len().alias("context_opportunities"),
    )
    park = valued.group_by(park_keys).agg(
        pl.col("advancement_value").sum().alias("park_value_sum"),
        pl.len().alias("park_opportunities"),
    )
    return (
        valued.join(broad, on=broad_keys, validate="m:1")
        .join(context, on=context_keys, validate="m:1")
        .join(park, on=park_keys, validate="m:1")
        .with_columns(
            (
                (
                    pl.col("context_value_sum") - pl.col("advancement_value")
                    + context_prior * pl.col("broad_advancement_rate")
                )
                / (pl.col("context_opportunities") - 1 + context_prior)
            ).alias("context_expected_advancement")
        )
        .with_columns(
            (
                (
                    pl.col("park_value_sum") - pl.col("advancement_value")
                    + park_prior * pl.col("context_expected_advancement")
                )
                / (pl.col("park_opportunities") - 1 + park_prior)
            ).alias("expected_advancement_value")
        )
        .with_columns(
            (
                pl.col("advancement_value")
                - pl.col("expected_advancement_value")
            ).alias("advancement_residual"),
            (
                pl.col("expected_advancement_value")
                - pl.col("context_expected_advancement")
            ).alias("park_advancement_adjustment"),
        )
    )


def fit_crossed_runner_arm_effects(
    scored: pl.DataFrame,
    *,
    runner_prior: float = 30.0,
    arm_prior: float = 50.0,
    iterations: int = 12,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fit shrinkage effects in ``residual = runner - outfielder + noise``."""

    if min(runner_prior, arm_prior) <= 0 or iterations <= 0:
        raise ValueError("joint runner/arm fitting parameters must be positive")
    required = {
        "season",
        "runner_id",
        "responsible_fielder_id",
        "opportunity_type",
        "outfield_arm_context",
        "advancement_residual",
    }
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"scored runner opportunities missing crossed fields: {missing}")
    work = scored.filter(
        pl.col("outfield_arm_context")
        & pl.col("opportunity_type").is_in(list(OUTFIELD_OPPORTUNITY_TYPES))
        & pl.col("runner_id").is_not_null()
        & pl.col("responsible_fielder_id").is_not_null()
    ).select(
        "season",
        "runner_id",
        pl.col("responsible_fielder_id").alias("outfielder_id"),
        "advancement_residual",
    )
    if work.is_empty():
        empty = pl.DataFrame(
            schema={
                "season": pl.Int64,
                "player_id": pl.Int64,
                "opportunities": pl.Int64,
                "effect": pl.Float64,
            }
        )
        return empty, empty

    arms = work.select("season", "outfielder_id").unique().with_columns(
        pl.lit(0.0).alias("arm_effect")
    )
    runners = work.select("season", "runner_id").unique().with_columns(
        pl.lit(0.0).alias("runner_effect")
    )
    for _ in range(iterations):
        runners = (
            work.join(arms, on=["season", "outfielder_id"], validate="m:1")
            .group_by("season", "runner_id")
            .agg(
                pl.len().alias("runner_opportunities"),
                (pl.col("advancement_residual") + pl.col("arm_effect"))
                .sum()
                .alias("runner_numerator"),
            )
            .with_columns(
                (
                    pl.col("runner_numerator")
                    / (pl.col("runner_opportunities") + runner_prior)
                ).alias("runner_effect")
            )
        )
        arms = (
            work.join(runners, on=["season", "runner_id"], validate="m:1")
            .group_by("season", "outfielder_id")
            .agg(
                pl.len().alias("arm_opportunities"),
                (pl.col("runner_effect") - pl.col("advancement_residual"))
                .sum()
                .alias("arm_numerator"),
            )
            .with_columns(
                (
                    pl.col("arm_numerator")
                    / (pl.col("arm_opportunities") + arm_prior)
                ).alias("arm_effect")
            )
        )
    return (
        runners.select(
            "season",
            pl.col("runner_id").alias("player_id"),
            pl.col("runner_opportunities").alias("opportunities"),
            pl.col("runner_effect").alias("effect"),
        ).sort("season", "player_id"),
        arms.select(
            "season",
            pl.col("outfielder_id").alias("player_id"),
            pl.col("arm_opportunities").alias("opportunities"),
            pl.col("arm_effect").alias("effect"),
        ).sort("season", "player_id"),
    )


def project_effects(
    effects: pl.DataFrame,
    *,
    target_season: int,
    regression_opportunities: float,
    recency_weights: Sequence[float] = (5.0, 4.0, 3.0),
) -> pl.DataFrame:
    """Project runner or arm effects from strictly earlier seasons."""

    history = effects.filter(
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
        .alias("recency_weight")
    )
    if history.is_empty():
        return pl.DataFrame(
            schema={
                "target_season": pl.Int64,
                "player_id": pl.Int64,
                "projected_effect": pl.Float64,
            }
        )
    return (
        history.group_by("player_id")
        .agg(
            (pl.col("effect") * pl.col("opportunities") * pl.col("recency_weight"))
            .sum()
            .alias("weighted_effect_sum"),
            (pl.col("opportunities") * pl.col("recency_weight"))
            .sum()
            .alias("weighted_opportunities"),
            pl.col("opportunities").sum().alias("raw_history_opportunities"),
        )
        .with_columns(
            (
                pl.col("weighted_effect_sum")
                / (pl.col("weighted_opportunities") + regression_opportunities)
            ).alias("projected_effect"),
            pl.lit(target_season, dtype=pl.Int64).alias("target_season"),
        )
    )


def evaluate_effect_projection(
    effects: pl.DataFrame,
    *,
    target_season: int,
    regression_opportunities: float,
    minimum_target_opportunities: int = 10,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Compare prior runner/arm effects with later measured effects."""

    projected = project_effects(
        effects,
        target_season=target_season,
        regression_opportunities=regression_opportunities,
    )
    target = effects.filter(
        (pl.col("season") == target_season)
        & (pl.col("opportunities") >= minimum_target_opportunities)
    ).select(
        "player_id",
        pl.col("opportunities").alias("target_opportunities"),
        pl.col("effect").alias("actual_effect"),
    )
    paired = target.join(projected, on="player_id", how="inner", validate="1:1")
    if paired.is_empty():
        return paired, {"target_season": target_season, "player_count": 0}
    paired = paired.with_columns(
        (pl.col("projected_effect") - pl.col("actual_effect")).alias("candidate_error"),
        (-pl.col("actual_effect")).alias("neutral_error"),
    )
    metrics = paired.select(
        pl.len().alias("player_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_effect", "actual_effect").alias("correlation"),
    ).row(0, named=True)
    return paired, {
        "target_season": target_season,
        **{
            key: int(value) if key == "player_count" else float(value)
            for key, value in metrics.items()
        },
        "rmse_change": float(metrics["candidate_rmse"] - metrics["neutral_rmse"]),
    }
