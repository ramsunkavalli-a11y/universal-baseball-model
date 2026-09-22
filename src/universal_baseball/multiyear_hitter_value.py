"""Versioned calendar-value labels and cutoff-only hitter features."""

from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.hitter_value_panel import (
    LEVEL_ORDER,
    build_hitter_stat_features,
    build_neutral_mlb_value_targets,
)


LEVELS = ("MLB", "AAA", "AA", "A+", "A", "A-", "RK", "INACTIVE", "UNKNOWN")
ALIASES = {"HIGH_A": "A+", "SINGLE_A": "A", "ROOKIE_COMPLEX": "RK", "ROOKIE": "RK"}
ORIGINS = tuple(y for y in range(2009, 2026) if y != 2020)
CORE_RATES = ("ubb_rate", "strikeout_rate", "single_rate", "double_rate",
              "triple_rate", "home_run_rate", "hbp_rate", "stolen_base_rate")


def calendar_targets(hitting: pl.DataFrame, schedules: pl.DataFrame) -> pl.DataFrame:
    """Scale only replacement to completed games; retain observed batting runs."""
    if hitting["season"].max() > 2025 or schedules["season"].max() > 2025:
        raise ValueError("Protected outcome season is not permitted")
    if schedules["season"].n_unique() != schedules.height:
        raise ValueError("Duplicate schedule season")
    if schedules.filter((pl.col("completed_games") <= 0) | (pl.col("teams") <= 0)).height:
        raise ValueError("Invalid completed-game counts")
    base = build_neutral_mlb_value_targets(hitting)
    missing = set(base["season"].unique()) - set(schedules["season"].unique())
    if missing:
        raise ValueError(f"Uncertified schedules: {sorted(missing)}")
    env = base.group_by("season").agg(pl.col("mlb_pa").sum().alias("league_pa"))
    env = env.join(schedules, on="season", validate="1:1").with_columns(
        (2.0 * pl.col("completed_games") / (162.0 * pl.col("teams"))).alias("schedule_fraction")
    )
    return base.join(env, on="season", validate="m:1").with_columns(
        pl.col("component_war").alias("legacy_component_war"),
        (pl.col("component_war") + 570.0 * (pl.col("schedule_fraction") - 1.0)
         * pl.col("mlb_pa") / pl.col("league_pa")).alias("component_war"),
    ).with_columns(
        (pl.col("component_war") * 600.0 / pl.col("mlb_pa")).alias("conditional_component_war_per_600")
    ).sort("season", "player_id")


def prepare_features(
    snapshots: pl.DataFrame, stats: pl.DataFrame, targets: pl.DataFrame,
    membership: pl.DataFrame,
) -> tuple[pl.DataFrame, list[str], list[str]]:
    """Snapshot denominator is retained, including players with no current stats."""
    if snapshots["snapshot_year"].max() > 2025 or stats["season"].max() > 2025:
        raise ValueError("Predictor evidence extends beyond 2025")
    stats = stats.filter(pl.col("plate_appearances") > 0)
    annual = build_hitter_stat_features(stats)
    if snapshots.unique(["snapshot_year", "player_id"]).height != snapshots.height:
        raise ValueError("Duplicate cohort identity")
    base = snapshots.filter(pl.col("snapshot_year").is_in(ORIGINS)).rename(
        {"snapshot_year": "origin_year", "age_years": "age"}
    ).with_columns(
        pl.col("as_of_level_group").replace(ALIASES).alias("level"),
        pl.col("age").is_null().cast(pl.Int8).alias("age_missing"),
    ).with_columns(
        ((pl.col("age") - 27.0) / 10.0).alias("age_centered"),
        (((pl.col("age") - 27.0) / 10.0) ** 2).alias("age_squared"),
        *[(pl.col("level") == level).cast(pl.Int8).alias(f"level_{level}") for level in LEVELS],
        (pl.col("origin_year") >= 2021).cast(pl.Int8).alias("reorganization_era"),
    )
    base_features = ["age_centered", "age_squared", "age_missing", "reorganization_era",
                     *[f"level_{level}" for level in LEVELS]]
    all_features = base_features.copy()
    for lag in range(3):
        selected = annual.select(
            (pl.col("season") + lag).alias("origin_year"), "player_id",
            pl.col("plate_appearances").alias(f"pa_lag{lag}"),
            pl.col("pa_level__MLB").alias(f"mlb_pa_lag{lag}"),
            *[pl.col(c).alias(f"{c}_lag{lag}") for c in CORE_RATES],
            *[pl.col(f"pa_level__{l}").alias(f"exposure_{l}_lag{lag}") for l in LEVEL_ORDER],
        )
        base = base.join(selected, on=["origin_year", "player_id"], how="left", validate="1:1")
        base = base.with_columns(
            pl.col(f"pa_lag{lag}").is_null().cast(pl.Int8).alias(f"missing_lag{lag}"),
            pl.col(f"pa_lag{lag}").fill_null(0).log1p().alias(f"log_pa_lag{lag}"),
            pl.col(f"mlb_pa_lag{lag}").fill_null(0).log1p().alias(f"log_mlb_pa_lag{lag}"),
        )
        bcols = [f"missing_lag{lag}", f"log_pa_lag{lag}", f"log_mlb_pa_lag{lag}"]
        base_features += bcols
        all_features += bcols + [f"{c}_lag{lag}" for c in CORE_RATES]
        for level in LEVEL_ORDER:
            col = f"share_{level}_lag{lag}"
            base = base.with_columns((pl.col(f"exposure_{level}_lag{lag}")
                                      / pl.col(f"pa_lag{lag}").clip(lower_bound=1)).fill_null(0).alias(col))
            all_features.append(col)
        previous = targets.select(
            (pl.col("season") + lag).alias("origin_year"), "player_id",
            pl.col("component_war").alias(f"observed_mlb_value_lag{lag}"),
        )
        base = base.join(previous, on=["origin_year", "player_id"], how="left", validate="1:1")
        base = base.with_columns(pl.col(f"observed_mlb_value_lag{lag}").fill_null(0),
            (pl.col("origin_year") - lag).is_in(targets["season"].unique().to_list()).cast(pl.Int8)
            .alias(f"mlb_value_history_available_lag{lag}"))
        all_features += [f"observed_mlb_value_lag{lag}", f"mlb_value_history_available_lag{lag}"]
    members = membership.select(pl.col("season").alias("origin_year"), "player_id", "on_40man")
    base = base.join(members, on=["origin_year", "player_id"], how="left", validate="1:1").with_columns(
        pl.col("on_40man").fill_null(False).cast(pl.Int8),
    )
    base_features += ["on_40man"]
    all_features += ["on_40man"]
    base = base.with_columns(
        pl.when(pl.col("mlb_pa_lag0").fill_null(0) > 0).then(pl.lit("Current MLB"))
        .when(pl.col("level").is_in(["AAA", "AA"])).then(pl.lit("Upper minors"))
        .when(pl.col("level").is_in(["INACTIVE", "UNKNOWN"])).then(pl.lit("Inactive / unknown"))
        .otherwise(pl.lit("Lower minors")).alias("stage")
    )
    return base.sort("origin_year", "player_id"), base_features, all_features


def attach_outcomes(features: pl.DataFrame, targets: pl.DataFrame) -> pl.DataFrame:
    """Keep unobserved future years null, but certify zeros through 2025."""
    seasons = set(targets["season"].unique())
    result = features
    for h in (1, 2, 3):
        out = targets.select(
            (pl.col("season") - h).alias("origin_year"), "player_id",
            pl.col("component_war").alias(f"war_h{h}"), pl.col("mlb_pa").alias(f"pa_h{h}"),
        )
        result = result.join(out, on=["origin_year", "player_id"], how="left", validate="1:1")
        complete = (pl.col("origin_year") + h).is_in(seasons)
        result = result.with_columns(
            pl.when(complete).then(pl.col(f"war_h{h}").fill_null(0)).otherwise(None).alias(f"war_h{h}"),
            pl.when(complete).then(pl.col(f"pa_h{h}").fill_null(0)).otherwise(None).alias(f"pa_h{h}"),
            complete.alias(f"complete_h{h}"),
        )
    return result.with_columns(
        (pl.col("war_h1") + pl.col("war_h2") + pl.col("war_h3")).alias("war_c3")
    )


def training_mask(panel: pl.DataFrame, cutoff: int, horizon: int, excluded_ids=()) -> np.ndarray:
    """Dec-31 reconstructed vintage: every label year is complete at the cutoff."""
    if horizon not in (1, 2, 3):
        raise ValueError("Unsupported horizon")
    target = panel[f"war_h{horizon}"].to_numpy()
    mask = (panel["origin_year"].to_numpy() + horizon <= cutoff) & np.isfinite(target)
    if len(excluded_ids):
        mask &= ~np.isin(panel["player_id"].to_numpy(), excluded_ids)
    return mask
