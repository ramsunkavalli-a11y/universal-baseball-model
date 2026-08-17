"""Controlled ablations for the simple Current Talent baseline pipeline.

The first ablation replaces fitted level CLR effects with zeros while leaving the
rest of the predictor/prior/shrinkage/scoring pipeline unchanged. Baseline 0 still
uses age + current level in its peer prior; this isolates the learned observation-
layer translation rather than removing all information about competitive level.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import polars as pl

from universal_baseball.current_talent_baselines import (
    BaselineProfiles,
    build_baseline_profiles,
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_score_diagnostics import (
    add_diagnostic_bands,
    build_calibration_summary,
    build_component_proper_score_contributions,
    build_separate_stratified_metrics,
)
from universal_baseball.current_talent_scoring import (
    CurrentTalentScoreReport,
    project_latent_profiles_to_target_environment,
    score_current_talent_profiles,
)
from universal_baseball.current_talent_validation_dataset import ValidationSnapshotDataset
from universal_baseball.performance_season import ALL_CORE_BINS


FITTED_TRANSLATION_VARIANT = "fitted_translation"
ZERO_TRANSLATION_VARIANT = "zero_offset_translation"
ZERO_TRANSLATION_METHOD = "zero_level_clr_effect_ablation_v1"


@dataclass(frozen=True, slots=True)
class BaselineValidationVariant:
    """Intermediate and score outputs for one controlled baseline variant."""

    variant: str
    offsets: pl.DataFrame
    translated_player_evidence: pl.DataFrame
    prior: pl.DataFrame
    baselines: BaselineProfiles
    scoring_context: pl.DataFrame
    score_report: CurrentTalentScoreReport
    separate_stratified_metrics: pl.DataFrame
    component_scores: pl.DataFrame
    calibration_summary: pl.DataFrame
    metrics: dict[str, Any]


def zero_translation_offsets(fitted_offsets: pl.DataFrame) -> pl.DataFrame:
    """Return a zero-effect observation layer with the fitted support metadata.

    The row grain and support diagnostics are preserved. Only the effect actually
    applied to predictor evidence and future target environments is set to zero.
    This makes fitted-vs-zero a controlled ablation of the learned level effects.
    """

    required = {
        "level_group",
        "core_bin",
        "clr_environment_effect",
        "anchor_level_group",
    }
    missing = sorted(required - set(fitted_offsets.columns))
    if missing:
        raise ValueError(f"fitted translation offsets missing ablation fields: {missing}")
    duplicate = fitted_offsets.group_by(["level_group", "core_bin"]).len().filter(
        pl.col("len") != 1
    )
    if not duplicate.is_empty():
        raise ValueError("fitted translation offsets violate level_group + core_bin grain")

    observed_bins = set(fitted_offsets.get_column("core_bin").unique().to_list())
    if observed_bins != set(ALL_CORE_BINS):
        raise ValueError(
            "fitted translation offsets do not contain the complete core profile: "
            f"observed={sorted(observed_bins)}"
        )
    if "MLB" not in set(fitted_offsets.get_column("level_group").unique().to_list()):
        raise ValueError("translation ablation requires MLB anchor rows")
    anchors = set(fitted_offsets.get_column("anchor_level_group").drop_nulls().to_list())
    if anchors != {"MLB"}:
        raise ValueError(f"translation ablation requires MLB reporting anchor, observed={sorted(anchors)}")

    output = fitted_offsets.with_columns(
        pl.col("clr_environment_effect").cast(pl.Float64).alias("fitted_clr_environment_effect"),
        pl.lit(0.0).cast(pl.Float64).alias("clr_environment_effect"),
        pl.lit(ZERO_TRANSLATION_METHOD).alias("ablation_method"),
    )
    check = output.group_by("level_group").agg(
        pl.col("clr_environment_effect").sum().alias("effect_sum")
    )
    if check.filter(pl.col("effect_sum").abs() > 1e-12).height:
        raise ValueError("zero translation ablation produced nonzero level effects")
    return output


def build_baseline_validation_variant(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    validation: ValidationSnapshotDataset,
    ages: pl.DataFrame,
    offsets: pl.DataFrame,
    *,
    variant: str,
    cutoff: date,
    window: EvidenceWindow,
    age_band_width_years: float = 2.0,
    min_age_level_peers: int = 12,
    prior_strength_core_events: float = 100.0,
) -> BaselineValidationVariant:
    """Run one otherwise-identical B0/B1 predictor/scoring variant."""

    if variant not in {FITTED_TRANSLATION_VARIANT, ZERO_TRANSLATION_VARIANT}:
        raise ValueError(f"unsupported Current Talent validation variant: {variant}")
    required_ages = {"player_id", "age_years", "age_source_status"}
    missing = sorted(required_ages - set(ages.columns))
    if missing:
        raise ValueError(f"ages missing baseline validation fields: {missing}")
    nonexact = ages.filter(pl.col("age_source_status") != "exact_birth_date")
    if not nonexact.is_empty():
        raise ValueError("baseline ablation requires exact age-as-of for every predictor player")

    context = (
        validation.predictor_summary.select(
            "player_id",
            "as_of_level_group",
            "as_of_environment_ambiguous",
            "prior_mlb_evidence",
            "effective_core_events",
        )
        .join(ages.select("player_id", "age_years"), on="player_id", how="left")
        .sort("player_id")
    )
    if context.filter(pl.col("age_years").is_null()).height:
        raise ValueError("baseline ablation context contains missing exact ages")

    translated = build_translated_player_evidence(
        summary,
        profile,
        offsets,
        cutoff=cutoff,
        window=window,
    )
    prior = fit_leave_one_out_age_level_prior(
        translated,
        context,
        age_band_width_years=age_band_width_years,
        min_age_level_peers=min_age_level_peers,
    )
    baselines = build_baseline_profiles(
        translated,
        prior,
        prior_strength_core_events=prior_strength_core_events,
    )
    projected = project_latent_profiles_to_target_environment(
        baselines.profile,
        validation.target_summary,
        offsets,
    )
    scoring_context = (
        validation.scoring_rows.join(
            ages.select("player_id", "age_years"),
            on="player_id",
            how="left",
        )
        .join(
            translated.select("player_id", "effective_core_events").unique(),
            on="player_id",
            how="left",
            suffix="_translated",
        )
    )
    scoring_context = add_diagnostic_bands(scoring_context)
    score_report = score_current_talent_profiles(
        projected,
        validation.target_profile,
        scoring_context=scoring_context,
    )
    separate_strata = build_separate_stratified_metrics(
        score_report.environment_scores,
        scoring_context,
    )
    component_scores = build_component_proper_score_contributions(
        projected,
        validation.target_profile,
    )
    calibration_summary = build_calibration_summary(score_report.component_calibration)

    metrics = {
        "variant": variant,
        "offset_effect_abs_sum": float(
            offsets.get_column("clr_environment_effect").abs().sum() or 0.0
        ),
        "prediction_player_count": baselines.metrics["prediction_player_count"],
        "scored_player_count": score_report.metrics["scored_player_count"],
        "scored_target_environment_count": score_report.metrics[
            "scored_target_environment_count"
        ],
    }
    return BaselineValidationVariant(
        variant=variant,
        offsets=offsets,
        translated_player_evidence=translated,
        prior=prior,
        baselines=baselines,
        scoring_context=scoring_context,
        score_report=score_report,
        separate_stratified_metrics=separate_strata,
        component_scores=component_scores,
        calibration_summary=calibration_summary,
        metrics=metrics,
    )
