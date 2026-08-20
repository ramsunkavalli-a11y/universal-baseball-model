"""Pre-registered two-part MLB playing-time model primitives.

This module implements the frozen Playing Time / Role v1 statistical family:
L2 logistic participation plus zero-truncated NB2 positive MLB PA. It does not
select a feature form, score 2023/2024/2025, infer batting skill, or allocate team
roster slots.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite, lgamma, log, log1p
from typing import Any

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from statsmodels.discrete.truncated_model import TruncatedLFNegativeBinomialP

from universal_baseball.performance_season import ALL_CORE_BINS
from universal_baseball.projection_composition import projection_ilr_to_profile


PT_FORM_B0 = "playing_time_level_hurdle_v1"
PT_FORM_A = "playing_time_recent_opportunity_hurdle_v1"
PT_FORM_B = "playing_time_recent_opportunity_40man_hurdle_v1"
PT_FORM_C = "playing_time_recent_opportunity_40man_b2_hurdle_v1"
PT_FORMS = (PT_FORM_B0, PT_FORM_A, PT_FORM_B, PT_FORM_C)
PT_FORM_COMPLEXITY = {form: index for index, form in enumerate(PT_FORMS)}
LOGISTIC_C = 1.0
LEVEL_TIER_REFERENCE = "MLB"
LEVEL_TIER_LEVELS = ("AAA", "AA", "A_OR_BELOW")
CONTINUOUS_BASE = ("age_centered", "log_current_mlb_pa", "log_current_milb_pa")
B2_TALENT_FEATURES = (
    "b2_bb_hbp_probability",
    "b2_k_probability",
    "b2_non_iffb_offb_probability",
    "b2_ld_probability",
)
LEVEL_DUMMY_FEATURES = tuple(f"level_{value.lower()}" for value in LEVEL_TIER_LEVELS)
B2_ILR_COLUMNS = tuple(f"b2_ilr_{index:02d}" for index in range(11))
STANDARDIZATION_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class PlayingTimeStandardization:
    means: dict[str, float]
    scales: dict[str, float]


@dataclass(frozen=True, slots=True)
class PlayingTimeHurdleFit:
    form: str
    feature_names: tuple[str, ...]
    continuous_features: tuple[str, ...]
    standardization: PlayingTimeStandardization
    logistic_intercept: float
    logistic_coefficients: tuple[float, ...]
    nb_coefficients: tuple[float, ...]
    nb_alpha: float
    participation_training_players: int
    positive_training_players: int
    metrics: dict[str, Any]

    def coefficient_frame(self) -> pl.DataFrame:
        rows: list[dict[str, object]] = []
        rows.append(
            {
                "component": "participation_logit",
                "feature": "intercept",
                "coefficient": self.logistic_intercept,
            }
        )
        rows.extend(
            {
                "component": "participation_logit",
                "feature": feature,
                "coefficient": coefficient,
            }
            for feature, coefficient in zip(
                self.feature_names, self.logistic_coefficients, strict=True
            )
        )
        rows.extend(
            {
                "component": "positive_truncated_nb2",
                "feature": feature,
                "coefficient": coefficient,
            }
            for feature, coefficient in zip(
                ("intercept", *self.feature_names), self.nb_coefficients, strict=True
            )
        )
        rows.append(
            {
                "component": "positive_truncated_nb2",
                "feature": "alpha",
                "coefficient": self.nb_alpha,
            }
        )
        return pl.DataFrame(rows)

    def standardization_frame(self) -> pl.DataFrame:
        return pl.DataFrame(
            [
                {
                    "feature": feature,
                    "mean": self.standardization.means[feature],
                    "scale": self.standardization.scales[feature],
                }
                for feature in self.continuous_features
            ]
        )


def playing_time_level_tier(level_group: object) -> str:
    level = str(level_group)
    if level == "MLB":
        return "MLB"
    if level == "AAA":
        return "AAA"
    if level == "AA":
        return "AA"
    if level in {"HIGH_A", "SINGLE_A", "ROOKIE_COMPLEX", "High-A", "Single-A", "Rookie Complex"}:
        return "A_OR_BELOW"
    raise ValueError(f"unsupported playing-time as-of level: {level_group}")


def playing_time_feature_names(form: str) -> tuple[str, ...]:
    if form not in PT_FORMS:
        raise ValueError(f"unsupported playing-time form: {form}")
    features: list[str] = [*LEVEL_DUMMY_FEATURES]
    if PT_FORM_COMPLEXITY[form] >= PT_FORM_COMPLEXITY[PT_FORM_A]:
        features.extend(CONTINUOUS_BASE)
    if PT_FORM_COMPLEXITY[form] >= PT_FORM_COMPLEXITY[PT_FORM_B]:
        features.append("on_40man")
    if PT_FORM_COMPLEXITY[form] >= PT_FORM_COMPLEXITY[PT_FORM_C]:
        features.extend(B2_TALENT_FEATURES)
    return tuple(features)


def playing_time_continuous_features(form: str) -> tuple[str, ...]:
    features = playing_time_feature_names(form)
    return tuple(feature for feature in features if feature in {*CONTINUOUS_BASE, *B2_TALENT_FEATURES})


def _b2_talent_summary(row: dict[str, object]) -> dict[str, float]:
    coordinates = [float(row[column]) for column in B2_ILR_COLUMNS]
    if any(not isfinite(value) for value in coordinates):
        raise ValueError("playing-time B2 ILR coordinates must be finite")
    profile = projection_ilr_to_profile(coordinates)
    if set(profile) != set(ALL_CORE_BINS):
        raise ValueError("playing-time B2 ILR reconstruction has unexpected core bins")
    return {
        "b2_bb_hbp_probability": float(profile["BB_HBP"]),
        "b2_k_probability": float(profile["K"]),
        "b2_non_iffb_offb_probability": float(
            profile["PULL_OFFB"] + profile["CENTER_OFFB"] + profile["OPPO_OFFB"]
        ),
        "b2_ld_probability": float(
            profile["PULL_LD"] + profile["CENTER_LD"] + profile["OPPO_LD"]
        ),
    }


def build_playing_time_design(predictors: pl.DataFrame, *, form: str) -> pl.DataFrame:
    required = {
        "player_id",
        "age_years",
        "as_of_level_group",
        "current_season_mlb_pa",
        "current_season_milb_pa",
        "on_40man",
    }
    if form == PT_FORM_C:
        required.update(B2_ILR_COLUMNS)
    missing = sorted(required - set(predictors.columns))
    if missing:
        raise ValueError(f"playing-time predictors missing fields: {missing}")
    if predictors.is_empty():
        raise ValueError("playing-time predictor surface must not be empty")
    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("playing-time predictor surface violates player_id grain")

    feature_names = playing_time_feature_names(form)
    rows: list[dict[str, object]] = []
    for row in predictors.iter_rows(named=True):
        age = float(row["age_years"])
        mlb_pa = int(row["current_season_mlb_pa"])
        milb_pa = int(row["current_season_milb_pa"])
        if not isfinite(age) or mlb_pa < 0 or milb_pa < 0:
            raise ValueError("playing-time predictor age/PA fields are invalid")
        tier = playing_time_level_tier(row["as_of_level_group"])
        values: dict[str, object] = {
            "player_id": int(row["player_id"]),
            "level_aaa": 1.0 if tier == "AAA" else 0.0,
            "level_aa": 1.0 if tier == "AA" else 0.0,
            "level_a_or_below": 1.0 if tier == "A_OR_BELOW" else 0.0,
            "age_centered": (age - 25.0) / 5.0,
            "log_current_mlb_pa": log1p(float(mlb_pa)),
            "log_current_milb_pa": log1p(float(milb_pa)),
            "on_40man": 1.0 if bool(row["on_40man"]) else 0.0,
        }
        if form == PT_FORM_C:
            values.update(_b2_talent_summary(row))
        rows.append(values)
    return pl.DataFrame(rows).select("player_id", *feature_names).sort("player_id")


def _fit_standardization(
    design: pl.DataFrame,
    *,
    continuous_features: tuple[str, ...],
) -> PlayingTimeStandardization:
    means: dict[str, float] = {}
    scales: dict[str, float] = {}
    for feature in continuous_features:
        values = np.asarray(design.get_column(feature).to_numpy(), dtype=np.float64)
        mean = float(values.mean())
        scale = float(values.std(ddof=0))
        means[feature] = mean
        scales[feature] = 1.0 if scale <= STANDARDIZATION_EPSILON else scale
    return PlayingTimeStandardization(means=means, scales=scales)


def _design_matrix(
    design: pl.DataFrame,
    *,
    feature_names: tuple[str, ...],
    continuous_features: tuple[str, ...],
    standardization: PlayingTimeStandardization,
) -> np.ndarray:
    x = np.asarray(design.select(*feature_names).to_numpy(), dtype=np.float64)
    if not np.all(np.isfinite(x)):
        raise ValueError("playing-time design contains non-finite values")
    for index, feature in enumerate(feature_names):
        if feature in continuous_features:
            x[:, index] = (
                x[:, index] - standardization.means[feature]
            ) / standardization.scales[feature]
    return x


def _align_design_target(
    design: pl.DataFrame,
    targets: pl.DataFrame,
) -> pl.DataFrame:
    required = {"player_id", "next_year_mlb_pa"}
    missing = sorted(required - set(targets.columns))
    if missing:
        raise ValueError(f"playing-time targets missing fields: {missing}")
    if targets.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("playing-time targets violate player_id grain")
    design_ids = set(int(value) for value in design.get_column("player_id").to_list())
    target_ids = set(int(value) for value in targets.get_column("player_id").to_list())
    if design_ids != target_ids:
        raise ValueError("playing-time design/target player coverage differs")
    joined = design.join(
        targets.select("player_id", "next_year_mlb_pa"), on="player_id", how="inner"
    ).sort("player_id")
    if joined.filter(pl.col("next_year_mlb_pa") < 0).height:
        raise ValueError("playing-time targets contain negative MLB PA")
    return joined


def fit_playing_time_hurdle(
    design: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    form: str,
) -> PlayingTimeHurdleFit:
    feature_names = playing_time_feature_names(form)
    continuous_features = playing_time_continuous_features(form)
    missing = sorted(set(feature_names) - set(design.columns))
    if missing:
        raise ValueError(f"playing-time design missing frozen features: {missing}")
    aligned = _align_design_target(design, targets)
    standardization = _fit_standardization(
        aligned.select("player_id", *feature_names),
        continuous_features=continuous_features,
    )
    x = _design_matrix(
        aligned,
        feature_names=feature_names,
        continuous_features=continuous_features,
        standardization=standardization,
    )
    y_count = np.asarray(aligned.get_column("next_year_mlb_pa").to_numpy(), dtype=np.int64)
    y_participation = (y_count > 0).astype(np.int64)
    if np.unique(y_participation).size != 2:
        raise ValueError("playing-time participation training sample requires both classes")

    logistic = LogisticRegression(
        C=LOGISTIC_C,
        penalty="l2",
        solver="lbfgs",
        fit_intercept=True,
        class_weight=None,
        max_iter=2000,
        random_state=0,
    )
    logistic.fit(x, y_participation)
    if int(logistic.n_iter_[0]) >= 2000:
        raise RuntimeError("playing-time participation logistic did not converge")

    positive_mask = y_count > 0
    x_positive = x[positive_mask]
    y_positive = y_count[positive_mask].astype(np.float64)
    if y_positive.size <= len(feature_names) + 2:
        raise ValueError("playing-time positive-count sample is too small for frozen NB2 form")
    nb_exog = np.column_stack([np.ones(y_positive.size), x_positive])
    nb_model = TruncatedLFNegativeBinomialP(y_positive, nb_exog, p=2)
    nb_result = nb_model.fit(method="bfgs", maxiter=1000, disp=0)
    mle_retvals = getattr(nb_result, "mle_retvals", {}) or {}
    if not bool(mle_retvals.get("converged", True)):
        raise RuntimeError("playing-time truncated NB2 did not converge")
    params = np.asarray(nb_result.params, dtype=np.float64)
    if params.size != len(feature_names) + 2:
        raise RuntimeError("playing-time truncated NB2 returned unexpected parameter count")
    if not np.all(np.isfinite(params)):
        raise RuntimeError("playing-time truncated NB2 returned non-finite parameters")
    alpha = float(params[-1])
    if not isfinite(alpha) or alpha <= 0.0:
        raise RuntimeError(f"playing-time truncated NB2 alpha must be positive, observed {alpha}")

    metrics = {
        "form": form,
        "participation_model": "sklearn_logistic_l2",
        "participation_C": LOGISTIC_C,
        "positive_count_model": "statsmodels_zero_truncated_negative_binomial_p2",
        "participation_training_players": int(y_count.size),
        "positive_training_players": int(y_positive.size),
        "feature_count": len(feature_names),
        "future_team_used": False,
        "future_level_used": False,
        "batting_rate_modified": False,
    }
    return PlayingTimeHurdleFit(
        form=form,
        feature_names=feature_names,
        continuous_features=continuous_features,
        standardization=standardization,
        logistic_intercept=float(logistic.intercept_[0]),
        logistic_coefficients=tuple(float(value) for value in logistic.coef_[0]),
        nb_coefficients=tuple(float(value) for value in params[:-1]),
        nb_alpha=alpha,
        participation_training_players=int(y_count.size),
        positive_training_players=int(y_positive.size),
        metrics=metrics,
    )


def _sigmoid(value: np.ndarray) -> np.ndarray:
    output = np.empty_like(value, dtype=np.float64)
    positive = value >= 0
    output[positive] = 1.0 / (1.0 + np.exp(-value[positive]))
    exp_value = np.exp(value[~positive])
    output[~positive] = exp_value / (1.0 + exp_value)
    return output


def _nb2_logpmf(y: int, mu: float, alpha: float) -> float:
    if y < 0 or mu <= 0.0 or alpha <= 0.0:
        raise ValueError("invalid NB2 arguments")
    size = 1.0 / alpha
    probability = size / (size + mu)
    return (
        lgamma(y + size)
        - lgamma(size)
        - lgamma(y + 1.0)
        + size * log(probability)
        + y * log1p(-probability)
    )


def _truncated_nb2_logpmf(y: int, mu: float, alpha: float) -> float:
    if y <= 0:
        raise ValueError("zero-truncated NB2 requires positive y")
    size = 1.0 / alpha
    probability = size / (size + mu)
    log_p0 = size * log(probability)
    p0 = exp(log_p0)
    if not 0.0 <= p0 < 1.0:
        raise RuntimeError("invalid NB2 zero probability")
    return _nb2_logpmf(y, mu, alpha) - log1p(-p0)


def score_playing_time_hurdle(
    fit: PlayingTimeHurdleFit,
    design: pl.DataFrame,
    targets: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    aligned = _align_design_target(design, targets)
    x = _design_matrix(
        aligned,
        feature_names=fit.feature_names,
        continuous_features=fit.continuous_features,
        standardization=fit.standardization,
    )
    y = np.asarray(aligned.get_column("next_year_mlb_pa").to_numpy(), dtype=np.int64)
    logistic_beta = np.asarray(fit.logistic_coefficients, dtype=np.float64)
    p_participation = _sigmoid(fit.logistic_intercept + x @ logistic_beta)
    p_participation = np.clip(p_participation, 1e-12, 1.0 - 1e-12)

    nb_beta = np.asarray(fit.nb_coefficients, dtype=np.float64)
    nb_exog = np.column_stack([np.ones(x.shape[0]), x])
    mu = np.exp(nb_exog @ nb_beta)
    if np.any(~np.isfinite(mu)) or np.any(mu <= 0.0):
        raise RuntimeError("playing-time NB2 prediction produced invalid means")
    size = 1.0 / fit.nb_alpha
    nb_probability = size / (size + mu)
    p_zero_untruncated = np.power(nb_probability, size)
    conditional_positive_mean = mu / (1.0 - p_zero_untruncated)
    expected_mlb_pa = p_participation * conditional_positive_mean

    rows: list[dict[str, object]] = []
    full_negative_log_likelihood: list[float] = []
    participation_negative_log_likelihood: list[float] = []
    positive_negative_log_likelihood: list[float] = []
    for index, player_id in enumerate(aligned.get_column("player_id").to_list()):
        observed = int(y[index])
        p = float(p_participation[index])
        participation_nll = -log(p if observed > 0 else 1.0 - p)
        if observed > 0:
            conditional_logpmf = _truncated_nb2_logpmf(
                observed, float(mu[index]), fit.nb_alpha
            )
            positive_nll = -conditional_logpmf
            full_nll = -log(p) + positive_nll
            positive_negative_log_likelihood.append(positive_nll)
        else:
            positive_nll = None
            full_nll = -log(1.0 - p)
        participation_negative_log_likelihood.append(participation_nll)
        full_negative_log_likelihood.append(full_nll)
        rows.append(
            {
                "player_id": int(player_id),
                "observed_mlb_pa": observed,
                "observed_any_mlb_pa": observed > 0,
                "predicted_any_mlb_pa_probability": p,
                "predicted_positive_mlb_pa_mean": float(conditional_positive_mean[index]),
                "predicted_expected_mlb_pa": float(expected_mlb_pa[index]),
                "full_negative_log_likelihood": float(full_nll),
                "participation_negative_log_likelihood": float(participation_nll),
                "positive_count_negative_log_likelihood": positive_nll,
            }
        )

    frame = pl.DataFrame(rows).sort("player_id")
    observed = frame.get_column("observed_mlb_pa").cast(pl.Float64)
    predicted = frame.get_column("predicted_expected_mlb_pa")
    participation_observed = frame.get_column("observed_any_mlb_pa").cast(pl.Float64)
    participation_predicted = frame.get_column("predicted_any_mlb_pa_probability")
    positive_frame = frame.filter(pl.col("observed_mlb_pa") > 0)
    metrics: dict[str, Any] = {
        "form": fit.form,
        "scored_players": int(frame.height),
        "positive_players": int(positive_frame.height),
        "mean_full_negative_log_likelihood": float(
            frame.get_column("full_negative_log_likelihood").mean()
        ),
        "participation_log_loss": float(
            frame.get_column("participation_negative_log_likelihood").mean()
        ),
        "participation_brier": float(
            ((participation_predicted - participation_observed) ** 2).mean()
        ),
        "positive_count_negative_log_likelihood": float(
            positive_frame.get_column("positive_count_negative_log_likelihood").mean()
        )
        if positive_frame.height
        else None,
        "unconditional_mlb_pa_mae": float((predicted - observed).abs().mean()),
        "unconditional_mlb_pa_rmse": float((((predicted - observed) ** 2).mean()) ** 0.5),
        "observed_mean_mlb_pa": float(observed.mean()),
        "predicted_mean_mlb_pa": float(predicted.mean()),
        "coverage_identical": True,
    }
    return frame, metrics
