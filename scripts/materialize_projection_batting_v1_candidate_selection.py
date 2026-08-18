#!/usr/bin/env python3
"""Run the frozen Projection-v1 candidate grid on the 2022 selection fold only.

This script is deliberately incapable of reading the 2023/2024 training-response
folds for model selection. It performs the pre-registered 5-fold player-held-out
CV over exactly two forms x four ridge penalties, scores held-out 2022 future
core events against carry-forward B2 with the existing proper-score engine, and
applies the frozen tie-break / early-reject rule.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.current_talent_scoring import (
    project_latent_profiles_to_target_environment,
    score_current_talent_profiles,
)
from universal_baseball.projection_ridge import (
    PROJECTION_CV_FOLD_COUNT,
    PROJECTION_FORMS,
    PROJECTION_RIDGE_LAMBDAS,
    build_projection_design,
    fit_projection_weighted_ridge,
    predict_projection_ridge,
)
from universal_baseball.projection_selection import (
    pooled_model_scores,
    select_projection_configuration,
)
from universal_baseball.projection_training import (
    PROJECTION_DELTA_COLUMNS,
    apply_projection_ilr_delta,
    build_projection_scoring_pair,
)
from universal_baseball.storage import write_canonical_parquet


SELECTION_FOLD = "projection_2021_to_2022"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-responses-root", type=Path, required=True)
    parser.add_argument("--development-evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-candidate-selection"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def _model_row(scores: pl.DataFrame, model: str) -> dict[str, object]:
    filtered = scores.filter(pl.col("model") == model)
    if filtered.height != 1:
        raise RuntimeError(f"expected one pooled score row for {model}, found {filtered.height}")
    return filtered.row(0, named=True)


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    training_root = args.training_responses_root / "tables" / SELECTION_FOLD
    target_root = args.development_evidence_root / "tables" / SELECTION_FOLD
    snapshot_fold_root = args.snapshot_root / "tables" / SELECTION_FOLD

    training_rows = pl.read_parquet(
        _one(training_root, "training_rows.parquet", "2022 selection training rows")
    )
    target_summary = pl.read_parquet(
        _one(target_root, "target_summary.parquet", "2022 selection target summary")
    )
    target_profile = pl.read_parquet(
        _one(target_root, "target_profile.parquet", "2022 selection target profile")
    )
    snapshot_profile = pl.read_parquet(
        _one(snapshot_fold_root, "frozen_b2_profile.parquet", "2021-10-15 B2 profile")
    )
    translation_offsets = pl.read_parquet(
        _one(snapshot_fold_root, "translation_offsets.parquet", "2021-10-15 translation")
    )

    required_training = {
        "player_id",
        "age_years",
        "as_of_level_group",
        "future_core_events",
        "cv_fold",
        *PROJECTION_DELTA_COLUMNS,
    }
    missing = sorted(required_training - set(training_rows.columns))
    if missing:
        raise RuntimeError(f"2022 Projection selection rows missing fields: {missing}")
    observed_folds = set(
        int(value) for value in training_rows.get_column("cv_fold").unique().to_list()
    )
    if observed_folds != set(range(PROJECTION_CV_FOLD_COUNT)):
        raise RuntimeError(
            f"Projection selection CV fold coverage mismatch: {sorted(observed_folds)}"
        )

    configuration_rows: list[dict[str, object]] = []
    fold_score_frames: list[pl.DataFrame] = []
    coefficient_frames: list[pl.DataFrame] = []
    standardization_frames: list[pl.DataFrame] = []

    for form in PROJECTION_FORMS:
        full_design = build_projection_design(training_rows, form=form)
        for ridge_lambda in PROJECTION_RIDGE_LAMBDAS:
            config_environment_scores: list[pl.DataFrame] = []
            for cv_fold in range(PROJECTION_CV_FOLD_COUNT):
                train_rows = training_rows.filter(pl.col("cv_fold") != cv_fold)
                heldout_rows = training_rows.filter(pl.col("cv_fold") == cv_fold)
                train_ids = set(
                    int(value) for value in train_rows.get_column("player_id").to_list()
                )
                heldout_ids = set(
                    int(value) for value in heldout_rows.get_column("player_id").to_list()
                )
                if train_ids & heldout_ids:
                    raise RuntimeError("Projection CV train/heldout player overlap")
                if not heldout_ids:
                    raise RuntimeError(f"Projection CV fold {cv_fold} is empty")

                train_design = full_design.filter(pl.col("player_id").is_in(sorted(train_ids)))
                heldout_design = full_design.filter(
                    pl.col("player_id").is_in(sorted(heldout_ids))
                )
                fit = fit_projection_weighted_ridge(
                    train_design,
                    train_rows.select(
                        "player_id", "future_core_events", *PROJECTION_DELTA_COLUMNS
                    ),
                    form=form,
                    ridge_lambda=float(ridge_lambda),
                    weight_column="future_core_events",
                    response_columns=PROJECTION_DELTA_COLUMNS,
                )
                predicted_delta = predict_projection_ridge(fit, heldout_design)
                candidate_profile = apply_projection_ilr_delta(
                    snapshot_profile, predicted_delta
                )
                scoring_pair = build_projection_scoring_pair(
                    snapshot_profile, candidate_profile
                )

                heldout_target_summary = target_summary.filter(
                    pl.col("player_id").is_in(sorted(heldout_ids))
                )
                heldout_target_profile = target_profile.filter(
                    pl.col("player_id").is_in(sorted(heldout_ids))
                )
                projected = project_latent_profiles_to_target_environment(
                    scoring_pair,
                    heldout_target_summary,
                    translation_offsets,
                )
                report = score_current_talent_profiles(
                    projected, heldout_target_profile
                )
                fold_scores = pooled_model_scores(report.environment_scores).with_columns(
                    pl.lit(form).alias("form"),
                    pl.lit(float(ridge_lambda)).alias("ridge_lambda"),
                    pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
                )
                fold_score_frames.append(fold_scores)
                config_environment_scores.append(report.environment_scores)

                coefficient_frames.append(
                    fit.coefficient_frame().with_columns(
                        pl.lit(form).alias("form"),
                        pl.lit(float(ridge_lambda)).alias("ridge_lambda"),
                        pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
                    )
                )
                standardization_frames.append(
                    fit.standardization_frame().with_columns(
                        pl.lit(form).alias("form"),
                        pl.lit(float(ridge_lambda)).alias("ridge_lambda"),
                        pl.lit(cv_fold).cast(pl.Int64).alias("cv_fold"),
                    )
                )

            pooled = pooled_model_scores(
                pl.concat(config_environment_scores, how="vertical_relaxed")
            )
            baseline = _model_row(pooled, "baseline0")
            candidate = _model_row(pooled, "baseline1")
            configuration_rows.append(
                {
                    "form": form,
                    "ridge_lambda": float(ridge_lambda),
                    "baseline0_log_loss": float(
                        baseline["event_weighted_log_loss"]
                    ),
                    "baseline0_brier": float(
                        baseline["event_weighted_multinomial_brier"]
                    ),
                    "candidate_log_loss": float(
                        candidate["event_weighted_log_loss"]
                    ),
                    "candidate_brier": float(
                        candidate["event_weighted_multinomial_brier"]
                    ),
                    "candidate_minus_baseline_log_loss": float(
                        candidate["event_weighted_log_loss"]
                    )
                    - float(baseline["event_weighted_log_loss"]),
                    "candidate_minus_baseline_brier": float(
                        candidate["event_weighted_multinomial_brier"]
                    )
                    - float(baseline["event_weighted_multinomial_brier"]),
                    "future_core_events": int(candidate["future_core_events"]),
                    "scored_players": int(candidate["scored_players"]),
                }
            )

    configuration_scores = pl.DataFrame(configuration_rows).sort(
        ["candidate_log_loss", "candidate_brier"]
    )
    selection = select_projection_configuration(configuration_scores)
    fold_scores = pl.concat(fold_score_frames, how="vertical_relaxed").sort(
        ["form", "ridge_lambda", "cv_fold", "model"]
    )
    coefficients = pl.concat(coefficient_frames, how="vertical_relaxed").sort(
        ["form", "ridge_lambda", "cv_fold", "feature", "response"]
    )
    standardization = pl.concat(
        standardization_frames, how="vertical_relaxed"
    ).sort(["form", "ridge_lambda", "cv_fold", "feature"])

    storage = {
        "configuration_scores": write_canonical_parquet(
            configuration_scores,
            table_root / "configuration_scores.parquet",
            table_name="projection_v1_2022_candidate_configuration_scores",
        ).as_record(),
        "cv_fold_scores": write_canonical_parquet(
            fold_scores,
            table_root / "cv_fold_scores.parquet",
            table_name="projection_v1_2022_candidate_cv_fold_scores",
        ).as_record(),
        "cv_coefficients": write_canonical_parquet(
            coefficients,
            table_root / "cv_coefficients.parquet",
            table_name="projection_v1_2022_candidate_cv_coefficients",
        ).as_record(),
        "cv_standardization": write_canonical_parquet(
            standardization,
            table_root / "cv_standardization.parquet",
            table_name="projection_v1_2022_candidate_cv_standardization",
        ).as_record(),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_2022_candidate_selection",
        "selection_fold": SELECTION_FOLD,
        "authorized_target_years_used_for_model_selection": [2022],
        "training_response_source_run": 32100142102,
        "development_evidence_source_run": 32097702869,
        "frozen_b2_snapshot_source_run": 32099733186,
        "candidate_grid": {
            "forms": list(PROJECTION_FORMS),
            "ridge_lambdas": list(PROJECTION_RIDGE_LAMBDAS),
            "cv_folds": PROJECTION_CV_FOLD_COUNT,
        },
        "selection": {
            "selected_form": selection.selected_form,
            "selected_lambda": selection.selected_lambda,
            "candidate_log_loss": selection.candidate_log_loss,
            "candidate_brier": selection.candidate_brier,
            "baseline0_log_loss": selection.baseline0_log_loss,
            "baseline0_brier": selection.baseline0_brier,
            "candidate_minus_baseline_log_loss": (
                selection.candidate_log_loss - selection.baseline0_log_loss
            ),
            "candidate_minus_baseline_brier": (
                selection.candidate_brier - selection.baseline0_brier
            ),
            "early_reject": selection.early_reject,
            "advances_to_out_of_time_validation": (
                selection.advances_to_out_of_time_validation
            ),
            "metrics": selection.metrics,
        },
        "storage": storage,
        "boundary": {
            "accessed_2023_candidate_scores": False,
            "accessed_2024_candidate_scores": False,
            "accessed_2025": False,
            "future_level_used_as_predictor": False,
            "playing_time_modeled": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection v1 — 2022-only candidate selection",
        "",
        f"- Selected form: {selection.selected_form}",
        f"- Selected lambda: {selection.selected_lambda}",
        f"- Candidate log loss: {selection.candidate_log_loss:.9f}",
        f"- Carry-forward B2 log loss: {selection.baseline0_log_loss:.9f}",
        f"- Delta log loss: {selection.candidate_log_loss - selection.baseline0_log_loss:+.9f}",
        f"- Candidate Brier: {selection.candidate_brier:.9f}",
        f"- Carry-forward B2 Brier: {selection.baseline0_brier:.9f}",
        f"- Delta Brier: {selection.candidate_brier - selection.baseline0_brier:+.9f}",
        f"- Early reject: {selection.early_reject}",
        f"- Advances to 2023/2024 OOT validation: {selection.advances_to_out_of_time_validation}",
        "- 2023 candidate scores accessed: False",
        "- 2024 candidate scores accessed: False",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
