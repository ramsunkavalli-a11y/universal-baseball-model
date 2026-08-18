"""Deterministic age/level ridge primitives for batting Projection v1.

Implements only the pre-registered design and weighted multi-output ridge math.
It does not build future responses, choose a candidate, score outcomes, or access
2025 confirmation data.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import isfinite, sqrt
from typing import Any, Sequence

import numpy as np
import polars as pl

from universal_baseball.current_talent_evidence import LEVEL_ORDINAL


PROJECTION_FORM_AGE = "projection_age_ilr_ridge_v1"
PROJECTION_FORM_AGE_LEVEL = "projection_age_level_ilr_ridge_v1"
PROJECTION_FORMS = (PROJECTION_FORM_AGE, PROJECTION_FORM_AGE_LEVEL)
PROJECTION_RIDGE_LAMBDAS = (0.001, 0.01, 0.1, 1.0)
PROJECTION_CV_FOLD_COUNT = 5

AGE_FEATURE_NAMES = (
    "age_center_27_over_5",
    "age_hinge_20_over_5",
    "age_hinge_23_over_5",
    "age_hinge_26_over_5",
    "age_hinge_29_over_5",
    "age_hinge_32_over_5",
    "age_hinge_35_over_5",
)
LEVEL_INDICATOR_LEVELS = (
    "ROOKIE_COMPLEX",
    "SINGLE_A",
    "HIGH_A",
    "AA",
    "AAA",
)
LEVEL_FEATURE_NAMES = tuple(f"level_{level.lower()}" for level in LEVEL_INDICATOR_LEVELS)
ALLOWED_LEVELS = frozenset(LEVEL_ORDINAL)
LEVEL_DISPLAY_ALIASES = {
    "Rookie Complex": "ROOKIE_COMPLEX",
    "Single-A": "SINGLE_A",
    "High-A": "HIGH_A",
}
ZERO_SCALE_TOLERANCE = 1e-12


@dataclass(frozen=True, slots=True)
class ProjectionRidgeFit:
    form: str
    ridge_lambda: float
    feature_names: tuple[str, ...]
    response_names: tuple[str, ...]
    coefficient_matrix: np.ndarray
    weighted_means: tuple[float, ...]
    weighted_scales: tuple[float, ...]
    zero_variance: tuple[bool, ...]
    training_player_count: int
    training_weight_sum: float
    metrics: dict[str, Any]

    def coefficient_frame(self) -> pl.DataFrame:
        rows: list[dict[str, object]] = []
        for feature_index, feature in enumerate(self.feature_names):
            for response_index, response in enumerate(self.response_names):
                rows.append(
                    {
                        "feature": feature,
                        "response": response,
                        "coefficient": float(self.coefficient_matrix[feature_index, response_index]),
                        "penalized": feature != "intercept",
                    }
                )
        return pl.DataFrame(rows)

    def standardization_frame(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "feature": list(self.feature_names),
                "weighted_mean": list(self.weighted_means),
                "weighted_rms_scale": list(self.weighted_scales),
                "zero_variance_in_training": list(self.zero_variance),
            }
        )


def projection_cv_fold(player_id: int) -> int:
    digest = sha256(str(int(player_id)).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % PROJECTION_CV_FOLD_COUNT


def projection_age_basis(age_years: float) -> dict[str, float]:
    age = float(age_years)
    if not isfinite(age):
        raise ValueError("Projection age must be finite")
    values = {
        "age_center_27_over_5": (age - 27.0) / 5.0,
    }
    for knot in (20, 23, 26, 29, 32, 35):
        values[f"age_hinge_{knot}_over_5"] = max(age - float(knot), 0.0) / 5.0
    return values


def projection_feature_names(form: str) -> tuple[str, ...]:
    if form == PROJECTION_FORM_AGE:
        return ("intercept", *AGE_FEATURE_NAMES)
    if form == PROJECTION_FORM_AGE_LEVEL:
        return ("intercept", *AGE_FEATURE_NAMES, *LEVEL_FEATURE_NAMES)
    raise ValueError(f"unsupported Projection candidate form: {form}")


def _canonical_level(value: object) -> str:
    level = str(value)
    level = LEVEL_DISPLAY_ALIASES.get(level, level)
    if level not in ALLOWED_LEVELS:
        raise ValueError(f"unsupported Projection as-of level: {value}")
    return level


def build_projection_design(context: pl.DataFrame, *, form: str) -> pl.DataFrame:
    required = {"player_id", "age_years", "as_of_level_group"}
    missing = sorted(required - set(context.columns))
    if missing:
        raise ValueError(f"Projection design context missing fields: {missing}")
    if context.is_empty():
        raise ValueError("Projection design context must not be empty")
    if context.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection design context violates player_id grain")

    feature_names = projection_feature_names(form)
    rows: list[dict[str, object]] = []
    for row in context.select("player_id", "age_years", "as_of_level_group").iter_rows(named=True):
        if row["age_years"] is None or row["as_of_level_group"] is None:
            raise ValueError("Projection design requires non-null age and as-of level")
        level = _canonical_level(row["as_of_level_group"])
        features: dict[str, object] = {
            "player_id": int(row["player_id"]),
            "intercept": 1.0,
            **projection_age_basis(float(row["age_years"])),
        }
        if form == PROJECTION_FORM_AGE_LEVEL:
            for feature, candidate_level in zip(
                LEVEL_FEATURE_NAMES, LEVEL_INDICATOR_LEVELS, strict=True
            ):
                features[feature] = 1.0 if level == candidate_level else 0.0
        rows.append(features)
    return pl.DataFrame(rows).select("player_id", *feature_names).sort("player_id")


def _aligned_training_arrays(
    design: pl.DataFrame,
    responses: pl.DataFrame,
    *,
    weight_column: str,
    response_columns: Sequence[str],
) -> tuple[pl.DataFrame, tuple[str, ...]]:
    response_names = tuple(str(value) for value in response_columns)
    if not response_names:
        raise ValueError("Projection ridge requires at least one response")
    required = {"player_id", weight_column, *response_names}
    missing = sorted(required - set(responses.columns))
    if missing:
        raise ValueError(f"Projection ridge responses missing fields: {missing}")
    if responses.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection ridge responses violate player_id grain")
    design_ids = set(int(value) for value in design.get_column("player_id").to_list())
    response_ids = set(int(value) for value in responses.get_column("player_id").to_list())
    if design_ids != response_ids:
        raise ValueError("Projection ridge design/response player coverage differs")
    aligned = design.join(
        responses.select("player_id", weight_column, *response_names),
        on="player_id",
        how="inner",
    ).sort("player_id")
    return aligned, response_names


def fit_projection_weighted_ridge(
    design: pl.DataFrame,
    responses: pl.DataFrame,
    *,
    form: str,
    ridge_lambda: float,
    weight_column: str,
    response_columns: Sequence[str],
) -> ProjectionRidgeFit:
    if ridge_lambda not in PROJECTION_RIDGE_LAMBDAS:
        raise ValueError(
            f"Projection ridge lambda outside frozen grid: {ridge_lambda}; "
            f"allowed={PROJECTION_RIDGE_LAMBDAS}"
        )
    feature_names = projection_feature_names(form)
    missing_design = sorted(set(feature_names) - set(design.columns))
    if missing_design:
        raise ValueError(f"Projection ridge design missing features: {missing_design}")

    aligned, response_names = _aligned_training_arrays(
        design,
        responses,
        weight_column=weight_column,
        response_columns=response_columns,
    )
    x_raw = np.asarray(aligned.select(*feature_names).to_numpy(), dtype=np.float64)
    y = np.asarray(aligned.select(*response_names).to_numpy(), dtype=np.float64)
    weights = np.asarray(aligned.get_column(weight_column).to_numpy(), dtype=np.float64)
    if not np.all(np.isfinite(x_raw)) or not np.all(np.isfinite(y)):
        raise ValueError("Projection ridge training data contains non-finite values")
    if not np.all(np.isfinite(weights)) or np.any(weights <= 0.0):
        raise ValueError("Projection ridge training weights must be finite and positive")
    weight_sum = float(weights.sum())
    if weight_sum <= 0.0:
        raise ValueError("Projection ridge training weight sum must be positive")

    x = x_raw.copy()
    means = np.zeros(x.shape[1], dtype=np.float64)
    scales = np.ones(x.shape[1], dtype=np.float64)
    zero_variance = np.zeros(x.shape[1], dtype=bool)
    for column in range(1, x.shape[1]):
        values = x_raw[:, column]
        mean = float(np.sum(weights * values) / weight_sum)
        centered = values - mean
        scale = sqrt(float(np.sum(weights * centered * centered) / weight_sum))
        means[column] = mean
        if scale <= ZERO_SCALE_TOLERANCE:
            scales[column] = 1.0
            zero_variance[column] = True
            x[:, column] = 0.0
        else:
            scales[column] = scale
            x[:, column] = centered / scale

    normalized_weights = weights / weight_sum
    sqrt_weights = np.sqrt(normalized_weights)[:, None]
    xw = x * sqrt_weights
    yw = y * sqrt_weights
    penalty = np.eye(x.shape[1], dtype=np.float64) * float(ridge_lambda)
    penalty[0, 0] = 0.0
    lhs = xw.T @ xw + penalty
    rhs = xw.T @ yw
    coefficients = np.linalg.solve(lhs, rhs)

    if np.any(~np.isfinite(coefficients)):
        raise ValueError("Projection ridge produced non-finite coefficients")
    metrics: dict[str, Any] = {
        "form": form,
        "ridge_lambda": float(ridge_lambda),
        "training_player_count": int(aligned.height),
        "training_weight_sum": weight_sum,
        "feature_count": len(feature_names),
        "response_count": len(response_names),
        "zero_variance_feature_count": int(zero_variance.sum()),
        "intercept_penalized": False,
        "shared_lambda_across_responses": True,
        "future_outcomes_scored": False,
        "candidate_selected": False,
    }
    return ProjectionRidgeFit(
        form=form,
        ridge_lambda=float(ridge_lambda),
        feature_names=feature_names,
        response_names=response_names,
        coefficient_matrix=coefficients,
        weighted_means=tuple(float(value) for value in means),
        weighted_scales=tuple(float(value) for value in scales),
        zero_variance=tuple(bool(value) for value in zero_variance),
        training_player_count=int(aligned.height),
        training_weight_sum=weight_sum,
        metrics=metrics,
    )


def predict_projection_ridge(fit: ProjectionRidgeFit, design: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(set(fit.feature_names) - set(design.columns))
    if missing:
        raise ValueError(f"Projection ridge prediction design missing features: {missing}")
    if design.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection ridge prediction design violates player_id grain")

    x_raw = np.asarray(design.select(*fit.feature_names).to_numpy(), dtype=np.float64)
    if not np.all(np.isfinite(x_raw)):
        raise ValueError("Projection ridge prediction design contains non-finite values")
    x = x_raw.copy()
    for column in range(1, x.shape[1]):
        if fit.zero_variance[column]:
            x[:, column] = 0.0
        else:
            x[:, column] = (
                x_raw[:, column] - fit.weighted_means[column]
            ) / fit.weighted_scales[column]
    predicted = x @ fit.coefficient_matrix
    if np.any(~np.isfinite(predicted)):
        raise ValueError("Projection ridge produced non-finite predictions")

    output = {"player_id": design.get_column("player_id").cast(pl.Int64)}
    for index, response in enumerate(fit.response_names):
        output[f"predicted_{response}"] = predicted[:, index].tolist()
    return pl.DataFrame(output).sort("player_id")
