#!/usr/bin/env python3
"""Audit conditional meaningful and established prospect-career hurdles."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.prospect_arrival_validation import (
    CandidateSpec,
    calibration_diagnostics,
    paired_bootstrap_difference,
    proper_scores,
    select_nested_candidate,
)


FEATURE_SETS = (
    "core", "baseball_interactions", "draft_pedigree", "baseball_pedigree"
)
REGULARIZATION = (0.1, 1.0)
PRODUCTION_REGRESSION = (0.0, 50.0)
INCUMBENT = CandidateSpec("core", 1.0, 0.0)
STAGES = (
    (
        "meaningful_given_arrival",
        "meaningful_role_within_horizon",
        "arrived_within_horizon",
    ),
    (
        "established_given_meaningful",
        "established_role_within_horizon",
        "meaningful_role_within_horizon",
    ),
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-conditional-career-hurdle-result.json"),
    )
    return parser.parse_args()


def _history(root: Path) -> pl.DataFrame:
    paths = sorted(
        (root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _score(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    *,
    player_type: str,
    stage: str,
    target: str,
    candidate: CandidateSpec,
) -> tuple[dict[str, object], np.ndarray]:
    fit = fit_arrival_model(
        training,
        player_type=player_type,
        target_column=target,
        outcome_name=stage,
        feature_set=candidate.feature_set,
        regularization_c=candidate.regularization_c,
        production_regression=candidate.production_regression,
    )
    probability = predict_arrival(fit, evaluation).get_column(
        f"predicted_two_year_{stage}_probability"
    ).to_numpy()
    metrics = proper_scores(evaluation.get_column(target).to_numpy(), probability)
    metrics.update(
        {
            "model_id": candidate.model_id,
            "feature_set": candidate.feature_set,
            "regularization_c": candidate.regularization_c,
            "production_regression": candidate.production_regression,
        }
    )
    return metrics, probability


def _subgroups(
    evaluation: pl.DataFrame,
    observed: np.ndarray,
    incumbent: np.ndarray,
    candidate: np.ndarray,
) -> list[dict[str, object]]:
    dimensions = {
        "level": evaluation.get_column("level_tier").cast(pl.String).to_list(),
        "age": [
            "16-19" if value < 20 else "20-22" if value < 23 else "23-25" if value < 26 else "26-30"
            for value in evaluation.get_column("age_years").to_list()
        ],
        "workload": [
            "0" if value == 0 else "1-99" if value < 100 else "100-299" if value < 300 else "300+"
            for value in evaluation.get_column("current_milb_workload").to_list()
        ],
    }
    rows = []
    for dimension, raw_labels in dimensions.items():
        labels = np.asarray(raw_labels, dtype=object)
        for group in sorted(set(raw_labels)):
            mask = labels == group
            y = observed[mask]
            base = proper_scores(y, incumbent[mask])
            challenge = proper_scores(y, candidate[mask])
            rows.append(
                {
                    "dimension": dimension,
                    "group": group,
                    "players": int(mask.sum()),
                    "positives": int(y.sum()),
                    "supported": bool(mask.sum() >= 30 and y.sum() >= 5),
                    "log_loss_delta": challenge["log_loss"] - base["log_loss"],
                    "brier_delta": challenge["brier"] - base["brier"],
                }
            )
    return rows


def main() -> int:
    args = _args()
    root = args.generated_root
    history = _history(root)
    membership = pl.read_parquet(
        root / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    demographics = pl.read_parquet(
        root / "player-demographics/tables/player-demographics.parquet"
    )
    debut_dates = pl.read_parquet(
        root / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    draft = pl.read_parquet(root / "draft-history/draft-history.parquet")
    candidates = [
        CandidateSpec(feature_set, c, regression)
        for feature_set in FEATURE_SETS
        for c in REGULARIZATION
        for regression in PRODUCTION_REGRESSION
    ]
    results = {}
    for player_type in ("hitter", "pitcher"):
        snapshots = pl.read_parquet(
            root / "opportunity-history-sources-v2/tables"
            / f"{player_type}_snapshots.parquet"
        )
        skill_name = (
            "affiliated_hitting_components.parquet"
            if player_type == "hitter"
            else "affiliated_pitching_components.parquet"
        )
        skill = pl.read_parquet(root / "phase2-arrival-skill-source/tables" / skill_name)
        cohorts = {
            year: build_arrival_cohort(
                snapshots,
                history,
                membership,
                skill,
                debut_dates,
                snapshot_year=year,
                horizon=2,
                player_type=player_type,
                demographics=demographics,
                draft_history=draft,
            )
            for year in (2018, 2021, 2023)
        }
        type_results = {}
        for stage, target, condition in STAGES:
            development_training = cohorts[2018].filter(pl.col(condition) == 1)
            development_evaluation = cohorts[2021].filter(pl.col(condition) == 1)
            selection_rows = []
            for candidate in candidates:
                metrics, _ = _score(
                    development_training,
                    development_evaluation,
                    player_type=player_type,
                    stage=stage,
                    target=target,
                    candidate=candidate,
                )
                metrics["evaluation_year"] = 2021
                selection_rows.append(metrics)
            selected_id = select_nested_candidate(
                selection_rows, eligible_years=(2021,), incumbent_id=INCUMBENT.model_id
            )
            selected = next(item for item in candidates if item.model_id == selected_id)
            outer_training = pl.concat([cohorts[2018], cohorts[2021]]).filter(
                pl.col(condition) == 1
            )
            outer_evaluation = cohorts[2023].filter(pl.col(condition) == 1)
            incumbent_metrics, incumbent_probability = _score(
                outer_training,
                outer_evaluation,
                player_type=player_type,
                stage=stage,
                target=target,
                candidate=INCUMBENT,
            )
            candidate_metrics, candidate_probability = _score(
                outer_training,
                outer_evaluation,
                player_type=player_type,
                stage=stage,
                target=target,
                candidate=selected,
            )
            observed = outer_evaluation.get_column(target).to_numpy()
            type_results[stage] = {
                "condition": condition,
                "development_training_players": development_training.height,
                "development_evaluation_players": development_evaluation.height,
                "development_selection_scores": selection_rows,
                "selected_candidate": {
                    "model_id": selected.model_id,
                    "feature_set": selected.feature_set,
                    "regularization_c": selected.regularization_c,
                    "production_regression": selected.production_regression,
                },
                "outer_training_players": outer_training.height,
                "outer_evaluation_players": outer_evaluation.height,
                "outer_positives": int(observed.sum()),
                "incumbent": incumbent_metrics,
                "candidate": candidate_metrics,
                "paired_bootstrap": paired_bootstrap_difference(
                    observed, incumbent_probability, candidate_probability
                ),
                "incumbent_calibration": calibration_diagnostics(
                    observed, incumbent_probability, bins=5
                ),
                "candidate_calibration": calibration_diagnostics(
                    observed, candidate_probability, bins=5
                ),
                "subgroups": _subgroups(
                    outer_evaluation, observed, incumbent_probability, candidate_probability
                ),
            }
        results[player_type] = type_results
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "conditional_career_hurdle_outer_test_complete",
        "contract": "docs/prospect-conditional-career-hurdle-plan.md",
        "candidate_grid": {
            "feature_sets": list(FEATURE_SETS),
            "regularization_c": list(REGULARIZATION),
            "production_regression": list(PRODUCTION_REGRESSION),
            "candidates": len(candidates),
        },
        "chronology": {
            "development_train": [2018],
            "development_evaluate": 2021,
            "outer_train": [2018, 2021],
            "outer_evaluate": 2023,
            "horizon_years": 2,
            "2026_opened": False,
        },
        "deployment_decision": {
            "hitter": {
                "meaningful_given_arrival": {
                    "model_id": "core__c_1",
                    "reason": "development-selected interaction model reversed on the outer check",
                },
                "established_given_meaningful": {
                    "model_id": "core__c_0.1__rate_reg_50",
                    "reason": "development-selected shrinkage within the core feature family improved both outer point scores; uncertainty remains explicit",
                },
            },
            "pitcher": {
                "meaningful_given_arrival": {
                    "model_id": "core__c_1",
                    "reason": "development selection retained the incumbent",
                },
                "established_given_meaningful": {
                    "model_id": "core__c_1",
                    "reason": "development-selected interaction model reversed on the outer check",
                },
            },
            "richer_feature_family_promoted": False,
        },
        "results": results,
        "boundaries": {
            "outside_fv_used": False,
            "birth_country_features_used": False,
            "current_physical_measurements_used": False,
            "organization_or_depth_used": False,
            "production_values_changed": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
