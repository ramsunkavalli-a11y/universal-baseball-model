"""Classic play-by-play fielding range measurement and projection helpers.

This is intentionally closer to Total Zone than to a black-box player model:
first estimate how often comparable balls become outs, then credit the fielder
with the residual.  Context rates are leave-one-play-out and hierarchically
shrunk from location/park to broader level and position environments.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import polars as pl


INFIELD_POSITIONS = (4, 5, 6)


def _safe_rate(successes: pl.Expr, opportunities: pl.Expr) -> pl.Expr:
    return pl.when(opportunities > 0).then(successes / opportunities).otherwise(0.0)


def score_contextual_fielding_residuals(
    opportunities: pl.DataFrame,
    *,
    positions: Sequence[int] = INFIELD_POSITIONS,
    batted_ball_types: Sequence[str] = ("ground_ball",),
    context_prior: float = 50.0,
    park_prior: float = 100.0,
    location_prior: float = 30.0,
    batter_prior: float = 100.0,
    use_coordinates: bool = True,
    use_park_adjustment: bool = True,
) -> pl.DataFrame:
    """Assign a leave-one-out expected-out probability to each opportunity."""

    if min(context_prior, park_prior, location_prior, batter_prior) <= 0:
        raise ValueError("all fielding priors must be positive")
    required = {
        "season",
        "level",
        "game_pk",
        "at_bat_index",
        "responsible_position",
        "responsible_fielder_id",
        "conversion_out",
        "bb_type",
        "stand",
        "p_throws",
        "park_key",
        "batter",
        "hc_x",
        "hc_y",
    }
    missing = sorted(required - set(opportunities.columns))
    if missing:
        raise ValueError(f"fielding opportunities missing range fields: {missing}")

    plays = opportunities.filter(
        pl.col("responsible_position").is_in(list(positions))
        & pl.col("bb_type").is_in(list(batted_ball_types))
        & pl.col("responsible_fielder_id").is_not_null()
    ).with_columns(
        pl.col("conversion_out").cast(pl.Float64).alias("actual_out"),
        pl.col("stand").fill_null("U").alias("stand_context"),
        pl.col("p_throws").fill_null("U").alias("pitcher_hand_context"),
        pl.col("park_key").fill_null("unknown_park").alias("park_context"),
        pl.when(pl.col("hc_x").is_not_null() & pl.col("hc_y").is_not_null())
        .then(
            pl.concat_str(
                [
                    (pl.col("hc_x") / 10.0).floor().cast(pl.Int64),
                    (pl.col("hc_y") / 10.0).floor().cast(pl.Int64),
                ],
                separator=":",
            )
        )
        .otherwise(pl.lit("missing"))
        .alias("coordinate_bin"),
    )
    if plays.is_empty():
        return plays.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("expected_out_probability"),
            pl.lit(None, dtype=pl.Float64).alias("fielding_out_residual"),
        )

    position_keys = ["season", "level", "responsible_position"]
    context_keys = [
        *position_keys,
        "bb_type",
        "stand_context",
        "pitcher_hand_context",
    ]
    park_keys = [*context_keys, "park_context"]
    location_parent_keys = park_keys if use_park_adjustment else context_keys
    location_keys = [*location_parent_keys, "coordinate_bin"]

    position = plays.group_by(position_keys).agg(
        pl.col("actual_out").sum().alias("position_outs"),
        pl.len().alias("position_opportunities"),
    ).with_columns(
        _safe_rate(pl.col("position_outs"), pl.col("position_opportunities")).alias(
            "position_out_rate"
        )
    )
    context = plays.group_by(context_keys).agg(
        pl.col("actual_out").sum().alias("context_outs"),
        pl.len().alias("context_opportunities"),
    )
    park = plays.group_by(park_keys).agg(
        pl.col("actual_out").sum().alias("park_outs"),
        pl.len().alias("park_opportunities"),
    )
    location = plays.group_by(location_keys).agg(
        pl.col("actual_out").sum().alias("location_outs"),
        pl.len().alias("location_opportunities"),
    )

    scored = (
        plays.join(position, on=position_keys, validate="m:1")
        .join(context, on=context_keys, validate="m:1")
        .join(park, on=park_keys, validate="m:1")
        .join(location, on=location_keys, validate="m:1")
        .with_columns(
            (
                (
                    (pl.col("context_outs") - pl.col("actual_out"))
                    + context_prior * pl.col("position_out_rate")
                )
                / (pl.col("context_opportunities") - 1 + context_prior)
            ).alias("context_expected_out")
        )
        .with_columns(
            pl.when(pl.lit(bool(use_park_adjustment)))
            .then(
                (
                    (pl.col("park_outs") - pl.col("actual_out"))
                    + park_prior * pl.col("context_expected_out")
                )
                / (pl.col("park_opportunities") - 1 + park_prior)
            )
            .otherwise(pl.col("context_expected_out"))
            .alias("park_expected_out")
        )
        .with_columns(
            pl.when(pl.lit(bool(use_coordinates)) & (pl.col("coordinate_bin") != "missing"))
            .then(
                (
                    (pl.col("location_outs") - pl.col("actual_out"))
                    + location_prior * pl.col("park_expected_out")
                )
                / (pl.col("location_opportunities") - 1 + location_prior)
            )
            .otherwise(pl.col("park_expected_out"))
            .alias("pre_batter_expected_out")
        )
        .with_columns(
            (pl.col("actual_out") - pl.col("pre_batter_expected_out")).alias(
                "pre_batter_residual"
            )
        )
    )
    batter = scored.group_by(["season", "level", "batter"]).agg(
        pl.col("pre_batter_residual").sum().alias("batter_residual_sum"),
        pl.len().alias("batter_opportunities"),
    )
    return (
        scored.join(batter, on=["season", "level", "batter"], validate="m:1")
        .with_columns(
            (
                (
                    pl.col("batter_residual_sum")
                    - pl.col("pre_batter_residual")
                )
                / (pl.col("batter_opportunities") - 1 + batter_prior)
            ).alias("batter_out_adjustment")
        )
        .with_columns(
            (pl.col("pre_batter_expected_out") + pl.col("batter_out_adjustment"))
            .clip(0.01, 0.99)
            .alias("expected_out_probability")
        )
        .with_columns(
            (pl.col("actual_out") - pl.col("expected_out_probability")).alias(
                "fielding_out_residual"
            ),
            pl.lit(
                "loo_level_position_context_plus_park_batter_location_v1"
                if use_coordinates and use_park_adjustment
                else (
                    "loo_level_position_context_plus_batter_location_v1"
                    if use_coordinates
                    else (
                        "loo_level_position_context_plus_park_batter_v1"
                        if use_park_adjustment
                        else "loo_level_position_context_plus_batter_v1"
                    )
                )
            ).alias("range_measurement_model"),
        )
        .sort(["season", "game_pk", "at_bat_index"])
    )


def _center_shrunken_effect(
    frame: pl.DataFrame,
    *,
    group_keys: Sequence[str],
    strata_keys: Sequence[str],
    target_column: str,
    output_column: str,
    prior: float,
) -> pl.DataFrame:
    """Estimate a zero-centered, partially pooled additive group effect."""

    grouped = frame.group_by(list(group_keys)).agg(
        pl.col(target_column).sum().alias("_effect_sum"),
        pl.len().alias("_effect_n"),
    ).with_columns(
        (pl.col("_effect_sum") / (pl.col("_effect_n") + float(prior))).alias(
            output_column
        )
    )
    centers = grouped.group_by(list(strata_keys)).agg(
        (
            (pl.col(output_column) * pl.col("_effect_n")).sum()
            / pl.col("_effect_n").sum()
        ).alias("_effect_center")
    )
    return (
        grouped.join(centers, on=list(strata_keys), validate="m:1")
        .with_columns(
            (pl.col(output_column) - pl.col("_effect_center")).alias(output_column)
        )
        .select(*group_keys, output_column, pl.col("_effect_n").alias(f"{output_column}_n"))
    )


def score_visitor_anchored_park_fielding_residuals(
    opportunities: pl.DataFrame,
    *,
    positions: Sequence[int] = INFIELD_POSITIONS,
    batted_ball_types: Sequence[str] = ("ground_ball",),
    park_prior: float = 200.0,
) -> pl.DataFrame:
    """Estimate each park from visiting defenses, then apply it to all plays."""

    if park_prior <= 0:
        raise ValueError("park prior must be positive")
    required = {"defense_team", "home_team"}
    missing = sorted(required - set(opportunities.columns))
    if missing:
        raise ValueError(f"fielding opportunities missing visitor-anchor fields: {missing}")
    base = score_contextual_fielding_residuals(
        opportunities,
        positions=positions,
        batted_ball_types=batted_ball_types,
        use_coordinates=True,
        use_park_adjustment=False,
    ).with_columns(
        (pl.col("defense_team") == pl.col("home_team")).fill_null(False).alias(
            "defense_is_home"
        ),
        pl.col("fielding_out_residual").alias("visitor_anchor_base_residual"),
    )
    if base.is_empty():
        return base
    strata = ["season", "level", "responsible_position"]
    park_keys = [*strata, "park_context"]
    visitor = base.filter(~pl.col("defense_is_home"))
    effect = _center_shrunken_effect(
        visitor,
        group_keys=park_keys,
        strata_keys=strata,
        target_column="visitor_anchor_base_residual",
        output_column="visitor_park_effect",
        prior=park_prior,
    )
    return (
        base.join(effect, on=park_keys, how="left", validate="m:1")
        .with_columns(
            pl.col("visitor_park_effect").fill_null(0.0),
            pl.col("visitor_park_effect_n").fill_null(0),
        )
        .with_columns(
            (
                pl.col("expected_out_probability")
                + pl.col("visitor_park_effect")
            )
            .clip(0.01, 0.99)
            .alias("expected_out_probability")
        )
        .with_columns(
            (pl.col("actual_out") - pl.col("expected_out_probability")).alias(
                "fielding_out_residual"
            ),
            pl.lit("visitor_anchored_park_v1").alias("range_measurement_model"),
        )
        .sort(["season", "game_pk", "at_bat_index"])
    )


def score_joint_park_defense_fielding_residuals(
    opportunities: pl.DataFrame,
    *,
    positions: Sequence[int] = INFIELD_POSITIONS,
    batted_ball_types: Sequence[str] = ("ground_ball",),
    park_prior: float = 200.0,
    team_prior: float = 400.0,
    player_prior: float = 250.0,
    iterations: int = 8,
) -> pl.DataFrame:
    """Separate crossed park, defensive-team, and responsible-fielder effects.

    The contact baseline deliberately excludes park. Additive effects are then
    backfit together so a home club's defense cannot automatically become its
    park factor. Visiting defenses provide the schedule variation that identifies
    the park term. The returned player residual excludes the fitted player term;
    that term is used only to keep player quality out of park and team estimates.
    """

    if min(park_prior, team_prior, player_prior) <= 0 or iterations <= 0:
        raise ValueError("joint-effect priors and iterations must be positive")
    required = {"defense_team", "home_team"}
    missing = sorted(required - set(opportunities.columns))
    if missing:
        raise ValueError(f"fielding opportunities missing joint-effect fields: {missing}")

    base = score_contextual_fielding_residuals(
        opportunities,
        positions=positions,
        batted_ball_types=batted_ball_types,
        use_coordinates=True,
        use_park_adjustment=False,
    ).with_columns(
        pl.col("defense_team").fill_null("unknown_team").alias("defense_team_context"),
        (pl.col("defense_team") == pl.col("home_team")).fill_null(False).alias(
            "defense_is_home"
        ),
        pl.col("fielding_out_residual").alias("joint_base_residual"),
        pl.lit(0.0).alias("joint_park_effect"),
        pl.lit(0.0).alias("joint_team_effect"),
        pl.lit(0.0).alias("joint_player_effect"),
    )
    if base.is_empty():
        return base

    strata = ["season", "level", "responsible_position"]
    park_keys = [*strata, "park_context"]
    team_keys = [*strata, "defense_team_context"]
    player_keys = ["season", "responsible_position", "responsible_fielder_id"]

    work = base
    for _ in range(iterations):
        work = work.with_columns(
            (
                pl.col("joint_base_residual")
                - pl.col("joint_team_effect")
                - pl.col("joint_player_effect")
            ).alias("_park_target")
        )
        park = _center_shrunken_effect(
            work,
            group_keys=park_keys,
            strata_keys=strata,
            target_column="_park_target",
            output_column="joint_park_effect",
            prior=park_prior,
        )
        work = work.drop(
            "joint_park_effect", "joint_park_effect_n", strict=False
        ).join(park, on=park_keys, validate="m:1")

        work = work.with_columns(
            (
                pl.col("joint_base_residual")
                - pl.col("joint_park_effect")
                - pl.col("joint_player_effect")
            ).alias("_team_target")
        )
        team = _center_shrunken_effect(
            work,
            group_keys=team_keys,
            strata_keys=strata,
            target_column="_team_target",
            output_column="joint_team_effect",
            prior=team_prior,
        )
        work = work.drop(
            "joint_team_effect", "joint_team_effect_n", strict=False
        ).join(team, on=team_keys, validate="m:1")

        work = work.with_columns(
            (
                pl.col("joint_base_residual")
                - pl.col("joint_park_effect")
                - pl.col("joint_team_effect")
            ).alias("_player_target")
        )
        player = _center_shrunken_effect(
            work,
            group_keys=player_keys,
            strata_keys=["season", "responsible_position"],
            target_column="_player_target",
            output_column="joint_player_effect",
            prior=player_prior,
        )
        work = work.drop(
            "joint_player_effect", "joint_player_effect_n", strict=False
        ).join(
            player, on=player_keys, validate="m:1"
        )

    return (
        work.with_columns(
            (
                pl.col("expected_out_probability")
                + pl.col("joint_park_effect")
                + pl.col("joint_team_effect")
            )
            .clip(0.01, 0.99)
            .alias("expected_out_probability")
        )
        .with_columns(
            (pl.col("actual_out") - pl.col("expected_out_probability")).alias(
                "fielding_out_residual"
            ),
            pl.lit("joint_park_team_player_backfit_v1").alias(
                "range_measurement_model"
            ),
        )
        .drop(
            "_park_target",
            "_team_target",
            "_player_target",
            strict=False,
        )
        .sort(["season", "game_pk", "at_bat_index"])
    )


def aggregate_player_fielding_seasons(scored: pl.DataFrame) -> pl.DataFrame:
    """Aggregate event residuals to player-position-season range rates."""

    required = {
        "season",
        "responsible_fielder_id",
        "responsible_position",
        "fielding_out_residual",
    }
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"scored fielding events missing fields: {missing}")
    return (
        scored.group_by(
            "season", "responsible_fielder_id", "responsible_position"
        )
        .agg(
            pl.len().alias("fielding_opportunities"),
            pl.col("fielding_out_residual").sum().alias("fielding_outs_above_expected"),
            pl.col("expected_out_probability").mean().alias("mean_expected_out_probability"),
        )
        .with_columns(
            (
                pl.col("fielding_outs_above_expected")
                / pl.col("fielding_opportunities")
            ).alias("fielding_outs_above_expected_rate")
        )
        .sort("season", "responsible_fielder_id", "responsible_position")
    )


def project_player_fielding_rates(
    player_seasons: pl.DataFrame,
    *,
    target_season: int,
    recency_weights: Sequence[float] = (5.0, 4.0, 3.0),
    regression_opportunities: float = 150.0,
) -> pl.DataFrame:
    """Project one target year from strictly earlier player-position seasons."""

    if regression_opportunities < 0 or not recency_weights:
        raise ValueError("invalid fielding projection weights")
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
    if history.is_empty():
        return pl.DataFrame(
            schema={
                "target_season": pl.Int64,
                "responsible_fielder_id": pl.Int64,
                "responsible_position": pl.Int64,
                "weighted_history_opportunities": pl.Float64,
                "projected_range_rate": pl.Float64,
            }
        )
    return (
        history.group_by("responsible_fielder_id", "responsible_position")
        .agg(
            (
                pl.col("fielding_outs_above_expected") * pl.col("recency_weight")
            ).sum().alias("weighted_history_residual_outs"),
            (
                pl.col("fielding_opportunities") * pl.col("recency_weight")
            ).sum().alias("weighted_history_opportunities"),
            pl.col("fielding_opportunities").sum().alias("raw_history_opportunities"),
            pl.col("season").n_unique().alias("history_seasons"),
        )
        .with_columns(
            (
                pl.col("weighted_history_residual_outs")
                / (
                    pl.col("weighted_history_opportunities")
                    + float(regression_opportunities)
                )
            ).alias("projected_range_rate"),
            pl.lit(int(target_season), dtype=pl.Int64).alias("target_season"),
            pl.lit(float(regression_opportunities)).alias("regression_opportunities"),
        )
        .sort("responsible_fielder_id", "responsible_position")
    )


def evaluate_fielding_projection(
    player_seasons: pl.DataFrame,
    *,
    target_season: int,
    regression_opportunities: float,
    minimum_target_opportunities: int = 25,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Evaluate one chronological fold against a neutral zero-rate forecast."""

    projected = project_player_fielding_rates(
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
        pl.col("fielding_outs_above_expected_rate").alias("actual_range_rate"),
        pl.col("fielding_outs_above_expected").alias("actual_residual_outs"),
    )
    paired = target.join(
        projected,
        on=["responsible_fielder_id", "responsible_position"],
        how="inner",
        validate="1:1",
    ).with_columns(
        (pl.col("projected_range_rate") - pl.col("actual_range_rate")).alias(
            "candidate_error"
        ),
        (-pl.col("actual_range_rate")).alias("neutral_error"),
    )
    if paired.is_empty():
        return paired, {
            "target_season": int(target_season),
            "player_position_count": 0,
            "candidate_rmse": None,
            "neutral_rmse": None,
            "rmse_change": None,
        }
    metrics = paired.select(
        (pl.col("candidate_error").pow(2).mean().sqrt()).alias("candidate_rmse"),
        (pl.col("neutral_error").pow(2).mean().sqrt()).alias("neutral_rmse"),
        (
            (
                pl.col("candidate_error").pow(2)
                * pl.col("target_opportunities")
            ).sum()
            / pl.col("target_opportunities").sum()
        ).sqrt().alias("candidate_weighted_rmse"),
        (
            (
                pl.col("neutral_error").pow(2)
                * pl.col("target_opportunities")
            ).sum()
            / pl.col("target_opportunities").sum()
        ).sqrt().alias("neutral_weighted_rmse"),
    ).row(0, named=True)
    return paired, {
        "target_season": int(target_season),
        "player_position_count": int(paired.height),
        **{key: float(value) for key, value in metrics.items()},
        "rmse_change": float(metrics["candidate_rmse"] - metrics["neutral_rmse"]),
        "weighted_rmse_change": float(
            metrics["candidate_weighted_rmse"] - metrics["neutral_weighted_rmse"]
        ),
    }


def pooled_projection_metrics(folds: Iterable[pl.DataFrame]) -> dict[str, Any]:
    """Pool fold prediction rows without averaging fold RMSEs."""

    rows = [fold for fold in folds if not fold.is_empty()]
    if not rows:
        return {"player_position_count": 0}
    pooled = pl.concat(rows, how="diagonal_relaxed")
    metrics = pooled.select(
        pl.len().alias("player_position_count"),
        pl.col("candidate_error").pow(2).mean().sqrt().alias("candidate_rmse"),
        pl.col("neutral_error").pow(2).mean().sqrt().alias("neutral_rmse"),
        pl.corr("projected_range_rate", "actual_range_rate").alias("correlation"),
    ).row(0, named=True)
    return {
        **{
            key: int(value) if key == "player_position_count" else float(value)
            for key, value in metrics.items()
        },
        "rmse_change": float(metrics["candidate_rmse"] - metrics["neutral_rmse"]),
    }
