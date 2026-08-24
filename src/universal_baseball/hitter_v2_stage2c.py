"""Narrow Stage 2c pulled-fly and ground-direction candidate primitives.

This module contains no source loader, scorer, promotion rule, tracking path,
leaderboard, or WAR assembly.  Candidate fitting requires callers to provide
explicit earlier-origin pairs.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Mapping, Sequence

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_stage2b import (
    DEFAULT_GRADIENT_TOLERANCE,
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_OBJECTIVE_TOLERANCE,
    _fit_with_backtracking,
    assemble_nested_probabilities,
    nested_conditionals,
)
from universal_baseball.performance_season import CONTACT_CORE_BINS


FIXED_HALF_LIFE_SEASONS = 2.0
FIXED_PRIOR_EVENTS = 100.0
FIXED_L2_PENALTY = 1.0
HR_MODE = "nested_pulled_offb_hr"
XBH_MODE = "pulled_offb_xbh_ablation"
GROUND_MODE = "separate_ground_direction"
PULLED_OFFB_FEATURES = (
    (
        "offb_per_contact",
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB"),
        CONTACT_CORE_BINS,
    ),
    (
        "pull_offb_per_offb",
        ("PULL_OFFB",),
        ("PULL_OFFB", "CENTER_OFFB", "OPPO_OFFB"),
    ),
)
FEATURES = {
    HR_MODE: PULLED_OFFB_FEATURES,
    XBH_MODE: PULLED_OFFB_FEATURES,
    GROUND_MODE: (
        ("gb_per_contact", ("PULL_GB", "CENTER_GB", "OPPO_GB"), CONTACT_CORE_BINS),
        ("oppo_gb_per_gb", ("OPPO_GB",), ("PULL_GB", "CENTER_GB", "OPPO_GB")),
    ),
}
CONTRASTS = {
    HR_MODE: ("hr_per_contact",),
    XBH_MODE: ("xbh_per_hit",),
    GROUND_MODE: ("reach_per_non_hr_contact",),
}
E1_MODEL_ID = "E1_NESTED_PULLED_OFFB_POWER"
E2_MODEL_ID = "E2_PULLED_OFFB_XBH_ABLATION"
E3_MODEL_ID = "E3_SEPARATE_GROUND_DIRECTION"
REQUIRED_BASE_MODELS = {
    XBH_MODE: frozenset((E1_MODEL_ID,)),
    GROUND_MODE: frozenset((E1_MODEL_ID, E2_MODEL_ID)),
}


@dataclass(frozen=True, slots=True)
class Stage2cFit:
    """A complete fixed-contract contrast coefficient surface."""

    coefficients: pl.DataFrame
    metrics: dict[str, object]


def _logit(value: float) -> float:
    clipped = min(max(value, 1e-12), 1.0 - 1e-12)
    return log(clipped / (1.0 - clipped))


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        inverse = np.exp(-value)
        return float(1.0 / (1.0 + inverse))
    exponent = np.exp(value)
    return float(exponent / (1.0 + exponent))


def _empty_features(mode: str) -> pl.DataFrame:
    names = [component[0] for component in FEATURES[mode]]
    return pl.DataFrame(
        schema={
            "player_id": pl.Int64,
            "shape_mode": pl.String,
            "shape_latest_season": pl.Int64,
            "shape_latest_league_id": pl.Int64,
            "shape_latest_level_group": pl.String,
            **{f"shape_feature_{name}": pl.Float64 for name in names},
            **{f"shape_evidence_{name}": pl.Float64 for name in names},
            **{f"shape_reliability_{name}": pl.Float64 for name in names},
        }
    )


def build_stage2c_features(
    shape_history: pl.DataFrame,
    player_ids: Sequence[int],
    *,
    predictor_cutoff_season: int,
    mode: str,
) -> pl.DataFrame:
    """Build chronology-safe nested EB features without target outcomes."""

    if mode not in FEATURES:
        raise ValueError(f"unsupported Stage 2c mode: {mode}")
    required = {
        "season",
        "league_id",
        "player_id",
        "level_group",
        "core_bin",
        "occurrence_count",
    }
    if missing := sorted(required - set(shape_history.columns)):
        raise ValueError(f"shape history is missing columns: {missing}")
    allowed = shape_history.filter(
        (pl.col("season") <= predictor_cutoff_season)
        & pl.col("core_bin").is_in(list(CONTACT_CORE_BINS))
    )
    if allowed.is_empty():
        return _empty_features(mode)
    players = sorted(set(int(value) for value in player_ids))
    if not players:
        return _empty_features(mode)

    sparse = (
        allowed.group_by(
            "season", "league_id", "level_group", "player_id", "core_bin"
        )
        .agg(pl.col("occurrence_count").sum())
    )
    contexts = (
        sparse.group_by("season", "league_id", "level_group", "core_bin")
        .agg(pl.col("occurrence_count").sum().alias("context_count"))
    )
    context_map = {
        (
            int(row["season"]),
            int(row["league_id"]),
            str(row["level_group"]),
            str(row["core_bin"]),
        ): float(row["context_count"])
        for row in contexts.iter_rows(named=True)
    }
    season_rows = sparse.filter(pl.col("player_id").is_in(players))
    count_map = {
        (
            int(row["season"]),
            int(row["league_id"]),
            str(row["level_group"]),
            int(row["player_id"]),
            str(row["core_bin"]),
        ): float(row["occurrence_count"])
        for row in season_rows.iter_rows(named=True)
    }
    player_contexts = (
        season_rows.group_by("season", "league_id", "level_group", "player_id")
        .agg(pl.col("occurrence_count").sum().alias("contact_events"))
        .sort("player_id", "season", "league_id", "level_group")
    )
    accumulators: dict[int, dict[str, object]] = {}
    for context in player_contexts.iter_rows(named=True):
        season = int(context["season"])
        league_id = int(context["league_id"])
        level = str(context["level_group"])
        player_id = int(context["player_id"])
        recency = 0.5 ** (
            (predictor_cutoff_season - season) / FIXED_HALF_LIFE_SEASONS
        )
        accumulator = accumulators.setdefault(
            player_id,
            {
                "latest": (season, league_id, level),
                "features": {name: 0.0 for name, _, _ in FEATURES[mode]},
                "weights": {name: 0.0 for name, _, _ in FEATURES[mode]},
            },
        )
        latest = accumulator["latest"]
        if (season, -league_id, level) > (latest[0], -latest[1], latest[2]):
            accumulator["latest"] = (season, league_id, level)
        for name, numerator_bins, denominator_bins in FEATURES[mode]:
            numerator = sum(
                count_map.get((season, league_id, level, player_id, value), 0.0)
                for value in numerator_bins
            )
            denominator = sum(
                count_map.get((season, league_id, level, player_id, value), 0.0)
                for value in denominator_bins
            )
            if denominator <= 0.0:
                continue
            context_numerator = sum(
                context_map.get((season, league_id, level, value), 0.0)
                for value in numerator_bins
            )
            context_denominator = sum(
                context_map.get((season, league_id, level, value), 0.0)
                for value in denominator_bins
            )
            if not 0.0 < context_numerator < context_denominator:
                raise ValueError(f"shape context lacks interior support for {name}")
            context_rate = context_numerator / context_denominator
            posterior = (
                numerator + FIXED_PRIOR_EVENTS * context_rate
            ) / (denominator + FIXED_PRIOR_EVENTS)
            weight = recency * denominator
            accumulator["features"][name] += weight * (
                _logit(posterior) - _logit(context_rate)
            )
            accumulator["weights"][name] += weight

    rows: list[dict[str, object]] = []
    for player_id, accumulator in sorted(accumulators.items()):
        feature_values = accumulator["features"]
        weights = accumulator["weights"]
        if max(weights.values()) <= 0.0:
            continue
        latest_season, latest_league, latest_level = accumulator["latest"]
        rows.append(
            {
                "player_id": player_id,
                "shape_mode": mode,
                "shape_latest_season": latest_season,
                "shape_latest_league_id": latest_league,
                "shape_latest_level_group": latest_level,
                **{
                    f"shape_feature_{name}": (
                        feature_values[name] / weights[name]
                        if weights[name] > 0.0
                        else 0.0
                    )
                    for name, _, _ in FEATURES[mode]
                },
                **{
                    f"shape_evidence_{name}": weights[name]
                    for name, _, _ in FEATURES[mode]
                },
                **{
                    f"shape_reliability_{name}": weights[name]
                    / (weights[name] + FIXED_PRIOR_EVENTS)
                    for name, _, _ in FEATURES[mode]
                },
            }
        )
    return pl.DataFrame(rows, schema=_empty_features(mode).schema)


def zero_stage2c_fit(mode: str) -> Stage2cFit:
    """Return the exact zero-increment fit used before an earlier origin exists."""

    if mode not in FEATURES:
        raise ValueError(f"unsupported Stage 2c mode: {mode}")
    names = [component[0] for component in FEATURES[mode]]
    rows = [
        {"contrast": contrast, "feature": feature, "coefficient": 0.0}
        for contrast in CONTRASTS[mode]
        for feature in names
    ]
    return Stage2cFit(
        coefficients=pl.DataFrame(rows).sort("contrast", "feature"),
        metrics={
            "shape_mode": mode,
            "fit_origin_count": 0,
            "zero_increment_fallback": True,
            "fixed_mean_loss_l2_penalty": FIXED_L2_PENALTY,
        },
    )


def _contrast_counts(row: Mapping[str, object], contrast: str) -> tuple[float, float]:
    if contrast == "hr_per_contact":
        return float(row["HR"]), sum(
            float(row[value])
            for value in ("1B", "2B", "3B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT")
        )
    if contrast == "xbh_per_hit":
        return float(row["2B"]) + float(row["3B"]), float(row["1B"])
    if contrast == "reach_per_non_hr_contact":
        return sum(float(row[value]) for value in ("1B", "2B", "3B", "ROE", "FC_REACH")), sum(
            float(row[value]) for value in ("SF", "MULTI_OUT", "OTHER_OUT")
        )
    raise ValueError(f"unsupported Stage 2c contrast: {contrast}")


def _contrast_probability(row: Mapping[str, object], contrast: str) -> float:
    p = {value: float(row[f"p_{value}"]) for value in HITTER_TALENT_OUTCOMES}
    if contrast == "hr_per_contact":
        return p["HR"] / sum(p[value] for value in ("HR", "1B", "2B", "3B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT"))
    if contrast == "xbh_per_hit":
        return (p["2B"] + p["3B"]) / (p["1B"] + p["2B"] + p["3B"])
    if contrast == "reach_per_non_hr_contact":
        reach = sum(p[value] for value in ("1B", "2B", "3B", "ROE", "FC_REACH"))
        non_reach = sum(p[value] for value in ("SF", "MULTI_OUT", "OTHER_OUT"))
        return reach / (reach + non_reach)
    raise ValueError(f"unsupported Stage 2c contrast: {contrast}")


def _validate_required_base_models(predictions: pl.DataFrame, mode: str) -> None:
    required_bases = REQUIRED_BASE_MODELS.get(mode)
    if required_bases is None:
        return
    if "model_id" not in predictions.columns:
        raise ValueError(f"Stage 2c {mode} residual requires model_id provenance")
    if predictions.filter(~pl.col("model_id").is_in(sorted(required_bases))).height:
        allowed = ", ".join(sorted(required_bases))
        raise ValueError(
            f"Stage 2c {mode} residual requires base model in: {allowed}"
        )


def fit_stage2c_residual(
    origin_examples: Sequence[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]],
    *,
    mode: str,
    l2_penalty: float = FIXED_L2_PENALTY,
) -> Stage2cFit:
    """Fit the frozen narrow contrasts from explicit earlier-origin examples."""

    if mode not in FEATURES:
        raise ValueError(f"unsupported Stage 2c mode: {mode}")
    if not origin_examples:
        return zero_stage2c_fit(mode)
    if l2_penalty != FIXED_L2_PENALTY:
        raise ValueError("Stage 2c residual penalty is frozen at 1.0")
    names = [component[0] for component in FEATURES[mode]]
    rows: list[dict[str, object]] = []
    metrics: dict[str, object] = {}
    for contrast in CONTRASTS[mode]:
        offsets: list[float] = []
        counts: list[tuple[float, float]] = []
        feature_rows: list[list[float]] = []
        for prediction, target, features in origin_examples:
            _validate_required_base_models(prediction, mode)
            joined = target.join(prediction, on="player_id", how="inner").join(
                features, on="player_id", how="inner"
            )
            for row in joined.iter_rows(named=True):
                success, failure = _contrast_counts(row, contrast)
                if success + failure <= 0.0:
                    continue
                offsets.append(_logit(_contrast_probability(row, contrast)))
                counts.append((success, failure))
                feature_rows.append(
                    [float(row[f"shape_feature_{name}"]) for name in names]
                )
        if not offsets:
            raise ValueError(f"Stage 2c origins lack events for {contrast}")
        offset_array = np.asarray(offsets, dtype=float)
        count_array = np.asarray(counts, dtype=float)
        feature_array = np.asarray(feature_rows, dtype=float)

        def objective_gradient(coefficient: np.ndarray) -> tuple[float, float, np.ndarray]:
            linear = np.clip(
                offset_array + feature_array @ coefficient, -700.0, 700.0
            )
            probability = 1.0 / (1.0 + np.exp(-linear))
            total = float(np.sum(count_array))
            mean_nll = float(
                -np.sum(
                    count_array[:, 0] * np.log(np.clip(probability, 1e-12, 1.0))
                    + count_array[:, 1]
                    * np.log(np.clip(1.0 - probability, 1e-12, 1.0))
                )
                / total
            )
            penalty = 0.5 * l2_penalty * float(np.mean(coefficient**2))
            residual = (count_array.sum(axis=1) * probability) - count_array[:, 0]
            gradient = (feature_array.T @ residual) / total
            gradient += l2_penalty * coefficient / coefficient.size
            return mean_nll + penalty, mean_nll, gradient

        fitted, diagnostic = _fit_with_backtracking(
            objective_gradient,
            np.zeros(len(names), dtype=float),
            max_iterations=DEFAULT_MAX_ITERATIONS,
            gradient_tolerance=DEFAULT_GRADIENT_TOLERANCE,
            objective_tolerance=DEFAULT_OBJECTIVE_TOLERANCE,
        )
        metrics[contrast] = {
            **diagnostic,
            "training_rows": len(offsets),
            "training_events": int(np.sum(count_array)),
        }
        rows.extend(
            {
                "contrast": contrast,
                "feature": name,
                "coefficient": float(fitted[index]),
            }
            for index, name in enumerate(names)
        )
    return Stage2cFit(
        coefficients=pl.DataFrame(rows).sort("contrast", "feature"),
        metrics={
            "shape_mode": mode,
            "fit_origin_count": len(origin_examples),
            "zero_increment_fallback": False,
            "fixed_mean_loss_l2_penalty": l2_penalty,
            "contrasts": metrics,
        },
    )


def _coefficient_map(fit: Stage2cFit, mode: str) -> dict[tuple[str, str], float]:
    result = {
        (str(row["contrast"]), str(row["feature"])): float(row["coefficient"])
        for row in fit.coefficients.iter_rows(named=True)
    }
    expected = {
        (contrast, component[0])
        for contrast in CONTRASTS[mode]
        for component in FEATURES[mode]
    }
    if set(result) != expected or any(not isfinite(value) for value in result.values()):
        raise ValueError("Stage 2c coefficient surface is incomplete or nonfinite")
    return result


def apply_stage2c_residual(
    predictions: pl.DataFrame,
    features: pl.DataFrame,
    fit: Stage2cFit,
    *,
    model_id: str,
) -> pl.DataFrame:
    """Apply only the frozen Stage 2c contrasts with exact missing fallback."""

    mode = str(fit.metrics["shape_mode"])
    if mode not in FEATURES:
        raise ValueError(f"unsupported Stage 2c mode: {mode}")
    _validate_required_base_models(predictions, mode)
    coefficient = _coefficient_map(fit, mode)
    names = [component[0] for component in FEATURES[mode]]
    feature_map = {
        int(row["player_id"]): row for row in features.iter_rows(named=True)
    }
    rows: list[dict[str, object]] = []
    for row in predictions.sort("player_id").iter_rows(named=True):
        player_id = int(row["player_id"])
        feature_row = feature_map.get(player_id)
        if feature_row is None or bool(fit.metrics.get("zero_increment_fallback")):
            rows.append(
                {
                    **row,
                    "model_id": model_id,
                    "shape_mode": mode,
                    "shape_fallback_reason": (
                        "zero_increment_no_prior_origin"
                        if feature_row is not None
                        else "missing_shape_evidence"
                    ),
                }
            )
            continue
        leaves = {
            outcome: float(row[f"p_{outcome}"])
            for outcome in HITTER_TALENT_OUTCOMES
        }
        conditional = nested_conditionals(leaves)
        vector = np.asarray(
            [float(feature_row[f"shape_feature_{name}"]) for name in names]
        )
        adjusted = {node: dict(values) for node, values in conditional.items()}
        if mode == HR_MODE:
            hr_increment = sum(
                coefficient[("hr_per_contact", name)] * vector[index]
                for index, name in enumerate(names)
            )
            hr = _sigmoid(_logit(conditional["contact"]["HR"]) + hr_increment)
            adjusted["contact"] = {"HR": hr, "NON_HR": 1.0 - hr}
        elif mode == XBH_MODE:
            xbh_increment = sum(
                coefficient[("xbh_per_hit", name)] * vector[index]
                for index, name in enumerate(names)
            )
            hit = conditional["hit_in_play"]
            old_xbh = hit["2B"] + hit["3B"]
            new_xbh = _sigmoid(_logit(old_xbh) + xbh_increment)
            triple_share = hit["3B"] / old_xbh if old_xbh > 0.0 else 0.0
            adjusted["hit_in_play"] = {
                "1B": 1.0 - new_xbh,
                "2B": new_xbh * (1.0 - triple_share),
                "3B": new_xbh * triple_share,
            }
        else:
            reach_increment = sum(
                coefficient[("reach_per_non_hr_contact", name)] * vector[index]
                for index, name in enumerate(names)
            )
            reach = _sigmoid(
                _logit(conditional["non_hr_contact"]["REACH"])
                + reach_increment
            )
            adjusted["non_hr_contact"] = {
                "REACH": reach,
                "NON_REACH": 1.0 - reach,
            }
        result = assemble_nested_probabilities(adjusted)
        validate_probability_vector(result, tolerance=1e-9)
        rows.append(
            {
                **row,
                "model_id": model_id,
                "shape_mode": mode,
                "shape_fallback_reason": None,
                **{f"p_{outcome}": result[outcome] for outcome in HITTER_TALENT_OUTCOMES},
            }
        )
    return pl.DataFrame(rows, infer_schema_length=None)
