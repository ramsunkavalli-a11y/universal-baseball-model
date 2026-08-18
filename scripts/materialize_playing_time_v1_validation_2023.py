#!/usr/bin/env python3
"""Run Playing Time / Role v1 out-of-time validation fold 1 on 2023 only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    PT_FORMS,
    build_playing_time_design,
    fit_playing_time_hurdle,
    score_playing_time_hurdle,
)
from universal_baseball.playing_time_selection import pooled_playing_time_metrics
from universal_baseball.storage import write_canonical_parquet


TRAINING_FOLD = "projection_2021_to_2022"
VALIDATION_FOLD = "projection_2022_to_2023"
SELECTION_RESULT_PATH = Path("docs/playing-time-v1-selection-result.json")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-artifact-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-validation-2023"),
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


def _load_selection() -> tuple[str, bool, dict[str, object]]:
    result = json.loads(SELECTION_RESULT_PATH.read_text(encoding="utf-8"))
    if result.get("gate") != "playing_time_v1_2022_candidate_selection":
        raise RuntimeError("unexpected playing-time selection result gate")
    selection = result.get("selection", {})
    form = str(selection.get("selected_form"))
    if form not in PT_FORMS:
        raise RuntimeError(f"playing-time selection contains unsupported form: {form}")
    advances = bool(selection.get("advances_to_out_of_time_validation"))
    if bool(selection.get("baseline0_selected")) != (form == PT_FORM_B0):
        raise RuntimeError("playing-time selection B0 flags are inconsistent")
    return form, advances, result


def _load_fold(root: Path, fold: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    predictors = pl.read_parquet(
        _fold_file(root, fold, "predictors.parquet", "playing-time predictors")
    )
    targets = pl.read_parquet(
        _fold_file(root, fold, "next_year_mlb_pa_targets.parquet", "playing-time targets")
    ).select("player_id", "next_year_mlb_pa")
    return predictors, targets


def _fit_score(
    training_predictors: pl.DataFrame,
    training_targets: pl.DataFrame,
    validation_predictors: pl.DataFrame,
    validation_targets: pl.DataFrame,
    *,
    form: str,
) -> tuple[pl.DataFrame, dict[str, object], pl.DataFrame, pl.DataFrame]:
    train_design = build_playing_time_design(training_predictors, form=form)
    fit = fit_playing_time_hurdle(train_design, training_targets, form=form)
    validation_design = build_playing_time_design(validation_predictors, form=form)
    scored, _ = score_playing_time_hurdle(fit, validation_design, validation_targets)
    metrics = pooled_playing_time_metrics(scored)
    return scored, metrics, fit.coefficient_frame(), fit.standardization_frame()


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    selected_form, advances, selection_record = _load_selection()
    if selected_form == PT_FORM_B0 or not advances:
        report = {
            "report_schema_version": "0.1",
            "gate": "playing_time_v1_out_of_time_validation_2023",
            "status": "skipped_baseline0_selected",
            "selected_form": selected_form,
            "selection_source_run": selection_record.get("source_run_id"),
            "decision": {
                "2023_validation_required": False,
                "2024_validation_authorized": False,
                "freeze_baseline0_as_playing_time_v1": True,
            },
            "boundary": {
                "2023_candidate_scores_accessed": False,
                "2024_candidate_scores_accessed": False,
                "2025_accessed": False,
            },
        }
        (args.output_root / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return 0

    training_predictors, training_targets = _load_fold(
        args.selection_artifact_root, TRAINING_FOLD
    )
    validation_predictors, validation_targets = _load_fold(
        args.selection_artifact_root, VALIDATION_FOLD
    )

    b0_scored, b0_metrics, b0_coef, b0_std = _fit_score(
        training_predictors,
        training_targets,
        validation_predictors,
        validation_targets,
        form=PT_FORM_B0,
    )
    candidate_scored, candidate_metrics, candidate_coef, candidate_std = _fit_score(
        training_predictors,
        training_targets,
        validation_predictors,
        validation_targets,
        form=selected_form,
    )
    if b0_metrics["scored_players"] != candidate_metrics["scored_players"]:
        raise RuntimeError("playing-time B0/candidate 2023 scored coverage differs")

    full_nll_delta = float(candidate_metrics["mean_full_negative_log_likelihood"]) - float(
        b0_metrics["mean_full_negative_log_likelihood"]
    )
    passes_primary = full_nll_delta < 0.0

    storage = {
        "baseline0_scored": write_canonical_parquet(
            b0_scored,
            table_root / "baseline0_scored.parquet",
            table_name="playing_time_v1_2023_baseline0_scored",
        ).as_record(),
        "candidate_scored": write_canonical_parquet(
            candidate_scored,
            table_root / "candidate_scored.parquet",
            table_name="playing_time_v1_2023_candidate_scored",
        ).as_record(),
        "baseline0_coefficients": write_canonical_parquet(
            b0_coef,
            table_root / "baseline0_coefficients.parquet",
            table_name="playing_time_v1_2023_baseline0_coefficients",
        ).as_record(),
        "candidate_coefficients": write_canonical_parquet(
            candidate_coef,
            table_root / "candidate_coefficients.parquet",
            table_name="playing_time_v1_2023_candidate_coefficients",
        ).as_record(),
        "baseline0_standardization": write_canonical_parquet(
            b0_std,
            table_root / "baseline0_standardization.parquet",
            table_name="playing_time_v1_2023_baseline0_standardization",
        ).as_record(),
        "candidate_standardization": write_canonical_parquet(
            candidate_std,
            table_root / "candidate_standardization.parquet",
            table_name="playing_time_v1_2023_candidate_standardization",
        ).as_record(),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_out_of_time_validation_2023",
        "status": "scored",
        "training_fold": TRAINING_FOLD,
        "validation_fold": VALIDATION_FOLD,
        "training_target_years": [2022],
        "validation_target_year": 2023,
        "selected_form": selected_form,
        "selection_source_run": selection_record.get("source_run_id"),
        "baseline0_metrics": b0_metrics,
        "candidate_metrics": candidate_metrics,
        "candidate_minus_baseline0_full_nll": full_nll_delta,
        "decision": {
            "passes_required_2023_full_nll_gate": passes_primary,
            "2024_validation_authorized": passes_primary,
            "reason_if_stopped": None
            if passes_primary
            else "selected playing-time candidate did not beat level-only B0 on 2023 full hurdle NLL",
        },
        "storage": storage,
        "boundary": {
            "form_reselected_on_2023": False,
            "2024_candidate_scores_accessed": False,
            "2025_accessed": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 — 2023 out-of-time validation",
        "",
        f"- Selected form: {selected_form}",
        f"- Candidate full NLL: {candidate_metrics['mean_full_negative_log_likelihood']:.9f}",
        f"- Level-only B0 full NLL: {b0_metrics['mean_full_negative_log_likelihood']:.9f}",
        f"- Delta full NLL: {full_nll_delta:+.9f}",
        f"- Passes required 2023 primary gate: {passes_primary}",
        f"- 2024 validation authorized: {passes_primary}",
        "- 2024 candidate scores accessed: False",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
