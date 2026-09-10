"""Mutually exclusive one-year prospect career-state transition model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.prospect_arrival import (
    arrival_design,
    fit_arrival_model,
    predict_arrival,
)


CAREER_STATES = ("NO_MLB", "FRINGE_MLB", "MEANINGFUL_MLB", "ESTABLISHED_MLB")


def add_career_state(frame: pl.DataFrame) -> pl.DataFrame:
    """Collapse ordered cumulative outcomes to one exhaustive state."""

    required = {
        "arrived_within_horizon", "meaningful_role_within_horizon",
        "established_role_within_horizon",
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"career-state cohort missing fields: {missing}")
    invalid = frame.filter(
        (pl.col("meaningful_role_within_horizon") > pl.col("arrived_within_horizon"))
        | (pl.col("established_role_within_horizon") > pl.col("meaningful_role_within_horizon"))
    )
    if invalid.height:
        raise ValueError("career-state outcomes are not ordered")
    return frame.with_columns(
        pl.when(pl.col("established_role_within_horizon") == 1)
        .then(pl.lit("ESTABLISHED_MLB"))
        .when(pl.col("meaningful_role_within_horizon") == 1)
        .then(pl.lit("MEANINGFUL_MLB"))
        .when(pl.col("arrived_within_horizon") == 1)
        .then(pl.lit("FRINGE_MLB"))
        .otherwise(pl.lit("NO_MLB"))
        .alias("career_state")
    )


@dataclass(frozen=True, slots=True)
class CareerStateFit:
    player_type: str
    feature_set: str
    regularization_c: float
    model: LogisticRegression


def fit_career_state_model(
    frame: pl.DataFrame, *, player_type: str,
    feature_set: str = "level_exposure", regularization_c: float = 1.0,
) -> CareerStateFit:
    if regularization_c <= 0:
        raise ValueError("career-state regularization must be positive")
    source = add_career_state(frame)
    if set(source.get_column("career_state")) != set(CAREER_STATES):
        raise ValueError("career-state fit requires all four states")
    model = LogisticRegression(C=regularization_c, max_iter=2000).fit(
        arrival_design(source, feature_set=feature_set),
        source.get_column("career_state").to_numpy(),
    )
    return CareerStateFit(player_type, feature_set, regularization_c, model)


def predict_career_state(fit: CareerStateFit, frame: pl.DataFrame) -> pl.DataFrame:
    probabilities = fit.model.predict_proba(
        arrival_design(frame, feature_set=fit.feature_set)
    )
    lookup = {str(value): index for index, value in enumerate(fit.model.classes_)}
    return frame.with_columns(*[
        pl.Series(f"p_{state.lower()}", probabilities[:, lookup[state]])
        for state in CAREER_STATES
    ])


def predict_independent_ordered_state(
    training: pl.DataFrame, evaluation: pl.DataFrame, *, player_type: str,
    feature_set: str = "level_exposure", regularization_c: float = 1.0,
) -> pl.DataFrame:
    """Coherent class probabilities from separately fitted cumulative logits."""

    predicted = evaluation
    definitions = (
        ("arrival", "arrived_within_horizon"),
        ("meaningful", "meaningful_role_within_horizon"),
        ("established", "established_role_within_horizon"),
    )
    for name, target in definitions:
        fit = fit_arrival_model(
            training, player_type=player_type, target_column=target,
            outcome_name=name, feature_set=feature_set,
            regularization_c=regularization_c,
        )
        predicted = predict_arrival(fit, predicted)
    return predicted.with_columns(
        pl.col("predicted_two_year_arrival_probability").alias("_a"),
        pl.min_horizontal(
            "predicted_two_year_arrival_probability",
            "predicted_two_year_meaningful_probability",
        ).alias("_m"),
    ).with_columns(
        pl.min_horizontal(
            "_m", "predicted_two_year_established_probability"
        ).alias("_e")
    ).with_columns(
        (1 - pl.col("_a")).alias("p_no_mlb"),
        (pl.col("_a") - pl.col("_m")).alias("p_fringe_mlb"),
        (pl.col("_m") - pl.col("_e")).alias("p_meaningful_mlb"),
        pl.col("_e").alias("p_established_mlb"),
    ).drop("_a", "_m", "_e")


def career_state_scores(frame: pl.DataFrame) -> dict[str, float | int]:
    source = add_career_state(frame)
    state = source.get_column("career_state").to_numpy()
    probabilities = np.column_stack([
        source.get_column(f"p_{value.lower()}").to_numpy()
        for value in CAREER_STATES
    ])
    if np.any(probabilities < 0) or not np.allclose(probabilities.sum(axis=1), 1.0):
        raise ValueError("career-state probabilities are not a simplex")
    truth = np.column_stack([state == value for value in CAREER_STATES]).astype(float)
    chosen = probabilities[np.arange(len(state)), np.argmax(truth, axis=1)]
    return {
        "players": len(state),
        "multiclass_log_loss": float(-np.mean(np.log(np.clip(chosen, 1e-12, 1)))),
        "multiclass_brier": float(np.mean(np.sum((probabilities - truth) ** 2, axis=1))),
    }
