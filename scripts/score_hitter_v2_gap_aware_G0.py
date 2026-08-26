#!/usr/bin/env python3
"""Execute the frozen one-shot disclosed comparison for gap-aware G0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_stage2f_scoring import (
    CORRELATION_METRICS,
    PRIMARY_METRICS,
    primary_gate,
    strongest_baseline,
    subgroup_reversal_gate,
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
BASELINES = ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200", "C0_NESTED_EB")
CANDIDATE = "G0_GAP_AWARE_HISTORICAL_C0"
MODELS = (*BASELINES, CANDIDATE)
POOLED_MINIMUM = {
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
        default=Path("docs/hitter-v2-gap-aware-G0-scoring-contract.json"),
    )
    parser.add_argument(
        "--g0-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-gap-aware-G0-fit/tables"),
    )
    parser.add_argument(
        "--baseline-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation/tables"),
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
        default=Path("reports/generated/hitter-v2-gap-aware-G0-comparison/report.json"),
    )
    return parser.parse_args()


def _verify(contract: dict[str, object], runner: Path) -> None:
    if contract["status"] != "frozen_before_first_disclosed_G0_score":
        raise ValueError("G0 scoring contract is not frozen")
    if sha256_file(runner) != contract["runner_sha256"]:
        raise ValueError("G0 scoring runner changed after freeze")
    for boundary in (
        "post_result_retuning_authorized",
        "later_increment_fit_authorized",
        "protected_confirmation_access_authorized",
        "stage3_authorized",
        "full_war_authorized",
    ):
        if contract[boundary] is not False:
            raise ValueError(f"G0 scoring improperly opened {boundary}")
    for fold in FOLDS:
        for record in contract["folds"][fold]["inputs"]:
            path = Path(record["path"])
            if sha256_file(path) != record["sha256"]:
                raise ValueError(f"G0 scoring input changed: {path}")


def _correlation_gate(metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    rows = {}
    for metric in CORRELATION_METRICS:
        baseline_id = max(BASELINES, key=lambda model: (float(metrics[model][metric]), model))
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
    prediction: pl.DataFrame,
    target: pl.DataFrame,
    surface: pl.DataFrame,
    metrics: dict[str, dict[str, object]],
) -> dict[str, object]:
    components = {
        view: terminal_component_calibration(prediction, target, weighting=view)
        for view in ("player", "pa")
    }
    deciles = predicted_woba_decile_calibration(surface)
    levels = level_aggregate_calibration(prediction, target)
    woba_pass = all(
        abs(float(metrics[view]["woba_calibration_intercept"])) <= 0.005
        and 0.90 <= float(metrics[view]["woba_calibration_slope"]) <= 1.10
        for view in ("player", "pa")
    )
    component_pass = all(
        row["slope_guardrail_pass"] is not False
        for group in components.values()
        for row in group
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
    predictions: dict[str, pl.DataFrame], target: pl.DataFrame, labels: pl.DataFrame
) -> tuple[list[dict[str, object]], bool]:
    definitions = {
        "level": ("primary_target_level_group", 100, 10_000),
        "age": ("age_band", 50, 5_000),
        "evidence": ("evidence_band", 50, 5_000),
        "movement": ("movement_band", 50, 5_000),
        "K": ("k_band", 50, 5_000),
        "power": ("hr_power_band", 50, 5_000),
    }
    rows = []
    all_pass = True
    for dimension, (column, minimum_players, minimum_pa) in definitions.items():
        for label in sorted(str(value) for value in labels[column].drop_nulls().unique()):
            ids = labels.filter(pl.col(column) == label)["player_id"].to_list()
            scores = {model: score_subgroup(frame, target, ids) for model, frame in predictions.items()}
            players = int(scores[CANDIDATE]["players"])
            target_pa = int(scores[CANDIDATE]["target_pa"])
            supported = players >= minimum_players and target_pa >= minimum_pa
            gates = {}
            if supported:
                gates = {
                    view: subgroup_reversal_gate(
                        scores[CANDIDATE]["metrics"][view],
                        {model: scores[model]["metrics"][view] for model in BASELINES},
                    )
                    for view in ("player", "pa")
                }
                all_pass = all_pass and all(gate["pass"] for gate in gates.values())
            rows.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "players": players,
                    "target_pa": target_pa,
                    "supported": supported,
                    "scores": scores,
                    "gates": gates,
                }
            )
    return rows, all_pass


def _pooled_gate(metrics: dict[str, dict[str, object]]) -> dict[str, object]:
    comparisons = {}
    for view in ("player", "pa"):
        comparisons[view] = {}
        for metric in PRIMARY_METRICS:
            baseline_id, baseline = strongest_baseline(
                {model: metrics[model][view] for model in BASELINES}, metric
            )
            candidate = float(metrics[CANDIDATE][view][metric])
            relative = (baseline - candidate) / baseline
            comparisons[view][metric] = {
                "candidate": candidate,
                "baseline_id": baseline_id,
                "baseline": baseline,
                "relative_improvement": relative,
                "minimum": POOLED_MINIMUM[metric],
                "pass": relative >= POOLED_MINIMUM[metric],
            }
    return {
        "comparisons": comparisons,
        "pass": all(row["pass"] for view in comparisons.values() for row in view.values()),
    }


def main() -> int:
    args = _args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    _verify(contract, Path(__file__))
    fold_reports = []
    pooled = {model: [] for model in MODELS}
    filenames = {
        "B0_ONE_YEAR_EB": "b0_one_year_eb_predictions.parquet",
        "B1_MARCEL_345_K1200": "b1_marcel_345_k1200_predictions.parquet",
        "C0_NESTED_EB": "c0_nested_eb_predictions.parquet",
    }
    for fold in FOLDS:
        slug = fold.lower()
        predictions = {
            model: pl.read_parquet(args.baseline_root / slug / filename)
            for model, filename in filenames.items()
        }
        predictions[CANDIDATE] = pl.read_parquet(
            args.g0_root / slug / "g0_unscored_predictions.parquet"
        )
        target = pl.read_parquet(args.prescore_root / slug / "target_players.parquet")
        training = pl.read_parquet(args.prescore_root / slug / "training_player_league_seasons.parquet")
        ages = pl.read_parquet(args.age_root / slug / "forecast_player_ages.parquet")
        cohorts = [set(frame["player_id"].to_list()) for frame in predictions.values()]
        if any(cohort != cohorts[0] for cohort in cohorts[1:]):
            raise ValueError(f"{fold} comparison cohorts differ")
        metrics = {
            model: {
                view: score_hitter_predictions(frame, target, weighting=view)
                for view in ("player", "pa")
            }
            for model, frame in predictions.items()
        }
        surfaces = {
            model: build_player_scoring_surface(frame, target, model_id=model, fold_id=fold)
            for model, frame in predictions.items()
        }
        for model, surface in surfaces.items():
            pooled[model].append(surface)
        primary = {
            view: primary_gate(
                metrics[CANDIDATE][view],
                {model: metrics[model][view] for model in BASELINES},
            )
            for view in ("player", "pa")
        }
        correlations = {
            view: _correlation_gate({model: metrics[model][view] for model in MODELS})
            for view in ("player", "pa")
        }
        subgroup_rows, subgroup_pass = _subgroups(
            predictions, target, build_evaluation_subgroups(training, target, ages)
        )
        calibration = _calibration(
            predictions[CANDIDATE], target, surfaces[CANDIDATE], metrics[CANDIDATE]
        )
        fold_reports.append(
            {
                "fold_id": fold,
                "metrics": metrics,
                "primary_gate": primary,
                "primary_gate_pass": all(gate["pass"] for gate in primary.values()),
                "correlation_gate": correlations,
                "correlation_gate_pass": all(gate["pass"] for gate in correlations.values()),
                "calibration": calibration,
                "subgroups": subgroup_rows,
                "subgroup_reversal_gate_pass": subgroup_pass,
                "identical_cohort": True,
            }
        )
    pooled_surfaces = {
        model: pl.concat(frames, how="vertical_relaxed") for model, frames in pooled.items()
    }
    pooled_metrics = {
        model: {
            view: summarize_scoring_surface(surface, weighting=view)
            for view in ("player", "pa")
        }
        for model, surface in pooled_surfaces.items()
    }
    pooled_result = _pooled_gate(pooled_metrics)
    promotion_pass = (
        all(row["primary_gate_pass"] for row in fold_reports)
        and all(row["correlation_gate_pass"] for row in fold_reports)
        and all(row["calibration"]["pass"] for row in fold_reports)
        and all(row["subgroup_reversal_gate_pass"] for row in fold_reports)
        and pooled_result["pass"]
    )
    report = {
        "schema_version": "0.1",
        "program": "hitter_v2",
        "stage": "G0_one_shot_disclosed_comparison",
        "status": "G0_passed" if promotion_pass else "G0_failed_final",
        "folds": fold_reports,
        "pooled_metrics": pooled_metrics,
        "pooled_gate": pooled_result,
        "promotion_pass": promotion_pass,
        "candidate_failure_final": not promotion_pass,
        "post_result_retuning_authorized": False,
        "later_increment_fit_authorized": promotion_pass,
        "protected_confirmation_opened": False,
        "stage3_authorized": False,
        "full_war_authorized": False,
        "next_gate": (
            "review_then_separately_authorize_G1_or_G2_target_free_fit"
            if promotion_pass
            else "document_failure_and_require_a_distinct_preregistered_candidate"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "promotion_pass": promotion_pass,
                "fold_primary_pass": {
                    row["fold_id"]: row["primary_gate_pass"] for row in fold_reports
                },
                "pooled_gate_pass": pooled_result["pass"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
