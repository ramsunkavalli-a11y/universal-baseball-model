#!/usr/bin/env python3
"""Fit and score only the pre-registered Stage 2c E1 candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_stage2b_validation import (
    LEVEL_SUPPORT_PA,
    LEVEL_SUPPORT_PLAYERS,
    pooled_woba_calibration,
    proper_score_gate,
    supported_level_reversal_gate,
)
from universal_baseball.hitter_v2_stage2c import (
    E1_MODEL_ID,
    HR_MODE,
    Stage2cFit,
    apply_stage2c_residual,
    fit_stage2c_residual,
)
from universal_baseball.hitter_v2_stage2c_validation import (
    hr_increment_gate,
    pooled_rate_gate,
    score_hr_conditional,
)
from universal_baseball.hitter_v2_validation import (
    build_player_scoring_surface,
    summarize_scoring_surface,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
SELECTION_FOLDS = ("V2023", "V2024")
BASELINES = ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200")
E0_MODEL_ID = "C0_NESTED_EB"
EVIDENCE_BANDS = (
    ("none", 0.0, 0.0),
    ("1_24", 0.0, 25.0),
    ("25_49", 25.0, 50.0),
    ("50_99", 50.0, 100.0),
    ("100_199", 100.0, 200.0),
    ("200_plus", 200.0, float("inf")),
)
LEVEL_ORDER = {
    "complex": 0,
    "rookie": 0,
    "A": 1,
    "High-A": 2,
    "AA": 3,
    "AAA": 4,
    "MLB": 5,
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
        default=Path("reports/generated/hitter-v2-stage2c-unscored/tables"),
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2c-development-contract.json"),
    )
    parser.add_argument(
        "--scoring-contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2c-e1-scoring-contract.json"),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2c-e1-development"),
    )
    return parser.parse_args()


def _prediction_path(root: Path, fold_id: str, model_id: str) -> Path:
    return root / fold_id.lower() / f"{model_id.lower()}_predictions.parquet"


def _target_path(root: Path, fold_id: str) -> Path:
    return root / fold_id.lower() / "target_players.parquet"


def _feature_path(root: Path, fold_id: str) -> Path:
    return root / fold_id.lower() / f"{HR_MODE}.parquet"


def _fit_artifact(
    fit: Stage2cFit,
    root: Path,
    *,
    fold_id: str,
) -> dict[str, object]:
    artifact = write_canonical_parquet(
        fit.coefficients,
        root / "fits" / fold_id.lower() / "e1_coefficients.parquet",
        table_name=f"hitter_v2_stage2c_{fold_id.lower()}_e1_coefficients",
    ).as_record()
    return {"coefficients": artifact, "fit_metrics": fit.metrics}


def _pooled_metrics(
    surfaces: dict[str, list[pl.DataFrame]],
) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for model_id, frames in surfaces.items():
        pooled = pl.concat(
            [
                frame
                for frame in frames
                if str(frame["fold_id"][0]) in SELECTION_FOLDS
            ],
            how="vertical_relaxed",
        )
        result[model_id] = {
            weighting: {
                **summarize_scoring_surface(pooled, weighting=weighting),
                **pooled_woba_calibration(pooled, weighting=weighting),
            }
            for weighting in ("player", "pa")
        }
    return result


def _level_diagnostics(
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
    levels = sorted(str(value) for value in overlap["primary_target_level_group"].unique())
    for level in levels:
        level_target = overlap.filter(pl.col("primary_target_level_group") == level)
        ids = level_target["player_id"].to_list()
        players = level_target.height
        target_pa = int(level_target["hitter_talent_pa"].sum())
        supported = players >= LEVEL_SUPPORT_PLAYERS and target_pa >= LEVEL_SUPPORT_PA
        metrics = {
            model_id: {
                weighting: score_hitter_predictions(
                    frame.filter(pl.col("player_id").is_in(ids)),
                    level_target,
                    weighting=weighting,
                )
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
        }
        reversal = (
            {
                weighting: supported_level_reversal_gate(
                    metrics[E1_MODEL_ID][weighting],
                    metrics[BASELINES[0]][weighting],
                    metrics[BASELINES[1]][weighting],
                )
                for weighting in ("player", "pa")
            }
            if supported
            else {}
        )
        rows.append(
            {
                "level_group": level,
                "players": players,
                "target_pa": target_pa,
                "supported": supported,
                "metrics": metrics,
                "e1_reversal": reversal,
            }
        )
    return rows


def _score_diagnostic_group(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    ids: list[int],
) -> dict[str, object]:
    group_target = target.filter(pl.col("player_id").is_in(ids))
    return {
        "players": group_target.height,
        "target_pa": int(group_target["hitter_talent_pa"].sum()),
        "terminal_metrics": {
            model_id: {
                weighting: score_hitter_predictions(
                    frame.filter(pl.col("player_id").is_in(ids)),
                    group_target,
                    weighting=weighting,
                )
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
            if model_id in (E0_MODEL_ID, E1_MODEL_ID)
        },
        "hr_conditional_metrics": {
            model_id: {
                weighting: score_hr_conditional(
                    frame.filter(pl.col("player_id").is_in(ids)),
                    group_target,
                    weighting=weighting,
                )
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
            if model_id in (E0_MODEL_ID, E1_MODEL_ID)
        },
    }


def _auxiliary_diagnostics(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    features: pl.DataFrame,
) -> dict[str, object]:
    cohort = target.select(
        "player_id", "hitter_talent_pa", "primary_target_level_group"
    ).join(
        features.select(
            "player_id",
            "shape_latest_level_group",
            "shape_evidence_offb_per_contact",
            "shape_evidence_pull_offb_per_offb",
        ),
        on="player_id",
        how="inner",
        validate="1:1",
    ).with_columns(
        pl.min_horizontal(
            "shape_evidence_offb_per_contact",
            "shape_evidence_pull_offb_per_offb",
        ).alias("joint_shape_evidence")
    )
    evidence: dict[str, object] = {}
    for label, lower, upper in EVIDENCE_BANDS:
        if label == "none":
            group = cohort.filter(pl.col("joint_shape_evidence") <= 0.0)
        else:
            lower_bound = (
                pl.col("joint_shape_evidence") > lower
                if lower == 0.0
                else pl.col("joint_shape_evidence") >= lower
            )
            group = cohort.filter(
                lower_bound & (pl.col("joint_shape_evidence") < upper)
            )
        if group.height:
            evidence[label] = _score_diagnostic_group(
                predictions, target, group["player_id"].to_list()
            )

    transitions: dict[str, list[int]] = {
        "same_level": [],
        "promotion": [],
        "demotion": [],
        "unclassified": [],
    }
    for row in cohort.iter_rows(named=True):
        prior = LEVEL_ORDER.get(str(row["shape_latest_level_group"]))
        future = LEVEL_ORDER.get(str(row["primary_target_level_group"]))
        if prior is None or future is None:
            label = "unclassified"
        elif future > prior:
            label = "promotion"
        elif future < prior:
            label = "demotion"
        else:
            label = "same_level"
        transitions[label].append(int(row["player_id"]))
    transition_metrics = {
        label: _score_diagnostic_group(predictions, target, ids)
        for label, ids in transitions.items()
        if ids
    }
    supported = cohort.filter(pl.col("joint_shape_evidence") > 0.0)
    return {
        "coverage": {
            "evaluation_players": cohort.height,
            "shape_supported_players": supported.height,
            "exact_fallback_players": cohort.height - supported.height,
            "shape_supported_rate": supported.height / cohort.height,
        },
        "evidence_bands_non_gating": evidence,
        "level_transitions_non_gating": transition_metrics,
    }


def main() -> int:
    args = _parse_args()
    development_contract = json.loads(args.contract.read_text(encoding="utf-8"))
    scoring_contract = json.loads(args.scoring_contract.read_text(encoding="utf-8"))
    if development_contract.get("contract_schema_version") != "0.4":
        raise ValueError("E1 scorer requires Stage 2c development schema 0.4")
    if scoring_contract.get("contract_id") != "hitter_v2_stage2c_e1_scoring_v1":
        raise ValueError("unexpected Stage 2c E1 scoring contract")

    prior_origins: list[tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]] = []
    surfaces: dict[str, list[pl.DataFrame]] = {
        model_id: [] for model_id in (*BASELINES, E0_MODEL_ID, E1_MODEL_ID)
    }
    fold_reports: list[dict[str, object]] = []
    for fold_id in FOLDS:
        paths = {
            model_id: _prediction_path(args.prediction_root, fold_id, model_id)
            for model_id in (*BASELINES, E0_MODEL_ID)
        }
        source_predictions = {
            model_id: pl.read_parquet(path) for model_id, path in paths.items()
        }
        features_path = _feature_path(args.feature_root, fold_id)
        features = pl.read_parquet(features_path)
        fit = fit_stage2c_residual(prior_origins, mode=HR_MODE)
        e1 = apply_stage2c_residual(
            source_predictions[E0_MODEL_ID],
            features,
            fit,
            model_id=E1_MODEL_ID,
        )
        predictions = {**source_predictions, E1_MODEL_ID: e1}
        target_path = _target_path(args.target_root, fold_id)
        target = pl.read_parquet(target_path)
        metrics = {
            model_id: {
                weighting: score_hitter_predictions(frame, target, weighting=weighting)
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
        }
        hr_metrics = {
            model_id: {
                weighting: score_hr_conditional(frame, target, weighting=weighting)
                for weighting in ("player", "pa")
            }
            for model_id, frame in predictions.items()
            if model_id in (E0_MODEL_ID, E1_MODEL_ID)
        }
        for model_id, frame in predictions.items():
            surfaces[model_id].append(
                build_player_scoring_surface(
                    frame,
                    target,
                    model_id=model_id,
                    fold_id=fold_id,
                )
            )
        prediction_artifact = write_canonical_parquet(
            e1,
            args.report_root / "tables" / fold_id.lower() / "e1_predictions.parquet",
            table_name=f"hitter_v2_stage2c_{fold_id.lower()}_e1_predictions",
        ).as_record()
        fold_reports.append(
            {
                "fold_id": fold_id,
                "fit_origin_count": len(prior_origins),
                "metrics": metrics,
                "hr_conditional_metrics": hr_metrics,
                "level_diagnostics": _level_diagnostics(predictions, target),
                "auxiliary_diagnostics": _auxiliary_diagnostics(
                    predictions, target, features
                ),
                "prediction_artifact": prediction_artifact,
                "fit_artifact": _fit_artifact(fit, args.report_root / "tables", fold_id=fold_id),
                "source_hashes": {
                    **{f"{model_id}_predictions": sha256_file(path) for model_id, path in paths.items()},
                    "features": sha256_file(features_path),
                    "target": sha256_file(target_path),
                },
            }
        )
        prior_origins.append((source_predictions[E0_MODEL_ID], target, features))

    pooled = _pooled_metrics(surfaces)
    per_fold_gates: dict[str, object] = {}
    for fold in fold_reports:
        if fold["fold_id"] not in SELECTION_FOLDS:
            continue
        per_fold_gates[str(fold["fold_id"])] = {
            weighting: {
                "terminal_proper_scores": proper_score_gate(
                    fold["metrics"][E1_MODEL_ID][weighting],
                    fold["metrics"][BASELINES[0]][weighting],
                    fold["metrics"][BASELINES[1]][weighting],
                ),
                "hr_conditional": hr_increment_gate(
                    fold["hr_conditional_metrics"][E1_MODEL_ID][weighting],
                    fold["hr_conditional_metrics"][E0_MODEL_ID][weighting],
                ),
            }
            for weighting in ("player", "pa")
        }
    pooled_rate_gates = {
        weighting: pooled_rate_gate(
            pooled[E1_MODEL_ID][weighting],
            pooled[BASELINES[0]][weighting],
            pooled[BASELINES[1]][weighting],
        )
        for weighting in ("player", "pa")
    }
    supported_level_pass = all(
        bool(gate["pass"])
        for fold in fold_reports
        if fold["fold_id"] in SELECTION_FOLDS
        for level in fold["level_diagnostics"]
        if level["supported"]
        for gate in level["e1_reversal"].values()
    )
    overall_pass = (
        all(
            bool(view[gate]["pass"])
            for fold in per_fold_gates.values()
            for view in fold.values()
            for gate in ("terminal_proper_scores", "hr_conditional")
        )
        and all(bool(gate["pass"]) for gate in pooled_rate_gates.values())
        and supported_level_pass
    )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "2c_e1",
        "status": "e1_passed_disclosed_development" if overall_pass else "e1_failed_disclosed_development",
        "candidate_fit": True,
        "candidate_scored": True,
        "development_contract_sha256": sha256_file(args.contract),
        "scoring_contract_sha256": sha256_file(args.scoring_contract),
        "folds": fold_reports,
        "pooled_selection_fold_metrics": pooled,
        "e1_gate": {
            "per_fold": per_fold_gates,
            "pooled_rate": pooled_rate_gates,
            "supported_level_reversal_pass": supported_level_pass,
            "overall_development_pass": overall_pass,
        },
        "e2_authorized": overall_pass,
        "protected_2026_opened": False,
        "tracking_authorized": False,
        "stage3_authorized": False,
        "full_war_authorized": False,
        "next_step": "freeze_e2_scorer_before_evaluation" if overall_pass else "document_e1_failure_and_stop_without_rescue_or_retuning",
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    (args.report_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "overall_development_pass": overall_pass,
                "e2_authorized": overall_pass,
                "protected_2026_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
