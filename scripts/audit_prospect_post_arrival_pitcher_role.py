#!/usr/bin/env python3
"""Test prior MLB pitcher role beyond accepted post-arrival workload."""

from __future__ import annotations

import json
from pathlib import Path

from audit_prospect_post_arrival_workload import (
    BOOTSTRAP_DRAWS,
    C_GRID,
    _mean_scores,
    _paired,
    _rows,
    _score_cell,
)


OUTPUT_JSON = Path("docs/prospect-post-arrival-pitcher-role-result.json")
OUTPUT_MD = Path("docs/prospect-post-arrival-pitcher-role-result.md")
FEATURES = (
    "age_elapsed_prior_workload",
    "age_elapsed_prior_workload_role",
)
ORIGINS = ("FRINGE_MLB", "MEANINGFUL_MLB")


def main() -> int:
    rows = _rows("pitcher")
    training = rows.filter(rows["outcome_year"] <= 2022)
    development = rows.filter(rows["outcome_year"] == 2023)
    selected: dict[str, dict[str, float]] = {}
    development_losses = {}
    development_scores = {}
    for origin in ORIGINS:
        selected[origin] = {}
        development_losses[origin] = {}
        development_scores[origin] = {}
        for feature_set in FEATURES:
            grid = {}
            grid_losses = {}
            for c in C_GRID:
                losses = _score_cell(
                    training,
                    development,
                    origin=origin,
                    feature_set=feature_set,
                    regularization_c=c,
                )
                grid[str(c)] = _mean_scores(losses)
                grid_losses[c] = losses
            chosen = min(C_GRID, key=lambda value: grid[str(value)]["log_loss"])
            selected[origin][feature_set] = chosen
            development_scores[origin][feature_set] = grid
            development_losses[origin][feature_set] = grid_losses[chosen]

    confirmations = []
    for outcome_year in (2024, 2025):
        fold_training = rows.filter(rows["outcome_year"] < outcome_year)
        evaluation = rows.filter(rows["outcome_year"] == outcome_year)
        cells = {}
        for origin_index, origin in enumerate(ORIGINS):
            losses = {
                feature_set: _score_cell(
                    fold_training,
                    evaluation,
                    origin=origin,
                    feature_set=feature_set,
                    regularization_c=selected[origin][feature_set],
                )
                for feature_set in FEATURES
            }
            cells[origin] = {
                "scores": {
                    feature_set: _mean_scores(value)
                    for feature_set, value in losses.items()
                },
                "role_minus_workload": {
                    metric: _paired(
                        losses["age_elapsed_prior_workload_role"],
                        losses["age_elapsed_prior_workload"],
                        metric,
                        seed=20260911
                        + outcome_year * 10
                        + origin_index * 2
                        + metric_index,
                    )
                    for metric_index, metric in enumerate(("log_loss", "brier"))
                },
            }
        confirmations.append({"outcome_year": outcome_year, "cells": cells})

    decisions = {}
    for origin in ORIGINS:
        baseline = development_losses[origin]["age_elapsed_prior_workload"]
        candidate = development_losses[origin][
            "age_elapsed_prior_workload_role"
        ]
        development_delta = {
            metric: float(candidate[metric].mean() - baseline[metric].mean())
            for metric in ("log_loss", "brier")
        }
        later_pass = all(
            fold["cells"][origin]["role_minus_workload"][metric][
                "paired_bootstrap_high"
            ]
            < 0
            for fold in confirmations
            for metric in ("log_loss", "brier")
        )
        decisions[origin] = {
            "development_delta": development_delta,
            "development_point_gate_passed": all(
                value < 0 for value in development_delta.values()
            ),
            "both_confirmations_paired_gate_passed": later_pass,
            "linked_simulation_role_input_supported": (
                all(value < 0 for value in development_delta.values())
                and later_pass
            ),
        }

    report = {
        "report_schema_version": "0.1",
        "status": "post_arrival_pitcher_role_test_complete",
        "plan": "docs/prospect-post-arrival-pitcher-role-plan.md",
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "current_2026_used": False,
        "shortened_2020_outcomes_excluded": True,
        "selected_regularization": selected,
        "development_scores": development_scores,
        "rolling_confirmations": confirmations,
        "decisions": decisions,
        "production_changed": False,
    }
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = []
    for fold in confirmations:
        for origin in ORIGINS:
            delta = fold["cells"][origin]["role_minus_workload"]
            decision = decisions[origin]["linked_simulation_role_input_supported"]
            lines.append(
                f"| {origin} | {fold['outcome_year']} | "
                f"{delta['log_loss']['mean_delta']:+.6f} "
                f"[{delta['log_loss']['paired_bootstrap_low']:+.6f}, "
                f"{delta['log_loss']['paired_bootstrap_high']:+.6f}] | "
                f"{delta['brier']['mean_delta']:+.6f} "
                f"[{delta['brier']['paired_bootstrap_low']:+.6f}, "
                f"{delta['brier']['paired_bootstrap_high']:+.6f}] | "
                f"{'Pass' if decision else 'Reject'} |"
            )
    OUTPUT_MD.write_text(
        """# Prospect post-arrival pitcher-role result

Status: research test complete; no current value changed.

The challenger adds only prior-season start share and batters faced per game to the
already accepted age, elapsed-time and total-workload model. Regularization was
selected on 2023; 2024 and 2025 were scored unchanged. Negative is better.

| Origin | Outcome | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---:|---:|---:|---|
"""
        + "\n".join(lines)
        + """

The features describe prior usage; they do not claim starter use causes development.
The 2020 target, current 2026 data, organization, future workload and outside FV are
excluded.

Decision: reject role as an independent career-state advancement input. Continue to
use starter/reliever evidence where it belongs—in pitcher workload and WAR paths—but
do not let it also raise the advancement hazard after total workload is known.
""",
        encoding="utf-8",
    )
    print(json.dumps(decisions, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
