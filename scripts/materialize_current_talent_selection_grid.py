#!/usr/bin/env python3
"""Evaluate the predeclared simple Current Talent grid on one development season.

This script intentionally evaluates only the candidate dimensions frozen in
`docs/current-talent-baseline-selection-plan.md`. It reuses cutoff-level evidence,
translation, age, and target work so prior-strength variants do not redundantly
rebuild the data foundation.
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
from universal_baseball.current_talent_ablation import zero_translation_offsets
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
from universal_baseball.current_talent_validation_dataset import (
    build_validation_snapshot_dataset,
)


HALF_LIVES = (45.0, 90.0, 180.0)
PRIOR_STRENGTHS = (50.0, 100.0, 200.0)
TRANSLATION_VARIANTS = ("fitted_translation", "zero_offset_translation")
CUTOFF_MONTH_DAYS = ("07-15", "08-01", "09-01")
AGE_BAND_WIDTH_YEARS = 2.0
MIN_AGE_LEVEL_PEERS = 12
MIN_CORE_EVENTS_PER_STINT = 20
MAX_GAP_DAYS = 365


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--mlb-input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True, choices=(2021, 2022))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-selection-grid"),
    )
    return parser.parse_args()


def _candidate_id(half_life: float, prior_strength: float, translation_variant: str) -> str:
    translation_token = "fitted" if translation_variant == "fitted_translation" else "zero"
    return f"hl{int(half_life)}_ps{int(prior_strength)}_{translation_token}"


def _metric_lookup(frame: pl.DataFrame) -> dict[str, dict[str, object]]:
    return {str(row["model"]): dict(row) for row in frame.iter_rows(named=True)}


def _mean_component_metric(frame: pl.DataFrame, column: str) -> float:
    if frame.is_empty():
        raise ValueError(f"cannot summarize empty calibration frame for {column}")
    return float(frame.get_column(column).mean())


def _write(frame: pl.DataFrame, output_dir: Path, name: str) -> None:
    frame.write_parquet(output_dir / f"{name}.parquet", compression="zstd")
    frame.write_csv(output_dir / f"{name}.csv")


def main() -> int:
    args = _parse_args()
    season = int(args.season)
    summary, profile, combination_metrics, inputs = _load_universal_evidence(
        args.input_root,
        args.mlb_input_root,
        season,
    )

    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    fold_rows: list[dict[str, object]] = []
    component_frames: list[pl.DataFrame] = []
    stratum_frames: list[pl.DataFrame] = []
    fold_support: list[dict[str, object]] = []

    for month_day in CUTOFF_MONTH_DAYS:
        cutoff = date.fromisoformat(f"{season}-{month_day}")
        translation_evidence = build_training_environment_transition_evidence(
            summary,
            profile,
            training_end=cutoff,
            min_core_events_per_stint=MIN_CORE_EVENTS_PER_STINT,
            max_gap_days=MAX_GAP_DAYS,
        )
        fit = fit_level_clr_translation(
            translation_evidence.pair_summary,
            translation_evidence.pair_profile,
            anchor_level="MLB",
        )
        offsets_by_variant = {
            "fitted_translation": fit.offsets,
            "zero_offset_translation": zero_translation_offsets(fit.offsets),
        }
        fold_support.append(
            {
                "season": season,
                "as_of_date": cutoff.isoformat(),
                **translation_evidence.metrics,
                **{f"translation_fit_{key}": value for key, value in fit.metrics.items()},
            }
        )

        # Predictor membership is identical for these season-to-date half-life
        # windows. Derive age once from the first window and verify membership
        # remains fixed for the other half-lives.
        ages: pl.DataFrame | None = None
        expected_predictor_ids: list[int] | None = None
        expected_coverage: tuple[int, int, int] | None = None

        for half_life in HALF_LIVES:
            window = EvidenceWindow(
                label=f"season_to_date_half_life_{half_life:g}d",
                lookback_days=None,
                half_life_days=half_life,
            )
            validation = build_validation_snapshot_dataset(
                summary,
                profile,
                cutoff=cutoff,
                window=window,
            )
            predictor_ids = sorted(
                int(value)
                for value in validation.predictor_summary.get_column("player_id").to_list()
            )
            if expected_predictor_ids is None:
                expected_predictor_ids = predictor_ids
                ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
                missing_age = ages.filter(pl.col("age_source_status") != "exact_birth_date")
                if not missing_age.is_empty():
                    raise ValueError(
                        f"selection grid requires exact age for all predictor players at {cutoff}"
                    )
            elif predictor_ids != expected_predictor_ids:
                raise ValueError(
                    f"selection-grid predictor membership changed by half-life at {cutoff}"
                )
            assert ages is not None

            baseline_context = (
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
            if baseline_context.filter(pl.col("age_years").is_null()).height:
                raise ValueError(f"selection-grid context has missing age at {cutoff}")

            for translation_variant in TRANSLATION_VARIANTS:
                offsets = offsets_by_variant[translation_variant]
                translated = build_translated_player_evidence(
                    summary,
                    profile,
                    offsets,
                    cutoff=cutoff,
                    window=window,
                )
                prior = fit_leave_one_out_age_level_prior(
                    translated,
                    baseline_context,
                    age_band_width_years=AGE_BAND_WIDTH_YEARS,
                    min_age_level_peers=MIN_AGE_LEVEL_PEERS,
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

                for prior_strength in PRIOR_STRENGTHS:
                    candidate_id = _candidate_id(
                        half_life,
                        prior_strength,
                        translation_variant,
                    )
                    baselines = build_baseline_profiles(
                        translated,
                        prior,
                        prior_strength_core_events=prior_strength,
                    )
                    projected = project_latent_profiles_to_target_environment(
                        baselines.profile,
                        validation.target_summary,
                        offsets,
                    )
                    scores = score_current_talent_profiles(
                        projected,
                        validation.target_profile,
                        scoring_context=scoring_context,
                    )
                    aggregate = _metric_lookup(scores.aggregate_metrics)
                    if set(aggregate) != {"baseline0", "baseline1"}:
                        raise ValueError(f"candidate {candidate_id} missing baseline score rows")

                    coefficients = build_component_calibration_coefficients(
                        projected,
                        validation.target_profile,
                    )
                    nonconverged = coefficients.filter(~pl.col("converged"))
                    if not nonconverged.is_empty():
                        raise ValueError(
                            f"candidate {candidate_id} has nonconverged calibration coefficients"
                        )
                    reliability = build_calibration_summary(scores.component_calibration)

                    b0_coeff = coefficients.filter(pl.col("model") == "baseline0")
                    b1_coeff = coefficients.filter(pl.col("model") == "baseline1")
                    b0_rel = reliability.filter(pl.col("model") == "baseline0")
                    b1_rel = reliability.filter(pl.col("model") == "baseline1")

                    b0 = aggregate["baseline0"]
                    b1 = aggregate["baseline1"]
                    coverage = (
                        int(scores.metrics["scored_player_count"]),
                        int(scores.metrics["scored_target_environment_count"]),
                        int(b1["future_core_events"]),
                    )
                    if expected_coverage is None:
                        expected_coverage = coverage
                    elif coverage != expected_coverage:
                        raise ValueError(
                            "selection-grid score coverage changed across candidates: "
                            f"cutoff={cutoff}, candidate={candidate_id}, observed={coverage}, "
                            f"expected={expected_coverage}"
                        )

                    fold_rows.append(
                        {
                            "candidate_id": candidate_id,
                            "season": season,
                            "as_of_date": cutoff,
                            "half_life_days": half_life,
                            "prior_strength_core_events": prior_strength,
                            "translation_variant": translation_variant,
                            "scored_player_count": coverage[0],
                            "scored_target_environment_count": coverage[1],
                            "future_core_events": coverage[2],
                            "baseline0_log_loss": float(b0["event_weighted_log_loss"]),
                            "baseline1_log_loss": float(b1["event_weighted_log_loss"]),
                            "baseline1_minus_baseline0_log_loss": float(
                                b1["event_weighted_log_loss"] - b0["event_weighted_log_loss"]
                            ),
                            "baseline0_brier": float(b0["event_weighted_multinomial_brier"]),
                            "baseline1_brier": float(b1["event_weighted_multinomial_brier"]),
                            "baseline1_minus_baseline0_brier": float(
                                b1["event_weighted_multinomial_brier"]
                                - b0["event_weighted_multinomial_brier"]
                            ),
                            "baseline0_mean_abs_calibration_intercept_error": _mean_component_metric(
                                b0_coeff, "absolute_intercept_error"
                            ),
                            "baseline1_mean_abs_calibration_intercept_error": _mean_component_metric(
                                b1_coeff, "absolute_intercept_error"
                            ),
                            "baseline0_mean_abs_calibration_slope_error": _mean_component_metric(
                                b0_coeff, "absolute_slope_error"
                            ),
                            "baseline1_mean_abs_calibration_slope_error": _mean_component_metric(
                                b1_coeff, "absolute_slope_error"
                            ),
                            "baseline0_mean_ece": _mean_component_metric(
                                b0_rel, "event_weighted_expected_calibration_error"
                            ),
                            "baseline1_mean_ece": _mean_component_metric(
                                b1_rel, "event_weighted_expected_calibration_error"
                            ),
                        }
                    )

                    component_scores = build_component_proper_score_contributions(
                        projected,
                        validation.target_profile,
                    )
                    component_frames.append(
                        component_scores.join(
                            coefficients.select(
                                "model",
                                "core_bin",
                                "calibration_intercept",
                                "calibration_slope",
                                "absolute_intercept_error",
                                "absolute_slope_error",
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
                        ).with_columns(
                            pl.lit(candidate_id).alias("candidate_id"),
                            pl.lit(season).cast(pl.Int64).alias("season"),
                            pl.lit(cutoff).alias("as_of_date"),
                            pl.lit(half_life).alias("half_life_days"),
                            pl.lit(prior_strength).alias("prior_strength_core_events"),
                            pl.lit(translation_variant).alias("translation_variant"),
                        )
                    )

                    strata = build_separate_stratified_metrics(
                        scores.environment_scores,
                        scoring_context,
                    )
                    stratum_frames.append(
                        strata.with_columns(
                            pl.lit(candidate_id).alias("candidate_id"),
                            pl.lit(season).cast(pl.Int64).alias("season"),
                            pl.lit(cutoff).alias("as_of_date"),
                            pl.lit(half_life).alias("half_life_days"),
                            pl.lit(prior_strength).alias("prior_strength_core_events"),
                            pl.lit(translation_variant).alias("translation_variant"),
                        )
                    )

    fold_metrics = pl.DataFrame(fold_rows).sort(["as_of_date", "candidate_id"])
    expected_rows = len(CUTOFF_MONTH_DAYS) * len(HALF_LIVES) * len(PRIOR_STRENGTHS) * len(
        TRANSLATION_VARIANTS
    )
    if fold_metrics.height != expected_rows:
        raise ValueError(
            f"selection grid expected {expected_rows} fold-candidate rows, got {fold_metrics.height}"
        )
    components = pl.concat(component_frames, how="vertical_relaxed").sort(
        ["as_of_date", "candidate_id", "model", "core_bin"]
    )
    strata = pl.concat(stratum_frames, how="vertical_relaxed").sort(
        ["as_of_date", "candidate_id", "model", "stratum_type", "stratum_value"]
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write(fold_metrics, args.output_dir, "candidate_fold_metrics")
    _write(components, args.output_dir, "candidate_component_metrics")
    _write(strata, args.output_dir, "candidate_stratum_metrics")
    (args.output_dir / "report.json").write_text(
        json.dumps(
            {
                "report_schema_version": "0.1",
                "season": season,
                "candidate_count": len(HALF_LIVES)
                * len(PRIOR_STRENGTHS)
                * len(TRANSLATION_VARIANTS),
                "fold_count": len(CUTOFF_MONTH_DAYS),
                "candidate_fold_row_count": int(fold_metrics.height),
                "grid": {
                    "half_life_days": list(HALF_LIVES),
                    "prior_strength_core_events": list(PRIOR_STRENGTHS),
                    "translation_variants": list(TRANSLATION_VARIANTS),
                },
                "fixed_settings": {
                    "age_band_width_years": AGE_BAND_WIDTH_YEARS,
                    "min_age_level_peers": MIN_AGE_LEVEL_PEERS,
                    "min_core_events_per_translation_stint": MIN_CORE_EVENTS_PER_STINT,
                    "translation_max_gap_days": MAX_GAP_DAYS,
                },
                "combined_evidence_metrics": combination_metrics,
                "inputs": inputs,
                "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
                "chadwick_archive": archive_metadata,
                "fold_support": fold_support,
                "selection_role": "development_grid_only",
                "does_not_include_2023": True,
            },
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "season": season,
                "candidate_count": len(HALF_LIVES)
                * len(PRIOR_STRENGTHS)
                * len(TRANSLATION_VARIANTS),
                "fold_count": len(CUTOFF_MONTH_DAYS),
                "candidate_fold_row_count": fold_metrics.height,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
