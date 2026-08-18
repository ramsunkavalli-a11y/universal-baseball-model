#!/usr/bin/env python3
"""Run Playing Time / Role v1 rolling-origin 2024 validation and promotion gates.

Caller must establish that the binding 2023 primary gate passed before invoking
this script. The selected form is immutable from 2022. No 2025 data is accessed.
"""

from __future__ import annotations

import argparse
import json
from math import log
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    PT_FORMS,
    build_playing_time_design,
    fit_playing_time_hurdle,
    playing_time_level_tier,
    score_playing_time_hurdle,
)
from universal_baseball.playing_time_selection import pooled_playing_time_metrics
from universal_baseball.storage import write_canonical_parquet


TRAINING_FOLDS = (
    ("projection_2021_to_2022", 1),
    ("projection_2022_to_2023", 2),
)
VALIDATION_2023_FOLD = "projection_2022_to_2023"
VALIDATION_2024_FOLD = "projection_2023_to_2024"
SELECTION_RESULT_PATH = Path("docs/playing-time-v1-selection-result.json")
VALIDATION_2023_RESULT_PATH = Path("docs/playing-time-v1-validation-2023-result.json")
ROW_KEY_MULTIPLIER = 10_000_000


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-artifact-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-validation-2024"),
    )
    return parser.parse_args()


def _fold_file(root: Path, fold: str, filename: str, label: str) -> Path:
    matches = sorted(
        path for path in root.rglob(filename) if path.is_file() and fold in path.parts
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {label} for {fold} named {filename}, found {len(matches)}: {matches}"
        )
    return matches[0]


def _load_fold(root: Path, fold: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    predictors = pl.read_parquet(
        _fold_file(root, fold, "predictors.parquet", "playing-time predictors")
    )
    targets = pl.read_parquet(
        _fold_file(root, fold, "next_year_mlb_pa_targets.parquet", "playing-time targets")
    ).select("player_id", "next_year_mlb_pa")
    return predictors, targets


def _load_binding_state() -> tuple[str, dict[str, object], dict[str, object]]:
    selection = json.loads(SELECTION_RESULT_PATH.read_text(encoding="utf-8"))
    validation_2023 = json.loads(VALIDATION_2023_RESULT_PATH.read_text(encoding="utf-8"))
    form = str(selection.get("selection", {}).get("selected_form"))
    if form not in PT_FORMS or form == PT_FORM_B0:
        raise RuntimeError("2024 playing-time validation requires a frozen non-B0 selected form")
    if not bool(selection.get("selection", {}).get("advances_to_out_of_time_validation")):
        raise RuntimeError("2022 playing-time selection did not authorize OOT validation")
    if validation_2023.get("status") != "scored":
        raise RuntimeError("2023 playing-time validation was not scored")
    if not bool(validation_2023.get("decision", {}).get("2024_validation_authorized")):
        raise RuntimeError("2023 playing-time validation did not authorize 2024")
    return form, selection, validation_2023


def _remap_training_observation(
    design: pl.DataFrame,
    targets: pl.DataFrame,
    *,
    fold_index: int,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    if design.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("playing-time training design violates within-fold player grain")
    if targets.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("playing-time training targets violate within-fold player grain")
    design_ids = set(int(value) for value in design.get_column("player_id").to_list())
    target_ids = set(int(value) for value in targets.get_column("player_id").to_list())
    if design_ids != target_ids:
        raise RuntimeError("playing-time training design/target coverage differs")
    offset = fold_index * ROW_KEY_MULTIPLIER
    remapped_design = design.with_columns(
        (pl.lit(offset, dtype=pl.Int64) + pl.col("player_id").cast(pl.Int64)).alias("player_id")
    )
    remapped_targets = targets.with_columns(
        (pl.lit(offset, dtype=pl.Int64) + pl.col("player_id").cast(pl.Int64)).alias("player_id")
    )
    return remapped_design, remapped_targets


def _fit_rolling(
    root: Path,
    *,
    form: str,
) -> tuple[object, dict[str, object]]:
    design_frames: list[pl.DataFrame] = []
    target_frames: list[pl.DataFrame] = []
    source_players: set[int] = set()
    repeated: dict[int, int] = {}
    fold_counts: dict[str, int] = {}
    for fold, fold_index in TRAINING_FOLDS:
        predictors, targets = _load_fold(root, fold)
        source_ids = [int(value) for value in predictors.get_column("player_id").to_list()]
        for player_id in source_ids:
            repeated[player_id] = repeated.get(player_id, 0) + 1
            source_players.add(player_id)
        design = build_playing_time_design(predictors, form=form)
        remapped_design, remapped_targets = _remap_training_observation(
            design, targets, fold_index=fold_index
        )
        design_frames.append(remapped_design)
        target_frames.append(remapped_targets)
        fold_counts[fold] = int(remapped_design.height)
    combined_design = pl.concat(design_frames, how="vertical_relaxed")
    combined_targets = pl.concat(target_frames, how="vertical_relaxed")
    if combined_design.get_column("player_id").n_unique() != combined_design.height:
        raise RuntimeError("playing-time rolling training observation IDs collide")
    fit = fit_playing_time_hurdle(combined_design, combined_targets, form=form)
    metrics = {
        "training_observation_count": int(combined_design.height),
        "unique_source_player_count": len(source_players),
        "source_players_repeated_across_folds": sum(1 for count in repeated.values() if count > 1),
        "training_fold_row_counts": fold_counts,
        "player_identity_used_as_predictor": False,
    }
    return fit, metrics


def _fit_single_fold(
    root: Path,
    *,
    training_fold: str,
    form: str,
):
    predictors, targets = _load_fold(root, training_fold)
    design = build_playing_time_design(predictors, form=form)
    return fit_playing_time_hurdle(design, targets, form=form)


def _score_fold(root: Path, fold: str, *, fit, form: str) -> tuple[pl.DataFrame, dict[str, object], pl.DataFrame]:
    predictors, targets = _load_fold(root, fold)
    design = build_playing_time_design(predictors, form=form)
    scored, _ = score_playing_time_hurdle(fit, design, targets)
    metrics = pooled_playing_time_metrics(scored)
    tier = predictors.select("player_id", "as_of_level_group").with_columns(
        pl.col("as_of_level_group")
        .map_elements(playing_time_level_tier, return_dtype=pl.String)
        .alias("as_of_level_tier")
    ).select("player_id", "as_of_level_tier")
    return scored, metrics, scored.join(tier, on="player_id", how="left")


def _calibration(scored: pl.DataFrame) -> dict[str, object]:
    p = np.asarray(
        scored.get_column("predicted_any_mlb_pa_probability").to_numpy(), dtype=np.float64
    )
    y = np.asarray(scored.get_column("observed_any_mlb_pa").cast(pl.Int64).to_numpy(), dtype=np.float64)
    p = np.clip(p, 1e-8, 1.0 - 1e-8)
    logit = np.log(p / (1.0 - p))
    exog = sm.add_constant(logit, prepend=True)
    try:
        result = sm.GLM(y, exog, family=sm.families.Binomial()).fit(maxiter=200, disp=0)
        params = np.asarray(result.params, dtype=np.float64)
        converged = bool(getattr(result, "converged", True))
        return {
            "converged": converged,
            "intercept": float(params[0]),
            "slope": float(params[1]),
        }
    except Exception as exc:
        return {
            "converged": False,
            "intercept": None,
            "slope": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def _strata(
    b0: pl.DataFrame,
    candidate: pl.DataFrame,
) -> pl.DataFrame:
    paired = b0.select(
        "player_id",
        "as_of_level_tier",
        "observed_any_mlb_pa",
        pl.col("full_negative_log_likelihood").alias("b0_full_nll"),
    ).join(
        candidate.select(
            "player_id",
            pl.col("full_negative_log_likelihood").alias("candidate_full_nll"),
        ),
        on="player_id",
        how="inner",
    )
    return (
        paired.group_by("as_of_level_tier")
        .agg(
            pl.len().cast(pl.Int64).alias("snapshot_players"),
            pl.col("observed_any_mlb_pa").sum().cast(pl.Int64).alias("positive_players"),
            pl.col("b0_full_nll").mean().alias("baseline0_full_nll"),
            pl.col("candidate_full_nll").mean().alias("candidate_full_nll"),
        )
        .with_columns(
            (pl.col("candidate_full_nll") - pl.col("baseline0_full_nll")).alias(
                "candidate_minus_baseline0_full_nll"
            ),
            (
                (pl.col("snapshot_players") >= 100)
                & (pl.col("positive_players") >= 25)
            ).alias("meaningfully_supported"),
        )
        .sort("as_of_level_tier")
    )


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    selected_form, selection_record, validation_2023_record = _load_binding_state()

    # Reproduce 2023 from the frozen fit for diagnostics and transport checks.
    b0_2023_fit = _fit_single_fold(
        args.selection_artifact_root, training_fold=TRAINING_FOLDS[0][0], form=PT_FORM_B0
    )
    candidate_2023_fit = _fit_single_fold(
        args.selection_artifact_root, training_fold=TRAINING_FOLDS[0][0], form=selected_form
    )
    b0_2023, b0_2023_metrics, b0_2023_tier = _score_fold(
        args.selection_artifact_root, VALIDATION_2023_FOLD, fit=b0_2023_fit, form=PT_FORM_B0
    )
    candidate_2023, candidate_2023_metrics, candidate_2023_tier = _score_fold(
        args.selection_artifact_root,
        VALIDATION_2023_FOLD,
        fit=candidate_2023_fit,
        form=selected_form,
    )
    recorded_2023_delta = float(validation_2023_record["candidate_minus_baseline0_full_nll"])
    reproduced_2023_delta = float(candidate_2023_metrics["mean_full_negative_log_likelihood"]) - float(
        b0_2023_metrics["mean_full_negative_log_likelihood"]
    )
    if abs(recorded_2023_delta - reproduced_2023_delta) > 1e-10:
        raise RuntimeError(
            "playing-time 2023 validation reproduction changed before 2024: "
            f"recorded={recorded_2023_delta}, reproduced={reproduced_2023_delta}"
        )

    b0_2024_fit, b0_training_metrics = _fit_rolling(
        args.selection_artifact_root, form=PT_FORM_B0
    )
    candidate_2024_fit, candidate_training_metrics = _fit_rolling(
        args.selection_artifact_root, form=selected_form
    )
    b0_2024, b0_2024_metrics, b0_2024_tier = _score_fold(
        args.selection_artifact_root, VALIDATION_2024_FOLD, fit=b0_2024_fit, form=PT_FORM_B0
    )
    candidate_2024, candidate_2024_metrics, candidate_2024_tier = _score_fold(
        args.selection_artifact_root,
        VALIDATION_2024_FOLD,
        fit=candidate_2024_fit,
        form=selected_form,
    )
    if b0_2024_metrics["scored_players"] != candidate_2024_metrics["scored_players"]:
        raise RuntimeError("playing-time 2024 B0/candidate scored coverage differs")

    delta_2024 = float(candidate_2024_metrics["mean_full_negative_log_likelihood"]) - float(
        b0_2024_metrics["mean_full_negative_log_likelihood"]
    )
    primary_2024_pass = delta_2024 < 0.0

    participation_mean_candidate = (
        float(candidate_2023_metrics["participation_log_loss"])
        + float(candidate_2024_metrics["participation_log_loss"])
    ) / 2.0
    participation_mean_b0 = (
        float(b0_2023_metrics["participation_log_loss"])
        + float(b0_2024_metrics["participation_log_loss"])
    ) / 2.0
    positive_nll_mean_candidate = (
        float(candidate_2023_metrics["positive_count_negative_log_likelihood"])
        + float(candidate_2024_metrics["positive_count_negative_log_likelihood"])
    ) / 2.0
    positive_nll_mean_b0 = (
        float(b0_2023_metrics["positive_count_negative_log_likelihood"])
        + float(b0_2024_metrics["positive_count_negative_log_likelihood"])
    ) / 2.0
    mae_mean_candidate = (
        float(candidate_2023_metrics["unconditional_mlb_pa_mae"])
        + float(candidate_2024_metrics["unconditional_mlb_pa_mae"])
    ) / 2.0
    mae_mean_b0 = (
        float(b0_2023_metrics["unconditional_mlb_pa_mae"])
        + float(b0_2024_metrics["unconditional_mlb_pa_mae"])
    ) / 2.0

    b0_calibration_2023 = _calibration(b0_2023)
    candidate_calibration_2023 = _calibration(candidate_2023)
    b0_calibration_2024 = _calibration(b0_2024)
    candidate_calibration_2024 = _calibration(candidate_2024)
    calibration_converged = all(
        bool(row["converged"])
        for row in (
            b0_calibration_2023,
            candidate_calibration_2023,
            b0_calibration_2024,
            candidate_calibration_2024,
        )
    )

    strata_2023 = _strata(b0_2023_tier, candidate_2023_tier).with_columns(
        pl.lit(2023).cast(pl.Int64).alias("target_year")
    )
    strata_2024 = _strata(b0_2024_tier, candidate_2024_tier).with_columns(
        pl.lit(2024).cast(pl.Int64).alias("target_year")
    )
    supported_2023 = {
        str(row["as_of_level_tier"]): float(row["candidate_minus_baseline0_full_nll"])
        for row in strata_2023.filter(pl.col("meaningfully_supported")).iter_rows(named=True)
    }
    supported_2024 = {
        str(row["as_of_level_tier"]): float(row["candidate_minus_baseline0_full_nll"])
        for row in strata_2024.filter(pl.col("meaningfully_supported")).iter_rows(named=True)
    }
    repeated_level_failures = sorted(
        tier
        for tier in set(supported_2023) & set(supported_2024)
        if supported_2023[tier] > 0.02 and supported_2024[tier] > 0.02
    )

    gates = {
        "2023_full_nll_lower": recorded_2023_delta < 0.0,
        "2024_full_nll_lower": primary_2024_pass,
        "equal_fold_participation_log_loss_no_worse": participation_mean_candidate
        <= participation_mean_b0,
        "equal_fold_positive_count_nll_no_worse": positive_nll_mean_candidate
        <= positive_nll_mean_b0,
        "equal_fold_unconditional_pa_mae_within_2pct": mae_mean_candidate
        <= mae_mean_b0 * 1.02,
        "coverage_identical": bool(
            b0_2023_metrics["scored_players"] == candidate_2023_metrics["scored_players"]
            and b0_2024_metrics["scored_players"] == candidate_2024_metrics["scored_players"]
        ),
        "participation_calibration_fits_converged": calibration_converged,
        "no_repeated_supported_level_reversal": not repeated_level_failures,
        "2025_accessed": False,
    }
    development_promotion_passed = all(
        value for key, value in gates.items() if key != "2025_accessed"
    ) and not gates["2025_accessed"]

    storage = {
        "baseline0_2024_scored": write_canonical_parquet(
            b0_2024,
            table_root / "baseline0_2024_scored.parquet",
            table_name="playing_time_v1_baseline0_2024_scored",
        ).as_record(),
        "candidate_2024_scored": write_canonical_parquet(
            candidate_2024,
            table_root / "candidate_2024_scored.parquet",
            table_name="playing_time_v1_candidate_2024_scored",
        ).as_record(),
        "strata_2023": write_canonical_parquet(
            strata_2023,
            table_root / "strata_2023.parquet",
            table_name="playing_time_v1_2023_level_strata",
        ).as_record(),
        "strata_2024": write_canonical_parquet(
            strata_2024,
            table_root / "strata_2024.parquet",
            table_name="playing_time_v1_2024_level_strata",
        ).as_record(),
        "baseline0_2024_coefficients": write_canonical_parquet(
            b0_2024_fit.coefficient_frame(),
            table_root / "baseline0_2024_coefficients.parquet",
            table_name="playing_time_v1_baseline0_2024_coefficients",
        ).as_record(),
        "candidate_2024_coefficients": write_canonical_parquet(
            candidate_2024_fit.coefficient_frame(),
            table_root / "candidate_2024_coefficients.parquet",
            table_name="playing_time_v1_candidate_2024_coefficients",
        ).as_record(),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_out_of_time_validation_2024",
        "status": "scored",
        "selected_form": selected_form,
        "selection_source_run": selection_record.get("source_run_id"),
        "validation_target_year": 2024,
        "training_target_years": [2022, 2023],
        "training_observation_metrics": {
            "baseline0": b0_training_metrics,
            "candidate": candidate_training_metrics,
        },
        "validation_2023_reproduction_delta": reproduced_2023_delta,
        "baseline0_2023_metrics": b0_2023_metrics,
        "candidate_2023_metrics": candidate_2023_metrics,
        "baseline0_2024_metrics": b0_2024_metrics,
        "candidate_2024_metrics": candidate_2024_metrics,
        "candidate_minus_baseline0_full_nll_2024": delta_2024,
        "equal_fold_means": {
            "baseline0_participation_log_loss": participation_mean_b0,
            "candidate_participation_log_loss": participation_mean_candidate,
            "baseline0_positive_count_nll": positive_nll_mean_b0,
            "candidate_positive_count_nll": positive_nll_mean_candidate,
            "baseline0_unconditional_pa_mae": mae_mean_b0,
            "candidate_unconditional_pa_mae": mae_mean_candidate,
        },
        "calibration": {
            "baseline0_2023": b0_calibration_2023,
            "candidate_2023": candidate_calibration_2023,
            "baseline0_2024": b0_calibration_2024,
            "candidate_2024": candidate_calibration_2024,
        },
        "repeated_supported_level_failures": repeated_level_failures,
        "promotion_gates": gates,
        "decision": {
            "development_promotion_passed": development_promotion_passed,
            "2025_confirmation_authorized": development_promotion_passed,
            "retain_baseline0_if_failed": not development_promotion_passed,
        },
        "storage": storage,
        "boundary": {
            "form_reselected_on_2024": False,
            "player_identity_used_as_predictor": False,
            "future_team_used": False,
            "future_level_used": False,
            "2025_accessed": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 — 2024 out-of-time validation",
        "",
        f"- Selected form: {selected_form}",
        f"- Candidate full NLL: {candidate_2024_metrics['mean_full_negative_log_likelihood']:.9f}",
        f"- Level-only B0 full NLL: {b0_2024_metrics['mean_full_negative_log_likelihood']:.9f}",
        f"- Delta full NLL: {delta_2024:+.9f}",
        f"- Development promotion passed: {development_promotion_passed}",
        f"- 2025 confirmation authorized: {development_promotion_passed}",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
