#!/usr/bin/env python3
"""Audit chronology-safe recalibration of deployed prospect hurdle probabilities."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression

from universal_baseball.prospect_arrival import (
    build_arrival_cohort,
    fit_arrival_model,
    predict_arrival,
)
from universal_baseball.prospect_arrival_validation import (
    calibration_diagnostics,
    paired_bootstrap_difference,
    proper_scores,
)


STAGES = (
    ("arrival", "arrived_within_horizon", None),
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
        default=Path("docs/prospect-upper-tail-calibration-result.json"),
    )
    return parser.parse_args()


def _history(root: Path) -> pl.DataFrame:
    paths = sorted(
        (root / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _logit(probability: np.ndarray) -> np.ndarray:
    clipped = np.clip(np.asarray(probability, dtype=float), 1e-9, 1 - 1e-9)
    return np.log(clipped / (1 - clipped))


def _fit_intercept(observed: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    y = np.asarray(observed, dtype=float)
    logits = _logit(probability)
    intercept = 0.0
    for _ in range(100):
        fitted = 1.0 / (1.0 + np.exp(-(logits + intercept)))
        gradient = float((fitted - y).sum())
        curvature = float((fitted * (1.0 - fitted)).sum())
        step = gradient / max(curvature, 1e-12)
        intercept -= step
        if abs(step) < 1e-12:
            break
    return {"slope": 1.0, "intercept": intercept}


def _fit_platt(observed: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    model = LogisticRegression(C=1.0, max_iter=2_000, random_state=0).fit(
        _logit(probability).reshape(-1, 1), observed
    )
    return {
        "slope": float(model.coef_[0, 0]),
        "intercept": float(model.intercept_[0]),
    }


def _apply(probability: np.ndarray, parameters: dict[str, float]) -> np.ndarray:
    linear = parameters["intercept"] + parameters["slope"] * _logit(probability)
    return 1.0 / (1.0 + np.exp(-linear))


def _base_probability(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    *,
    player_type: str,
    stage: str,
    target: str,
) -> np.ndarray:
    hitter_established = player_type == "hitter" and stage == "established_given_meaningful"
    fit = fit_arrival_model(
        training,
        player_type=player_type,
        target_column=target,
        outcome_name=stage,
        feature_set="core",
        regularization_c=0.1 if hitter_established else 1.0,
        production_regression=50.0 if hitter_established else 0.0,
    )
    return predict_arrival(fit, evaluation).get_column(
        f"predicted_two_year_{stage}_probability"
    ).to_numpy()


def _upper_tail(
    observed: np.ndarray, probability: np.ndarray, *, fraction: float
) -> dict[str, float | int]:
    count = max(1, int(np.ceil(len(observed) * fraction)))
    selected = np.argsort(probability, kind="stable")[-count:]
    return {
        "players": count,
        "predicted_rate": float(probability[selected].mean()),
        "observed_rate": float(observed[selected].mean()),
        "minimum_probability": float(probability[selected].min()),
    }


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
    draft = pl.read_parquet(root / "draft-history/draft-history.parquet")
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
                snapshot_year=year,
                horizon=2,
                player_type=player_type,
                demographics=demographics,
                draft_history=draft,
            )
            for year in (2018, 2021, 2023)
        }
        stage_results = {}
        for stage, target, condition in STAGES:
            def conditioned(frame: pl.DataFrame) -> pl.DataFrame:
                return frame if condition is None else frame.filter(pl.col(condition) == 1)

            development_train = conditioned(cohorts[2018])
            development_eval = conditioned(cohorts[2021])
            development_observed = development_eval.get_column(target).to_numpy()
            development_raw = _base_probability(
                development_train,
                development_eval,
                player_type=player_type,
                stage=stage,
                target=target,
            )
            calibrators = {
                "intercept_only": _fit_intercept(
                    development_observed, development_raw
                ),
                "platt_c_1": _fit_platt(development_observed, development_raw),
            }
            raw_development_score = proper_scores(
                development_observed, development_raw
            )
            development_scores = {}
            passing = []
            for name, parameters in calibrators.items():
                calibrated = _apply(development_raw, parameters)
                score = proper_scores(development_observed, calibrated)
                development_scores[name] = score
                if (
                    score["log_loss"] < raw_development_score["log_loss"]
                    and score["brier"] <= raw_development_score["brier"]
                ):
                    passing.append(name)
            selected = min(
                passing,
                key=lambda name: (development_scores[name]["log_loss"], name),
                default="identity",
            )
            outer_train = conditioned(pl.concat([cohorts[2018], cohorts[2021]]))
            outer_eval = conditioned(cohorts[2023])
            outer_observed = outer_eval.get_column(target).to_numpy()
            outer_raw = _base_probability(
                outer_train,
                outer_eval,
                player_type=player_type,
                stage=stage,
                target=target,
            )
            selected_parameters = (
                calibrators[selected]
                if selected != "identity"
                else {"slope": 1.0, "intercept": 0.0}
            )
            outer_candidate = _apply(outer_raw, selected_parameters)
            raw_score = proper_scores(outer_observed, outer_raw)
            candidate_score = proper_scores(outer_observed, outer_candidate)
            stage_results[stage] = {
                "condition": condition,
                "development_players": development_eval.height,
                "development_raw": raw_development_score,
                "development_candidates": development_scores,
                "calibration_parameters": calibrators,
                "selected_calibration": selected,
                "selected_parameters": selected_parameters,
                "outer_players": outer_eval.height,
                "outer_raw": raw_score,
                "outer_candidate": candidate_score,
                "outer_paired_bootstrap": paired_bootstrap_difference(
                    outer_observed, outer_raw, outer_candidate
                ),
                "outer_raw_calibration": calibration_diagnostics(
                    outer_observed, outer_raw, bins=5
                ),
                "outer_candidate_calibration": calibration_diagnostics(
                    outer_observed, outer_candidate, bins=5
                ),
                "outer_raw_top_decile": _upper_tail(
                    outer_observed, outer_raw, fraction=0.1
                ),
                "outer_candidate_top_decile": _upper_tail(
                    outer_observed, outer_candidate, fraction=0.1
                ),
                "outer_raw_top_one_percent": _upper_tail(
                    outer_observed, outer_raw, fraction=0.01
                ),
                "outer_candidate_top_one_percent": _upper_tail(
                    outer_observed, outer_candidate, fraction=0.01
                ),
                "passed_outer": bool(
                    candidate_score["log_loss"] < raw_score["log_loss"]
                    and candidate_score["brier"] < raw_score["brier"]
                ),
            }
        results[player_type] = stage_results
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "prospect_probability_calibration_outer_audit_complete",
        "contract": "docs/prospect-upper-tail-calibration-plan.md",
        "chronology": {
            "development_train": [2018],
            "development_calibration": 2021,
            "outer_train": [2018, 2021],
            "outer_evaluate": 2023,
            "horizon_years": 2,
        },
        "results": results,
        "boundaries": {
            "outside_fv_used": False,
            "current_probabilities_changed": False,
            "demographic_or_organization_features_added": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
