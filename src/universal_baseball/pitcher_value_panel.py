"""Clean-slate historical pitcher features and next-season value targets."""

from __future__ import annotations

from collections.abc import Iterable
import math

import polars as pl

from universal_baseball.conditional_war_rates import PITCHER_WAR_ALLOCATION
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.hitter_value_panel import LEVEL_ALIASES, LEVEL_ORDER


PITCHER_COMPONENTS = (
    "batters_faced",
    "strike_outs",
    "base_on_balls",
    "intentional_walks",
    "hit_batters",
    "home_runs",
    "games",
    "starts",
)
MODEL_ORIGINS = (
    2009,
    2010,
    2011,
    2012,
    2013,
    2014,
    2015,
    2016,
    2017,
    2018,
    2021,
    2022,
    2023,
    2024,
)


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def _assert_unique(frame: pl.DataFrame, key: tuple[str, ...], label: str) -> None:
    if frame.group_by(list(key)).len().filter(pl.col("len") != 1).height:
        raise ValueError(f"{label} violates {'/'.join(key)} grain")


def build_pitcher_stat_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Aggregate affiliated pitching lines to one player-season feature row."""

    _require(
        frame,
        {"season", "player_id", "level_group", *PITCHER_COMPONENTS},
        "affiliated pitcher statistics",
    )
    source = (
        frame.with_columns(
            pl.col("level_group").cast(pl.String).str.to_uppercase().alias("_level")
        )
        .with_columns(pl.col("_level").replace(LEVEL_ALIASES).alias("_level"))
        .with_columns(
            pl.col("_level")
            .replace_strict(LEVEL_ORDER, default=-1)
            .cast(pl.Int64)
            .alias("_level_rank"),
            (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        )
        .with_columns(
            (
                pl.col("batters_faced")
                - pl.col("strike_outs")
                - pl.col("ubb")
                - pl.col("hit_batters")
                - pl.col("home_runs")
            ).alias("other_bf")
        )
    )
    if source.filter(pl.col("_level_rank") < 0).height:
        unsupported = sorted(source.filter(pl.col("_level_rank") < 0)["_level"].unique())
        raise ValueError(f"unsupported pitcher levels: {unsupported}")
    if source.filter(
        pl.any_horizontal(pl.col("ubb") < 0, pl.col("other_bf") < 0)
    ).height:
        raise ValueError("pitcher component accounting produced a negative count")

    component_counts = {
        "strikeout": "strike_outs",
        "ubb": "ubb",
        "hbp": "hit_batters",
        "home_run": "home_runs",
        "other": "other_bf",
    }
    environments = source.group_by("season", "_level").agg(
        pl.col("batters_faced").sum().alias("_environment_bf"),
        *(
            pl.col(column).sum().alias(f"_environment_{name}")
            for name, column in component_counts.items()
        ),
    ).with_columns(
        *(
            (
                pl.col(f"_environment_{name}")
                / pl.col("_environment_bf").clip(lower_bound=1)
            ).alias(f"_environment_{name}_rate")
            for name in component_counts
        )
    )
    source = source.join(
        environments.select(
            "season",
            "_level",
            *(f"_environment_{name}_rate" for name in component_counts),
        ),
        on=["season", "_level"],
        validate="m:1",
    ).with_columns(
        *(
            (pl.col("batters_faced") * pl.col(f"_environment_{name}_rate")).alias(
                f"_expected_{name}"
            )
            for name in component_counts
        )
    )

    level_bf = (
        source.group_by("season", "player_id", "_level")
        .agg(pl.col("batters_faced").sum().alias("bf"))
        .pivot(on="_level", index=["season", "player_id"], values="bf")
    )
    for level in LEVEL_ORDER:
        if level not in level_bf.columns:
            level_bf = level_bf.with_columns(pl.lit(0).alias(level))
    level_bf = level_bf.select(
        "season",
        "player_id",
        *(pl.col(level).fill_null(0).alias(f"bf_level__{level}") for level in LEVEL_ORDER),
    )

    totals = source.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in PITCHER_COMPONENTS),
        pl.col("ubb").sum(),
        pl.col("other_bf").sum(),
        *(
            pl.col(f"_expected_{name}").sum().alias(f"expected_{name}")
            for name in component_counts
        ),
        pl.col("_level").sort_by("_level_rank").last().alias("highest_level"),
        pl.col("reported_age").drop_nulls().mean().alias("reported_age")
        if "reported_age" in source.columns
        else pl.lit(None, dtype=pl.Float64).alias("reported_age"),
    )
    totals = totals.with_columns(
        pl.col("batters_faced").log1p().alias("log_batters_faced"),
        (pl.col("starts") / pl.col("games").clip(lower_bound=1)).alias("start_share"),
        *(
            (
                pl.col(column) / pl.col("batters_faced").clip(lower_bound=1)
            ).alias(f"{name}_rate")
            for name, column in component_counts.items()
        ),
        *(
            (
                (pl.col(column) - pl.col(f"expected_{name}"))
                / pl.col("batters_faced").clip(lower_bound=1)
            ).alias(f"relative_{name}_rate")
            for name, column in component_counts.items()
        ),
    )
    return totals.join(
        level_bf, on=["season", "player_id"], how="left", validate="1:1"
    ).sort("season", "player_id")


def build_neutral_mlb_pitcher_value_targets(
    pitching: pl.DataFrame,
    *,
    runs_per_win: float = 10.0,
    neutral_woba: float = 0.3188,
) -> pl.DataFrame:
    """Compute pitcher component WAR from MLB K, UBB, HBP, HR, and other BF."""

    required = {
        "season",
        "player_id",
        "pitching_bf",
        "pitching_so",
        "pitching_ubb",
        "pitching_hbp",
        "pitching_hr",
    }
    _require(pitching, required, "MLB pitcher outcomes")
    if not math.isfinite(runs_per_win) or runs_per_win <= 0:
        raise ValueError("runs_per_win must be finite and positive")
    grouped = (
        pitching.group_by("season", "player_id")
        .agg(*(pl.col(column).sum() for column in required - {"season", "player_id"}))
        .filter(pl.col("pitching_bf") > 0)
        .with_columns(
            (
                pl.col("pitching_bf")
                - pl.col("pitching_so")
                - pl.col("pitching_ubb")
                - pl.col("pitching_hbp")
                - pl.col("pitching_hr")
            ).alias("pitching_other")
        )
    )
    if grouped.filter(pl.col("pitching_other") < 0).height:
        raise ValueError("MLB pitcher component accounting produced a negative count")
    environment = grouped.group_by("season").agg(
        pl.col("pitching_bf").sum().alias("league_bf"),
        pl.col("pitching_ubb").sum().alias("league_ubb"),
        pl.col("pitching_hbp").sum().alias("league_hbp"),
        pl.col("pitching_hr").sum().alias("league_hr"),
        pl.col("pitching_other").sum().alias("league_other"),
    ).with_columns(
        (
            (
                neutral_woba
                - pl.col("league_ubb")
                / pl.col("league_bf")
                * NEUTRAL_WOBA_WEIGHTS["UBB"]
                - pl.col("league_hbp")
                / pl.col("league_bf")
                * NEUTRAL_WOBA_WEIGHTS["HBP"]
                - pl.col("league_hr")
                / pl.col("league_bf")
                * NEUTRAL_WOBA_WEIGHTS["HR"]
            )
            / (pl.col("league_other") / pl.col("league_bf"))
        ).alias("other_weight"),
        (PITCHER_WAR_ALLOCATION * runs_per_win * 800.0 / pl.col("league_bf")).alias(
            "replacement_runs_per_800"
        ),
    )
    return (
        grouped.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                (
                    pl.col("pitching_ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
                    + pl.col("pitching_hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
                    + pl.col("pitching_hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
                    + pl.col("pitching_other") * pl.col("other_weight")
                )
                / pl.col("pitching_bf")
            ).alias("observed_woba_allowed")
        )
        .with_columns(
            (
                -(pl.col("observed_woba_allowed") - neutral_woba)
                * 800.0
                / NEUTRAL_WOBA_SCALE
            ).alias("pitching_runs_above_average_per_800")
        )
        .with_columns(
            (
                (
                    pl.col("pitching_runs_above_average_per_800")
                    + pl.col("replacement_runs_per_800")
                )
                / runs_per_win
            ).alias("conditional_component_war_per_800")
        )
        .with_columns(
            (
                pl.col("pitching_bf")
                * pl.col("conditional_component_war_per_800")
                / 800.0
            ).alias("component_war"),
            pl.lit(1).cast(pl.Int8).alias("mlb_active"),
        )
        .select(
            "season",
            "player_id",
            pl.col("pitching_bf").alias("mlb_bf"),
            "mlb_active",
            "pitching_runs_above_average_per_800",
            "conditional_component_war_per_800",
            "component_war",
        )
        .sort("season", "player_id")
    )


def build_pitcher_value_panel(
    stat_features: pl.DataFrame,
    value_targets: pl.DataFrame,
    *,
    origins: Iterable[int] = MODEL_ORIGINS,
    lags: tuple[int, ...] = (0, 1, 2),
) -> pl.DataFrame:
    """Build chronology-safe pitcher rows with zero-inclusive next-year MLB value."""

    origins = tuple(int(value) for value in origins)
    if any(year >= 2025 for year in origins):
        raise ValueError("development origins may not expose a 2026 target")
    if 2019 in origins or 2020 in origins:
        raise ValueError("2019/2020 cannot define a normal next-season MiLB transition")
    if not lags or lags[0] != 0 or any(lag < 0 for lag in lags):
        raise ValueError("lags must begin at zero and be nonnegative")
    _assert_unique(stat_features, ("season", "player_id"), "stat features")
    _assert_unique(value_targets, ("season", "player_id"), "value targets")

    base = stat_features.with_columns(
        pl.lit(1).cast(pl.Int8).alias("season_available")
    )
    panel = base.filter(pl.col("season").is_in(origins)).select(
        pl.col("season").alias("origin_year"), "player_id"
    )
    feature_columns = [
        column for column in base.columns if column not in {"season", "player_id"}
    ]
    for lag in lags:
        renamed = {column: f"lag{lag}__{column}" for column in feature_columns}
        shifted = base.with_columns((pl.col("season") + lag).alias("origin_year")).select(
            "origin_year", "player_id", *feature_columns
        ).rename(renamed)
        panel = (
            panel.join(
                shifted,
                on=["origin_year", "player_id"],
                how="left",
                validate="1:1",
            )
            .with_columns(
                pl.col(f"lag{lag}__season_available")
                .is_null()
                .cast(pl.Int8)
                .alias(f"lag{lag}__missing")
            )
            .with_columns(pl.col(f"lag{lag}__season_available").fill_null(0))
        )

    panel = panel.with_columns(
        (pl.col("origin_year") + 1).alias("target_season"),
        (pl.col("origin_year") >= 2021).cast(pl.Int8).alias("post_2020_reorg"),
        (pl.col("origin_year") <= 2019)
        .cast(pl.Int8)
        .alias("short_season_structure_present"),
    )
    target = value_targets.with_columns(
        (pl.col("season") - 1).alias("origin_year")
    ).select(
        "origin_year",
        "player_id",
        pl.col("mlb_bf").alias("target_mlb_bf"),
        pl.col("mlb_active").alias("target_mlb_active"),
        pl.col("conditional_component_war_per_800").alias(
            "target_conditional_component_war_per_800"
        ),
        pl.col("component_war").alias("target_component_war"),
    )
    panel = panel.join(
        target,
        on=["origin_year", "player_id"],
        how="left",
        validate="1:1",
    ).with_columns(
        pl.col("target_mlb_bf").fill_null(0.0),
        pl.col("target_mlb_active").fill_null(0),
        pl.col("target_component_war").fill_null(0.0),
    )
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise ValueError("protected 2026 targets entered the pitcher value panel")
    return panel.sort("origin_year", "player_id")
