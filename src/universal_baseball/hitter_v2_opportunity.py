"""PBP-derived Hitter v2 opportunity accounting."""

from __future__ import annotations

from typing import Literal

import polars as pl


def _integer(column: str, alias: str | None = None) -> pl.Expr:
    return pl.col(column).cast(pl.Int64, strict=False).alias(alias or column)


def project_gidp_opportunities(
    raw_pbp: pl.DataFrame,
    *,
    base_state_semantics: Literal["pre_pa", "post_pa"],
    game_type: str = "R",
) -> pl.DataFrame:
    """Project one observed GIDP-opportunity flag per plate appearance.

    A GIDP opportunity requires a runner on first and fewer than two outs at
    PA start. ``base_state_semantics`` must declare whether the source
    ``on_1b`` field is already the pre-PA state or is the post-play state that
    must be shifted from the preceding PA in the same half-inning. Ambiguity is
    retained and failed closed.
    """

    required = {
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "inning",
        "inning_half",
        "game_type",
        "batter",
        "on_1b",
        "outs_when_up",
    }
    missing = sorted(required - set(raw_pbp.columns))
    if missing:
        raise ValueError(f"GIDP opportunity source missing fields: {missing}")
    projected = (
        raw_pbp.select(
            _integer("game_pk", "game_id"),
            _integer("at_bat_number", "at_bat_index"),
            _integer("pitch_number"),
            _integer("inning"),
            pl.col("inning_half").cast(pl.String),
            pl.col("game_type").cast(pl.String),
            _integer("batter", "player_id"),
            _integer("on_1b", "source_runner_on_first_id"),
            _integer("outs_when_up"),
        )
        .drop_nulls(
            [
                "game_id",
                "at_bat_index",
                "pitch_number",
                "inning",
                "inning_half",
                "player_id",
            ]
        )
        .filter(pl.col("game_type") == game_type)
    )
    opening = (
        projected.with_columns(
            pl.col("pitch_number")
            .min()
            .over(["game_id", "at_bat_index"])
            .alias("opening_pitch_number")
        )
        .filter(pl.col("pitch_number") == pl.col("opening_pitch_number"))
    )
    resolved = opening.group_by(["game_id", "at_bat_index"]).agg(
        pl.col("player_id").n_unique().alias("player_variant_count"),
        pl.col("player_id").first().alias("player_id"),
        pl.col("inning").n_unique().alias("inning_variant_count"),
        pl.col("inning").first().alias("inning"),
        pl.col("inning_half").n_unique().alias("half_variant_count"),
        pl.col("inning_half").first().alias("inning_half"),
        pl.col("source_runner_on_first_id")
        .fill_null(0)
        .n_unique()
        .alias("source_first_variant_count"),
        pl.col("source_runner_on_first_id")
        .fill_null(0)
        .first()
        .alias("source_runner_on_first_id"),
        pl.col("outs_when_up").n_unique().alias("outs_variant_count"),
        pl.col("outs_when_up").first().alias("outs_when_up"),
        pl.len().alias("raw_opening_row_count"),
    )
    current_conflict = (
        (pl.col("player_variant_count") != 1)
        | (pl.col("inning_variant_count") != 1)
        | (pl.col("half_variant_count") != 1)
        | (pl.col("outs_variant_count") != 1)
        | pl.col("outs_when_up").is_null()
        | ~pl.col("outs_when_up").is_between(0, 2)
    )
    resolved = resolved.with_columns(
        (~current_conflict).alias("current_identity_outs_valid"),
        (pl.col("source_first_variant_count") == 1).alias("source_first_state_valid"),
    ).sort(["game_id", "inning", "inning_half", "at_bat_index"])
    if base_state_semantics == "pre_pa":
        with_start = resolved.with_columns(
            pl.col("source_runner_on_first_id").alias("runner_on_first_id"),
            (
                pl.col("current_identity_outs_valid")
                & pl.col("source_first_state_valid")
            ).alias("opportunity_state_valid"),
        )
        accepted_status = "accepted_exact_pre_pa_state"
        state_failure_status = "failed_closed_current_pre_pa_state_conflict"
    elif base_state_semantics == "post_pa":
        group = ["game_id", "inning", "inning_half"]
        with_start = resolved.with_columns(
            (
                pl.col("at_bat_index")
                == pl.col("at_bat_index").min().over(group)
            ).alias("first_pa_in_half"),
            pl.col("source_runner_on_first_id")
            .shift(1)
            .over(group)
            .fill_null(0)
            .alias("runner_on_first_id"),
            pl.col("source_first_state_valid")
            .shift(1)
            .over(group)
            .alias("previous_post_first_state_valid"),
        ).with_columns(
            (
                pl.col("current_identity_outs_valid")
                & (
                    pl.col("first_pa_in_half")
                    | pl.col("previous_post_first_state_valid").fill_null(False)
                )
            ).alias("opportunity_state_valid")
        )
        accepted_status = "accepted_shifted_prior_post_state"
        state_failure_status = "failed_closed_prior_post_state_conflict"
    else:
        raise ValueError(f"unsupported base-state semantics: {base_state_semantics!r}")
    return (
        with_start.with_columns(
            pl.when(pl.col("opportunity_state_valid"))
            .then(
                (
                    (pl.col("runner_on_first_id") != 0)
                    & (pl.col("outs_when_up") < 2)
                ).cast(pl.Int64)
            )
            .otherwise(None)
            .alias("gidp_opportunity"),
            pl.when(~pl.col("current_identity_outs_valid"))
            .then(pl.lit("failed_closed_current_identity_outs_conflict"))
            .when(~pl.col("opportunity_state_valid"))
            .then(pl.lit(state_failure_status))
            .otherwise(pl.lit(accepted_status))
            .alias("opportunity_source_status"),
        )
        .select(
            "game_id",
            "at_bat_index",
            "player_id",
            "runner_on_first_id",
            "outs_when_up",
            "gidp_opportunity",
            "opportunity_source_status",
            "raw_opening_row_count",
        )
        .sort(["game_id", "at_bat_index"])
    )


def aggregate_player_game_gidp_opportunities(
    opportunities: pl.DataFrame,
) -> pl.DataFrame:
    """Aggregate PA-opening opportunities to canonical player-game grain."""

    duplicate = (
        opportunities.group_by(["game_id", "at_bat_index"])
        .len()
        .filter(pl.col("len") != 1)
    )
    if not duplicate.is_empty():
        raise ValueError("PA GIDP opportunity keys are not unique")
    return (
        opportunities.group_by(["game_id", "player_id"])
        .agg(
            pl.when(pl.col("gidp_opportunity").null_count() == 0)
            .then(pl.col("gidp_opportunity").sum())
            .otherwise(None)
            .alias("gidp_opportunities"),
            pl.col("gidp_opportunity").null_count().alias("ambiguous_opening_pa"),
            pl.len().alias("observed_pbp_pa"),
        )
        .with_columns(
            (pl.col("ambiguous_opening_pa") == 0).alias(
                "gidp_opportunity_modeling_eligible"
            )
        )
        .sort(["game_id", "player_id"])
    )
