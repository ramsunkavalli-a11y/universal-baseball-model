#!/usr/bin/env python3
"""Run Projection-v1 out-of-time validation fold 1 on 2023 outcomes only.

The selected form/lambda are read from the binding 2022 selection result. This
script fits that exact configuration on all authorized 2022-response rows,
predicts the frozen 2022-10-15 B2 state, and scores only 2023 future outcomes.
It has no code path to the 2024 target fold or 2025 confirmation outcomes.
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
    PROJECTION_FORMS,
    PROJECTION_RIDGE_LAMBDAS,
    build_projection_design,
    fit_projection_weighted_ridge,
    predict_projection_ridge,
)
from universal_baseball.projection_selection import pooled_model_scores
from universal_baseball.projection_training import (
    PROJECTION_DELTA_COLUMNS,
    apply_projection_ilr_delta,
    build_projection_scoring_pair,
)
from universal_baseball.storage import write_canonical_parquet


TRAINING_FOLD = "projection_2021_to_2022"
VALIDATION_FOLD = "projection_2022_to_2023"
SELECTION_RESULT_PATH = Path("docs/projection-batting-v1-selection-result.json")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-responses-root", type=Path, required=True)
    parser.add_argument("--development-evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-validation-2023"),
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


def _load_frozen_selection() -> tuple[str, float, dict[str, object]]:
    result = json.loads(SELECTION_RESULT_PATH.read_text(encoding="utf-8"))
    if result.get("gate") != "projection_batting_v1_2022_candidate_selection":
        raise RuntimeError("unexpected Projection selection result gate")
    if not bool(result.get("advances_to_out_of_time_validation")):
        raise RuntimeError("Projection selection result does not authorize OOT validation")
    form = str(result["selected_form"])
    ridge_lambda = float(result["selected_lambda"])
    if form not in PROJECTION_FORMS:
        raise RuntimeError(f"frozen Projection selection has unsupported form: {form}")
    if ridge_lambda not in PROJECTION_RIDGE_LAMBDAS:
        raise RuntimeError(f"frozen Projection selection has unsupported lambda: {ridge_lambda}")
    if result.get("authorized_target_years_used_for_model_selection") != [2022]:
        raise RuntimeError("Projection selection record does not preserve 2022-only selection")
    return form, ridge_lambda, result


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    form, ridge_lambda, selection_record = _load_frozen_selection()

    training_rows = pl.read_parquet(
        _one(
            args.training_responses_root / "tables" / TRAINING_FOLD,
            "training_rows.parquet",
            "2022 Projection training rows",
        )
    )
    target_summary = pl.read_parquet(
        _one(
            args.development_evidence_root / "tables" / VALIDATION_FOLD,
            "target_summary.parquet",
            "2023 validation target summary",
        )
    )
    target_profile = pl.read_parquet(
        _one(
            args.development_evidence_root / "tables" / VALIDATION_FOLD,
            "target_profile.parquet",
            "2023 validation target profile",
        )
    )
    snapshot_fold_root = args.snapshot_root / "tables" / VALIDATION_FOLD
    snapshot_profile = pl.read_parquet(
        _one(snapshot_fold_root, "frozen_b2_profile.parquet", "2022-10-15 B2 profile")
    )
    player_context = pl.read_parquet(
        _one(snapshot_fold_root, "player_context.parquet", "2022-10-15 player context")
    )
    translation_offsets = pl.read_parquet(
        _one(snapshot_fold_root, "translation_offsets.parquet", "2022-10-15 translation")
    )

    train_design = build_projection_design(training_rows, form=form)
    fit = fit_projection_weighted_ridge(
        train_design,
        training_rows.select("player_id", "future_core_events", *PROJECTION_DELTA_COLUMNS),
        form=form,
        ridge_lambda=ridge_lambda,
        weight_column="future_core_events",
        response_columns=PROJECTION_DELTA_COLUMNS,
    )

    validation_design = build_projection_design(player_context, form=form)
    predicted_delta = predict_projection_ridge(fit, validation_design)
    candidate_profile = apply_projection_ilr_delta(snapshot_profile, predicted_delta)
    scoring_pair = build_projection_scoring_pair(snapshot_profile, candidate_profile)
    projected = project_latent_profiles_to_target_environment(
        scoring_pair,
        target_summary,
        translation_offsets,
    )
    scored = score_current_talent_profiles(projected, target_profile)
    aggregate_scores = pooled_model_scores(scored.environment_scores)
    baseline = _model_row(aggregate_scores, "baseline0")
    candidate = _model_row(aggregate_scores, "baseline1")

    baseline_log_loss = float(baseline["event_weighted_log_loss"])
    candidate_log_loss = float(candidate["event_weighted_log_loss"])
    baseline_brier = float(baseline["event_weighted_multinomial_brier"])
    candidate_brier = float(candidate["event_weighted_multinomial_brier"])
    passes_log_loss_gate = candidate_log_loss < baseline_log_loss

    storage = {
        "aggregate_scores": write_canonical_parquet(
            aggregate_scores,
            table_root / "aggregate_scores.parquet",
            table_name="projection_v1_2023_validation_aggregate_scores",
        ).as_record(),
        "environment_scores": write_canonical_parquet(
            scored.environment_scores,
            table_root / "environment_scores.parquet",
            table_name="projection_v1_2023_validation_environment_scores",
        ).as_record(),
        "candidate_profile": write_canonical_parquet(
            candidate_profile,
            table_root / "candidate_latent_profile.parquet",
            table_name="projection_v1_2023_validation_candidate_latent_profile",
        ).as_record(),
        "coefficients": write_canonical_parquet(
            fit.coefficient_frame(),
            table_root / "coefficients.parquet",
            table_name="projection_v1_2023_validation_coefficients",
        ).as_record(),
        "standardization": write_canonical_parquet(
            fit.standardization_frame(),
            table_root / "standardization.parquet",
            table_name="projection_v1_2023_validation_standardization",
        ).as_record(),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_out_of_time_validation_2023",
        "training_fold": TRAINING_FOLD,
        "validation_fold": VALIDATION_FOLD,
        "training_target_years": [2022],
        "validation_target_year": 2023,
        "selection_source_run": int(selection_record["selection_source_run"]),
        "frozen_form": form,
        "frozen_lambda": ridge_lambda,
        "scores": {
            "candidate_log_loss": candidate_log_loss,
            "baseline0_log_loss": baseline_log_loss,
            "candidate_minus_baseline_log_loss": candidate_log_loss - baseline_log_loss,
            "candidate_brier": candidate_brier,
            "baseline0_brier": baseline_brier,
            "candidate_minus_baseline_brier": candidate_brier - baseline_brier,
            "future_core_events": int(candidate["future_core_events"]),
            "scored_players": int(candidate["scored_players"]),
        },
        "decision": {
            "passes_required_2023_log_loss_gate": passes_log_loss_gate,
            "2024_validation_authorized": passes_log_loss_gate,
            "reason_if_stopped": None
            if passes_log_loss_gate
            else "candidate did not beat carry-forward B2 on 2023 log loss; two-fold promotion rule cannot pass",
        },
        "storage": storage,
        "boundary": {
            "form_or_lambda_reselected_on_2023": false,
            "2024_candidate_scores_accessed": false,
            "2025_accessed": false,
            "future_level_used_as_predictor": false,
            "playing_time_modeled": false
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection v1 — 2023 out-of-time validation",
        "",
        f"- Frozen form: {form}",
        f"- Frozen lambda: {ridge_lambda}",
        f"- Candidate log loss: {candidate_log_loss:.9f}",
        f"- Carry-forward B2 log loss: {baseline_log_loss:.9f}",
        f"- Delta log loss: {candidate_log_loss - baseline_log_loss:+.9f}",
        f"- Candidate Brier: {candidate_brier:.9f}",
        f"- Carry-forward B2 Brier: {baseline_brier:.9f}",
        f"- Delta Brier: {candidate_brier - baseline_brier:+.9f}",
        f"- Passes required 2023 log-loss gate: {passes_log_loss_gate}",
        f"- 2024 validation authorized: {passes_log_loss_gate}",
        "- 2024 candidate scores accessed: False",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
