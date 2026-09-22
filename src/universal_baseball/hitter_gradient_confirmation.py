"""Locked scoring primitives for the protected hitter-gradient confirmation."""

from __future__ import annotations

import numpy as np
import polars as pl

from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES


def probability_metrics(
    actual: np.ndarray, prediction: np.ndarray, weights: np.ndarray
) -> dict[str, float]:
    """Score player-rate RMSE plus contact-weighted distribution losses."""

    if actual.shape != prediction.shape or actual.ndim != 2:
        raise ValueError("actual and prediction matrices must have matching shape")
    if len(weights) != actual.shape[0] or np.any(weights <= 0):
        raise ValueError("positive weights must align with probability rows")
    prediction = np.clip(prediction, 1e-12, 1.0)
    prediction = prediction / prediction.sum(axis=1, keepdims=True)
    return {
        "rate_rmse": float(np.sqrt(np.mean((prediction - actual) ** 2))),
        "multinomial_log_loss": float(
            -np.sum(weights[:, None] * actual * np.log(prediction)) / weights.sum()
        ),
        "multinomial_brier": float(
            np.sum(weights * np.sum((prediction - actual) ** 2, axis=1))
            / weights.sum()
        ),
    }


def score_confirmation_rows(frame: pl.DataFrame) -> dict[str, object]:
    """Score frozen baseline and gradient columns against completed targets."""

    required = {
        "player_id",
        "source_level",
        "target_source_level",
        "contacts",
        "target_contacts",
        *(f"actual__{value}" for value in CONTACT_OUTCOMES),
        *(f"contact_only__{value}" for value in CONTACT_OUTCOMES),
        *(f"gradient__{value}" for value in CONTACT_OUTCOMES),
    }
    if missing := sorted(required - set(frame.columns)):
        raise ValueError(f"confirmation rows missing fields: {missing}")
    actual = frame.select(
        *(f"actual__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    base = frame.select(
        *(f"contact_only__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    gradient = frame.select(
        *(f"gradient__{value}" for value in CONTACT_OUTCOMES)
    ).to_numpy()
    weights = frame["target_contacts"].to_numpy().astype(float)
    baseline = probability_metrics(actual, base, weights)
    candidate = probability_metrics(actual, gradient, weights)
    return {
        "players": frame.height,
        "target_contacts": int(weights.sum()),
        "contact_only": baseline,
        "gradient": candidate,
        "gradient_vs_contact_only": {
            name: candidate[name] - baseline[name] for name in baseline
        },
    }


def add_confirmation_strata(frame: pl.DataFrame) -> pl.DataFrame:
    """Attach the locked workload and level-transition groups."""

    rank = {"rk": 0, "a-": 1, "a": 2, "a+": 3, "aa": 4, "aaa": 5, "MLB": 6}
    source_rank = [rank.get(str(value), -1) for value in frame["source_level"]]
    target_rank = [rank.get(str(value), -1) for value in frame["target_source_level"]]
    transition = [
        "advanced" if target > source else "demoted" if target < source else "same_level"
        for source, target in zip(source_rank, target_rank, strict=True)
    ]
    return frame.with_columns(
        pl.when(pl.col("contacts") < 75)
        .then(pl.lit("30_to_74"))
        .when(pl.col("contacts") < 150)
        .then(pl.lit("75_to_149"))
        .otherwise(pl.lit("150_plus"))
        .alias("source_workload_group"),
        pl.Series("level_transition", transition),
    )


def outcome_metrics(frame: pl.DataFrame) -> list[dict[str, float | str]]:
    """Return locked binary rate and log-loss diagnostics for every outcome."""

    weights = frame["target_contacts"].to_numpy().astype(float)
    rows = []
    for outcome in CONTACT_OUTCOMES:
        actual = frame[f"actual__{outcome}"].to_numpy().astype(float)
        base = np.clip(
            frame[f"contact_only__{outcome}"].to_numpy().astype(float), 1e-12, 1 - 1e-12
        )
        candidate = np.clip(
            frame[f"gradient__{outcome}"].to_numpy().astype(float), 1e-12, 1 - 1e-12
        )

        def metric(prediction: np.ndarray) -> tuple[float, float]:
            rmse = float(np.sqrt(np.mean((prediction - actual) ** 2)))
            log_loss = float(
                -np.sum(
                    weights
                    * (
                        actual * np.log(prediction)
                        + (1 - actual) * np.log(1 - prediction)
                    )
                )
                / weights.sum()
            )
            return rmse, log_loss

        base_rmse, base_log = metric(base)
        candidate_rmse, candidate_log = metric(candidate)
        rows.append(
            {
                "outcome": outcome,
                "contact_only_rate_rmse": base_rmse,
                "gradient_rate_rmse": candidate_rmse,
                "rate_rmse_delta": candidate_rmse - base_rmse,
                "contact_only_binary_log_loss": base_log,
                "gradient_binary_log_loss": candidate_log,
                "binary_log_loss_delta": candidate_log - base_log,
            }
        )
    return rows
