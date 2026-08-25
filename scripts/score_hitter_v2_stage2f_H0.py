#!/usr/bin/env python3
"""Execute the frozen one-shot H0 comparison on disclosed V2022-V2024."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_stage2f_scoring import (
    CORRELATION_METRICS,
    PRIMARY_METRICS,
    primary_gate,
    strongest_baseline,
    subgroup_reversal_gate,
    translate_target_to_reference,
)
from universal_baseball.hitter_v2_validation import (
    build_evaluation_subgroups,
    build_player_scoring_surface,
    level_aggregate_calibration,
    predicted_woba_decile_calibration,
    score_subgroup,
    summarize_scoring_surface,
    terminal_component_calibration,
)
from universal_baseball.storage import sha256_file


FOLDS = ("V2022", "V2023", "V2024")
BASELINES = (
    "REFERENCE_B0_ONE_YEAR_EB",
    "REFERENCE_B1_MARCEL_345_K1200",
    "REFERENCE_C0_NESTED_EB",
)
CANDIDATE = "H0_NEUTRAL_HIERARCHICAL_OUTCOMES"
MODELS = (*BASELINES, CANDIDATE)
POOLED_RELATIVE_MINIMUM = {
    "terminal_log_loss": 0.0025,
    "terminal_brier_score": 0.0025,
    "woba_rmse": 0.01,
    "runs_per_600_rmse": 0.01,
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2f-H0-scoring-contract.json"),
    )
    parser.add_argument(
        "--selection-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2f-H0-selection/tables"),
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--age-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age/tables"),
    )
    parser.add_argument(
        "--raw-baseline-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2f-H0-comparison"),
    )
    return parser.parse_args()


def _atomic_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def verify_scoring_boundary(contract: dict[str, object], *, runner: Path) -> None:
    """Fail before target loading unless the immutable comparison is certified."""

    if contract["status"] != "frozen_before_first_disclosed_target_access":
        raise ValueError("Stage 2f scoring contract is not frozen")
    if sha256_file(runner) != contract["runner_sha256"]:
        raise ValueError("Stage 2f scoring runner changed after freeze")
    if contract["candidate_scoring_authorized"] is not True:
        raise ValueError("Stage 2f disclosed comparison is not authorized")
    for boundary in (
        "post_result_retuning_authorized",
        "H1_authorized",
        "tracking_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        if contract[boundary] is not False:
            raise ValueError(f"Stage 2f scoring contract improperly opened {boundary}")


def _prediction_paths(root: Path, slug: str) -> dict[str, Path]:
    return {
        "REFERENCE_B0_ONE_YEAR_EB": root / slug / "reference_wrapped_b0.parquet",
        "REFERENCE_B1_MARCEL_345_K1200": root / slug / "reference_wrapped_b1.parquet",
        "REFERENCE_C0_NESTED_EB": root / slug / "reference_wrapped_c0.parquet",
        CANDIDATE: root / slug / "h0_predictions.parquet",
    }


def _correlation_gate(
    metrics: dict[str, dict[str, object]],
) -> dict[str, object]:
    rows: dict[str, object] = {}
    for metric in CORRELATION_METRICS:
        baseline_id = max(
            BASELINES,
            key=lambda model: (
                float(metrics[model][metric]),
                model,
            ),
        )
        baseline = float(metrics[baseline_id][metric])
        candidate = float(metrics[CANDIDATE][metric])
        rows[metric] = {
            "candidate": candidate,
            "baseline_id": baseline_id,
            "baseline": baseline,
            "decline": baseline - candidate,
            "pass": baseline - candidate <= 0.01,
        }
    return {"comparisons": rows, "pass": all(row["pass"] for row in rows.values())}


def _calibration(
    candidate: pl.DataFrame, target: pl.DataFrame, metrics: dict[str, dict[str, object]]
) -> dict[str, object]:
    components = {
        view: terminal_component_calibration(candidate, target, weighting=view)
        for view in ("player", "pa")
    }
    surface = build_player_scoring_surface(
        candidate, target, model_id=CANDIDATE, fold_id="calibration"
    )
    deciles = predicted_woba_decile_calibration(surface)
    levels = level_aggregate_calibration(candidate, target)
    woba_pass = all(
        abs(float(metrics[view]["woba_calibration_intercept"])) <= 0.005
        and 0.90 <= float(metrics[view]["woba_calibration_slope"]) <= 1.10
        for view in ("player", "pa")
    )
    component_pass = all(
        row["slope_guardrail_pass"] is not False
        for rows in components.values()
        for row in rows
    )
    decile_pass = all(bool(row["guardrail_pass"]) for row in deciles)
    level_pass = all(row["guardrail_pass"] is not False for row in levels)
    return {
        "woba_pass": woba_pass,
        "terminal_components": components,
        "terminal_component_pass": component_pass,
        "predicted_woba_deciles": deciles,
        "predicted_woba_decile_pass": decile_pass,
        "level_aggregate": levels,
        "level_aggregate_pass": level_pass,
        "pass": woba_pass and component_pass and decile_pass and level_pass,
    }


def _subgroups(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    standard: pl.DataFrame,
) -> tuple[list[dict[str, object]], bool]:
    quality = predictions[CANDIDATE].select("player_id", "translation_path_quality")
    labels = standard.join(quality, on="player_id", how="left", validate="1:1")
    definitions = {
        "level": ("primary_target_level_group", 100, 10_000),
        "age": ("age_band", 50, 5_000),
        "evidence": ("evidence_band", 50, 5_000),
        "movement": ("movement_band", 50, 5_000),
        "K": ("k_band", 50, 5_000),
        "power": ("hr_power_band", 50, 5_000),
        "translation_path_quality": ("translation_path_quality", 50, 5_000),
    }
    rows: list[dict[str, object]] = []
    all_pass = True
    for dimension, (column, minimum_players, minimum_pa) in definitions.items():
        for label in sorted(str(value) for value in labels[column].drop_nulls().unique()):
            player_ids = labels.filter(pl.col(column) == label)["player_id"].to_list()
            scores = {
                model: score_subgroup(predictions[model], target, player_ids)
                for model in MODELS
            }
            players = int(scores[CANDIDATE]["players"])
            target_pa = int(scores[CANDIDATE]["target_pa"])
            supported = players >= minimum_players and target_pa >= minimum_pa
            gates = {}
            if supported:
                for view in ("player", "pa"):
                    gates[view] = subgroup_reversal_gate(
                        scores[CANDIDATE]["metrics"][view],
                        {
                            model: scores[model]["metrics"][view]
                            for model in BASELINES
                        },
                    )
                all_pass = all_pass and all(gate["pass"] for gate in gates.values())
            rows.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "players": players,
                    "target_pa": target_pa,
                    "supported": supported,
                    "model_scores": scores,
                    "gates": gates,
                }
            )
    return rows, all_pass


def _verify_fold_inputs(
    frozen: dict[str, object],
    predictions: dict[str, Path],
    target: Path,
    training: Path,
    age: Path,
    raw_marcel: Path,
    translation: Path | None,
) -> None:
    for model, path in predictions.items():
        if sha256_file(path) != frozen["prediction_sha256"][model]:
            raise ValueError(f"frozen prediction changed: {model}")
    for key, path in (
        ("target_sha256", target),
        ("training_sha256", training),
        ("age_sha256", age),
        ("raw_marcel_sha256", raw_marcel),
    ):
        if sha256_file(path) != frozen[key]:
            raise ValueError(f"frozen scoring input changed: {key}")
    expected_translation = frozen["translation_offsets_sha256"]
    if translation is None:
        if expected_translation is not None:
            raise ValueError("frozen translation input is missing")
    elif sha256_file(translation) != expected_translation:
        raise ValueError("frozen translation offsets changed")


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    verify_scoring_boundary(contract, runner=Path(__file__))
    for key in ("authorization", "selection_checkpoint", "selection_report"):
        path = Path(contract[f"{key}_path"])
        if sha256_file(path) != contract[f"{key}_sha256"]:
            raise ValueError(f"Stage 2f frozen {key} changed")

    fold_reports: list[dict[str, object]] = []
    pooled: dict[str, list[pl.DataFrame]] = {model: [] for model in MODELS}
    for fold_id in FOLDS:
        slug = fold_id.lower()
        frozen = contract["folds"][fold_id]
        prediction_paths = _prediction_paths(args.selection_root, slug)
        target_path = args.target_root / slug / "target_players.parquet"
        training_path = args.target_root / slug / "training_player_league_seasons.parquet"
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        raw_marcel_path = args.raw_baseline_root / slug / "b1_marcel_345_k1200_predictions.parquet"
        offset_path = args.selection_root / slug / "translation_offsets.parquet"
        translation_path = offset_path if offset_path.exists() else None
        _verify_fold_inputs(
            frozen,
            prediction_paths,
            target_path,
            training_path,
            age_path,
            raw_marcel_path,
            translation_path,
        )

        predictions = {
            model: pl.read_parquet(path) for model, path in prediction_paths.items()
        }
        raw_target = pl.read_parquet(target_path)
        translation = (
            None if translation_path is None else pl.read_parquet(translation_path)
        )
        target = translate_target_to_reference(raw_target, translation)
        training = pl.read_parquet(training_path)
        ages = pl.read_parquet(age_path)
        metrics = {
            model: {
                view: score_hitter_predictions(frame, target, weighting=view)
                for view in ("player", "pa")
            }
            for model, frame in predictions.items()
        }
        raw_marcel = pl.read_parquet(raw_marcel_path)
        raw_marcel_diagnostic = {
            view: score_hitter_predictions(raw_marcel, raw_target, weighting=view)
            for view in ("player", "pa")
        }
        primary = {
            view: primary_gate(
                metrics[CANDIDATE][view],
                {model: metrics[model][view] for model in BASELINES},
            )
            for view in ("player", "pa")
        }
        correlations = {
            view: _correlation_gate(
                {model: metrics[model][view] for model in MODELS}
            )
            for view in ("player", "pa")
        }
        calibration = _calibration(predictions[CANDIDATE], target, metrics[CANDIDATE])
        standard = build_evaluation_subgroups(training, raw_target, ages)
        subgroup_rows, subgroup_pass = _subgroups(predictions, target, standard)
        surfaces = {
            model: build_player_scoring_surface(
                frame, target, model_id=model, fold_id=fold_id
            )
            for model, frame in predictions.items()
        }
        for model, surface in surfaces.items():
            pooled[model].append(surface)
        fold_pass = (
            all(gate["pass"] for gate in primary.values())
            and all(gate["pass"] for gate in correlations.values())
            and calibration["pass"]
            and subgroup_pass
        )
        fold_reports.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": int(training["season"].max()),
                "target_season": int(raw_target["season"].item(0)),
                "reference_target_translation": "training_frozen_ALL_age_band_offsets",
                "metrics": metrics,
                "raw_unwrapped_marcel_diagnostic": raw_marcel_diagnostic,
                "primary_gates": primary,
                "primary_gate_pass": all(gate["pass"] for gate in primary.values()),
                "correlation_guardrails": correlations,
                "correlation_guardrails_pass": all(
                    gate["pass"] for gate in correlations.values()
                ),
                "calibration": calibration,
                "subgroups": subgroup_rows,
                "subgroup_reversal_pass": subgroup_pass,
                "fold_pass": fold_pass,
            }
        )

    pooled_surfaces = {
        model: pl.concat(frames, how="vertical_relaxed")
        for model, frames in pooled.items()
    }
    pooled_metrics = {
        model: {
            view: summarize_scoring_surface(surface, weighting=view)
            for view in ("player", "pa")
        }
        for model, surface in pooled_surfaces.items()
    }
    pooled_gates: dict[str, object] = {}
    for view in ("player", "pa"):
        rows: dict[str, object] = {}
        for metric in PRIMARY_METRICS:
            baseline_id, baseline = strongest_baseline(
                {model: pooled_metrics[model][view] for model in BASELINES}, metric
            )
            candidate = float(pooled_metrics[CANDIDATE][view][metric])
            relative = (baseline - candidate) / baseline
            rows[metric] = {
                "candidate": candidate,
                "baseline_id": baseline_id,
                "baseline": baseline,
                "relative_improvement": relative,
                "required": POOLED_RELATIVE_MINIMUM[metric],
                "pass": relative >= POOLED_RELATIVE_MINIMUM[metric],
            }
        pooled_gates[view] = {
            "metrics": rows,
            "pass": all(row["pass"] for row in rows.values()),
        }
    development_pass = (
        all(fold["fold_pass"] for fold in fold_reports)
        and all(view["pass"] for view in pooled_gates.values())
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2f_H0_disclosed_validation_comparison",
        "status": "passed" if development_pass else "failed",
        "candidate_scored": True,
        "development_gate_pass": development_pass,
        "production_promotion_made": False,
        "post_result_retuning_authorized": False,
        "protected_confirmation_opened": False,
        "contract_sha256": sha256_file(args.contract),
        "folds": fold_reports,
        "pooled_metrics": pooled_metrics,
        "pooled_relative_gates": pooled_gates,
        "next_gate": (
            "review_pass_before_separate_H1_or_protected_confirmation_authorization"
            if development_pass
            else "document_final_H0_failure_and_stop_without_H1_tracking_stage3_or_WAR"
        ),
    }
    output = args.report_root / "report.json"
    _atomic_json(output, report)
    print(
        json.dumps(
            {
                "report": str(output),
                "status": report["status"],
                "development_gate_pass": development_pass,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
