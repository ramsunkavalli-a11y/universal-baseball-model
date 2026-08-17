"""Proper scoring for Current Talent latent profiles in realized future environments.

The Current Talent baselines report latent core-profile probabilities on an MLB
reporting scale. Validation, however, must score future outcomes in the
competitive environment where those outcomes actually occur. This module applies
the training-only level observation effect forward to each realized target level
and computes proper scores from aggregated future core-event counts.

No playing-time, projection, WAR, or ranking inference is performed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, log
from typing import Any

import polars as pl

from universal_baseball.current_talent_validation_dataset import TARGET_ENVIRONMENT_KEY
from universal_baseball.performance_season import ALL_CORE_BINS


MODEL_LATENT_COLUMNS = {
    "baseline0": "baseline0_latent_probability",
    "baseline1": "baseline1_latent_probability",
}
MODEL_TARGET_COLUMNS = {
    "baseline0": "baseline0_target_probability",
    "baseline1": "baseline1_target_probability",
}
DEFAULT_CALIBRATION_BIN_COUNT = 10


@dataclass(frozen=True, slots=True)
class CurrentTalentScoreReport:
    """Deterministic proper-score outputs for one historical cutoff."""

    projected_profile: pl.DataFrame
    environment_scores: pl.DataFrame
    component_calibration: pl.DataFrame
    aggregate_metrics: pl.DataFrame
    stratified_metrics: pl.DataFrame
    metrics: dict[str, Any]


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"{label} missing fields: {missing}")


def _clr(probabilities: list[float]) -> list[float]:
    if any(value <= 0 for value in probabilities):
        raise ValueError("latent profile probabilities must be strictly positive")
    logs = [log(value) for value in probabilities]
    mean_log = sum(logs) / len(logs)
    return [value - mean_log for value in logs]


def _softmax(values: list[float]) -> list[float]:
    maximum = max(values)
    numerators = [exp(value - maximum) for value in values]
    denominator = sum(numerators)
    if denominator <= 0:
        raise ValueError("softmax denominator must be positive")
    return [value / denominator for value in numerators]


def _translation_lookup(offsets: pl.DataFrame) -> dict[str, dict[str, float]]:
    required = {"level_group", "core_bin", "clr_environment_effect"}
    _require_columns(offsets, required, "translation offsets")
    duplicate = offsets.group_by(["level_group", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("translation offsets violate level_group + core_bin grain")

    lookup: dict[str, dict[str, float]] = {}
    for row in offsets.select(*required).iter_rows(named=True):
        level = str(row["level_group"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported translation core bin: {core_bin}")
        lookup.setdefault(level, {})[core_bin] = float(row["clr_environment_effect"])
    for level, values in lookup.items():
        if set(values) != set(ALL_CORE_BINS):
            raise ValueError(f"translation level {level} does not contain all core bins")
        if abs(sum(values.values())) > 1e-7:
            raise ValueError(f"translation CLR effects do not sum to zero for level {level}")
    if "MLB" not in lookup:
        raise ValueError("translation offsets must contain MLB anchor")
    return lookup


def _latent_profiles(profile: pl.DataFrame) -> dict[int, dict[str, dict[str, float]]]:
    required = {"player_id", "core_bin", *MODEL_LATENT_COLUMNS.values()}
    _require_columns(profile, required, "baseline profile")
    duplicate = profile.group_by(["player_id", "core_bin"]).len().filter(pl.col("len") != 1)
    if not duplicate.is_empty():
        raise ValueError("baseline profile violates player_id + core_bin grain")

    output: dict[int, dict[str, dict[str, float]]] = {}
    for row in profile.iter_rows(named=True):
        player_id = int(row["player_id"])
        core_bin = str(row["core_bin"])
        if core_bin not in ALL_CORE_BINS:
            raise ValueError(f"unsupported baseline core bin: {core_bin}")
        by_model = output.setdefault(player_id, {model: {} for model in MODEL_LATENT_COLUMNS})
        for model, column in MODEL_LATENT_COLUMNS.items():
            by_model[model][core_bin] = float(row[column])

    for player_id, by_model in output.items():
        for model, probabilities in by_model.items():
            if set(probabilities) != set(ALL_CORE_BINS):
                raise ValueError(f"{model} profile incomplete for player {player_id}")
            total = sum(probabilities.values())
            if abs(total - 1.0) > 1e-7:
                raise ValueError(f"{model} latent profile does not sum to one for player {player_id}")
            if any(value <= 0 or value >= 1 for value in probabilities.values()):
                raise ValueError(f"{model} latent probabilities must lie strictly between zero and one")
    return output


def project_latent_profiles_to_target_environment(
    baseline_profile: pl.DataFrame,
    target_summary: pl.DataFrame,
    offsets: pl.DataFrame,
) -> pl.DataFrame:
    """Map MLB-scale latent profiles into each realized target level.

    The fitted translation contract is

    ``CLR(observed at level L) = CLR(latent MLB-scale profile) + beta[L]``.

    Therefore validation adds the target-level effect and maps the result back
    through softmax. Only target rows with positive future core evidence and an
    available baseline profile are projected; target-only players are coverage,
    not talent failures.
    """

    _require_columns(
        target_summary,
        {*TARGET_ENVIRONMENT_KEY, "future_core_events"},
        "future target summary",
    )
    duplicate_target = target_summary.group_by(list(TARGET_ENVIRONMENT_KEY)).len().filter(
        pl.col("len") != 1
    )
    if not duplicate_target.is_empty():
        raise ValueError("future target summary violates target-environment grain")

    latent = _latent_profiles(baseline_profile)
    translation = _translation_lookup(offsets)
    rows: list[dict[str, object]] = []
    target_rows = target_summary.filter(pl.col("future_core_events") > 0)
    for target in target_rows.iter_rows(named=True):
        player_id = int(target["player_id"])
        if player_id not in latent:
            continue
        level = str(target["target_level_group"])
        if level not in translation:
            raise ValueError(f"no fitted translation offsets for target level {level}")

        projected_by_model: dict[str, dict[str, float]] = {}
        for model in MODEL_LATENT_COLUMNS:
            probabilities = [latent[player_id][model][core_bin] for core_bin in ALL_CORE_BINS]
            latent_clr = _clr(probabilities)
            observed_clr = [
                latent_clr[index] + translation[level][core_bin]
                for index, core_bin in enumerate(ALL_CORE_BINS)
            ]
            target_probabilities = _softmax(observed_clr)
            projected_by_model[model] = dict(zip(ALL_CORE_BINS, target_probabilities, strict=True))

        for core_bin in ALL_CORE_BINS:
            row: dict[str, object] = {
                key: target[key] for key in TARGET_ENVIRONMENT_KEY
            }
            row.update(
                {
                    "future_core_events": int(target["future_core_events"]),
                    "core_bin": core_bin,
                    "baseline0_target_probability": projected_by_model["baseline0"][core_bin],
                    "baseline1_target_probability": projected_by_model["baseline1"][core_bin],
                }
            )
            rows.append(row)

    schema = {
        "player_id": pl.Int64,
        "target_season": pl.Int64,
        "target_league_id": pl.Int64,
        "target_level_group": pl.String,
        "future_core_events": pl.Int64,
        "core_bin": pl.String,
        "baseline0_target_probability": pl.Float64,
        "baseline1_target_probability": pl.Float64,
    }
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(rows, schema=schema).sort([*TARGET_ENVIRONMENT_KEY, "core_bin"])


def _attach_target_counts(
    projected: pl.DataFrame,
    target_profile: pl.DataFrame,
) -> pl.DataFrame:
    required = {*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count"}
    _require_columns(target_profile, required, "future target profile")
    duplicate = target_profile.group_by([*TARGET_ENVIRONMENT_KEY, "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("future target profile violates target-environment + core-bin grain")

    counts = target_profile.select(*TARGET_ENVIRONMENT_KEY, "core_bin", "future_occurrence_count")
    attached = projected.join(
        counts,
        on=[*TARGET_ENVIRONMENT_KEY, "core_bin"],
        how="left",
    ).with_columns(pl.col("future_occurrence_count").fill_null(0).cast(pl.Int64))

    reconciled = attached.group_by(list(TARGET_ENVIRONMENT_KEY)).agg(
        pl.col("future_occurrence_count").sum().alias("_future_count"),
        pl.col("future_core_events").first().alias("_future_core_events"),
    )
    if reconciled.filter(pl.col("_future_count") != pl.col("_future_core_events")).height:
        raise ValueError("future profile counts do not reconcile to future_core_events")
    return attached


def _environment_scores(attached: pl.DataFrame) -> pl.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in attached.group_by(list(TARGET_ENVIRONMENT_KEY), maintain_order=True):
        target_key = dict(zip(TARGET_ENVIRONMENT_KEY, key, strict=True))
        future_core_events = int(group.get_column("future_core_events").item(0))
        if future_core_events <= 0:
            continue
        counts = {
            str(row["core_bin"]): int(row["future_occurrence_count"])
            for row in group.iter_rows(named=True)
        }
        if set(counts) != set(ALL_CORE_BINS):
            raise ValueError("projected target environment does not contain all core bins")

        for model, probability_column in MODEL_TARGET_COLUMNS.items():
            probabilities = {
                str(row["core_bin"]): float(row[probability_column])
                for row in group.iter_rows(named=True)
            }
            probability_sum = sum(probabilities.values())
            if abs(probability_sum - 1.0) > 1e-7:
                raise ValueError(f"{model} target probabilities do not sum to one")
            log_loss = -sum(
                counts[core_bin] * log(probabilities[core_bin])
                for core_bin in ALL_CORE_BINS
            ) / future_core_events
            empirical = {
                core_bin: counts[core_bin] / future_core_events
                for core_bin in ALL_CORE_BINS
            }
            multinomial_brier = (
                1.0
                - 2.0 * sum(empirical[core_bin] * probabilities[core_bin] for core_bin in ALL_CORE_BINS)
                + sum(probabilities[core_bin] ** 2 for core_bin in ALL_CORE_BINS)
            )
            rows.append(
                {
                    **target_key,
                    "model": model,
                    "future_core_events": future_core_events,
                    "log_loss": float(log_loss),
                    "multinomial_brier": float(multinomial_brier),
                }
            )
    return pl.DataFrame(rows).sort(["model", *TARGET_ENVIRONMENT_KEY])


def _weighted_metrics(frame: pl.DataFrame, group_columns: list[str]) -> pl.DataFrame:
    if frame.is_empty():
        return pl.DataFrame()
    weight = pl.col("future_core_events").cast(pl.Float64)
    aggregations = [
        pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
        pl.len().cast(pl.Int64).alias("target_environment_rows"),
        ((pl.col("log_loss") * weight).sum() / weight.sum()).alias("event_weighted_log_loss"),
        ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias(
            "event_weighted_multinomial_brier"
        ),
        pl.col("log_loss").mean().alias("target_environment_mean_log_loss"),
        pl.col("multinomial_brier").mean().alias("target_environment_mean_multinomial_brier"),
    ]
    if group_columns:
        return frame.group_by(group_columns).agg(*aggregations).sort(group_columns)
    return frame.select(*aggregations)


def _component_calibration(
    attached: pl.DataFrame,
    *,
    calibration_bin_count: int,
) -> pl.DataFrame:
    if calibration_bin_count < 2:
        raise ValueError("calibration_bin_count must be at least two")
    rows: list[dict[str, object]] = []
    for model, probability_column in MODEL_TARGET_COLUMNS.items():
        for row in attached.iter_rows(named=True):
            n = int(row["future_core_events"])
            if n <= 0:
                continue
            probability = float(row[probability_column])
            observed_count = int(row["future_occurrence_count"])
            bin_index = min(int(probability * calibration_bin_count), calibration_bin_count - 1)
            rows.append(
                {
                    "model": model,
                    "core_bin": str(row["core_bin"]),
                    "calibration_bin": bin_index,
                    "future_core_events": n,
                    "observed_count": observed_count,
                    "predicted_event_mass": probability * n,
                }
            )
    if not rows:
        return pl.DataFrame()
    frame = pl.DataFrame(rows)
    result = (
        frame.group_by(["model", "core_bin", "calibration_bin"])
        .agg(
            pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
            pl.col("observed_count").sum().cast(pl.Int64).alias("observed_count"),
            pl.col("predicted_event_mass").sum().alias("predicted_event_mass"),
        )
        .with_columns(
            (pl.col("predicted_event_mass") / pl.col("future_core_events")).alias(
                "mean_predicted_probability"
            ),
            (pl.col("observed_count") / pl.col("future_core_events")).alias(
                "observed_event_rate"
            ),
        )
        .with_columns(
            (pl.col("observed_event_rate") - pl.col("mean_predicted_probability"))
            .abs()
            .alias("absolute_calibration_error")
        )
        .sort(["model", "core_bin", "calibration_bin"])
    )
    return result


def score_current_talent_profiles(
    projected_profile: pl.DataFrame,
    target_profile: pl.DataFrame,
    *,
    scoring_context: pl.DataFrame | None = None,
    calibration_bin_count: int = DEFAULT_CALIBRATION_BIN_COUNT,
) -> CurrentTalentScoreReport:
    """Compute exact event-weighted proper scores from future aggregate counts."""

    required = {
        *TARGET_ENVIRONMENT_KEY,
        "future_core_events",
        "core_bin",
        *MODEL_TARGET_COLUMNS.values(),
    }
    _require_columns(projected_profile, required, "projected Current Talent profile")
    attached = _attach_target_counts(projected_profile, target_profile)
    environment_scores = _environment_scores(attached)

    context_columns: list[str] = []
    if scoring_context is not None and not environment_scores.is_empty():
        _require_columns(scoring_context, set(TARGET_ENVIRONMENT_KEY), "scoring context")
        duplicate = scoring_context.group_by(list(TARGET_ENVIRONMENT_KEY)).len().filter(
            pl.col("len") != 1
        )
        if not duplicate.is_empty():
            raise ValueError("scoring context violates target-environment grain")
        candidate_context = [
            column
            for column in (
                "target_transition",
                "as_of_level_group",
                "as_of_environment_ambiguous",
                "prior_mlb_evidence",
            )
            if column in scoring_context.columns
        ]
        if candidate_context:
            environment_scores = environment_scores.join(
                scoring_context.select(*TARGET_ENVIRONMENT_KEY, *candidate_context),
                on=list(TARGET_ENVIRONMENT_KEY),
                how="left",
            )
            context_columns = candidate_context

    aggregate_metrics = _weighted_metrics(environment_scores, ["model"])
    strata = ["model", "target_level_group"]
    if "target_transition" in context_columns:
        strata.append("target_transition")
    stratified_metrics = _weighted_metrics(environment_scores, strata)
    calibration = _component_calibration(
        attached,
        calibration_bin_count=calibration_bin_count,
    )

    scored_players = (
        int(environment_scores.get_column("player_id").n_unique())
        if not environment_scores.is_empty()
        else 0
    )
    scored_target_rows = (
        int(environment_scores.select(list(TARGET_ENVIRONMENT_KEY)).unique().height)
        if not environment_scores.is_empty()
        else 0
    )
    metrics = {
        "scored_player_count": scored_players,
        "scored_target_environment_count": scored_target_rows,
        "projected_profile_row_count": int(projected_profile.height),
        "calibration_bin_count": int(calibration_bin_count),
        "proper_score_basis": "all_realized_future_core_events_in_calendar_horizon",
        "aggregate_pa_cap_applied": False,
        "target_environment_mapping": "latent_clr_plus_fitted_target_level_effect_then_softmax",
    }
    return CurrentTalentScoreReport(
        projected_profile=projected_profile,
        environment_scores=environment_scores,
        component_calibration=calibration,
        aggregate_metrics=aggregate_metrics,
        stratified_metrics=stratified_metrics,
        metrics=metrics,
    )
