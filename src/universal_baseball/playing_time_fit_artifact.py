"""Stable JSON contract for fitted playing-time hurdle models."""

from __future__ import annotations

from math import isfinite
from typing import Any, Mapping

from universal_baseball.playing_time_model import (
    PlayingTimeHurdleFit,
    PlayingTimeStandardization,
    playing_time_continuous_features,
    playing_time_feature_names,
)


FIT_ARTIFACT_SCHEMA_VERSION = "0.1"


def playing_time_fit_to_artifact(fit: PlayingTimeHurdleFit) -> dict[str, Any]:
    """Convert a fitted model to a deterministic, JSON-compatible payload."""

    return {
        "artifact_schema_version": FIT_ARTIFACT_SCHEMA_VERSION,
        "form": fit.form,
        "feature_names": list(fit.feature_names),
        "continuous_features": list(fit.continuous_features),
        "standardization": {
            "means": dict(sorted(fit.standardization.means.items())),
            "scales": dict(sorted(fit.standardization.scales.items())),
        },
        "logistic_intercept": fit.logistic_intercept,
        "logistic_coefficients": list(fit.logistic_coefficients),
        "nb_coefficients": list(fit.nb_coefficients),
        "nb_alpha": fit.nb_alpha,
        "participation_training_players": fit.participation_training_players,
        "positive_training_players": fit.positive_training_players,
        "metrics": fit.metrics,
    }


def playing_time_fit_from_artifact(
    payload: Mapping[str, Any],
) -> PlayingTimeHurdleFit:
    """Restore and validate one fitted model from its stable payload."""

    if payload.get("artifact_schema_version") != FIT_ARTIFACT_SCHEMA_VERSION:
        raise ValueError("unsupported playing-time fit artifact schema")
    form = str(payload.get("form", ""))
    expected_features = playing_time_feature_names(form)
    expected_continuous = playing_time_continuous_features(form)
    feature_names = tuple(str(value) for value in payload.get("feature_names", ()))
    continuous_features = tuple(
        str(value) for value in payload.get("continuous_features", ())
    )
    if feature_names != expected_features:
        raise ValueError("playing-time fit artifact feature contract differs from form")
    if continuous_features != expected_continuous:
        raise ValueError(
            "playing-time fit artifact continuous-feature contract differs from form"
        )

    standardization = payload.get("standardization")
    if not isinstance(standardization, Mapping):
        raise ValueError("playing-time fit artifact lacks standardization")
    raw_means = standardization.get("means")
    raw_scales = standardization.get("scales")
    if not isinstance(raw_means, Mapping) or not isinstance(raw_scales, Mapping):
        raise ValueError("playing-time fit artifact has invalid standardization")
    means = {str(key): float(value) for key, value in raw_means.items()}
    scales = {str(key): float(value) for key, value in raw_scales.items()}
    expected_keys = set(continuous_features)
    if set(means) != expected_keys or set(scales) != expected_keys:
        raise ValueError("playing-time fit artifact standardization keys differ")
    if any(not isfinite(value) for value in means.values()) or any(
        not isfinite(value) or value <= 0.0 for value in scales.values()
    ):
        raise ValueError("playing-time fit artifact standardization is invalid")

    logistic_intercept = float(payload.get("logistic_intercept"))
    logistic_coefficients = tuple(
        float(value) for value in payload.get("logistic_coefficients", ())
    )
    nb_coefficients = tuple(
        float(value) for value in payload.get("nb_coefficients", ())
    )
    nb_alpha = float(payload.get("nb_alpha"))
    if len(logistic_coefficients) != len(feature_names):
        raise ValueError("playing-time fit artifact logistic coefficient count differs")
    if len(nb_coefficients) != len(feature_names) + 1:
        raise ValueError("playing-time fit artifact NB coefficient count differs")
    numeric = (
        logistic_intercept,
        *logistic_coefficients,
        *nb_coefficients,
        nb_alpha,
    )
    if any(not isfinite(value) for value in numeric) or nb_alpha <= 0.0:
        raise ValueError("playing-time fit artifact coefficients are invalid")

    participation_players = int(payload.get("participation_training_players", 0))
    positive_players = int(payload.get("positive_training_players", 0))
    if participation_players <= 0 or not 0 < positive_players <= participation_players:
        raise ValueError("playing-time fit artifact training counts are invalid")
    metrics = payload.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ValueError("playing-time fit artifact metrics are invalid")

    return PlayingTimeHurdleFit(
        form=form,
        feature_names=feature_names,
        continuous_features=continuous_features,
        standardization=PlayingTimeStandardization(means=means, scales=scales),
        logistic_intercept=logistic_intercept,
        logistic_coefficients=logistic_coefficients,
        nb_coefficients=nb_coefficients,
        nb_alpha=nb_alpha,
        participation_training_players=participation_players,
        positive_training_players=positive_players,
        metrics=dict(metrics),
    )
