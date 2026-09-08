"""Chronology-safe future MLB career outcome panel.

This module turns a fixed player denominator and complete season outcome
backbones into explicit player-season follow-up. Absence from a completed MLB
season is a zero-participation outcome; absence beyond the completed-data
boundary is right censoring and remains null.
"""

from __future__ import annotations

from collections.abc import Collection
from datetime import date

import polars as pl


BATTING_COUNT_COLUMNS = (
    "batting_pa",
    "batting_ab",
    "batting_hits",
    "batting_doubles",
    "batting_triples",
    "batting_hr",
    "batting_bb",
    "batting_hbp",
    "batting_so",
)
PITCHING_COUNT_COLUMNS = (
    "pitching_games",
    "pitching_starts",
    "pitching_bf",
    "pitching_so",
    "pitching_ubb",
    "pitching_hbp",
    "pitching_hr",
)

BATTING_OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    **{column: pl.Int64 for column in BATTING_COUNT_COLUMNS},
}
PITCHING_OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "player_id": pl.Int64,
    **{column: pl.Int64 for column in PITCHING_COUNT_COLUMNS},
}
CAREER_OUTCOME_SCHEMA: dict[str, pl.DataType] = {
    "cohort_as_of_date": pl.Date,
    "player_id": pl.Int64,
    "season": pl.Int64,
    "horizon_year": pl.Int64,
    "followup_status": pl.String,
    "is_right_censored": pl.Boolean,
    "any_mlb_participation": pl.Boolean,
    **{column: pl.Int64 for column in BATTING_COUNT_COLUMNS},
    **{column: pl.Int64 for column in PITCHING_COUNT_COLUMNS},
}

FOLLOWUP_STATUSES = frozenset(
    {"observed_participation", "observed_zero", "right_censored"}
)


def project_mlb_batting_backbone(frame: pl.DataFrame) -> pl.DataFrame:
    """Project the certified MLB batting backbone to career-label counts."""

    mapping = {
        "batting_plate_appearances": "batting_pa",
        "batting_at_bats": "batting_ab",
        "batting_hits": "batting_hits",
        "batting_doubles": "batting_doubles",
        "batting_triples": "batting_triples",
        "batting_home_runs": "batting_hr",
        "batting_base_on_balls": "batting_bb",
        "batting_hit_by_pitch": "batting_hbp",
        "batting_strike_outs": "batting_so",
    }
    required = {"season", "player_id", *mapping}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"MLB batting backbone missing career fields: {missing}")
    projected = frame.select(
        pl.col("season"),
        pl.col("player_id"),
        *(pl.col(source).alias(target) for source, target in mapping.items()),
    )
    return _aggregate_batting(projected)


def project_mlb_pitching_backbone(frame: pl.DataFrame) -> pl.DataFrame:
    """Project the certified MLB pitching backbone to career-label counts."""

    required = {
        "season",
        "player_id",
        "pitching_games_played",
        "pitching_games_started",
        "pitching_batters_faced",
        "pitching_strike_outs",
        "pitching_base_on_balls",
        "pitching_intentional_walks",
        "pitching_hit_batsmen",
        "pitching_home_runs",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"MLB pitching backbone missing career fields: {missing}")
    projected = frame.select(
        pl.col("season"),
        pl.col("player_id"),
        pl.col("pitching_games_played").alias("pitching_games"),
        pl.col("pitching_games_started").alias("pitching_starts"),
        pl.col("pitching_batters_faced").alias("pitching_bf"),
        pl.col("pitching_strike_outs").alias("pitching_so"),
        (
            pl.col("pitching_base_on_balls")
            - pl.col("pitching_intentional_walks")
        ).alias("pitching_ubb"),
        pl.col("pitching_hit_batsmen").alias("pitching_hbp"),
        pl.col("pitching_home_runs").alias("pitching_hr"),
    )
    return _aggregate_pitching(projected)


def _validate_denominator(players: pl.DataFrame) -> pl.DataFrame:
    if set(players.columns) != {"player_id"}:
        raise ValueError("career denominator must contain only player_id")
    result = players.select(pl.col("player_id").cast(pl.Int64, strict=True))
    if result.filter(pl.col("player_id").is_null() | (pl.col("player_id") <= 0)).height:
        raise ValueError("career denominator has null or non-positive player_id")
    if result.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise ValueError("career denominator has duplicate player_id")
    return result.sort("player_id")


def _validate_outcomes(
    frame: pl.DataFrame,
    *,
    schema: dict[str, pl.DataType],
    counts: tuple[str, ...],
    label: str,
) -> pl.DataFrame:
    missing = sorted(set(schema) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(schema))
    if missing:
        raise ValueError(f"{label} missing columns: {missing}")
    if extra:
        raise ValueError(f"{label} has undeclared columns: {extra}")
    result = frame.select(list(schema)).cast(schema, strict=True)
    required = ["season", "player_id", *counts]
    if result.filter(pl.any_horizontal([pl.col(c).is_null() for c in required])).height:
        raise ValueError(f"{label} has null required values")
    if result.filter(pl.any_horizontal([pl.col(c) < 0 for c in counts])).height:
        raise ValueError(f"{label} has negative counts")
    return result


def _aggregate_batting(frame: pl.DataFrame) -> pl.DataFrame:
    result = _validate_outcomes(
        frame,
        schema=BATTING_OUTCOME_SCHEMA,
        counts=BATTING_COUNT_COLUMNS,
        label="batting_outcomes",
    )
    result = result.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in BATTING_COUNT_COLUMNS)
    )
    if result.filter(
        (pl.col("batting_ab") > pl.col("batting_pa"))
        | (pl.col("batting_hits") > pl.col("batting_ab"))
        | (pl.col("batting_doubles") + pl.col("batting_triples") + pl.col("batting_hr")
           > pl.col("batting_hits"))
        | (pl.col("batting_so") > pl.col("batting_pa"))
    ).height:
        raise ValueError("batting_outcomes violate count relationships")
    return result


def _aggregate_pitching(frame: pl.DataFrame) -> pl.DataFrame:
    result = _validate_outcomes(
        frame,
        schema=PITCHING_OUTCOME_SCHEMA,
        counts=PITCHING_COUNT_COLUMNS,
        label="pitching_outcomes",
    )
    result = result.group_by("season", "player_id").agg(
        *(pl.col(column).sum().alias(column) for column in PITCHING_COUNT_COLUMNS)
    )
    if result.filter(
        (pl.col("pitching_starts") > pl.col("pitching_games"))
        | (pl.col("pitching_so") + pl.col("pitching_ubb")
           + pl.col("pitching_hbp") + pl.col("pitching_hr")
           > pl.col("pitching_bf"))
        | ((pl.col("pitching_bf") > 0) & (pl.col("pitching_games") == 0))
    ).height:
        raise ValueError("pitching_outcomes violate count relationships")
    return result


def _validate_complete_prefix(
    seasons: list[int],
    complete_seasons: Collection[int],
) -> set[int]:
    complete = {int(season) for season in complete_seasons}
    outside = sorted(complete - set(seasons))
    if outside:
        raise ValueError(f"complete_seasons outside requested horizon: {outside}")
    observed = [season in complete for season in seasons]
    if any(observed[index] and not all(observed[:index]) for index in range(len(observed))):
        raise ValueError("complete_seasons must be a contiguous prefix of the horizon")
    return complete


def build_career_outcome_panel(
    players: pl.DataFrame,
    batting_outcomes: pl.DataFrame,
    pitching_outcomes: pl.DataFrame,
    *,
    cohort_as_of_date: date,
    first_followup_season: int,
    horizon_seasons: int,
    complete_seasons: Collection[int],
) -> pl.DataFrame:
    """Build complete player-calendar-season follow-up with explicit censoring.

    `complete_seasons` is a source certification assertion. It must be a
    contiguous prefix of the requested horizon. No partial season may be called
    a zero-outcome season through this interface.
    """

    if horizon_seasons < 1:
        raise ValueError("horizon_seasons must be positive")
    if first_followup_season < cohort_as_of_date.year:
        raise ValueError("first_followup_season cannot precede cohort as-of year")
    denominator = _validate_denominator(players)
    seasons = list(range(first_followup_season, first_followup_season + horizon_seasons))
    complete = _validate_complete_prefix(seasons, complete_seasons)
    batting = _aggregate_batting(batting_outcomes)
    pitching = _aggregate_pitching(pitching_outcomes)

    requested = set(seasons)
    incomplete_batting = batting.filter(
        pl.col("season").is_in(sorted(requested - complete))
        & pl.col("player_id").is_in(denominator.get_column("player_id"))
    )
    incomplete_pitching = pitching.filter(
        pl.col("season").is_in(sorted(requested - complete))
        & pl.col("player_id").is_in(denominator.get_column("player_id"))
    )
    if incomplete_batting.height or incomplete_pitching.height:
        raise ValueError("outcome inputs contain rows in right-censored seasons")

    grid = denominator.join(
        pl.DataFrame(
            {
                "season": seasons,
                "horizon_year": list(range(1, horizon_seasons + 1)),
            },
            schema={"season": pl.Int64, "horizon_year": pl.Int64},
        ),
        how="cross",
    )
    joined = grid.join(
        batting.filter(pl.col("season").is_in(seasons)),
        on=["season", "player_id"],
        how="left",
    ).join(
        pitching.filter(pl.col("season").is_in(seasons)),
        on=["season", "player_id"],
        how="left",
    )

    is_complete = pl.col("season").is_in(sorted(complete))
    participated = (
        pl.col("batting_pa").fill_null(0) > 0
    ) | (pl.col("pitching_bf").fill_null(0) > 0)
    result = (
        joined.with_columns(
            *[
                pl.when(is_complete)
                .then(pl.col(column).fill_null(0))
                .otherwise(None)
                .cast(pl.Int64)
                .alias(column)
                for column in (*BATTING_COUNT_COLUMNS, *PITCHING_COUNT_COLUMNS)
            ],
            pl.when(is_complete)
            .then(participated)
            .otherwise(None)
            .cast(pl.Boolean)
            .alias("any_mlb_participation"),
            (~is_complete).alias("is_right_censored"),
            pl.when(~is_complete)
            .then(pl.lit("right_censored"))
            .when(participated)
            .then(pl.lit("observed_participation"))
            .otherwise(pl.lit("observed_zero"))
            .alias("followup_status"),
            pl.lit(cohort_as_of_date).cast(pl.Date).alias("cohort_as_of_date"),
        )
        .select(list(CAREER_OUTCOME_SCHEMA))
        .cast(CAREER_OUTCOME_SCHEMA, strict=True)
        .sort(["player_id", "season"])
    )
    return validate_career_outcome_panel(result)


def validate_career_outcome_panel(frame: pl.DataFrame) -> pl.DataFrame:
    """Validate materialized follow-up semantics and exact panel grain."""

    missing = sorted(set(CAREER_OUTCOME_SCHEMA) - set(frame.columns))
    extra = sorted(set(frame.columns) - set(CAREER_OUTCOME_SCHEMA))
    if missing:
        raise ValueError(f"career_outcome_panel missing columns: {missing}")
    if extra:
        raise ValueError(f"career_outcome_panel has undeclared columns: {extra}")
    result = frame.select(list(CAREER_OUTCOME_SCHEMA)).cast(
        CAREER_OUTCOME_SCHEMA,
        strict=True,
    )
    if result.group_by(["cohort_as_of_date", "player_id", "season"]).len().filter(
        pl.col("len") > 1
    ).height:
        raise ValueError("career_outcome_panel violates cohort/player/season grain")
    if result.filter(~pl.col("followup_status").is_in(sorted(FOLLOWUP_STATUSES))).height:
        raise ValueError("career_outcome_panel has invalid followup_status")

    counts = [*BATTING_COUNT_COLUMNS, *PITCHING_COUNT_COLUMNS]
    censored = pl.col("is_right_censored")
    invalid_censored = result.filter(
        censored
        & (
            pl.col("any_mlb_participation").is_not_null()
            | pl.any_horizontal([pl.col(column).is_not_null() for column in counts])
            | (pl.col("followup_status") != "right_censored")
        )
    )
    if invalid_censored.height:
        raise ValueError("right-censored career rows must retain null outcomes")
    invalid_observed = result.filter(
        ~censored
        & (
            pl.col("any_mlb_participation").is_null()
            | pl.any_horizontal([pl.col(column).is_null() for column in counts])
            | (pl.col("followup_status") == "right_censored")
        )
    )
    if invalid_observed.height:
        raise ValueError("observed career rows require complete non-null outcomes")
    return result
