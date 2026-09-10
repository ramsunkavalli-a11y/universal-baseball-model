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
CAREER_STATE_ORDER = {value: index for index, value in enumerate(CAREER_STATES)}


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


@dataclass(frozen=True, slots=True)
class TransitionHazardFit:
    player_type: str
    feature_set: str
    regularization_c: float
    models: dict[str, LogisticRegression]


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


def build_career_transition_rows(
    cumulative_cohorts: dict[int, pl.DataFrame], *, snapshot_year: int
) -> pl.DataFrame:
    """Turn cumulative horizon cohorts into monotone annual state transitions."""

    horizons = sorted(cumulative_cohorts)
    if not horizons or horizons != list(range(1, max(horizons) + 1)):
        raise ValueError("career transition horizons must be contiguous from one")
    first = add_career_state(cumulative_cohorts[1])
    players = first.select("player_id")
    if players.get_column("player_id").n_unique() != players.height:
        raise ValueError("career transition cohort violates player grain")
    previous = players.with_columns(pl.lit("NO_MLB").alias("from_state"))
    rows = []
    for horizon in horizons:
        current = add_career_state(cumulative_cohorts[horizon]).select(
            "player_id", pl.col("career_state").alias("to_state")
        )
        if current.height != players.height or current.join(
            players, on="player_id", how="anti"
        ).height:
            raise ValueError("career transition horizons do not share one cohort")
        transition = previous.join(current, on="player_id", validate="1:1").with_columns(
            pl.lit(snapshot_year).alias("snapshot_year"),
            pl.lit(horizon).alias("elapsed_year"),
            pl.lit(snapshot_year + horizon).alias("outcome_year"),
        )
        invalid = transition.filter(
            pl.col("to_state").replace_strict(CAREER_STATE_ORDER)
            < pl.col("from_state").replace_strict(CAREER_STATE_ORDER)
        )
        if invalid.height:
            raise ValueError("cumulative career state moved backward")
        rows.append(transition)
        previous = current.rename({"to_state": "from_state"})
    return pl.concat(rows, how="vertical").sort(["player_id", "elapsed_year"])


def _transition_design(frame: pl.DataFrame, *, feature_set: str) -> np.ndarray:
    aged = frame.with_columns(
        (pl.col("age_years") + pl.col("elapsed_year") - 1).alias("age_years")
    )
    base = arrival_design(aged, feature_set=feature_set)
    elapsed = aged.get_column("elapsed_year").to_numpy().astype(float)
    time = np.column_stack([
        (elapsed - 1.0) / 3.0,
        elapsed == 2,
        elapsed == 3,
        elapsed >= 4,
    ]).astype(float)
    return np.column_stack([base, time])


def fit_transition_hazard_model(
    frame: pl.DataFrame, *, player_type: str,
    feature_set: str = "level_exposure", regularization_c: float = 1.0,
) -> TransitionHazardFit:
    """Fit a separate forward-only next-state model for each nonterminal state."""

    required = {"from_state", "to_state", "elapsed_year", "age_years"}
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"transition hazard rows missing fields: {missing}")
    models = {}
    for origin in CAREER_STATES[:-1]:
        cell = frame.filter(pl.col("from_state") == origin)
        if cell.is_empty() or cell.get_column("to_state").n_unique() < 2:
            raise ValueError(f"transition hazard lacks outcomes for {origin}")
        if cell.filter(
            pl.col("to_state").replace_strict(CAREER_STATE_ORDER)
            < CAREER_STATE_ORDER[origin]
        ).height:
            raise ValueError("transition hazard contains backward movement")
        models[origin] = LogisticRegression(
            C=regularization_c, max_iter=2000
        ).fit(
            _transition_design(cell, feature_set=feature_set),
            cell.get_column("to_state").to_numpy(),
        )
    return TransitionHazardFit(
        player_type, feature_set, regularization_c, models
    )


def predict_transition_path(
    fit: TransitionHazardFit, frame: pl.DataFrame, *, horizon: int
) -> pl.DataFrame:
    """Propagate player-specific forward hazards through an ordered state simplex."""

    if horizon < 1:
        raise ValueError("transition horizon must be positive")
    probabilities = np.zeros((frame.height, len(CAREER_STATES)), dtype=float)
    probabilities[:, 0] = 1.0
    for elapsed_year in range(1, horizon + 1):
        scoring = frame.with_columns(pl.lit(elapsed_year).alias("elapsed_year"))
        design = _transition_design(scoring, feature_set=fit.feature_set)
        updated = np.zeros_like(probabilities)
        for origin_index, origin in enumerate(CAREER_STATES):
            mass = probabilities[:, origin_index]
            if origin == "ESTABLISHED_MLB":
                updated[:, origin_index] += mass
                continue
            model = fit.models[origin]
            conditional = model.predict_proba(design)
            for class_index, destination in enumerate(model.classes_):
                destination_index = CAREER_STATE_ORDER[str(destination)]
                if destination_index < origin_index:
                    raise ValueError("fitted transition hazard moves backward")
                updated[:, destination_index] += mass * conditional[:, class_index]
        probabilities = updated
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError("propagated transition probabilities do not sum to one")
    return frame.with_columns(*[
        pl.Series(f"p_{state.lower()}", probabilities[:, index])
        for index, state in enumerate(CAREER_STATES)
    ])
