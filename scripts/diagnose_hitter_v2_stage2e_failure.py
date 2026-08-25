#!/usr/bin/env python3
"""Diagnose frozen C0, Marcel, and J0R disclosed results without model fitting."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_validation import (
    build_evaluation_subgroups,
    score_subgroup,
    terminal_component_calibration,
)
from universal_baseball.storage import sha256_file


FOLDS = ("V2022", "V2023", "V2024")
MODELS = ("B1_MARCEL_345_K1200", "C0_NESTED_EB", "J0R_FIXED_INFORMATION_SHRINKAGE")
DIMENSIONS = {
    "level": "primary_target_level_group",
    "age": "age_band",
    "evidence": "evidence_band",
    "movement": "movement_band",
    "K": "k_band",
    "power": "hr_power_band",
}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-scoring-contract.json"),
    )
    parser.add_argument(
        "--comparison",
        type=Path,
        default=Path("docs/hitter-v2-stage2e-comparison-result.json"),
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
    )
    parser.add_argument(
        "--fit-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-j0r-fit/tables"),
    )
    parser.add_argument(
        "--prescore-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-prescore/tables"),
    )
    parser.add_argument(
        "--age-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-age/tables"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2e-postmortem/report.json"),
    )
    return parser.parse_args()


def component_diagnostics(
    predictions: pl.DataFrame,
    target: pl.DataFrame,
    *,
    weighting: str,
) -> list[dict[str, object]]:
    """Return marginal outcome bias, binary proper scores, and calibration."""

    joined = target.join(predictions, on="player_id", how="inner", validate="1:1")
    pa = joined["hitter_talent_pa"].to_numpy().astype(float)
    weights = np.ones(joined.height) if weighting == "player" else pa
    calibration = {
        row["outcome"]: row
        for row in terminal_component_calibration(
            predictions, target, weighting=weighting
        )
    }
    rows = []
    for outcome in HITTER_TALENT_OUTCOMES:
        actual = joined[outcome].to_numpy().astype(float) / pa
        predicted = joined[f"p_{outcome}"].to_numpy().astype(float)
        actual_rate = float(np.average(actual, weights=weights))
        predicted_rate = float(np.average(predicted, weights=weights))
        probability = np.clip(predicted, 1e-12, 1.0 - 1e-12)
        binary_log_loss = float(
            np.average(
                -(
                    actual * np.log(probability)
                    + (1.0 - actual) * np.log(1.0 - probability)
                ),
                weights=weights,
            )
        )
        rows.append(
            {
                "outcome": outcome,
                "actual_rate": actual_rate,
                "predicted_rate": predicted_rate,
                "bias": predicted_rate - actual_rate,
                "absolute_bias": abs(predicted_rate - actual_rate),
                "binary_log_loss": binary_log_loss,
                "binary_brier": float(
                    np.average((predicted - actual) ** 2, weights=weights)
                ),
                "calibration_intercept": calibration[outcome]["intercept"],
                "calibration_slope": calibration[outcome]["slope"],
                "calibration_slope_pass": calibration[outcome]["slope_guardrail_pass"],
            }
        )
    return rows


def _prediction_paths(base: Path, fit: Path, fold: str) -> dict[str, Path]:
    slug = fold.lower()
    return {
        "B1_MARCEL_345_K1200": base / slug / "b1_marcel_345_k1200_predictions.parquet",
        "C0_NESTED_EB": base / slug / "c0_nested_eb_predictions.parquet",
        "J0R_FIXED_INFORMATION_SHRINKAGE": fit
        / slug
        / "j0r_fixed_information_shrinkage_predictions.parquet",
    }


def _subgroup_rows(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    subgroups: pl.DataFrame,
) -> list[dict[str, object]]:
    rows = []
    for dimension, column in DIMENSIONS.items():
        for label in sorted(
            str(value) for value in subgroups[column].drop_nulls().unique()
        ):
            ids = subgroups.filter(pl.col(column) == label)["player_id"].to_list()
            scores = {
                model: score_subgroup(frame, target, ids)
                for model, frame in predictions.items()
            }
            players = int(scores[MODELS[0]]["players"])
            target_pa = int(scores[MODELS[0]]["target_pa"])
            supported = players >= (
                100 if dimension == "level" else 50
            ) and target_pa >= (10_000 if dimension == "level" else 5_000)
            deltas = {}
            if supported:
                for model in ("C0_NESTED_EB", "J0R_FIXED_INFORMATION_SHRINKAGE"):
                    deltas[model] = {
                        weighting: {
                            metric: float(scores[model]["metrics"][weighting][metric])
                            - float(
                                scores["B1_MARCEL_345_K1200"]["metrics"][weighting][
                                    metric
                                ]
                            )
                            for metric in (
                                "terminal_log_loss",
                                "terminal_brier_score",
                                "woba_rmse",
                                "runs_per_600_rmse",
                            )
                        }
                        for weighting in ("player", "pa")
                    }
            rows.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "players": players,
                    "target_pa": target_pa,
                    "supported": supported,
                    "model_minus_Marcel": deltas,
                }
            )
    return rows


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    comparison = json.loads(args.comparison.read_text(encoding="utf-8"))
    if comparison["candidate_failure_final"] is not True:
        raise ValueError("postmortem requires a final frozen candidate failure")
    folds = []
    pooled_predictions = {model: [] for model in MODELS}
    pooled_targets = []
    for fold in FOLDS:
        slug = fold.lower()
        frozen = contract["folds"][fold]
        paths = _prediction_paths(args.baseline_root, args.fit_root, fold)
        for model, path in paths.items():
            if sha256_file(path) != frozen["prediction_sha256"][model]:
                raise ValueError(f"{fold} {model} changed after frozen scoring")
        target_path = args.prescore_root / slug / "target_players.parquet"
        training_path = (
            args.prescore_root / slug / "training_player_league_seasons.parquet"
        )
        age_path = args.age_root / slug / "forecast_player_ages.parquet"
        if sha256_file(target_path) != frozen["target_sha256"]:
            raise ValueError(f"{fold} target changed")
        predictions = {model: pl.read_parquet(path) for model, path in paths.items()}
        target = pl.read_parquet(target_path)
        training = pl.read_parquet(training_path)
        ages = pl.read_parquet(age_path)
        for model, frame in predictions.items():
            pooled_predictions[model].append(
                frame.with_columns(pl.lit(fold).alias("fold_id"))
            )
        pooled_targets.append(target.with_columns(pl.lit(fold).alias("fold_id")))
        folds.append(
            {
                "fold_id": fold,
                "overall": {
                    model: {
                        weighting: score_hitter_predictions(
                            frame, target, weighting=weighting
                        )
                        for weighting in ("player", "pa")
                    }
                    for model, frame in predictions.items()
                },
                "components": {
                    model: {
                        weighting: component_diagnostics(
                            frame, target, weighting=weighting
                        )
                        for weighting in ("player", "pa")
                    }
                    for model, frame in predictions.items()
                },
                "subgroups": _subgroup_rows(
                    predictions,
                    target,
                    build_evaluation_subgroups(training, target, ages),
                ),
            }
        )
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "stage2e_failure_postmortem",
        "status": "diagnostic_only_no_candidate_selection",
        "comparison_result_sha256": sha256_file(args.comparison),
        "scoring_contract_sha256": sha256_file(args.contract),
        "folds": folds,
        "protected_2026_opened": False,
        "candidate_fit": False,
        "candidate_scored": False,
        "post_result_rescue": False,
        "next_gate": "summarize_failure_patterns_and_freeze_distinct_candidate_contract",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
