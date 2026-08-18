#!/usr/bin/env python3
"""Freeze Playing Time / Role v1 pre-2025 confirmation refit.

Runs only after the binding 2024 development result authorizes confirmation.
Refits the exact frozen selected form and B0 on all 2022-2024 authorized training
observations, verifies deterministic reproduction, and persists parameters.
No 2025 evidence is accessed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl
import sklearn
import statsmodels

from universal_baseball.playing_time_model import (
    PT_FORM_B0,
    PT_FORMS,
    build_playing_time_design,
    fit_playing_time_hurdle,
)
from universal_baseball.storage import write_canonical_parquet


TRAINING_FOLDS = (
    ("projection_2021_to_2022", 1),
    ("projection_2022_to_2023", 2),
    ("projection_2023_to_2024", 3),
)
ROW_KEY_MULTIPLIER = 10_000_000
SELECTION_RESULT_PATH = Path("docs/playing-time-v1-selection-result.json")
VALIDATION_2024_RESULT_PATH = Path("docs/playing-time-v1-validation-2024-result.json")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-artifact-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-confirmation-refit"),
    )
    return parser.parse_args()


def _fold_file(root: Path, fold: str, filename: str, label: str) -> Path:
    matches = sorted(
        path for path in root.rglob(filename) if path.is_file() and fold in path.parts
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected one {label} for {fold} named {filename}, found {len(matches)}"
        )
    return matches[0]


def _binding_form() -> tuple[str, dict[str, object], dict[str, object]]:
    selection = json.loads(SELECTION_RESULT_PATH.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION_2024_RESULT_PATH.read_text(encoding="utf-8"))
    form = str(selection.get("selection", {}).get("selected_form"))
    if form not in PT_FORMS or form == PT_FORM_B0:
        raise RuntimeError("confirmation refit requires frozen non-B0 selected form")
    if not bool(validation.get("decision", {}).get("development_promotion_passed")):
        raise RuntimeError("playing-time development result does not authorize confirmation refit")
    if not bool(validation.get("decision", {}).get("2025_confirmation_authorized")):
        raise RuntimeError("playing-time 2024 result does not authorize 2025 confirmation")
    return form, selection, validation


def _combined_training(root: Path, *, form: str) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, object]]:
    designs: list[pl.DataFrame] = []
    targets: list[pl.DataFrame] = []
    source_counts: dict[int, int] = {}
    fold_counts: dict[str, int] = {}
    for fold, fold_index in TRAINING_FOLDS:
        predictors = pl.read_parquet(
            _fold_file(root, fold, "predictors.parquet", "playing-time predictors")
        )
        target = pl.read_parquet(
            _fold_file(root, fold, "next_year_mlb_pa_targets.parquet", "playing-time targets")
        ).select("player_id", "next_year_mlb_pa")
        design = build_playing_time_design(predictors, form=form)
        if set(design.get_column("player_id").to_list()) != set(target.get_column("player_id").to_list()):
            raise RuntimeError(f"playing-time refit coverage differs in {fold}")
        for player_id in design.get_column("player_id").to_list():
            source_counts[int(player_id)] = source_counts.get(int(player_id), 0) + 1
        offset = fold_index * ROW_KEY_MULTIPLIER
        designs.append(
            design.with_columns(
                (pl.lit(offset, dtype=pl.Int64) + pl.col("player_id").cast(pl.Int64)).alias("player_id")
            )
        )
        targets.append(
            target.with_columns(
                (pl.lit(offset, dtype=pl.Int64) + pl.col("player_id").cast(pl.Int64)).alias("player_id")
            )
        )
        fold_counts[fold] = int(design.height)
    combined_design = pl.concat(designs, how="vertical_relaxed")
    combined_target = pl.concat(targets, how="vertical_relaxed")
    if combined_design.get_column("player_id").n_unique() != combined_design.height:
        raise RuntimeError("playing-time confirmation refit observation IDs collide")
    metrics = {
        "training_observation_count": int(combined_design.height),
        "unique_source_player_count": len(source_counts),
        "source_players_repeated_across_folds": sum(1 for value in source_counts.values() if value > 1),
        "training_fold_row_counts": fold_counts,
        "player_identity_used_as_predictor": False,
    }
    return combined_design, combined_target, metrics


def _max_fit_difference(first, second) -> float:
    differences = [
        abs(first.logistic_intercept - second.logistic_intercept),
        abs(first.nb_alpha - second.nb_alpha),
    ]
    differences.extend(
        abs(a - b)
        for a, b in zip(first.logistic_coefficients, second.logistic_coefficients, strict=True)
    )
    differences.extend(
        abs(a - b) for a, b in zip(first.nb_coefficients, second.nb_coefficients, strict=True)
    )
    for feature in first.continuous_features:
        differences.append(
            abs(first.standardization.means[feature] - second.standardization.means[feature])
        )
        differences.append(
            abs(first.standardization.scales[feature] - second.standardization.scales[feature])
        )
    return max(differences) if differences else 0.0


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    selected_form, selection_record, validation_record = _binding_form()
    candidate_design, candidate_target, candidate_training = _combined_training(
        args.selection_artifact_root, form=selected_form
    )
    b0_design, b0_target, b0_training = _combined_training(
        args.selection_artifact_root, form=PT_FORM_B0
    )

    candidate_fit = fit_playing_time_hurdle(
        candidate_design, candidate_target, form=selected_form
    )
    candidate_reproduction = fit_playing_time_hurdle(
        candidate_design, candidate_target, form=selected_form
    )
    b0_fit = fit_playing_time_hurdle(b0_design, b0_target, form=PT_FORM_B0)
    b0_reproduction = fit_playing_time_hurdle(b0_design, b0_target, form=PT_FORM_B0)
    candidate_max_diff = _max_fit_difference(candidate_fit, candidate_reproduction)
    b0_max_diff = _max_fit_difference(b0_fit, b0_reproduction)
    reproduction_tolerance = 1e-10
    if candidate_max_diff > reproduction_tolerance or b0_max_diff > reproduction_tolerance:
        raise RuntimeError(
            "playing-time confirmation refit is not deterministic to frozen tolerance: "
            f"candidate={candidate_max_diff}, b0={b0_max_diff}"
        )

    storage = {
        "candidate_coefficients": write_canonical_parquet(
            candidate_fit.coefficient_frame(),
            table_root / "candidate_coefficients.parquet",
            table_name="playing_time_v1_confirmation_candidate_coefficients",
        ).as_record(),
        "candidate_standardization": write_canonical_parquet(
            candidate_fit.standardization_frame(),
            table_root / "candidate_standardization.parquet",
            table_name="playing_time_v1_confirmation_candidate_standardization",
        ).as_record(),
        "baseline0_coefficients": write_canonical_parquet(
            b0_fit.coefficient_frame(),
            table_root / "baseline0_coefficients.parquet",
            table_name="playing_time_v1_confirmation_baseline0_coefficients",
        ).as_record(),
        "baseline0_standardization": write_canonical_parquet(
            b0_fit.standardization_frame(),
            table_root / "baseline0_standardization.parquet",
            table_name="playing_time_v1_confirmation_baseline0_standardization",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_confirmation_refit_freeze",
        "status": "frozen_ready_for_2025_source_materialization",
        "selected_form": selected_form,
        "baseline0_form": PT_FORM_B0,
        "training_target_years": [2022, 2023, 2024],
        "selection_source_run": selection_record.get("source_run_id"),
        "validation_2024_source_run": validation_record.get("source_run_id"),
        "candidate_training": candidate_training,
        "baseline0_training": b0_training,
        "candidate_nb_alpha": candidate_fit.nb_alpha,
        "baseline0_nb_alpha": b0_fit.nb_alpha,
        "deterministic_reproduction": {
            "tolerance": reproduction_tolerance,
            "candidate_max_parameter_difference": candidate_max_diff,
            "baseline0_max_parameter_difference": b0_max_diff,
            "passed": True,
        },
        "package_versions": {
            "numpy": np.__version__,
            "polars": pl.__version__,
            "scikit_learn": sklearn.__version__,
            "statsmodels": statsmodels.__version__,
        },
        "storage": storage,
        "boundary": {
            "2025_accessed": False,
            "2025_target_materialized": False,
            "form_reselected_after_development": False,
            "batting_rate_modified": False,
        },
        "decision": {
            "parameters_frozen_before_2025": True,
            "2025_source_materialization_authorized": True,
            "2025_confirmation_scoring_authorized_after_source_certification": True,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        "# Playing-time v1 confirmation refit freeze",
        "",
        f"- Selected form: {selected_form}",
        f"- Training observations: {candidate_training['training_observation_count']:,}",
        f"- Candidate NB alpha: {candidate_fit.nb_alpha:.9f}",
        f"- Deterministic reproduction max diff: {candidate_max_diff:.3e}",
        "- 2025 accessed: False",
        "- Parameters frozen before 2025: True",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
