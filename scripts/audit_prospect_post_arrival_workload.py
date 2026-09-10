#!/usr/bin/env python3
"""Test prior MLB workload in annual post-arrival state progression."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_prospect_ordered_transition_path import _data, _transition_training
from universal_baseball.prospect_mlb_progression import (
    ORIGINS,
    build_post_arrival_progression_rows,
    fit_progression,
    score_progression,
)


OUTPUT_JSON = Path("docs/prospect-post-arrival-workload-result.json")
OUTPUT_MD = Path("docs/prospect-post-arrival-workload-result.md")
C_GRID = (0.03, 0.1, 0.3, 1.0)
FEATURES = ("age_elapsed", "age_elapsed_prior_workload")
BOOTSTRAP_DRAWS = 2000


def _rows(player_type: str) -> pl.DataFrame:
    data = _data(player_type)
    transitions = [
        _transition_training(data[year], year) for year in (2018, 2019, 2021)
    ]
    table = (
        "mlb_batting_2009_2025.parquet"
        if player_type == "hitter"
        else "mlb_pitching_2009_2025.parquet"
    )
    column = "batting_pa" if player_type == "hitter" else "pitching_bf"
    workload = (
        pl.read_parquet(
            Path("reports/generated/career-mlb-outcome-inventory-2009-2025/tables")
            / table
        )
        .select("season", "player_id", pl.col(column).alias("mlb_workload"))
    )
    return build_post_arrival_progression_rows(transitions, workload)


def _paired(candidate: pl.DataFrame, baseline: pl.DataFrame, column: str, seed: int) -> dict[str, float]:
    values = candidate.select(
        "player_id", pl.col(column).alias("candidate")
    ).join(
        baseline.select("player_id", pl.col(column).alias("baseline")),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    if values.height != candidate.height or values.height != baseline.height:
        raise ValueError("progression comparison does not use identical players")
    delta = values["candidate"].to_numpy() - values["baseline"].to_numpy()
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(delta), size=(BOOTSTRAP_DRAWS, len(delta)))
    means = delta[indices].mean(axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return {
        "mean_delta": float(delta.mean()),
        "paired_bootstrap_low": float(low),
        "paired_bootstrap_high": float(high),
    }


def _score_cell(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    *,
    origin: str,
    feature_set: str,
    regularization_c: float,
) -> pl.DataFrame:
    fit = fit_progression(
        training,
        origin_state=origin,
        feature_set=feature_set,
        regularization_c=regularization_c,
    )
    return score_progression(fit, evaluation)


def _mean_scores(losses: pl.DataFrame) -> dict[str, float | int]:
    return {
        "players": losses.height,
        "advances": int(losses.get_column("advanced").sum()),
        "log_loss": float(losses.get_column("log_loss").mean()),
        "brier": float(losses.get_column("brier").mean()),
    }


def _one(player_type: str) -> dict[str, object]:
    rows = _rows(player_type)
    training = rows.filter(pl.col("outcome_year") <= 2022)
    development = rows.filter(pl.col("outcome_year") == 2023)
    selected = {}
    development_scores = {}
    development_losses = {}
    for origin in ORIGINS:
        selected[origin] = {}
        development_scores[origin] = {}
        development_losses[origin] = {}
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
            chosen = min(C_GRID, key=lambda c: grid[str(c)]["log_loss"])
            selected[origin][feature_set] = chosen
            development_scores[origin][feature_set] = grid
            development_losses[origin][feature_set] = grid_losses[chosen]

    confirmations = []
    for outcome_year in (2024, 2025):
        fold_training = rows.filter(pl.col("outcome_year") < outcome_year)
        evaluation = rows.filter(pl.col("outcome_year") == outcome_year)
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
                "workload_minus_baseline": {
                    metric: _paired(
                        losses["age_elapsed_prior_workload"],
                        losses["age_elapsed"],
                        metric,
                        seed=20260910 + outcome_year * 10 + origin_index * 2 + metric_index,
                    )
                    for metric_index, metric in enumerate(("log_loss", "brier"))
                },
            }
        confirmations.append({"outcome_year": outcome_year, "cells": cells})

    decisions = {}
    for origin in ORIGINS:
        baseline = development_losses[origin]["age_elapsed"]
        candidate = development_losses[origin]["age_elapsed_prior_workload"]
        development_delta = {
            metric: float(candidate[metric].mean() - baseline[metric].mean())
            for metric in ("log_loss", "brier")
        }
        later_pass = all(
            fold["cells"][origin]["workload_minus_baseline"][metric][
                "paired_bootstrap_high"
            ]
            < 0
            for fold in confirmations
            for metric in ("log_loss", "brier")
        )
        decisions[origin] = {
            "development_delta": development_delta,
            "development_point_gate_passed": (
                development_delta["log_loss"] < 0
                and development_delta["brier"] < 0
            ),
            "both_confirmations_paired_gate_passed": later_pass,
            "linked_simulation_input_supported": (
                development_delta["log_loss"] < 0
                and development_delta["brier"] < 0
                and later_pass
            ),
        }
    return {
        "rows": rows.height,
        "support": rows.group_by("outcome_year", "from_state").agg(
            pl.len().alias("players"), pl.col("advanced").sum().alias("advances")
        ).sort("outcome_year", "from_state").to_dicts(),
        "selected_regularization": selected,
        "development_scores": development_scores,
        "rolling_confirmations": confirmations,
        "decisions": decisions,
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "post_arrival_prior_workload_test_complete",
        "plan": "docs/prospect-post-arrival-workload-plan.md",
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "current_2026_used": False,
        "shortened_2020_outcomes_excluded": True,
        "hitter": _one("hitter"),
        "pitcher": _one("pitcher"),
        "production_changed": False,
    }
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    def lines(player_type: str) -> str:
        result = []
        for fold in report[player_type]["rolling_confirmations"]:
            for origin in ORIGINS:
                delta = fold["cells"][origin]["workload_minus_baseline"]
                decision = report[player_type]["decisions"][origin]
                result.append(
                    f"| {player_type.title()} | {origin} | {fold['outcome_year']} | "
                    f"{delta['log_loss']['mean_delta']:+.6f} "
                    f"[{delta['log_loss']['paired_bootstrap_low']:+.6f}, "
                    f"{delta['log_loss']['paired_bootstrap_high']:+.6f}] | "
                    f"{delta['brier']['mean_delta']:+.6f} "
                    f"[{delta['brier']['paired_bootstrap_low']:+.6f}, "
                    f"{delta['brier']['paired_bootstrap_high']:+.6f}] | "
                    f"{'Pass' if decision['linked_simulation_input_supported'] else 'Reject'} |"
                )
        return "\n".join(result)

    OUTPUT_MD.write_text(
        f"""# Prospect post-arrival workload progression result

Status: research test complete; no current value changed.

The challenger adds only prior-season official MLB workload, normalized to mean active
workload in that season, plus an active indicator. It predicts advancement from fringe
to a higher state and from meaningful to established. Regularization was selected for
the 2023 outcome; 2024 and 2025 were then scored unchanged. Negative is better.

| Group | Origin | Outcome | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---|---:|---:|---:|---|
{lines('hitter')}
{lines('pitcher')}

A pass means realized workload should be carried inside a future annually linked
career simulation. It does not authorize using future workload as if known today and
does not alter current player values. The 2020 target, current 2026 data, organization
and outside FV are excluded.
""",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                player_type: report[player_type]["decisions"]
                for player_type in ("hitter", "pitcher")
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
