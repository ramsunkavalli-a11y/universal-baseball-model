#!/usr/bin/env python3
"""Test development-path features in the one-year ordered career state."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_career_state import (
    career_state_losses,
    career_state_scores,
    fit_career_state_model,
    predict_career_state,
    predict_independent_ordered_state,
)


ROOT = Path("reports/generated")
OUTPUT_JSON = Path("docs/prospect-development-state-result.json")
OUTPUT_MD = Path("docs/prospect-development-state-result.md")
C_GRID = (0.03, 0.1, 0.3, 1.0)
TRAINING_YEARS = (2018, 2019, 2021)
DEVELOPMENT_YEAR = 2022
CONFIRMATION_YEARS = (2023, 2024)
BOOTSTRAP_DRAWS = 1000
CANDIDATES = {
    "ordered_level_exposure": ("ordered", "level_exposure"),
    "ordered_development_path": ("ordered", "development_path"),
    "joint_level_exposure": ("joint", "level_exposure"),
    "joint_development_path": ("joint", "development_path"),
}
BASELINE = "ordered_level_exposure"


def _history_stats() -> pl.DataFrame:
    paths = sorted(
        (ROOT / "opportunity-history-sources-v2/tables").glob(
            "*/affiliated_season_stats.parquet"
        )
    )
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
        ROOT
        / "phase2-arrival-skill-source/tables"
        / f"affiliated_{'hitting' if player_type == 'hitter' else 'pitching'}_components.parquet"
    )
    debut = pl.read_parquet(
        ROOT / "career-mlb-outcome-inventory-2009-2025/tables/people-debut-dates.parquet"
    )
    return {
        year: build_arrival_cohort(
            snapshots,
            stats,
            membership,
            skill,
            debut,
            snapshot_year=year,
            horizon=1,
            player_type=player_type,
            demographics=demographics,
        )
        for year in (*TRAINING_YEARS, DEVELOPMENT_YEAR, *CONFIRMATION_YEARS)
    }


def _predict(
    training: pl.DataFrame,
    evaluation: pl.DataFrame,
    *,
    player_type: str,
    candidate: str,
    regularization_c: float,
) -> pl.DataFrame:
    structure, feature_set = CANDIDATES[candidate]
    if structure == "joint":
        fit = fit_career_state_model(
            training,
            player_type=player_type,
            feature_set=feature_set,
            regularization_c=regularization_c,
        )
        return predict_career_state(fit, evaluation)
    return predict_independent_ordered_state(
        training,
        evaluation,
        player_type=player_type,
        feature_set=feature_set,
        regularization_c=regularization_c,
    )


def _paired_interval(
    candidate: pl.DataFrame,
    baseline: pl.DataFrame,
    column: str,
    *,
    seed: int,
) -> dict[str, float]:
    paired = candidate.select("player_id", pl.col(column).alias("candidate")).join(
        baseline.select("player_id", pl.col(column).alias("baseline")),
        on="player_id",
        how="inner",
        validate="1:1",
    )
    if paired.height != candidate.height or paired.height != baseline.height:
        raise ValueError("career-state comparison does not use identical players")
    delta = paired.get_column("candidate").to_numpy() - paired.get_column(
        "baseline"
    ).to_numpy()
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(delta), size=(BOOTSTRAP_DRAWS, len(delta)))
    means = delta[indices].mean(axis=1)
    low, high = np.quantile(means, (0.025, 0.975))
    return {
        "mean_delta": float(delta.mean()),
        "paired_bootstrap_low": float(low),
        "paired_bootstrap_high": float(high),
    }


def _one(player_type: str) -> dict[str, object]:
    cohorts = _cohorts(player_type)
    initial_training = pl.concat([cohorts[year] for year in TRAINING_YEARS])
    development_scores: dict[str, dict[str, dict[str, float | int]]] = {}
    selected: dict[str, float] = {}
    for candidate in CANDIDATES:
        development_scores[candidate] = {}
        for c in C_GRID:
            prediction = _predict(
                initial_training,
                cohorts[DEVELOPMENT_YEAR],
                player_type=player_type,
                candidate=candidate,
                regularization_c=c,
            )
            development_scores[candidate][str(c)] = career_state_scores(prediction)
        selected[candidate] = min(
            C_GRID,
            key=lambda c: development_scores[candidate][str(c)][
                "multiclass_log_loss"
            ],
        )

    development_baseline = development_scores[BASELINE][str(selected[BASELINE])]
    development_delta = {
        candidate: {
            "log_loss": float(
                development_scores[candidate][str(selected[candidate])][
                    "multiclass_log_loss"
                ]
                - development_baseline["multiclass_log_loss"]
            ),
            "brier": float(
                development_scores[candidate][str(selected[candidate])][
                    "multiclass_brier"
                ]
                - development_baseline["multiclass_brier"]
            ),
        }
        for candidate in CANDIDATES
        if candidate != BASELINE
    }

    confirmations = []
    training_years = list(TRAINING_YEARS) + [DEVELOPMENT_YEAR]
    for evaluation_year in CONFIRMATION_YEARS:
        training = pl.concat([cohorts[year] for year in training_years])
        predictions = {
            candidate: _predict(
                training,
                cohorts[evaluation_year],
                player_type=player_type,
                candidate=candidate,
                regularization_c=selected[candidate],
            )
            for candidate in CANDIDATES
        }
        losses = {
            candidate: career_state_losses(prediction)
            for candidate, prediction in predictions.items()
        }
        comparisons = {}
        for candidate_index, candidate in enumerate(CANDIDATES):
            if candidate == BASELINE:
                continue
            comparisons[candidate] = {
                metric: _paired_interval(
                    losses[candidate],
                    losses[BASELINE],
                    column,
                    seed=(
                        20260910
                        + 1000 * evaluation_year
                        + 100 * (player_type == "pitcher")
                        + 10 * candidate_index
                        + metric_index
                    ),
                )
                for metric_index, (metric, column) in enumerate(
                    (
                        ("log_loss", "multiclass_log_loss"),
                        ("brier", "multiclass_brier"),
                    )
                )
            }
        confirmations.append(
            {
                "snapshot_year": evaluation_year,
                "target_year": evaluation_year + 1,
                "training_snapshot_years": list(training_years),
                "players": cohorts[evaluation_year].height,
                "scores": {
                    candidate: career_state_scores(prediction)
                    for candidate, prediction in predictions.items()
                },
                "paired_comparisons": comparisons,
            }
        )
        training_years.append(evaluation_year)

    decisions = {}
    for candidate in CANDIDATES:
        if candidate == BASELINE:
            continue
        development_pass = (
            development_delta[candidate]["log_loss"] < 0
            and development_delta[candidate]["brier"] <= 0
        )
        confirmation_pass = all(
            row["paired_comparisons"][candidate][metric][
                "paired_bootstrap_high"
            ]
            < 0
            for row in confirmations
            for metric in ("log_loss", "brier")
        )
        decisions[candidate] = {
            "development_point_gate_passed": development_pass,
            "both_confirmations_paired_gate_passed": confirmation_pass,
            "future_confirmation_candidate": development_pass and confirmation_pass,
        }
    return {
        "selected_regularization": selected,
        "development_scores": development_scores,
        "development_delta": development_delta,
        "rolling_confirmations": confirmations,
        "decisions": decisions,
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "prospect_development_state_test_complete",
        "plan": "docs/prospect-development-state-plan.md",
        "baseline": BASELINE,
        "candidates": CANDIDATES,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "shortened_2020_snapshot_excluded": True,
        "current_2026_used": False,
        "hitter": _one("hitter"),
        "pitcher": _one("pitcher"),
        "production_changed": False,
    }
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    def rows(player_type: str) -> str:
        values = []
        for confirmation in report[player_type]["rolling_confirmations"]:
            for candidate, comparison in confirmation["paired_comparisons"].items():
                decision = report[player_type]["decisions"][candidate]
                values.append(
                    f"| {player_type.title()} | {confirmation['target_year']} | "
                    f"{candidate} | {comparison['log_loss']['mean_delta']:+.6f} "
                    f"[{comparison['log_loss']['paired_bootstrap_low']:+.6f}, "
                    f"{comparison['log_loss']['paired_bootstrap_high']:+.6f}] | "
                    f"{comparison['brier']['mean_delta']:+.6f} "
                    f"[{comparison['brier']['paired_bootstrap_low']:+.6f}, "
                    f"{comparison['brier']['paired_bootstrap_high']:+.6f}] | "
                    f"{'Carry' if decision['future_confirmation_candidate'] else 'Reject'} |"
                )
        return "\n".join(values)

    OUTPUT_MD.write_text(
        f"""# Prospect development-state result

Status: research test complete; no current value changed.

The test adds four cutoff-safe development-history facts to the next-season ordered
career-state forecast and also checks whether a joint multinomial structure helps.
Regularization was selected on 2022-to-2023, then frozen for rolling 2023-to-2024 and
2024-to-2025 evaluation. Negative deltas beat the ordered level/exposure baseline.

| Group | Target | Candidate | Log-loss delta [95% paired interval] | Brier delta [95% paired interval] | Decision |
|---|---:|---|---:|---:|---|
{rows('hitter')}
{rows('pitcher')}

The gate requires development point improvement and both later paired intervals below
zero for both scores. These cohorts were previously inspected by related models, so a
passing result would only define a future confirmation candidate. It cannot change
current values. No 2026 outcome, organization, or outside FV is used.
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
