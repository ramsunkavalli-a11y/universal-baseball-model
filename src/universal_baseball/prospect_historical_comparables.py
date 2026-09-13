"""Transparent historical comparable outcomes for pre-MLB players.

The output deliberately keeps three questions separate: whether a player reaches
MLB, how well he performs there conditional on arriving, and the all-player
expected outcome with non-arrivals retained as zero.
"""

from __future__ import annotations

import numpy as np
import polars as pl


RATE_COLUMNS = tuple(f"production_rate_{index}" for index in range(1, 5))
FEATURE_COLUMNS = ("age_years", "log_workload", *RATE_COLUMNS)
RATE_REGRESSION_PA = 200.0
DEFAULT_COMPARABLES = 150
CONDITIONAL_RATE_REGRESSION_PA = 200.0
EXACT_LEVEL_ORDER = {
    "ROOKIE_COMPLEX": 0,
    "SINGLE_A": 1,
    "HIGH_A": 2,
    "AA": 3,
    "AAA": 4,
}


def primary_exact_level(
    skill: pl.DataFrame, *, season: int, exposure: str
) -> pl.DataFrame:
    """Return the exact level supplying the most current-season workload."""

    required = {"player_id", "season", "level_group", exposure}
    if missing := sorted(required - set(skill.columns)):
        raise ValueError(f"skill history missing exact-level fields: {missing}")
    return (
        skill.filter(
            (pl.col("season") == season)
            & (pl.col("level_group").is_in(list(EXACT_LEVEL_ORDER)))
            & (pl.col(exposure) > 0)
        )
        .group_by("player_id", "level_group")
        .agg(pl.col(exposure).sum().alias("level_workload"))
        .with_columns(
            pl.col("level_workload").sum().over("player_id").alias("season_workload"),
            pl.col("level_group").replace_strict(EXACT_LEVEL_ORDER).alias("level_order"),
        )
        .sort(
            ["player_id", "level_workload", "level_order"],
            descending=[False, True, True],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select(
            "player_id",
            pl.col("level_group").alias("primary_level_group"),
            (pl.col("level_workload") / pl.col("season_workload"))
            .alias("primary_exact_level_workload_share"),
        )
    )


def _prepared(reference: pl.DataFrame, frame: pl.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    workload = reference["current_milb_workload"].to_numpy().astype(float)
    total = max(float(workload.sum()), 1.0)
    priors = np.asarray([
        float((reference[column] * reference["current_milb_workload"]).sum()) / total
        for column in RATE_COLUMNS
    ])

    def matrix(source: pl.DataFrame) -> np.ndarray:
        exposure = source["current_milb_workload"].to_numpy().astype(float)
        rates = source.select(RATE_COLUMNS).to_numpy().astype(float)
        regressed = (
            rates * exposure[:, None] + priors * RATE_REGRESSION_PA
        ) / (exposure[:, None] + RATE_REGRESSION_PA)
        return np.column_stack((
            source["age_years"].to_numpy().astype(float),
            np.log1p(exposure),
            regressed,
        ))

    reference_matrix = matrix(reference)
    target_matrix = matrix(frame)
    center = np.nanmedian(reference_matrix, axis=0)
    scale = np.nanstd(reference_matrix, axis=0)
    scale[scale < 1e-9] = 1.0
    reference_matrix = np.nan_to_num((reference_matrix - center) / scale)
    target_matrix = np.nan_to_num((target_matrix - center) / scale)
    return reference_matrix, target_matrix


def _score_comparables(
    reference: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    comparable_count: int = DEFAULT_COMPARABLES,
    rate_basis: float,
) -> pl.DataFrame:
    """Score every target from the same procedure and all-player outcomes.

    Comparisons stay within primary level. Rates are regressed before distance is
    measured. Every reference player remains in the outcome distribution, including
    players with zero later MLB opportunities.
    """

    required = {
        "player_id", "age_years", "primary_level_tier", "current_milb_workload",
        *RATE_COLUMNS,
    }
    outcome_columns = {"later_component_war", "later_mlb_workload"}
    if missing := sorted((required | outcome_columns) - set(reference.columns)):
        raise ValueError(f"reference missing comparable fields: {missing}")
    if missing := sorted(required - set(targets.columns)):
        raise ValueError(f"targets missing comparable fields: {missing}")
    if comparable_count < 25:
        raise ValueError("comparable_count must be at least 25")

    rows: list[dict[str, float | int | str]] = []
    level_column = (
        "primary_level_group"
        if "primary_level_group" in reference.columns
        and "primary_level_group" in targets.columns
        else "primary_level_tier"
    )
    arrived_reference = reference.filter(pl.col("later_mlb_workload") > 0)
    total_arrived_workload = float(arrived_reference["later_mlb_workload"].sum() or 0.0)
    conditional_rate_prior = (
        float(arrived_reference["later_component_war"].sum())
        * rate_basis
        / total_arrived_workload
        if total_arrived_workload > 0
        else 0.0
    )
    reference = reference.with_columns(
        pl.when(pl.col("later_mlb_workload") > 0)
        .then(
            (
                pl.col("later_component_war") * rate_basis
                + pl.lit(conditional_rate_prior) * CONDITIONAL_RATE_REGRESSION_PA
            )
            / (pl.col("later_mlb_workload") + CONDITIONAL_RATE_REGRESSION_PA)
        )
        .otherwise(None)
        .alias("later_component_war_rate_regressed")
    )

    for level in targets[level_column].unique().to_list():
        target_group = targets.filter(pl.col(level_column) == level)
        reference_group = reference.filter(pl.col(level_column) == level)
        if reference_group.height < 25:
            reference_group = reference
        reference_matrix, target_matrix = _prepared(reference_group, target_group)
        outcome = reference_group["later_component_war"].to_numpy().astype(float)
        workload = reference_group["later_mlb_workload"].to_numpy().astype(float)
        k = min(comparable_count, reference_group.height)
        for index, target in enumerate(target_group.iter_rows(named=True)):
            distance = np.sum((reference_matrix - target_matrix[index]) ** 2, axis=1)
            neighbor_index = np.argpartition(distance, k - 1)[:k]
            neighbor_outcome = outcome[neighbor_index]
            neighbor_workload = workload[neighbor_index]
            neighbor_arrived = neighbor_workload > 0
            arrival_rate = float(neighbor_arrived.mean())
            conditional_war = float(neighbor_outcome[neighbor_arrived].mean()) if neighbor_arrived.any() else 0.0
            conditional_rates = reference_group[
                "later_component_war_rate_regressed"
            ].to_numpy().astype(float)[neighbor_index][neighbor_arrived]
            rows.append({
                "player_id": int(target["player_id"]),
                "historical_comparable_level": str(level),
                "historical_comparable_players": int(k),
                "historical_arrivals_4y": int(neighbor_arrived.sum()),
                "historical_arrival_rate_4y": arrival_rate,
                "historical_conditional_component_war_per_600": (
                    float(conditional_rates.mean())
                    if len(conditional_rates) and rate_basis == 600.0
                    else None
                ),
                "historical_conditional_component_war_per_800": (
                    float(conditional_rates.mean())
                    if len(conditional_rates) and rate_basis == 800.0
                    else None
                ),
                "historical_conditional_component_war_rate": (
                    float(conditional_rates.mean()) if len(conditional_rates) else 0.0
                ),
                "historical_conditional_rate_basis": int(rate_basis),
                "historical_conditional_component_war_4y": conditional_war,
                "historical_component_war_4y": float(neighbor_outcome.mean()),
                "historical_positive_component_war_4y": float(
                    np.maximum(neighbor_outcome, 0.0).mean()
                ),
                "historical_impact_rate_4y": float((neighbor_outcome >= 1.0).mean()),
                "historical_expectation_identity_error": abs(
                    float(neighbor_outcome.mean()) - arrival_rate * conditional_war
                ),
            })
    return pl.DataFrame(rows).sort("player_id")


def score_hitter_comparables(
    reference: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    comparable_count: int = DEFAULT_COMPARABLES,
) -> pl.DataFrame:
    """Score hitter outcomes on a 600-PA conditional-rate basis."""

    return _score_comparables(
        reference, targets, comparable_count=comparable_count, rate_basis=600.0
    )


def score_pitcher_comparables(
    reference: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    comparable_count: int = DEFAULT_COMPARABLES,
) -> pl.DataFrame:
    """Score pitcher outcomes on an 800-BF conditional-rate basis."""

    return _score_comparables(
        reference, targets, comparable_count=comparable_count, rate_basis=800.0
    )
