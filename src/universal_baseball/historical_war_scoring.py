"""Score frozen expected WAR against a like-for-like neutral realized proxy."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)


HITTER_EVENTS = ("ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_EVENTS = ("so", "ubb", "hbp", "hr", "other")


def _hitter_counts(source: pl.DataFrame) -> pl.DataFrame:
    required = {
        "player_id",
        "batting_plate_appearances",
        "batting_hits",
        "batting_doubles",
        "batting_triples",
        "batting_home_runs",
        "batting_base_on_balls",
        "batting_intentional_walks",
        "batting_hit_by_pitch",
    }
    if missing := sorted(required - set(source.columns)):
        raise ValueError(f"historical hitter WAR outcomes missing fields: {missing}")
    result = source.group_by("player_id").agg(
        *(
            pl.col(column).sum().alias(column)
            for column in sorted(required - {"player_id"})
        )
    ).with_columns(
        (
            pl.col("batting_base_on_balls")
            - pl.col("batting_intentional_walks")
        ).alias("ubb"),
        pl.col("batting_hit_by_pitch").alias("hbp"),
        (
            pl.col("batting_hits")
            - pl.col("batting_doubles")
            - pl.col("batting_triples")
            - pl.col("batting_home_runs")
        ).alias("single"),
        pl.col("batting_doubles").alias("double"),
        pl.col("batting_triples").alias("triple"),
        pl.col("batting_home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("batting_plate_appearances")
            - pl.sum_horizontal("ubb", "hbp", "single", "double", "triple", "hr")
        ).alias("other")
    )
    if result.filter(
        pl.any_horizontal(*(pl.col(event) < 0 for event in HITTER_EVENTS))
    ).height:
        raise ValueError("historical hitter WAR event accounting is invalid")
    return result


def _pitcher_counts(source: pl.DataFrame) -> pl.DataFrame:
    required = {
        "player_id",
        "pitching_batters_faced",
        "pitching_strike_outs",
        "pitching_base_on_balls",
        "pitching_intentional_walks",
        "pitching_hit_batsmen",
        "pitching_home_runs",
    }
    if missing := sorted(required - set(source.columns)):
        raise ValueError(f"historical pitcher WAR outcomes missing fields: {missing}")
    result = source.group_by("player_id").agg(
        *(
            pl.col(column).sum().alias(column)
            for column in sorted(required - {"player_id"})
        )
    ).with_columns(
        pl.col("pitching_strike_outs").alias("so"),
        (
            pl.col("pitching_base_on_balls")
            - pl.col("pitching_intentional_walks")
        ).alias("ubb"),
        pl.col("pitching_hit_batsmen").alias("hbp"),
        pl.col("pitching_home_runs").alias("hr"),
    ).with_columns(
        (
            pl.col("pitching_batters_faced")
            - pl.sum_horizontal("so", "ubb", "hbp", "hr")
        ).alias("other")
    )
    if result.filter(
        pl.any_horizontal(*(pl.col(event) < 0 for event in PITCHER_EVENTS))
    ).height:
        raise ValueError("historical pitcher WAR event accounting is invalid")
    return result


def _probabilities(
    counts: pl.DataFrame, *, workload_column: str, events: tuple[str, ...]
) -> dict[str, float]:
    total = float(counts.get_column(workload_column).sum())
    if total <= 0:
        raise ValueError("historical WAR reference workload must be positive")
    return {event: float(counts.get_column(event).sum()) / total for event in events}


def _summary(
    scored: pl.DataFrame,
    *,
    workload_column: str,
    events: tuple[str, ...],
    population_probabilities: dict[str, float],
) -> dict[str, float | int]:
    error = scored.get_column("war_error")
    event_count = 0.0
    model_log_loss = 0.0
    population_log_loss = 0.0
    for row in scored.iter_rows(named=True):
        for event in events:
            count = float(row[event])
            event_count += count
            model_log_loss -= count * math.log(
                max(float(row[f"predicted_{event}_rate"]), 1e-12)
            )
            population_log_loss -= count * math.log(
                max(float(population_probabilities[event]), 1e-12)
            )
    return {
        "players": scored.height,
        "positive_workload_players": scored.filter(
            pl.col(workload_column) > 0
        ).height,
        "observed_total_workload": float(scored.get_column(workload_column).sum()),
        "predicted_total_war": float(scored.get_column("expected_war").sum()),
        "observed_total_neutral_war": float(
            scored.get_column("observed_neutral_war").sum()
        ),
        "war_mae": float(error.abs().mean()),
        "war_rmse": math.sqrt(float((error * error).mean())),
        "component_events": int(event_count),
        "model_component_log_loss": model_log_loss / event_count,
        "population_component_log_loss": population_log_loss / event_count,
        "model_minus_population_component_log_loss": (
            model_log_loss - population_log_loss
        )
        / event_count,
    }


def score_hitter_neutral_war(
    projections: pl.DataFrame,
    outcomes: pl.DataFrame,
    reference: pl.DataFrame,
    *,
    runs_per_win: float,
) -> tuple[pl.DataFrame, dict[str, float | int]]:
    """Score hitter WAR using the projection's neutral component definition."""

    required = {
        "player_id",
        "expected_war",
        "positional_runs_per_600",
        "replacement_runs_per_600",
        *(f"predicted_{event}_rate" for event in HITTER_EVENTS),
    }
    if missing := sorted(required - set(projections.columns)):
        raise ValueError(f"historical hitter WAR projections missing fields: {missing}")
    actual = _hitter_counts(outcomes)
    reference_counts = _hitter_counts(reference)
    prior = _probabilities(
        reference_counts,
        workload_column="batting_plate_appearances",
        events=HITTER_EVENTS,
    )
    weights = {
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "single": NEUTRAL_WOBA_WEIGHTS["1B"],
        "double": NEUTRAL_WOBA_WEIGHTS["2B"],
        "triple": NEUTRAL_WOBA_WEIGHTS["3B"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": 0.0,
    }
    reference_woba = sum(prior[event] * weights[event] for event in HITTER_EVENTS)
    source = projections.select(*sorted(required)).join(
        actual, on="player_id", how="left", validate="1:1"
    ).with_columns(
        pl.col("batting_plate_appearances").fill_null(0),
        *(pl.col(event).fill_null(0) for event in HITTER_EVENTS),
    )
    rows = []
    for row in source.iter_rows(named=True):
        workload = float(row["batting_plate_appearances"])
        if workload > 0:
            actual_woba = sum(
                float(row[event]) * weights[event] for event in HITTER_EVENTS
            ) / workload
            batting_runs_per_600 = (
                (actual_woba - reference_woba) * 600.0 / NEUTRAL_WOBA_SCALE
            )
            actual_war = workload / 600.0 * (
                batting_runs_per_600
                + float(row["positional_runs_per_600"])
                + float(row["replacement_runs_per_600"])
            ) / runs_per_win
        else:
            actual_war = 0.0
        rows.append(
            {
                **row,
                "observed_neutral_war": actual_war,
                "war_error": float(row["expected_war"]) - actual_war,
            }
        )
    scored = pl.DataFrame(rows).sort("player_id")
    return scored, _summary(
        scored,
        workload_column="batting_plate_appearances",
        events=HITTER_EVENTS,
        population_probabilities=prior,
    )


def score_pitcher_neutral_war(
    projections: pl.DataFrame,
    outcomes: pl.DataFrame,
    reference: pl.DataFrame,
    *,
    runs_per_win: float,
) -> tuple[pl.DataFrame, dict[str, float | int]]:
    """Score pitcher WAR using the projection's neutral component definition."""

    required = {
        "player_id",
        "expected_war",
        "replacement_runs_per_800",
        *(f"predicted_{event}_rate" for event in PITCHER_EVENTS),
    }
    if missing := sorted(required - set(projections.columns)):
        raise ValueError(f"historical pitcher WAR projections missing fields: {missing}")
    actual = _pitcher_counts(outcomes)
    reference_counts = _pitcher_counts(reference)
    prior = _probabilities(
        reference_counts,
        workload_column="pitching_batters_faced",
        events=PITCHER_EVENTS,
    )
    known_weight_sum = (
        prior["ubb"] * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + prior["hbp"] * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + prior["hr"] * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    other_weight = (0.3188 - known_weight_sum) / prior["other"]
    weights = {
        "so": 0.0,
        "ubb": NEUTRAL_WOBA_WEIGHTS["UBB"],
        "hbp": NEUTRAL_WOBA_WEIGHTS["HBP"],
        "hr": NEUTRAL_WOBA_WEIGHTS["HR"],
        "other": other_weight,
    }
    source = projections.select(*sorted(required)).join(
        actual, on="player_id", how="left", validate="1:1"
    ).with_columns(
        pl.col("pitching_batters_faced").fill_null(0),
        *(pl.col(event).fill_null(0) for event in PITCHER_EVENTS),
    )
    rows = []
    for row in source.iter_rows(named=True):
        workload = float(row["pitching_batters_faced"])
        if workload > 0:
            actual_woba = sum(
                float(row[event]) * weights[event] for event in PITCHER_EVENTS
            ) / workload
            runs_above_per_800 = (
                -(actual_woba - 0.3188) * 800.0 / NEUTRAL_WOBA_SCALE
            )
            actual_war = workload / 800.0 * (
                runs_above_per_800 + float(row["replacement_runs_per_800"])
            ) / runs_per_win
        else:
            actual_war = 0.0
        rows.append(
            {
                **row,
                "observed_neutral_war": actual_war,
                "war_error": float(row["expected_war"]) - actual_war,
            }
        )
    scored = pl.DataFrame(rows).sort("player_id")
    return scored, _summary(
        scored,
        workload_column="pitching_batters_faced",
        events=PITCHER_EVENTS,
        population_probabilities=prior,
    )


def whole_player_war_metrics(
    hitter_scores: pl.DataFrame, pitcher_scores: pl.DataFrame
) -> tuple[pl.DataFrame, dict[str, float | int]]:
    """Combine two-way components and score one expected WAR row per player."""

    combined = (
        pl.concat(
            [
                frame.select("player_id", "expected_war", "observed_neutral_war")
                for frame in (hitter_scores, pitcher_scores)
            ]
        )
        .group_by("player_id")
        .agg(
            pl.col("expected_war").sum(),
            pl.col("observed_neutral_war").sum(),
        )
        .with_columns(
            (pl.col("expected_war") - pl.col("observed_neutral_war")).alias(
                "war_error"
            )
        )
        .sort("player_id")
    )
    error = combined.get_column("war_error")
    return combined, {
        "players": combined.height,
        "predicted_total_war": float(combined.get_column("expected_war").sum()),
        "observed_total_neutral_war": float(
            combined.get_column("observed_neutral_war").sum()
        ),
        "war_mae": float(error.abs().mean()),
        "war_rmse": math.sqrt(float((error * error).mean())),
    }
