"""Frozen Playing Time / Role v1 candidate-selection rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from universal_baseball.playing_time_model import PT_FORM_B0, PT_FORMS, PT_FORM_COMPLEXITY


FULL_NLL_TIE_TOLERANCE = 0.001
PARTICIPATION_LOG_LOSS_TIE_TOLERANCE = 0.0005
MAE_TIE_TOLERANCE = 1e-6


@dataclass(frozen=True, slots=True)
class PlayingTimeSelection:
    selected_form: str
    selected_full_nll: float
    baseline0_full_nll: float
    selected_participation_log_loss: float
    selected_unconditional_pa_mae: float
    baseline0_selected: bool
    advances_to_out_of_time_validation: bool
    metrics: dict[str, Any]


def pooled_playing_time_metrics(scored: pl.DataFrame) -> dict[str, float | int]:
    required = {
        "observed_mlb_pa",
        "observed_any_mlb_pa",
        "predicted_any_mlb_pa_probability",
        "predicted_expected_mlb_pa",
        "full_negative_log_likelihood",
        "participation_negative_log_likelihood",
        "positive_count_negative_log_likelihood",
    }
    missing = sorted(required - set(scored.columns))
    if missing:
        raise ValueError(f"playing-time scored rows missing fields: {missing}")
    if scored.is_empty():
        raise ValueError("playing-time pooled scoring requires rows")

    observed = scored.get_column("observed_mlb_pa").cast(pl.Float64)
    predicted = scored.get_column("predicted_expected_mlb_pa").cast(pl.Float64)
    observed_participation = scored.get_column("observed_any_mlb_pa").cast(pl.Float64)
    predicted_participation = scored.get_column("predicted_any_mlb_pa_probability").cast(pl.Float64)
    positive = scored.filter(pl.col("observed_mlb_pa") > 0)
    return {
        "scored_players": int(scored.height),
        "positive_players": int(positive.height),
        "mean_full_negative_log_likelihood": float(
            scored.get_column("full_negative_log_likelihood").mean()
        ),
        "participation_log_loss": float(
            scored.get_column("participation_negative_log_likelihood").mean()
        ),
        "participation_brier": float(
            ((predicted_participation - observed_participation) ** 2).mean()
        ),
        "positive_count_negative_log_likelihood": float(
            positive.get_column("positive_count_negative_log_likelihood").mean()
        )
        if positive.height
        else float("nan"),
        "unconditional_mlb_pa_mae": float((predicted - observed).abs().mean()),
        "unconditional_mlb_pa_rmse": float((((predicted - observed) ** 2).mean()) ** 0.5),
        "observed_mean_mlb_pa": float(observed.mean()),
        "predicted_mean_mlb_pa": float(predicted.mean()),
    }


def select_playing_time_form(form_results: pl.DataFrame) -> PlayingTimeSelection:
    required = {
        "form",
        "mean_full_negative_log_likelihood",
        "participation_log_loss",
        "unconditional_mlb_pa_mae",
    }
    missing = sorted(required - set(form_results.columns))
    if missing:
        raise ValueError(f"playing-time selection results missing fields: {missing}")
    if form_results.is_empty():
        raise ValueError("playing-time selection requires candidate results")
    if form_results.group_by("form").len().filter(pl.col("len") != 1).height:
        raise ValueError("playing-time selection results violate form grain")
    observed_forms = set(str(value) for value in form_results.get_column("form").to_list())
    if observed_forms != set(PT_FORMS):
        raise ValueError(
            f"playing-time selection must evaluate exact frozen forms: observed={sorted(observed_forms)}"
        )

    min_full_nll = float(form_results.get_column("mean_full_negative_log_likelihood").min())
    full_nll_eligible = form_results.filter(
        pl.col("mean_full_negative_log_likelihood")
        <= min_full_nll + FULL_NLL_TIE_TOLERANCE
    )
    min_participation = float(full_nll_eligible.get_column("participation_log_loss").min())
    participation_eligible = full_nll_eligible.filter(
        pl.col("participation_log_loss")
        <= min_participation + PARTICIPATION_LOG_LOSS_TIE_TOLERANCE
    )
    min_mae = float(participation_eligible.get_column("unconditional_mlb_pa_mae").min())
    mae_eligible = participation_eligible.filter(
        pl.col("unconditional_mlb_pa_mae") <= min_mae + MAE_TIE_TOLERANCE
    )
    ranked = mae_eligible.with_columns(
        pl.col("form")
        .cast(pl.String)
        .replace_strict(PT_FORM_COMPLEXITY, return_dtype=pl.Int64)
        .alias("_complexity")
    ).sort("_complexity")
    selected = ranked.row(0, named=True)

    baseline = form_results.filter(pl.col("form") == PT_FORM_B0).row(0, named=True)
    selected_form = str(selected["form"])
    selected_full_nll = float(selected["mean_full_negative_log_likelihood"])
    baseline_full_nll = float(baseline["mean_full_negative_log_likelihood"])
    baseline_selected = selected_form == PT_FORM_B0
    advances = bool((not baseline_selected) and selected_full_nll < baseline_full_nll)
    metrics: dict[str, Any] = {
        "selection_target": "2021-10-15_to_2022_only",
        "full_nll_tie_tolerance": FULL_NLL_TIE_TOLERANCE,
        "participation_log_loss_tie_tolerance": PARTICIPATION_LOG_LOSS_TIE_TOLERANCE,
        "mae_tie_tolerance": MAE_TIE_TOLERANCE,
        "frozen_form_count": len(PT_FORMS),
        "full_nll_tie_eligible_count": int(full_nll_eligible.height),
        "participation_tie_eligible_count": int(participation_eligible.height),
        "mae_tie_eligible_count": int(mae_eligible.height),
        "simplicity_order": list(PT_FORMS),
    }
    return PlayingTimeSelection(
        selected_form=selected_form,
        selected_full_nll=selected_full_nll,
        baseline0_full_nll=baseline_full_nll,
        selected_participation_log_loss=float(selected["participation_log_loss"]),
        selected_unconditional_pa_mae=float(selected["unconditional_mlb_pa_mae"]),
        baseline0_selected=baseline_selected,
        advances_to_out_of_time_validation=advances,
        metrics=metrics,
    )
