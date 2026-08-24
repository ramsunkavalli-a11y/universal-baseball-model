"""Chronology-safe adjustment primitives for the Hitter v2 C1 model.

This module contains estimator machinery only.  It deliberately has no target
loader, validation scorer, ranking code, or tracking-data dependency.
"""

from __future__ import annotations

from math import exp, isfinite, log
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_model import nested_empirical_bayes_probabilities
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


PROBABILITY_FLOOR = 1e-12
MLB_LEVEL = "MLB"
NON_REACH_OUTCOMES = ("SF", "MULTI_OUT", "OTHER_OUT")
AGE_KNOTS = (20.0, 24.0, 28.0, 32.0)


@dataclass(frozen=True, slots=True)
class C1AdjustmentFit:
    park_offsets: pl.DataFrame
    player_park_exposure: pl.DataFrame
    player_season_park_exposure: pl.DataFrame
    player_seasons: pl.DataFrame
    movement_observations: pl.DataFrame
    first_pass_level_offsets: pl.DataFrame
    age_coefficients: pl.DataFrame
    final_level_offsets: pl.DataFrame
    age_fit_fallback_reason: str | None


def _check_cutoff(frame: pl.DataFrame, predictor_cutoff_season: int) -> None:
    if "season" not in frame.columns:
        raise ValueError("chronology-checked input is missing season")
    if frame.filter(pl.col("season") > predictor_cutoff_season).height:
        raise ValueError("input contains rows after the predictor cutoff")


def apply_log_probability_offsets(
    probabilities: Mapping[str, float],
    offsets: Mapping[str, float],
) -> dict[str, float]:
    """Apply additive log-probability offsets and normalize with softmax."""

    validate_probability_vector(probabilities, tolerance=1e-10)
    unknown = sorted(set(offsets) - set(HITTER_TALENT_OUTCOMES))
    if unknown:
        raise ValueError(f"offsets contain unknown terminal outcomes: {unknown}")
    normalized_offsets = {
        outcome: float(offsets.get(outcome, 0.0))
        for outcome in HITTER_TALENT_OUTCOMES
    }
    if all(value == 0.0 for value in normalized_offsets.values()):
        return {outcome: float(probabilities[outcome]) for outcome in HITTER_TALENT_OUTCOMES}
    logits: dict[str, float] = {}
    for outcome in HITTER_TALENT_OUTCOMES:
        offset = normalized_offsets[outcome]
        if not isfinite(offset):
            raise ValueError("probability offsets must be finite")
        probability = float(probabilities[outcome])
        logits[outcome] = log(max(probability, PROBABILITY_FLOOR)) + offset
    maximum = max(logits.values())
    weights = {outcome: exp(value - maximum) for outcome, value in logits.items()}
    denominator = sum(weights.values())
    result = {outcome: value / denominator for outcome, value in weights.items()}
    validate_probability_vector(result, tolerance=1e-10)
    return result


def estimate_visitor_park_offsets(
    player_games: pl.DataFrame,
    park_context: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    prior_pa: float,
) -> pl.DataFrame:
    """Estimate pooled venue effects from accepted visiting-hitter outcomes."""

    if not isfinite(prior_pa) or prior_pa <= 0.0:
        raise ValueError("park prior PA must be finite and positive")
    _check_cutoff(player_games, predictor_cutoff_season)
    _check_cutoff(park_context, predictor_cutoff_season)
    keys = ["season", "game_id", "team_id", "player_id"]
    required_games = {
        *keys,
        "league_id",
        "level_group",
        "hitter_talent_pa",
        *HITTER_TALENT_OUTCOMES,
    }
    required_park = {
        *keys,
        "venue_id",
        "away_team_id",
        "venue_context_eligible",
    }
    for label, frame, required in (
        ("player-game", player_games, required_games),
        ("park", park_context, required_park),
    ):
        missing = sorted(required - set(frame.columns))
        if missing:
            raise ValueError(f"{label} input missing columns: {missing}")
    duplicate_context = park_context.group_by(keys).len().filter(pl.col("len") != 1)
    if duplicate_context.height:
        raise ValueError("park context is not unique at the canonical player-game grain")

    visitors = (
        player_games.join(
            park_context.select(
                *keys, "venue_id", "away_team_id", "venue_context_eligible"
            ),
            on=keys,
            how="inner",
            validate="1:1",
        )
        .filter(
            pl.col("venue_context_eligible")
            & (pl.col("team_id") == pl.col("away_team_id"))
            & (pl.col("hitter_talent_pa") > 0)
        )
    )
    if visitors.is_empty():
        raise ValueError("no accepted visiting-hitter park evidence")
    group = ["season", "league_id", "level_group"]
    reference = visitors.group_by(group).agg(
        pl.col("hitter_talent_pa").sum().alias("reference_pa"),
        *[
            pl.col(outcome).sum().alias(f"reference_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ],
    )
    venue = visitors.group_by([*group, "venue_id"]).agg(
        pl.col("hitter_talent_pa").sum().alias("venue_pa"),
        *[pl.col(outcome).sum().alias(outcome) for outcome in HITTER_TALENT_OUTCOMES],
    )
    joined = venue.join(reference, on=group, how="left", validate="m:1")
    rows: list[dict[str, object]] = []
    for row in joined.sort([*group, "venue_id"]).iter_rows(named=True):
        reference_pa = float(row["reference_pa"])
        venue_pa = float(row["venue_pa"])
        offsets: dict[str, float] = {}
        for outcome in HITTER_TALENT_OUTCOMES:
            reference_probability = float(row[f"reference_{outcome}"]) / reference_pa
            if reference_probability <= 0.0:
                offsets[outcome] = 0.0
                continue
            pooled_probability = (
                float(row[outcome]) + prior_pa * reference_probability
            ) / (venue_pa + prior_pa)
            offsets[outcome] = log(
                max(pooled_probability, PROBABILITY_FLOOR)
                / reference_probability
            )
        rows.append(
            {
                **{column: row[column] for column in group},
                "venue_id": row["venue_id"],
                "venue_pa": venue_pa,
                "park_prior_pa": float(prior_pa),
                **{
                    f"park_log_offset_{outcome}": offsets[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def aggregate_player_park_exposure(
    player_games: pl.DataFrame,
    park_context: pl.DataFrame,
    park_offsets: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    by_season: bool = False,
) -> pl.DataFrame:
    """Return observed-PA-weighted venue offsets for each player history."""

    _check_cutoff(player_games, predictor_cutoff_season)
    _check_cutoff(park_context, predictor_cutoff_season)
    _check_cutoff(park_offsets, predictor_cutoff_season)
    keys = ["season", "game_id", "team_id", "player_id"]
    offset_keys = ["season", "league_id", "level_group", "venue_id"]
    offset_columns = [
        f"park_log_offset_{outcome}" for outcome in HITTER_TALENT_OUTCOMES
    ]
    joined = (
        player_games.select(
            *keys, "league_id", "level_group", "hitter_talent_pa"
        )
        .join(
            park_context.select(*keys, "venue_id", "venue_context_eligible"),
            on=keys,
            how="left",
            validate="1:1",
        )
        .join(
            park_offsets.select(*offset_keys, *offset_columns),
            on=offset_keys,
            how="left",
            validate="m:1",
        )
        .filter(
            pl.col("venue_context_eligible").fill_null(False)
            & pl.col("park_log_offset_K").is_not_null()
            & (pl.col("hitter_talent_pa") > 0)
        )
    )
    grouping = ["player_id"] if not by_season else ["player_id", "season"]
    if joined.is_empty():
        return pl.DataFrame(
            schema={
                **{column: pl.Int64 for column in grouping},
                "park_evidence_pa": pl.Float64,
                **{column: pl.Float64 for column in offset_columns},
            }
        )
    return (
        joined.group_by(grouping)
        .agg(
            pl.col("hitter_talent_pa").sum().cast(pl.Float64).alias("park_evidence_pa"),
            *[
                (
                    (pl.col(column) * pl.col("hitter_talent_pa")).sum()
                    / pl.col("hitter_talent_pa").sum()
                ).alias(column)
                for column in offset_columns
            ],
        )
        .sort(grouping)
    )


def estimate_player_season_probabilities(
    training: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    component_prior_pa: float,
) -> pl.DataFrame:
    """Estimate pooled terminal simplexes at the player-season grain."""

    _check_cutoff(training, predictor_cutoff_season)
    if not isfinite(component_prior_pa) or component_prior_pa <= 0.0:
        raise ValueError("component prior PA must be finite and positive")
    required = {
        "player_id",
        "season",
        "league_id",
        "level_group",
        "hitter_talent_pa",
        *HITTER_TALENT_OUTCOMES,
    }
    missing = sorted(required - set(training.columns))
    if missing:
        raise ValueError(f"training missing player-season columns: {missing}")
    accepted = training.filter(pl.col("hitter_talent_pa") > 0)
    if accepted.is_empty():
        raise ValueError("no accepted player-season evidence")
    context_totals = accepted.group_by(
        ["season", "league_id", "level_group"]
    ).agg(*[pl.col(outcome).sum().alias(outcome) for outcome in HITTER_TALENT_OUTCOMES])
    context_map = {
        (int(row["season"]), int(row["league_id"]), str(row["level_group"])): {
            outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES
        }
        for row in context_totals.iter_rows(named=True)
    }
    primary = (
        accepted.group_by(["player_id", "season", "league_id", "level_group"])
        .agg(pl.col("hitter_talent_pa").sum().alias("context_pa"))
        .sort(
            ["player_id", "season", "context_pa", "league_id", "level_group"],
            descending=[False, False, True, False, False],
        )
        .unique(["player_id", "season"], keep="first", maintain_order=True)
    )
    totals = accepted.group_by(["player_id", "season"]).agg(
        pl.col("hitter_talent_pa").sum().alias("hitter_talent_pa"),
        *[pl.col(outcome).sum().alias(outcome) for outcome in HITTER_TALENT_OUTCOMES],
    )
    joined = totals.join(
        primary.select("player_id", "season", "league_id", "level_group"),
        on=["player_id", "season"],
        how="left",
        validate="1:1",
    )
    priors = {name: float(component_prior_pa) for name in (
        "plate_appearance",
        "non_k",
        "non_k_non_ubb",
        "contact",
        "non_hr_contact",
        "reach",
        "hit_in_play",
        "non_hit_reach",
        "non_reach",
    )}
    rows: list[dict[str, object]] = []
    for row in joined.sort(["player_id", "season"]).iter_rows(named=True):
        counts = {outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES}
        key = (int(row["season"]), int(row["league_id"]), str(row["level_group"]))
        probabilities = nested_empirical_bayes_probabilities(
            counts,
            context_map[key],
            component_prior_pa=priors,
        )
        rows.append(
            {
                "player_id": int(row["player_id"]),
                "season": int(row["season"]),
                "league_id": int(row["league_id"]),
                "level_group": str(row["level_group"]),
                "hitter_talent_pa": float(row["hitter_talent_pa"]),
                **{
                    f"p_{outcome}": probabilities[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def neutralize_player_season_parks(
    player_seasons: pl.DataFrame,
    park_exposure: pl.DataFrame,
) -> pl.DataFrame:
    """Subtract each season's observed park mix from its terminal simplex."""

    require_probability_columns(player_seasons)
    offset_columns = [
        f"park_log_offset_{outcome}" for outcome in HITTER_TALENT_OUTCOMES
    ]
    joined = player_seasons.join(
        park_exposure.select("player_id", "season", "park_evidence_pa", *offset_columns),
        on=["player_id", "season"],
        how="left",
        validate="1:1",
    )
    rows: list[dict[str, object]] = []
    for row in joined.iter_rows(named=True):
        probabilities = prediction_probability(row)
        observed_offsets = terminal_offsets_from_row(
            row, prefix="park_log_offset_", multiplier=-1.0
        )
        neutral = apply_log_probability_offsets(probabilities, observed_offsets)
        rows.append(
            {
                **row,
                "park_adjustment_fallback": (
                    "missing_park_context" if row["park_evidence_pa"] is None else None
                ),
                **{
                    f"neutral_p_{outcome}": neutral[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def relative_age_basis(relative_age: float) -> np.ndarray:
    """Return the continuous piecewise-linear absolute-age hinge basis."""

    value = float(relative_age)
    if not isfinite(value):
        raise ValueError("relative age must be finite")
    return np.asarray([value, *[max(value - knot, 0.0) for knot in AGE_KNOTS]])


def centered_age_basis(age_years: float, context_median_age: float) -> np.ndarray:
    """Center the absolute-age hinge basis on its chronology-safe context."""

    return relative_age_basis(age_years) - relative_age_basis(context_median_age)


def attach_relative_ages(
    player_seasons: pl.DataFrame,
    historical_ages: pl.DataFrame,
) -> pl.DataFrame:
    """Attach July 1 age relative to the league-season-level median."""

    required = {"player_id", "season", "age_years"}
    missing = sorted(required - set(historical_ages.columns))
    if missing:
        raise ValueError(f"historical ages missing columns: {missing}")
    joined = player_seasons.join(
        historical_ages.select("player_id", "season", "age_years"),
        on=["player_id", "season"],
        how="left",
        validate="1:1",
    )
    medians = joined.group_by(["season", "league_id", "level_group"]).agg(
        pl.col("age_years").median().alias("context_median_age")
    )
    return joined.join(
        medians,
        on=["season", "league_id", "level_group"],
        how="left",
        validate="m:1",
    ).with_columns(
        (pl.col("age_years") - pl.col("context_median_age")).alias("relative_age")
    )


def build_adjacent_movement_observations(
    player_seasons: pl.DataFrame,
    *,
    probability_prefix: str = "neutral_p_",
) -> pl.DataFrame:
    """Build same-player consecutive-season component residuals."""

    required = {
        "player_id",
        "season",
        "level_group",
        "hitter_talent_pa",
        *[f"{probability_prefix}{outcome}" for outcome in HITTER_TALENT_OUTCOMES],
    }
    missing = sorted(required - set(player_seasons.columns))
    if missing:
        raise ValueError(f"player seasons missing movement columns: {missing}")
    lookup = {
        (int(row["player_id"]), int(row["season"])): row
        for row in player_seasons.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for (player_id, season), source in sorted(lookup.items()):
        destination = lookup.get((player_id, season + 1))
        if destination is None:
            continue
        row: dict[str, object] = {
            "player_id": player_id,
            "source_season": season,
            "destination_season": season + 1,
            "source_level": str(source["level_group"]),
            "destination_level": str(destination["level_group"]),
            "pair_weight": min(
                float(source["hitter_talent_pa"]),
                float(destination["hitter_talent_pa"]),
            ),
        }
        for column in ("relative_age",):
            row[f"source_{column}"] = source.get(column)
            row[f"destination_{column}"] = destination.get(column)
        for column in ("age_years", "context_median_age"):
            row[f"source_{column}"] = source.get(column)
            row[f"destination_{column}"] = destination.get(column)
        for outcome in HITTER_TALENT_OUTCOMES:
            source_probability = max(
                float(source[f"{probability_prefix}{outcome}"]), PROBABILITY_FLOOR
            )
            destination_probability = max(
                float(destination[f"{probability_prefix}{outcome}"]), PROBABILITY_FLOOR
            )
            row[f"delta_{outcome}"] = log(destination_probability) - log(
                source_probability
            )
        rows.append(row)
    if not rows:
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "source_season": pl.Int64,
                "destination_season": pl.Int64,
                "source_level": pl.String,
                "destination_level": pl.String,
                "pair_weight": pl.Float64,
                "source_relative_age": pl.Float64,
                "destination_relative_age": pl.Float64,
                "source_age_years": pl.Float64,
                "destination_age_years": pl.Float64,
                "source_context_median_age": pl.Float64,
                "destination_context_median_age": pl.Float64,
                **{
                    f"delta_{outcome}": pl.Float64
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows)


def fit_ridge_age_offsets(
    movement_observations: pl.DataFrame,
    level_offsets: pl.DataFrame,
    *,
    ridge_penalty: float,
) -> pl.DataFrame:
    """Fit component age curves after subtracting first-pass movement effects."""

    if not isfinite(ridge_penalty) or ridge_penalty <= 0.0:
        raise ValueError("age ridge penalty must be finite and positive")
    usable = movement_observations.filter(
        pl.col("source_age_years").is_not_null()
        & pl.col("destination_age_years").is_not_null()
        & pl.col("source_context_median_age").is_not_null()
        & pl.col("destination_context_median_age").is_not_null()
        & (pl.col("pair_weight") > 0)
    )
    if usable.is_empty():
        raise ValueError("no adjacent movement rows have complete ages")
    level_map = {
        str(row["level_group"]): row for row in level_offsets.iter_rows(named=True)
    }
    design: list[np.ndarray] = []
    weights: list[float] = []
    rows = list(usable.iter_rows(named=True))
    for row in rows:
        design.append(
            centered_age_basis(
                float(row["destination_age_years"]),
                float(row["destination_context_median_age"]),
            )
            - centered_age_basis(
                float(row["source_age_years"]),
                float(row["source_context_median_age"]),
            )
        )
        weights.append(float(row["pair_weight"]))
    matrix = np.vstack(design)
    weight = np.asarray(weights, dtype=float)
    gram = matrix.T @ (weight[:, None] * matrix)
    penalized = gram + ridge_penalty * np.eye(matrix.shape[1])
    coefficient_rows: list[dict[str, object]] = []
    for outcome in HITTER_TALENT_OUTCOMES:
        response_values = []
        for row in rows:
            source = level_map.get(str(row["source_level"]))
            destination = level_map.get(str(row["destination_level"]))
            source_offset = (
                0.0 if source is None else float(source[f"level_log_offset_{outcome}"])
            )
            destination_offset = (
                0.0
                if destination is None
                else float(destination[f"level_log_offset_{outcome}"])
            )
            response_values.append(
                float(row[f"delta_{outcome}"])
                - (destination_offset - source_offset)
            )
        response = np.asarray(response_values, dtype=float)
        coefficients = np.linalg.solve(penalized, matrix.T @ (weight * response))
        coefficient_rows.append(
            {
                "outcome": outcome,
                "ridge_penalty": float(ridge_penalty),
                "age_pair_count": len(rows),
                "age_pair_weight": float(weight.sum()),
                **{
                    f"coefficient_{index}": float(value)
                    for index, value in enumerate(coefficients)
                },
            }
        )
    return pl.DataFrame(coefficient_rows)


def age_change_offsets(
    target_age_context: tuple[float, float] | None,
    age_coefficients: pl.DataFrame,
) -> tuple[dict[str, float], str | None]:
    """Evaluate the centered absolute-age basis change into target year."""

    if target_age_context is None:
        return (
            {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES},
            "missing_age",
        )
    target_age, cutoff_context_median = map(float, target_age_context)
    change = centered_age_basis(
        target_age, cutoff_context_median + 1.0
    ) - centered_age_basis(
        target_age - 1.0, cutoff_context_median
    )
    by_outcome = {
        str(row["outcome"]): row for row in age_coefficients.iter_rows(named=True)
    }
    return (
        {
            outcome: float(
                sum(
                    float(by_outcome[outcome][f"coefficient_{index}"]) * value
                    for index, value in enumerate(change)
                )
            )
            for outcome in HITTER_TALENT_OUTCOMES
        },
        None,
    )


def zero_age_coefficients(*, ridge_penalty: float) -> pl.DataFrame:
    """Return an explicit neutral age surface when chronology has no pairs."""

    return pl.DataFrame(
        [
            {
                "outcome": outcome,
                "ridge_penalty": float(ridge_penalty),
                "age_pair_count": 0,
                "age_pair_weight": 0.0,
                **{f"coefficient_{index}": 0.0 for index in range(5)},
            }
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
def remove_age_from_movement_observations(
    movement_observations: pl.DataFrame,
    age_coefficients: pl.DataFrame,
) -> pl.DataFrame:
    """Remove fitted adjacent-season age changes before movement refit."""

    coefficient_map = {
        str(row["outcome"]): np.asarray(
            [float(row[f"coefficient_{index}"]) for index in range(5)]
        )
        for row in age_coefficients.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for row in movement_observations.iter_rows(named=True):
        source_age = row.get("source_age_years")
        destination_age = row.get("destination_age_years")
        source_median = row.get("source_context_median_age")
        destination_median = row.get("destination_context_median_age")
        basis_change = None
        if all(
            value is not None
            for value in (source_age, destination_age, source_median, destination_median)
        ):
            basis_change = centered_age_basis(
                float(destination_age), float(destination_median)
            ) - centered_age_basis(
                float(source_age), float(source_median)
            )
        adjusted = dict(row)
        for outcome in HITTER_TALENT_OUTCOMES:
            fitted = (
                0.0
                if basis_change is None
                else float(coefficient_map[outcome] @ basis_change)
            )
            adjusted[f"delta_{outcome}"] = float(row[f"delta_{outcome}"]) - fitted
        rows.append(adjusted)
    return pl.DataFrame(rows)


def solve_level_offsets(
    movement_observations: pl.DataFrame,
    *,
    prior_mover_pa: float,
    anchor_level: str = MLB_LEVEL,
) -> pl.DataFrame:
    """Solve component level effects from directed movement residuals."""

    if not isfinite(prior_mover_pa) or prior_mover_pa <= 0.0:
        raise ValueError("movement prior PA must be finite and positive")
    required = {
        "source_level",
        "destination_level",
        "pair_weight",
        *[f"delta_{outcome}" for outcome in HITTER_TALENT_OUTCOMES],
    }
    missing = sorted(required - set(movement_observations.columns))
    if missing:
        raise ValueError(f"movement observations missing columns: {missing}")
    observations = movement_observations.filter(
        (pl.col("pair_weight") > 0)
        & (pl.col("source_level") != pl.col("destination_level"))
    )
    levels = sorted(
        {
            str(value)
            for column in ("source_level", "destination_level")
            for value in observations[column].to_list()
        }
        | {anchor_level}
    )
    unknown_levels = [level for level in levels if level != anchor_level]
    if observations.is_empty() or not unknown_levels:
        return pl.DataFrame(
            [
                {
                    "level_group": anchor_level,
                    "translation_connected_to_mlb": True,
                    **{
                        f"level_log_offset_{outcome}": 0.0
                        for outcome in HITTER_TALENT_OUTCOMES
                    },
                }
            ]
        )

    pair_groups = observations.group_by(
        ["source_level", "destination_level"]
    ).agg(
        pl.col("pair_weight").sum().alias("mover_pa"),
        *[
            (
                (pl.col(f"delta_{outcome}") * pl.col("pair_weight")).sum()
                / pl.col("pair_weight").sum()
            ).alias(f"delta_{outcome}")
            for outcome in HITTER_TALENT_OUTCOMES
        ],
    )
    index = {level: position for position, level in enumerate(unknown_levels)}
    design_rows: list[list[float]] = []
    weights: list[float] = []
    pair_rows = pair_groups.iter_rows(named=True)
    cached_rows = list(pair_rows)
    for row in cached_rows:
        design = [0.0] * len(unknown_levels)
        source = str(row["source_level"])
        destination = str(row["destination_level"])
        if source != anchor_level:
            design[index[source]] -= 1.0
        if destination != anchor_level:
            design[index[destination]] += 1.0
        design_rows.append(design)
        weights.append(float(row["mover_pa"]))
    design_matrix = np.asarray(design_rows, dtype=float)
    sqrt_weight = np.sqrt(np.asarray(weights, dtype=float))

    adjacency: dict[str, set[str]] = {level: set() for level in levels}
    for row in cached_rows:
        source = str(row["source_level"])
        destination = str(row["destination_level"])
        adjacency[source].add(destination)
        adjacency[destination].add(source)
    connected = {anchor_level}
    frontier = [anchor_level]
    while frontier:
        level = frontier.pop()
        for neighbor in adjacency[level] - connected:
            connected.add(neighbor)
            frontier.append(neighbor)

    solved = {
        level: {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
        for level in levels
    }
    for outcome in HITTER_TALENT_OUTCOMES:
        response = np.asarray(
            [
                float(row[f"delta_{outcome}"])
                * float(row["mover_pa"])
                / (float(row["mover_pa"]) + prior_mover_pa)
                for row in cached_rows
            ],
            dtype=float,
        )
        coefficients = np.linalg.lstsq(
            design_matrix * sqrt_weight[:, None],
            response * sqrt_weight,
            rcond=None,
        )[0]
        for level, position in index.items():
            solved[level][outcome] = float(coefficients[position])

    return pl.DataFrame(
        [
            {
                "level_group": level,
                "translation_connected_to_mlb": level in connected,
                **{
                    f"level_log_offset_{outcome}": (
                        solved[level][outcome] if level in connected else 0.0
                    )
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
            for level in levels
        ]
    ).sort("level_group")


def adjust_multi_out_for_gidp(
    probabilities: Mapping[str, float],
    *,
    opportunity_rate: float | None,
    conversion_rate: float | None,
    non_gidp_multi_out_rate: float | None,
) -> tuple[dict[str, float], str | None]:
    """Replace MULTI_OUT mass while preserving upstream and reach branches."""

    validate_probability_vector(probabilities, tolerance=1e-10)
    values = (opportunity_rate, conversion_rate, non_gidp_multi_out_rate)
    if any(value is None for value in values):
        return dict(probabilities), "missing_gidp_opportunity_evidence"
    numeric = tuple(float(value) for value in values)
    if any(not isfinite(value) or value < 0.0 for value in numeric):
        raise ValueError("GIDP component rates must be finite and nonnegative")
    opportunity, conversion, residual = numeric
    if opportunity > 1.0 or conversion > 1.0 or residual > 1.0:
        raise ValueError("GIDP component rates cannot exceed one")
    target_multi_out = opportunity * conversion + residual
    non_reach_total = sum(float(probabilities[outcome]) for outcome in NON_REACH_OUTCOMES)
    if target_multi_out < 0.0 or target_multi_out > non_reach_total:
        raise ValueError("adjusted MULTI_OUT mass exceeds the non-reach out branch")
    other_out_mass = non_reach_total - float(probabilities["MULTI_OUT"])
    remaining = non_reach_total - target_multi_out
    result = dict(probabilities)
    result["MULTI_OUT"] = target_multi_out
    if other_out_mass <= 0.0:
        result["SF"] = 0.0
        result["OTHER_OUT"] = remaining
    else:
        scale = remaining / other_out_mass
        result["SF"] = float(probabilities["SF"]) * scale
        result["OTHER_OUT"] = float(probabilities["OTHER_OUT"]) * scale
    validate_probability_vector(result, tolerance=1e-10)
    return result, None


def estimate_player_gidp_rates(
    gidp_history: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    half_life_seasons: float,
    prior_pa: float,
) -> pl.DataFrame:
    """Estimate opportunity, conversion, and residual multi-out components."""

    _check_cutoff(gidp_history, predictor_cutoff_season)
    if not isfinite(half_life_seasons) or half_life_seasons <= 0.0:
        raise ValueError("GIDP half-life must be finite and positive")
    if not isfinite(prior_pa) or prior_pa <= 0.0:
        raise ValueError("GIDP prior PA must be finite and positive")
    required = {
        "player_id",
        "season",
        "gidp_opportunities",
        "batting_GiDP",
        "MULTI_OUT",
        "accepted_terminal_pa",
        "gidp_opportunity_modeling_eligible",
    }
    missing = sorted(required - set(gidp_history.columns))
    if missing:
        raise ValueError(f"GIDP history missing columns: {missing}")
    eligible = gidp_history.filter(
        pl.col("gidp_opportunity_modeling_eligible")
        & (pl.col("accepted_terminal_pa") > 0)
    ).with_columns(
        (
            0.5
            ** (
                (pl.lit(predictor_cutoff_season) - pl.col("season"))
                / pl.lit(float(half_life_seasons))
            )
        ).alias("recency_weight"),
        (pl.col("MULTI_OUT") - pl.col("batting_GiDP"))
        .clip(lower_bound=0)
        .alias("non_gidp_multi_out"),
    )
    if eligible.is_empty():
        raise ValueError("no eligible GIDP opportunity history")
    totals = eligible.select(
        pl.col("accepted_terminal_pa").sum().alias("pa"),
        pl.col("gidp_opportunities").sum().alias("opportunities"),
        pl.col("batting_GiDP").sum().alias("gidp"),
        pl.col("non_gidp_multi_out").sum().alias("residual"),
    ).row(0, named=True)
    total_pa = float(totals["pa"])
    total_opportunities = float(totals["opportunities"])
    population_opportunity_rate = total_opportunities / total_pa
    population_conversion_rate = (
        float(totals["gidp"]) / total_opportunities
        if total_opportunities > 0.0
        else 0.0
    )
    population_residual_rate = float(totals["residual"]) / total_pa
    prior_opportunities = prior_pa * population_opportunity_rate
    aggregates = eligible.group_by("player_id").agg(
        (pl.col("accepted_terminal_pa") * pl.col("recency_weight"))
        .sum()
        .alias("gidp_evidence_pa"),
        (pl.col("gidp_opportunities") * pl.col("recency_weight"))
        .sum()
        .alias("gidp_evidence_opportunities"),
        (pl.col("batting_GiDP") * pl.col("recency_weight"))
        .sum()
        .alias("gidp_evidence_events"),
        (pl.col("non_gidp_multi_out") * pl.col("recency_weight"))
        .sum()
        .alias("non_gidp_multi_out_events"),
    )
    by_player = {
        int(row["player_id"]): row for row in aggregates.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for player_id in ensure_unique_ids(player_ids):
        evidence = by_player.get(player_id)
        if evidence is None:
            rows.append(
                {
                    "player_id": player_id,
                    "gidp_evidence_available": False,
                    "gidp_evidence_pa": 0.0,
                    "gidp_evidence_opportunities": 0.0,
                    "gidp_opportunity_rate": None,
                    "gidp_conversion_rate": None,
                    "non_gidp_multi_out_rate": None,
                    "gidp_fallback_reason": "missing_gidp_opportunity_evidence",
                }
            )
            continue
        pa = float(evidence["gidp_evidence_pa"])
        opportunities = float(evidence["gidp_evidence_opportunities"])
        events = float(evidence["gidp_evidence_events"])
        residual_events = float(evidence["non_gidp_multi_out_events"])
        opportunity_rate = (
            opportunities + prior_pa * population_opportunity_rate
        ) / (pa + prior_pa)
        conversion_rate = (
            (events + prior_opportunities * population_conversion_rate)
            / (opportunities + prior_opportunities)
            if opportunities + prior_opportunities > 0.0
            else 0.0
        )
        residual_rate = (
            residual_events + prior_pa * population_residual_rate
        ) / (pa + prior_pa)
        rows.append(
            {
                "player_id": player_id,
                "gidp_evidence_available": True,
                "gidp_evidence_pa": pa,
                "gidp_evidence_opportunities": opportunities,
                "gidp_opportunity_rate": opportunity_rate,
                "gidp_conversion_rate": conversion_rate,
                "non_gidp_multi_out_rate": residual_rate,
                "gidp_fallback_reason": None,
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def fit_c1_adjustments(
    player_games: pl.DataFrame,
    park_context: pl.DataFrame,
    historical_ages: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    component_prior_pa: float,
    park_prior_pa: float,
    movement_prior_pa: float,
    ridge_penalty: float,
) -> C1AdjustmentFit:
    """Fit the frozen park, movement, and age sequence without target rows."""

    _check_cutoff(player_games, predictor_cutoff_season)
    park_offsets = estimate_visitor_park_offsets(
        player_games,
        park_context,
        predictor_cutoff_season=predictor_cutoff_season,
        prior_pa=park_prior_pa,
    )
    player_exposure = aggregate_player_park_exposure(
        player_games,
        park_context,
        park_offsets,
        predictor_cutoff_season=predictor_cutoff_season,
    )
    season_exposure = aggregate_player_park_exposure(
        player_games,
        park_context,
        park_offsets,
        predictor_cutoff_season=predictor_cutoff_season,
        by_season=True,
    )
    seasons = estimate_player_season_probabilities(
        player_games,
        predictor_cutoff_season=predictor_cutoff_season,
        component_prior_pa=component_prior_pa,
    )
    neutral = neutralize_player_season_parks(seasons, season_exposure)
    aged = attach_relative_ages(neutral, historical_ages)
    movement = build_adjacent_movement_observations(aged)
    first_pass = solve_level_offsets(
        movement,
        prior_mover_pa=movement_prior_pa,
    )
    complete_age_pairs = (
        0
        if movement.is_empty()
        else movement.filter(
            pl.col("source_age_years").is_not_null()
            & pl.col("destination_age_years").is_not_null()
            & pl.col("source_context_median_age").is_not_null()
            & pl.col("destination_context_median_age").is_not_null()
        ).height
    )
    if complete_age_pairs:
        age_coefficients = fit_ridge_age_offsets(
            movement,
            first_pass,
            ridge_penalty=ridge_penalty,
        )
        age_fallback = None
        age_removed = remove_age_from_movement_observations(
            movement, age_coefficients
        )
    else:
        age_coefficients = zero_age_coefficients(ridge_penalty=ridge_penalty)
        age_fallback = "insufficient_chronology_safe_adjacent_seasons"
        age_removed = movement
    final_levels = solve_level_offsets(
        age_removed,
        prior_mover_pa=movement_prior_pa,
    )
    return C1AdjustmentFit(
        park_offsets=park_offsets,
        player_park_exposure=player_exposure,
        player_season_park_exposure=season_exposure,
        player_seasons=aged,
        movement_observations=movement,
        first_pass_level_offsets=first_pass,
        age_coefficients=age_coefficients,
        final_level_offsets=final_levels,
        age_fit_fallback_reason=age_fallback,
    )


def predict_c1_hierarchical_pbp(
    c0_predictions: pl.DataFrame,
    training: pl.DataFrame,
    fit: C1AdjustmentFit,
    gidp_rates: pl.DataFrame,
    *,
    target_age_contexts: Mapping[int, tuple[float, float] | None] | None = None,
) -> pl.DataFrame:
    """Apply frozen C1 adjustments to an unscored C0 forecast population."""

    require_probability_columns(c0_predictions)
    latest_levels = select_latest_evidenced_level(training)
    park_map = {
        int(row["player_id"]): row
        for row in fit.player_park_exposure.iter_rows(named=True)
    }
    level_map = {
        str(row["level_group"]): row
        for row in fit.final_level_offsets.iter_rows(named=True)
    }
    gidp_map = {
        int(row["player_id"]): row for row in gidp_rates.iter_rows(named=True)
    }
    ages = target_age_contexts or {}
    rows: list[dict[str, object]] = []
    for row in c0_predictions.sort("player_id").iter_rows(named=True):
        player_id = int(row["player_id"])
        probability = prediction_probability(row)
        park = park_map.get(player_id)
        park_offsets = (
            {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
            if park is None
            else terminal_offsets_from_row(
                park, prefix="park_log_offset_", multiplier=-1.0
            )
        )
        latest_level = latest_levels.get(player_id)
        level = None if latest_level is None else level_map.get(latest_level)
        level_connected = bool(
            level is not None and level["translation_connected_to_mlb"]
        )
        translation_offsets = (
            {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
            if not level_connected
            else terminal_offsets_from_row(
                level, prefix="level_log_offset_", multiplier=-1.0
            )
        )
        age_offsets, age_fallback = age_change_offsets(
            ages.get(player_id), fit.age_coefficients
        )
        combined = combine_offsets(park_offsets, translation_offsets, age_offsets)
        pre_gidp = apply_log_probability_offsets(probability, combined)
        gidp = gidp_map.get(player_id)
        adjusted, gidp_fallback = adjust_multi_out_for_gidp(
            pre_gidp,
            opportunity_rate=(
                None if gidp is None else gidp["gidp_opportunity_rate"]
            ),
            conversion_rate=(
                None if gidp is None else gidp["gidp_conversion_rate"]
            ),
            non_gidp_multi_out_rate=(
                None if gidp is None else gidp["non_gidp_multi_out_rate"]
            ),
        )
        rows.append(
            {
                **row,
                "model_id": "C1_HIERARCHICAL_PBP",
                "latest_evidenced_level": latest_level,
                "park_evidence_pa": 0.0 if park is None else park["park_evidence_pa"],
                "park_fallback_reason": (
                    "missing_park_context" if park is None else None
                ),
                "translation_fallback_reason": (
                    None
                    if level_connected
                    else (
                        "missing_level_history"
                        if latest_level is None
                        else "disconnected_level"
                    )
                ),
                "age_fallback_reason": (
                    fit.age_fit_fallback_reason or age_fallback
                ),
                "gidp_fallback_reason": gidp_fallback,
                **{
                    f"pre_gidp_p_{outcome}": pre_gidp[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
                **{
                    f"p_{outcome}": adjusted[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    result = pl.DataFrame(rows, infer_schema_length=None)
    require_probability_columns(result)
    return result


def terminal_offsets_from_row(
    row: Mapping[str, object],
    *,
    prefix: str,
    multiplier: float = 1.0,
) -> dict[str, float]:
    """Extract a complete named offset vector from a materialized row."""

    result: dict[str, float] = {}
    for outcome in HITTER_TALENT_OUTCOMES:
        value = row.get(f"{prefix}{outcome}")
        result[outcome] = 0.0 if value is None else float(value) * multiplier
    return result


def combine_offsets(*offsets: Mapping[str, float]) -> dict[str, float]:
    """Add compatible terminal-component offset vectors."""

    return {
        outcome: sum(float(vector.get(outcome, 0.0)) for vector in offsets)
        for outcome in HITTER_TALENT_OUTCOMES
    }


def require_probability_columns(frame: pl.DataFrame, *, prefix: str = "p_") -> None:
    """Validate a materialized prediction table without consulting outcomes."""

    required = [f"{prefix}{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(f"prediction table missing columns: {missing}")
    for row in frame.select(required).iter_rows(named=True):
        validate_probability_vector(
            {outcome: float(row[f"{prefix}{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES},
            tolerance=1e-10,
        )


def select_latest_evidenced_level(training: pl.DataFrame) -> dict[int, str]:
    """Select each player's latest, then largest-PA, evidenced level."""

    required = {"player_id", "season", "level_group", "hitter_talent_pa"}
    missing = sorted(required - set(training.columns))
    if missing:
        raise ValueError(f"training missing latest-level columns: {missing}")
    selected = (
        training.filter(pl.col("hitter_talent_pa") > 0)
        .sort(
            ["player_id", "season", "hitter_talent_pa", "level_group"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
    )
    return {
        int(row["player_id"]): str(row["level_group"])
        for row in selected.select("player_id", "level_group").iter_rows(named=True)
    }


def prediction_probability(row: Mapping[str, object]) -> dict[str, float]:
    """Read one standard prediction row into a named probability vector."""

    return {
        outcome: float(row[f"p_{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES
    }


def ensure_unique_ids(player_ids: Sequence[int]) -> list[int]:
    """Canonicalize a forecast population independently of target membership."""

    return sorted({int(player_id) for player_id in player_ids})
