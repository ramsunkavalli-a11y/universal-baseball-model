"""Pre-fit J0 contextual primitives for Hitter v2 Stage 2d.

The module constructs chronology-safe same-node pitcher residuals and applies
already-estimated player context increments to the frozen B1 simplex. It does not
load evaluation targets, fit the real-data candidate, score a fold, or rank players.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, log
from typing import Mapping

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b import (
    assemble_nested_probabilities,
    nested_conditionals,
)


@dataclass(frozen=True, slots=True)
class BinaryContextNode:
    name: str
    numerator: tuple[str, ...]
    denominator: tuple[str, ...]
    prior_pa: float
    nested_node: str
    positive_child: str


CONTACT_OUTCOMES = (
    "HR",
    "3B",
    "2B",
    "1B",
    "ROE",
    "FC_REACH",
    "SF",
    "MULTI_OUT",
    "OTHER_OUT",
)
NON_HR_CONTACT_OUTCOMES = tuple(x for x in CONTACT_OUTCOMES if x != "HR")
NON_HR_REACH_OUTCOMES = ("3B", "2B", "1B", "ROE", "FC_REACH")
BINARY_CONTEXT_NODES = (
    BinaryContextNode(
        "K",
        ("K",),
        HITTER_TALENT_OUTCOMES,
        200.0,
        "plate_appearance",
        "K",
    ),
    BinaryContextNode(
        "UBB",
        ("UBB",),
        tuple(x for x in HITTER_TALENT_OUTCOMES if x != "K"),
        400.0,
        "non_k",
        "UBB",
    ),
    BinaryContextNode(
        "HBP",
        ("HBP",),
        ("HBP", *CONTACT_OUTCOMES),
        1000.0,
        "non_k_non_ubb",
        "HBP",
    ),
    BinaryContextNode(
        "HR",
        ("HR",),
        CONTACT_OUTCOMES,
        400.0,
        "contact",
        "HR",
    ),
    BinaryContextNode(
        "NON_HR_REACH",
        NON_HR_REACH_OUTCOMES,
        NON_HR_CONTACT_OUTCOMES,
        800.0,
        "non_hr_contact",
        "REACH",
    ),
)
NODE_BY_NAME = {node.name: node for node in BINARY_CONTEXT_NODES}
HIT_COMPOSITION = ("1B", "2B", "3B")
HIT_COMPOSITION_PRIOR_PA = 800.0
RECENCY_HALF_LIFE_SEASONS = 2.0
PROBABILITY_FLOOR = 1e-9
LSL_PRIOR_SD = 0.35
PLATOON_PRIOR_SD = 0.20
PITCHER_COEFFICIENT_PRIOR_MEAN = 1.0
PITCHER_COEFFICIENT_PRIOR_SD = 0.25
PITCHER_COEFFICIENT_BOUNDS = (0.0, 1.5)
BATTER_EFFECT_SD_BOUNDS = (0.05, 1.25)


@dataclass(frozen=True, slots=True)
class BinaryContextFit:
    """Matched binary-node coefficient surfaces and deterministic diagnostics."""

    contextual_batter_effects: pl.DataFrame
    uncontextual_batter_effects: pl.DataFrame
    context_increments: pl.DataFrame
    fixed_effects: pl.DataFrame
    metrics: dict[str, object]


@dataclass(frozen=True, slots=True)
class MultinomialContextFit:
    """Matched hit-composition coefficient surfaces and diagnostics."""

    contextual_batter_effects: pl.DataFrame
    uncontextual_batter_effects: pl.DataFrame
    context_increments: pl.DataFrame
    fixed_effects: pl.DataFrame
    metrics: dict[str, object]


def _validate_event_frame(frame: pl.DataFrame) -> None:
    required = {
        "season",
        "game_date",
        "game_pk",
        "at_bat_index",
        "league_id",
        "level_group",
        "pitcher_id",
        "canonical_outcome",
        "context_label_ready",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"J0 event source missing fields: {missing}")
    if frame.filter(pl.col("season") >= 2025).height:
        raise ValueError("J0 pre-fit context source crossed the 2021-2024 boundary")
    duplicate = frame.group_by(["season", "game_pk", "at_bat_index"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("J0 event source is not unique at PA grain")


def attach_binary_node_observation(
    frame: pl.DataFrame, node_name: str
) -> pl.DataFrame:
    """Attach frozen eligibility and response for one nested binary node."""

    node = NODE_BY_NAME.get(node_name)
    if node is None:
        raise ValueError(f"unknown J0 binary node: {node_name}")
    return frame.with_columns(
        (
            pl.col("context_label_ready")
            & pl.col("canonical_outcome").is_in(node.denominator)
        ).alias(f"{node.name}_eligible"),
        pl.when(
            pl.col("context_label_ready")
            & pl.col("canonical_outcome").is_in(node.denominator)
        )
        .then(pl.col("canonical_outcome").is_in(node.numerator).cast(pl.Int8))
        .otherwise(pl.lit(None, dtype=pl.Int8))
        .alias(f"{node.name}_response"),
    )


def _strict_prior_daily_counts(
    daily: pl.DataFrame,
    *,
    group_columns: list[str],
    numerator_column: str,
    denominator_column: str,
    prefix: str,
    half_life_seasons: float,
) -> pl.DataFrame:
    """Return decayed counts from dates strictly before each daily row."""

    half_life = float(half_life_seasons)
    if not isfinite(half_life) or half_life <= 0.0:
        raise ValueError("context half-life must be finite and positive")
    base_season = int(daily["season"].min())
    scale = 2.0 ** (
        (pl.col("season") - pl.lit(base_season)) / pl.lit(half_life)
    )
    ordered = daily.sort([*group_columns, "game_date"]).with_columns(
        (pl.col(numerator_column) * scale).alias("_weighted_numerator"),
        (pl.col(denominator_column) * scale).alias("_weighted_denominator"),
    )
    prior_weighted_numerator = (
        pl.col("_weighted_numerator").cum_sum().over(group_columns)
        - pl.col("_weighted_numerator")
    )
    prior_weighted_denominator = (
        pl.col("_weighted_denominator").cum_sum().over(group_columns)
        - pl.col("_weighted_denominator")
    )
    return ordered.with_columns(
        (prior_weighted_numerator / scale).alias(f"{prefix}_numerator"),
        (prior_weighted_denominator / scale).alias(f"{prefix}_denominator"),
    ).drop("_weighted_numerator", "_weighted_denominator")


def build_prior_pitcher_binary_feature(
    frame: pl.DataFrame,
    node_name: str,
    *,
    half_life_seasons: float = RECENCY_HALF_LIFE_SEASONS,
) -> pl.DataFrame:
    """Attach a same-node prior pitcher residual with the whole current date excluded."""

    _validate_event_frame(frame)
    node = NODE_BY_NAME.get(node_name)
    if node is None:
        raise ValueError(f"unknown J0 binary node: {node_name}")
    observed = attach_binary_node_observation(frame, node_name)
    eligible = f"{node.name}_eligible"
    response = f"{node.name}_response"
    daily_pitcher = observed.group_by(["pitcher_id", "game_date"]).agg(
        pl.col("season").first().alias("season"),
        pl.col(response).drop_nulls().sum().alias("daily_numerator"),
        pl.col(eligible).sum().alias("daily_denominator"),
    )
    pitcher_prior = _strict_prior_daily_counts(
        daily_pitcher,
        group_columns=["pitcher_id"],
        numerator_column="daily_numerator",
        denominator_column="daily_denominator",
        prefix=f"{node.name}_prior_pitcher",
        half_life_seasons=half_life_seasons,
    ).select(
        "pitcher_id",
        "game_date",
        f"{node.name}_prior_pitcher_numerator",
        f"{node.name}_prior_pitcher_denominator",
    )
    daily_context = observed.group_by(
        ["league_id", "level_group", "game_date"]
    ).agg(
        pl.col("season").first().alias("season"),
        pl.col(response).drop_nulls().sum().alias("daily_numerator"),
        pl.col(eligible).sum().alias("daily_denominator"),
    )
    context_prior = _strict_prior_daily_counts(
        daily_context,
        group_columns=["league_id", "level_group"],
        numerator_column="daily_numerator",
        denominator_column="daily_denominator",
        prefix=f"{node.name}_prior_context",
        half_life_seasons=half_life_seasons,
    ).select(
        "league_id",
        "level_group",
        "game_date",
        f"{node.name}_prior_context_numerator",
        f"{node.name}_prior_context_denominator",
    )
    joined = observed.join(
        pitcher_prior,
        on=["pitcher_id", "game_date"],
        how="left",
        validate="m:1",
    ).join(
        context_prior,
        on=["league_id", "level_group", "game_date"],
        how="left",
        validate="m:1",
    )
    pitcher_n = pl.col(f"{node.name}_prior_pitcher_denominator").fill_null(0.0)
    context_n = pl.col(f"{node.name}_prior_context_denominator").fill_null(0.0)
    context_rate = (
        pl.col(f"{node.name}_prior_context_numerator") / context_n
    ).clip(PROBABILITY_FLOOR, 1.0 - PROBABILITY_FLOOR)
    posterior_rate = (
        pl.col(f"{node.name}_prior_pitcher_numerator").fill_null(0.0)
        + pl.lit(node.prior_pa) * context_rate
    ) / (pitcher_n + pl.lit(node.prior_pa))
    logit = lambda value: value.log() - (1.0 - value).log()  # noqa: E731
    return joined.with_columns(
        context_rate.alias(f"{node.name}_prior_context_rate"),
        pl.when((pitcher_n > 0.0) & (context_n > 0.0))
        .then(logit(posterior_rate) - logit(context_rate))
        .otherwise(pl.lit(0.0))
        .alias(f"{node.name}_prior_pitcher_log_odds_residual"),
        pl.when(context_n > 0.0)
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.lit("no_prior_context_events"))
        .alias(f"{node.name}_pitcher_feature_fallback"),
    )


def build_all_prior_pitcher_binary_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Attach all five frozen binary-node pitcher features."""

    result = frame
    base_columns = set(frame.columns)
    for node in BINARY_CONTEXT_NODES:
        augmented = build_prior_pitcher_binary_feature(frame, node.name)
        additions = [column for column in augmented.columns if column not in base_columns]
        result = result.join(
            augmented.select("season", "game_pk", "at_bat_index", *additions),
            on=["season", "game_pk", "at_bat_index"],
            how="left",
            validate="1:1",
        )
    return result


def build_prior_pitcher_hit_composition_features(
    frame: pl.DataFrame,
    *,
    half_life_seasons: float = RECENCY_HALF_LIFE_SEASONS,
) -> pl.DataFrame:
    """Attach prior-only pitcher ALR residuals for 2B/3B versus the 1B reference."""

    _validate_event_frame(frame)
    observed = frame.with_columns(
        (
            pl.col("context_label_ready")
            & pl.col("canonical_outcome").is_in(HIT_COMPOSITION)
        ).alias("HIT_COMPOSITION_eligible"),
        pl.when(
            pl.col("context_label_ready")
            & pl.col("canonical_outcome").is_in(HIT_COMPOSITION)
        )
        .then(pl.col("canonical_outcome"))
        .otherwise(pl.lit(None, dtype=pl.String))
        .alias("HIT_COMPOSITION_response"),
    )
    daily_pitcher = observed.group_by(["pitcher_id", "game_date"]).agg(
        pl.col("season").first().alias("season"),
        pl.col("HIT_COMPOSITION_eligible").sum().alias("daily_denominator"),
        *[
            (pl.col("HIT_COMPOSITION_response") == outcome)
            .sum()
            .alias(f"daily_{outcome}")
            for outcome in HIT_COMPOSITION
        ],
    )
    daily_context = observed.group_by(
        ["league_id", "level_group", "game_date"]
    ).agg(
        pl.col("season").first().alias("season"),
        pl.col("HIT_COMPOSITION_eligible").sum().alias("daily_denominator"),
        *[
            (pl.col("HIT_COMPOSITION_response") == outcome)
            .sum()
            .alias(f"daily_{outcome}")
            for outcome in HIT_COMPOSITION
        ],
    )

    def prior_surface(
        daily: pl.DataFrame, group_columns: list[str], prefix: str
    ) -> pl.DataFrame:
        result = _strict_prior_daily_counts(
            daily,
            group_columns=group_columns,
            numerator_column="daily_1B",
            denominator_column="daily_denominator",
            prefix=prefix,
            half_life_seasons=half_life_seasons,
        ).rename({f"{prefix}_numerator": f"{prefix}_1B"})
        for outcome in ("2B", "3B"):
            outcome_prior = _strict_prior_daily_counts(
                daily,
                group_columns=group_columns,
                numerator_column=f"daily_{outcome}",
                denominator_column="daily_denominator",
                prefix=f"_{outcome}",
                half_life_seasons=half_life_seasons,
            ).select(
                *group_columns,
                "game_date",
                pl.col(f"_{outcome}_numerator").alias(f"{prefix}_{outcome}"),
            )
            result = result.join(
                outcome_prior,
                on=[*group_columns, "game_date"],
                how="left",
                validate="1:1",
            )
        return result

    pitcher_prior = prior_surface(
        daily_pitcher, ["pitcher_id"], "HIT_COMPOSITION_prior_pitcher"
    ).select(
        "pitcher_id",
        "game_date",
        "HIT_COMPOSITION_prior_pitcher_denominator",
        *[f"HIT_COMPOSITION_prior_pitcher_{x}" for x in HIT_COMPOSITION],
    )
    context_prior = prior_surface(
        daily_context,
        ["league_id", "level_group"],
        "HIT_COMPOSITION_prior_context",
    ).select(
        "league_id",
        "level_group",
        "game_date",
        "HIT_COMPOSITION_prior_context_denominator",
        *[f"HIT_COMPOSITION_prior_context_{x}" for x in HIT_COMPOSITION],
    )
    joined = observed.join(
        pitcher_prior,
        on=["pitcher_id", "game_date"],
        how="left",
        validate="m:1",
    ).join(
        context_prior,
        on=["league_id", "level_group", "game_date"],
        how="left",
        validate="m:1",
    )
    pitcher_n = pl.col("HIT_COMPOSITION_prior_pitcher_denominator").fill_null(0.0)
    context_n = pl.col("HIT_COMPOSITION_prior_context_denominator").fill_null(0.0)
    context_rates = {
        outcome: (
            pl.col(f"HIT_COMPOSITION_prior_context_{outcome}") / context_n
        ).clip(PROBABILITY_FLOOR, 1.0 - PROBABILITY_FLOOR)
        for outcome in HIT_COMPOSITION
    }
    posterior_rates = {
        outcome: (
            pl.col(f"HIT_COMPOSITION_prior_pitcher_{outcome}").fill_null(0.0)
            + pl.lit(HIT_COMPOSITION_PRIOR_PA) * context_rates[outcome]
        )
        / (pitcher_n + pl.lit(HIT_COMPOSITION_PRIOR_PA))
        for outcome in HIT_COMPOSITION
    }
    return joined.with_columns(
        *[
            context_rates[outcome].alias(
                f"HIT_COMPOSITION_prior_context_rate_{outcome}"
            )
            for outcome in HIT_COMPOSITION
        ],
        pl.lit(0.0).alias("HIT_COMPOSITION_prior_pitcher_alr_residual_1B"),
        *[
            pl.when((pitcher_n > 0.0) & (context_n > 0.0))
            .then(
                (posterior_rates[outcome] / posterior_rates["1B"]).log()
                - (context_rates[outcome] / context_rates["1B"]).log()
            )
            .otherwise(pl.lit(0.0))
            .alias(f"HIT_COMPOSITION_prior_pitcher_alr_residual_{outcome}")
            for outcome in ("2B", "3B")
        ],
        pl.when(context_n > 0.0)
        .then(pl.lit(None, dtype=pl.String))
        .otherwise(pl.lit("no_prior_context_events"))
        .alias("HIT_COMPOSITION_pitcher_feature_fallback"),
    )


def build_all_prior_pitcher_features(frame: pl.DataFrame) -> pl.DataFrame:
    """Attach all frozen J0 binary and hit-composition pitcher features."""

    binary = build_all_prior_pitcher_binary_features(frame)
    composition = build_prior_pitcher_hit_composition_features(frame)
    additions = [column for column in composition.columns if column not in frame.columns]
    return binary.join(
        composition.select("season", "game_pk", "at_bat_index", *additions),
        on=["season", "game_pk", "at_bat_index"],
        how="left",
        validate="1:1",
    )


def _encode_groups(values: list[object]) -> tuple[np.ndarray, list[object]]:
    levels = sorted(set(values), key=lambda value: str(value))
    lookup = {value: index for index, value in enumerate(levels)}
    return np.asarray([lookup[value] for value in values], dtype=np.int64), levels


def _binary_objective(
    y: np.ndarray,
    eta: np.ndarray,
    *,
    lsl_effect: np.ndarray,
    batter_effect: np.ndarray,
    platoon_effect: np.ndarray,
    pitcher_coefficient: float,
    batter_sd: float,
    include_context: bool,
) -> float:
    value = float(np.sum(np.logaddexp(0.0, eta) - y * eta))
    value += 0.5 * float(np.sum((lsl_effect / LSL_PRIOR_SD) ** 2))
    value += 0.5 * float(np.sum((batter_effect / batter_sd) ** 2))
    if include_context:
        value += 0.5 * float(np.sum((platoon_effect / PLATOON_PRIOR_SD) ** 2))
        value += 0.5 * (
            (pitcher_coefficient - PITCHER_COEFFICIENT_PRIOR_MEAN)
            / PITCHER_COEFFICIENT_PRIOR_SD
        ) ** 2
    return value


def _fit_binary_map_arrays(
    *,
    y: np.ndarray,
    lsl_index: np.ndarray,
    batter_index: np.ndarray,
    platoon_index: np.ndarray,
    pitcher_residual: np.ndarray,
    batter_sd: float,
    include_context: bool,
    max_iterations: int,
    tolerance: float,
) -> tuple[dict[str, object], dict[str, object]]:
    """Fit one deterministic penalized event model with grouped Newton updates."""

    if len(y) == 0:
        raise ValueError("binary context model has no eligible events")
    if not BATTER_EFFECT_SD_BOUNDS[0] <= batter_sd <= BATTER_EFFECT_SD_BOUNDS[1]:
        raise ValueError("batter effect SD is outside frozen bounds")
    if max_iterations <= 0 or tolerance <= 0.0:
        raise ValueError("optimizer controls must be positive")
    lsl_count = int(lsl_index.max()) + 1
    batter_count = int(batter_index.max()) + 1
    platoon_count = int(platoon_index.max()) + 1
    intercept = _logit(float(np.clip(y.mean(), PROBABILITY_FLOOR, 1 - PROBABILITY_FLOOR)))
    lsl_effect = np.zeros(lsl_count, dtype=float)
    batter_effect = np.zeros(batter_count, dtype=float)
    platoon_effect = np.zeros(platoon_count, dtype=float)
    pitcher_coefficient = PITCHER_COEFFICIENT_PRIOR_MEAN if include_context else 0.0
    lsl_precision = 1.0 / LSL_PRIOR_SD**2
    batter_precision = 1.0 / batter_sd**2
    platoon_precision = 1.0 / PLATOON_PRIOR_SD**2
    pitcher_precision = 1.0 / PITCHER_COEFFICIENT_PRIOR_SD**2
    lsl_weights = np.bincount(lsl_index, minlength=lsl_count).astype(float)
    platoon_weights = np.bincount(platoon_index, minlength=platoon_count).astype(float)

    def linear_predictor() -> np.ndarray:
        result = intercept + lsl_effect[lsl_index] + batter_effect[batter_index]
        if include_context:
            result = (
                result
                + platoon_effect[platoon_index]
                + pitcher_coefficient * pitcher_residual
            )
        return result

    eta = linear_predictor()
    objective = _binary_objective(
        y,
        eta,
        lsl_effect=lsl_effect,
        batter_effect=batter_effect,
        platoon_effect=platoon_effect,
        pitcher_coefficient=pitcher_coefficient,
        batter_sd=batter_sd,
        include_context=include_context,
    )
    initial_objective = objective
    converged = False
    iterations = 0
    final_max_delta = float("inf")
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        probability = 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))
        residual = y - probability
        curvature = np.maximum(probability * (1.0 - probability), 1e-8)
        intercept_delta = float(residual.sum() / curvature.sum())
        lsl_delta = (
            np.bincount(lsl_index, weights=residual, minlength=lsl_count)
            - lsl_precision * lsl_effect
        ) / (
            np.bincount(lsl_index, weights=curvature, minlength=lsl_count)
            + lsl_precision
        )
        batter_information = np.bincount(
            batter_index, weights=curvature, minlength=batter_count
        )
        batter_delta = (
            np.bincount(batter_index, weights=residual, minlength=batter_count)
            - batter_precision * batter_effect
        ) / (batter_information + batter_precision)
        platoon_delta = np.zeros_like(platoon_effect)
        pitcher_delta = 0.0
        if include_context:
            platoon_delta = (
                np.bincount(platoon_index, weights=residual, minlength=platoon_count)
                - platoon_precision * platoon_effect
            ) / (
                np.bincount(platoon_index, weights=curvature, minlength=platoon_count)
                + platoon_precision
            )
            pitcher_delta = float(
                (
                    np.sum(pitcher_residual * residual)
                    - pitcher_precision
                    * (pitcher_coefficient - PITCHER_COEFFICIENT_PRIOR_MEAN)
                )
                /
                (
                    np.sum(curvature * pitcher_residual**2)
                    + pitcher_precision
                )
            )

        accepted = False
        step = 1.0
        while step >= 2.0**-24:
            candidate_intercept = intercept + step * intercept_delta
            candidate_lsl = lsl_effect + step * lsl_delta
            candidate_lsl -= np.average(candidate_lsl, weights=lsl_weights)
            candidate_batter = batter_effect + step * batter_delta
            candidate_platoon = platoon_effect + step * platoon_delta
            if include_context:
                candidate_platoon -= np.average(
                    candidate_platoon, weights=platoon_weights
                )
            candidate_pitcher = float(
                np.clip(
                    pitcher_coefficient + step * pitcher_delta,
                    *PITCHER_COEFFICIENT_BOUNDS,
                )
            )
            candidate_eta = (
                candidate_intercept
                + candidate_lsl[lsl_index]
                + candidate_batter[batter_index]
            )
            if include_context:
                candidate_eta = (
                    candidate_eta
                    + candidate_platoon[platoon_index]
                    + candidate_pitcher * pitcher_residual
                )
            candidate_objective = _binary_objective(
                y,
                candidate_eta,
                lsl_effect=candidate_lsl,
                batter_effect=candidate_batter,
                platoon_effect=candidate_platoon,
                pitcher_coefficient=candidate_pitcher,
                batter_sd=batter_sd,
                include_context=include_context,
            )
            if candidate_objective <= objective:
                accepted = True
                break
            step *= 0.5
        if not accepted:
            raise ValueError("J0 binary optimizer could not find a descending step")
        final_max_delta = max(
            abs(candidate_intercept - intercept),
            float(np.max(np.abs(candidate_lsl - lsl_effect))),
            float(np.max(np.abs(candidate_batter - batter_effect))),
            float(np.max(np.abs(candidate_platoon - platoon_effect))),
            abs(candidate_pitcher - pitcher_coefficient),
        )
        improvement = objective - candidate_objective
        intercept = candidate_intercept
        lsl_effect = candidate_lsl
        batter_effect = candidate_batter
        platoon_effect = candidate_platoon
        pitcher_coefficient = candidate_pitcher
        eta = candidate_eta
        objective = candidate_objective
        if final_max_delta <= tolerance or improvement / len(y) <= tolerance:
            converged = True
            break
    if not converged:
        raise ValueError("J0 binary optimizer did not converge")
    probability = 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))
    batter_information = np.bincount(
        batter_index,
        weights=np.maximum(probability * (1.0 - probability), 1e-8),
        minlength=batter_count,
    )
    return (
        {
            "intercept": intercept,
            "lsl_effect": lsl_effect,
            "batter_effect": batter_effect,
            "platoon_effect": platoon_effect,
            "pitcher_coefficient": pitcher_coefficient,
            "batter_information": batter_information,
        },
        {
            "converged": True,
            "iterations": iterations,
            "initial_penalized_objective": initial_objective,
            "final_penalized_objective": objective,
            "final_max_parameter_delta": final_max_delta,
            "event_count": len(y),
            "include_context": include_context,
        },
    )


def fit_matched_binary_context_models(
    events: pl.DataFrame,
    node_name: str,
    *,
    max_iterations: int = 500,
    tolerance: float = 1e-8,
    variance_max_iterations: int = 20,
    variance_tolerance: float = 0.01,
) -> BinaryContextFit:
    """Fit matched J0/context-free models on identical rows and fixed penalties.

    The batter SD is estimated from the uncontextual predictor-history likelihood
    by deterministic posterior-second-moment iteration, then frozen identically for
    both fits. This is a Laplace/EM marginal-likelihood implementation, not a
    validation-metric search.
    """

    node = NODE_BY_NAME.get(node_name)
    if node is None:
        raise ValueError(f"unknown J0 binary node: {node_name}")
    required = {
        "player_id",
        "season",
        "league_id",
        "level_group",
        "platoon_cell",
        f"{node.name}_eligible",
        f"{node.name}_response",
        f"{node.name}_prior_pitcher_log_odds_residual",
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"J0 fit input missing fields: {missing}")
    usable = events.filter(pl.col(f"{node.name}_eligible")).select(
        *sorted(required)
    )
    if usable.filter(pl.col(f"{node.name}_response").is_null()).height:
        raise ValueError("eligible J0 binary events contain null responses")
    players = usable["player_id"].to_list()
    lsl_values = list(
        zip(
            usable["season"].to_list(),
            usable["league_id"].to_list(),
            usable["level_group"].to_list(),
            strict=True,
        )
    )
    platoons = usable["platoon_cell"].to_list()
    batter_index, batter_levels = _encode_groups(players)
    lsl_index, lsl_levels = _encode_groups(lsl_values)
    platoon_index, platoon_levels = _encode_groups(platoons)
    y = usable[f"{node.name}_response"].to_numpy().astype(float)
    pitcher_residual = usable[
        f"{node.name}_prior_pitcher_log_odds_residual"
    ].to_numpy()
    if not np.all(np.isfinite(pitcher_residual)):
        raise ValueError("J0 pitcher feature contains nonfinite values")

    batter_sd = 0.35
    variance_iterations = 0
    variance_converged = False
    uncontextual: dict[str, object] | None = None
    uncontextual_metrics: dict[str, object] | None = None
    for iteration in range(1, variance_max_iterations + 1):
        variance_iterations = iteration
        uncontextual, uncontextual_metrics = _fit_binary_map_arrays(
            y=y,
            lsl_index=lsl_index,
            batter_index=batter_index,
            platoon_index=platoon_index,
            pitcher_residual=pitcher_residual,
            batter_sd=batter_sd,
            include_context=False,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )
        effect = np.asarray(uncontextual["batter_effect"], dtype=float)
        information = np.asarray(uncontextual["batter_information"], dtype=float)
        posterior_variance = 1.0 / (information + 1.0 / batter_sd**2)
        moment_update = float(np.sqrt(np.mean(effect**2 + posterior_variance)))
        updated = 0.5 * batter_sd + 0.5 * moment_update
        updated = float(np.clip(updated, *BATTER_EFFECT_SD_BOUNDS))
        relative_change = abs(updated - batter_sd) / max(
            batter_sd, BATTER_EFFECT_SD_BOUNDS[0]
        )
        if relative_change <= variance_tolerance:
            batter_sd = updated
            variance_converged = True
            break
        batter_sd = updated
    if not variance_converged:
        raise ValueError("J0 batter variance marginal-likelihood iteration did not converge")
    uncontextual, uncontextual_metrics = _fit_binary_map_arrays(
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher_residual,
        batter_sd=batter_sd,
        include_context=False,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    contextual, contextual_metrics = _fit_binary_map_arrays(
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher_residual,
        batter_sd=batter_sd,
        include_context=True,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    uncontextual_effect = np.asarray(uncontextual["batter_effect"], dtype=float)
    contextual_effect = np.asarray(contextual["batter_effect"], dtype=float)
    uncontextual_frame = pl.DataFrame(
        {"player_id": batter_levels, "uncontextual_batter_effect": uncontextual_effect}
    )
    contextual_frame = pl.DataFrame(
        {"player_id": batter_levels, "contextual_batter_effect": contextual_effect}
    )
    increments = contextual_frame.join(
        uncontextual_frame, on="player_id", how="inner", validate="1:1"
    ).with_columns(
        (
            pl.col("contextual_batter_effect")
            - pl.col("uncontextual_batter_effect")
        ).alias("context_increment")
    )
    fixed_rows = [
        {
            "effect_type": "pitcher_coefficient",
            "effect_key": node.name,
            "contextual_value": float(contextual["pitcher_coefficient"]),
            "uncontextual_value": 0.0,
        }
    ]
    for key, contextual_value, uncontextual_value in zip(
        lsl_levels,
        np.asarray(contextual["lsl_effect"]),
        np.asarray(uncontextual["lsl_effect"]),
        strict=True,
    ):
        fixed_rows.append(
            {
                "effect_type": "league_season_level",
                "effect_key": "|".join(map(str, key)),
                "contextual_value": float(contextual_value),
                "uncontextual_value": float(uncontextual_value),
            }
        )
    for key, value in zip(
        platoon_levels, np.asarray(contextual["platoon_effect"]), strict=True
    ):
        fixed_rows.append(
            {
                "effect_type": "platoon",
                "effect_key": str(key),
                "contextual_value": float(value),
                "uncontextual_value": 0.0,
            }
        )
    return BinaryContextFit(
        contextual_batter_effects=contextual_frame,
        uncontextual_batter_effects=uncontextual_frame,
        context_increments=increments,
        fixed_effects=pl.DataFrame(fixed_rows),
        metrics={
            "node": node.name,
            "identical_event_rows": True,
            "event_count": usable.height,
            "player_count": len(batter_levels),
            "league_season_level_count": len(lsl_levels),
            "platoon_cell_count": len(platoon_levels),
            "batter_effect_sd": batter_sd,
            "batter_variance_method": "deterministic_laplace_em_marginal_likelihood",
            "batter_variance_iterations": variance_iterations,
            "batter_variance_converged": True,
            "uncontextual": uncontextual_metrics,
            "contextual": contextual_metrics,
        },
    )


def _multinomial_probabilities(logits: np.ndarray) -> np.ndarray:
    full = np.column_stack((np.zeros(len(logits)), logits))
    shifted = full - np.max(full, axis=1, keepdims=True)
    weights = np.exp(shifted)
    return weights / weights.sum(axis=1, keepdims=True)


def _multinomial_objective(
    y: np.ndarray,
    logits: np.ndarray,
    *,
    lsl_effect: np.ndarray,
    batter_effect: np.ndarray,
    platoon_effect: np.ndarray,
    pitcher_coefficient: np.ndarray,
    batter_sd: float,
    include_context: bool,
) -> float:
    probability = _multinomial_probabilities(logits)
    value = float(-np.log(np.clip(probability[np.arange(len(y)), y], 1e-12, 1.0)).sum())
    value += 0.5 * float(np.sum((lsl_effect / LSL_PRIOR_SD) ** 2))
    value += 0.5 * float(np.sum((batter_effect / batter_sd) ** 2))
    if include_context:
        value += 0.5 * float(np.sum((platoon_effect / PLATOON_PRIOR_SD) ** 2))
        value += 0.5 * float(
            np.sum(
                (
                    (pitcher_coefficient - PITCHER_COEFFICIENT_PRIOR_MEAN)
                    / PITCHER_COEFFICIENT_PRIOR_SD
                )
                ** 2
            )
        )
    return value


def _fit_multinomial_map_arrays(
    *,
    y: np.ndarray,
    lsl_index: np.ndarray,
    batter_index: np.ndarray,
    platoon_index: np.ndarray,
    pitcher_residual: np.ndarray,
    batter_sd: float,
    include_context: bool,
    max_iterations: int,
    tolerance: float,
) -> tuple[dict[str, object], dict[str, object]]:
    """Fit the 2B/3B additive-log-ratio surface with 1B as reference."""

    category_count = 2
    lsl_count = int(lsl_index.max()) + 1
    batter_count = int(batter_index.max()) + 1
    platoon_count = int(platoon_index.max()) + 1
    observed = np.bincount(y, minlength=3).astype(float) + 0.5
    intercept = np.log(observed[1:] / observed[0])
    lsl_effect = np.zeros((lsl_count, category_count), dtype=float)
    batter_effect = np.zeros((batter_count, category_count), dtype=float)
    platoon_effect = np.zeros((platoon_count, category_count), dtype=float)
    pitcher_coefficient = np.full(
        category_count,
        PITCHER_COEFFICIENT_PRIOR_MEAN if include_context else 0.0,
    )
    lsl_precision = 1.0 / LSL_PRIOR_SD**2
    batter_precision = 1.0 / batter_sd**2
    platoon_precision = 1.0 / PLATOON_PRIOR_SD**2
    pitcher_precision = 1.0 / PITCHER_COEFFICIENT_PRIOR_SD**2
    lsl_weights = np.bincount(lsl_index, minlength=lsl_count).astype(float)
    platoon_weights = np.bincount(platoon_index, minlength=platoon_count).astype(float)

    def predictor() -> np.ndarray:
        value = intercept + lsl_effect[lsl_index] + batter_effect[batter_index]
        if include_context:
            value = (
                value
                + platoon_effect[platoon_index]
                + pitcher_coefficient[None, :] * pitcher_residual
            )
        return value

    logits = predictor()
    objective = _multinomial_objective(
        y,
        logits,
        lsl_effect=lsl_effect,
        batter_effect=batter_effect,
        platoon_effect=platoon_effect,
        pitcher_coefficient=pitcher_coefficient,
        batter_sd=batter_sd,
        include_context=include_context,
    )
    initial_objective = objective
    converged = False
    final_max_delta = float("inf")
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        probability = _multinomial_probabilities(logits)
        residual = np.column_stack(
            ((y == 1).astype(float) - probability[:, 1],
             (y == 2).astype(float) - probability[:, 2])
        )
        curvature = np.maximum(probability[:, 1:] * (1.0 - probability[:, 1:]), 1e-8)
        intercept_delta = residual.sum(axis=0) / curvature.sum(axis=0)
        lsl_delta = np.zeros_like(lsl_effect)
        batter_delta = np.zeros_like(batter_effect)
        platoon_delta = np.zeros_like(platoon_effect)
        pitcher_delta = np.zeros_like(pitcher_coefficient)
        batter_information = np.zeros_like(batter_effect)
        for category in range(category_count):
            lsl_delta[:, category] = (
                np.bincount(lsl_index, weights=residual[:, category], minlength=lsl_count)
                - lsl_precision * lsl_effect[:, category]
            ) / (
                np.bincount(lsl_index, weights=curvature[:, category], minlength=lsl_count)
                + lsl_precision
            )
            batter_information[:, category] = np.bincount(
                batter_index, weights=curvature[:, category], minlength=batter_count
            )
            batter_delta[:, category] = (
                np.bincount(batter_index, weights=residual[:, category], minlength=batter_count)
                - batter_precision * batter_effect[:, category]
            ) / (batter_information[:, category] + batter_precision)
            if include_context:
                platoon_delta[:, category] = (
                    np.bincount(platoon_index, weights=residual[:, category], minlength=platoon_count)
                    - platoon_precision * platoon_effect[:, category]
                ) / (
                    np.bincount(platoon_index, weights=curvature[:, category], minlength=platoon_count)
                    + platoon_precision
                )
                feature = pitcher_residual[:, category]
                pitcher_delta[category] = (
                    np.sum(feature * residual[:, category])
                    - pitcher_precision
                    * (pitcher_coefficient[category] - PITCHER_COEFFICIENT_PRIOR_MEAN)
                ) / (
                    np.sum(curvature[:, category] * feature**2) + pitcher_precision
                )

        step = 1.0
        accepted = False
        while step >= 2.0**-24:
            candidate_intercept = intercept + step * intercept_delta
            candidate_lsl = lsl_effect + step * lsl_delta
            for category in range(category_count):
                candidate_lsl[:, category] -= np.average(
                    candidate_lsl[:, category], weights=lsl_weights
                )
            candidate_batter = batter_effect + step * batter_delta
            candidate_platoon = platoon_effect + step * platoon_delta
            if include_context:
                for category in range(category_count):
                    candidate_platoon[:, category] -= np.average(
                        candidate_platoon[:, category], weights=platoon_weights
                    )
            candidate_pitcher = np.clip(
                pitcher_coefficient + step * pitcher_delta,
                *PITCHER_COEFFICIENT_BOUNDS,
            )
            candidate_logits = (
                candidate_intercept
                + candidate_lsl[lsl_index]
                + candidate_batter[batter_index]
            )
            if include_context:
                candidate_logits = (
                    candidate_logits
                    + candidate_platoon[platoon_index]
                    + candidate_pitcher[None, :] * pitcher_residual
                )
            candidate_objective = _multinomial_objective(
                y,
                candidate_logits,
                lsl_effect=candidate_lsl,
                batter_effect=candidate_batter,
                platoon_effect=candidate_platoon,
                pitcher_coefficient=candidate_pitcher,
                batter_sd=batter_sd,
                include_context=include_context,
            )
            if candidate_objective <= objective:
                accepted = True
                break
            step *= 0.5
        if not accepted:
            raise ValueError("J0 multinomial optimizer could not find a descending step")
        final_max_delta = max(
            float(np.max(np.abs(candidate_intercept - intercept))),
            float(np.max(np.abs(candidate_lsl - lsl_effect))),
            float(np.max(np.abs(candidate_batter - batter_effect))),
            float(np.max(np.abs(candidate_platoon - platoon_effect))),
            float(np.max(np.abs(candidate_pitcher - pitcher_coefficient))),
        )
        improvement = objective - candidate_objective
        intercept = candidate_intercept
        lsl_effect = candidate_lsl
        batter_effect = candidate_batter
        platoon_effect = candidate_platoon
        pitcher_coefficient = candidate_pitcher
        logits = candidate_logits
        objective = candidate_objective
        if final_max_delta <= tolerance or improvement / len(y) <= tolerance:
            converged = True
            break
    if not converged:
        raise ValueError("J0 multinomial optimizer did not converge")
    probability = _multinomial_probabilities(logits)
    information = np.zeros_like(batter_effect)
    for category in range(category_count):
        information[:, category] = np.bincount(
            batter_index,
            weights=np.maximum(
                probability[:, category + 1] * (1.0 - probability[:, category + 1]),
                1e-8,
            ),
            minlength=batter_count,
        )
    return (
        {
            "intercept": intercept,
            "lsl_effect": lsl_effect,
            "batter_effect": batter_effect,
            "platoon_effect": platoon_effect,
            "pitcher_coefficient": pitcher_coefficient,
            "batter_information": information,
        },
        {
            "converged": True,
            "iterations": iterations,
            "initial_penalized_objective": initial_objective,
            "final_penalized_objective": objective,
            "final_max_parameter_delta": final_max_delta,
            "event_count": len(y),
            "include_context": include_context,
        },
    )


def fit_matched_hit_composition_context_models(
    events: pl.DataFrame,
    *,
    max_iterations: int = 500,
    tolerance: float = 1e-8,
    variance_max_iterations: int = 20,
    variance_tolerance: float = 0.01,
) -> MultinomialContextFit:
    """Fit matched 1B/2B/3B J0 models on one immutable event cohort."""

    required = {
        "player_id",
        "season",
        "league_id",
        "level_group",
        "platoon_cell",
        "HIT_COMPOSITION_eligible",
        "HIT_COMPOSITION_response",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_2B",
        "HIT_COMPOSITION_prior_pitcher_alr_residual_3B",
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"J0 hit-composition input missing fields: {missing}")
    usable = events.filter(pl.col("HIT_COMPOSITION_eligible")).select(*sorted(required))
    if usable.filter(pl.col("HIT_COMPOSITION_response").is_null()).height:
        raise ValueError("eligible hit-composition events contain null responses")
    players = usable["player_id"].to_list()
    lsl_values = list(zip(
        usable["season"].to_list(),
        usable["league_id"].to_list(),
        usable["level_group"].to_list(),
        strict=True,
    ))
    platoons = usable["platoon_cell"].to_list()
    batter_index, batter_levels = _encode_groups(players)
    lsl_index, lsl_levels = _encode_groups(lsl_values)
    platoon_index, platoon_levels = _encode_groups(platoons)
    category = {"1B": 0, "2B": 1, "3B": 2}
    y = np.asarray([category[str(value)] for value in usable["HIT_COMPOSITION_response"]], dtype=np.int64)
    pitcher_residual = np.column_stack((
        usable["HIT_COMPOSITION_prior_pitcher_alr_residual_2B"].to_numpy(),
        usable["HIT_COMPOSITION_prior_pitcher_alr_residual_3B"].to_numpy(),
    ))
    if not np.all(np.isfinite(pitcher_residual)):
        raise ValueError("hit-composition pitcher features contain nonfinite values")

    batter_sd = 0.35
    variance_converged = False
    variance_iterations = 0
    for iteration in range(1, variance_max_iterations + 1):
        variance_iterations = iteration
        fit, _ = _fit_multinomial_map_arrays(
            y=y, lsl_index=lsl_index, batter_index=batter_index,
            platoon_index=platoon_index, pitcher_residual=pitcher_residual,
            batter_sd=batter_sd, include_context=False,
            max_iterations=max_iterations, tolerance=tolerance,
        )
        effect = np.asarray(fit["batter_effect"], dtype=float)
        information = np.asarray(fit["batter_information"], dtype=float)
        posterior_variance = 1.0 / (information + 1.0 / batter_sd**2)
        moment_update = float(np.sqrt(np.mean(effect**2 + posterior_variance)))
        updated = 0.5 * batter_sd + 0.5 * moment_update
        updated = float(np.clip(updated, *BATTER_EFFECT_SD_BOUNDS))
        relative_change = abs(updated - batter_sd) / max(
            batter_sd, BATTER_EFFECT_SD_BOUNDS[0]
        )
        if relative_change <= variance_tolerance:
            batter_sd = updated
            variance_converged = True
            break
        batter_sd = updated
    if not variance_converged:
        raise ValueError(
            "hit-composition batter variance iteration did not converge: "
            f"sd={batter_sd}, update={updated}, moment={moment_update}"
        )
    uncontextual, uncontextual_metrics = _fit_multinomial_map_arrays(
        y=y, lsl_index=lsl_index, batter_index=batter_index,
        platoon_index=platoon_index, pitcher_residual=pitcher_residual,
        batter_sd=batter_sd, include_context=False,
        max_iterations=max_iterations, tolerance=tolerance,
    )
    contextual, contextual_metrics = _fit_multinomial_map_arrays(
        y=y, lsl_index=lsl_index, batter_index=batter_index,
        platoon_index=platoon_index, pitcher_residual=pitcher_residual,
        batter_sd=batter_sd, include_context=True,
        max_iterations=max_iterations, tolerance=tolerance,
    )
    uncontextual_effect = np.asarray(uncontextual["batter_effect"])
    contextual_effect = np.asarray(contextual["batter_effect"])
    uncontextual_frame = pl.DataFrame({
        "player_id": batter_levels,
        "uncontextual_batter_effect_2B": uncontextual_effect[:, 0],
        "uncontextual_batter_effect_3B": uncontextual_effect[:, 1],
    })
    contextual_frame = pl.DataFrame({
        "player_id": batter_levels,
        "contextual_batter_effect_2B": contextual_effect[:, 0],
        "contextual_batter_effect_3B": contextual_effect[:, 1],
    })
    increments = contextual_frame.join(
        uncontextual_frame, on="player_id", how="inner", validate="1:1"
    ).with_columns(
        (pl.col("contextual_batter_effect_2B") - pl.col("uncontextual_batter_effect_2B")).alias("context_increment_2B"),
        (pl.col("contextual_batter_effect_3B") - pl.col("uncontextual_batter_effect_3B")).alias("context_increment_3B"),
    )
    fixed_rows: list[dict[str, object]] = []
    for category_index, category_name in enumerate(("2B", "3B")):
        fixed_rows.append({
            "effect_type": "pitcher_coefficient",
            "effect_key": category_name,
            "contextual_value": float(np.asarray(contextual["pitcher_coefficient"])[category_index]),
            "uncontextual_value": 0.0,
        })
        for key, contextual_value, uncontextual_value in zip(
            lsl_levels,
            np.asarray(contextual["lsl_effect"])[:, category_index],
            np.asarray(uncontextual["lsl_effect"])[:, category_index],
            strict=True,
        ):
            fixed_rows.append({
                "effect_type": f"league_season_level_{category_name}",
                "effect_key": "|".join(map(str, key)),
                "contextual_value": float(contextual_value),
                "uncontextual_value": float(uncontextual_value),
            })
        for key, value in zip(
            platoon_levels,
            np.asarray(contextual["platoon_effect"])[:, category_index],
            strict=True,
        ):
            fixed_rows.append({
                "effect_type": f"platoon_{category_name}",
                "effect_key": str(key),
                "contextual_value": float(value),
                "uncontextual_value": 0.0,
            })
    return MultinomialContextFit(
        contextual_batter_effects=contextual_frame,
        uncontextual_batter_effects=uncontextual_frame,
        context_increments=increments,
        fixed_effects=pl.DataFrame(fixed_rows),
        metrics={
            "node": "HIT_COMPOSITION",
            "reference_category": "1B",
            "identical_event_rows": True,
            "event_count": usable.height,
            "player_count": len(batter_levels),
            "league_season_level_count": len(lsl_levels),
            "platoon_cell_count": len(platoon_levels),
            "batter_effect_sd": batter_sd,
            "batter_variance_method": "deterministic_laplace_em_marginal_likelihood",
            "batter_variance_iterations": variance_iterations,
            "batter_variance_converged": True,
            "uncontextual": uncontextual_metrics,
            "contextual": contextual_metrics,
        },
    )


def _logit(probability: float) -> float:
    value = min(max(float(probability), PROBABILITY_FLOOR), 1.0 - PROBABILITY_FLOOR)
    return log(value) - log(1.0 - value)


def _logistic(value: float) -> float:
    if value >= 0.0:
        inverse = exp(-value)
        return 1.0 / (1.0 + inverse)
    exponential = exp(value)
    return exponential / (1.0 + exponential)


def apply_j0_context_increment(
    base_probabilities: Mapping[str, float],
    increments: Mapping[str, float] | None,
) -> dict[str, float]:
    """Apply frozen J0 nested-node increments, with exact missing/zero fallback."""

    base = {outcome: float(base_probabilities[outcome]) for outcome in HITTER_TALENT_OUTCOMES}
    validate_probability_vector(base, tolerance=1e-10)
    if increments is None:
        return dict(base)
    unknown = sorted(set(increments) - {*NODE_BY_NAME, "HIT_2B", "HIT_3B"})
    if unknown:
        raise ValueError(f"unknown J0 context increments: {unknown}")
    values = {name: float(increments.get(name, 0.0)) for name in NODE_BY_NAME}
    values.update(
        {
            "HIT_2B": float(increments.get("HIT_2B", 0.0)),
            "HIT_3B": float(increments.get("HIT_3B", 0.0)),
        }
    )
    if any(not isfinite(value) for value in values.values()):
        raise ValueError("J0 context increments must be finite")
    if all(value == 0.0 for value in values.values()):
        return dict(base)

    conditionals = nested_conditionals(base)
    for node in BINARY_CONTEXT_NODES:
        probability = conditionals[node.nested_node][node.positive_child]
        adjusted = _logistic(_logit(probability) + values[node.name])
        conditionals[node.nested_node] = {
            node.positive_child: adjusted,
            **{
                child: 1.0 - adjusted
                for child in conditionals[node.nested_node]
                if child != node.positive_child
            },
        }

    hit = conditionals["hit_in_play"]
    logits = {
        "1B": log(max(hit["1B"], PROBABILITY_FLOOR)),
        "2B": log(max(hit["2B"], PROBABILITY_FLOOR)) + values["HIT_2B"],
        "3B": log(max(hit["3B"], PROBABILITY_FLOOR)) + values["HIT_3B"],
    }
    maximum = max(logits.values())
    weights = {child: exp(value - maximum) for child, value in logits.items()}
    total = sum(weights.values())
    conditionals["hit_in_play"] = {
        child: weight / total for child, weight in weights.items()
    }
    result = assemble_nested_probabilities(conditionals)
    validate_probability_vector(result, tolerance=1e-10)
    return result
