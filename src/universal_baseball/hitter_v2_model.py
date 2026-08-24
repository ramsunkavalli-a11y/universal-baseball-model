"""Interpretable nested empirical-Bayes primitives for Hitter v2.

The estimator operates only on chronology-filtered terminal-outcome history.
It exposes no validation scorer and cannot access target-season rows.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping, Sequence

import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


@dataclass(frozen=True, slots=True)
class NestedNode:
    name: str
    children: tuple[str, ...]


NESTED_NODES = (
    NestedNode("plate_appearance", ("K", "NON_K")),
    NestedNode("non_k", ("UBB", "NON_UBB")),
    NestedNode("non_k_non_ubb", ("HBP", "CONTACT")),
    NestedNode("contact", ("HR", "NON_HR")),
    NestedNode("non_hr_contact", ("REACH", "NON_REACH")),
    NestedNode("reach", ("HIT", "NON_HIT_REACH")),
    NestedNode("hit_in_play", ("1B", "2B", "3B")),
    NestedNode("non_hit_reach", ("ROE", "FC_REACH")),
    NestedNode("non_reach", ("SF", "MULTI_OUT", "OTHER_OUT")),
)

DEFAULT_COMPONENT_PRIOR_PA = {node.name: 200.0 for node in NESTED_NODES}
MARCEL_REGRESSION_PA = 1200.0
MARCEL_RECENCY_WEIGHTS = {0: 5.0, 1: 4.0, 2: 3.0}
MARCEL_POSITIVE_OUTCOMES = ("UBB", "HBP", "1B", "2B", "3B", "HR")


def _leaf_counts(counts: Mapping[str, float]) -> dict[str, float]:
    missing = sorted(set(HITTER_TALENT_OUTCOMES) - set(counts))
    if missing:
        raise ValueError(f"terminal history is missing outcomes: {missing}")
    result = {key: float(counts[key]) for key in HITTER_TALENT_OUTCOMES}
    if any(not isfinite(value) or value < 0.0 for value in result.values()):
        raise ValueError("terminal history counts must be finite and nonnegative")
    return result


def _branch_counts(leaves: Mapping[str, float]) -> dict[str, float]:
    hit = leaves["1B"] + leaves["2B"] + leaves["3B"]
    non_hit_reach = leaves["ROE"] + leaves["FC_REACH"]
    reach = hit + non_hit_reach
    non_reach = leaves["SF"] + leaves["MULTI_OUT"] + leaves["OTHER_OUT"]
    non_hr = reach + non_reach
    contact = leaves["HR"] + non_hr
    non_ubb = leaves["HBP"] + contact
    non_k = leaves["UBB"] + non_ubb
    return {
        **leaves,
        "HIT": hit,
        "NON_HIT_REACH": non_hit_reach,
        "REACH": reach,
        "NON_REACH": non_reach,
        "NON_HR": non_hr,
        "CONTACT": contact,
        "NON_UBB": non_ubb,
        "NON_K": non_k,
    }


def nested_empirical_bayes_probabilities(
    history_counts: Mapping[str, float],
    prior_counts: Mapping[str, float],
    *,
    component_prior_pa: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Estimate one coherent terminal-outcome simplex via nested shrinkage."""

    histories = {
        node.name: history_counts for node in NESTED_NODES
    }
    return nested_empirical_bayes_probabilities_componentwise(
        histories,
        prior_counts,
        component_prior_pa=component_prior_pa,
    )


def nested_empirical_bayes_probabilities_componentwise(
    history_counts_by_component: Mapping[str, Mapping[str, float]],
    prior_counts: Mapping[str, float],
    *,
    component_prior_pa: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Estimate a simplex with independently weighted component histories."""

    expected = {node.name for node in NESTED_NODES}
    observed = set(history_counts_by_component)
    if observed != expected:
        raise ValueError(
            "component histories differ: "
            f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
        )
    histories = {
        name: _branch_counts(_leaf_counts(counts))
        for name, counts in history_counts_by_component.items()
    }
    prior = _branch_counts(_leaf_counts(prior_counts))
    strengths = dict(DEFAULT_COMPONENT_PRIOR_PA)
    if component_prior_pa is not None:
        unknown = sorted(set(component_prior_pa) - set(strengths))
        if unknown:
            raise ValueError(f"unknown nested component priors: {unknown}")
        strengths.update({key: float(value) for key, value in component_prior_pa.items()})
    if any(not isfinite(value) or value <= 0.0 for value in strengths.values()):
        raise ValueError("component prior PA must be finite and positive")

    conditional: dict[tuple[str, str], float] = {}
    for node in NESTED_NODES:
        history = histories[node.name]
        history_total = sum(history[child] for child in node.children)
        prior_total = sum(prior[child] for child in node.children)
        if prior_total <= 0.0:
            prior_probabilities = {
                child: 1.0 / len(node.children) for child in node.children
            }
        else:
            prior_probabilities = {
                child: prior[child] / prior_total for child in node.children
            }
        denominator = history_total + strengths[node.name]
        for child in node.children:
            conditional[(node.name, child)] = (
                history[child]
                + strengths[node.name] * prior_probabilities[child]
            ) / denominator

    probabilities = {
        "K": conditional[("plate_appearance", "K")],
        "UBB": conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "UBB")],
        "HBP": conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "NON_UBB")]
        * conditional[("non_k_non_ubb", "HBP")],
    }
    contact_probability = (
        conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "NON_UBB")]
        * conditional[("non_k_non_ubb", "CONTACT")]
    )
    probabilities["HR"] = contact_probability * conditional[("contact", "HR")]
    non_hr_probability = contact_probability * conditional[("contact", "NON_HR")]
    reach_probability = non_hr_probability * conditional[("non_hr_contact", "REACH")]
    hit_probability = reach_probability * conditional[("reach", "HIT")]
    for outcome in ("1B", "2B", "3B"):
        probabilities[outcome] = hit_probability * conditional[
            ("hit_in_play", outcome)
        ]
    non_hit_reach_probability = reach_probability * conditional[
        ("reach", "NON_HIT_REACH")
    ]
    for outcome in ("ROE", "FC_REACH"):
        probabilities[outcome] = non_hit_reach_probability * conditional[
            ("non_hit_reach", outcome)
        ]
    non_reach_probability = non_hr_probability * conditional[
        ("non_hr_contact", "NON_REACH")
    ]
    for outcome in ("SF", "MULTI_OUT", "OTHER_OUT"):
        probabilities[outcome] = non_reach_probability * conditional[
            ("non_reach", outcome)
        ]
    validate_probability_vector(probabilities, tolerance=1e-10)
    return probabilities


def recency_weighted_player_counts(
    training: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    half_life_seasons: float,
) -> dict[int, dict[str, float]]:
    """Aggregate player outcome histories with a fixed seasonal half-life."""

    half_life = float(half_life_seasons)
    if not isfinite(half_life) or half_life <= 0.0:
        raise ValueError("recency half-life must be finite and positive")
    if training.filter(pl.col("season") > predictor_cutoff_season).height:
        raise ValueError("training contains rows after the predictor cutoff")
    weights = training.with_columns(
        (
            0.5
            ** (
                (pl.lit(predictor_cutoff_season) - pl.col("season"))
                / pl.lit(half_life)
            )
        ).alias("recency_weight")
    )
    aggregated = weights.group_by("player_id").agg(
        *[
            (pl.col(outcome) * pl.col("recency_weight")).sum().alias(outcome)
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    return {
        int(row["player_id"]): {
            outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES
        }
        for row in aggregated.to_dicts()
    }


def pooled_prior_counts(training: pl.DataFrame) -> dict[str, float]:
    """Build a full-population chronology-safe prior without target membership."""

    if training.is_empty():
        raise ValueError("training population cannot be empty")
    return {
        outcome: float(training[outcome].sum())
        for outcome in HITTER_TALENT_OUTCOMES
    }


def _player_environment_priors(
    training: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
) -> tuple[dict[int, dict[str, float]], dict[str, float]]:
    """Return chronology-safe league-season-level priors for each known player."""

    latest_season = int(training["season"].max())
    latest_population = training.filter(pl.col("season") == latest_season)
    global_prior = pooled_prior_counts(latest_population)
    groups = training.group_by(["season", "league_id", "level_group"]).agg(
        *[pl.col(outcome).sum().alias(outcome) for outcome in HITTER_TALENT_OUTCOMES]
    )
    group_map = {
        (int(row["season"]), int(row["league_id"]), str(row["level_group"])): {
            outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES
        }
        for row in groups.to_dicts()
    }
    primary = (
        training.sort(
            ["player_id", "season", "hitter_talent_pa", "league_id"],
            descending=[False, True, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "season", "league_id", "level_group")
    )
    priors = {
        int(row["player_id"]): group_map[
            (
                int(row["season"]),
                int(row["league_id"]),
                str(row["level_group"]),
            )
        ]
        for row in primary.to_dicts()
    }
    if latest_season > predictor_cutoff_season:
        raise ValueError("environment priors cross the predictor cutoff")
    return priors, global_prior


def predict_c0_nested_eb(
    training: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    half_life_seasons: float | Mapping[str, float],
    component_prior_pa: Mapping[str, float] | None = None,
) -> pl.DataFrame:
    """Predict C0 from history only; target rows and target context are not accepted."""

    if isinstance(half_life_seasons, Mapping):
        expected = {node.name for node in NESTED_NODES}
        observed = set(half_life_seasons)
        if observed != expected:
            raise ValueError(
                "component half-lives differ: "
                f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
            )
        component_half_lives = {
            name: float(value) for name, value in half_life_seasons.items()
        }
    else:
        component_half_lives = {
            node.name: float(half_life_seasons) for node in NESTED_NODES
        }
    histories_by_half_life = {
        half_life: recency_weighted_player_counts(
            training,
            predictor_cutoff_season=predictor_cutoff_season,
            half_life_seasons=half_life,
        )
        for half_life in sorted(set(component_half_lives.values()))
    }
    player_priors, global_prior = _player_environment_priors(
        training, predictor_cutoff_season=predictor_cutoff_season
    )
    zero = {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
    rows = []
    for player_id in sorted(set(int(value) for value in player_ids)):
        histories = {
            node.name: histories_by_half_life[component_half_lives[node.name]].get(
                player_id, zero
            )
            for node in NESTED_NODES
        }
        probabilities = nested_empirical_bayes_probabilities_componentwise(
            histories,
            player_priors.get(player_id, global_prior),
            component_prior_pa=component_prior_pa,
        )
        evidence_counts = histories_by_half_life[
            component_half_lives["plate_appearance"]
        ].get(player_id, zero)
        rows.append(
            {
                "player_id": player_id,
                "model_id": "C0_NESTED_EB",
                "predictor_cutoff_season": predictor_cutoff_season,
                "prior_history_available": any(
                    player_id in history for history in histories_by_half_life.values()
                ),
                "prior_hitter_talent_pa": sum(evidence_counts.values()),
                **{f"p_{outcome}": probabilities[outcome] for outcome in HITTER_TALENT_OUTCOMES},
            }
        )
    return pl.DataFrame(rows)


def predict_b0_one_year_eb(
    training: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    component_prior_pa: Mapping[str, float] | None = None,
) -> pl.DataFrame:
    """Predict the permanent one-year empirical-Bayes outcome baseline."""

    one_year = training.filter(pl.col("season") == predictor_cutoff_season)
    if one_year.is_empty():
        raise ValueError("B0 has no prior-season evidence at the cutoff")
    prediction = predict_c0_nested_eb(
        one_year,
        player_ids,
        predictor_cutoff_season=predictor_cutoff_season,
        half_life_seasons=1.0,
        component_prior_pa=component_prior_pa,
    )
    return prediction.with_columns(pl.lit("B0_ONE_YEAR_EB").alias("model_id"))


def marcel_age_factor(age_at_target: float | None) -> float:
    """Return the standard Marcel hitter age multiplier, neutral when missing."""

    if age_at_target is None:
        return 1.0
    age = float(age_at_target)
    if not isfinite(age) or age < 15.0 or age > 50.0:
        raise ValueError("Marcel target age must be finite and between 15 and 50")
    rate = 0.006 if age <= 29.0 else 0.003
    return 1.0 + (29.0 - age) * rate


def _apply_marcel_age(
    probabilities: Mapping[str, float],
    age_at_target: float | None,
) -> dict[str, float]:
    """Apply Marcel age to positive-event odds while preserving the simplex."""

    validate_probability_vector(probabilities)
    factor = marcel_age_factor(age_at_target)
    result = {
        outcome: float(probabilities[outcome])
        * (factor if outcome in MARCEL_POSITIVE_OUTCOMES else 1.0)
        for outcome in HITTER_TALENT_OUTCOMES
    }
    denominator = sum(result.values())
    normalized = {outcome: value / denominator for outcome, value in result.items()}
    validate_probability_vector(normalized)
    return normalized


def predict_b1_marcel_345_k1200(
    training: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    ages_at_target: Mapping[int, float] | None = None,
) -> pl.DataFrame:
    """Predict the fixed 3/4/5, 1,200-PA-regressed Marcel baseline."""

    relevant = training.filter(
        (pl.col("season") <= predictor_cutoff_season)
        & (pl.col("season") >= predictor_cutoff_season - 2)
    )
    if relevant.is_empty():
        raise ValueError("B1 has no evidence in its three-season window")
    if training.filter(pl.col("season") > predictor_cutoff_season).height:
        raise ValueError("B1 training crosses the predictor cutoff")
    weighted = relevant.with_columns(
        (pl.lit(predictor_cutoff_season) - pl.col("season"))
        .replace_strict(MARCEL_RECENCY_WEIGHTS, return_dtype=pl.Float64)
        .alias("marcel_weight")
    )
    player_counts = weighted.group_by("player_id").agg(
        *[
            (pl.col(outcome) * pl.col("marcel_weight")).sum().alias(outcome)
            for outcome in HITTER_TALENT_OUTCOMES
        ]
    )
    history = {
        int(row["player_id"]): {
            outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES
        }
        for row in player_counts.to_dicts()
    }
    prior_counts = pooled_prior_counts(
        relevant.filter(pl.col("season") == int(relevant["season"].max()))
    )
    prior_total = sum(prior_counts.values())
    prior_probabilities = {
        outcome: prior_counts[outcome] / prior_total
        for outcome in HITTER_TALENT_OUTCOMES
    }
    ages = ages_at_target or {}
    zero = {outcome: 0.0 for outcome in HITTER_TALENT_OUTCOMES}
    rows = []
    for player_id in sorted(set(int(value) for value in player_ids)):
        counts = history.get(player_id, zero)
        evidence = sum(counts.values())
        raw = {
            outcome: (
                counts[outcome] + MARCEL_REGRESSION_PA * prior_probabilities[outcome]
            )
            / (evidence + MARCEL_REGRESSION_PA)
            for outcome in HITTER_TALENT_OUTCOMES
        }
        age = ages.get(player_id)
        probabilities = _apply_marcel_age(raw, age)
        rows.append(
            {
                "player_id": player_id,
                "model_id": "B1_MARCEL_345_K1200",
                "predictor_cutoff_season": predictor_cutoff_season,
                "prior_history_available": player_id in history,
                "prior_hitter_talent_pa": evidence,
                "age_at_target": age,
                "age_fallback": "neutral_missing_age" if age is None else None,
                "marcel_age_factor": marcel_age_factor(age),
                **{
                    f"p_{outcome}": probabilities[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows)
