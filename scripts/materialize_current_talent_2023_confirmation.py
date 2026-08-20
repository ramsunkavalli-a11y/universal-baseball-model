#!/usr/bin/env python3
"""Confirm the preselected simple Current Talent candidate on 2023 only.

The selected candidate must come from the persisted 2021–2022 development-grid
checkpoint. This script never enumerates the 18-candidate grid and therefore
cannot reselect using 2023.
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
from universal_baseball.current_talent_calibration import build_component_calibration_coefficients
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
from universal_baseball.current_talent_validation_dataset import build_validation_snapshot_dataset


SEASON = 2023
CUTOFF_MONTH_DAYS = ("07-15", "08-01", "09-01")
REFERENCE = {
    "candidate_id": "hl90_ps100_fitted",
    "half_life_days": 90.0,
    "prior_strength_core_events": 100.0,
    "translation_variant": "fitted_translation",
}
AGE_BAND_WIDTH_YEARS = 2.0
MIN_AGE_LEVEL_PEERS = 12
MIN_CORE_EVENTS_PER_STINT = 20
MAX_GAP_DAYS = 365


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--mlb-input-root", type=Path, required=True)
    parser.add_argument("--selected-candidate", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-2023-confirmation"),
    )
    return parser.parse_args()


def _candidate_spec(raw: dict[str, object]) -> dict[str, object]:
    required = {
        "candidate_id",
        "half_life_days",
        "prior_strength_core_events",
        "translation_variant",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"persisted selected candidate missing fields: {missing}")
    variant = str(raw["translation_variant"])
    if variant not in {"fitted_translation", "zero_offset_translation"}:
        raise ValueError(f"unsupported persisted translation variant: {variant}")
    return {
        "candidate_id": str(raw["candidate_id"]),
        "half_life_days": float(raw["half_life_days"]),
        "prior_strength_core_events": float(raw["prior_strength_core_events"]),
        "translation_variant": variant,
    }


def _write(frame: pl.DataFrame, output_dir: Path, name: str) -> None:
    frame.write_parquet(output_dir / f"{name}.parquet", compression="zstd")
    frame.write_csv(output_dir / f"{name}.csv")


def _metric_lookup(frame: pl.DataFrame) -> dict[str, dict[str, object]]:
    return {str(row["model"]): dict(row) for row in frame.iter_rows(named=True)}


def _candidate_key(spec: dict[str, object]) -> tuple[float, float, str]:
    return (
        float(spec["half_life_days"]),
        float(spec["prior_strength_core_events"]),
        str(spec["translation_variant"]),
    )


def main() -> int:
    args = _parse_args()
    selected_raw = json.loads(args.selected_candidate.read_text(encoding="utf-8"))
    selected = _candidate_spec(selected_raw)
    reference = dict(REFERENCE)

    specs: list[dict[str, object]] = [selected]
    if _candidate_key(selected) != _candidate_key(reference):
        specs.append(reference)

    # Guard against accidentally widening 2023 confirmation into a search.
    if len(specs) > 2:
        raise ValueError("2023 confirmation may evaluate at most selected + reference candidates")

    summary, profile, combination_metrics, inputs = _load_universal_evidence(
        args.input_root,
        args.mlb_input_root,
        SEASON,
    )
    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    fold_rows: list[dict[str, object]] = []
    component_frames: list[pl.DataFrame] = []
    stratum_frames: list[pl.DataFrame] = []

    for month_day in CUTOFF_MONTH_DAYS:
        cutoff = date.fromisoformat(f"{SEASON}-{month_day}")
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

        validation_by_half_life: dict[float, object] = {}
        ages: pl.DataFrame | None = None
        predictor_ids_expected: list[int] | None = None
        expected_coverage: tuple[int, int, int] | None = None

        for spec in specs:
            half_life = float(spec["half_life_days"])
            if half_life not in validation_by_half_life:
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
                validation_by_half_life[half_life] = (validation, window)
                predictor_ids = sorted(
                    int(value)
                    for value in validation.predictor_summary.get_column("player_id").to_list()
                )
                if predictor_ids_expected is None:
                    predictor_ids_expected = predictor_ids
                    ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
                    if ages.filter(pl.col("age_source_status") != "exact_birth_date").height:
                        raise ValueError(f"2023 confirmation requires exact ages at {cutoff}")
                elif predictor_ids != predictor_ids_expected:
                    raise ValueError("2023 confirmation predictor membership changed by half-life")

            validation, window = validation_by_half_life[half_life]
            if ages is None:
                raise RuntimeError("confirmation age surface was not initialized")
            offsets = offsets_by_variant[str(spec["translation_variant"])]
            translated = build_translated_player_evidence(
                summary,
                profile,
                offsets,
                cutoff=cutoff,
                window=window,
            )
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
            prior = fit_leave_one_out_age_level_prior(
                translated,
                baseline_context,
                age_band_width_years=AGE_BAND_WIDTH_YEARS,
                min_age_level_peers=MIN_AGE_LEVEL_PEERS,
            )
            baselines = build_baseline_profiles(
                translated,
                prior,
                prior_strength_core_events=float(spec["prior_strength_core_events"]),
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
            scores = score_current_talent_profiles(
                projected,
                validation.target_profile,
                scoring_context=scoring_context,
            )
            aggregate = _metric_lookup(scores.aggregate_metrics)
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
                    f"2023 confirmation coverage differs across candidates at {cutoff}"
                )

            coefficients = build_component_calibration_coefficients(
                projected,
                validation.target_profile,
            )
            if coefficients.filter(~pl.col("converged")).height:
                raise ValueError("2023 confirmation calibration coefficients failed to converge")
            reliability = build_calibration_summary(scores.component_calibration)
            b1_coeff = coefficients.filter(pl.col("model") == "baseline1")
            b1_rel = reliability.filter(pl.col("model") == "baseline1")

            candidate_id = str(spec["candidate_id"])
            fold_rows.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_role": "selected" if candidate_id == selected["candidate_id"] else "reference",
                    "season": SEASON,
                    "as_of_date": cutoff,
                    "half_life_days": half_life,
                    "prior_strength_core_events": float(spec["prior_strength_core_events"]),
                    "translation_variant": str(spec["translation_variant"]),
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
                    "baseline1_mean_abs_calibration_intercept_error": float(
                        b1_coeff.get_column("absolute_intercept_error").mean()
                    ),
                    "baseline1_mean_abs_calibration_slope_error": float(
                        b1_coeff.get_column("absolute_slope_error").mean()
                    ),
                    "baseline1_mean_ece": float(
                        b1_rel.get_column("event_weighted_expected_calibration_error").mean()
                    ),
                }
            )

            component_frames.append(
                build_component_proper_score_contributions(
                    projected,
                    validation.target_profile,
                ).with_columns(
                    pl.lit(candidate_id).alias("candidate_id"),
                    pl.lit(cutoff).alias("as_of_date"),
                )
            )
            stratum_frames.append(
                build_separate_stratified_metrics(
                    scores.environment_scores,
                    scoring_context,
                ).with_columns(
                    pl.lit(candidate_id).alias("candidate_id"),
                    pl.lit(cutoff).alias("as_of_date"),
                )
            )

    folds = pl.DataFrame(fold_rows).sort(["as_of_date", "candidate_role"])
    expected_rows = 3 * len(specs)
    if folds.height != expected_rows:
        raise ValueError(f"expected {expected_rows} 2023 confirmation rows, got {folds.height}")

    selected_rows = folds.filter(pl.col("candidate_role") == "selected")
    if selected_rows.height != 3:
        raise ValueError("selected candidate must have exactly three 2023 confirmation folds")
    selected_mean_ll = float(selected_rows.get_column("baseline1_log_loss").mean())
    selected_mean_brier = float(selected_rows.get_column("baseline1_brier").mean())
    selected_b0_ll_delta = float(
        selected_rows.get_column("baseline1_minus_baseline0_log_loss").mean()
    )
    selected_b0_brier_delta = float(
        selected_rows.get_column("baseline1_minus_baseline0_brier").mean()
    )

    reference_rows = folds.filter(pl.col("candidate_id") == REFERENCE["candidate_id"])
    if _candidate_key(selected) == _candidate_key(reference):
        reference_rows = selected_rows
    if reference_rows.height != 3:
        raise ValueError("reference candidate must have exactly three 2023 folds")
    reference_mean_ll = float(reference_rows.get_column("baseline1_log_loss").mean())
    reference_mean_brier = float(reference_rows.get_column("baseline1_brier").mean())

    selected_components = pl.concat(component_frames, how="vertical_relaxed").filter(
        pl.col("candidate_id") == selected["candidate_id"]
    )
    selected_strata = pl.concat(stratum_frames, how="vertical_relaxed").filter(
        pl.col("candidate_id") == selected["candidate_id"]
    )
    component_b0 = selected_components.filter(pl.col("model") == "baseline0")
    component_b1 = selected_components.filter(pl.col("model") == "baseline1")
    comp_keys = ["as_of_date", "core_bin"]
    comp_compare = component_b0.select(
        *comp_keys,
        pl.col("multinomial_log_loss_contribution").alias("b0_ll"),
        pl.col("binary_brier_contribution").alias("b0_brier"),
    ).join(
        component_b1.select(
            *comp_keys,
            pl.col("multinomial_log_loss_contribution").alias("b1_ll"),
            pl.col("binary_brier_contribution").alias("b1_brier"),
        ),
        on=comp_keys,
        how="inner",
    )
    stratum_b0 = selected_strata.filter(pl.col("model") == "baseline0")
    stratum_b1 = selected_strata.filter(pl.col("model") == "baseline1")
    stratum_keys = ["as_of_date", "stratum_type", "stratum_value"]
    strata_compare = stratum_b0.select(
        *stratum_keys,
        pl.col("event_weighted_log_loss").alias("b0_ll"),
        pl.col("event_weighted_multinomial_brier").alias("b0_brier"),
    ).join(
        stratum_b1.select(
            *stratum_keys,
            pl.col("event_weighted_log_loss").alias("b1_ll"),
            pl.col("event_weighted_multinomial_brier").alias("b1_brier"),
        ),
        on=stratum_keys,
        how="inner",
    )

    confirmation = {
        "report_schema_version": "0.1",
        "selection_source": str(args.selected_candidate),
        "selected_candidate": selected,
        "reference_candidate": reference,
        "confirmation_season": 2023,
        "confirmation_fold_count": 3,
        "selected_mean_baseline1_log_loss": selected_mean_ll,
        "selected_mean_baseline1_brier": selected_mean_brier,
        "selected_mean_b1_minus_b0_log_loss": selected_b0_ll_delta,
        "selected_mean_b1_minus_b0_brier": selected_b0_brier_delta,
        "selected_b1_log_loss_win_vs_b0_fold_count": int(
            (selected_rows.get_column("baseline1_minus_baseline0_log_loss") < 0).sum()
        ),
        "selected_b1_brier_win_vs_b0_fold_count": int(
            (selected_rows.get_column("baseline1_minus_baseline0_brier") < 0).sum()
        ),
        "reference_mean_baseline1_log_loss": reference_mean_ll,
        "reference_mean_baseline1_brier": reference_mean_brier,
        "selected_minus_reference_mean_log_loss": selected_mean_ll - reference_mean_ll,
        "selected_minus_reference_mean_brier": selected_mean_brier - reference_mean_brier,
        "selected_component_log_loss_win_vs_b0_count": int(
            comp_compare.filter(pl.col("b1_ll") < pl.col("b0_ll")).height
        ),
        "selected_component_brier_win_vs_b0_count": int(
            comp_compare.filter(pl.col("b1_brier") < pl.col("b0_brier")).height
        ),
        "selected_component_comparison_count": int(comp_compare.height),
        "selected_stratum_log_loss_win_vs_b0_count": int(
            strata_compare.filter(pl.col("b1_ll") < pl.col("b0_ll")).height
        ),
        "selected_stratum_brier_win_vs_b0_count": int(
            strata_compare.filter(pl.col("b1_brier") < pl.col("b0_brier")).height
        ),
        "selected_stratum_comparison_count": int(strata_compare.height),
        "selected_mean_abs_calibration_intercept_error": float(
            selected_rows.get_column("baseline1_mean_abs_calibration_intercept_error").mean()
        ),
        "selected_mean_abs_calibration_slope_error": float(
            selected_rows.get_column("baseline1_mean_abs_calibration_slope_error").mean()
        ),
        "selected_mean_ece": float(selected_rows.get_column("baseline1_mean_ece").mean()),
        "proper_score_confirmation": bool(
            selected_b0_ll_delta < 0
            and selected_b0_brier_delta < 0
            and selected_mean_ll <= reference_mean_ll + 1e-15
        ),
        "selection_uses_only_preselected_candidate_on_2023": True,
        "full_grid_evaluated_on_2023": False,
        "combined_evidence_metrics": combination_metrics,
        "inputs": inputs,
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_archive": archive_metadata,
        "interpretation": (
            "Confirmation only. If the preselected development candidate fails, do not reselect "
            "using 2023. Record instability and keep the baseline unfrozen."
        ),
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    _write(folds, args.output_dir, "confirmation_fold_metrics")
    _write(selected_components, args.output_dir, "selected_candidate_component_metrics")
    _write(selected_strata, args.output_dir, "selected_candidate_stratum_metrics")
    (args.output_dir / "report.json").write_text(
        json.dumps(confirmation, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(confirmation, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
