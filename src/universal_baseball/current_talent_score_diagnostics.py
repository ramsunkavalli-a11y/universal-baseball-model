"""Reusable diagnostic summaries for chronological Current Talent proper scores.

These diagnostics do not select a model or tune hyperparameters. They make the
first baseline gate inspectable across fixed age/evidence bands, target levels,
transition classes, profile components, and reliability bins.
"""

from __future__ import annotations

import polars as pl

from universal_baseball.current_talent_scoring import MODEL_TARGET_COLUMNS
from universal_baseball.current_talent_validation_dataset import TARGET_ENVIRONMENT_KEY
from universal_baseball.performance_season import ALL_CORE_BINS


DEFAULT_STRATA = (
    "target_level_group",
    "target_transition",
    "age_band",
    "evidence_band",
)


def add_diagnostic_bands(scoring_context: pl.DataFrame) -> pl.DataFrame:
    """Add fixed, descriptive age/evidence bands; these are not model features."""

    required = {"age_years", "effective_core_events_translated"}
    missing = sorted(required - set(scoring_context.columns))
    if missing:
        raise ValueError(f"scoring context missing diagnostic fields: {missing}")
    return scoring_context.with_columns(
        pl.when(pl.col("age_years") < 20)
        .then(pl.lit("<20"))
        .when(pl.col("age_years") < 22)
        .then(pl.lit("20-21.9"))
        .when(pl.col("age_years") < 24)
        .then(pl.lit("22-23.9"))
        .when(pl.col("age_years") < 27)
        .then(pl.lit("24-26.9"))
        .otherwise(pl.lit("27+"))
        .alias("age_band"),
        pl.when(pl.col("effective_core_events_translated") < 25)
        .then(pl.lit("<25"))
        .when(pl.col("effective_core_events_translated") < 50)
        .then(pl.lit("25-49"))
        .when(pl.col("effective_core_events_translated") < 100)
        .then(pl.lit("50-99"))
        .when(pl.col("effective_core_events_translated") < 200)
        .then(pl.lit("100-199"))
        .otherwise(pl.lit("200+"))
        .alias("evidence_band"),
    )


def build_separate_stratified_metrics(
    environment_scores: pl.DataFrame,
    scoring_context: pl.DataFrame,
    *,
    strata: tuple[str, ...] = DEFAULT_STRATA,
) -> pl.DataFrame:
    """Summarize proper scores one diagnostic dimension at a time."""

    required_scores = {*TARGET_ENVIRONMENT_KEY, "model", "future_core_events", "log_loss", "multinomial_brier"}
    missing = sorted(required_scores - set(environment_scores.columns))
    if missing:
        raise ValueError(f"environment scores missing fields: {missing}")
    missing_keys = sorted(set(TARGET_ENVIRONMENT_KEY) - set(scoring_context.columns))
    if missing_keys:
        raise ValueError(f"scoring context missing target keys: {missing_keys}")
    duplicate = scoring_context.group_by(list(TARGET_ENVIRONMENT_KEY)).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("scoring context violates target-environment grain")

    context_columns = [
        column
        for column in strata
        if column not in environment_scores.columns and column in scoring_context.columns
    ]
    working = environment_scores
    if context_columns:
        working = working.join(
            scoring_context.select(*TARGET_ENVIRONMENT_KEY, *context_columns),
            on=list(TARGET_ENVIRONMENT_KEY),
            how="left",
        )

    outputs: list[pl.DataFrame] = []
    weight = pl.col("future_core_events").cast(pl.Float64)
    for stratum in strata:
        if stratum not in working.columns:
            continue
        grouped = (
            working.filter(pl.col(stratum).is_not_null())
            .group_by(["model", stratum])
            .agg(
                pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
                pl.len().cast(pl.Int64).alias("target_environment_rows"),
                ((pl.col("log_loss") * weight).sum() / weight.sum()).alias("event_weighted_log_loss"),
                ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias(
                    "event_weighted_multinomial_brier"
                ),
            )
            .with_columns(
                pl.lit(stratum).alias("stratum_type"),
                pl.col(stratum).cast(pl.String).alias("stratum_value"),
            )
            .select(
                "model",
                "stratum_type",
                "stratum_value",
                "future_core_events",
                "target_environment_rows",
                "event_weighted_log_loss",
                "event_weighted_multinomial_brier",
            )
        )
        outputs.append(grouped)
    if not outputs:
        return pl.DataFrame()
    return pl.concat(outputs, how="vertical_relaxed").sort(
        ["stratum_type", "stratum_value", "model"]
    )


def build_component_proper_score_contributions(
    projected_profile: pl.DataFrame,
    target_profile: pl.DataFrame,
) -> pl.DataFrame:
    """Decompose multinomial log loss/Brier into the 12 profile components."""

    projected_required = {
        *TARGET_ENVIRONMENT_KEY,
        "future_core_events",
        "core_bin",
        *MODEL_TARGET_COLUMNS.values(),
    }
    target_required = {*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count"}
    if missing := sorted(projected_required - set(projected_profile.columns)):
        raise ValueError(f"projected profile missing component-score fields: {missing}")
    if missing := sorted(target_required - set(target_profile.columns)):
        raise ValueError(f"target profile missing component-score fields: {missing}")

    counts = target_profile.select(*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count")
    attached = projected_profile.join(
        counts,
        on=[*TARGET_ENVIRONMENT_KEY, "core_bin"],
        how="left",
    ).with_columns(pl.col("future_occurrence_count").fill_null(0).cast(pl.Int64))
    total_future_events = (
        attached.select(*TARGET_ENVIRONMENT_KEY, "future_core_events")
        .unique()
        .get_column("future_core_events")
        .sum()
    )
    if not total_future_events or total_future_events <= 0:
        raise ValueError("component scoring requires positive future core events")

    rows: list[dict[str, object]] = []
    for model, probability_column in MODEL_TARGET_COLUMNS.items():
        for core_bin in ALL_CORE_BINS:
            group = attached.filter(pl.col("core_bin") == core_bin)
            probability = pl.col(probability_column)
            observed = pl.col("future_occurrence_count").cast(pl.Float64)
            opportunities = pl.col("future_core_events").cast(pl.Float64)
            summary = group.select(
                pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
                pl.col("future_occurrence_count").sum().cast(pl.Int64).alias("observed_count"),
                (probability * opportunities).sum().alias("predicted_event_mass"),
                (-(observed * probability.log()).sum() / float(total_future_events)).alias(
                    "multinomial_log_loss_contribution"
                ),
                (
                    (
                        observed * (1.0 - probability) ** 2
                        + (opportunities - observed) * probability**2
                    ).sum()
                    / float(total_future_events)
                ).alias("binary_brier_contribution"),
            ).to_dicts()[0]
            rows.append(
                {
                    "model": model,
                    "core_bin": core_bin,
                    **summary,
                    "observed_event_rate": summary["observed_count"] / summary["future_core_events"],
                    "mean_predicted_probability": summary["predicted_event_mass"] / summary["future_core_events"],
                }
            )
    return pl.DataFrame(rows).sort(["core_bin", "model"])


def build_calibration_summary(component_calibration: pl.DataFrame) -> pl.DataFrame:
    """Summarize reliability-bin calibration error by model/component."""

    required = {
        "model",
        "core_bin",
        "future_core_events",
        "absolute_calibration_error",
    }
    if missing := sorted(required - set(component_calibration.columns)):
        raise ValueError(f"component calibration missing fields: {missing}")
    weight = pl.col("future_core_events").cast(pl.Float64)
    return (
        component_calibration.group_by(["model", "core_bin"])
        .agg(
            pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
            ((pl.col("absolute_calibration_error") * weight).sum() / weight.sum()).alias(
                "event_weighted_expected_calibration_error"
            ),
            pl.col("absolute_calibration_error").max().alias("max_bin_absolute_calibration_error"),
            pl.len().cast(pl.Int64).alias("occupied_calibration_bins"),
        )
        .sort(["core_bin", "model"])
    )
