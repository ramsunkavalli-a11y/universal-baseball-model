"""Chronology-safe pitcher role, workload, and level-transition features."""

from __future__ import annotations

import polars as pl

from universal_baseball.hitter_target_architecture import LEVEL_VALUES


ROLE_FEATURES = (
    "role_recent_start_share",
    "role_weighted_start_share",
    "role_start_share_trend",
    "role_start_share_volatility",
    "workload_recent_log_bf",
    "workload_log_bf_trend",
    "workload_peak_log_bf",
    "workload_weighted_log_bf",
    "workload_interrupted",
    "workload_rebound",
    "history_available_seasons",
    "prior_mlb_bf_share",
    "prior_mlb_bf_total_log",
    "level_recent_rank",
    "level_rank_trend",
)


def add_pitcher_role_features(panel: pl.DataFrame) -> pl.DataFrame:
    """Expose compact transitions already latent in three historical lag rows."""

    required = {
        "lag0__start_share",
        "lag1__start_share",
        "lag2__start_share",
        "lag0__games",
        "lag1__games",
        "lag2__games",
        "lag0__starts",
        "lag1__starts",
        "lag2__starts",
        "lag0__batters_faced",
        "lag1__batters_faced",
        "lag2__batters_faced",
        "lag0__log_batters_faced",
        "lag1__log_batters_faced",
        "lag2__log_batters_faced",
        "lag0__bf_level__MLB",
        "lag1__bf_level__MLB",
        "lag2__bf_level__MLB",
        "lag0__highest_level",
        "lag1__highest_level",
        "lag0__missing",
        "lag1__missing",
        "lag2__missing",
    }
    if missing := sorted(required - set(panel.columns)):
        raise ValueError(f"pitcher panel missing role-history fields: {missing}")

    available = [1.0 - pl.col(f"lag{lag}__missing") for lag in range(3)]
    log_bf = [pl.col(f"lag{lag}__log_batters_faced").fill_null(0.0) for lag in range(3)]
    bf = [pl.col(f"lag{lag}__batters_faced").fill_null(0.0) for lag in range(3)]
    mlb_bf = [pl.col(f"lag{lag}__bf_level__MLB").fill_null(0.0) for lag in range(3)]
    starts = [pl.col(f"lag{lag}__starts").fill_null(0.0) for lag in range(3)]
    games = [pl.col(f"lag{lag}__games").fill_null(0.0) for lag in range(3)]
    start_share = [
        pl.col(f"lag{lag}__start_share").fill_null(0.0) for lag in range(3)
    ]
    level0 = pl.col("lag0__highest_level").replace_strict(
        LEVEL_VALUES, default=-1.0
    )
    level1 = pl.col("lag1__highest_level").replace_strict(
        LEVEL_VALUES, default=-1.0
    )
    total_bf = pl.sum_horizontal(*bf)
    total_mlb_bf = pl.sum_horizontal(*mlb_bf)

    return panel.with_columns(
        start_share[0].alias("role_recent_start_share"),
        (
            pl.sum_horizontal(*starts)
            / pl.sum_horizontal(*games).clip(lower_bound=1.0)
        ).alias("role_weighted_start_share"),
        (start_share[0] - start_share[1]).alias("role_start_share_trend"),
        (
            (start_share[0] - start_share[1]).abs()
            + (start_share[1] - start_share[2]).abs()
        ).alias("role_start_share_volatility"),
        log_bf[0].alias("workload_recent_log_bf"),
        (log_bf[0] - log_bf[1]).alias("workload_log_bf_trend"),
        pl.max_horizontal(*log_bf).alias("workload_peak_log_bf"),
        (
            (5.0 * log_bf[0] + 4.0 * log_bf[1] + 3.0 * log_bf[2])
            / (5.0 * available[0] + 4.0 * available[1] + 3.0 * available[2])
            .clip(lower_bound=1.0)
        ).alias("workload_weighted_log_bf"),
        ((bf[1] >= 100.0) & (bf[0] < 0.5 * bf[1])).cast(pl.Int8).alias(
            "workload_interrupted"
        ),
        ((bf[2] >= 100.0) & (bf[1] < 0.5 * bf[2]) & (bf[0] > bf[1])).cast(
            pl.Int8
        ).alias("workload_rebound"),
        pl.sum_horizontal(*available).alias("history_available_seasons"),
        (total_mlb_bf / total_bf.clip(lower_bound=1.0)).alias("prior_mlb_bf_share"),
        total_mlb_bf.log1p().alias("prior_mlb_bf_total_log"),
        level0.alias("level_recent_rank"),
        (level0 - level1).alias("level_rank_trend"),
    )
