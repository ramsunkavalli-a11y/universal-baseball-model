"""Fixed protected-outcome confirmation metrics for opportunity v2."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log

import polars as pl

from universal_baseball.player_value_uncertainty import recover_untruncated_nb2_mean
from universal_baseball.playing_time_model import _truncated_nb2_logpmf


@dataclass(frozen=True, slots=True)
class OpportunityConfirmationResult:
    component: str
    confirmed: bool
    metrics: pl.DataFrame
    gates: dict[str, bool]


def _prediction_columns(unit: str) -> tuple[str, str, str]:
    if unit not in {"pa", "bf"}:
        raise ValueError("opportunity confirmation unit must be pa or bf")
    return (
        f"predicted_any_mlb_{unit}_probability",
        f"predicted_positive_mlb_{unit}_mean",
        f"predicted_expected_mlb_{unit}",
    )


def _align(
    predictions: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    unit: str,
    requires_distribution: bool,
) -> pl.DataFrame:
    probability, positive_mean, expected = _prediction_columns(unit)
    required = {"player_id", probability, positive_mean, expected}
    if requires_distribution:
        required.add("model_nb_alpha")
    missing = sorted(required - set(predictions.columns))
    if missing:
        raise ValueError(f"confirmation prediction missing fields: {missing}")
    target_column = f"observed_mlb_{unit}"
    if {"player_id", target_column} - set(targets.columns):
        raise ValueError("confirmation target has an unexpected schema")
    if predictions.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("confirmation predictions duplicate player IDs")
    if targets.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("confirmation targets duplicate player IDs")
    prediction_ids = set(predictions.get_column("player_id").to_list())
    target_ids = set(targets.get_column("player_id").to_list())
    if prediction_ids != target_ids:
        raise ValueError("confirmation prediction and target coverage differs")
    selected = predictions.select(sorted(required)).join(
        targets.select("player_id", target_column), on="player_id", validate="1:1"
    )
    if selected.filter(
        (pl.col(target_column) < 0)
        | (pl.col(target_column) != pl.col(target_column).floor())
    ).height:
        raise ValueError("confirmation outcomes must be nonnegative integer counts")
    return selected.sort("player_id")


def _metrics(
    predictions: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    unit: str,
    model: str,
    requires_distribution: bool,
) -> dict[str, object]:
    probability_column, positive_mean_column, expected_column = _prediction_columns(unit)
    target_column = f"observed_mlb_{unit}"
    data = _align(
        predictions, targets, unit=unit, requires_distribution=requires_distribution
    )
    observed = [int(value) for value in data.get_column(target_column).to_list()]
    probabilities = [float(value) for value in data.get_column(probability_column)]
    positive_means = [float(value) for value in data.get_column(positive_mean_column)]
    expected = [float(value) for value in data.get_column(expected_column)]
    alphas = (
        [float(value) for value in data.get_column("model_nb_alpha")]
        if requires_distribution
        else []
    )
    participation_nll = []
    full_nll = []
    for index, outcome in enumerate(observed):
        probability = probabilities[index]
        positive_mean = positive_means[index]
        if (
            not isfinite(probability)
            or not 0.0 < probability < 1.0
            or not isfinite(positive_mean)
            or positive_mean <= 0.0
            or not isfinite(expected[index])
            or expected[index] <= 0.0
            or abs(expected[index] - probability * positive_mean) > 1e-8 * max(
                1.0, expected[index]
            )
        ):
            raise ValueError("confirmation predictions contain invalid values")
        part_loss = -log(probability if outcome > 0 else 1.0 - probability)
        participation_nll.append(part_loss)
        if requires_distribution:
            alpha = alphas[index]
            if not isfinite(alpha) or alpha <= 0.0:
                raise ValueError("confirmation prediction dispersion is invalid")
            if outcome > 0:
                mu = recover_untruncated_nb2_mean(positive_mean, alpha=alpha)
                full_nll.append(
                    -log(probability) - _truncated_nb2_logpmf(outcome, mu, alpha)
                )
            else:
                full_nll.append(-log(1.0 - probability))
    count = len(observed)
    observed_active = [1.0 if value > 0 else 0.0 for value in observed]
    mean_observed = sum(observed) / count
    mean_predicted = sum(expected) / count
    return {
        "model": model,
        "players": count,
        "positive_players": sum(value > 0 for value in observed),
        "full_negative_log_likelihood": (
            sum(full_nll) / count if requires_distribution else None
        ),
        "participation_log_loss": sum(participation_nll) / count,
        "participation_brier": sum(
            (probabilities[index] - observed_active[index]) ** 2
            for index in range(count)
        )
        / count,
        "opportunity_mae": sum(
            abs(expected[index] - observed[index]) for index in range(count)
        )
        / count,
        "observed_mean_opportunity": mean_observed,
        "predicted_mean_opportunity": mean_predicted,
        "absolute_mean_error": abs(mean_predicted - mean_observed),
    }


def evaluate_opportunity_confirmation(
    selected: pl.DataFrame,
    parametric_baseline: pl.DataFrame,
    incumbent: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    component: str,
    unit: str,
) -> OpportunityConfirmationResult:
    """Apply the frozen component confirmation rule on identical player rows."""

    selected_metrics = _metrics(
        selected,
        targets,
        unit=unit,
        model="selected_v2",
        requires_distribution=True,
    )
    baseline_metrics = _metrics(
        parametric_baseline,
        targets,
        unit=unit,
        model="parametric_baseline",
        requires_distribution=True,
    )
    incumbent_metrics = _metrics(
        incumbent,
        targets,
        unit=unit,
        model="historical_cohort_incumbent",
        requires_distribution=False,
    )
    gates = {
        "full_nll_lower_than_parametric_baseline": (
            float(selected_metrics["full_negative_log_likelihood"])
            < float(baseline_metrics["full_negative_log_likelihood"])
        ),
        "participation_log_loss_no_worse_than_parametric_baseline": (
            float(selected_metrics["participation_log_loss"])
            <= float(baseline_metrics["participation_log_loss"])
        ),
        "mae_within_two_percent_of_parametric_baseline": (
            float(selected_metrics["opportunity_mae"])
            <= float(baseline_metrics["opportunity_mae"]) * 1.02
        ),
        "brier_no_worse_than_incumbent": (
            float(selected_metrics["participation_brier"])
            <= float(incumbent_metrics["participation_brier"])
        ),
        "mae_no_worse_than_incumbent": (
            float(selected_metrics["opportunity_mae"])
            <= float(incumbent_metrics["opportunity_mae"])
        ),
        "absolute_mean_error_no_worse_than_incumbent": (
            float(selected_metrics["absolute_mean_error"])
            <= float(incumbent_metrics["absolute_mean_error"])
        ),
    }
    return OpportunityConfirmationResult(
        component=component,
        confirmed=all(gates.values()),
        metrics=pl.DataFrame(
            [selected_metrics, baseline_metrics, incumbent_metrics],
            infer_schema_length=None,
        ),
        gates=gates,
    )
