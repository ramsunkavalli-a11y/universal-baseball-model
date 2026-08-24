"""Pre-registered Hitter v2 Stage 2b calibration and contact-shape residuals.

The module contains estimator primitives only. It has no protected-source
loader, promotion rule, leaderboard, or WAR assembly.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from collections.abc import Callable
from typing import Mapping, Sequence

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_model import NESTED_NODES
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.performance_season import CONTACT_CORE_BINS


FIXED_MEAN_LOSS_L2_PENALTY = 0.01
FIXED_SHAPE_HALF_LIFE_SEASONS = 2.0
FIXED_SHAPE_PRIOR_EVENTS = 200.0
FIXED_SHAPE_RELIABILITY_K = 200.0
# This ceiling governs numerical completion only; objective convergence still
# stops the deterministic optimizer, usually long before the ceiling.
DEFAULT_MAX_ITERATIONS = 20_000
DEFAULT_GRADIENT_TOLERANCE = 1e-8
DEFAULT_OBJECTIVE_TOLERANCE = 1e-12
MIN_BACKTRACK_STEP = 2.0**-30
ARMIJO_FRACTION = 1e-4

TRAJECTORY_GROUP_MAP = {
    "IFFB": "IFFB",
    "PULL_OFFB": "OFFB",
    "CENTER_OFFB": "OFFB",
    "OPPO_OFFB": "OFFB",
    "PULL_LD": "LD",
    "CENTER_LD": "LD",
    "OPPO_LD": "LD",
    "PULL_GB": "GB",
    "CENTER_GB": "GB",
    "OPPO_GB": "GB",
}
TRAJECTORY_GROUPS = ("IFFB", "OFFB", "LD", "GB")
DIRECTION_TRAJECTORY_GROUPS = CONTACT_CORE_BINS
SHAPE_AFFECTED_NODES = (
    "contact",
    "non_hr_contact",
    "reach",
    "hit_in_play",
    "non_hit_reach",
    "non_reach",
)


@dataclass(frozen=True, slots=True)
class NodeOffsetFit:
    """A complete node-offset coefficient surface plus fit diagnostics."""

    coefficients: pl.DataFrame
    metrics: dict[str, object]


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=1, keepdims=True)
    exponentiated = np.exp(shifted)
    return exponentiated / np.sum(exponentiated, axis=1, keepdims=True)


def _leaf_values(values: Mapping[str, object], *, prefix: str = "") -> dict[str, float]:
    result = {
        outcome: float(values[f"{prefix}{outcome}"])
        for outcome in HITTER_TALENT_OUTCOMES
    }
    validate_probability_vector(result, tolerance=1e-9)
    return result


def _branch_values(leaves: Mapping[str, float]) -> dict[str, float]:
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


def nested_conditionals(
    probabilities: Mapping[str, float],
) -> dict[str, dict[str, float]]:
    """Decompose one terminal simplex into the frozen nested conditionals."""

    validate_probability_vector(probabilities, tolerance=1e-9)
    branches = _branch_values(probabilities)
    result: dict[str, dict[str, float]] = {}
    for node in NESTED_NODES:
        denominator = sum(branches[child] for child in node.children)
        if denominator <= 0.0:
            result[node.name] = {
                child: 1.0 / len(node.children) for child in node.children
            }
        else:
            result[node.name] = {
                child: branches[child] / denominator for child in node.children
            }
    return result


def assemble_nested_probabilities(
    conditionals: Mapping[str, Mapping[str, float]],
) -> dict[str, float]:
    """Assemble a coherent terminal simplex from complete node conditionals."""

    expected = {node.name for node in NESTED_NODES}
    if set(conditionals) != expected:
        raise ValueError("nested conditional nodes are incomplete")
    for node in NESTED_NODES:
        values = conditionals[node.name]
        if set(values) != set(node.children):
            raise ValueError(f"nested conditional children differ for {node.name}")
        if any(not isfinite(float(value)) or float(value) < 0 for value in values.values()):
            raise ValueError("nested conditionals must be finite and nonnegative")
        if abs(sum(float(value) for value in values.values()) - 1.0) > 1e-9:
            raise ValueError("nested conditionals must sum to one")

    p = conditionals
    non_k = p["plate_appearance"]["NON_K"]
    non_ubb = non_k * p["non_k"]["NON_UBB"]
    contact = non_ubb * p["non_k_non_ubb"]["CONTACT"]
    non_hr = contact * p["contact"]["NON_HR"]
    reach = non_hr * p["non_hr_contact"]["REACH"]
    hit = reach * p["reach"]["HIT"]
    non_hit_reach = reach * p["reach"]["NON_HIT_REACH"]
    non_reach = non_hr * p["non_hr_contact"]["NON_REACH"]
    result = {
        "K": p["plate_appearance"]["K"],
        "UBB": non_k * p["non_k"]["UBB"],
        "HBP": non_ubb * p["non_k_non_ubb"]["HBP"],
        "HR": contact * p["contact"]["HR"],
        **{
            outcome: hit * p["hit_in_play"][outcome]
            for outcome in ("1B", "2B", "3B")
        },
        **{
            outcome: non_hit_reach * p["non_hit_reach"][outcome]
            for outcome in ("ROE", "FC_REACH")
        },
        **{
            outcome: non_reach * p["non_reach"][outcome]
            for outcome in ("SF", "MULTI_OUT", "OTHER_OUT")
        },
    }
    validate_probability_vector(result, tolerance=1e-9)
    return result


def _node_training_arrays(
    origin_pairs: Sequence[tuple[pl.DataFrame, pl.DataFrame]],
) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    probabilities: dict[str, list[list[float]]] = {
        node.name: [] for node in NESTED_NODES
    }
    counts: dict[str, list[list[float]]] = {
        node.name: [] for node in NESTED_NODES
    }
    for prediction, target in origin_pairs:
        joined = target.join(prediction, on="player_id", how="inner")
        for row in joined.iter_rows(named=True):
            leaf_probability = {
                outcome: float(row[f"p_{outcome}"])
                for outcome in HITTER_TALENT_OUTCOMES
            }
            conditional = nested_conditionals(leaf_probability)
            leaf_counts = {
                outcome: float(row[outcome]) for outcome in HITTER_TALENT_OUTCOMES
            }
            branch_counts = _branch_values(leaf_counts)
            for node in NESTED_NODES:
                node_counts = [branch_counts[child] for child in node.children]
                if sum(node_counts) <= 0.0:
                    continue
                probabilities[node.name].append(
                    [conditional[node.name][child] for child in node.children]
                )
                counts[node.name].append(node_counts)
    result: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for node in NESTED_NODES:
        if probabilities[node.name]:
            result[node.name] = (
                np.asarray(probabilities[node.name], dtype=float),
                np.asarray(counts[node.name], dtype=float),
            )
    return result


def _calibration_objective_gradient(
    probability: np.ndarray,
    counts: np.ndarray,
    parameters: np.ndarray,
    *,
    l2_penalty: float,
) -> tuple[float, float, np.ndarray]:
    log_probability = np.log(np.clip(probability, 1e-12, 1.0))
    alpha = parameters[:, 0]
    beta = parameters[:, 1]
    fitted = _softmax(alpha[None, :] + log_probability * beta[None, :])
    total = float(np.sum(counts))
    mean_nll = float(-np.sum(counts * np.log(np.clip(fitted, 1e-12, 1.0))) / total)
    anchor = np.column_stack((np.zeros(len(alpha)), np.ones(len(beta))))
    delta = parameters - anchor
    penalty = 0.5 * l2_penalty * float(np.mean(delta**2))
    residual = np.sum(counts, axis=1, keepdims=True) * fitted - counts
    gradient = np.column_stack(
        (
            np.sum(residual, axis=0) / total,
            np.sum(residual * log_probability, axis=0) / total,
        )
    ) + l2_penalty * delta / delta.size
    return mean_nll + penalty, mean_nll, gradient


def _fit_with_backtracking(
    objective_gradient: Callable[[np.ndarray], tuple[float, float, np.ndarray]],
    initial: np.ndarray,
    *,
    max_iterations: int,
    gradient_tolerance: float,
    objective_tolerance: float,
) -> tuple[np.ndarray, dict[str, object]]:
    parameters = initial.copy()
    objective, mean_nll, gradient = objective_gradient(parameters)
    initial_objective = float(objective)
    initial_mean_nll = float(mean_nll)
    converged = False
    iterations = 0
    for iteration in range(1, max_iterations + 1):
        iterations = iteration
        gradient_max = float(np.max(np.abs(gradient)))
        if gradient_max <= gradient_tolerance:
            converged = True
            break
        squared_norm = float(np.sum(gradient**2))
        step = 1.0
        accepted = False
        while step >= MIN_BACKTRACK_STEP:
            candidate = parameters - step * gradient
            candidate_objective, candidate_nll, candidate_gradient = objective_gradient(
                candidate
            )
            if candidate_objective <= objective - ARMIJO_FRACTION * step * squared_norm:
                accepted = True
                break
            step *= 0.5
        if not accepted:
            raise ValueError("node-offset optimizer could not find a descending step")
        improvement = float(objective - candidate_objective)
        parameters = candidate
        objective = float(candidate_objective)
        mean_nll = float(candidate_nll)
        gradient = candidate_gradient
        if improvement <= objective_tolerance:
            converged = True
            break
    if not converged:
        raise ValueError("node-offset optimizer did not converge")
    return parameters, {
        "converged": True,
        "iterations": iterations,
        "initial_mean_log_loss": initial_mean_nll,
        "final_mean_log_loss": float(mean_nll),
        "initial_penalized_objective": initial_objective,
        "final_penalized_objective": float(objective),
        "final_gradient_max_abs": float(np.max(np.abs(gradient))),
    }


def identity_node_calibration() -> NodeOffsetFit:
    """Return the exact identity calibration used when no prior origin exists."""

    rows = [
        {
            "node": node.name,
            "child": child,
            "alpha": 0.0,
            "beta": 1.0,
        }
        for node in NESTED_NODES
        for child in node.children
    ]
    return NodeOffsetFit(
        coefficients=pl.DataFrame(rows).sort("node", "child"),
        metrics={
            "fit_origin_count": 0,
            "identity_fallback": True,
            "fixed_mean_loss_l2_penalty": FIXED_MEAN_LOSS_L2_PENALTY,
        },
    )


def fit_node_calibration(
    origin_pairs: Sequence[tuple[pl.DataFrame, pl.DataFrame]],
    *,
    l2_penalty: float = FIXED_MEAN_LOSS_L2_PENALTY,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    gradient_tolerance: float = DEFAULT_GRADIENT_TOLERANCE,
    objective_tolerance: float = DEFAULT_OBJECTIVE_TOLERANCE,
) -> NodeOffsetFit:
    """Fit identity-anchored node calibration on strictly earlier origins."""

    if not origin_pairs:
        return identity_node_calibration()
    if l2_penalty != FIXED_MEAN_LOSS_L2_PENALTY:
        raise ValueError("Stage 2b calibration penalty is frozen at 0.01")
    arrays = _node_training_arrays(origin_pairs)
    rows: list[dict[str, object]] = []
    node_metrics: dict[str, object] = {}
    for node in NESTED_NODES:
        if node.name not in arrays:
            raise ValueError(f"calibration origin lacks node events: {node.name}")
        probability, counts = arrays[node.name]
        initial = np.column_stack(
            (np.zeros(len(node.children)), np.ones(len(node.children)))
        )
        fitted, metrics = _fit_with_backtracking(
            lambda parameters: _calibration_objective_gradient(
                probability, counts, parameters, l2_penalty=l2_penalty
            ),
            initial,
            max_iterations=max_iterations,
            gradient_tolerance=gradient_tolerance,
            objective_tolerance=objective_tolerance,
        )
        node_metrics[node.name] = {
            **metrics,
            "training_rows": len(probability),
            "training_events": int(np.sum(counts)),
        }
        for index, child in enumerate(node.children):
            rows.append(
                {
                    "node": node.name,
                    "child": child,
                    "alpha": float(fitted[index, 0]),
                    "beta": float(fitted[index, 1]),
                }
            )
    return NodeOffsetFit(
        coefficients=pl.DataFrame(rows).sort("node", "child"),
        metrics={
            "fit_origin_count": len(origin_pairs),
            "identity_fallback": False,
            "fixed_mean_loss_l2_penalty": l2_penalty,
            "nodes": node_metrics,
        },
    )


def apply_node_calibration(
    predictions: pl.DataFrame,
    fit: NodeOffsetFit,
    *,
    model_id: str = "D0_NODE_CALIBRATED_C0",
) -> pl.DataFrame:
    """Apply a complete calibration surface to a prediction table."""

    if bool(fit.metrics.get("identity_fallback", False)):
        return predictions.with_columns(
            pl.lit(model_id).alias("model_id"),
            pl.lit(True).alias("calibration_identity_fallback"),
        )

    coefficient_map = {
        (str(row["node"]), str(row["child"])): (
            float(row["alpha"]),
            float(row["beta"]),
        )
        for row in fit.coefficients.iter_rows(named=True)
    }
    expected = {
        (node.name, child) for node in NESTED_NODES for child in node.children
    }
    if set(coefficient_map) != expected:
        raise ValueError("node calibration coefficients are incomplete")
    rows: list[dict[str, object]] = []
    for row in predictions.sort("player_id").iter_rows(named=True):
        leaves = {
            outcome: float(row[f"p_{outcome}"])
            for outcome in HITTER_TALENT_OUTCOMES
        }
        conditional = nested_conditionals(leaves)
        adjusted: dict[str, dict[str, float]] = {}
        for node in NESTED_NODES:
            logits = []
            for child in node.children:
                alpha, beta = coefficient_map[(node.name, child)]
                logits.append(
                    alpha + beta * log(max(conditional[node.name][child], 1e-12))
                )
            probability = _softmax(np.asarray([logits], dtype=float))[0]
            adjusted[node.name] = {
                child: float(probability[index])
                for index, child in enumerate(node.children)
            }
        result = assemble_nested_probabilities(adjusted)
        rows.append(
            {
                **row,
                "model_id": model_id,
                "calibration_identity_fallback": bool(
                    fit.metrics.get("identity_fallback", False)
                ),
                **{
                    f"p_{outcome}": result[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)


def _shape_groups(mode: str) -> tuple[tuple[str, ...], Mapping[str, str]]:
    if mode == "trajectory":
        return TRAJECTORY_GROUPS, TRAJECTORY_GROUP_MAP
    if mode == "direction_trajectory":
        return DIRECTION_TRAJECTORY_GROUPS, {
            value: value for value in DIRECTION_TRAJECTORY_GROUPS
        }
    raise ValueError(f"unsupported Stage 2b shape mode: {mode}")


def build_shape_features(
    shape_history: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    mode: str,
) -> pl.DataFrame:
    """Build chronology-safe, shrunk, reliability-weighted shape log ratios."""

    groups, group_map = _shape_groups(mode)
    required = {
        "season",
        "league_id",
        "player_id",
        "level_group",
        "core_bin",
        "occurrence_count",
    }
    missing = sorted(required - set(shape_history.columns))
    if missing:
        raise ValueError(f"shape history is missing columns: {missing}")
    allowed = (
        shape_history.filter(
            (pl.col("season") <= predictor_cutoff_season)
            & pl.col("core_bin").is_in(list(CONTACT_CORE_BINS))
        )
        .with_columns(
            pl.col("core_bin").replace_strict(group_map).alias("shape_group"),
            (
                0.5
                ** (
                    (pl.lit(predictor_cutoff_season) - pl.col("season"))
                    / pl.lit(FIXED_SHAPE_HALF_LIFE_SEASONS)
                )
            ).alias("recency_weight"),
        )
        .with_columns(
            (pl.col("occurrence_count") * pl.col("recency_weight")).alias(
                "weighted_count"
            )
        )
    )
    if allowed.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64,
                "shape_mode": pl.String,
                "shape_evidence_events": pl.Float64,
                "shape_reliability": pl.Float64,
                "shape_latest_season": pl.Int64,
                "shape_latest_league_id": pl.Int64,
                "shape_latest_level_group": pl.String,
                **{f"shape_feature_{group}": pl.Float64 for group in groups},
            }
        )

    player_set = set(int(value) for value in player_ids)
    player_counts = (
        allowed.filter(pl.col("player_id").is_in(sorted(player_set)))
        .group_by("player_id", "shape_group")
        .agg(pl.col("weighted_count").sum())
    )
    contexts = (
        allowed.filter(pl.col("player_id").is_in(sorted(player_set)))
        .group_by("player_id", "season", "league_id", "level_group")
        .agg(pl.col("occurrence_count").sum().alias("context_events"))
        .sort(
            "player_id",
            "season",
            "context_events",
            "league_id",
            descending=[False, True, True, False],
        )
        .group_by("player_id", maintain_order=True)
        .first()
    )
    priors = (
        allowed.group_by("season", "league_id", "level_group", "shape_group")
        .agg(pl.col("occurrence_count").sum().alias("prior_count"))
    )
    prior_map = {
        (
            int(row["season"]),
            int(row["league_id"]),
            str(row["level_group"]),
            str(row["shape_group"]),
        ): float(row["prior_count"])
        for row in priors.iter_rows(named=True)
    }
    count_map = {
        (int(row["player_id"]), str(row["shape_group"])): float(
            row["weighted_count"]
        )
        for row in player_counts.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for context in contexts.iter_rows(named=True):
        player_id = int(context["player_id"])
        season = int(context["season"])
        league_id = int(context["league_id"])
        level = str(context["level_group"])
        counts = np.asarray(
            [count_map.get((player_id, group), 0.0) for group in groups], dtype=float
        )
        prior_counts = np.asarray(
            [
                prior_map.get((season, league_id, level, group), 0.0)
                for group in groups
            ],
            dtype=float,
        )
        if np.any(prior_counts <= 0.0):
            raise ValueError("shape context lacks positive support for every group")
        evidence = float(np.sum(counts))
        if evidence <= 0.0:
            continue
        prior_probability = prior_counts / np.sum(prior_counts)
        posterior = (
            counts + FIXED_SHAPE_PRIOR_EVENTS * prior_probability
        ) / (evidence + FIXED_SHAPE_PRIOR_EVENTS)
        log_ratio = np.log(posterior / prior_probability)
        centered = log_ratio - np.mean(log_ratio)
        reliability = evidence / (evidence + FIXED_SHAPE_RELIABILITY_K)
        features = reliability * centered
        rows.append(
            {
                "player_id": player_id,
                "shape_mode": mode,
                "shape_evidence_events": evidence,
                "shape_reliability": reliability,
                "shape_latest_season": season,
                "shape_latest_league_id": league_id,
                "shape_latest_level_group": level,
                **{
                    f"shape_feature_{group}": float(features[index])
                    for index, group in enumerate(groups)
                },
            }
        )
    schema = {
        "player_id": pl.Int64,
        "shape_mode": pl.String,
        "shape_evidence_events": pl.Float64,
        "shape_reliability": pl.Float64,
        "shape_latest_season": pl.Int64,
        "shape_latest_league_id": pl.Int64,
        "shape_latest_level_group": pl.String,
        **{f"shape_feature_{group}": pl.Float64 for group in groups},
    }
    return (
        pl.DataFrame(rows, schema=schema)
        if rows
        else pl.DataFrame(schema=schema)
    )


def _shape_training_arrays(
    origin_examples: Sequence[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]],
    *,
    mode: str,
) -> dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    groups, _ = _shape_groups(mode)
    features_by_node: dict[str, list[list[float]]] = {
        node: [] for node in SHAPE_AFFECTED_NODES
    }
    probabilities_by_node: dict[str, list[list[float]]] = {
        node: [] for node in SHAPE_AFFECTED_NODES
    }
    counts_by_node: dict[str, list[list[float]]] = {
        node: [] for node in SHAPE_AFFECTED_NODES
    }
    feature_columns = [f"shape_feature_{group}" for group in groups]
    for prediction, target, features in origin_examples:
        joined = target.join(prediction, on="player_id", how="inner").join(
            features, on="player_id", how="inner"
        )
        for row in joined.iter_rows(named=True):
            leaf_probability = {
                outcome: float(row[f"p_{outcome}"])
                for outcome in HITTER_TALENT_OUTCOMES
            }
            conditional = nested_conditionals(leaf_probability)
            branch_counts = _branch_values(
                {
                    outcome: float(row[outcome])
                    for outcome in HITTER_TALENT_OUTCOMES
                }
            )
            feature = [float(row[column]) for column in feature_columns]
            for node_name in SHAPE_AFFECTED_NODES:
                node = next(value for value in NESTED_NODES if value.name == node_name)
                node_counts = [branch_counts[child] for child in node.children]
                if sum(node_counts) <= 0.0:
                    continue
                features_by_node[node_name].append(feature)
                probabilities_by_node[node_name].append(
                    [conditional[node_name][child] for child in node.children]
                )
                counts_by_node[node_name].append(node_counts)
    return {
        node: (
            np.asarray(probabilities_by_node[node], dtype=float),
            np.asarray(counts_by_node[node], dtype=float),
            np.asarray(features_by_node[node], dtype=float),
        )
        for node in SHAPE_AFFECTED_NODES
        if features_by_node[node]
    }


def _residual_objective_gradient(
    probability: np.ndarray,
    counts: np.ndarray,
    features: np.ndarray,
    coefficients: np.ndarray,
    *,
    l2_penalty: float,
) -> tuple[float, float, np.ndarray]:
    logits = np.log(np.clip(probability, 1e-12, 1.0)) + features @ coefficients.T
    fitted = _softmax(logits)
    total = float(np.sum(counts))
    mean_nll = float(-np.sum(counts * np.log(np.clip(fitted, 1e-12, 1.0))) / total)
    penalty = 0.5 * l2_penalty * float(np.mean(coefficients**2))
    residual = np.sum(counts, axis=1, keepdims=True) * fitted - counts
    gradient = (residual.T @ features) / total
    gradient += l2_penalty * coefficients / coefficients.size
    return mean_nll + penalty, mean_nll, gradient


def zero_shape_residual(mode: str) -> NodeOffsetFit:
    """Return an exact zero shape residual for the no-prior-origin fold."""

    groups, _ = _shape_groups(mode)
    rows = [
        {
            "node": node.name,
            "child": child,
            "feature": group,
            "coefficient": 0.0,
        }
        for node in NESTED_NODES
        if node.name in SHAPE_AFFECTED_NODES
        for child in node.children
        for group in groups
    ]
    return NodeOffsetFit(
        coefficients=pl.DataFrame(rows).sort("node", "child", "feature"),
        metrics={
            "shape_mode": mode,
            "fit_origin_count": 0,
            "zero_residual_fallback": True,
            "fixed_mean_loss_l2_penalty": FIXED_MEAN_LOSS_L2_PENALTY,
        },
    )


def fit_shape_residual(
    origin_examples: Sequence[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]],
    *,
    mode: str,
    l2_penalty: float = FIXED_MEAN_LOSS_L2_PENALTY,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    gradient_tolerance: float = DEFAULT_GRADIENT_TOLERANCE,
    objective_tolerance: float = DEFAULT_OBJECTIVE_TOLERANCE,
) -> NodeOffsetFit:
    """Fit a fixed-penalty contact-node offset using earlier shape evidence."""

    groups, _ = _shape_groups(mode)
    if not origin_examples:
        return zero_shape_residual(mode)
    if l2_penalty != FIXED_MEAN_LOSS_L2_PENALTY:
        raise ValueError("Stage 2b shape-residual penalty is frozen at 0.01")
    arrays = _shape_training_arrays(origin_examples, mode=mode)
    rows: list[dict[str, object]] = []
    node_metrics: dict[str, object] = {}
    for node in NESTED_NODES:
        if node.name not in SHAPE_AFFECTED_NODES:
            continue
        if node.name not in arrays:
            raise ValueError(f"shape origins lack node events: {node.name}")
        probability, counts, features = arrays[node.name]
        initial = np.zeros((len(node.children), len(groups)), dtype=float)
        fitted, metrics = _fit_with_backtracking(
            lambda coefficients: _residual_objective_gradient(
                probability,
                counts,
                features,
                coefficients,
                l2_penalty=l2_penalty,
            ),
            initial,
            max_iterations=max_iterations,
            gradient_tolerance=gradient_tolerance,
            objective_tolerance=objective_tolerance,
        )
        node_metrics[node.name] = {
            **metrics,
            "training_rows": len(probability),
            "training_events": int(np.sum(counts)),
        }
        for child_index, child in enumerate(node.children):
            for feature_index, group in enumerate(groups):
                rows.append(
                    {
                        "node": node.name,
                        "child": child,
                        "feature": group,
                        "coefficient": float(fitted[child_index, feature_index]),
                    }
                )
    return NodeOffsetFit(
        coefficients=pl.DataFrame(rows).sort("node", "child", "feature"),
        metrics={
            "shape_mode": mode,
            "fit_origin_count": len(origin_examples),
            "zero_residual_fallback": False,
            "fixed_mean_loss_l2_penalty": l2_penalty,
            "nodes": node_metrics,
        },
    )


def apply_shape_residual(
    predictions: pl.DataFrame,
    features: pl.DataFrame,
    fit: NodeOffsetFit,
    *,
    model_id: str,
) -> pl.DataFrame:
    """Apply a shape residual with exact base fallback for unsupported players."""

    mode = str(fit.metrics["shape_mode"])
    groups, _ = _shape_groups(mode)
    if bool(fit.metrics.get("zero_residual_fallback", False)):
        evidence = features.select(
            "player_id", "shape_evidence_events", "shape_reliability"
        )
        return (
            predictions.join(evidence, on="player_id", how="left")
            .with_columns(
                pl.lit(model_id).alias("model_id"),
                pl.lit(mode).alias("shape_mode"),
                pl.col("shape_evidence_events").fill_null(0.0),
                pl.col("shape_reliability").fill_null(0.0),
                pl.when(pl.col("shape_evidence_events") > 0.0)
                .then(pl.lit(None, dtype=pl.String))
                .otherwise(pl.lit("missing_shape_evidence"))
                .alias("shape_fallback_reason"),
            )
        )
    coefficient_map = {
        (str(row["node"]), str(row["child"]), str(row["feature"])): float(
            row["coefficient"]
        )
        for row in fit.coefficients.iter_rows(named=True)
    }
    expected = {
        (node.name, child, group)
        for node in NESTED_NODES
        if node.name in SHAPE_AFFECTED_NODES
        for child in node.children
        for group in groups
    }
    if set(coefficient_map) != expected:
        raise ValueError("shape residual coefficients are incomplete")
    feature_map = {
        int(row["player_id"]): row for row in features.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for row in predictions.sort("player_id").iter_rows(named=True):
        player_id = int(row["player_id"])
        feature_row = feature_map.get(player_id)
        leaves = {
            outcome: float(row[f"p_{outcome}"])
            for outcome in HITTER_TALENT_OUTCOMES
        }
        if feature_row is None:
            rows.append(
                {
                    **row,
                    "model_id": model_id,
                    "shape_mode": mode,
                    "shape_evidence_events": 0.0,
                    "shape_reliability": 0.0,
                    "shape_fallback_reason": "missing_shape_evidence",
                }
            )
            continue
        conditional = nested_conditionals(leaves)
        adjusted = {node: dict(values) for node, values in conditional.items()}
        vector = np.asarray(
            [float(feature_row[f"shape_feature_{group}"]) for group in groups],
            dtype=float,
        )
        for node in NESTED_NODES:
            if node.name not in SHAPE_AFFECTED_NODES:
                continue
            logits = []
            for child in node.children:
                increment = sum(
                    coefficient_map[(node.name, child, group)] * vector[index]
                    for index, group in enumerate(groups)
                )
                logits.append(log(max(conditional[node.name][child], 1e-12)) + increment)
            probability = _softmax(np.asarray([logits], dtype=float))[0]
            adjusted[node.name] = {
                child: float(probability[index])
                for index, child in enumerate(node.children)
            }
        result = assemble_nested_probabilities(adjusted)
        rows.append(
            {
                **row,
                "model_id": model_id,
                "shape_mode": mode,
                "shape_evidence_events": float(feature_row["shape_evidence_events"]),
                "shape_reliability": float(feature_row["shape_reliability"]),
                "shape_fallback_reason": None,
                **{
                    f"p_{outcome}": result[outcome]
                    for outcome in HITTER_TALENT_OUTCOMES
                },
            }
        )
    output = pl.DataFrame(rows, infer_schema_length=None)
    for output_row in output.iter_rows(named=True):
        _leaf_values(output_row, prefix="p_")
    return output
