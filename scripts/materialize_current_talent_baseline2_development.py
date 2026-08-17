#!/usr/bin/env python3
"""Evaluate the predeclared Current Talent Baseline 2 challenger on 2022 only.

The challenger changes one thing relative to the frozen Baseline 1 comparator:
it lets player-specific results evidence cross season boundaries.  Hyperparameters,
translation, Baseline 0 prior, target construction, and scoring stay frozen.

2023 is intentionally absent from this script.  It remains the confirmation set
unless the 2022 development gate passes.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from materialize_current_talent_baseline_validation import _load_universal_evidence
from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_baseline2 import (
    BASELINE2_LOOKBACK_DAYS,
    BASELINE2_METHOD,
    FROZEN_BASELINE2_HALF_LIFE_DAYS,
    FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
    build_baseline2_profiles,
    build_frozen_b1_vs_b2_scoring_pair,
    relabel_pair_model,
)
from universal_baseball.current_talent_baselines import (
    build_baseline_profiles,
    build_translated_player_evidence,
    fit_leave_one_out_age_level_prior,
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
    build_validation_snapshot_dataset,
)


DEVELOPMENT_SEASON = 2022
HISTORY_SEASONS = (2021, 2022)
CUTOFF_MONTH_DAYS = ("07-15", "08-01", "09-01")
AGE_BAND_WIDTH_YEARS = 2.0
MIN_AGE_LEVEL_PEERS = 12
MIN_CORE_EVENTS_PER_STINT = 20
MAX_GAP_DAYS = 365
MEANINGFUL_LEVEL_FUTURE_CORE_EVENTS = 1000
CALIBRATION_MAX_RELATIVE_WORSENING = 1.25
NUMERIC_TOLERANCE = 1e-12


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--milb-input-root-2021", type=Path, required=True)
    parser.add_argument("--mlb-input-root-2021", type=Path, required=True)
    parser.add_argument("--milb-input-root-2022", type=Path, required=True)
    parser.add_argument("--mlb-input-root-2022", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-baseline2-development"),
    )
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


def _relabel_models(frame: pl.DataFrame) -> pl.DataFrame:
    if "model" not in frame.columns:
        return frame
    return frame.with_columns(
        pl.col("model")
        .map_elements(relabel_pair_model, return_dtype=pl.String)
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


def _level_guardrail(strata: pl.DataFrame) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    level_rows = strata.filter(pl.col("stratum_type") == "target_level_group")
    diagnostics: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    levels = sorted(
        str(value)
        for value in level_rows.get_column("stratum_value").unique().to_list()
        if str(value) != "MLB"
    )
    for level in levels:
        level_frame = level_rows.filter(pl.col("stratum_value") == level)
        comparator = level_frame.filter(pl.col("model") == "frozen_baseline1")
        support = int(comparator.get_column("future_core_events").sum() or 0)
        reversal_folds = 0
        fold_deltas: list[dict[str, object]] = []
        for cutoff in sorted(level_frame.get_column("as_of_date").unique().to_list()):
            fold = level_frame.filter(pl.col("as_of_date") == cutoff)
            by_model = _model_rows(fold)
            if set(by_model) != {"frozen_baseline1", "baseline2"}:
                raise ValueError(f"level stratum {level} at {cutoff} lacks paired models")
            frozen = by_model["frozen_baseline1"]
            challenger = by_model["baseline2"]
            log_delta = float(challenger["event_weighted_log_loss"]) - float(
                frozen["event_weighted_log_loss"]
            )
            brier_delta = float(challenger["event_weighted_multinomial_brier"]) - float(
                frozen["event_weighted_multinomial_brier"]
            )
            reversed_both = log_delta > 0 and brier_delta > 0
            reversal_folds += int(reversed_both)
            fold_deltas.append(
                {
                    "as_of_date": cutoff.isoformat() if hasattr(cutoff, "isoformat") else str(cutoff),
                    "log_loss_delta": log_delta,
                    "brier_delta": brier_delta,
                    "worse_on_both": bool(reversed_both),
                }
            )
        meaningful = support >= MEANINGFUL_LEVEL_FUTURE_CORE_EVENTS
        failed = meaningful and reversal_folds >= 2
        diagnostic = {
            "level_group": level,
            "future_core_events": support,
            "meaningfully_supported": meaningful,
            "worse_on_both_proper_scores_fold_count": reversal_folds,
            "failed_guardrail": failed,
            "fold_deltas": fold_deltas,
        }
        diagnostics.append(diagnostic)
        if failed:
            failures.append(diagnostic)
    return diagnostics, failures


def main() -> int:
    args = _parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)

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

    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    frozen_window = EvidenceWindow(
        label="frozen_b1_season_to_date_180d",
        lookback_days=None,
        half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
    )
    baseline2_window = EvidenceWindow(
        label="baseline2_multiseason_1095d_180d",
        lookback_days=BASELINE2_LOOKBACK_DAYS,
        half_life_days=FROZEN_BASELINE2_HALF_LIFE_DAYS,
    )

    fold_rows: list[dict[str, object]] = []
    component_frames: list[pl.DataFrame] = []
    stratum_frames: list[pl.DataFrame] = []
    calibration_frames: list[pl.DataFrame] = []
    history_frames: list[pl.DataFrame] = []
    translation_support: list[dict[str, object]] = []

    for month_day in CUTOFF_MONTH_DAYS:
        cutoff = date.fromisoformat(f"{DEVELOPMENT_SEASON}-{month_day}")

        # Freeze translation to exactly the comparator's current-season training
        # surface. Prior-season results are the only challenger addition.
        transition_evidence = build_training_environment_transition_evidence(
            summary_2022,
            profile_2022,
            training_end=cutoff,
            min_core_events_per_stint=MIN_CORE_EVENTS_PER_STINT,
            max_gap_days=MAX_GAP_DAYS,
        )
        translation_fit = fit_level_clr_translation(
            transition_evidence.pair_summary,
            transition_evidence.pair_profile,
            anchor_level="MLB",
        )
        translation_support.append(
            {
                "as_of_date": cutoff.isoformat(),
                **transition_evidence.metrics,
                **{f"translation_fit_{key}": value for key, value in translation_fit.metrics.items()},
            }
        )

        validation = build_validation_snapshot_dataset(
            summary_2022,
            profile_2022,
            cutoff=cutoff,
            window=frozen_window,
        )
        predictor_ids = sorted(
            int(value)
            for value in validation.predictor_summary.get_column("player_id").to_list()
        )
        ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
        missing_age = ages.filter(pl.col("age_source_status") != "exact_birth_date")
        if not missing_age.is_empty():
            raise ValueError(f"Baseline 2 development requires exact age at {cutoff}")

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
            raise ValueError(f"Baseline 2 development context has missing age at {cutoff}")

        frozen_translated = build_translated_player_evidence(
            summary_2022,
            profile_2022,
            translation_fit.offsets,
            cutoff=cutoff,
            window=frozen_window,
        )
        frozen_prior = fit_leave_one_out_age_level_prior(
            frozen_translated,
            context,
            age_band_width_years=AGE_BAND_WIDTH_YEARS,
            min_age_level_peers=MIN_AGE_LEVEL_PEERS,
        )
        frozen_b1 = build_baseline_profiles(
            frozen_translated,
            frozen_prior,
            prior_strength_core_events=FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
        )

        multiseason_translated = build_translated_player_evidence(
            history_summary,
            history_profile,
            translation_fit.offsets,
            cutoff=cutoff,
            window=baseline2_window,
        )
        baseline2 = build_baseline2_profiles(
            multiseason_translated,
            frozen_prior,
            prior_strength_core_events=FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
        )
        paired_profile = build_frozen_b1_vs_b2_scoring_pair(frozen_b1, baseline2)
        frozen_model_player_count = frozen_b1.profile.get_column("player_id").n_unique()
        baseline2_model_player_count = baseline2.profile.get_column("player_id").n_unique()
        if frozen_model_player_count != baseline2_model_player_count:
            raise ValueError(f"Baseline 2 model coverage differs from frozen B1 at {cutoff}")

        evidence_comparison = (
            frozen_translated.select(
                "player_id",
                pl.col("effective_core_events").alias("frozen_b1_effective_core_events"),
            )
            .unique()
            .join(
                baseline2.profile.select(
                    "player_id",
                    "baseline2_effective_core_events",
                ).unique(),
                on="player_id",
                how="inner",
            )
            .with_columns(
                (
                    pl.col("baseline2_effective_core_events")
                    - pl.col("frozen_b1_effective_core_events")
                ).alias("additional_effective_core_events")
            )
            .with_columns(
                (pl.col("additional_effective_core_events") > NUMERIC_TOLERANCE).alias(
                    "has_prior_season_effective_evidence"
                ),
                pl.lit(cutoff).alias("as_of_date"),
            )
        )
        if evidence_comparison.height != frozen_model_player_count:
            raise ValueError(f"Baseline 2 evidence coverage differs from frozen B1 at {cutoff}")
        history_frames.append(evidence_comparison)

        projected = project_latent_profiles_to_target_environment(
            paired_profile,
            validation.target_summary,
            translation_fit.offsets,
        )
        scoring_context = (
            validation.scoring_rows.join(
                ages.select("player_id", "age_years"),
                on="player_id",
                how="left",
            )
            .join(
                frozen_translated.select("player_id", "effective_core_events").unique(),
                on="player_id",
                how="left",
                suffix="_translated",
            )
        )
        scoring_context = add_diagnostic_bands(scoring_context).join(
            evidence_comparison.select(
                "player_id",
                "baseline2_effective_core_events",
                "additional_effective_core_events",
                "has_prior_season_effective_evidence",
            ),
            on="player_id",
            how="left",
        )

        scores = score_current_talent_profiles(
            projected,
            validation.target_profile,
            scoring_context=scoring_context,
        )
        aggregate = _relabel_models(scores.aggregate_metrics)
        environment_scores = _relabel_models(scores.environment_scores)
        by_model = _model_rows(aggregate)
        if set(by_model) != {"frozen_baseline1", "baseline2"}:
            raise ValueError(f"Baseline 2 development missing paired aggregate rows at {cutoff}")

        coverage = _coverage(environment_scores)
        coverage_equal = (
            set(coverage) == {"frozen_baseline1", "baseline2"}
            and coverage["frozen_baseline1"] == coverage["baseline2"]
        )

        coefficients = _relabel_models(
            build_component_calibration_coefficients(projected, validation.target_profile)
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        reliability = _relabel_models(
            build_calibration_summary(scores.component_calibration)
        )
        calibration_frames.append(coefficients)

        component = _relabel_models(
            build_component_proper_score_contributions(projected, validation.target_profile)
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
            build_separate_stratified_metrics(environment_scores, scoring_context)
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        stratum_frames.append(strata)

        frozen = by_model["frozen_baseline1"]
        challenger = by_model["baseline2"]
        prior_players = evidence_comparison.filter(
            pl.col("has_prior_season_effective_evidence")
        )
        fold_rows.append(
            {
                "as_of_date": cutoff,
                "frozen_baseline1_log_loss": float(frozen["event_weighted_log_loss"]),
                "baseline2_log_loss": float(challenger["event_weighted_log_loss"]),
                "baseline2_minus_frozen_log_loss": float(challenger["event_weighted_log_loss"])
                - float(frozen["event_weighted_log_loss"]),
                "frozen_baseline1_brier": float(frozen["event_weighted_multinomial_brier"]),
                "baseline2_brier": float(challenger["event_weighted_multinomial_brier"]),
                "baseline2_minus_frozen_brier": float(
                    challenger["event_weighted_multinomial_brier"]
                )
                - float(frozen["event_weighted_multinomial_brier"]),
                "baseline2_log_loss_win": float(challenger["event_weighted_log_loss"])
                < float(frozen["event_weighted_log_loss"]),
                "baseline2_brier_win": float(challenger["event_weighted_multinomial_brier"])
                < float(frozen["event_weighted_multinomial_brier"]),
                "coverage_equal": coverage_equal,
                "scored_player_count": coverage.get("baseline2", (0, 0, 0))[0],
                "scored_target_environment_rows": coverage.get("baseline2", (0, 0, 0))[1],
                "future_core_events": coverage.get("baseline2", (0, 0, 0))[2],
                "predictor_player_count": len(predictor_ids),
                "model_eligible_player_count": frozen_model_player_count,
                "players_with_prior_season_effective_evidence": int(prior_players.height),
                "share_players_with_prior_season_effective_evidence": float(prior_players.height)
                / frozen_model_player_count,
                "mean_additional_effective_core_events": float(
                    evidence_comparison.get_column("additional_effective_core_events").mean()
                ),
                "frozen_baseline1_mean_abs_calibration_intercept_error": _mean_model_metric(
                    coefficients, "frozen_baseline1", "absolute_intercept_error"
                ),
                "baseline2_mean_abs_calibration_intercept_error": _mean_model_metric(
                    coefficients, "baseline2", "absolute_intercept_error"
                ),
                "frozen_baseline1_mean_abs_calibration_slope_error": _mean_model_metric(
                    coefficients, "frozen_baseline1", "absolute_slope_error"
                ),
                "baseline2_mean_abs_calibration_slope_error": _mean_model_metric(
                    coefficients, "baseline2", "absolute_slope_error"
                ),
                "frozen_baseline1_mean_ece": _mean_model_metric(
                    reliability, "frozen_baseline1", "event_weighted_expected_calibration_error"
                ),
                "baseline2_mean_ece": _mean_model_metric(
                    reliability, "baseline2", "event_weighted_expected_calibration_error"
                ),
                "all_calibration_fits_converged": bool(
                    coefficients.get_column("converged").all()
                ),
            }
        )

    folds = pl.DataFrame(fold_rows).sort("as_of_date")
    components = pl.concat(component_frames, how="vertical_relaxed").sort(
        ["as_of_date", "core_bin", "model"]
    )
    strata = pl.concat(stratum_frames, how="vertical_relaxed").sort(
        ["as_of_date", "stratum_type", "stratum_value", "model"]
    )
    calibration = pl.concat(calibration_frames, how="vertical_relaxed").sort(
        ["as_of_date", "core_bin", "model"]
    )
    history = pl.concat(history_frames, how="vertical_relaxed").sort(
        ["as_of_date", "player_id"]
    )

    if folds.height != len(CUTOFF_MONTH_DAYS):
        raise ValueError("Baseline 2 development did not produce all predeclared folds")

    mean_frozen_log = float(folds.get_column("frozen_baseline1_log_loss").mean())
    mean_b2_log = float(folds.get_column("baseline2_log_loss").mean())
    mean_frozen_brier = float(folds.get_column("frozen_baseline1_brier").mean())
    mean_b2_brier = float(folds.get_column("baseline2_brier").mean())
    log_win_count = int(folds.get_column("baseline2_log_loss_win").sum())
    brier_win_count = int(folds.get_column("baseline2_brier_win").sum())
    coverage_equal = bool(folds.get_column("coverage_equal").all())
    calibration_converged = bool(folds.get_column("all_calibration_fits_converged").all())

    mean_frozen_intercept = float(
        folds.get_column("frozen_baseline1_mean_abs_calibration_intercept_error").mean()
    )
    mean_b2_intercept = float(
        folds.get_column("baseline2_mean_abs_calibration_intercept_error").mean()
    )
    mean_frozen_slope = float(
        folds.get_column("frozen_baseline1_mean_abs_calibration_slope_error").mean()
    )
    mean_b2_slope = float(
        folds.get_column("baseline2_mean_abs_calibration_slope_error").mean()
    )
    calibration_intercept_guardrail = (
        mean_b2_intercept <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_frozen_intercept
    )
    calibration_slope_guardrail = (
        mean_b2_slope <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_frozen_slope
    )

    level_diagnostics, level_failures = _level_guardrail(strata)
    promotion_checks = {
        "lower_equal_fold_mean_log_loss": mean_b2_log < mean_frozen_log,
        "no_worse_equal_fold_mean_brier": mean_b2_brier <= mean_frozen_brier + NUMERIC_TOLERANCE,
        "log_loss_wins_at_least_2_of_3": log_win_count >= 2,
        "identical_scored_coverage": coverage_equal,
        "no_meaningful_non_mlb_consistent_reversal": not level_failures,
        "all_component_calibration_fits_converged": calibration_converged,
        "calibration_intercept_within_25pct_guardrail": calibration_intercept_guardrail,
        "calibration_slope_within_25pct_guardrail": calibration_slope_guardrail,
    }
    eligible_for_confirmation = all(promotion_checks.values())

    output_tables = {
        "fold_metrics": _write(folds, args.output_dir, "baseline2_development_fold_metrics"),
        "component_metrics": _write(
            components, args.output_dir, "baseline2_development_component_metrics"
        ),
        "stratum_metrics": _write(
            strata, args.output_dir, "baseline2_development_stratum_metrics"
        ),
        "calibration_coefficients": _write(
            calibration, args.output_dir, "baseline2_development_calibration_coefficients"
        ),
        "history_evidence": _write(
            history, args.output_dir, "baseline2_development_history_evidence"
        ),
    }

    report = {
        "report_schema_version": "0.1",
        "development_season": DEVELOPMENT_SEASON,
        "history_seasons": list(HISTORY_SEASONS),
        "cutoffs": [f"{DEVELOPMENT_SEASON}-{value}" for value in CUTOFF_MONTH_DAYS],
        "comparator": {
            "name": "hl180_ps100_fitted",
            "scoring_label": "frozen_baseline1",
            "season_to_date_only": True,
            "half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
            "prior_strength_core_events": FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
            "translation": "fitted_training_only_current_season",
        },
        "challenger": {
            "method": BASELINE2_METHOD,
            "lookback_days": BASELINE2_LOOKBACK_DAYS,
            "half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
            "prior_strength_core_events": FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
            "same_frozen_baseline0_prior": True,
            "same_fold_translation_as_comparator": True,
        },
        "proper_score_summary": {
            "frozen_baseline1_equal_fold_mean_log_loss": mean_frozen_log,
            "baseline2_equal_fold_mean_log_loss": mean_b2_log,
            "baseline2_minus_frozen_equal_fold_mean_log_loss": mean_b2_log - mean_frozen_log,
            "frozen_baseline1_equal_fold_mean_brier": mean_frozen_brier,
            "baseline2_equal_fold_mean_brier": mean_b2_brier,
            "baseline2_minus_frozen_equal_fold_mean_brier": mean_b2_brier - mean_frozen_brier,
            "baseline2_log_loss_fold_wins": log_win_count,
            "baseline2_brier_fold_wins": brier_win_count,
        },
        "calibration_summary": {
            "frozen_baseline1_mean_abs_intercept_error": mean_frozen_intercept,
            "baseline2_mean_abs_intercept_error": mean_b2_intercept,
            "frozen_baseline1_mean_abs_slope_error": mean_frozen_slope,
            "baseline2_mean_abs_slope_error": mean_b2_slope,
            "relative_worsening_limit": CALIBRATION_MAX_RELATIVE_WORSENING,
            "all_fits_converged": calibration_converged,
        },
        "level_guardrail": {
            "meaningful_support_future_core_events": MEANINGFUL_LEVEL_FUTURE_CORE_EVENTS,
            "diagnostics": level_diagnostics,
            "failures": level_failures,
        },
        "promotion_checks": promotion_checks,
        "eligible_for_2023_confirmation": eligible_for_confirmation,
        "history_evidence_summary": {
            "mean_share_players_with_prior_season_effective_evidence": float(
                folds.get_column("share_players_with_prior_season_effective_evidence").mean()
            ),
            "mean_additional_effective_core_events": float(
                folds.get_column("mean_additional_effective_core_events").mean()
            ),
        },
        "source_metrics": {
            "2021": metrics_2021,
            "2022": metrics_2022,
            "combined_history": history_metrics,
        },
        "inputs": {
            "2021": inputs_2021,
            "2022": inputs_2022,
        },
        "chadwick_archive": archive_metadata,
        "translation_support": translation_support,
        "output_tables": output_tables,
        "holdout_boundary": (
            "No 2023 evidence or Baseline 2 score is evaluated by this development script. "
            "If eligible_for_2023_confirmation is false, do not tune a nearby history window on 2023."
        ),
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
