"""Personnel-adjusted event model for descriptive park effects.

The estimator uses only outcome labels and ordinary game context.  Statcast
quality measurements such as exit velocity and launch angle are intentionally
absent.  Batter and pitcher identity are nuisance controls; only venue
coefficients leave this module as park effects.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl


@dataclass(frozen=True, slots=True)
class EventParkFit:
    factors: pl.DataFrame
    validation: dict[str, float | int]


def _matrix(frame: pl.DataFrame, columns: list[str]) -> np.ndarray:
    return np.asarray(
        [[str(row[column]) for column in columns] for row in frame.iter_rows(named=True)],
        dtype=object,
    )


def _scores(observed: np.ndarray, probability: np.ndarray) -> tuple[float, float]:
    clipped = np.clip(probability, 1e-15, 1.0)
    log_loss = -float(np.mean(np.log(clipped[np.arange(len(observed)), observed])))
    truth = np.eye(probability.shape[1])[observed]
    brier = float(np.mean(np.sum((probability - truth) ** 2, axis=1)))
    return log_loss, brier


def fit_event_context_park_factors(
    events: pl.DataFrame,
    *,
    outcome_column: str = "outcome",
    regularization_c: float = 0.1,
    validation_fraction: float = 0.25,
) -> EventParkFit:
    """Fit batter/pitcher/hand controls with and without venue on a time split."""

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder, OneHotEncoder
    except ImportError as exc:  # pragma: no cover - environment boundary
        raise RuntimeError("event park fitting requires the playing-time extra") from exc

    required = {
        "game_date",
        "batter_id",
        "pitcher_id",
        "batter_side",
        "pitcher_hand",
        "venue_id",
        outcome_column,
    }
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"event park source missing fields: {missing}")
    if not 0 < validation_fraction < 0.5 or regularization_c <= 0:
        raise ValueError("validation fraction and regularization must be positive")
    working = events.drop_nulls(list(required)).sort("game_date")
    if working.height < 100:
        raise ValueError("event park fit requires at least 100 complete events")
    dates = working["game_date"].unique().sort()
    split_index = max(1, int(len(dates) * (1.0 - validation_fraction)))
    if split_index >= len(dates):
        raise ValueError("event park fit requires multiple validation dates")
    cutoff = dates[split_index]
    training = working.filter(pl.col("game_date") < cutoff)
    validation = working.filter(pl.col("game_date") >= cutoff)

    encoder = LabelEncoder().fit(working[outcome_column].to_list())
    classes = [str(value) for value in encoder.classes_]
    validation_y = encoder.transform(validation[outcome_column].to_list())
    base_columns = ["batter_id", "pitcher_id", "batter_side", "pitcher_hand"]

    def fit(frame: pl.DataFrame, columns: list[str]):
        one_hot = OneHotEncoder(handle_unknown="ignore")
        design = one_hot.fit_transform(_matrix(frame, columns))
        model = LogisticRegression(
            C=regularization_c,
            max_iter=250,
            solver="lbfgs",
        ).fit(design, encoder.transform(frame[outcome_column].to_list()))
        return one_hot, model

    base_encoder, base_model = fit(training, base_columns)
    context_columns = [*base_columns, "venue_id"]
    park_encoder, park_model = fit(training, context_columns)
    base_probability = base_model.predict_proba(
        base_encoder.transform(_matrix(validation, base_columns))
    )
    park_probability = park_model.predict_proba(
        park_encoder.transform(_matrix(validation, context_columns))
    )
    base_log_loss, base_brier = _scores(validation_y, base_probability)
    park_log_loss, park_brier = _scores(validation_y, park_probability)

    full_encoder, full_model = fit(working, context_columns)
    venue_categories = [str(value) for value in full_encoder.categories_[-1]]
    venue_offset = sum(len(values) for values in full_encoder.categories_[:-1])
    venue_coefficients = full_model.coef_[
        :, venue_offset : venue_offset + len(venue_categories)
    ]
    if len(classes) == 2 and venue_coefficients.shape[0] == 1:
        venue_coefficients = np.vstack(
            [-0.5 * venue_coefficients[0], 0.5 * venue_coefficients[0]]
        )
    venue_coefficients = venue_coefficients - venue_coefficients.mean(axis=1)[:, None]
    venue_coefficients = venue_coefficients - venue_coefficients.mean(axis=0)[None, :]
    rows = []
    for venue_index, venue_id in enumerate(venue_categories):
        for class_index, outcome in enumerate(classes):
            rows.append(
                {
                    "venue_id": int(float(venue_id)),
                    "component": outcome,
                    "park_clr_effect": float(
                        venue_coefficients[class_index, venue_index]
                    ),
                }
            )
    return EventParkFit(
        factors=pl.DataFrame(rows).sort("venue_id", "component"),
        validation={
            "training_events": training.height,
            "validation_events": validation.height,
            "validation_start": str(cutoff),
            "baseline_log_loss": base_log_loss,
            "park_log_loss": park_log_loss,
            "park_minus_baseline_log_loss": park_log_loss - base_log_loss,
            "baseline_brier": base_brier,
            "park_brier": park_brier,
            "park_minus_baseline_brier": park_brier - base_brier,
        },
    )
