#!/usr/bin/env python3
"""Evaluate the predeclared EV/LA Current Talent challenger on 2022 only.

This evaluator is deliberately offline. It consumes:

- already-certified 2021/2022 universal Current Talent results evidence;
- a pinned local Chadwick register archive for exact age-as-of;
- pre-materialized, reconciled 2021/2022 tracked-BBE parquet files.

It performs no network requests and contains no 2023 inputs. Source acquisition is
a separate gate. The model fit is frozen to 2021-07-15 and its 90-day future
contact outcomes; the fitted standardization and residual coefficients are then
held fixed across the three 2022 development folds.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from materialize_current_talent_baseline_validation import _load_universal_evidence
from universal_baseball.chadwick import build_mlbam_age_as_of, read_chadwick_people_archive
from universal_baseball.current_talent_baseline2 import (
    BASELINE2_LOOKBACK_DAYS,
    FROZEN_BASELINE2_HALF_LIFE_DAYS,
    FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
    build_baseline2_profiles,
)
from universal_baseball.current_talent_baselines import (
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
)
from universal_baseball.current_talent_batted_ball_capability import (
    build_player_tracking_capability,
)
from universal_baseball.current_talent_batted_ball_quality import (
    build_batted_ball_quality_features,
    apply_batted_ball_quality_residual,
)
from universal_baseball.current_talent_batted_ball_reconciliation import (
    RECONCILED_TRACKED_BBE_SCHEMA,
)
from universal_baseball.current_talent_batted_ball_residual_fit import (
    FIXED_RESIDUAL_L2_PENALTY,
    build_batted_ball_residual_training_table,
    fit_batted_ball_residual_coefficients,
)
from universal_baseball.current_talent_batted_ball_scoring import (
    SCORING_CHALLENGER_LABEL,
    SCORING_COMPARATOR_LABEL,
    build_baseline2_vs_richer_scoring_pair,
    relabel_richer_pair_model,
)
from universal_baseball.current_talent_batted_ball_standardization import (
    fit_batted_ball_feature_standardization,
    standardize_batted_ball_quality_features,
)
from universal_baseball.current_talent_calibration import (
    build_component_calibration_coefficients,
)
from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_score_diagnostics import (
    add_diagnostic_bands,
    build_calibration_summary,
    build_component_proper_score_contributions,
    build_separate_stratified_metrics,
)
from universal_baseball.current_talent_scoring import (
    project_latent_profiles_to_target_environment,
    score_current_talent_profiles,
)
from universal_baseball.current_talent_translation import (
    build_training_environment_transition_evidence,
    fit_level_clr_translation,
)
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.current_talent_validation_dataset import (
    TARGET_ENVIRONMENT_KEY,
    build_validation_snapshot_dataset,
)


TRAINING_CUTOFF = date(2021, 7, 15)
DEVELOPMENT_CUTOFFS = (
    date(2022, 7, 15),
    date(2022, 8, 1),
    date(2022, 9, 1),
)
HISTORY_SEASONS = (2021, 2022)
AGE_BAND_WIDTH_YEARS = 2.0
MIN_AGE_LEVEL_PEERS = 12
MIN_CORE_EVENTS_PER_STINT = 20
MAX_GAP_DAYS = 365
MEANINGFUL_NON_MLB_FUTURE_CORE_EVENTS = 1000
CALIBRATION_MAX_RELATIVE_WORSENING = 1.25
NUMERIC_TOLERANCE = 1e-12


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--milb-input-root-2021", type=Path, required=True)
    parser.add_argument("--mlb-input-root-2021", type=Path, required=True)
    parser.add_argument("--milb-input-root-2022", type=Path, required=True)
    parser.add_argument("--mlb-input-root-2022", type=Path, required=True)
    parser.add_argument("--tracked-bbe-2021", type=Path, required=True)
    parser.add_argument("--tracked-bbe-2022", type=Path, required=True)
    parser.add_argument("--chadwick-archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def _write(frame: pl.DataFrame, output_dir: Path, name: str) -> dict[str, object]:
    parquet = output_dir / f"{name}.parquet"
    csv = output_dir / f"{name}.csv"
    frame.write_parquet(parquet, compression="zstd")
    frame.write_csv(csv)
    return {
        "parquet": str(parquet),
        "csv": str(csv),
        "row_count": int(frame.height),
        "column_count": len(frame.columns),
    }


def _load_tracking(path: Path, expected_season: int) -> pl.DataFrame:
    frame = pl.read_parquet(path)
    missing = sorted(set(RECONCILED_TRACKED_BBE_SCHEMA) - set(frame.columns))
    if missing:
        raise ValueError(f"reconciled tracking {path} missing fields: {missing}")
    if frame.is_empty():
        return frame.cast(RECONCILED_TRACKED_BBE_SCHEMA, strict=True)
    seasons = {int(value) for value in frame.get_column("season").unique().to_list()}
    if seasons != {expected_season}:
        raise ValueError(
            f"reconciled tracking season mismatch for {path}: observed={sorted(seasons)}, "
            f"expected={[expected_season]}"
        )
    return frame.select(*RECONCILED_TRACKED_BBE_SCHEMA).cast(
        RECONCILED_TRACKED_BBE_SCHEMA, strict=True
    )


def _relabel_models(frame: pl.DataFrame) -> pl.DataFrame:
    if "model" not in frame.columns:
        return frame
    return frame.with_columns(
        pl.col("model")
        .map_elements(relabel_richer_pair_model, return_dtype=pl.String)
        .alias("model")
    )


def _model_rows(frame: pl.DataFrame) -> dict[str, dict[str, object]]:
    return {str(row["model"]): dict(row) for row in frame.iter_rows(named=True)}


def _mean_model_metric(frame: pl.DataFrame, model: str, column: str) -> float:
    values = frame.filter(pl.col("model") == model).get_column(column)
    if values.is_empty():
        raise ValueError(f"missing {model} values for {column}")
    return float(values.mean())


def _coverage(frame: pl.DataFrame) -> dict[str, tuple[int, int, int]]:
    if frame.is_empty():
        return {}
    rows = (
        frame.group_by("model")
        .agg(
            pl.col("player_id").n_unique().alias("player_count"),
            pl.len().alias("target_environment_rows"),
            pl.col("future_core_events").sum().alias("future_core_events"),
        )
        .to_dicts()
    )
    return {
        str(row["model"]): (
            int(row["player_count"]),
            int(row["target_environment_rows"]),
            int(row["future_core_events"]),
        )
        for row in rows
    }


def _fit_translation(summary: pl.DataFrame, profile: pl.DataFrame, cutoff: date):
    transition = build_training_environment_transition_evidence(
        summary,
        profile,
        training_end=cutoff,
        min_core_events_per_stint=MIN_CORE_EVENTS_PER_STINT,
        max_gap_days=MAX_GAP_DAYS,
    )
    fitted = fit_level_clr_translation(
        transition.pair_summary,
        transition.pair_profile,
        anchor_level="MLB",
    )
    return fitted, {**transition.metrics, **{f"fit_{k}": v for k, v in fitted.metrics.items()}}


def _build_b2_snapshot(
    *,
    current_summary: pl.DataFrame,
    current_profile: pl.DataFrame,
    history_summary: pl.DataFrame,
    history_profile: pl.DataFrame,
    people: pl.DataFrame,
    cutoff: date,
):
    translation, translation_metrics = _fit_translation(current_summary, current_profile, cutoff)
    frozen_window = EvidenceWindow(
        label="frozen_current_season_180d",
        lookback_days=None,
        half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
    )
    b2_window = EvidenceWindow(
        label="baseline2_multiseason_1095d_180d",
        lookback_days=BASELINE2_LOOKBACK_DAYS,
        half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
    )
    validation = build_validation_snapshot_dataset(
        current_summary,
        current_profile,
        cutoff=cutoff,
        window=frozen_window,
    )
    predictor_ids = sorted(
        int(value) for value in validation.predictor_summary.get_column("player_id").to_list()
    )
    ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
    missing_age = ages.filter(pl.col("age_source_status") != "exact_birth_date")
    if not missing_age.is_empty():
        raise ValueError(f"richer development requires exact age at {cutoff}")

    context = (
        validation.predictor_summary.select(
            "player_id",
            "as_of_level_group",
            "as_of_environment_ambiguous",
            "prior_mlb_evidence",
        )
        .join(ages.select("player_id", "age_years"), on="player_id", how="left")
        .sort("player_id")
    )
    if context.filter(pl.col("age_years").is_null()).height:
        raise ValueError(f"richer development context has missing age at {cutoff}")

    current_translated = build_translated_player_evidence(
        current_summary,
        current_profile,
        translation.offsets,
        cutoff=cutoff,
        window=frozen_window,
    )
    frozen_prior = fit_leave_one_out_age_level_prior(
        current_translated,
        context,
        age_band_width_years=AGE_BAND_WIDTH_YEARS,
        min_age_level_peers=MIN_AGE_LEVEL_PEERS,
    )
    multiseason_translated = build_translated_player_evidence(
        history_summary,
        history_profile,
        translation.offsets,
        cutoff=cutoff,
        window=b2_window,
    )
    b2 = build_baseline2_profiles(
        multiseason_translated,
        frozen_prior,
        prior_strength_core_events=FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
    )
    return {
        "translation": translation,
        "translation_metrics": translation_metrics,
        "validation": validation,
        "ages": ages,
        "baseline2": b2,
        "multiseason_translated": multiseason_translated,
    }


def _b2_player_features(features: pl.DataFrame, b2_profile: pl.DataFrame) -> pl.DataFrame:
    player_ids = b2_profile.select("player_id").unique()
    return features.join(player_ids, on="player_id", how="inner").sort("player_id")


def _tracked_bbe_band() -> pl.Expr:
    return (
        pl.when(pl.col("raw_complete_tracked_bbe") < 30)
        .then(pl.lit("20-29"))
        .when(pl.col("raw_complete_tracked_bbe") < 50)
        .then(pl.lit("30-49"))
        .when(pl.col("raw_complete_tracked_bbe") < 100)
        .then(pl.lit("50-99"))
        .otherwise(pl.lit("100+"))
        .alias("tracked_bbe_band")
    )


def _build_scoring_context(
    *,
    snapshot: dict[str, Any],
    features: pl.DataFrame,
    capability: pl.DataFrame,
    eligible_player_ids: pl.DataFrame,
) -> pl.DataFrame:
    validation = snapshot["validation"]
    ages = snapshot["ages"]
    multiseason = snapshot["multiseason_translated"]
    context = (
        validation.scoring_rows.join(eligible_player_ids, on="player_id", how="inner")
        .join(ages.select("player_id", "age_years"), on="player_id", how="left")
        .join(
            multiseason.select(
                "player_id",
                pl.col("effective_core_events").alias("effective_core_events_translated"),
            ).unique(),
            on="player_id",
            how="left",
        )
        .join(
            features.select(
                "player_id",
                "raw_complete_tracked_bbe",
                "effective_complete_tracked_bbe",
                "recency_weighted_mean_exit_velocity",
                "recency_weighted_sweet_spot_share",
            ),
            on="player_id",
            how="left",
        )
        .join(
            capability.select(
                "player_id",
                "observed_model_bbe",
                "observed_tracked_game_count",
                "observed_mlb_bbe",
                "observed_milb_bbe",
                "source_family_group",
                "source_capability_tier_count",
                "observed_source_capability_tiers",
                "observed_level_groups",
                "observed_league_ids",
            ),
            on="player_id",
            how="left",
        )
    )
    if context.filter(
        pl.col("age_years").is_null()
        | pl.col("effective_core_events_translated").is_null()
        | pl.col("raw_complete_tracked_bbe").is_null()
        | pl.col("source_family_group").is_null()
    ).height:
        raise ValueError("richer scoring context lost required age/evidence/capability fields")
    return add_diagnostic_bands(context).with_columns(_tracked_bbe_band()).sort(
        list(TARGET_ENVIRONMENT_KEY)
    )


def _event_weighted_pair(frame: pl.DataFrame) -> dict[str, dict[str, float | int]]:
    if frame.is_empty():
        return {}
    weight = pl.col("future_core_events").cast(pl.Float64)
    rows = (
        frame.group_by("model")
        .agg(
            pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
            ((pl.col("log_loss") * weight).sum() / weight.sum()).alias("log_loss"),
            ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias("brier"),
        )
        .to_dicts()
    )
    return {
        str(row["model"]): {
            "future_core_events": int(row["future_core_events"]),
            "log_loss": float(row["log_loss"]),
            "brier": float(row["brier"]),
        }
        for row in rows
    }


def _capability_tier_rows(
    environment_scores: pl.DataFrame,
    scoring_context: pl.DataFrame,
    *,
    cutoff: date,
) -> pl.DataFrame:
    context = scoring_context.select(
        *TARGET_ENVIRONMENT_KEY, "observed_source_capability_tiers"
    )
    joined = environment_scores.join(context, on=list(TARGET_ENVIRONMENT_KEY), how="left")
    tokens = sorted(
        {
            token
            for value in joined.get_column("observed_source_capability_tiers").drop_nulls().to_list()
            for token in str(value).split("|")
            if token
        }
    )
    outputs: list[pl.DataFrame] = []
    for token in tokens:
        subset = joined.filter(
            pl.col("observed_source_capability_tiers")
            .str.split("|")
            .list.contains(token)
        )
        if subset.is_empty():
            continue
        weight = pl.col("future_core_events").cast(pl.Float64)
        outputs.append(
            subset.group_by("model")
            .agg(
                pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
                pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
                ((pl.col("log_loss") * weight).sum() / weight.sum()).alias(
                    "event_weighted_log_loss"
                ),
                ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias(
                    "event_weighted_multinomial_brier"
                ),
            )
            .with_columns(
                pl.lit(cutoff).alias("as_of_date"),
                pl.lit(token).alias("source_capability_tier"),
                pl.lit(token.startswith("MILB_SAVANT_TRACKED:")).alias("non_mlb_source_tier"),
            )
        )
    if not outputs:
        return pl.DataFrame()
    return pl.concat(outputs, how="vertical_relaxed").sort(
        ["as_of_date", "source_capability_tier", "model"]
    )


def _paired_deltas(frame: pl.DataFrame) -> tuple[float, float]:
    by_model = _model_rows(frame)
    if set(by_model) != {SCORING_COMPARATOR_LABEL, SCORING_CHALLENGER_LABEL}:
        raise ValueError("paired aggregate metrics do not contain B2 and richer rows")
    comparator = by_model[SCORING_COMPARATOR_LABEL]
    richer = by_model[SCORING_CHALLENGER_LABEL]
    return (
        float(richer["event_weighted_log_loss"]) - float(comparator["event_weighted_log_loss"]),
        float(richer["event_weighted_multinomial_brier"])
        - float(comparator["event_weighted_multinomial_brier"]),
    )


def _non_mlb_guardrails(capability: pl.DataFrame) -> tuple[dict[str, object], list[dict[str, object]]]:
    if capability.is_empty():
        return {
            "future_core_events": 0,
            "meaningfully_supported": False,
            "equal_fold_mean_log_loss_delta": None,
            "richer_log_loss_improves": False,
        }, []

    non_mlb = capability.filter(pl.col("non_mlb_source_tier"))
    tier_failures: list[dict[str, object]] = []
    tier_support_rows: list[dict[str, object]] = []
    for tier in sorted(non_mlb.get_column("source_capability_tier").unique().to_list()):
        tier_frame = non_mlb.filter(pl.col("source_capability_tier") == tier)
        support = int(
            tier_frame.filter(pl.col("model") == SCORING_COMPARATOR_LABEL)
            .get_column("future_core_events")
            .sum()
            or 0
        )
        worse_both = 0
        for cutoff in sorted(tier_frame.get_column("as_of_date").unique().to_list()):
            fold = tier_frame.filter(pl.col("as_of_date") == cutoff)
            by_model = _model_rows(fold)
            if set(by_model) != {SCORING_COMPARATOR_LABEL, SCORING_CHALLENGER_LABEL}:
                raise ValueError(f"capability tier {tier} lacks paired model rows at {cutoff}")
            b2 = by_model[SCORING_COMPARATOR_LABEL]
            richer = by_model[SCORING_CHALLENGER_LABEL]
            if (
                float(richer["event_weighted_log_loss"]) > float(b2["event_weighted_log_loss"])
                and float(richer["event_weighted_multinomial_brier"])
                > float(b2["event_weighted_multinomial_brier"])
            ):
                worse_both += 1
        meaningful = support >= MEANINGFUL_NON_MLB_FUTURE_CORE_EVENTS
        record = {
            "source_capability_tier": str(tier),
            "future_core_events": support,
            "meaningfully_supported": meaningful,
            "worse_on_both_fold_count": worse_both,
        }
        tier_support_rows.append(record)
        if meaningful and worse_both >= 2:
            tier_failures.append(record)

    # "Not solely an MLB artifact" is operationalized before scoring as a
    # combined any-MiLB-evidence cohort. Players may have mixed MLB/MiLB tracked
    # histories; they qualify because some observed richer evidence came from MiLB.
    # A cohort with <1000 future events is insufficient to establish transport.
    # Build the combined cohort from per-tier aggregate rows without summing them,
    # because players can appear in multiple source tiers. The caller supplies a
    # separate combined cohort below; this function only returns per-tier failures.
    return {
        "tier_diagnostics": tier_support_rows,
    }, tier_failures


def _combined_milb_evidence_fold(
    environment_scores: pl.DataFrame,
    scoring_context: pl.DataFrame,
    *,
    cutoff: date,
) -> pl.DataFrame:
    context = scoring_context.select(
        *TARGET_ENVIRONMENT_KEY, "observed_milb_bbe"
    ).filter(pl.col("observed_milb_bbe") > 0)
    subset = environment_scores.join(context, on=list(TARGET_ENVIRONMENT_KEY), how="inner")
    if subset.is_empty():
        return pl.DataFrame()
    weight = pl.col("future_core_events").cast(pl.Float64)
    return (
        subset.group_by("model")
        .agg(
            pl.col("future_core_events").sum().cast(pl.Int64).alias("future_core_events"),
            pl.col("player_id").n_unique().cast(pl.Int64).alias("player_count"),
            ((pl.col("log_loss") * weight).sum() / weight.sum()).alias(
                "event_weighted_log_loss"
            ),
            ((pl.col("multinomial_brier") * weight).sum() / weight.sum()).alias(
                "event_weighted_multinomial_brier"
            ),
        )
        .with_columns(pl.lit(cutoff).alias("as_of_date"))
        .sort("model")
    )


def _mean_pair_delta(frame: pl.DataFrame, metric: str) -> float:
    fold_deltas: list[float] = []
    for cutoff in sorted(frame.get_column("as_of_date").unique().to_list()):
        fold = frame.filter(pl.col("as_of_date") == cutoff)
        by_model = _model_rows(fold)
        if set(by_model) != {SCORING_COMPARATOR_LABEL, SCORING_CHALLENGER_LABEL}:
            raise ValueError(f"combined MiLB-evidence cohort lacks paired models at {cutoff}")
        fold_deltas.append(
            float(by_model[SCORING_CHALLENGER_LABEL][metric])
            - float(by_model[SCORING_COMPARATOR_LABEL][metric])
        )
    return sum(fold_deltas) / len(fold_deltas)


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    if not args.chadwick_archive.is_file():
        raise ValueError("offline richer evaluator requires an existing Chadwick archive")
    people = read_chadwick_people_archive(args.chadwick_archive)

    summary_2021, profile_2021, metrics_2021, inputs_2021 = _load_universal_evidence(
        args.milb_input_root_2021,
        args.mlb_input_root_2021,
        2021,
    )
    summary_2022, profile_2022, metrics_2022, inputs_2022 = _load_universal_evidence(
        args.milb_input_root_2022,
        args.mlb_input_root_2022,
        2022,
    )
    history_summary, history_profile, history_metrics = combine_universal_player_game_evidence(
        [summary_2021, summary_2022],
        [profile_2021, profile_2022],
        expected_seasons=set(HISTORY_SEASONS),
        require_all_universal_leagues=False,
    )

    tracking_2021 = _load_tracking(args.tracked_bbe_2021, 2021)
    tracking_2022 = _load_tracking(args.tracked_bbe_2022, 2022)
    tracking_history = pl.concat([tracking_2021, tracking_2022], how="vertical_relaxed")

    # Fixed 2021 training snapshot. 2022 outcomes/features cannot enter here.
    training_snapshot = _build_b2_snapshot(
        current_summary=summary_2021,
        current_profile=profile_2021,
        history_summary=summary_2021,
        history_profile=profile_2021,
        people=people,
        cutoff=TRAINING_CUTOFF,
    )
    training_features = _b2_player_features(
        build_batted_ball_quality_features(tracking_2021, cutoff=TRAINING_CUTOFF),
        training_snapshot["baseline2"].profile,
    )
    standardization = fit_batted_ball_feature_standardization(training_features)
    standardized_training = standardize_batted_ball_quality_features(
        training_features, standardization
    )
    training_table = build_batted_ball_residual_training_table(
        training_snapshot["baseline2"].profile,
        standardized_training,
        training_snapshot["validation"].target_summary,
        training_snapshot["validation"].target_profile,
        training_snapshot["translation"].offsets,
        expected_as_of_date=TRAINING_CUTOFF,
    )
    residual_fit = fit_batted_ball_residual_coefficients(training_table)

    fold_rows: list[dict[str, object]] = []
    component_frames: list[pl.DataFrame] = []
    calibration_frames: list[pl.DataFrame] = []
    strata_frames: list[pl.DataFrame] = []
    capability_frames: list[pl.DataFrame] = []
    milb_cohort_frames: list[pl.DataFrame] = []
    feature_frames: list[pl.DataFrame] = []
    scoring_context_frames: list[pl.DataFrame] = []
    translation_support: list[dict[str, object]] = []

    for cutoff in DEVELOPMENT_CUTOFFS:
        snapshot = _build_b2_snapshot(
            current_summary=summary_2022,
            current_profile=profile_2022,
            history_summary=history_summary,
            history_profile=history_profile,
            people=people,
            cutoff=cutoff,
        )
        translation_support.append(
            {"as_of_date": cutoff.isoformat(), **snapshot["translation_metrics"]}
        )

        features = _b2_player_features(
            build_batted_ball_quality_features(tracking_history, cutoff=cutoff),
            snapshot["baseline2"].profile,
        )
        standardized = standardize_batted_ball_quality_features(features, standardization)
        richer_profile = apply_batted_ball_quality_residual(
            snapshot["baseline2"].profile,
            standardized,
            residual_fit.coefficients,
        )
        pair = build_baseline2_vs_richer_scoring_pair(richer_profile, richer_eligible_only=True)
        eligible_ids = pair.select("player_id").unique()
        if eligible_ids.is_empty():
            raise ValueError(f"no richer-eligible B2 players at {cutoff}")

        capability = build_player_tracking_capability(tracking_history, cutoff=cutoff).join(
            eligible_ids, on="player_id", how="inner"
        )
        scoring_context = _build_scoring_context(
            snapshot=snapshot,
            features=features,
            capability=capability,
            eligible_player_ids=eligible_ids,
        )
        projected = project_latent_profiles_to_target_environment(
            pair,
            snapshot["validation"].target_summary,
            snapshot["translation"].offsets,
        )
        scores = score_current_talent_profiles(
            projected,
            snapshot["validation"].target_profile,
            scoring_context=scoring_context,
        )
        aggregate = _relabel_models(scores.aggregate_metrics)
        environment_scores = _relabel_models(scores.environment_scores)
        coverage = _coverage(environment_scores)
        coverage_equal = (
            set(coverage) == {SCORING_COMPARATOR_LABEL, SCORING_CHALLENGER_LABEL}
            and coverage[SCORING_COMPARATOR_LABEL] == coverage[SCORING_CHALLENGER_LABEL]
        )
        log_delta, brier_delta = _paired_deltas(aggregate)

        coefficients = _relabel_models(
            build_component_calibration_coefficients(projected, snapshot["validation"].target_profile)
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        reliability = _relabel_models(build_calibration_summary(scores.component_calibration))
        calibration_frames.append(coefficients)

        component = _relabel_models(
            build_component_proper_score_contributions(
                projected, snapshot["validation"].target_profile
            )
        ).join(
            coefficients.select(
                "model",
                "core_bin",
                "calibration_intercept",
                "calibration_slope",
                "absolute_intercept_error",
                "absolute_slope_error",
                "converged",
                "fit_status",
            ),
            on=["model", "core_bin"],
            how="inner",
        ).join(
            reliability.select(
                "model",
                "core_bin",
                "event_weighted_expected_calibration_error",
            ),
            on=["model", "core_bin"],
            how="inner",
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        component_frames.append(component)

        strata = _relabel_models(
            build_separate_stratified_metrics(
                environment_scores,
                scoring_context,
                strata=(
                    "target_level_group",
                    "target_transition",
                    "age_band",
                    "evidence_band",
                    "tracked_bbe_band",
                    "source_family_group",
                    "observed_level_groups",
                ),
            )
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        strata_frames.append(strata)

        capability_rows = _capability_tier_rows(
            environment_scores, scoring_context, cutoff=cutoff
        )
        if not capability_rows.is_empty():
            capability_frames.append(capability_rows)
        milb_cohort = _combined_milb_evidence_fold(
            environment_scores, scoring_context, cutoff=cutoff
        )
        if not milb_cohort.is_empty():
            milb_cohort_frames.append(milb_cohort)

        feature_frames.append(features.with_columns(pl.lit(cutoff).alias("feature_cutoff")))
        scoring_context_frames.append(scoring_context.with_columns(pl.lit(cutoff).alias("fold_cutoff")))

        by_model = _model_rows(aggregate)
        b2_row = by_model[SCORING_COMPARATOR_LABEL]
        richer_row = by_model[SCORING_CHALLENGER_LABEL]
        fold_rows.append(
            {
                "as_of_date": cutoff,
                "baseline2_log_loss": float(b2_row["event_weighted_log_loss"]),
                "richer_log_loss": float(richer_row["event_weighted_log_loss"]),
                "richer_minus_baseline2_log_loss": log_delta,
                "baseline2_brier": float(b2_row["event_weighted_multinomial_brier"]),
                "richer_brier": float(richer_row["event_weighted_multinomial_brier"]),
                "richer_minus_baseline2_brier": brier_delta,
                "richer_log_loss_win": log_delta < 0,
                "richer_brier_win": brier_delta < 0,
                "coverage_equal": coverage_equal,
                "scored_player_count": coverage.get(SCORING_CHALLENGER_LABEL, (0, 0, 0))[0],
                "scored_target_environment_rows": coverage.get(
                    SCORING_CHALLENGER_LABEL, (0, 0, 0)
                )[1],
                "future_core_events": coverage.get(SCORING_CHALLENGER_LABEL, (0, 0, 0))[2],
                "richer_eligible_player_count": int(eligible_ids.height),
                "eligible_player_with_any_milb_bbe": int(
                    capability.filter(pl.col("observed_milb_bbe") > 0).height
                ),
                "all_calibration_fits_converged": bool(coefficients.get_column("converged").all()),
                "baseline2_mean_abs_calibration_intercept_error": _mean_model_metric(
                    coefficients, SCORING_COMPARATOR_LABEL, "absolute_intercept_error"
                ),
                "richer_mean_abs_calibration_intercept_error": _mean_model_metric(
                    coefficients, SCORING_CHALLENGER_LABEL, "absolute_intercept_error"
                ),
                "baseline2_mean_abs_calibration_slope_error": _mean_model_metric(
                    coefficients, SCORING_COMPARATOR_LABEL, "absolute_slope_error"
                ),
                "richer_mean_abs_calibration_slope_error": _mean_model_metric(
                    coefficients, SCORING_CHALLENGER_LABEL, "absolute_slope_error"
                ),
            }
        )

    folds = pl.DataFrame(fold_rows).sort("as_of_date")
    if folds.height != len(DEVELOPMENT_CUTOFFS):
        raise ValueError("richer development did not produce all three predeclared folds")
    components = pl.concat(component_frames, how="vertical_relaxed")
    calibration = pl.concat(calibration_frames, how="vertical_relaxed")
    strata = pl.concat(strata_frames, how="vertical_relaxed")
    capability_tiers = (
        pl.concat(capability_frames, how="vertical_relaxed") if capability_frames else pl.DataFrame()
    )
    milb_cohort = (
        pl.concat(milb_cohort_frames, how="vertical_relaxed") if milb_cohort_frames else pl.DataFrame()
    )
    feature_surface = pl.concat(feature_frames, how="vertical_relaxed")
    scoring_context_surface = pl.concat(scoring_context_frames, how="vertical_relaxed")

    mean_b2_log = float(folds.get_column("baseline2_log_loss").mean())
    mean_richer_log = float(folds.get_column("richer_log_loss").mean())
    mean_b2_brier = float(folds.get_column("baseline2_brier").mean())
    mean_richer_brier = float(folds.get_column("richer_brier").mean())
    log_win_count = int(folds.get_column("richer_log_loss_win").sum())
    coverage_equal = bool(folds.get_column("coverage_equal").all())
    calibration_converged = bool(folds.get_column("all_calibration_fits_converged").all())

    mean_b2_intercept = float(
        folds.get_column("baseline2_mean_abs_calibration_intercept_error").mean()
    )
    mean_richer_intercept = float(
        folds.get_column("richer_mean_abs_calibration_intercept_error").mean()
    )
    mean_b2_slope = float(
        folds.get_column("baseline2_mean_abs_calibration_slope_error").mean()
    )
    mean_richer_slope = float(
        folds.get_column("richer_mean_abs_calibration_slope_error").mean()
    )

    non_mlb_summary, tier_failures = _non_mlb_guardrails(capability_tiers)
    if milb_cohort.is_empty():
        milb_support = 0
        milb_log_delta = None
        milb_transport_pass = False
    else:
        milb_support = int(
            milb_cohort.filter(pl.col("model") == SCORING_COMPARATOR_LABEL)
            .get_column("future_core_events")
            .sum()
            or 0
        )
        milb_log_delta = _mean_pair_delta(milb_cohort, "event_weighted_log_loss")
        milb_transport_pass = (
            milb_support >= MEANINGFUL_NON_MLB_FUTURE_CORE_EVENTS and milb_log_delta < 0
        )

    promotion_checks = {
        "lower_equal_fold_mean_log_loss": mean_richer_log < mean_b2_log,
        "no_worse_equal_fold_mean_brier": mean_richer_brier <= mean_b2_brier + NUMERIC_TOLERANCE,
        "log_loss_wins_at_least_2_of_3": log_win_count >= 2,
        "identical_scored_coverage": coverage_equal,
        "non_mlb_evidence_cohort_supported_and_improves_log_loss": milb_transport_pass,
        "no_meaningful_non_mlb_capability_tier_worse_on_both_in_2_folds": not tier_failures,
        "all_component_calibration_fits_converged": calibration_converged,
        "calibration_intercept_within_25pct_guardrail": (
            mean_richer_intercept <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_b2_intercept
        ),
        "calibration_slope_within_25pct_guardrail": (
            mean_richer_slope <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_b2_slope
        ),
    }
    eligible_for_confirmation = all(promotion_checks.values())

    output_tables = {
        "training_features": _write(training_features, args.output_dir, "richer_training_features"),
        "training_standardized_features": _write(
            standardized_training, args.output_dir, "richer_training_standardized_features"
        ),
        "training_table": _write(training_table, args.output_dir, "richer_training_table"),
        "residual_coefficients": _write(
            residual_fit.coefficients, args.output_dir, "richer_residual_coefficients"
        ),
        "fold_metrics": _write(folds, args.output_dir, "richer_development_fold_metrics"),
        "component_metrics": _write(
            components, args.output_dir, "richer_development_component_metrics"
        ),
        "calibration_coefficients": _write(
            calibration, args.output_dir, "richer_development_calibration_coefficients"
        ),
        "stratum_metrics": _write(
            strata, args.output_dir, "richer_development_stratum_metrics"
        ),
        "feature_surface": _write(
            feature_surface, args.output_dir, "richer_development_feature_surface"
        ),
        "scoring_context": _write(
            scoring_context_surface, args.output_dir, "richer_development_scoring_context"
        ),
    }
    if not capability_tiers.is_empty():
        output_tables["capability_tier_metrics"] = _write(
            capability_tiers, args.output_dir, "richer_development_capability_tier_metrics"
        )
    if not milb_cohort.is_empty():
        output_tables["milb_evidence_cohort_metrics"] = _write(
            milb_cohort, args.output_dir, "richer_development_milb_evidence_cohort_metrics"
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "current_talent_batted_ball_quality_2022_development",
        "offline_evaluator": True,
        "network_requests_performed": False,
        "training_cutoff": TRAINING_CUTOFF.isoformat(),
        "development_cutoffs": [value.isoformat() for value in DEVELOPMENT_CUTOFFS],
        "confirmation_data_present": False,
        "comparator": "translated_multiseason_recency_empirical_bayes_v1",
        "challenger": "baseline2_plus_ev_sweet_spot_contact_residual_v1",
        "tracked_bbe_definition": (
            "result_producing_type_X_terminal_event_complete_EV_LA_non_bunt_pitch_grain"
        ),
        "primary_min_complete_tracked_bbe": 20,
        "feature_half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
        "fixed_l2_penalty": FIXED_RESIDUAL_L2_PENALTY,
        "penalty_search_performed": False,
        "feature_standardization": asdict(standardization),
        "residual_fit_metrics": residual_fit.metrics,
        "proper_score_summary": {
            "baseline2_equal_fold_mean_log_loss": mean_b2_log,
            "richer_equal_fold_mean_log_loss": mean_richer_log,
            "richer_minus_baseline2_equal_fold_mean_log_loss": mean_richer_log - mean_b2_log,
            "baseline2_equal_fold_mean_brier": mean_b2_brier,
            "richer_equal_fold_mean_brier": mean_richer_brier,
            "richer_minus_baseline2_equal_fold_mean_brier": mean_richer_brier - mean_b2_brier,
            "richer_log_loss_fold_wins": log_win_count,
        },
        "calibration_summary": {
            "baseline2_mean_abs_intercept_error": mean_b2_intercept,
            "richer_mean_abs_intercept_error": mean_richer_intercept,
            "baseline2_mean_abs_slope_error": mean_b2_slope,
            "richer_mean_abs_slope_error": mean_richer_slope,
        },
        "non_mlb_transport": {
            "combined_any_milb_evidence_future_core_events": milb_support,
            "combined_any_milb_evidence_equal_fold_mean_log_loss_delta": milb_log_delta,
            "combined_any_milb_evidence_supported_and_improves": milb_transport_pass,
            **non_mlb_summary,
            "failed_capability_tiers": tier_failures,
        },
        "promotion_checks": promotion_checks,
        "eligible_for_fixed_2023_confirmation": eligible_for_confirmation,
        "source_inputs": {
            "certified_results_2021": inputs_2021,
            "certified_results_2022": inputs_2022,
            "tracked_bbe_2021": str(args.tracked_bbe_2021),
            "tracked_bbe_2022": str(args.tracked_bbe_2022),
            "chadwick_archive": str(args.chadwick_archive),
        },
        "source_metrics": {
            "universal_2021": metrics_2021,
            "universal_2022": metrics_2022,
            "universal_history": history_metrics,
            "translation_support_by_cutoff": translation_support,
        },
        "outputs": output_tables,
        "decision_boundary": (
            "This report may authorize only the fixed 2023 richer confirmation when every "
            "predeclared development check passes. It does not authorize feature/threshold/" 
            "penalty/model-form reselection and does not perform any 2023 evaluation."
        ),
    }
    report_path = args.output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
