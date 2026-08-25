"""Target-free primitives for neutral-reference Hitter v2 Stage 2f H0.

This module contains transformations and estimators only. It has no repository
paths, target loader, scorer, or protected-season knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import validate_probability_vector
from universal_baseball.hitter_v2_model import NESTED_NODES
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


LEVELS = ("ROOKIE_COMPLEX", "SINGLE_A", "HIGH_A", "AA", "AAA", "MLB")
LEVEL_ALIASES = {
    "complex": "ROOKIE_COMPLEX",
    "rookie": "ROOKIE_COMPLEX",
    "rookie_complex": "ROOKIE_COMPLEX",
    "rk": "ROOKIE_COMPLEX",
    "a": "SINGLE_A",
    "single_a": "SINGLE_A",
    "low-a": "SINGLE_A",
    "a+": "HIGH_A",
    "high_a": "HIGH_A",
    "high-a": "HIGH_A",
    "aa": "AA",
    "aaa": "AAA",
    "mlb": "MLB",
}
AGE_KNOTS = (20.0, 24.0, 28.0, 32.0)
TRANSLATION_AGE_BANDS = ("LE_20", "21_23", "24_27", "GE_28")
RATE_FLOOR = 1e-9


@dataclass(frozen=True, slots=True)
class ReferenceTranslationFit:
    """Component-link translations to one anchored reference level."""

    reference_level: str
    predictor_cutoff_season: int
    prior_mover_pa: float
    edges: pl.DataFrame
    offsets: pl.DataFrame


@dataclass(frozen=True, slots=True)
class DevelopmentFit:
    """Chronology-safe component development coefficients and transforms."""

    predictor_cutoff_season: int
    prior_sd: float
    coefficients: pl.DataFrame
    transforms: pl.DataFrame
    level_age_references: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class CalibrationFit:
    """Training-origin link calibration shrunk toward identity."""

    predictor_cutoff_season: int
    prior_sd: float
    coefficients: pl.DataFrame


@dataclass(frozen=True, slots=True)
class H0Projection:
    """One neutral-reference probability vector plus fallback provenance."""

    probabilities: dict[str, float]
    reference_level: str
    translation_path_quality: str
    translation_uncertainty: float
    development_applied: bool
    calibration_applied: bool


def normalize_level(value: object) -> str:
    """Normalize the frozen affiliated-level vocabulary."""

    text = str(value).strip()
    if text in LEVELS:
        return text
    normalized = LEVEL_ALIASES.get(text.lower().replace(" ", "_"))
    if normalized is None:
        raise ValueError(f"unsupported affiliated level: {value}")
    return normalized


def _logit(probability: float) -> float:
    value = float(np.clip(probability, RATE_FLOOR, 1.0 - RATE_FLOOR))
    return float(np.log(value / (1.0 - value)))


def _logistic(value: float) -> float:
    return float(1.0 / (1.0 + np.exp(-np.clip(value, -35.0, 35.0))))


def _branch_probabilities(probabilities: Mapping[str, float]) -> dict[str, float]:
    validate_probability_vector(probabilities, tolerance=1e-10)
    leaves = {
        outcome: float(probabilities[outcome]) for outcome in HITTER_TALENT_OUTCOMES
    }
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


def probability_links(probabilities: Mapping[str, float]) -> dict[str, float]:
    """Convert a terminal simplex into nested binary logits and ALR contrasts."""

    branch = _branch_probabilities(probabilities)
    result: dict[str, float] = {}
    for node in NESTED_NODES:
        values = np.asarray([branch[child] for child in node.children], dtype=float)
        total = float(values.sum())
        conditional = (
            np.full(len(values), 1.0 / len(values)) if total <= 0.0 else values / total
        )
        if len(node.children) == 2:
            result[node.name] = _logit(float(conditional[0]))
        else:
            reference = max(float(conditional[0]), RATE_FLOOR)
            for index, child in enumerate(node.children[1:], start=1):
                result[f"{node.name}:{child}_vs_{node.children[0]}"] = float(
                    np.log(max(float(conditional[index]), RATE_FLOOR) / reference)
                )
    return result


def probabilities_from_links(links: Mapping[str, float]) -> dict[str, float]:
    """Reconstruct the exhaustive terminal simplex from nested link values."""

    conditional: dict[tuple[str, str], float] = {}
    for node in NESTED_NODES:
        if len(node.children) == 2:
            if node.name not in links:
                raise ValueError(f"missing binary link: {node.name}")
            first = _logistic(float(links[node.name]))
            conditional[(node.name, node.children[0])] = first
            conditional[(node.name, node.children[1])] = 1.0 - first
        else:
            keys = [
                f"{node.name}:{child}_vs_{node.children[0]}"
                for child in node.children[1:]
            ]
            missing = [key for key in keys if key not in links]
            if missing:
                raise ValueError(f"missing multinomial links: {missing}")
            logits = np.asarray([0.0, *[float(links[key]) for key in keys]])
            shifted = logits - logits.max()
            values = np.exp(shifted)
            values /= values.sum()
            for child, value in zip(node.children, values, strict=True):
                conditional[(node.name, child)] = float(value)

    result = {
        "K": conditional[("plate_appearance", "K")],
        "UBB": conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "UBB")],
        "HBP": conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "NON_UBB")]
        * conditional[("non_k_non_ubb", "HBP")],
    }
    contact = (
        conditional[("plate_appearance", "NON_K")]
        * conditional[("non_k", "NON_UBB")]
        * conditional[("non_k_non_ubb", "CONTACT")]
    )
    result["HR"] = contact * conditional[("contact", "HR")]
    non_hr = contact * conditional[("contact", "NON_HR")]
    reach = non_hr * conditional[("non_hr_contact", "REACH")]
    hit = reach * conditional[("reach", "HIT")]
    for outcome in ("1B", "2B", "3B"):
        result[outcome] = hit * conditional[("hit_in_play", outcome)]
    non_hit = reach * conditional[("reach", "NON_HIT_REACH")]
    for outcome in ("ROE", "FC_REACH"):
        result[outcome] = non_hit * conditional[("non_hit_reach", outcome)]
    non_reach = non_hr * conditional[("non_hr_contact", "NON_REACH")]
    for outcome in ("SF", "MULTI_OUT", "OTHER_OUT"):
        result[outcome] = non_reach * conditional[("non_reach", outcome)]
    validate_probability_vector(result, tolerance=1e-10)
    return result


def _validate_pair_chronology(pairs: pl.DataFrame, cutoff: int) -> None:
    required = {"origin_season", "destination_season"}
    if missing := sorted(required - set(pairs.columns)):
        raise ValueError(f"adjacent-season pairs missing chronology: {missing}")
    if pairs.filter(pl.col("destination_season") != pl.col("origin_season") + 1).height:
        raise ValueError("development/translation pairs must be adjacent seasons")
    if pairs.filter(pl.col("destination_season") > cutoff).height:
        raise ValueError("pair data cross the predictor cutoff")


def translation_age_band(age: float) -> str:
    """Return the frozen broad age band used for mover translations."""

    value = float(age)
    if not isfinite(value):
        raise ValueError("translation age must be finite")
    if value <= 20.0:
        return "LE_20"
    if value <= 23.0:
        return "21_23"
    if value <= 27.0:
        return "24_27"
    return "GE_28"


def fit_reference_level_translations(
    mover_pairs: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    prior_mover_pa: float,
    reference_level: str = "MLB",
) -> ReferenceTranslationFit:
    """Fit partially pooled component-link level steps from prior mover pairs."""

    required = {
        "component",
        "origin_level",
        "destination_level",
        "age",
        "link_delta",
        "mover_pa",
        "origin_season",
        "destination_season",
    }
    if missing := sorted(required - set(mover_pairs.columns)):
        raise ValueError(f"translation pairs missing fields: {missing}")
    _validate_pair_chronology(mover_pairs, predictor_cutoff_season)
    prior = float(prior_mover_pa)
    if not isfinite(prior) or prior <= 0.0:
        raise ValueError("translation prior mover PA must be finite and positive")
    reference = normalize_level(reference_level)
    if reference != "MLB":
        raise ValueError("Stage 2f reference level is frozen to MLB")

    rows: list[dict[str, object]] = []
    for row in mover_pairs.iter_rows(named=True):
        origin = normalize_level(row["origin_level"])
        destination = normalize_level(row["destination_level"])
        origin_rank = LEVELS.index(origin)
        destination_rank = LEVELS.index(destination)
        steps = destination_rank - origin_rank
        delta = float(row["link_delta"])
        evidence = float(row["mover_pa"])
        age_band = translation_age_band(float(row["age"]))
        if steps == 0:
            continue
        if not isfinite(delta) or not isfinite(evidence) or evidence <= 0.0:
            raise ValueError(
                "translation deltas and evidence must be finite and positive"
            )
        upward_per_step = delta / steps
        allocated_evidence = evidence / abs(steps)
        for boundary in range(
            min(origin_rank, destination_rank), max(origin_rank, destination_rank)
        ):
            rows.append(
                {
                    "component": str(row["component"]),
                    "boundary": boundary,
                    "age_band": age_band,
                    "upward_link_delta": upward_per_step,
                    "mover_pa": allocated_evidence,
                }
            )
    if not rows:
        raise ValueError("translation fit has no level-moving pairs")
    expanded = pl.DataFrame(rows)
    edge_rows: list[dict[str, object]] = []
    offset_rows: list[dict[str, object]] = []
    for component in sorted(str(value) for value in expanded["component"].unique()):
        component_rows = expanded.filter(pl.col("component") == component)
        global_evidence = float(component_rows["mover_pa"].sum())
        global_delta = float(
            (component_rows["upward_link_delta"] * component_rows["mover_pa"]).sum()
            / global_evidence
        )
        edges_by_band: dict[str, list[dict[str, object]]] = {
            band: [] for band in ("ALL", *TRANSLATION_AGE_BANDS)
        }
        for boundary in range(len(LEVELS) - 1):
            cell = component_rows.filter(pl.col("boundary") == boundary)
            evidence = float(cell["mover_pa"].sum()) if cell.height else 0.0
            observed_sum = (
                float((cell["upward_link_delta"] * cell["mover_pa"]).sum())
                if cell.height
                else 0.0
            )
            boundary_estimate = (observed_sum + prior * global_delta) / (
                evidence + prior
            )
            for age_band in ("ALL", *TRANSLATION_AGE_BANDS):
                age_cell = (
                    cell
                    if age_band == "ALL"
                    else cell.filter(pl.col("age_band") == age_band)
                )
                age_evidence = (
                    float(age_cell["mover_pa"].sum()) if age_cell.height else 0.0
                )
                age_sum = (
                    float((age_cell["upward_link_delta"] * age_cell["mover_pa"]).sum())
                    if age_cell.height
                    else 0.0
                )
                estimate = (
                    boundary_estimate
                    if age_band == "ALL"
                    else (age_sum + prior * boundary_estimate) / (age_evidence + prior)
                )
                effective_evidence = evidence if age_band == "ALL" else age_evidence
                edge = {
                    "component": component,
                    "age_band": age_band,
                    "origin_level": LEVELS[boundary],
                    "destination_level": LEVELS[boundary + 1],
                    "upward_link_delta": estimate,
                    "specific_mover_pa": effective_evidence,
                    "prior_mover_pa": prior,
                    "reliability": effective_evidence / (effective_evidence + prior),
                    "global_upward_link_delta": global_delta,
                    "used_age_band_fallback": age_band != "ALL" and age_evidence == 0.0,
                    "used_global_fallback": evidence == 0.0,
                    "edge_uncertainty": float(
                        1.0 / np.sqrt(effective_evidence + prior)
                    ),
                }
                edges_by_band[age_band].append(edge)
                edge_rows.append(edge)
        for age_band, component_edges in edges_by_band.items():
            for level_index, level in enumerate(LEVELS):
                path = component_edges[level_index:]
                offset_rows.append(
                    {
                        "component": component,
                        "age_band": age_band,
                        "level": level,
                        "link_offset_to_MLB": float(
                            sum(float(edge["upward_link_delta"]) for edge in path)
                        ),
                        "translation_uncertainty": float(
                            np.sqrt(
                                sum(
                                    float(edge["edge_uncertainty"]) ** 2
                                    for edge in path
                                )
                            )
                        ),
                        "path_quality": (
                            "reference"
                            if not path
                            else "global_fallback"
                            if any(bool(edge["used_global_fallback"]) for edge in path)
                            else "age_band_fallback"
                            if any(
                                bool(edge["used_age_band_fallback"]) for edge in path
                            )
                            else "partially_pooled_mover_path"
                        ),
                    }
                )
    return ReferenceTranslationFit(
        reference_level=reference,
        predictor_cutoff_season=int(predictor_cutoff_season),
        prior_mover_pa=prior,
        edges=pl.DataFrame(edge_rows).sort("component", "age_band", "origin_level"),
        offsets=pl.DataFrame(offset_rows).sort("component", "age_band", "level"),
    )


def _age_features(age: float, level_reference_age: float) -> dict[str, float]:
    if not isfinite(age) or not isfinite(level_reference_age):
        raise ValueError("age inputs must be finite")
    return {
        "age_relative_to_level": age - level_reference_age,
        **{f"age_above_{int(knot)}": max(age - knot, 0.0) for knot in AGE_KNOTS},
    }


def fit_forward_development(
    pairs: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    prior_sd: float,
    level_age_references: Mapping[str, float],
) -> DevelopmentFit:
    """Fit weighted, standardized forward link changes with Gaussian shrinkage."""

    required = {
        "component",
        "level",
        "age",
        "reference_link_delta",
        "mover_pa",
        "origin_season",
        "destination_season",
    }
    if missing := sorted(required - set(pairs.columns)):
        raise ValueError(f"development pairs missing fields: {missing}")
    _validate_pair_chronology(pairs, predictor_cutoff_season)
    shrinkage = float(prior_sd)
    if not isfinite(shrinkage) or shrinkage <= 0.0:
        raise ValueError("development prior SD must be finite and positive")
    references = {
        normalize_level(key): float(value)
        for key, value in level_age_references.items()
    }
    if set(references) != set(LEVELS):
        raise ValueError("development requires an age reference for every frozen level")

    feature_names = [
        "age_relative_to_level",
        *[f"age_above_{int(knot)}" for knot in AGE_KNOTS],
    ]
    coefficient_rows: list[dict[str, object]] = []
    transform_rows: list[dict[str, object]] = []
    for component in sorted(str(value) for value in pairs["component"].unique()):
        rows = pairs.filter(pl.col("component") == component)
        features = np.asarray(
            [
                list(
                    _age_features(
                        float(row["age"]), references[normalize_level(row["level"])]
                    ).values()
                )
                for row in rows.iter_rows(named=True)
            ],
            dtype=float,
        )
        target = rows["reference_link_delta"].to_numpy().astype(float)
        weights = rows["mover_pa"].to_numpy().astype(float)
        if (
            not np.all(np.isfinite(target))
            or not np.all(np.isfinite(weights))
            or np.any(weights <= 0.0)
        ):
            raise ValueError(
                "development response and evidence must be finite and positive"
            )
        means = np.average(features, axis=0, weights=weights)
        scales = np.sqrt(np.average((features - means) ** 2, axis=0, weights=weights))
        scales = np.where(scales > 1e-9, scales, 1.0)
        standardized = (features - means) / scales
        design = np.column_stack((np.ones(rows.height), standardized))
        weighted_design = design * np.sqrt(weights)[:, None]
        precision = 1.0 / shrinkage**2
        penalty = np.eye(design.shape[1]) * precision
        coefficients = np.linalg.solve(
            weighted_design.T @ weighted_design + penalty,
            weighted_design.T @ (target * np.sqrt(weights)),
        )
        coefficient_rows.extend(
            {
                "component": component,
                "feature": feature,
                "coefficient": float(value),
            }
            for feature, value in zip(
                ("intercept", *feature_names), coefficients, strict=True
            )
        )
        transform_rows.extend(
            {
                "component": component,
                "feature": feature,
                "mean": float(mean),
                "scale": float(scale),
            }
            for feature, mean, scale in zip(feature_names, means, scales, strict=True)
        )
    return DevelopmentFit(
        predictor_cutoff_season=int(predictor_cutoff_season),
        prior_sd=shrinkage,
        coefficients=pl.DataFrame(coefficient_rows).sort("component", "feature"),
        transforms=pl.DataFrame(transform_rows).sort("component", "feature"),
        level_age_references=references,
    )


def fit_training_origin_calibration(
    origins: pl.DataFrame,
    *,
    predictor_cutoff_season: int,
    prior_sd: float,
) -> CalibrationFit:
    """Fit weighted link calibration using only completed earlier origins."""

    required = {
        "component",
        "predicted_link",
        "observed_link",
        "evidence",
        "target_season",
    }
    if missing := sorted(required - set(origins.columns)):
        raise ValueError(f"calibration origins missing fields: {missing}")
    if origins.filter(pl.col("target_season") > predictor_cutoff_season).height:
        raise ValueError("calibration origin crosses the predictor cutoff")
    shrinkage = float(prior_sd)
    if not isfinite(shrinkage) or shrinkage <= 0.0:
        raise ValueError("calibration prior SD must be finite and positive")
    rows = []
    precision = 1.0 / shrinkage**2
    for component in sorted(str(value) for value in origins["component"].unique()):
        group = origins.filter(pl.col("component") == component)
        x = group["predicted_link"].to_numpy().astype(float)
        y = group["observed_link"].to_numpy().astype(float)
        weights = group["evidence"].to_numpy().astype(float)
        if (
            not np.all(np.isfinite(x))
            or not np.all(np.isfinite(y))
            or not np.all(np.isfinite(weights))
            or np.any(weights <= 0.0)
        ):
            raise ValueError(
                "calibration values and evidence must be finite and positive"
            )
        design = np.column_stack((np.ones(group.height), x))
        weighted = design * np.sqrt(weights)[:, None]
        penalty = np.eye(2) * precision
        prior_mean = np.asarray([0.0, 1.0])
        coefficients = np.linalg.solve(
            weighted.T @ weighted + penalty,
            weighted.T @ (y * np.sqrt(weights)) + penalty @ prior_mean,
        )
        rows.append(
            {
                "component": component,
                "intercept": float(coefficients[0]),
                "slope": float(coefficients[1]),
                "origin_rows": group.height,
                "evidence": float(weights.sum()),
            }
        )
    return CalibrationFit(
        predictor_cutoff_season=int(predictor_cutoff_season),
        prior_sd=shrinkage,
        coefficients=pl.DataFrame(rows).sort("component"),
    )


def _development_delta(
    fit: DevelopmentFit | None,
    component: str,
    *,
    age: float | None,
    level: str,
) -> float:
    if fit is None or age is None:
        return 0.0
    coefficients = fit.coefficients.filter(pl.col("component") == component)
    transforms = fit.transforms.filter(pl.col("component") == component)
    if coefficients.is_empty() or transforms.is_empty():
        return 0.0
    raw = _age_features(float(age), float(fit.level_age_references[level]))
    value = float(
        coefficients.filter(pl.col("feature") == "intercept")["coefficient"].item()
    )
    for row in transforms.iter_rows(named=True):
        coefficient = float(
            coefficients.filter(pl.col("feature") == row["feature"])[
                "coefficient"
            ].item()
        )
        value += (
            coefficient
            * (raw[str(row["feature"])] - float(row["mean"]))
            / float(row["scale"])
        )
    return value


def predict_development_delta(
    fit: DevelopmentFit,
    component: str,
    *,
    age: float,
    level: object,
) -> float:
    """Evaluate one fitted forward-development effect without outcome access."""

    return _development_delta(
        fit,
        component,
        age=float(age),
        level=normalize_level(level),
    )


def apply_h0_neutral_projection(
    base_probabilities: Mapping[str, float],
    *,
    observed_level: object,
    translation: ReferenceTranslationFit | None = None,
    development: DevelopmentFit | None = None,
    calibration: CalibrationFit | None = None,
    age_at_target: float | None = None,
) -> H0Projection:
    """Apply frozen H0 link transforms with explicit exact neutral fallbacks."""

    validate_probability_vector(base_probabilities, tolerance=1e-10)
    level = normalize_level(observed_level)
    if translation is None and development is None and calibration is None:
        return H0Projection(
            probabilities={
                outcome: float(base_probabilities[outcome])
                for outcome in HITTER_TALENT_OUTCOMES
            },
            reference_level="MLB",
            translation_path_quality="exact_untranslated_base",
            translation_uncertainty=0.0,
            development_applied=False,
            calibration_applied=False,
        )
    links = probability_links(base_probabilities)
    age_band = (
        translation_age_band(float(age_at_target))
        if age_at_target is not None
        else "ALL"
    )
    qualities: list[str] = []
    uncertainties: list[float] = []
    development_applied = False
    calibration_applied = False
    adjusted: dict[str, float] = {}
    for component, raw_link in links.items():
        value = raw_link
        if translation is not None:
            offset = translation.offsets.filter(
                (pl.col("component") == component)
                & (pl.col("age_band") == age_band)
                & (pl.col("level") == level)
            )
            if offset.height:
                value += float(offset["link_offset_to_MLB"].item())
                qualities.append(str(offset["path_quality"].item()))
                uncertainties.append(float(offset["translation_uncertainty"].item()))
            else:
                qualities.append("neutral_disconnected_component_fallback")
                uncertainties.append(float("inf"))
        delta = _development_delta(
            development, component, age=age_at_target, level=level
        )
        if delta != 0.0:
            value += delta
            development_applied = True
        if calibration is not None:
            row = calibration.coefficients.filter(pl.col("component") == component)
            if row.height:
                value = (
                    float(row["intercept"].item()) + float(row["slope"].item()) * value
                )
                calibration_applied = True
        adjusted[component] = value
    probabilities = probabilities_from_links(adjusted)
    if translation is None:
        quality = "exact_untranslated_base"
        uncertainty = 0.0
    elif any(value.startswith("neutral_disconnected") for value in qualities):
        quality = "neutral_disconnected_component_fallback"
        uncertainty = float("inf")
    elif "global_fallback" in qualities:
        quality = "global_fallback"
        uncertainty = max(uncertainties, default=0.0)
    elif "age_band_fallback" in qualities:
        quality = "age_band_fallback"
        uncertainty = max(uncertainties, default=0.0)
    elif level == translation.reference_level:
        quality = "reference"
        uncertainty = 0.0
    else:
        quality = "partially_pooled_mover_path"
        uncertainty = max(uncertainties, default=0.0)
    return H0Projection(
        probabilities=probabilities,
        reference_level="MLB",
        translation_path_quality=quality,
        translation_uncertainty=uncertainty,
        development_applied=development_applied,
        calibration_applied=calibration_applied,
    )


def wrap_reference_level_probabilities(
    base_probabilities: Mapping[str, float],
    *,
    observed_level: object,
    translation: ReferenceTranslationFit,
) -> H0Projection:
    """Apply only the common-reference translation used by permanent baselines."""

    return apply_h0_neutral_projection(
        base_probabilities,
        observed_level=observed_level,
        translation=translation,
    )
