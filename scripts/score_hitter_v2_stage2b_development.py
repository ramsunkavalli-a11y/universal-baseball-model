#!/usr/bin/env python3
"""Fit and score the pre-registered Hitter v2 Stage 2b candidate ladder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_stage2b import (
    NodeOffsetFit,
    apply_node_calibration,
    apply_shape_residual,
    fit_node_calibration,
    fit_shape_residual,
)
from universal_baseball.hitter_v2_stage2b_validation import (
    LEVEL_SUPPORT_PA,
    LEVEL_SUPPORT_PLAYERS,
    calibration_improvement_gate,
    pooled_prediction_gate,
    pooled_woba_calibration,
    proper_score_gate,
    richer_ablation_gate,
    supported_level_reversal_gate,
)
from universal_baseball.hitter_v2_validation import (
    build_player_scoring_surface,
    summarize_scoring_surface,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
SELECTION_FOLDS = ("V2023", "V2024")
BASELINES = ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200")
CANDIDATES = (
    "D0_NODE_CALIBRATED_C0",
    "D1_TRAJECTORY_RESIDUAL",
    "D2_DIRECTION_TRAJECTORY_RESIDUAL",
)
MODES = {
    "D1_TRAJECTORY_RESIDUAL": "trajectory",
    "D2_DIRECTION_TRAJECTORY_RESIDUAL": "direction_trajectory",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prediction-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--feature-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2b-unscored/tables"),
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2b-development-contract.json"),
    )
    parser.add_argument(
        "--scoring-contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2b-scoring-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2b-development"),
    )
    return parser.parse_args()


def _prediction_path(root: Path, fold_id: str, model_id: str) -> Path:
    return root / fold_id.lower() / f"{model_id.lower()}_predictions.parquet"


def _feature_path(root: Path, fold_id: str, mode: str) -> Path:
    return root / fold_id.lower() / f"{mode}_features.parquet"


def _target_path(root: Path, fold_id: str) -> Path:
    return root / fold_id.lower() / "target_players.parquet"


def _fit_artifacts(
    fit: NodeOffsetFit,
    root: Path,
    *,
    fold_id: str,
    model_id: str,
) -> dict[str, object]:
    coefficient_artifact = write_canonical_parquet(
        fit.coefficients,
        root / fold_id.lower() / f"{model_id.lower()}_coefficients.parquet",
        table_name=f"hitter_v2_stage2b_{fold_id.lower()}_{model_id.lower()}_coefficients",
    ).as_record()
    return {"coefficients": coefficient_artifact, "fit_metrics": fit.metrics}


def _score_levels(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
) -> list[dict[str, object]]:
    overlap = target.join(
        predictions[BASELINES[0]].select("player_id"),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    rows: list[dict[str, object]] = []
    for level in sorted(str(value) for value in overlap["primary_target_level_group"].unique()):
        level_target = overlap.filter(pl.col("primary_target_level_group") == level)
        player_ids = [int(value) for value in level_target["player_id"].to_list()]
        players = level_target.height
        target_pa = int(level_target["hitter_talent_pa"].sum())
        supported = players >= LEVEL_SUPPORT_PLAYERS and target_pa >= LEVEL_SUPPORT_PA
        metrics = {
            model_id: {
                weighting: score_hitter_predictions(
                    frame.filter(pl.col("player_id").is_in(player_ids)),
                    level_target,
                    weighting=weighting,
                )
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
        }
        reversals: dict[str, object] = {}
        if supported:
            for candidate in CANDIDATES:
                reversals[candidate] = {
                    weighting: supported_level_reversal_gate(
                        metrics[candidate][weighting],
                        metrics[BASELINES[0]][weighting],
                        metrics[BASELINES[1]][weighting],
                    )
                    for weighting in ("player", "pa")
                }
        rows.append(
            {
                "level_group": level,
                "players": players,
                "target_pa": target_pa,
                "supported": supported,
                "metrics": metrics,
                "candidate_reversals": reversals,
            }
        )
    return rows


def _pooled_metrics(
    surfaces: dict[str, list[pl.DataFrame]],
) -> tuple[dict[str, dict[str, object]], dict[str, pl.DataFrame]]:
    pooled_surfaces = {
        model_id: pl.concat(
            [
                surface
                for surface in model_surfaces
                if str(surface["fold_id"][0]) in SELECTION_FOLDS
            ],
            how="vertical_relaxed",
        )
        for model_id, model_surfaces in surfaces.items()
    }
    metrics: dict[str, dict[str, object]] = {}
    for model_id, surface in pooled_surfaces.items():
        metrics[model_id] = {}
        for weighting in ("player", "pa"):
            metrics[model_id][weighting] = {
                **summarize_scoring_surface(surface, weighting=weighting),
                **pooled_woba_calibration(surface, weighting=weighting),
            }
    return metrics, pooled_surfaces


def main() -> int:
    args = _parse_args()
    prior_calibration: list[tuple[pl.DataFrame, pl.DataFrame]] = []
    prior_shapes: dict[
        str,
        list[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]],
    ] = {mode: [] for mode in MODES.values()}
    all_surfaces: dict[str, list[pl.DataFrame]] = {
        model_id: [] for model_id in (*BASELINES, "C0_NESTED_EB", *CANDIDATES)
    }
    fold_reports: list[dict[str, object]] = []

    for fold_id in FOLDS:
        b0_path = _prediction_path(args.prediction_root, fold_id, BASELINES[0])
        b1_path = _prediction_path(args.prediction_root, fold_id, BASELINES[1])
        c0_path = _prediction_path(args.prediction_root, fold_id, "C0_NESTED_EB")
        b0 = pl.read_parquet(b0_path)
        b1 = pl.read_parquet(b1_path)
        c0 = pl.read_parquet(c0_path)

        calibration_fit = fit_node_calibration(prior_calibration)
        d0 = apply_node_calibration(c0, calibration_fit)
        features = {
            mode: pl.read_parquet(_feature_path(args.feature_root, fold_id, mode))
            for mode in MODES.values()
        }
        shape_fits = {
            mode: fit_shape_residual(prior_shapes[mode], mode=mode)
            for mode in MODES.values()
        }
        d1 = apply_shape_residual(
            d0,
            features["trajectory"],
            shape_fits["trajectory"],
            model_id="D1_TRAJECTORY_RESIDUAL",
        )
        d2 = apply_shape_residual(
            d0,
            features["direction_trajectory"],
            shape_fits["direction_trajectory"],
            model_id="D2_DIRECTION_TRAJECTORY_RESIDUAL",
        )
        predictions = {
            BASELINES[0]: b0,
            BASELINES[1]: b1,
            "C0_NESTED_EB": c0,
            "D0_NODE_CALIBRATED_C0": d0,
            "D1_TRAJECTORY_RESIDUAL": d1,
            "D2_DIRECTION_TRAJECTORY_RESIDUAL": d2,
        }

        target_path = _target_path(args.target_root, fold_id)
        target = pl.read_parquet(target_path)
        metrics = {
            model_id: {
                weighting: score_hitter_predictions(frame, target, weighting=weighting)
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
        }
        for model_id, frame in predictions.items():
            all_surfaces[model_id].append(
                build_player_scoring_surface(
                    frame,
                    target,
                    model_id=model_id,
                    fold_id=fold_id,
                )
            )
        level_diagnostics = _score_levels(predictions, target)
        prediction_artifacts = {
            model_id: write_canonical_parquet(
                frame,
                args.report_root
                / "tables"
                / fold_id.lower()
                / f"{model_id.lower()}_predictions.parquet",
                table_name=f"hitter_v2_stage2b_{fold_id.lower()}_{model_id.lower()}_predictions",
            ).as_record()
            for model_id, frame in predictions.items()
            if model_id in CANDIDATES
        }
        fit_artifacts = {
            "D0_NODE_CALIBRATED_C0": _fit_artifacts(
                calibration_fit,
                args.report_root / "tables" / "fits",
                fold_id=fold_id,
                model_id="D0_NODE_CALIBRATED_C0",
            ),
            **{
                model_id: _fit_artifacts(
                    shape_fits[mode],
                    args.report_root / "tables" / "fits",
                    fold_id=fold_id,
                    model_id=model_id,
                )
                for model_id, mode in MODES.items()
            },
        }
        fold_reports.append(
            {
                "fold_id": fold_id,
                "fit_origin_count": len(prior_calibration),
                "metrics": metrics,
                "level_diagnostics": level_diagnostics,
                "prediction_artifacts": prediction_artifacts,
                "fit_artifacts": fit_artifacts,
                "source_hashes": {
                    "b0_predictions": sha256_file(b0_path),
                    "b1_predictions": sha256_file(b1_path),
                    "c0_predictions": sha256_file(c0_path),
                    "target": sha256_file(target_path),
                    **{
                        f"{mode}_features": sha256_file(
                            _feature_path(args.feature_root, fold_id, mode)
                        )
                        for mode in MODES.values()
                    },
                },
            }
        )

        prior_calibration.append((c0, target))
        prior_shapes["trajectory"].append((d0, target, features["trajectory"]))
        prior_shapes["direction_trajectory"].append(
            (d0, target, features["direction_trajectory"])
        )

    pooled_metrics, _ = _pooled_metrics(all_surfaces)
    candidate_gates: dict[str, object] = {}
    for candidate in CANDIDATES:
        per_fold = {}
        for fold in fold_reports:
            if fold["fold_id"] not in SELECTION_FOLDS:
                continue
            per_fold[fold["fold_id"]] = {
                weighting: proper_score_gate(
                    fold["metrics"][candidate][weighting],
                    fold["metrics"][BASELINES[0]][weighting],
                    fold["metrics"][BASELINES[1]][weighting],
                )
                for weighting in ("player", "pa")
            }
        level_pass = all(
            bool(gate["pass"])
            for fold in fold_reports
            if fold["fold_id"] in SELECTION_FOLDS
            for row in fold["level_diagnostics"]
            if row["supported"]
            for gate in row["candidate_reversals"][candidate].values()
        )
        pooled_gate = {
            weighting: pooled_prediction_gate(
                pooled_metrics[candidate][weighting],
                pooled_metrics[BASELINES[0]][weighting],
                pooled_metrics[BASELINES[1]][weighting],
            )
            for weighting in ("player", "pa")
        }
        calibration_gate = calibration_improvement_gate(
            pooled_metrics[candidate], pooled_metrics["C0_NESTED_EB"]
        )
        overall = (
            all(bool(gate["pass"]) for fold in per_fold.values() for gate in fold.values())
            and all(bool(gate["pass"]) for gate in pooled_gate.values())
            and bool(calibration_gate["pass"])
            and level_pass
        )
        candidate_gates[candidate] = {
            "per_fold_proper_scores": per_fold,
            "pooled_prediction": pooled_gate,
            "calibration_improvement_vs_c0": calibration_gate,
            "supported_level_reversal_pass": level_pass,
            "overall_development_pass": overall,
        }

    richer_ablations = {
        candidate: richer_ablation_gate(
            pooled_metrics[candidate], pooled_metrics["D0_NODE_CALIBRATED_C0"]
        )
        for candidate in (
            "D1_TRAJECTORY_RESIDUAL",
            "D2_DIRECTION_TRAJECTORY_RESIDUAL",
        )
    }
    eligible = []
    if candidate_gates["D0_NODE_CALIBRATED_C0"]["overall_development_pass"]:
        eligible.append("D0_NODE_CALIBRATED_C0")
    for candidate in (
        "D1_TRAJECTORY_RESIDUAL",
        "D2_DIRECTION_TRAJECTORY_RESIDUAL",
    ):
        if (
            candidate_gates[candidate]["overall_development_pass"]
            and richer_ablations[candidate]["pass"]
        ):
            eligible.append(candidate)
    selected = eligible[0] if eligible else None
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2b",
        "status": (
            "development_candidate_selected_for_confirmation_freeze"
            if selected is not None
            else "stage2b_candidates_failed_disclosed_development"
        ),
        "candidate_fit": True,
        "candidate_scored": True,
        "development_contract_sha256": sha256_file(args.contract),
        "scoring_contract_sha256": sha256_file(args.scoring_contract),
        "folds": fold_reports,
        "pooled_selection_fold_metrics": pooled_metrics,
        "candidate_gates": candidate_gates,
        "richer_ablations_vs_d0": richer_ablations,
        "eligible_candidates_in_simplicity_order": eligible,
        "selected_development_candidate": selected,
        "development_can_promote_to_production": False,
        "protected_2026_opened": False,
        "tracking_authorized": False,
        "stage3_authorized": False,
        "full_war_authorized": False,
        "next_step": (
            "freeze_confirmation_refit_and_scorer_then_stop_for_explicit_review"
            if selected is not None
            else "document_failure_and_stop_without_retuning_or_confirmation_access"
        ),
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"],
        "selected_development_candidate": selected,
        "candidate_gates": {
            candidate: gate["overall_development_pass"]
            for candidate, gate in candidate_gates.items()
        },
        "richer_ablations_vs_d0": {
            candidate: gate["pass"]
            for candidate, gate in richer_ablations.items()
        },
        "protected_2026_opened": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
