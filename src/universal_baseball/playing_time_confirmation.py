"""Frozen Playing Time v1 confirmation loading and decision helpers.

These helpers reconstruct an already-frozen hurdle fit from persisted parameter
tables and apply the pre-registered 2025 confirmation decision. They never fit,
reselect, recalibrate prediction parameters, or alter batting-rate skill.
"""

from __future__ import annotations

from math import isfinite, log
from typing import Any

import numpy as np
import polars as pl
import statsmodels.api as sm

from universal_baseball.playing_time_model import (
    PlayingTimeHurdleFit,
    PlayingTimeStandardization,
    playing_time_continuous_features,
    playing_time_feature_names,
)


CONFIRMATION_MAE_WORSE_TOLERANCE = 0.02


def _coefficient_value(
    coefficients: pl.DataFrame,
    *,
    component: str,
    feature: str,
) -> float:
    required = {"component", "feature", "coefficient"}
    missing = sorted(required - set(coefficients.columns))
    if missing:
        raise ValueError(f"frozen coefficient table missing fields: {missing}")
    matched = coefficients.filter(
        (pl.col("component") == component) & (pl.col("feature") == feature)
    )
    if matched.height != 1:
        raise ValueError(
            f"expected one frozen coefficient for {component}/{feature}, found {matched.height}"
        )
    value = float(matched.item(0, "coefficient"))
    if not isfinite(value):
        raise ValueError(f"non-finite frozen coefficient for {component}/{feature}")
    return value


def load_frozen_playing_time_fit(
    coefficients: pl.DataFrame,
    standardization: pl.DataFrame,
    *,
    form: str,
    expected_nb_alpha: float,
    participation_training_players: int,
    positive_training_players: int,
) -> PlayingTimeHurdleFit:
    """Reconstruct one frozen hurdle fit without running either estimator."""

    feature_names = playing_time_feature_names(form)
    continuous_features = playing_time_continuous_features(form)
    expected_rows = {
        *(('participation_logit', feature) for feature in ('intercept', *feature_names)),
        *(('positive_truncated_nb2', feature) for feature in ('intercept', *feature_names, 'alpha')),
    }
    observed_rows = set(
        zip(
            coefficients.get_column("component").cast(pl.String).to_list(),
            coefficients.get_column("feature").cast(pl.String).to_list(),
            strict=True,
        )
    )
    if observed_rows != expected_rows:
        raise ValueError(
            "frozen coefficient table does not exactly match form contract: "
            f"missing={sorted(expected_rows-observed_rows)}, extra={sorted(observed_rows-expected_rows)}"
        )

    if continuous_features:
        required_standardization = {"feature", "mean", "scale"}
        missing = sorted(required_standardization - set(standardization.columns))
        if missing:
            raise ValueError(f"frozen standardization table missing fields: {missing}")
        if standardization.group_by("feature").len().filter(pl.col("len") != 1).height:
            raise ValueError("frozen standardization table violates feature grain")
        observed_standardization = set(
            standardization.get_column("feature").cast(pl.String).to_list()
        )
        if observed_standardization != set(continuous_features):
            raise ValueError(
                "frozen standardization features do not match form contract: "
                f"observed={sorted(observed_standardization)}"
            )
        means = {
            feature: float(
                standardization.filter(pl.col("feature") == feature).item(0, "mean")
            )
            for feature in continuous_features
        }
        scales = {
            feature: float(
                standardization.filter(pl.col("feature") == feature).item(0, "scale")
            )
            for feature in continuous_features
        }
        if any(not isfinite(value) for value in means.values()):
            raise ValueError("frozen standardization contains non-finite mean")
        if any(not isfinite(value) or value <= 0.0 for value in scales.values()):
            raise ValueError("frozen standardization contains invalid scale")
    else:
        if standardization.height != 0:
            raise ValueError("form without continuous features has non-empty standardization")
        means = {}
        scales = {}

    nb_alpha = _coefficient_value(
        coefficients,
        component="positive_truncated_nb2",
        feature="alpha",
    )
    if not isfinite(expected_nb_alpha) or expected_nb_alpha <= 0.0:
        raise ValueError("expected frozen NB alpha is invalid")
    if abs(nb_alpha - float(expected_nb_alpha)) > 1e-12:
        raise ValueError(
            f"frozen NB alpha differs from binding refit record: {nb_alpha} != {expected_nb_alpha}"
        )

    return PlayingTimeHurdleFit(
        form=form,
        feature_names=feature_names,
        continuous_features=continuous_features,
        standardization=PlayingTimeStandardization(means=means, scales=scales),
        logistic_intercept=_coefficient_value(
            coefficients, component="participation_logit", feature="intercept"
        ),
        logistic_coefficients=tuple(
            _coefficient_value(
                coefficients,
                component="participation_logit",
                feature=feature,
            )
            for feature in feature_names
        ),
        nb_coefficients=tuple(
            _coefficient_value(
                coefficients,
                component="positive_truncated_nb2",
                feature=feature,
            )
            for feature in ("intercept", *feature_names)
        ),
        nb_alpha=nb_alpha,
        participation_training_players=int(participation_training_players),
        positive_training_players=int(positive_training_players),
        metrics={
            "loaded_from_frozen_pre_2025_parameters": True,
            "model_refit": False,
            "form_reselected": False,
        },
    )


def participation_calibration(scored: pl.DataFrame) -> dict[str, Any]:
    """Fit the predeclared diagnostic calibration intercept/slope only."""

    probabilities = np.asarray(
        scored.get_column("predicted_any_mlb_pa_probability").to_numpy(),
        dtype=np.float64,
    )
    observed = np.asarray(
        scored.get_column("observed_any_mlb_pa").cast(pl.Int64).to_numpy(),
        dtype=np.float64,
    )
    if np.unique(observed).size < 2:
        return {
            "identifiable": False,
            "converged": None,
            "intercept": None,
            "slope": None,
            "finite_parameters": None,
            "reason": "participation outcome has only one class",
        }
    probabilities = np.clip(probabilities, 1e-12, 1.0 - 1e-12)
    logits = np.asarray([log(value / (1.0 - value)) for value in probabilities], dtype=np.float64)
    exog = sm.add_constant(logits, has_constant="add")
    try:
        result = sm.GLM(observed, exog, family=sm.families.Binomial()).fit()
        params = np.asarray(result.params, dtype=np.float64)
        finite = bool(params.size == 2 and np.all(np.isfinite(params)))
        return {
            "identifiable": True,
            "converged": bool(getattr(result, "converged", True)),
            "intercept": float(params[0]) if params.size >= 1 else None,
            "slope": float(params[1]) if params.size >= 2 else None,
            "finite_parameters": finite,
            "reason": None,
        }
    except Exception as exc:  # diagnostic failure must fail confirmation closed
        return {
            "identifiable": True,
            "converged": False,
            "intercept": None,
            "slope": None,
            "finite_parameters": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }


def confirmation_decision(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    *,
    baseline_calibration: dict[str, Any],
    candidate_calibration: dict[str, Any],
    coverage_identical: bool,
) -> dict[str, Any]:
    """Apply the frozen all-gates 2025 confirmation rule."""

    baseline_positive_nll = baseline_metrics.get("positive_count_negative_log_likelihood")
    candidate_positive_nll = candidate_metrics.get("positive_count_negative_log_likelihood")
    positive_nll_available = baseline_positive_nll is not None and candidate_positive_nll is not None

    full_nll_pass = float(candidate_metrics["mean_full_negative_log_likelihood"]) < float(
        baseline_metrics["mean_full_negative_log_likelihood"]
    )
    participation_pass = float(candidate_metrics["participation_log_loss"]) <= float(
        baseline_metrics["participation_log_loss"]
    )
    positive_count_pass = bool(
        positive_nll_available
        and float(candidate_positive_nll) <= float(baseline_positive_nll)
    )
    mae_limit = float(baseline_metrics["unconditional_mlb_pa_mae"]) * (
        1.0 + CONFIRMATION_MAE_WORSE_TOLERANCE
    )
    mae_pass = float(candidate_metrics["unconditional_mlb_pa_mae"]) <= mae_limit

    def calibration_pass(calibration: dict[str, Any]) -> bool:
        if not bool(calibration.get("identifiable")):
            return True
        return bool(calibration.get("converged")) and bool(
            calibration.get("finite_parameters")
        )

    baseline_calibration_pass = calibration_pass(baseline_calibration)
    candidate_calibration_pass = calibration_pass(candidate_calibration)
    calibration_gate_pass = baseline_calibration_pass and candidate_calibration_pass

    gates = {
        "candidate_full_nll_strictly_lower_than_b0": full_nll_pass,
        "candidate_participation_log_loss_no_worse_than_b0": participation_pass,
        "candidate_positive_count_nll_no_worse_than_b0": positive_count_pass,
        "candidate_unconditional_pa_mae_within_2pct_of_b0": mae_pass,
        "identical_scored_player_coverage": bool(coverage_identical),
        "participation_calibration_converged_with_finite_parameters_where_identifiable": calibration_gate_pass,
    }
    confirmed = all(gates.values())
    return {
        "confirmed": confirmed,
        "gates": gates,
        "mae_worse_tolerance": CONFIRMATION_MAE_WORSE_TOLERANCE,
        "candidate_mae_limit": mae_limit,
        "baseline_calibration_gate_pass": baseline_calibration_pass,
        "candidate_calibration_gate_pass": candidate_calibration_pass,
        "production_model_decision": "candidate" if confirmed else "baseline0",
    }
