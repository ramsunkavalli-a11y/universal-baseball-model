"""Target-free Stage 2e J0R fixed-information contextual model."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2d import (
    BATTER_EFFECT_SD_BOUNDS,
    LSL_PRIOR_SD,
    NODE_BY_NAME,
    PITCHER_COEFFICIENT_BOUNDS,
    PITCHER_COEFFICIENT_PRIOR_MEAN,
    PITCHER_COEFFICIENT_PRIOR_SD,
    PLATOON_PRIOR_SD,
    apply_j0_context_increment,
)


RATE_FLOOR = 1e-6
MAX_ITERATIONS = 500
TOLERANCE = 1e-8
MINIMUM_STEP = 2.0**-24


class Stage2eFitError(ValueError):
    """A node/phase-specific failure with a durable-ready trace."""

    def __init__(
        self, node: str, phase: str, message: str, trace: list[dict[str, object]]
    ) -> None:
        super().__init__(f"{node} {phase}: {message}")
        self.node = node
        self.phase = phase
        self.trace = trace


@dataclass(frozen=True, slots=True)
class Stage2eNodeFit:
    """One matched contextual/uncontextual component fit."""

    node: str
    context_increments: pl.DataFrame
    contextual_batter_effects: pl.DataFrame
    uncontextual_batter_effects: pl.DataFrame
    fixed_effects: pl.DataFrame
    diagnostics: dict[str, object]


def derive_binary_batter_sd(rate: float, prior_pa: float) -> float:
    """Map frozen prior information to a logit-scale Gaussian SD."""

    if not isfinite(rate) or not isfinite(prior_pa) or prior_pa <= 0.0:
        raise ValueError("binary shrinkage inputs must be finite and positive")
    probability = float(np.clip(rate, RATE_FLOOR, 1.0 - RATE_FLOOR))
    value = np.sqrt(1.0 / (prior_pa * probability * (1.0 - probability)))
    return float(np.clip(value, *BATTER_EFFECT_SD_BOUNDS))


def derive_hit_composition_batter_sd(
    shares: Mapping[str, float], prior_pa: float
) -> np.ndarray:
    """Return fixed ALR SDs for 2B/3B versus the 1B reference."""

    if prior_pa <= 0.0 or not isfinite(prior_pa):
        raise ValueError("hit-composition prior PA must be finite and positive")
    if set(shares) != {"1B", "2B", "3B"}:
        raise ValueError("hit-composition shares must contain 1B, 2B, and 3B")
    raw = np.asarray([float(shares[key]) for key in ("1B", "2B", "3B")])
    if not np.all(np.isfinite(raw)) or np.any(raw < 0.0) or raw.sum() <= 0.0:
        raise ValueError("hit-composition shares must be finite and nonnegative")
    probabilities = np.maximum(raw, RATE_FLOOR)
    probabilities /= probabilities.sum()
    result = np.sqrt(
        1.0 / (prior_pa * probabilities[1:]) + 1.0 / (prior_pa * probabilities[0])
    )
    return np.clip(result, *BATTER_EFFECT_SD_BOUNDS)


def _encode(values: list[object]) -> tuple[np.ndarray, list[object]]:
    levels: list[object] = []
    lookup: dict[object, int] = {}
    encoded = np.empty(len(values), dtype=np.int64)
    for index, value in enumerate(values):
        if value not in lookup:
            lookup[value] = len(levels)
            levels.append(value)
        encoded[index] = lookup[value]
    return encoded, levels


def _logistic(eta: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))


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
    probability = _logistic(eta)
    value = float(
        -(
            y * np.log(np.clip(probability, 1e-12, 1.0))
            + (1.0 - y) * np.log(np.clip(1.0 - probability, 1e-12, 1.0))
        ).sum()
    )
    value += 0.5 * float(np.sum((lsl_effect / LSL_PRIOR_SD) ** 2))
    value += 0.5 * float(np.sum((batter_effect / batter_sd) ** 2))
    if include_context:
        value += 0.5 * float(np.sum((platoon_effect / PLATOON_PRIOR_SD) ** 2))
        value += (
            0.5
            * (
                (pitcher_coefficient - PITCHER_COEFFICIENT_PRIOR_MEAN)
                / PITCHER_COEFFICIENT_PRIOR_SD
            )
            ** 2
        )
    return value


def _fit_binary(
    *,
    node: str,
    phase: str,
    y: np.ndarray,
    lsl_index: np.ndarray,
    batter_index: np.ndarray,
    platoon_index: np.ndarray,
    pitcher_residual: np.ndarray,
    batter_sd: float,
    include_context: bool,
    max_iterations: int = MAX_ITERATIONS,
    tolerance: float = TOLERANCE,
) -> tuple[dict[str, object], dict[str, object]]:
    lsl_count = int(lsl_index.max()) + 1
    batter_count = int(batter_index.max()) + 1
    platoon_count = int(platoon_index.max()) + 1
    mean = float(np.clip(y.mean(), RATE_FLOOR, 1.0 - RATE_FLOOR))
    intercept = float(np.log(mean / (1.0 - mean)))
    lsl_effect = np.zeros(lsl_count)
    batter_effect = np.zeros(batter_count)
    platoon_effect = np.zeros(platoon_count)
    pitcher_coefficient = PITCHER_COEFFICIENT_PRIOR_MEAN if include_context else 0.0
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
                + pitcher_coefficient * pitcher_residual
            )
        return value

    eta = predictor()
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
    trace: list[dict[str, object]] = []
    convergence_reason: str | None = None
    for iteration in range(1, max_iterations + 1):
        probability = _logistic(eta)
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
        batter_delta = (
            np.bincount(batter_index, weights=residual, minlength=batter_count)
            - batter_precision * batter_effect
        ) / (
            np.bincount(batter_index, weights=curvature, minlength=batter_count)
            + batter_precision
        )
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
                / (np.sum(curvature * pitcher_residual**2) + pitcher_precision)
            )

        step = 1.0
        accepted = False
        while step >= MINIMUM_STEP:
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
            raise Stage2eFitError(node, phase, "no descending step", trace)
        maximum_change = max(
            abs(candidate_intercept - intercept),
            float(np.max(np.abs(candidate_lsl - lsl_effect))),
            float(np.max(np.abs(candidate_batter - batter_effect))),
            float(np.max(np.abs(candidate_platoon - platoon_effect))),
            abs(candidate_pitcher - pitcher_coefficient),
        )
        improvement = objective - candidate_objective
        trace.append(
            {
                "iteration": iteration,
                "penalized_objective": float(candidate_objective),
                "per_event_objective_improvement": float(improvement / len(y)),
                "maximum_parameter_change": maximum_change,
                "accepted_step_size": step,
            }
        )
        intercept = candidate_intercept
        lsl_effect = candidate_lsl
        batter_effect = candidate_batter
        platoon_effect = candidate_platoon
        pitcher_coefficient = candidate_pitcher
        eta = candidate_eta
        objective = candidate_objective
        if maximum_change <= tolerance:
            convergence_reason = "parameter_tolerance"
            break
        if improvement / len(y) <= tolerance:
            convergence_reason = "per_event_objective_tolerance"
            break
    if convergence_reason is None:
        raise Stage2eFitError(node, phase, "maximum iterations exceeded", trace)
    if not all(
        np.all(np.isfinite(value))
        for value in (lsl_effect, batter_effect, platoon_effect)
    ):
        raise Stage2eFitError(node, phase, "nonfinite fitted effect", trace)
    return (
        {
            "intercept": intercept,
            "lsl_effect": lsl_effect,
            "batter_effect": batter_effect,
            "platoon_effect": platoon_effect,
            "pitcher_coefficient": pitcher_coefficient,
        },
        {
            "converged": True,
            "convergence_reason": convergence_reason,
            "iterations": len(trace),
            "initial_penalized_objective": initial_objective,
            "final_penalized_objective": objective,
            "trace": trace,
            "include_context": include_context,
        },
    )


def fit_matched_binary_j0r(
    events: pl.DataFrame,
    node_name: str,
    *,
    max_iterations: int = MAX_ITERATIONS,
    tolerance: float = TOLERANCE,
) -> Stage2eNodeFit:
    """Fit one fixed-shrinkage matched binary J0R component."""

    node = NODE_BY_NAME.get(node_name)
    if node is None:
        raise ValueError(f"unknown Stage 2e binary node: {node_name}")
    columns = {
        "player_id",
        "season",
        "league_id",
        "level_group",
        "platoon_cell",
        f"{node_name}_eligible",
        f"{node_name}_response",
        f"{node_name}_prior_pitcher_log_odds_residual",
    }
    missing = sorted(columns - set(events.columns))
    if missing:
        raise ValueError(f"Stage 2e input missing columns: {missing}")
    usable = events.filter(pl.col(f"{node_name}_eligible")).select(*sorted(columns))
    y = usable[f"{node_name}_response"].to_numpy().astype(float)
    if len(y) == 0 or not np.all(np.isfinite(y)):
        raise ValueError("Stage 2e binary response is empty or nonfinite")
    batter_sd = derive_binary_batter_sd(float(y.mean()), node.prior_pa)
    players = usable["player_id"].to_list()
    lsl = list(
        zip(
            usable["season"].to_list(),
            usable["league_id"].to_list(),
            usable["level_group"].to_list(),
            strict=True,
        )
    )
    batter_index, batter_levels = _encode(players)
    lsl_index, lsl_levels = _encode(lsl)
    platoon_index, platoon_levels = _encode(usable["platoon_cell"].to_list())
    pitcher = usable[f"{node_name}_prior_pitcher_log_odds_residual"].to_numpy()
    uncontextual, uncontextual_diagnostics = _fit_binary(
        node=node_name,
        phase="uncontextual",
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher,
        batter_sd=batter_sd,
        include_context=False,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    contextual, contextual_diagnostics = _fit_binary(
        node=node_name,
        phase="contextual",
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher,
        batter_sd=batter_sd,
        include_context=True,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    uncontextual_frame = pl.DataFrame(
        {
            "player_id": batter_levels,
            "uncontextual_batter_effect": uncontextual["batter_effect"],
        }
    )
    contextual_frame = pl.DataFrame(
        {
            "player_id": batter_levels,
            "contextual_batter_effect": contextual["batter_effect"],
        }
    )
    increments = contextual_frame.join(
        uncontextual_frame, on="player_id", how="inner", validate="1:1"
    ).with_columns(
        (
            pl.col("contextual_batter_effect") - pl.col("uncontextual_batter_effect")
        ).alias("context_increment")
    )
    fixed_rows = [
        {
            "effect_type": "pitcher_coefficient",
            "effect_key": node_name,
            "contextual_value": float(contextual["pitcher_coefficient"]),
            "uncontextual_value": 0.0,
        }
    ]
    for key, c_value, u_value in zip(
        lsl_levels,
        np.asarray(contextual["lsl_effect"]),
        np.asarray(uncontextual["lsl_effect"]),
        strict=True,
    ):
        fixed_rows.append(
            {
                "effect_type": "league_season_level",
                "effect_key": "|".join(map(str, key)),
                "contextual_value": float(c_value),
                "uncontextual_value": float(u_value),
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
    return Stage2eNodeFit(
        node=node_name,
        context_increments=increments,
        contextual_batter_effects=contextual_frame,
        uncontextual_batter_effects=uncontextual_frame,
        fixed_effects=pl.DataFrame(fixed_rows),
        diagnostics={
            "node": node_name,
            "event_count": usable.height,
            "player_count": len(batter_levels),
            "league_season_level_count": len(lsl_levels),
            "platoon_cell_count": len(platoon_levels),
            "pooled_rate": float(y.mean()),
            "prior_pa": node.prior_pa,
            "derived_batter_sd": batter_sd,
            "identical_event_rows": True,
            "uncontextual": uncontextual_diagnostics,
            "contextual": contextual_diagnostics,
        },
    )


def certify_grouped_event_binary_equivalence(
    events: pl.DataFrame,
    node_name: str,
    *,
    tolerance: float = 1e-7,
) -> dict[str, float]:
    """Compare exact event and grouped sufficient-statistic uncontextual fits."""

    node = NODE_BY_NAME[node_name]
    usable = events.filter(pl.col(f"{node_name}_eligible"))
    y = usable[f"{node_name}_response"].to_numpy().astype(float)
    batter_index, _ = _encode(usable["player_id"].to_list())
    lsl_index, _ = _encode(
        list(
            zip(
                usable["season"].to_list(),
                usable["league_id"].to_list(),
                usable["level_group"].to_list(),
                strict=True,
            )
        )
    )
    platoon_index, _ = _encode(usable["platoon_cell"].to_list())
    pitcher = usable[f"{node_name}_prior_pitcher_log_odds_residual"].to_numpy()
    batter_sd = derive_binary_batter_sd(float(y.mean()), node.prior_pa)
    event_fit, event_diagnostics = _fit_binary(
        node=node_name,
        phase="event_equivalence",
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher,
        batter_sd=batter_sd,
        include_context=False,
        tolerance=tolerance,
    )

    pairs = np.column_stack((lsl_index, batter_index))
    unique_pairs, inverse = np.unique(pairs, axis=0, return_inverse=True)
    trials = np.bincount(inverse).astype(float)
    successes = np.bincount(inverse, weights=y).astype(float)
    grouped_lsl = unique_pairs[:, 0]
    grouped_batter = unique_pairs[:, 1]
    lsl_count = int(lsl_index.max()) + 1
    batter_count = int(batter_index.max()) + 1
    mean = float(np.clip(y.mean(), RATE_FLOOR, 1.0 - RATE_FLOOR))
    intercept = float(np.log(mean / (1.0 - mean)))
    lsl_effect = np.zeros(lsl_count)
    batter_effect = np.zeros(batter_count)
    lsl_precision = 1.0 / LSL_PRIOR_SD**2
    batter_precision = 1.0 / batter_sd**2
    lsl_weights = np.bincount(lsl_index, minlength=lsl_count).astype(float)
    objective = float("inf")
    grouped_iterations = 0
    for iteration in range(1, MAX_ITERATIONS + 1):
        grouped_iterations = iteration
        eta = intercept + lsl_effect[grouped_lsl] + batter_effect[grouped_batter]
        probability = _logistic(eta)
        residual = successes - trials * probability
        curvature = np.maximum(trials * probability * (1.0 - probability), 1e-8)
        intercept_delta = float(residual.sum() / curvature.sum())
        lsl_delta = (
            np.bincount(grouped_lsl, weights=residual, minlength=lsl_count)
            - lsl_precision * lsl_effect
        ) / (
            np.bincount(grouped_lsl, weights=curvature, minlength=lsl_count)
            + lsl_precision
        )
        batter_delta = (
            np.bincount(grouped_batter, weights=residual, minlength=batter_count)
            - batter_precision * batter_effect
        ) / (
            np.bincount(grouped_batter, weights=curvature, minlength=batter_count)
            + batter_precision
        )
        step = 1.0
        while step >= MINIMUM_STEP:
            candidate_intercept = intercept + step * intercept_delta
            candidate_lsl = lsl_effect + step * lsl_delta
            candidate_lsl -= np.average(candidate_lsl, weights=lsl_weights)
            candidate_batter = batter_effect + step * batter_delta
            candidate_eta = (
                candidate_intercept
                + candidate_lsl[grouped_lsl]
                + candidate_batter[grouped_batter]
            )
            candidate_probability = _logistic(candidate_eta)
            candidate_objective = float(
                -(
                    successes * np.log(np.clip(candidate_probability, 1e-12, 1.0))
                    + (trials - successes)
                    * np.log(np.clip(1.0 - candidate_probability, 1e-12, 1.0))
                ).sum()
                + 0.5 * np.sum((candidate_lsl / LSL_PRIOR_SD) ** 2)
                + 0.5 * np.sum((candidate_batter / batter_sd) ** 2)
            )
            current_eta = (
                intercept + lsl_effect[grouped_lsl] + batter_effect[grouped_batter]
            )
            current_probability = _logistic(current_eta)
            current_objective = float(
                -(
                    successes * np.log(np.clip(current_probability, 1e-12, 1.0))
                    + (trials - successes)
                    * np.log(np.clip(1.0 - current_probability, 1e-12, 1.0))
                ).sum()
                + 0.5 * np.sum((lsl_effect / LSL_PRIOR_SD) ** 2)
                + 0.5 * np.sum((batter_effect / batter_sd) ** 2)
            )
            if candidate_objective <= current_objective:
                break
            step *= 0.5
        maximum_change = max(
            abs(candidate_intercept - intercept),
            float(np.max(np.abs(candidate_lsl - lsl_effect))),
            float(np.max(np.abs(candidate_batter - batter_effect))),
        )
        improvement = current_objective - candidate_objective
        intercept = candidate_intercept
        lsl_effect = candidate_lsl
        batter_effect = candidate_batter
        objective = candidate_objective
        if maximum_change <= tolerance or improvement / len(y) <= tolerance:
            break
    return {
        "intercept_max_abs_delta": abs(float(event_fit["intercept"]) - intercept),
        "lsl_max_abs_delta": float(
            np.max(np.abs(np.asarray(event_fit["lsl_effect"]) - lsl_effect))
        ),
        "batter_max_abs_delta": float(
            np.max(np.abs(np.asarray(event_fit["batter_effect"]) - batter_effect))
        ),
        "objective_abs_delta": abs(
            float(event_diagnostics["final_penalized_objective"]) - objective
        ),
        "event_iterations": float(event_diagnostics["iterations"]),
        "grouped_iterations": float(grouped_iterations),
    }


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
    batter_sd: np.ndarray,
    include_context: bool,
) -> float:
    probability = _multinomial_probabilities(logits)
    value = float(-np.log(np.clip(probability[np.arange(len(y)), y], 1e-12, 1.0)).sum())
    value += 0.5 * float(np.sum((lsl_effect / LSL_PRIOR_SD) ** 2))
    value += 0.5 * float(np.sum((batter_effect / batter_sd[None, :]) ** 2))
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


def _fit_multinomial(
    *,
    phase: str,
    y: np.ndarray,
    lsl_index: np.ndarray,
    batter_index: np.ndarray,
    platoon_index: np.ndarray,
    pitcher_residual: np.ndarray,
    batter_sd: np.ndarray,
    include_context: bool,
    max_iterations: int = MAX_ITERATIONS,
    tolerance: float = TOLERANCE,
) -> tuple[dict[str, object], dict[str, object]]:
    node = "HIT_COMPOSITION"
    category_count = 2
    lsl_count = int(lsl_index.max()) + 1
    batter_count = int(batter_index.max()) + 1
    platoon_count = int(platoon_index.max()) + 1
    observed = np.bincount(y, minlength=3).astype(float) + 0.5
    intercept = np.log(observed[1:] / observed[0])
    lsl_effect = np.zeros((lsl_count, category_count))
    batter_effect = np.zeros((batter_count, category_count))
    platoon_effect = np.zeros((platoon_count, category_count))
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
    trace: list[dict[str, object]] = []
    convergence_reason: str | None = None
    for iteration in range(1, max_iterations + 1):
        probability = _multinomial_probabilities(logits)
        residual = np.column_stack(
            (
                (y == 1).astype(float) - probability[:, 1],
                (y == 2).astype(float) - probability[:, 2],
            )
        )
        curvature = np.maximum(probability[:, 1:] * (1.0 - probability[:, 1:]), 1e-8)
        intercept_delta = residual.sum(axis=0) / curvature.sum(axis=0)
        lsl_delta = np.zeros_like(lsl_effect)
        batter_delta = np.zeros_like(batter_effect)
        platoon_delta = np.zeros_like(platoon_effect)
        pitcher_delta = np.zeros_like(pitcher_coefficient)
        for category in range(category_count):
            lsl_delta[:, category] = (
                np.bincount(
                    lsl_index, weights=residual[:, category], minlength=lsl_count
                )
                - lsl_precision * lsl_effect[:, category]
            ) / (
                np.bincount(
                    lsl_index, weights=curvature[:, category], minlength=lsl_count
                )
                + lsl_precision
            )
            batter_delta[:, category] = (
                np.bincount(
                    batter_index,
                    weights=residual[:, category],
                    minlength=batter_count,
                )
                - batter_precision[category] * batter_effect[:, category]
            ) / (
                np.bincount(
                    batter_index,
                    weights=curvature[:, category],
                    minlength=batter_count,
                )
                + batter_precision[category]
            )
            if include_context:
                platoon_delta[:, category] = (
                    np.bincount(
                        platoon_index,
                        weights=residual[:, category],
                        minlength=platoon_count,
                    )
                    - platoon_precision * platoon_effect[:, category]
                ) / (
                    np.bincount(
                        platoon_index,
                        weights=curvature[:, category],
                        minlength=platoon_count,
                    )
                    + platoon_precision
                )
                feature = pitcher_residual[:, category]
                pitcher_delta[category] = (
                    np.sum(feature * residual[:, category])
                    - pitcher_precision
                    * (pitcher_coefficient[category] - PITCHER_COEFFICIENT_PRIOR_MEAN)
                ) / (np.sum(curvature[:, category] * feature**2) + pitcher_precision)
        step = 1.0
        accepted = False
        while step >= MINIMUM_STEP:
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
            raise Stage2eFitError(node, phase, "no descending step", trace)
        maximum_change = max(
            float(np.max(np.abs(candidate_intercept - intercept))),
            float(np.max(np.abs(candidate_lsl - lsl_effect))),
            float(np.max(np.abs(candidate_batter - batter_effect))),
            float(np.max(np.abs(candidate_platoon - platoon_effect))),
            float(np.max(np.abs(candidate_pitcher - pitcher_coefficient))),
        )
        improvement = objective - candidate_objective
        trace.append(
            {
                "iteration": iteration,
                "penalized_objective": float(candidate_objective),
                "per_event_objective_improvement": float(improvement / len(y)),
                "maximum_parameter_change": maximum_change,
                "accepted_step_size": step,
            }
        )
        intercept = candidate_intercept
        lsl_effect = candidate_lsl
        batter_effect = candidate_batter
        platoon_effect = candidate_platoon
        pitcher_coefficient = candidate_pitcher
        logits = candidate_logits
        objective = candidate_objective
        if maximum_change <= tolerance:
            convergence_reason = "parameter_tolerance"
            break
        if improvement / len(y) <= tolerance:
            convergence_reason = "per_event_objective_tolerance"
            break
    if convergence_reason is None:
        raise Stage2eFitError(node, phase, "maximum iterations exceeded", trace)
    return (
        {
            "intercept": intercept,
            "lsl_effect": lsl_effect,
            "batter_effect": batter_effect,
            "platoon_effect": platoon_effect,
            "pitcher_coefficient": pitcher_coefficient,
        },
        {
            "converged": True,
            "convergence_reason": convergence_reason,
            "iterations": len(trace),
            "initial_penalized_objective": initial_objective,
            "final_penalized_objective": objective,
            "trace": trace,
            "include_context": include_context,
        },
    )


def fit_matched_hit_composition_j0r(
    events: pl.DataFrame,
    *,
    max_iterations: int = MAX_ITERATIONS,
    tolerance: float = TOLERANCE,
) -> Stage2eNodeFit:
    """Fit fixed-information 1B-reference hit-composition contrasts."""

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
        raise ValueError(f"Stage 2e hit-composition input missing: {missing}")
    usable = events.filter(pl.col("HIT_COMPOSITION_eligible")).select(*sorted(required))
    category = {"1B": 0, "2B": 1, "3B": 2}
    labels = [str(value) for value in usable["HIT_COMPOSITION_response"]]
    y = np.asarray([category[value] for value in labels], dtype=np.int64)
    counts = np.bincount(y, minlength=3).astype(float)
    shares = dict(zip(("1B", "2B", "3B"), counts / counts.sum(), strict=True))
    batter_sd = derive_hit_composition_batter_sd(shares, 800.0)
    batter_index, batter_levels = _encode(usable["player_id"].to_list())
    lsl_index, lsl_levels = _encode(
        list(
            zip(
                usable["season"].to_list(),
                usable["league_id"].to_list(),
                usable["level_group"].to_list(),
                strict=True,
            )
        )
    )
    platoon_index, platoon_levels = _encode(usable["platoon_cell"].to_list())
    pitcher = np.column_stack(
        (
            usable["HIT_COMPOSITION_prior_pitcher_alr_residual_2B"].to_numpy(),
            usable["HIT_COMPOSITION_prior_pitcher_alr_residual_3B"].to_numpy(),
        )
    )
    uncontextual, u_diagnostics = _fit_multinomial(
        phase="uncontextual",
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher,
        batter_sd=batter_sd,
        include_context=False,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    contextual, c_diagnostics = _fit_multinomial(
        phase="contextual",
        y=y,
        lsl_index=lsl_index,
        batter_index=batter_index,
        platoon_index=platoon_index,
        pitcher_residual=pitcher,
        batter_sd=batter_sd,
        include_context=True,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    u_effect = np.asarray(uncontextual["batter_effect"])
    c_effect = np.asarray(contextual["batter_effect"])
    u_frame = pl.DataFrame(
        {
            "player_id": batter_levels,
            "uncontextual_batter_effect_2B": u_effect[:, 0],
            "uncontextual_batter_effect_3B": u_effect[:, 1],
        }
    )
    c_frame = pl.DataFrame(
        {
            "player_id": batter_levels,
            "contextual_batter_effect_2B": c_effect[:, 0],
            "contextual_batter_effect_3B": c_effect[:, 1],
        }
    )
    increments = c_frame.join(u_frame, on="player_id", validate="1:1").with_columns(
        (
            pl.col("contextual_batter_effect_2B")
            - pl.col("uncontextual_batter_effect_2B")
        ).alias("context_increment_2B"),
        (
            pl.col("contextual_batter_effect_3B")
            - pl.col("uncontextual_batter_effect_3B")
        ).alias("context_increment_3B"),
    )
    fixed_rows: list[dict[str, object]] = []
    for index, contrast in enumerate(("2B", "3B")):
        fixed_rows.append(
            {
                "effect_type": "pitcher_coefficient",
                "effect_key": contrast,
                "contextual_value": float(contextual["pitcher_coefficient"][index]),
                "uncontextual_value": 0.0,
            }
        )
        for key, c_value, u_value in zip(
            lsl_levels,
            np.asarray(contextual["lsl_effect"])[:, index],
            np.asarray(uncontextual["lsl_effect"])[:, index],
            strict=True,
        ):
            fixed_rows.append(
                {
                    "effect_type": f"league_season_level_{contrast}",
                    "effect_key": "|".join(map(str, key)),
                    "contextual_value": float(c_value),
                    "uncontextual_value": float(u_value),
                }
            )
        for key, value in zip(
            platoon_levels,
            np.asarray(contextual["platoon_effect"])[:, index],
            strict=True,
        ):
            fixed_rows.append(
                {
                    "effect_type": f"platoon_{contrast}",
                    "effect_key": str(key),
                    "contextual_value": float(value),
                    "uncontextual_value": 0.0,
                }
            )
    return Stage2eNodeFit(
        node="HIT_COMPOSITION",
        context_increments=increments,
        contextual_batter_effects=c_frame,
        uncontextual_batter_effects=u_frame,
        fixed_effects=pl.DataFrame(fixed_rows),
        diagnostics={
            "node": "HIT_COMPOSITION",
            "event_count": usable.height,
            "player_count": len(batter_levels),
            "league_season_level_count": len(lsl_levels),
            "platoon_cell_count": len(platoon_levels),
            "pooled_shares": shares,
            "prior_pa": 800.0,
            "derived_batter_sd": batter_sd.tolist(),
            "identical_event_rows": True,
            "uncontextual": u_diagnostics,
            "contextual": c_diagnostics,
        },
    )


def apply_j0r_to_predictions(
    base: pl.DataFrame,
    fits: Mapping[str, Stage2eNodeFit],
    *,
    model_id: str = "J0R_FIXED_INFORMATION_SHRINKAGE",
) -> pl.DataFrame:
    """Apply player context increments to B1, retaining exact missing fallback."""

    expected = {*NODE_BY_NAME, "HIT_COMPOSITION"}
    if set(fits) != expected:
        raise ValueError("Stage 2e fit collection is incomplete")
    augmented = base
    increment_columns: list[str] = []
    for node in NODE_BY_NAME:
        name = f"increment_{node}"
        augmented = augmented.join(
            fits[node].context_increments.select(
                "player_id", pl.col("context_increment").alias(name)
            ),
            on="player_id",
            how="left",
            validate="1:1",
        )
        increment_columns.append(name)
    augmented = augmented.join(
        fits["HIT_COMPOSITION"].context_increments.select(
            "player_id",
            pl.col("context_increment_2B").alias("increment_HIT_2B"),
            pl.col("context_increment_3B").alias("increment_HIT_3B"),
        ),
        on="player_id",
        how="left",
        validate="1:1",
    )
    increment_columns.extend(("increment_HIT_2B", "increment_HIT_3B"))
    rows: list[dict[str, object]] = []
    for row in augmented.iter_rows(named=True):
        probabilities = {
            outcome: float(row[f"p_{outcome}"]) for outcome in HITTER_TALENT_OUTCOMES
        }
        increments = {
            column.removeprefix("increment_"): float(row[column] or 0.0)
            for column in increment_columns
        }
        adjusted = apply_j0_context_increment(probabilities, increments)
        output = {
            key: value
            for key, value in row.items()
            if key not in increment_columns and not key.startswith("p_")
        }
        output.update({f"p_{key}": value for key, value in adjusted.items()})
        output["model_id"] = model_id
        rows.append(output)
    return pl.DataFrame(rows)
