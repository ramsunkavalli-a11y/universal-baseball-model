"""Chronology and proper-score guardrails for prospect-arrival research."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

import numpy as np
from sklearn.linear_model import LogisticRegression


@dataclass(frozen=True, slots=True)
class CandidateSpec:
    """One bounded arrival-model candidate."""

    feature_set: str
    regularization_c: float
    production_regression: float = 0.0

    @property
    def model_id(self) -> str:
        base = f"{self.feature_set}__c_{self.regularization_c:g}"
        if self.production_regression > 0:
            return f"{base}__rate_reg_{self.production_regression:g}"
        return base


@dataclass(frozen=True, slots=True)
class ForecastExperimentProtocol:
    """Frozen identity and chronology for one bounded forecast experiment.

    The protocol is deliberately model-agnostic.  It can guard demographic,
    performance, play-by-play, role, or workload candidate families without
    allowing the family or evaluation dates to change after an outer result is
    seen.
    """

    name: str
    target: str
    player_universe: str
    horizon: int
    incumbent_id: str
    candidate_ids: tuple[str, ...]
    selection_origins: tuple[int, ...]
    outer_origin: int
    outcome_available_through: int

    def validate(self) -> None:
        if not self.name.strip() or not self.target.strip() or not self.player_universe.strip():
            raise ValueError("experiment name, target, and player universe are required")
        if self.horizon < 1:
            raise ValueError("experiment horizon must be positive")
        if not self.candidate_ids:
            raise ValueError("candidate family must not be empty")
        if len(set(self.candidate_ids)) != len(self.candidate_ids):
            raise ValueError("candidate IDs must be unique")
        if self.incumbent_id not in self.candidate_ids:
            raise ValueError("incumbent must be part of the frozen candidate family")
        if tuple(sorted(set(self.selection_origins))) != self.selection_origins:
            raise ValueError("selection origins must be unique and increasing")
        if not self.selection_origins:
            raise ValueError("at least one selection origin is required")
        if any(origin >= self.outer_origin for origin in self.selection_origins):
            raise ValueError("selection origins must precede the outer origin")
        if any(
            origin + self.horizon > self.outcome_available_through
            for origin in (*self.selection_origins, self.outer_origin)
        ):
            raise ValueError("an evaluation outcome is not fully observable")

    @property
    def fingerprint(self) -> str:
        """Stable hash proving which family and chronology were evaluated."""

        self.validate()
        payload = {
            "candidate_ids": self.candidate_ids,
            "horizon": self.horizon,
            "incumbent_id": self.incumbent_id,
            "name": self.name,
            "outcome_available_through": self.outcome_available_through,
            "outer_origin": self.outer_origin,
            "player_universe": self.player_universe,
            "selection_origins": self.selection_origins,
            "target": self.target,
        }
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def as_dict(self, *, include_candidate_ids: bool = True) -> dict[str, object]:
        self.validate()
        result: dict[str, object] = {
            "name": self.name,
            "target": self.target,
            "player_universe": self.player_universe,
            "horizon": self.horizon,
            "incumbent_id": self.incumbent_id,
            "candidate_count": len(self.candidate_ids),
            "selection_origins": list(self.selection_origins),
            "outer_origin": self.outer_origin,
            "outcome_available_through": self.outcome_available_through,
            "fingerprint": self.fingerprint,
        }
        if include_candidate_ids:
            result["candidate_ids"] = list(self.candidate_ids)
        return result


def common_cohort_fingerprint(
    player_ids: np.ndarray, observed: np.ndarray, predictions: dict[str, np.ndarray]
) -> str:
    """Validate identical rows and return a stable evaluation-cohort hash."""

    ids = np.asarray(player_ids)
    y = np.asarray(observed, dtype=float)
    if ids.ndim != 1 or ids.size == 0 or y.shape != ids.shape:
        raise ValueError("player IDs and outcomes must be equal nonempty vectors")
    if np.unique(ids).size != ids.size:
        raise ValueError("evaluation player IDs must be unique")
    if not predictions:
        raise ValueError("at least one prediction vector is required")
    for model_id, probability in predictions.items():
        if np.asarray(probability).shape != y.shape:
            raise ValueError(f"{model_id} does not use the common evaluation cohort")
        proper_scores(y, np.asarray(probability, dtype=float))
    rows = sorted((str(player_id), int(outcome)) for player_id, outcome in zip(ids, y))
    return sha256(
        json.dumps(rows, separators=(",", ":")).encode()
    ).hexdigest()


def continuous_scores(
    observed: np.ndarray, prediction: np.ndarray
) -> dict[str, float | int]:
    """Return scale, bias, MAE, and RMSE on one fixed continuous-outcome cohort."""

    y = np.asarray(observed, dtype=float)
    p = np.asarray(prediction, dtype=float)
    if y.ndim != 1 or p.shape != y.shape or y.size == 0:
        raise ValueError("observed and prediction must be equal nonempty vectors")
    if not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("continuous outcomes and predictions must be finite")
    error = p - y
    return {
        "players": int(y.size),
        "observed_mean": float(y.mean()),
        "predicted_mean": float(p.mean()),
        "bias": float(error.mean()),
        "mae": float(np.abs(error).mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
    }


def common_continuous_cohort_fingerprint(
    player_ids: np.ndarray, observed: np.ndarray, predictions: dict[str, np.ndarray]
) -> str:
    """Validate common continuous-outcome rows and hash the evaluation cohort."""

    ids = np.asarray(player_ids)
    y = np.asarray(observed, dtype=float)
    if ids.ndim != 1 or ids.size == 0 or y.shape != ids.shape:
        raise ValueError("player IDs and outcomes must be equal nonempty vectors")
    if np.unique(ids).size != ids.size:
        raise ValueError("evaluation player IDs must be unique")
    if not predictions:
        raise ValueError("at least one prediction vector is required")
    for model_id, prediction in predictions.items():
        if np.asarray(prediction).shape != y.shape:
            raise ValueError(f"{model_id} does not use the common evaluation cohort")
        continuous_scores(y, np.asarray(prediction, dtype=float))
    rows = sorted((str(player_id), float(outcome)) for player_id, outcome in zip(ids, y))
    return sha256(
        json.dumps(rows, separators=(",", ":")).encode()
    ).hexdigest()


def paired_continuous_bootstrap_difference(
    observed: np.ndarray,
    incumbent_prediction: np.ndarray,
    candidate_prediction: np.ndarray,
    *,
    resamples: int = 2_000,
    seed: int = 20260910,
) -> dict[str, object]:
    """Bootstrap candidate-minus-incumbent MSE and absolute-error differences."""

    if resamples < 100:
        raise ValueError("at least 100 bootstrap resamples are required")
    y = np.asarray(observed, dtype=float)
    incumbent = np.asarray(incumbent_prediction, dtype=float)
    candidate = np.asarray(candidate_prediction, dtype=float)
    continuous_scores(y, incumbent)
    continuous_scores(y, candidate)
    mse_delta = (candidate - y) ** 2 - (incumbent - y) ** 2
    mae_delta = np.abs(candidate - y) - np.abs(incumbent - y)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, y.size, size=(resamples, y.size))

    def summary(values: np.ndarray) -> dict[str, float]:
        samples = values[indices].mean(axis=1)
        return {
            "difference": float(values.mean()),
            "ci_low": float(np.quantile(samples, 0.025)),
            "ci_high": float(np.quantile(samples, 0.975)),
            "probability_candidate_better": float(np.mean(samples < 0.0)),
        }

    return {
        "resamples": resamples,
        "mse": summary(mse_delta),
        "mae": summary(mae_delta),
    }


def continuous_promotion_gate(
    incumbent_scores: dict[str, float | int],
    candidate_scores: dict[str, float | int],
    paired_difference: dict[str, object],
    *,
    subgroup_review_passed: bool,
    fresh_confirmation: bool,
) -> dict[str, object]:
    """Require accuracy, scale, subgroup, and fresh-confirmation evidence."""

    reasons: list[str] = []
    for score in ("mse", "mae"):
        result = paired_difference.get(score)
        if not isinstance(result, dict):
            raise ValueError(f"paired result is missing {score}")
        if float(result["difference"]) >= 0:
            reasons.append(f"{score} point estimate did not improve")
        if float(result["ci_high"]) >= 0:
            reasons.append(f"{score} paired interval includes no improvement")
    if abs(float(candidate_scores["bias"])) > abs(float(incumbent_scores["bias"])):
        reasons.append("absolute forecast bias worsened")
    if not subgroup_review_passed:
        reasons.append("supported-subgroup review did not pass")
    if not fresh_confirmation:
        reasons.append("fresh confirmation is still required")
    return {"promote": not reasons, "reasons": reasons}


def promotion_gate(
    paired_difference: dict[str, object],
    *,
    calibration_review_passed: bool,
    subgroup_review_passed: bool,
    fresh_confirmation: bool,
) -> dict[str, object]:
    """Apply conservative, predeclared gates to an outer comparison.

    Point-score wins alone are insufficient. Both proper-score paired intervals,
    calibration, supported subgroups, and a genuinely fresh confirmation must pass.
    """

    reasons: list[str] = []
    for score in ("log_loss", "brier"):
        result = paired_difference.get(score)
        if not isinstance(result, dict):
            raise ValueError(f"paired result is missing {score}")
        difference = float(result["difference"])
        ci_high = float(result["ci_high"])
        if difference >= 0:
            reasons.append(f"{score} point estimate did not improve")
        if ci_high >= 0:
            reasons.append(f"{score} paired interval includes no improvement")
    if not calibration_review_passed:
        reasons.append("calibration review did not pass")
    if not subgroup_review_passed:
        reasons.append("supported-subgroup review did not pass")
    if not fresh_confirmation:
        reasons.append("fresh confirmation is still required")
    return {"promote": not reasons, "reasons": reasons}


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
