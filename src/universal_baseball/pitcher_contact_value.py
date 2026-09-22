"""Detailed pitcher contact features and complete result-value targets."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.conditional_war_rates import PITCHER_WAR_ALLOCATION
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.hitter_value_panel import LEVEL_ALIASES, LEVEL_ORDER


CONTACT_EVENTS = ("single", "double", "triple", "home_run", "non_hit_other")


def _require(frame: pl.DataFrame, columns: set[str], label: str) -> None:
    if missing := sorted(columns - set(frame.columns)):
        raise ValueError(f"{label} missing fields: {missing}")


def build_pitcher_contact_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Build season/level-relative hit-type features from affiliated totals."""

    required = {
        "season",
        "player_id",
        "level_group",
        "batters_faced",
        "strike_outs",
        "base_on_balls",
        "intentional_walks",
        "hit_batters",
        "hits",
        "doubles",
        "triples",
        "home_runs",
    }
    _require(frame, required, "affiliated pitcher contact statistics")
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
            (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("_ubb"),
            (
                pl.col("hits")
                - pl.col("doubles")
                - pl.col("triples")
                - pl.col("home_runs")
            ).alias("single"),
            pl.col("doubles").alias("double"),
            pl.col("triples").alias("triple"),
            pl.col("home_runs").alias("home_run"),
        )
        .with_columns(
            (
                pl.col("batters_faced")
                - pl.col("strike_outs")
                - pl.col("_ubb")
                - pl.col("hit_batters")
                - pl.sum_horizontal("single", "double", "triple", "home_run")
            ).alias("non_hit_other")
        )
    )
    if source.filter(pl.col("_level_rank") < 0).height:
        unsupported = sorted(source.filter(pl.col("_level_rank") < 0)["_level"].unique())
        raise ValueError(f"unsupported pitcher levels: {unsupported}")
    if source.filter(
        pl.any_horizontal(*(pl.col(event) < 0 for event in CONTACT_EVENTS))
    ).height:
        raise ValueError("pitcher detailed contact accounting produced a negative count")

    environment = source.group_by("season", "_level").agg(
        pl.col("batters_faced").sum().alias("_environment_bf"),
        *(pl.col(event).sum().alias(f"_environment_{event}") for event in CONTACT_EVENTS),
    ).with_columns(
        *(
            (
                pl.col(f"_environment_{event}")
                / pl.col("_environment_bf").clip(lower_bound=1)
            ).alias(f"_environment_{event}_rate")
            for event in CONTACT_EVENTS
        )
    )
    source = source.join(
        environment.select(
            "season",
            "_level",
            *(f"_environment_{event}_rate" for event in CONTACT_EVENTS),
        ),
        on=["season", "_level"],
        validate="m:1",
    ).with_columns(
        *(
            (pl.col("batters_faced") * pl.col(f"_environment_{event}_rate")).alias(
                f"_expected_{event}"
            )
            for event in CONTACT_EVENTS
        )
    )
    return (
        source.group_by("season", "player_id")
        .agg(
            pl.col("batters_faced").sum(),
            *(pl.col(event).sum().alias(event) for event in CONTACT_EVENTS),
            *(
                pl.col(f"_expected_{event}").sum().alias(f"expected_{event}")
                for event in CONTACT_EVENTS
            ),
        )
        .with_columns(
            *(
                (pl.col(event) / pl.col("batters_faced").clip(lower_bound=1)).alias(
                    f"contact_{event}_rate"
                )
                for event in CONTACT_EVENTS
            ),
            *(
                (
                    (pl.col(event) - pl.col(f"expected_{event}"))
                    / pl.col("batters_faced").clip(lower_bound=1)
                ).alias(f"relative_contact_{event}_rate")
                for event in CONTACT_EVENTS
            ),
        )
        .select(
            "season",
            "player_id",
            *(f"contact_{event}_rate" for event in CONTACT_EVENTS),
            *(f"relative_contact_{event}_rate" for event in CONTACT_EVENTS),
        )
        .sort("season", "player_id")
    )


def build_full_mlb_pitcher_value_targets(
    pitching: pl.DataFrame,
    *,
    runs_per_win: float = 10.0,
) -> pl.DataFrame:
    """Value every observed hit type allowed while centering each MLB season."""

    required = {
        "season",
        "player_id",
        "pitching_bf",
        "pitching_so",
        "pitching_ubb",
        "pitching_hbp",
        "pitching_hits",
        "pitching_doubles",
        "pitching_triples",
        "pitching_hr",
    }
    _require(pitching, required, "detailed MLB pitcher outcomes")
    if not math.isfinite(runs_per_win) or runs_per_win <= 0:
        raise ValueError("runs_per_win must be finite and positive")
    grouped = (
        pitching.group_by("season", "player_id")
        .agg(*(pl.col(column).sum() for column in required - {"season", "player_id"}))
        .filter(pl.col("pitching_bf") > 0)
        .with_columns(
            (
                pl.col("pitching_hits")
                - pl.col("pitching_doubles")
                - pl.col("pitching_triples")
                - pl.col("pitching_hr")
            ).alias("single")
        )
    )
    if grouped.filter(
        (pl.col("single") < 0)
        | (pl.col("pitching_hits") > pl.col("pitching_bf"))
    ).height:
        raise ValueError("detailed MLB pitcher hit accounting is invalid")
    weighted_events = (
        pl.col("pitching_ubb") * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + pl.col("pitching_hbp") * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + pl.col("single") * NEUTRAL_WOBA_WEIGHTS["1B"]
        + pl.col("pitching_doubles") * NEUTRAL_WOBA_WEIGHTS["2B"]
        + pl.col("pitching_triples") * NEUTRAL_WOBA_WEIGHTS["3B"]
        + pl.col("pitching_hr") * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    grouped = grouped.with_columns(
        (weighted_events / pl.col("pitching_bf")).alias("observed_full_woba_allowed")
    )
    environment = grouped.group_by("season").agg(
        pl.col("pitching_bf").sum().alias("league_bf"),
        weighted_events.sum().alias("league_weighted_events"),
    ).with_columns(
        (pl.col("league_weighted_events") / pl.col("league_bf")).alias(
            "league_full_woba_allowed"
        ),
        (PITCHER_WAR_ALLOCATION * runs_per_win * 800.0 / pl.col("league_bf")).alias(
            "replacement_runs_per_800"
        ),
    )
    return (
        grouped.join(environment, on="season", validate="m:1")
        .with_columns(
            (
                -(pl.col("observed_full_woba_allowed") - pl.col("league_full_woba_allowed"))
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
            "observed_full_woba_allowed",
            "league_full_woba_allowed",
            "pitching_runs_above_average_per_800",
            "conditional_component_war_per_800",
            "component_war",
        )
        .sort("season", "player_id")
    )
