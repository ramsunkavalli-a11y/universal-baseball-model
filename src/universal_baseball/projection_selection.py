"""Frozen Projection-v1 candidate-selection rules.

Selection is intentionally separated from fitting/scoring so the pre-registered
2022-only tie-break and early-reject rules are deterministic and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from universal_baseball.projection_ridge import (
    PROJECTION_FORM_AGE,
    PROJECTION_FORMS,
    PROJECTION_RIDGE_LAMBDAS,
)


LOG_LOSS_TIE_TOLERANCE = 1e-5
BRIER_TIE_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class ProjectionCandidateSelection:
    selected_form: str
    selected_lambda: float
    candidate_log_loss: float
    candidate_brier: float
    baseline0_log_loss: float
    baseline0_brier: float
    early_reject: bool
    advances_to_out_of_time_validation: bool
    metrics: dict[str, Any]


def pooled_model_scores(environment_scores: pl.DataFrame) -> pl.DataFrame:
    required = {"model", "future_core_events", "log_loss", "multinomial_brier"}
    missing = sorted(required - set(environment_scores.columns))
    if missing:
        raise ValueError(f"Projection environment scores missing fields: {missing}")
    if environment_scores.is_empty():
        raise ValueError("Projection environment scores must not be empty")
    if environment_scores.filter(pl.col("future_core_events") <= 0).height:
        raise ValueError("Projection environment scores require positive future core-event weights")

    weight = pl.col("future_core_events").cast(pl.Float64)
    return (
        environment_scores.group_by("model")
        .agg(
            pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("scored_players")
            if "player_id" in environment_scores.columns
            else pl.len().cast(pl.Int64).alias("scored_players"),
            ((pl.col("log_loss") * weight).sum() / weight.sum()).alias("event_weighted_log_loss"),
            ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias(
                "event_weighted_multinomial_brier"
            ),
        )
        .sort("model")
    )


def select_projection_configuration(config_results: pl.DataFrame) -> ProjectionCandidateSelection:
    required = {
        "form",
        "ridge_lambda",
        "candidate_log_loss",
        "candidate_brier",
        "baseline0_log_loss",
        "baseline0_brier",
    }
    missing = sorted(required - set(config_results.columns))
    if missing:
        raise ValueError(f"Projection selection results missing fields: {missing}")
    if config_results.is_empty():
        raise ValueError("Projection selection requires candidate results")
    if config_results.group_by(["form", "ridge_lambda"]).len().filter(pl.col("len") != 1).height:
        raise ValueError("Projection selection results violate form + lambda grain")

    observed_forms = set(str(value) for value in config_results.get_column("form").unique().to_list())
    if not observed_forms <= set(PROJECTION_FORMS):
        raise ValueError(f"Projection selection contains unsupported forms: {sorted(observed_forms)}")
    observed_lambdas = set(float(value) for value in config_results.get_column("ridge_lambda").unique().to_list())
    if not observed_lambdas <= set(PROJECTION_RIDGE_LAMBDAS):
        raise ValueError(f"Projection selection contains unsupported lambdas: {sorted(observed_lambdas)}")

    baseline_log_losses = [float(value) for value in config_results.get_column("baseline0_log_loss").to_list()]
    baseline_briers = [float(value) for value in config_results.get_column("baseline0_brier").to_list()]
    if max(baseline_log_losses) - min(baseline_log_losses) > 1e-12:
        raise ValueError("Projection Baseline 0 log loss differs across candidate configurations")
    if max(baseline_briers) - min(baseline_briers) > 1e-12:
        raise ValueError("Projection Baseline 0 Brier differs across candidate configurations")

    min_log_loss = float(config_results.get_column("candidate_log_loss").min())
    log_loss_eligible = config_results.filter(
        pl.col("candidate_log_loss") <= min_log_loss + LOG_LOSS_TIE_TOLERANCE
    )
    min_brier = float(log_loss_eligible.get_column("candidate_brier").min())
    brier_eligible = log_loss_eligible.filter(
        pl.col("candidate_brier") <= min_brier + BRIER_TIE_TOLERANCE
    )
    ranked = brier_eligible.with_columns(
        (pl.col("form") != PROJECTION_FORM_AGE).cast(pl.Int64).alias("_form_rank")
    ).sort(["_form_rank", "ridge_lambda"], descending=[False, True])
    selected = ranked.row(0, named=True)

    candidate_log_loss = float(selected["candidate_log_loss"])
    candidate_brier = float(selected["candidate_brier"])
    baseline0_log_loss = float(selected["baseline0_log_loss"])
    baseline0_brier = float(selected["baseline0_brier"])
    early_reject = not (candidate_log_loss < baseline0_log_loss)
    metrics: dict[str, Any] = {
        "selection_target": "projection_2021_to_2022_only",
        "log_loss_tie_tolerance": LOG_LOSS_TIE_TOLERANCE,
        "brier_tie_tolerance": BRIER_TIE_TOLERANCE,
        "form_tie_preference": PROJECTION_FORM_AGE,
        "lambda_tie_preference": "larger",
        "candidate_configuration_count": int(config_results.height),
        "log_loss_tie_eligible_count": int(log_loss_eligible.height),
        "brier_tie_eligible_count": int(brier_eligible.height),
        "early_reject_rule": "candidate_log_loss_must_be_strictly_below_baseline0",
    }
    return ProjectionCandidateSelection(
        selected_form=str(selected["form"]),
        selected_lambda=float(selected["ridge_lambda"]),
        candidate_log_loss=candidate_log_loss,
        candidate_brier=candidate_brier,
        baseline0_log_loss=baseline0_log_loss,
        baseline0_brier=baseline0_brier,
        early_reject=early_reject,
        advances_to_out_of_time_validation=not early_reject,
        metrics=metrics,
    )
