"""Target-free mechanics for the preregistered S0 stability blend."""

from __future__ import annotations

import math

import polars as pl

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


SELECTION_TOLERANCE = 1e-8


def blend_outcome_predictions(
    c0: pl.DataFrame,
    marcel: pl.DataFrame,
    *,
    c0_weight: float,
    model_id: str = "S0_C0_MARCEL_STABILITY_BLEND",
) -> pl.DataFrame:
    """Return one row-wise convex probability blend on an identical cohort."""

    weight = float(c0_weight)
    if not math.isfinite(weight) or not 0.0 <= weight <= 1.0:
        raise ValueError("C0 blend weight must be finite and within [0, 1]")
    probability_columns = [f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES]
    required = {"player_id", *probability_columns}
    for name, frame in (("C0", c0), ("Marcel", marcel)):
        if missing := sorted(required - set(frame.columns)):
            raise ValueError(f"{name} predictions are missing columns: {missing}")
        if frame["player_id"].n_unique() != frame.height:
            raise ValueError(f"{name} predictions contain duplicate players")
    if set(c0["player_id"].to_list()) != set(marcel["player_id"].to_list()):
        raise ValueError("S0 requires identical C0 and Marcel player cohorts")
    left = c0.select("player_id", *probability_columns).rename(
        {column: f"{column}_c0" for column in probability_columns}
    )
    right = marcel.select("player_id", *probability_columns).rename(
        {column: f"{column}_marcel" for column in probability_columns}
    )
    joined = left.join(right, on="player_id", how="inner", validate="1:1")
    blended = joined.select(
        "player_id",
        pl.lit(model_id).alias("model_id"),
        pl.lit(weight).alias("c0_weight"),
        pl.lit(1.0 - weight).alias("marcel_weight"),
        *[
            (
                pl.col(f"{column}_c0") * weight
                + pl.col(f"{column}_marcel") * (1.0 - weight)
            ).alias(column)
            for column in probability_columns
        ],
    ).sort("player_id")
    sums = blended.select(pl.sum_horizontal(*probability_columns).alias("sum"))["sum"]
    if blended.select(
        *[pl.col(column).is_finite().all() for column in probability_columns]
    ).row(0).count(False):
        raise ValueError("S0 produced non-finite probabilities")
    if blended.select(
        *[(pl.col(column) >= 0.0).all() for column in probability_columns]
    ).row(0).count(False):
        raise ValueError("S0 produced negative probabilities")
    if float((sums - 1.0).abs().max()) > 1e-12:
        raise ValueError("S0 probability simplex is not normalized")
    return blended


def select_c0_weight(scores: pl.DataFrame) -> dict[str, float]:
    """Apply the frozen loss minimum and C0-favoring tie rule."""

    required = {"c0_weight", "mean_player_pa_terminal_log_loss"}
    if missing := sorted(required - set(scores.columns)):
        raise ValueError(f"S0 selection scores are missing columns: {missing}")
    if scores.is_empty():
        raise ValueError("S0 selection score table is empty")
    minimum = float(scores["mean_player_pa_terminal_log_loss"].min())
    winner = (
        scores.filter(
            pl.col("mean_player_pa_terminal_log_loss") <= minimum + SELECTION_TOLERANCE
        )
        .sort("c0_weight", descending=True)
        .row(0, named=True)
    )
    return {
        "c0_weight": float(winner["c0_weight"]),
        "marcel_weight": 1.0 - float(winner["c0_weight"]),
        "mean_player_pa_terminal_log_loss": float(
            winner["mean_player_pa_terminal_log_loss"]
        ),
    }
