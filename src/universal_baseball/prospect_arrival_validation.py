"""Chronology and proper-score guardrails for prospect-arrival research."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    """One bounded arrival-model candidate."""

    feature_set: str
    regularization_c: float

    @property
    def model_id(self) -> str:
        return f"{self.feature_set}__c_{self.regularization_c:g}"


def proper_scores(observed: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    """Return binary proper scores on one fixed cohort."""

    y = np.asarray(observed, dtype=float)
    p = np.asarray(probability, dtype=float)
    if y.ndim != 1 or p.shape != y.shape or y.size == 0:
        raise ValueError("observed and probability must be equal nonempty vectors")
    if not np.isin(y, (0.0, 1.0)).all():
        raise ValueError("observed outcomes must be binary")
    if not np.isfinite(p).all() or ((p < 0.0) | (p > 1.0)).any():
        raise ValueError("probabilities must be finite and inside [0, 1]")
    clipped = np.clip(p, 1e-12, 1.0 - 1e-12)
    return {
        "players": int(y.size),
        "observed_rate": float(y.mean()),
        "predicted_rate": float(p.mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(
            np.mean(-(y * np.log(clipped) + (1.0 - y) * np.log(1.0 - clipped)))
        ),
    }


def completed_evaluation_years(
    *, outer_year: int, horizon: int, evaluation_years: tuple[int, ...]
) -> tuple[int, ...]:
    """Return evaluation outcomes fully observable before an outer forecast."""

    if horizon < 1:
        raise ValueError("horizon must be positive")
    return tuple(
        year for year in evaluation_years if year + horizon <= outer_year
    )


def calibration_diagnostics(
    observed: np.ndarray, probability: np.ndarray, *, bins: int = 10
) -> dict[str, object]:
    """Return weak-calibration slope/intercept and equal-count reliability bins."""

    if bins < 2:
        raise ValueError("calibration requires at least two bins")
    y = np.asarray(observed, dtype=float)
    p = np.asarray(probability, dtype=float)
    proper_scores(y, p)
    if np.unique(y).size != 2:
        return {"intercept": None, "slope": None, "reliability_bins": []}
    clipped = np.clip(p, 1e-9, 1.0 - 1e-9)
    logit = np.log(clipped / (1.0 - clipped)).reshape(-1, 1)
    calibration = LogisticRegression(C=1e6, max_iter=2_000).fit(logit, y)
    ordered = np.argsort(p, kind="stable")
    cells = []
    for index, indices in enumerate(np.array_split(ordered, bins), start=1):
        if indices.size:
            cells.append(
                {
                    "bin": index,
                    "players": int(indices.size),
                    "predicted_rate": float(p[indices].mean()),
                    "observed_rate": float(y[indices].mean()),
                }
            )
    return {
        "intercept": float(calibration.intercept_[0]),
        "slope": float(calibration.coef_[0, 0]),
        "reliability_bins": cells,
    }


def select_nested_candidate(
    score_rows: list[dict[str, object]],
    *,
    eligible_years: tuple[int, ...],
    incumbent_id: str,
) -> str:
    """Select by earlier pooled log loss with Brier as a no-harm gate."""

    eligible = [
        row for row in score_rows if int(row["evaluation_year"]) in eligible_years
    ]
    if not eligible:
        return incumbent_id
    totals: dict[str, dict[str, float]] = {}
    for row in eligible:
        model_id = str(row["model_id"])
        cell = totals.setdefault(
            model_id, {"players": 0.0, "log_loss": 0.0, "brier": 0.0}
        )
        players = float(row["players"])
        cell["players"] += players
        cell["log_loss"] += players * float(row["log_loss"])
        cell["brier"] += players * float(row["brier"])
    if incumbent_id not in totals:
        raise ValueError("incumbent is missing from eligible score rows")
    for cell in totals.values():
        cell["log_loss"] /= cell["players"]
        cell["brier"] /= cell["players"]
    incumbent = totals[incumbent_id]
    passing = [
        model_id
        for model_id, cell in totals.items()
        if cell["log_loss"] < incumbent["log_loss"]
        and cell["brier"] <= incumbent["brier"]
    ]
    return min(
        passing,
        key=lambda model_id: (totals[model_id]["log_loss"], model_id),
        default=incumbent_id,
    )


def paired_bootstrap_difference(
    observed: np.ndarray,
    incumbent_probability: np.ndarray,
    candidate_probability: np.ndarray,
    *,
    resamples: int = 2_000,
    seed: int = 20260909,
) -> dict[str, float]:
    """Bootstrap candidate-minus-incumbent proper-score differences by player."""

    if resamples < 100:
        raise ValueError("at least 100 bootstrap resamples are required")
    y = np.asarray(observed, dtype=float)
    incumbent = np.asarray(incumbent_probability, dtype=float)
    candidate = np.asarray(candidate_probability, dtype=float)
    proper_scores(y, incumbent)
    proper_scores(y, candidate)
    incumbent_clip = np.clip(incumbent, 1e-12, 1.0 - 1e-12)
    candidate_clip = np.clip(candidate, 1e-12, 1.0 - 1e-12)
    brier_delta = (candidate - y) ** 2 - (incumbent - y) ** 2
    log_delta = -(
        y * np.log(candidate_clip) + (1.0 - y) * np.log(1.0 - candidate_clip)
    ) + (
        y * np.log(incumbent_clip) + (1.0 - y) * np.log(1.0 - incumbent_clip)
    )
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, y.size, size=(resamples, y.size))
    brier_samples = brier_delta[indices].mean(axis=1)
    log_samples = log_delta[indices].mean(axis=1)

    def summary(values: np.ndarray, estimate: float) -> dict[str, float]:
        return {
            "difference": float(estimate),
            "ci_low": float(np.quantile(values, 0.025)),
            "ci_high": float(np.quantile(values, 0.975)),
            "probability_candidate_better": float(np.mean(values < 0.0)),
        }

    return {
        "resamples": resamples,
        "brier": summary(brier_samples, float(brier_delta.mean())),
        "log_loss": summary(log_samples, float(log_delta.mean())),
    }
