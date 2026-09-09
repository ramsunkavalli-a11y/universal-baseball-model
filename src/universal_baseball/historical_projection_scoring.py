"""Score frozen historical participation and workload projections."""

from __future__ import annotations

import math

import polars as pl


def score_historical_workload_projection(
    projections: pl.DataFrame,
    outcomes: pl.DataFrame,
    prior_workload: pl.DataFrame,
    *,
    predicted_workload_column: str,
    participation_probability_column: str,
    observed_workload_column: str,
) -> tuple[pl.DataFrame, dict[str, float | int]]:
    """Score one player-universe forecast while retaining observed zeroes."""

    projection_required = {
        "player_id",
        predicted_workload_column,
        participation_probability_column,
    }
    outcome_required = {"player_id", observed_workload_column}
    prior_required = {"player_id", "prior_mlb_workload"}
    if missing := sorted(projection_required - set(projections.columns)):
        raise ValueError(f"historical workload projections missing fields: {missing}")
    if missing := sorted(outcome_required - set(outcomes.columns)):
        raise ValueError(f"historical workload outcomes missing fields: {missing}")
    if missing := sorted(prior_required - set(prior_workload.columns)):
        raise ValueError(f"historical prior workload missing fields: {missing}")
    for label, frame in (
        ("projection", projections),
        ("outcome", outcomes),
        ("prior", prior_workload),
    ):
        if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
            raise ValueError(f"historical {label} workload violates player grain")

    scored = (
        projections.select(*sorted(projection_required))
        .join(
            outcomes.select(*sorted(outcome_required)),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .join(
            prior_workload.select(*sorted(prior_required)),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col(observed_workload_column).fill_null(0).cast(pl.Float64),
            pl.col("prior_mlb_workload").fill_null(0).cast(pl.Float64),
        )
        .with_columns(
            (pl.col(observed_workload_column) > 0)
            .cast(pl.Int64)
            .alias("observed_mlb_active"),
            (
                pl.col(predicted_workload_column)
                - pl.col(observed_workload_column)
            ).alias("workload_error"),
            (
                pl.col("prior_mlb_workload")
                - pl.col(observed_workload_column)
            ).alias("prior_workload_error"),
        )
        .sort("player_id")
    )
    if scored.filter(
        ~pl.col(predicted_workload_column).is_finite()
        | (pl.col(predicted_workload_column) < 0)
        | ~pl.col(participation_probability_column).is_finite()
        | ~pl.col(participation_probability_column).is_between(0.0, 1.0)
        | (pl.col(observed_workload_column) < 0)
    ).height:
        raise ValueError("historical workload score contains invalid values")

    probability = scored.get_column(participation_probability_column).to_list()
    observed_active = scored.get_column("observed_mlb_active").to_list()
    log_loss = -sum(
        int(observed) * math.log(min(max(float(predicted), 1e-12), 1.0 - 1e-12))
        + (1 - int(observed))
        * math.log(min(max(1.0 - float(predicted), 1e-12), 1.0 - 1e-12))
        for predicted, observed in zip(probability, observed_active, strict=True)
    ) / scored.height
    error = scored.get_column("workload_error")
    prior_error = scored.get_column("prior_workload_error")
    observed_total = float(scored.get_column(observed_workload_column).sum())
    predicted_total = float(scored.get_column(predicted_workload_column).sum())
    return scored, {
        "players": scored.height,
        "observed_active_players": int(sum(observed_active)),
        "predicted_active_players": float(sum(probability)),
        "participation_brier": float(
            sum(
                (float(predicted) - int(observed)) ** 2
                for predicted, observed in zip(
                    probability, observed_active, strict=True
                )
            )
            / scored.height
        ),
        "participation_log_loss": log_loss,
        "observed_total_workload": observed_total,
        "predicted_total_workload": predicted_total,
        "predicted_to_observed_total_ratio": (
            predicted_total / observed_total if observed_total else math.nan
        ),
        "workload_mae": float(error.abs().mean()),
        "workload_rmse": math.sqrt(float((error * error).mean())),
        "prior_carry_forward_mae": float(prior_error.abs().mean()),
        "prior_carry_forward_rmse": math.sqrt(float((prior_error * prior_error).mean())),
    }


def workload_comparator_metrics(
    scored: pl.DataFrame,
    *,
    observed_column: str,
    model_column: str,
    comparator_column: str,
) -> dict[str, float | int]:
    """Compare two workload forecasts on their exact shared player rows."""

    required = {observed_column, model_column, comparator_column}
    if missing := sorted(required - set(scored.columns)):
        raise ValueError(f"historical workload comparator missing fields: {missing}")
    common = scored.filter(pl.col(comparator_column).is_not_null())
    if common.is_empty():
        raise ValueError("historical workload comparator has no common rows")
    model_error = common.get_column(model_column) - common.get_column(observed_column)
    comparator_error = (
        common.get_column(comparator_column) - common.get_column(observed_column)
    )
    return {
        "players": common.height,
        "observed_mean": float(common.get_column(observed_column).mean()),
        "model_mean": float(common.get_column(model_column).mean()),
        "comparator_mean": float(common.get_column(comparator_column).mean()),
        "model_mae": float(model_error.abs().mean()),
        "comparator_mae": float(comparator_error.abs().mean()),
        "model_rmse": math.sqrt(float((model_error * model_error).mean())),
        "comparator_rmse": math.sqrt(
            float((comparator_error * comparator_error).mean())
        ),
    }
