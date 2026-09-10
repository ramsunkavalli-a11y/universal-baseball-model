#!/usr/bin/env python3
"""Test a joint one-year prospect state transition against ordered binary logits."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_career_state import (
    career_state_scores,
    fit_career_state_model,
    predict_career_state,
    predict_independent_ordered_state,
)


ROOT = Path("reports/generated")
OUTPUT_JSON = Path("docs/prospect-one-year-career-state-result.json")
OUTPUT_MD = Path("docs/prospect-one-year-career-state-result.md")
C_GRID = (0.03, 0.1, 0.3, 1.0)
TRAINING_YEARS = (2018, 2019, 2021)
DEVELOPMENT_YEAR = 2022
CONFIRMATION_YEARS = (2023, 2024)


def _history_stats() -> pl.DataFrame:
    paths = sorted((ROOT / "opportunity-history-sources-v2/tables").glob(
        "*/affiliated_season_stats.parquet"
    ))
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _cohorts(player_type: str) -> dict[int, pl.DataFrame]:
    history = ROOT / "opportunity-history-sources-v2/tables"
    snapshots = pl.read_parquet(history / f"{player_type}_snapshots.parquet")
    stats = _history_stats()
    membership = pl.read_parquet(
        ROOT / "opportunity-40man-history/tables/historical_40man_membership.parquet"
    )
    demographics = pl.read_parquet(
        ROOT / "player-demographics/tables/player-demographics.parquet"
    )
    skill = pl.read_parquet(
        ROOT / "phase2-arrival-skill-source/tables"
        / f"affiliated_{'hitting' if player_type == 'hitter' else 'pitching'}_components.parquet"
    )
    debut = pl.read_parquet(
        ROOT / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    return {
        year: build_arrival_cohort(
            snapshots, stats, membership, skill, debut,
            snapshot_year=year, horizon=1, player_type=player_type,
            demographics=demographics,
        )
        for year in (*TRAINING_YEARS, DEVELOPMENT_YEAR, *CONFIRMATION_YEARS)
    }


def _fit_score(
    training: pl.DataFrame, evaluation: pl.DataFrame, *,
    player_type: str, method: str, regularization_c: float,
) -> dict[str, float | int]:
    if method == "joint_multinomial":
        fit = fit_career_state_model(
            training, player_type=player_type, feature_set="level_exposure",
            regularization_c=regularization_c,
        )
        prediction = predict_career_state(fit, evaluation)
    else:
        prediction = predict_independent_ordered_state(
            training, evaluation, player_type=player_type,
            feature_set="level_exposure", regularization_c=regularization_c,
        )
    return career_state_scores(prediction)


def _one(player_type: str) -> dict[str, object]:
    cohorts = _cohorts(player_type)
    initial_training = pl.concat([cohorts[year] for year in TRAINING_YEARS])
    grids = {}
    selected = {}
    for method in ("ordered_binary", "joint_multinomial"):
        grids[method] = {
            str(c): _fit_score(
                initial_training, cohorts[DEVELOPMENT_YEAR],
                player_type=player_type, method=method, regularization_c=c,
            )
            for c in C_GRID
        }
        selected[method] = min(
            C_GRID, key=lambda c: grids[method][str(c)]["multiclass_log_loss"]
        )
    confirmations = []
    training_years = list(TRAINING_YEARS) + [DEVELOPMENT_YEAR]
    for evaluation_year in CONFIRMATION_YEARS:
        training = pl.concat([cohorts[year] for year in training_years])
        baseline = _fit_score(
            training, cohorts[evaluation_year], player_type=player_type,
            method="ordered_binary", regularization_c=selected["ordered_binary"],
        )
        joint = _fit_score(
            training, cohorts[evaluation_year], player_type=player_type,
            method="joint_multinomial", regularization_c=selected["joint_multinomial"],
        )
        confirmations.append({
            "snapshot_year": evaluation_year,
            "target_year": evaluation_year + 1,
            "training_snapshot_years": list(training_years),
            "ordered_binary": baseline, "joint_multinomial": joint,
            "joint_minus_ordered_log_loss": (
                joint["multiclass_log_loss"] - baseline["multiclass_log_loss"]
            ),
            "joint_minus_ordered_brier": (
                joint["multiclass_brier"] - baseline["multiclass_brier"]
            ),
        })
        training_years.append(evaluation_year)
    passed = all(
        row["joint_minus_ordered_log_loss"] < 0
        and row["joint_minus_ordered_brier"] <= 0
        for row in confirmations
    )
    return {
        "development_snapshot": DEVELOPMENT_YEAR,
        "development_target": DEVELOPMENT_YEAR + 1,
        "regularization_grid": list(C_GRID),
        "development_scores": grids,
        "selected_regularization": selected,
        "rolling_confirmations": confirmations,
        "joint_structure_gate_passed": passed,
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "one_year_joint_career_state_outer_test_complete",
        "state_order": ["NO_MLB", "FRINGE_MLB", "MEANINGFUL_MLB", "ESTABLISHED_MLB"],
        "shortened_2020_snapshot_excluded": True,
        "current_2026_used": False,
        "hitter": _one("hitter"), "pitcher": _one("pitcher"),
        "production_changed": False,
        "boundary": (
            "This tests the first pre-MLB-to-next-season transition only. MLB-state "
            "progression, future MiLB covariates, workload and WAR remain separate."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def rows(name: str) -> str:
        return "\n".join(
            f"| {name.title()} | {row['target_year']} | {row['ordered_binary']['players']} | "
            f"{row['joint_minus_ordered_log_loss']:+.6f} | "
            f"{row['joint_minus_ordered_brier']:+.6f} |"
            for row in report[name]["rolling_confirmations"]
        )
    OUTPUT_MD.write_text(f"""# One-year joint prospect career state

Status: structure test complete; no current player value changed.

The challenger predicts one mutually exclusive next-season state: no MLB, fringe
MLB, meaningful MLB, or established MLB. It is compared with three independently
fit cumulative logits forced back into that same ordered simplex. Both use the same
cutoff-safe level/exposure features. Regularization was selected on 2022-to-2023,
then frozen for rolling 2023-to-2024 and 2024-to-2025 checks. Negative is better.

| Group | Target | Players | Joint-minus-ordered log loss | Joint-minus-ordered Brier |
|---|---:|---:|---:|---:|
{rows('hitter')}
{rows('pitcher')}

This is the first transition, not the complete six-year model. It tests whether a
joint state representation is a better foundation before adding later MLB-state
progression, attrition, workload and WAR. The 2020 snapshot is excluded because its
current workload was structurally shortened. No outside FV enters either model.
""", encoding="utf-8")
    print(json.dumps({name: {
        "selected": report[name]["selected_regularization"],
        "confirmation": report[name]["rolling_confirmations"],
        "passed": report[name]["joint_structure_gate_passed"],
    } for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
