#!/usr/bin/env python3
"""Run one-pass disclosed validation for frozen Hitter v2 PBP candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_hitter_v2_stage2_c1_prescore import (
    _historical_ages,
    _target_age_contexts,
)
from select_hitter_v2_stage2_c1_adjustments import _component_parameters
from universal_baseball.chadwick import read_chadwick_people_archive
from universal_baseball.hitter_v2_c1 import (
    estimate_player_gidp_rates,
    fit_c1_adjustments,
    predict_c1_hierarchical_pbp,
)
from universal_baseball.hitter_v2_evaluation import score_hitter_predictions
from universal_baseball.hitter_v2_model import (
    predict_b0_one_year_eb,
    predict_b1_marcel_345_k1200,
    predict_c0_nested_eb,
)
from universal_baseball.hitter_v2_validation import (
    PRIMARY_LOSS_METRICS,
    build_evaluation_subgroups,
    build_player_scoring_surface,
    fold_primary_gate,
    level_aggregate_calibration,
    paired_player_bootstrap_rmse_delta,
    predicted_woba_decile_calibration,
    score_subgroup,
    strongest_simple_baseline,
    subgroup_reversal_gate,
    summarize_scoring_surface,
    terminal_component_calibration,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


FOLDS = ("V2022", "V2023", "V2024")
CANDIDATES = ("C0_NESTED_EB", "C1_HIERARCHICAL_PBP")
POOLED_RELATIVE_THRESHOLDS = {
    "terminal_log_loss": 0.0025,
    "terminal_brier_score": 0.0025,
    "woba_mae": 0.005,
    "woba_rmse": 0.01,
    "runs_per_600_mae": 0.005,
    "runs_per_600_rmse": 0.01,
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--component-selection",
        type=Path,
        default=Path("docs/hitter-v2-stage2-component-selection-result.json"),
    )
    parser.add_argument(
        "--adjustment-selection",
        type=Path,
        default=Path("docs/hitter-v2-stage2-c1-adjustment-selection-result.json"),
    )
    parser.add_argument(
        "--player-games",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage1-universal/tables/"
            "hitter_v2_player_game_outcomes_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--park-context",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-park-context/tables/"
            "hitter_v2_player_game_park_context_2021_2023.parquet"
        ),
    )
    parser.add_argument(
        "--gidp-history",
        type=Path,
        default=Path(
            "reports/generated/hitter-v2-stage2-gidp-opportunities/tables/"
            "hitter_v2_player_game_gidp_opportunities_2021_2024.parquet"
        ),
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
        "--register-archive",
        type=Path,
        default=Path(
            "data/quarantine/hitter-v2-stage2-age/"
            "register-2e8e73355f9c77b963115377bd98c784cfeec10f.zip"
        ),
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=Path("reports/generated/hitter-v2-stage2-final-validation"),
    )
    return parser.parse_args()


def _adjustment_parameters(selection: dict[str, object], fold_id: str) -> dict[str, float]:
    return {
        key: float(value)
        for key, value in selection["folds"][fold_id]["selected"].items()
        if key != "event_log_loss"
    }


def _subgroup_diagnostics(
    predictions: dict[str, pl.DataFrame],
    target: pl.DataFrame,
    subgroups: pl.DataFrame,
) -> tuple[list[dict[str, object]], bool]:
    definitions = {
        "level": ("primary_target_level_group", None),
        "age": ("age_band", None),
        "evidence": ("evidence_band", None),
        "movement": ("movement_band", None),
        "k": ("k_band", {"low_K", "high_K"}),
        "power": ("hr_power_band", {"low_power", "high_power"}),
    }
    rows = []
    all_supported_pass = True
    for dimension, (column, allowed) in definitions.items():
        labels = sorted(str(value) for value in subgroups[column].unique())
        if allowed is not None:
            labels = [label for label in labels if label in allowed]
        for label in labels:
            player_ids = [
                int(value)
                for value in subgroups.filter(pl.col(column) == label)["player_id"].to_list()
            ]
            model_scores = {
                model_id: score_subgroup(frame, target, player_ids)
                for model_id, frame in predictions.items()
            }
            level_support = dimension == "level"
            players = int(model_scores["B0_ONE_YEAR_EB"]["players"])
            target_pa = int(model_scores["B0_ONE_YEAR_EB"]["target_pa"])
            supported = (
                players >= (100 if level_support else 50)
                and target_pa >= (10_000 if level_support else 5_000)
            )
            reversals = {}
            if supported:
                for candidate in CANDIDATES:
                    reversals[candidate] = {
                        weighting: subgroup_reversal_gate(
                            model_scores[candidate]["metrics"][weighting],
                            model_scores["B0_ONE_YEAR_EB"]["metrics"][weighting],
                            model_scores["B1_MARCEL_345_K1200"]["metrics"][weighting],
                        )
                        for weighting in ("player", "pa")
                    }
                    all_supported_pass = all_supported_pass and all(
                        bool(value["pass"]) for value in reversals[candidate].values()
                    )
            rows.append(
                {
                    "dimension": dimension,
                    "label": label,
                    "players": players,
                    "target_pa": target_pa,
                    "supported": supported,
                    "model_scores": model_scores,
                    "reversals": reversals,
                }
            )
    return rows, all_supported_pass


def _candidate_pooled_gate(
    candidate: str,
    pooled_metrics: dict[str, dict[str, dict[str, object]]],
    pooled_surfaces: dict[str, pl.DataFrame],
    fold_reports: list[dict[str, object]],
) -> dict[str, object]:
    relative = {}
    for weighting in ("player", "pa"):
        relative[weighting] = {}
        for metric in PRIMARY_LOSS_METRICS:
            baseline_id, baseline_value = strongest_simple_baseline(
                pooled_metrics["B0_ONE_YEAR_EB"][weighting],
                pooled_metrics["B1_MARCEL_345_K1200"][weighting],
                metric,
            )
            candidate_value = float(pooled_metrics[candidate][weighting][metric])
            improvement = (baseline_value - candidate_value) / baseline_value
            relative[weighting][metric] = {
                "candidate": candidate_value,
                "baseline_id": baseline_id,
                "baseline": baseline_value,
                "relative_improvement": improvement,
                "required": POOLED_RELATIVE_THRESHOLDS[metric],
                "pass": improvement >= POOLED_RELATIVE_THRESHOLDS[metric],
            }
    baseline_for_bootstrap = min(
        ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200"),
        key=lambda model: float(pooled_metrics[model]["player"]["woba_rmse"]),
    )
    bootstrap = {
        error: paired_player_bootstrap_rmse_delta(
            pooled_surfaces[candidate],
            pooled_surfaces[baseline_for_bootstrap],
            error_column=error,
        )
        for error in ("woba_error", "runs_per_600_error")
    }
    correlations = {}
    for weighting in ("player", "pa"):
        correlations[weighting] = {}
        for metric in ("woba_pearson", "woba_spearman", "runs_per_600_pearson", "runs_per_600_spearman"):
            baseline = max(
                float(pooled_metrics[model][weighting][metric])
                for model in ("B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200")
            )
            value = float(pooled_metrics[candidate][weighting][metric])
            correlations[weighting][metric] = {
                "candidate": value,
                "strongest_baseline": baseline,
                "decline": baseline - value,
                "pass": baseline - value <= 0.02,
            }
    per_fold_primary = all(
        bool(report["candidate_diagnostics"][candidate]["primary_gate_all_views"])
        for report in fold_reports
    )
    calibration = all(
        bool(report["candidate_diagnostics"][candidate]["calibration_gate_pass"])
        for report in fold_reports
    )
    subgroup = all(
        bool(report["candidate_diagnostics"][candidate]["subgroup_reversal_gate_pass"])
        for report in fold_reports
    )
    return {
        "per_fold_primary_pass": per_fold_primary,
        "pooled_relative": relative,
        "pooled_relative_pass": all(
            bool(value["pass"])
            for view in relative.values()
            for value in view.values()
        ),
        "bootstrap_baseline": baseline_for_bootstrap,
        "bootstrap": bootstrap,
        "bootstrap_pass": all(
            bool(value["upper_bound_below_zero"]) for value in bootstrap.values()
        ),
        "correlations": correlations,
        "correlation_pass": all(
            bool(value["pass"])
            for view in correlations.values()
            for value in view.values()
        ),
        "calibration_pass": calibration,
        "subgroup_reversal_pass": subgroup,
        "promotion_pass": (
            per_fold_primary
            and all(bool(value["pass"]) for view in relative.values() for value in view.values())
            and all(bool(value["upper_bound_below_zero"]) for value in bootstrap.values())
            and all(bool(value["pass"]) for view in correlations.values() for value in view.values())
            and calibration
            and subgroup
        ),
    }


def main() -> int:
    args = _parse_args()
    component_selection = json.loads(args.component_selection.read_text(encoding="utf-8"))
    adjustment_selection = json.loads(args.adjustment_selection.read_text(encoding="utf-8"))
    all_games = pl.read_parquet(args.player_games).filter(pl.col("modeling_eligible"))
    all_park = pl.read_parquet(args.park_context)
    all_gidp = pl.read_parquet(args.gidp_history)
    people = read_chadwick_people_archive(args.register_archive)
    fold_reports = []
    all_surfaces: dict[str, list[pl.DataFrame]] = {
        model: []
        for model in (
            "B0_ONE_YEAR_EB", "B1_MARCEL_345_K1200", *CANDIDATES
        )
    }
    for fold_id in FOLDS:
        root = args.prescore_root / fold_id.lower()
        training = pl.read_parquet(root / "training_player_league_seasons.parquet")
        forecast = pl.read_parquet(root / "forecast_population.parquet")
        target = pl.read_parquet(root / "target_players.parquet")
        forecast_ages = pl.read_parquet(
            args.age_root / fold_id.lower() / "forecast_player_ages.parquet"
        )
        cutoff = int(training["season"].max())
        player_ids = [int(value) for value in forecast["player_id"].to_list()]
        half_lives, component_priors = _component_parameters(
            component_selection, fold_id
        )
        ages = {
            int(row["player_id"]): row["age_years"]
            for row in forecast_ages.iter_rows(named=True)
        }
        b0 = predict_b0_one_year_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            component_prior_pa=component_priors,
        )
        b1 = predict_b1_marcel_345_k1200(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            ages_at_target=ages,
        )
        c0 = predict_c0_nested_eb(
            training,
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives,
            component_prior_pa=component_priors,
        )
        games = all_games.filter(pl.col("season") <= cutoff)
        historical_ages = _historical_ages(people, games)
        adjustment = _adjustment_parameters(adjustment_selection, fold_id)
        fit = fit_c1_adjustments(
            games,
            all_park.filter(pl.col("season") <= cutoff),
            historical_ages,
            predictor_cutoff_season=cutoff,
            component_prior_pa=component_priors,
            park_prior_pa=adjustment["park_prior_pa"],
            movement_prior_pa=adjustment["movement_prior_pa"],
            ridge_penalty=adjustment["ridge_penalty"],
        )
        gidp = estimate_player_gidp_rates(
            all_gidp.filter(pl.col("season") <= cutoff),
            player_ids,
            predictor_cutoff_season=cutoff,
            half_life_seasons=half_lives["non_reach"],
            prior_pa=component_priors["non_reach"],
        )
        age_contexts = _target_age_contexts(
            fit.player_seasons, forecast_ages, predictor_cutoff_season=cutoff
        )
        c1 = predict_c1_hierarchical_pbp(
            c0,
            training,
            fit,
            gidp,
            target_age_contexts=age_contexts,
        )
        predictions = {
            "B0_ONE_YEAR_EB": b0,
            "B1_MARCEL_345_K1200": b1,
            "C0_NESTED_EB": c0,
            "C1_HIERARCHICAL_PBP": c1,
        }
        table_root = args.report_root / "tables" / fold_id.lower()
        prediction_artifacts = {
            model: write_canonical_parquet(
                frame,
                table_root / f"{model.lower()}_predictions.parquet",
                table_name=f"hitter_v2_{fold_id.lower()}_{model.lower()}_predictions",
            ).as_record()
            for model, frame in predictions.items()
        }
        metrics = {
            model: {
                weighting: score_hitter_predictions(frame, target, weighting=weighting)
                for weighting in ("player", "pa")
            }
            for model, frame in predictions.items()
        }
        surfaces = {
            model: build_player_scoring_surface(
                frame, target, model_id=model, fold_id=fold_id
            )
            for model, frame in predictions.items()
        }
        for model, surface in surfaces.items():
            all_surfaces[model].append(surface)
        subgroups = build_evaluation_subgroups(training, target, forecast_ages)
        subgroup_rows, _ = _subgroup_diagnostics(predictions, target, subgroups)
        candidate_diagnostics = {}
        for candidate in CANDIDATES:
            primary = {
                weighting: fold_primary_gate(
                    metrics[candidate][weighting],
                    metrics["B0_ONE_YEAR_EB"][weighting],
                    metrics["B1_MARCEL_345_K1200"][weighting],
                )
                for weighting in ("player", "pa")
            }
            component_calibration = {
                weighting: terminal_component_calibration(
                    predictions[candidate], target, weighting=weighting
                )
                for weighting in ("player", "pa")
            }
            deciles = predicted_woba_decile_calibration(surfaces[candidate])
            levels = level_aggregate_calibration(predictions[candidate], target)
            woba_calibration_pass = all(
                abs(float(metrics[candidate][view]["woba_calibration_intercept"])) <= 0.005
                and 0.90 <= float(metrics[candidate][view]["woba_calibration_slope"]) <= 1.10
                for view in ("player", "pa")
            )
            component_pass = all(
                row["slope_guardrail_pass"] is not False
                for rows in component_calibration.values()
                for row in rows
            )
            decile_pass = all(bool(row["guardrail_pass"]) for row in deciles)
            level_pass = all(row["guardrail_pass"] is not False for row in levels)
            subgroup_pass = all(
                all(
                    bool(value["pass"])
                    for value in row["reversals"].get(candidate, {}).values()
                )
                for row in subgroup_rows
                if row["supported"]
            )
            candidate_diagnostics[candidate] = {
                "primary_gate": primary,
                "primary_gate_all_views": all(
                    bool(value["pass"]) for value in primary.values()
                ),
                "terminal_component_calibration": component_calibration,
                "predicted_woba_deciles": deciles,
                "level_aggregate_calibration": levels,
                "calibration_gate_pass": (
                    woba_calibration_pass
                    and component_pass
                    and decile_pass
                    and level_pass
                ),
                "subgroup_reversal_gate_pass": subgroup_pass,
            }
        fold_reports.append(
            {
                "fold_id": fold_id,
                "predictor_cutoff_season": cutoff,
                "target_season": cutoff + 1,
                "component_parameters": {
                    "half_lives": half_lives,
                    "component_priors": component_priors,
                },
                "adjustment_parameters": adjustment,
                "metrics": metrics,
                "candidate_diagnostics": candidate_diagnostics,
                "subgroups": subgroup_rows,
                "prediction_artifacts": prediction_artifacts,
            }
        )
    pooled_surfaces = {
        model: pl.concat(frames, how="vertical_relaxed")
        for model, frames in all_surfaces.items()
    }
    pooled_metrics = {
        model: {
            weighting: summarize_scoring_surface(surface, weighting=weighting)
            for weighting in ("player", "pa")
        }
        for model, surface in pooled_surfaces.items()
    }
    candidate_gates = {
        candidate: _candidate_pooled_gate(
            candidate, pooled_metrics, pooled_surfaces, fold_reports
        )
        for candidate in CANDIDATES
    }
    promoted = [
        candidate for candidate, gate in candidate_gates.items() if gate["promotion_pass"]
    ]
    report = {
        "report_schema_version": "0.1",
        "program": "hitter_v2",
        "stage": 2,
        "status": (
            "pbp_candidate_passed_disclosed_validation"
            if promoted
            else "pbp_candidates_failed_disclosed_validation"
        ),
        "candidate_scored": True,
        "protected_2026_opened": False,
        "component_selection_sha256": sha256_file(args.component_selection),
        "adjustment_selection_sha256": sha256_file(args.adjustment_selection),
        "folds": fold_reports,
        "pooled_metrics": pooled_metrics,
        "candidate_gates": candidate_gates,
        "promoted_candidates": promoted,
        "tracking_authorized": bool(promoted),
        "stage3_authorized": False,
        "v1_continuity": {
            "status": "retained_stage0_external_validity_comparator",
            "proper_event_scores_available": False,
            "promotion_comparator": False,
        },
    }
    args.report_root.mkdir(parents=True, exist_ok=True)
    report_path = args.report_root / "report.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "promoted_candidates": promoted,
                "candidate_gates": candidate_gates,
                "protected_2026_opened": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
