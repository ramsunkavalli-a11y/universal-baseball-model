#!/usr/bin/env python3
"""Run Projection-v1 out-of-time validation fold 2 on 2024 outcomes only.

The selected form/lambda are immutable from the 2022 selection gate. This script
refits that exact configuration on the two chronologically prior authorized
training-response folds (2022 and 2023 outcomes), predicts the frozen
2023-10-15 B2 state, and scores only 2024 future outcomes.

Repeated players across training years are represented as distinct training
observations via a deterministic fold+player row key. Player identity itself is
not a predictor and the model specification is unchanged.
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


TRAINING_FOLDS = (
    ("projection_2021_to_2022", 1),
    ("projection_2022_to_2023", 2),
)
VALIDATION_FOLD = "projection_2023_to_2024"
SELECTION_RESULT_PATH = Path("docs/projection-batting-v1-selection-result.json")
VALIDATION_2023_RESULT_PATH = Path("docs/projection-batting-v1-validation-2023-result.json")
ROW_KEY_MULTIPLIER = 10_000_000


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--training-responses-root", type=Path, required=True)
    parser.add_argument("--development-evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-validation-2024"),
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
    return form, ridge_lambda, result


def _require_2023_pass() -> dict[str, object]:
    result = json.loads(VALIDATION_2023_RESULT_PATH.read_text(encoding="utf-8"))
    if result.get("gate") != "projection_batting_v1_out_of_time_validation_2023":
        raise RuntimeError("unexpected Projection 2023 validation result gate")
    decision = result.get("decision", {})
    if not bool(decision.get("2024_validation_authorized")):
        raise RuntimeError("2023 validation did not authorize 2024 Projection scoring")
    return result


def _training_observations(root: Path) -> tuple[pl.DataFrame, dict[str, object]]:
    frames: list[pl.DataFrame] = []
    fold_counts: dict[str, int] = {}
    original_players: set[int] = set()
    for fold_label, fold_index in TRAINING_FOLDS:
        frame = pl.read_parquet(
            _one(
                root / "tables" / fold_label,
                "training_rows.parquet",
                f"{fold_label} training rows",
            )
        )
        if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
            raise RuntimeError(f"{fold_label} violates within-fold player grain")
        original_players.update(int(value) for value in frame.get_column("player_id").to_list())
        keyed = frame.with_columns(
            (
                pl.lit(fold_index * ROW_KEY_MULTIPLIER, dtype=pl.Int64)
                + pl.col("player_id").cast(pl.Int64)
            ).alias("training_observation_id"),
            pl.lit(fold_label).alias("training_source_fold"),
            pl.col("player_id").cast(pl.Int64).alias("source_player_id"),
        )
        if keyed.get_column("training_observation_id").n_unique() != keyed.height:
            raise RuntimeError(f"{fold_label} training-observation IDs are not unique")
        fold_counts[fold_label] = int(keyed.height)
        frames.append(keyed)

    combined = pl.concat(frames, how="vertical_relaxed")
    if combined.get_column("training_observation_id").n_unique() != combined.height:
        raise RuntimeError("cross-fold Projection training-observation IDs collide")
    duplicated_players = int(
        combined.group_by("source_player_id").len().filter(pl.col("len") > 1).height
    )
    metrics = {
        "training_observation_count": int(combined.height),
        "unique_source_player_count": len(original_players),
        "source_players_repeated_across_folds": duplicated_players,
        "training_fold_row_counts": fold_counts,
        "training_row_key": "deterministic_fold_index_times_10000000_plus_player_id",
        "player_identity_used_as_predictor": False,
    }
    return combined, metrics


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    form, ridge_lambda, selection_record = _load_frozen_selection()
    validation_2023_result = _require_2023_pass()
    training_rows, training_metrics = _training_observations(args.training_responses_root)

    # The ridge primitive uses `player_id` only as a row-alignment key. Replace it
    # with the unique training-observation key so repeated players across years
    # remain separate observations without adding identity to the predictor set.
    fit_context = training_rows.drop("player_id").rename(
        {"training_observation_id": "player_id"}
    )
    fit_responses = training_rows.select(
        pl.col("training_observation_id").alias("player_id"),
        "future_core_events",
        *PROJECTION_DELTA_COLUMNS,
    )
    train_design = build_projection_design(fit_context, form=form)
    fit = fit_projection_weighted_ridge(
        train_design,
        fit_responses,
        form=form,
        ridge_lambda=ridge_lambda,
        weight_column="future_core_events",
        response_columns=PROJECTION_DELTA_COLUMNS,
    )

    target_summary = pl.read_parquet(
        _one(
            args.development_evidence_root / "tables" / VALIDATION_FOLD,
            "target_summary.parquet",
            "2024 validation target summary",
        )
    )
    target_profile = pl.read_parquet(
        _one(
            args.development_evidence_root / "tables" / VALIDATION_FOLD,
            "target_profile.parquet",
            "2024 validation target profile",
        )
    )
    snapshot_fold_root = args.snapshot_root / "tables" / VALIDATION_FOLD
    snapshot_profile = pl.read_parquet(
        _one(snapshot_fold_root, "frozen_b2_profile.parquet", "2023-10-15 B2 profile")
    )
    player_context = pl.read_parquet(
        _one(snapshot_fold_root, "player_context.parquet", "2023-10-15 player context")
    )
    translation_offsets = pl.read_parquet(
        _one(snapshot_fold_root, "translation_offsets.parquet", "2023-10-15 translation")
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
            table_name="projection_v1_2024_validation_aggregate_scores",
        ).as_record(),
        "environment_scores": write_canonical_parquet(
            scored.environment_scores,
            table_root / "environment_scores.parquet",
            table_name="projection_v1_2024_validation_environment_scores",
        ).as_record(),
        "candidate_profile": write_canonical_parquet(
            candidate_profile,
            table_root / "candidate_latent_profile.parquet",
            table_name="projection_v1_2024_validation_candidate_latent_profile",
        ).as_record(),
        "coefficients": write_canonical_parquet(
            fit.coefficient_frame(),
            table_root / "coefficients.parquet",
            table_name="projection_v1_2024_validation_coefficients",
        ).as_record(),
        "standardization": write_canonical_parquet(
            fit.standardization_frame(),
            table_root / "standardization.parquet",
            table_name="projection_v1_2024_validation_standardization",
        ).as_record(),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_out_of_time_validation_2024",
        "training_folds": [label for label, _ in TRAINING_FOLDS],
        "training_target_years": [2022, 2023],
        "validation_fold": VALIDATION_FOLD,
        "validation_target_year": 2024,
        "selection_source_run": int(selection_record["selection_source_run"]),
        "frozen_form": form,
        "frozen_lambda": ridge_lambda,
        "prior_validation_2023_log_loss_delta": float(
            validation_2023_result["scores"]["candidate_minus_baseline_log_loss"]
        ),
        "training_observation_metrics": training_metrics,
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
            "passes_required_2024_log_loss_gate": passes_log_loss_gate,
            "full_development_diagnostics_authorized": passes_log_loss_gate,
            "reason_if_stopped": None
            if passes_log_loss_gate
            else "candidate did not beat carry-forward B2 on 2024 log loss; frozen two-fold promotion rule fails",
        },
        "storage": storage,
        "boundary": {
            "form_or_lambda_reselected_on_2024": False,
            "2025_accessed": False,
            "future_level_used_as_predictor": False,
            "player_identity_used_as_predictor": False,
            "playing_time_modeled": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection v1 — 2024 out-of-time validation",
        "",
        f"- Frozen form: {form}",
        f"- Frozen lambda: {ridge_lambda}",
        f"- Training observations: {training_metrics['training_observation_count']:,}",
        f"- Unique source players: {training_metrics['unique_source_player_count']:,}",
        f"- Players repeated across training folds: {training_metrics['source_players_repeated_across_folds']:,}",
        f"- Candidate log loss: {candidate_log_loss:.9f}",
        f"- Carry-forward B2 log loss: {baseline_log_loss:.9f}",
        f"- Delta log loss: {candidate_log_loss - baseline_log_loss:+.9f}",
        f"- Candidate Brier: {candidate_brier:.9f}",
        f"- Carry-forward B2 Brier: {baseline_brier:.9f}",
        f"- Delta Brier: {candidate_brier - baseline_brier:+.9f}",
        f"- Passes required 2024 log-loss gate: {passes_log_loss_gate}",
        f"- Full development diagnostics authorized: {passes_log_loss_gate}",
        "- 2025 accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
