#!/usr/bin/env python3
"""Confirm the fixed Current Talent Baseline 2 challenger on held-out 2023.

This script is intentionally unable to search Baseline 2 hyperparameters. It
requires the persisted 2022 development result and evaluates exactly one fixed
multi-season challenger against the frozen season-to-date Baseline 1 comparator.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import polars as pl

from materialize_current_talent_baseline_validation import _load_universal_evidence
from materialize_current_talent_baseline2_development import (
    AGE_BAND_WIDTH_YEARS,
    CALIBRATION_MAX_RELATIVE_WORSENING,
    MAX_GAP_DAYS,
    MEANINGFUL_LEVEL_FUTURE_CORE_EVENTS,
    MIN_AGE_LEVEL_PEERS,
    MIN_CORE_EVENTS_PER_STINT,
    NUMERIC_TOLERANCE,
    _coverage,
    _level_guardrail,
    _mean_model_metric,
    _model_rows,
    _relabel_models,
    _write,
)
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


CONFIRMATION_SEASON = 2023
HISTORY_SEASONS = (2021, 2022, 2023)
CUTOFF_MONTH_DAYS = ("07-15", "08-01", "09-01")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for season in HISTORY_SEASONS:
        parser.add_argument(f"--milb-input-root-{season}", type=Path, required=True)
        parser.add_argument(f"--mlb-input-root-{season}", type=Path, required=True)
    parser.add_argument("--development-result", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-baseline2-confirmation"),
    )
    return parser.parse_args()


def _require_frozen_development_result(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text())
    if payload.get("eligible_for_2023_confirmation") is not True:
        raise ValueError("Baseline 2 confirmation requires a passed development gate")
    challenger = payload.get("baseline2")
    if not isinstance(challenger, dict):
        raise ValueError("development result lacks Baseline 2 definition")
    expected = {
        "method": BASELINE2_METHOD,
        "lookback_days": BASELINE2_LOOKBACK_DAYS,
        "half_life_days": FROZEN_BASELINE2_HALF_LIFE_DAYS,
        "prior_strength_core_events": FROZEN_BASELINE2_PRIOR_STRENGTH_CORE_EVENTS,
        "same_frozen_baseline0_prior": True,
        "same_fold_translation_as_comparator": True,
        "only_intended_change_vs_frozen_b1": "player_specific_history_depth",
    }
    observed = {key: challenger.get(key) for key in expected}
    if observed != expected:
        raise ValueError(
            "persisted Baseline 2 development candidate does not match fixed confirmation spec: "
            f"observed={observed}, expected={expected}"
        )
    return payload


def _component_breadth(frame: pl.DataFrame) -> dict[str, object]:
    keys = ["as_of_date", "core_bin"]
    frozen = frame.filter(pl.col("model") == "frozen_baseline1").select(
        *keys,
        pl.col("multinomial_log_loss_contribution").alias("frozen_log"),
        pl.col("binary_brier_contribution").alias("frozen_brier"),
    )
    b2 = frame.filter(pl.col("model") == "baseline2").select(
        *keys,
        pl.col("multinomial_log_loss_contribution").alias("b2_log"),
        pl.col("binary_brier_contribution").alias("b2_brier"),
    )
    paired = frozen.join(b2, on=keys, how="inner")
    if paired.height != len(CUTOFF_MONTH_DAYS) * 12:
        raise ValueError("confirmation component comparison lacks complete paired coverage")
    paired = paired.with_columns(
        (pl.col("b2_log") - pl.col("frozen_log")).alias("log_delta"),
        (pl.col("b2_brier") - pl.col("frozen_brier")).alias("brier_delta"),
    )
    persistent = (
        paired.group_by("core_bin")
        .agg(
            (pl.col("log_delta") > 0).sum().alias("log_loss_fold_losses"),
            (pl.col("brier_delta") > 0).sum().alias("brier_fold_losses"),
        )
        .with_columns(
            (
                (pl.col("log_loss_fold_losses") == len(CUTOFF_MONTH_DAYS))
                & (pl.col("brier_fold_losses") == len(CUTOFF_MONTH_DAYS))
            ).alias("worse_on_both_all_folds")
        )
    )
    return {
        "comparison_count": int(paired.height),
        "log_loss_win_count": int(paired.filter(pl.col("log_delta") < 0).height),
        "brier_win_count": int(paired.filter(pl.col("brier_delta") < 0).height),
        "persistent_both_score_loser_count": int(
            persistent.filter(pl.col("worse_on_both_all_folds")).height
        ),
        "persistent_both_score_losers": persistent.filter(
            pl.col("worse_on_both_all_folds")
        ).get_column("core_bin").to_list(),
    }


def main() -> int:
    args = _parse_args()
    development_result = _require_frozen_development_result(args.development_result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    season_data: dict[int, tuple[pl.DataFrame, pl.DataFrame, dict[str, object], list[dict[str, str]]]] = {}
    for season in HISTORY_SEASONS:
        season_data[season] = _load_universal_evidence(
            getattr(args, f"milb_input_root_{season}"),
            getattr(args, f"mlb_input_root_{season}"),
            season,
        )

    current_summary, current_profile, _, _ = season_data[CONFIRMATION_SEASON]
    history_summary, history_profile, history_metrics = combine_universal_player_game_evidence(
        [season_data[season][0] for season in HISTORY_SEASONS],
        [season_data[season][1] for season in HISTORY_SEASONS],
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
        cutoff = date.fromisoformat(f"{CONFIRMATION_SEASON}-{month_day}")
        transition_evidence = build_training_environment_transition_evidence(
            current_summary,
            current_profile,
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
            current_summary,
            current_profile,
            cutoff=cutoff,
            window=frozen_window,
        )
        predictor_ids = sorted(
            int(value)
            for value in validation.predictor_summary.get_column("player_id").to_list()
        )
        ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
        if not ages.filter(pl.col("age_source_status") != "exact_birth_date").is_empty():
            raise ValueError(f"Baseline 2 confirmation requires exact age at {cutoff}")

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
            raise ValueError(f"Baseline 2 confirmation context has missing age at {cutoff}")

        frozen_translated = build_translated_player_evidence(
            current_summary,
            current_profile,
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
        if baseline2.profile.get_column("player_id").n_unique() != frozen_model_player_count:
            raise ValueError(f"Baseline 2 confirmation model coverage differs at {cutoff}")

        evidence_comparison = (
            frozen_translated.select(
                "player_id",
                pl.col("effective_core_events").alias("frozen_b1_effective_core_events"),
            )
            .unique()
            .join(
                baseline2.profile.select(
                    "player_id", "baseline2_effective_core_events"
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
            raise ValueError(f"Baseline 2 confirmation evidence coverage differs at {cutoff}")
        history_frames.append(evidence_comparison)

        projected = project_latent_profiles_to_target_environment(
            paired_profile,
            validation.target_summary,
            translation_fit.offsets,
        )
        scoring_context = (
            validation.scoring_rows.join(
                ages.select("player_id", "age_years"), on="player_id", how="left"
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
            raise ValueError(f"Baseline 2 confirmation missing paired rows at {cutoff}")

        coverage = _coverage(environment_scores)
        coverage_equal = (
            set(coverage) == {"frozen_baseline1", "baseline2"}
            and coverage["frozen_baseline1"] == coverage["baseline2"]
        )

        coefficients = _relabel_models(
            build_component_calibration_coefficients(projected, validation.target_profile)
        ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        reliability = _relabel_models(build_calibration_summary(scores.component_calibration))
        calibration_frames.append(coefficients)

        component_frames.append(
            _relabel_models(
                build_component_proper_score_contributions(projected, validation.target_profile)
            )
            .join(
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
            )
            .join(
                reliability.select(
                    "model", "core_bin", "event_weighted_expected_calibration_error"
                ),
                on=["model", "core_bin"],
                how="inner",
            )
            .with_columns(pl.lit(cutoff).alias("as_of_date"))
        )
        stratum_frames.append(
            _relabel_models(
                build_separate_stratified_metrics(environment_scores, scoring_context)
            ).with_columns(pl.lit(cutoff).alias("as_of_date"))
        )

        frozen = by_model["frozen_baseline1"]
        challenger = by_model["baseline2"]
        prior_players = evidence_comparison.filter(pl.col("has_prior_season_effective_evidence"))
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
                "future_core_events": coverage.get("baseline2", (0, 0, 0))[2],
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
                "all_calibration_fits_converged": bool(coefficients.get_column("converged").all()),
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
    history = pl.concat(history_frames, how="vertical_relaxed").sort(["as_of_date", "player_id"])

    mean_frozen_log = float(folds.get_column("frozen_baseline1_log_loss").mean())
    mean_b2_log = float(folds.get_column("baseline2_log_loss").mean())
    mean_frozen_brier = float(folds.get_column("frozen_baseline1_brier").mean())
    mean_b2_brier = float(folds.get_column("baseline2_brier").mean())
    mean_frozen_intercept = float(
        folds.get_column("frozen_baseline1_mean_abs_calibration_intercept_error").mean()
    )
    mean_b2_intercept = float(
        folds.get_column("baseline2_mean_abs_calibration_intercept_error").mean()
    )
    mean_frozen_slope = float(
        folds.get_column("frozen_baseline1_mean_abs_calibration_slope_error").mean()
    )
    mean_b2_slope = float(folds.get_column("baseline2_mean_abs_calibration_slope_error").mean())

    level_diagnostics, level_failures = _level_guardrail(strata)
    component_breadth = _component_breadth(components)
    hard_checks = {
        "lower_equal_fold_mean_log_loss": mean_b2_log < mean_frozen_log,
        "no_worse_equal_fold_mean_brier": mean_b2_brier <= mean_frozen_brier + NUMERIC_TOLERANCE,
        "identical_scored_coverage": bool(folds.get_column("coverage_equal").all()),
        "no_meaningful_non_mlb_consistent_reversal": not level_failures,
        "all_component_calibration_fits_converged": bool(
            folds.get_column("all_calibration_fits_converged").all()
        ),
        "calibration_intercept_within_25pct_guardrail": (
            mean_b2_intercept <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_frozen_intercept
        ),
        "calibration_slope_within_25pct_guardrail": (
            mean_b2_slope <= CALIBRATION_MAX_RELATIVE_WORSENING * mean_frozen_slope
        ),
    }
    confirmed_under_hard_checks = all(hard_checks.values())

    output_tables = {
        "fold_metrics": _write(folds, args.output_dir, "baseline2_confirmation_fold_metrics"),
        "component_metrics": _write(components, args.output_dir, "baseline2_confirmation_component_metrics"),
        "stratum_metrics": _write(strata, args.output_dir, "baseline2_confirmation_stratum_metrics"),
        "calibration_coefficients": _write(
            calibration, args.output_dir, "baseline2_confirmation_calibration_coefficients"
        ),
        "history_evidence": _write(history, args.output_dir, "baseline2_confirmation_history_evidence"),
    }

    report = {
        "report_schema_version": "0.1",
        "confirmation_season": CONFIRMATION_SEASON,
        "history_seasons": list(HISTORY_SEASONS),
        "cutoffs": [f"{CONFIRMATION_SEASON}-{value}" for value in CUTOFF_MONTH_DAYS],
        "development_result": development_result,
        "full_candidate_search_on_2023": False,
        "fixed_challenger_only": True,
        "proper_score_summary": {
            "frozen_baseline1_equal_fold_mean_log_loss": mean_frozen_log,
            "baseline2_equal_fold_mean_log_loss": mean_b2_log,
            "baseline2_minus_frozen_equal_fold_mean_log_loss": mean_b2_log - mean_frozen_log,
            "frozen_baseline1_equal_fold_mean_brier": mean_frozen_brier,
            "baseline2_equal_fold_mean_brier": mean_b2_brier,
            "baseline2_minus_frozen_equal_fold_mean_brier": mean_b2_brier - mean_frozen_brier,
            "baseline2_log_loss_fold_wins": int(folds.get_column("baseline2_log_loss_win").sum()),
            "baseline2_brier_fold_wins": int(folds.get_column("baseline2_brier_win").sum()),
        },
        "calibration_summary": {
            "frozen_baseline1_mean_abs_intercept_error": mean_frozen_intercept,
            "baseline2_mean_abs_intercept_error": mean_b2_intercept,
            "frozen_baseline1_mean_abs_slope_error": mean_frozen_slope,
            "baseline2_mean_abs_slope_error": mean_b2_slope,
            "frozen_baseline1_mean_ece": float(folds.get_column("frozen_baseline1_mean_ece").mean()),
            "baseline2_mean_ece": float(folds.get_column("baseline2_mean_ece").mean()),
        },
        "component_breadth": component_breadth,
        "level_guardrail": {
            "meaningful_support_future_core_events": MEANINGFUL_LEVEL_FUTURE_CORE_EVENTS,
            "diagnostics": level_diagnostics,
            "failures": level_failures,
        },
        "confirmation_hard_checks": hard_checks,
        "confirmed_under_predeclared_hard_checks": confirmed_under_hard_checks,
        "history_evidence_summary": {
            "mean_share_players_with_prior_season_effective_evidence": float(
                folds.get_column("share_players_with_prior_season_effective_evidence").mean()
            ),
            "mean_additional_effective_core_events": float(
                folds.get_column("mean_additional_effective_core_events").mean()
            ),
        },
        "combined_history_metrics": history_metrics,
        "season_source_metrics": {
            str(season): season_data[season][2] for season in HISTORY_SEASONS
        },
        "inputs": {str(season): season_data[season][3] for season in HISTORY_SEASONS},
        "chadwick_archive": archive_metadata,
        "translation_support": translation_support,
        "output_tables": output_tables,
        "decision_boundary": (
            "No Baseline 2 parameters may be changed in response to this 2023 result. "
            "If confirmation fails, retain the frozen Baseline 1 results-only baseline."
        ),
    }
    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
