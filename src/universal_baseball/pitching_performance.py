"""Universal batter-faced outcome profile for Pitching v1.

The first pitching layer deliberately uses only certified season aggregate
fields that exist across MLB and affiliated levels.  It does not assign ordinary
balls in play to the pitcher, infer missing sacrifice bunts, or mix future
workload into rate skill.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl


PITCHING_OUTCOME_BINS = ("K", "UBB", "HBP", "HR", "OTHER_BF")
PITCHING_PROFILE_METHOD = "universal_bf_outcome_profile_v1"
PITCHING_GRAIN = ("season", "league_id", "player_id")

_COUNT_COLUMNS = (
    "pitching_games_played",
    "pitching_games_started",
    "pitching_batters_faced",
    "pitching_strike_outs",
    "pitching_base_on_balls",
    "pitching_intentional_walks",
    "pitching_hit_batsmen",
    "pitching_home_runs",
)
_REQUIRED_COLUMNS = {*PITCHING_GRAIN, *_COUNT_COLUMNS}


@dataclass(frozen=True, slots=True)
class PitchingPerformance:
    """Validated player/league/season summary and long outcome profile."""

    summary: pl.DataFrame
    profile: pl.DataFrame
    metrics: dict[str, Any]


def _integer_like(column: str) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & numeric.is_finite() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64))
        .otherwise(None)
        .alias(column)
    )


def _validated_counts(frame: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(_REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"pitching Performance source missing required fields: {missing}")

    working = frame.select(
        *(_integer_like(column) for column in PITCHING_GRAIN),
        *(_integer_like(column) for column in _COUNT_COLUMNS),
    )
    required_order = [*PITCHING_GRAIN, *_COUNT_COLUMNS]
    invalid_integer_counts = {
        column: working.get_column(column).null_count()
        for column in required_order
        if working.get_column(column).null_count()
    }
    if invalid_integer_counts:
        raise ValueError(
            "pitching Performance identifiers and counts must be finite integers; "
            f"invalid/null counts by field={invalid_integer_counts}"
        )
    if working.filter(pl.any_horizontal(*(pl.col(column) < 0 for column in _COUNT_COLUMNS))).height:
        raise ValueError("pitching Performance counts must be nonnegative")
    if working.filter(pl.col("pitching_games_started") > pl.col("pitching_games_played")).height:
        raise ValueError("pitching games started cannot exceed games played")
    if working.filter(
        (pl.col("pitching_batters_faced") > 0)
        & (pl.col("pitching_games_played") == 0)
    ).height:
        raise ValueError("positive pitching BF requires at least one game played")
    return working


def _profile_frame(summary: pl.DataFrame) -> pl.DataFrame:
    count_columns = {
        "K": "pitching_strike_outs",
        "UBB": "pitching_unintentional_walks",
        "HBP": "pitching_hit_batsmen",
        "HR": "pitching_home_runs",
        "OTHER_BF": "pitching_other_batters_faced",
    }
    frames = []
    for outcome_bin in PITCHING_OUTCOME_BINS:
        frames.append(
            summary.select(
                *PITCHING_GRAIN,
                pl.lit(outcome_bin).alias("pitching_outcome_bin"),
                pl.col(count_columns[outcome_bin]).alias("occurrence_count"),
                (
                    pl.col(count_columns[outcome_bin])
                    / pl.col("pitching_batters_faced")
                ).alias("observed_probability"),
                pl.lit(PITCHING_PROFILE_METHOD).alias("pitching_profile_method"),
            )
        )
    return pl.concat(frames, how="vertical").sort(
        [*PITCHING_GRAIN, "pitching_outcome_bin"]
    )


def validate_pitching_performance(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    *,
    tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Validate the canonical Pitching v1 Performance outputs."""

    if tolerance < 0:
        raise ValueError("pitching profile tolerance must be nonnegative")
    summary_required = {
        *PITCHING_GRAIN,
        "pitching_batters_faced",
        "pitching_profile_event_count",
    }
    profile_required = {
        *PITCHING_GRAIN,
        "pitching_outcome_bin",
        "occurrence_count",
        "observed_probability",
    }
    if missing := sorted(summary_required - set(summary.columns)):
        raise ValueError(f"pitching Performance summary missing fields: {missing}")
    if missing := sorted(profile_required - set(profile.columns)):
        raise ValueError(f"pitching Performance profile missing fields: {missing}")

    duplicate_summary = summary.group_by(list(PITCHING_GRAIN)).len().filter(pl.col("len") != 1)
    if not duplicate_summary.is_empty():
        raise ValueError("pitching Performance summary violates canonical grain")
    duplicate_profile = profile.group_by(
        [*PITCHING_GRAIN, "pitching_outcome_bin"]
    ).len().filter(pl.col("len") != 1)
    if not duplicate_profile.is_empty():
        raise ValueError("pitching Performance profile violates canonical grain")

    invalid_bins = sorted(set(profile.get_column("pitching_outcome_bin").to_list()) - set(PITCHING_OUTCOME_BINS))
    if invalid_bins:
        raise ValueError(f"pitching Performance profile has unsupported bins: {invalid_bins}")

    reconciliation = summary.select(
        *PITCHING_GRAIN,
        "pitching_batters_faced",
        "pitching_profile_event_count",
    ).join(
        profile.group_by(list(PITCHING_GRAIN)).agg(
            pl.len().alias("profile_bin_count"),
            pl.col("occurrence_count").sum().alias("profile_occurrence_count"),
            pl.col("observed_probability").sum().alias("profile_probability_sum"),
        ),
        on=list(PITCHING_GRAIN),
        how="left",
    )
    invalid = reconciliation.filter(
        (pl.col("profile_bin_count") != len(PITCHING_OUTCOME_BINS))
        | (pl.col("profile_occurrence_count") != pl.col("pitching_batters_faced"))
        | (pl.col("pitching_profile_event_count") != pl.col("pitching_batters_faced"))
        | ((pl.col("profile_probability_sum") - 1.0).abs() > tolerance)
    )
    if not invalid.is_empty():
        raise ValueError("pitching Performance profile does not reconcile exactly to BF")

    return {
        "summary_row_count": summary.height,
        "profile_row_count": profile.height,
        "outcome_bin_count": len(PITCHING_OUTCOME_BINS),
        "all_profile_counts_reconcile_to_bf": True,
        "all_profile_probabilities_sum_to_one": True,
    }


def build_pitching_performance(frame: pl.DataFrame) -> PitchingPerformance:
    """Build the canonical positive-BF Pitching v1 Performance profile.

    Input may contain multiple team rows for one player/league/season. Those
    rows are summed before rates are calculated. A player in multiple actual
    leagues remains in multiple rows.
    """

    working = _validated_counts(frame)
    source_row_count = working.height
    zero_bf_source_row_count = working.filter(
        pl.col("pitching_batters_faced") == 0
    ).height
    positive = working.filter(pl.col("pitching_batters_faced") > 0)
    if positive.is_empty():
        raise ValueError("pitching Performance source contains no positive-BF rows")

    aggregated = (
        positive.group_by(list(PITCHING_GRAIN))
        .agg(*(pl.col(column).sum().alias(column) for column in _COUNT_COLUMNS))
        .with_columns(
            (
                pl.col("pitching_base_on_balls")
                - pl.col("pitching_intentional_walks")
            ).alias("pitching_unintentional_walks")
        )
    )
    if aggregated.filter(pl.col("pitching_unintentional_walks") < 0).height:
        raise ValueError("pitching intentional walks cannot exceed total walks")

    summary = (
        aggregated.with_columns(
            (
                pl.col("pitching_batters_faced")
                - pl.col("pitching_strike_outs")
                - pl.col("pitching_unintentional_walks")
                - pl.col("pitching_hit_batsmen")
                - pl.col("pitching_home_runs")
            ).alias("pitching_other_batters_faced")
        )
        .with_columns(
            pl.col("pitching_batters_faced").alias("pitching_profile_event_count"),
            (
                pl.col("pitching_games_started")
                / pl.col("pitching_games_played")
            ).alias("observed_starter_share"),
            pl.lit(PITCHING_PROFILE_METHOD).alias("pitching_profile_method"),
        )
        .sort(list(PITCHING_GRAIN))
    )
    if summary.filter(pl.col("pitching_other_batters_faced") < 0).height:
        raise ValueError("pitching outcome components exceed batters faced")

    profile = _profile_frame(summary)
    validation = validate_pitching_performance(summary, profile)
    metrics = {
        **validation,
        "source_row_count": source_row_count,
        "zero_bf_source_row_count": zero_bf_source_row_count,
        "positive_bf_source_row_count": positive.height,
        "distinct_player_count": summary.get_column("player_id").n_unique(),
        "total_batters_faced": int(summary.get_column("pitching_batters_faced").sum()),
        "pitching_profile_method": PITCHING_PROFILE_METHOD,
        "intentional_walk_policy": "retained_in_other_bf_not_pitcher_walk_skill",
    }
    return PitchingPerformance(summary=summary, profile=profile, metrics=metrics)
