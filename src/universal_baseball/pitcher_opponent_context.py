"""Exact prior-only opponent-quality exposures for affiliated pitchers."""

from __future__ import annotations

import polars as pl

from universal_baseball.historical_matchup_profiles import PROFILE_SPECS


OPPONENT_CONTEXT_COLUMNS = (
    "opponent_context_pa",
    "opponent_overall_known_rate",
    "opponent_split_known_rate",
    "opponent_left_batter_share",
    "opponent_switch_batter_share",
    "opponent_mean_log_history_pa",
    "opponent_mean_split_log_history_pa",
    "opponent_mean_level_step",
    *(f"opponent_overall_{name}" for name in PROFILE_SPECS),
    *(f"opponent_split_{name}" for name in PROFILE_SPECS),
)


def aggregate_pitcher_opponent_context(
    events: pl.DataFrame,
    overall_profiles: pl.DataFrame,
    split_profiles: pl.DataFrame,
) -> pl.DataFrame:
    """Summarize the strictly prior hitter quality actually faced by each pitcher."""

    required = {
        "season",
        "pitcher_id",
        "batter_id",
        "pitcher_hand",
        "batter_side",
        "level_rank",
    }
    if missing := sorted(required - set(events.columns)):
        raise ValueError(f"matchup events missing pitcher context fields: {missing}")
    joined = (
        events.join(
            overall_profiles.rename(
                {"target_season": "season", "player_id": "batter_id"}
            ),
            on=["season", "batter_id"],
            how="left",
            validate="m:1",
        )
        .join(
            split_profiles.rename(
                {"target_season": "season", "player_id": "batter_id"}
            ),
            on=["season", "batter_id", "pitcher_hand"],
            how="left",
            validate="m:1",
        )
        .with_columns(
            pl.col("h_history_pa").is_not_null().alias("overall_known"),
            pl.col("hs_history_pa").is_not_null().alias("split_known"),
            (
                pl.col("level_rank")
                - pl.col("h_last_level_rank").fill_null(pl.col("level_rank"))
            ).alias("opponent_level_step"),
            pl.col("h_history_pa").fill_null(0.0).log1p().alias(
                "opponent_log_history_pa"
            ),
            pl.col("hs_history_pa").fill_null(0.0).log1p().alias(
                "opponent_split_log_history_pa"
            ),
            *(
                pl.col(f"h_{name}").fill_null(0.0)
                for name in PROFILE_SPECS
            ),
            *(
                pl.col(f"hs_{name}").fill_null(pl.col(f"h_{name}")).fill_null(0.0)
                for name in PROFILE_SPECS
            ),
        )
    )
    return (
        joined.group_by("season", "pitcher_id")
        .agg(
            pl.len().alias("opponent_context_pa"),
            pl.col("overall_known").mean().alias("opponent_overall_known_rate"),
            pl.col("split_known").mean().alias("opponent_split_known_rate"),
            (pl.col("batter_side") == "L").mean().alias(
                "opponent_left_batter_share"
            ),
            (pl.col("batter_side") == "S").mean().alias(
                "opponent_switch_batter_share"
            ),
            pl.col("opponent_log_history_pa").mean().alias(
                "opponent_mean_log_history_pa"
            ),
            pl.col("opponent_split_log_history_pa").mean().alias(
                "opponent_mean_split_log_history_pa"
            ),
            pl.col("opponent_level_step").mean().alias("opponent_mean_level_step"),
            *(
                pl.col(f"h_{name}").mean().alias(f"opponent_overall_{name}")
                for name in PROFILE_SPECS
            ),
            *(
                pl.col(f"hs_{name}").mean().alias(f"opponent_split_{name}")
                for name in PROFILE_SPECS
            ),
        )
        .rename({"pitcher_id": "player_id"})
        .sort("season", "player_id")
    )


def add_neutral_opponent_context(
    stat_features: pl.DataFrame, context: pl.DataFrame
) -> pl.DataFrame:
    """Join exact-season context, making unavailable evidence exactly neutral."""

    required = {"season", "player_id", *OPPONENT_CONTEXT_COLUMNS}
    if missing := sorted(required - set(context.columns)):
        raise ValueError(f"pitcher opponent context missing fields: {missing}")
    return stat_features.join(
        context.select(*required),
        on=["season", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        *(pl.col(column).fill_null(0.0) for column in OPPONENT_CONTEXT_COLUMNS),
        pl.col("opponent_context_pa").is_not_null().cast(pl.Int8).alias(
            "opponent_context_available"
        ),
    )
