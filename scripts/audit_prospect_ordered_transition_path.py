#!/usr/bin/env python3
"""Compare a four-year ordered transition path with a direct endpoint model."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.prospect_arrival import build_arrival_cohort
from universal_baseball.prospect_career_state import (
    build_career_transition_rows,
    career_state_scores,
    fit_transition_hazard_model,
    predict_independent_ordered_state,
    predict_transition_path,
)


ROOT = Path("reports/generated")
OUTPUT_JSON = Path("docs/prospect-ordered-transition-path-result.json")
OUTPUT_MD = Path("docs/prospect-ordered-transition-path-result.md")
C_GRID = (0.03, 0.1, 0.3, 1.0)
HORIZONS = (1, 2, 3, 4)


def _history_stats() -> pl.DataFrame:
    paths = sorted((ROOT / "opportunity-history-sources-v2/tables").glob(
        "*/affiliated_season_stats.parquet"
    ))
    return pl.concat([pl.read_parquet(path) for path in paths], how="vertical_relaxed")


def _data(player_type: str) -> dict[int, dict[int, pl.DataFrame]]:
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
        year: {
            horizon: build_arrival_cohort(
                snapshots, stats, membership, skill, debut,
                snapshot_year=year, horizon=horizon, player_type=player_type,
                demographics=demographics,
            )
            for horizon in HORIZONS
        }
        for year in (2018, 2019, 2021)
    }


def _transition_training(cohorts: dict[int, pl.DataFrame], year: int) -> pl.DataFrame:
    rows = build_career_transition_rows(cohorts, snapshot_year=year)
    feature_columns = [
        column for column in cohorts[1].columns
        if column not in {
            "arrived_within_horizon", "meaningful_role_within_horizon",
            "established_role_within_horizon",
            "positive_component_role_within_horizon",
        }
    ]
    features = cohorts[1].select(*feature_columns).with_columns(
        pl.lit(year).alias("snapshot_year")
    )
    return rows.join(
        features, on=["snapshot_year", "player_id"], how="left", validate="m:1"
    )


def _scores(
    data: dict[int, dict[int, pl.DataFrame]], *, player_type: str,
    method: str, regularization_c: float, evaluation_year: int, horizon: int = 4,
) -> dict[str, float | int]:
    if method == "ordered_transition":
        training = _transition_training(data[2018], 2018)
        fit = fit_transition_hazard_model(
            training, player_type=player_type, feature_set="level_exposure",
            regularization_c=regularization_c,
        )
        prediction = predict_transition_path(
            fit, data[evaluation_year][1], horizon=horizon
        ).join(
            data[evaluation_year][horizon].select(
                "player_id", "arrived_within_horizon",
                "meaningful_role_within_horizon", "established_role_within_horizon",
            ), on="player_id", how="inner", validate="1:1", suffix="_target",
        )
        # Horizon-one outcome columns already exist in the prediction input.
        prediction = prediction.drop(
            "arrived_within_horizon", "meaningful_role_within_horizon",
            "established_role_within_horizon",
        ).rename({
            "arrived_within_horizon_target": "arrived_within_horizon",
            "meaningful_role_within_horizon_target": "meaningful_role_within_horizon",
            "established_role_within_horizon_target": "established_role_within_horizon",
        })
    else:
        prediction = predict_independent_ordered_state(
            data[2018][horizon], data[evaluation_year][horizon],
            player_type=player_type, feature_set="level_exposure",
            regularization_c=regularization_c,
        )
    return career_state_scores(prediction)


def _one(player_type: str) -> dict[str, object]:
    data = _data(player_type)
    development = {}
    selected = {}
    for method in ("direct_endpoint", "ordered_transition"):
        development[method] = {
            str(c): _scores(
                data, player_type=player_type, method=method,
                regularization_c=c, evaluation_year=2019,
            )
            for c in C_GRID
        }
        selected[method] = min(
            C_GRID,
            key=lambda c: development[method][str(c)]["multiclass_log_loss"],
        )
    confirmation = {
        method: _scores(
            data, player_type=player_type, method=method,
            regularization_c=selected[method], evaluation_year=2021,
        )
        for method in ("direct_endpoint", "ordered_transition")
    }
    selected_development = {
        method: development[method][str(selected[method])]
        for method in ("direct_endpoint", "ordered_transition")
    }
    development_delta = {
        "transition_minus_direct_log_loss": (
            selected_development["ordered_transition"]["multiclass_log_loss"]
            - selected_development["direct_endpoint"]["multiclass_log_loss"]
        ),
        "transition_minus_direct_brier": (
            selected_development["ordered_transition"]["multiclass_brier"]
            - selected_development["direct_endpoint"]["multiclass_brier"]
        ),
    }
    delta = {
        "transition_minus_direct_log_loss": (
            confirmation["ordered_transition"]["multiclass_log_loss"]
            - confirmation["direct_endpoint"]["multiclass_log_loss"]
        ),
        "transition_minus_direct_brier": (
            confirmation["ordered_transition"]["multiclass_brier"]
            - confirmation["direct_endpoint"]["multiclass_brier"]
        ),
    }
    horizon_diagnostics = []
    for evaluation_year in (2019, 2021):
        for horizon in HORIZONS:
            direct = _scores(
                data, player_type=player_type, method="direct_endpoint",
                regularization_c=selected["direct_endpoint"],
                evaluation_year=evaluation_year, horizon=horizon,
            )
            transition = _scores(
                data, player_type=player_type, method="ordered_transition",
                regularization_c=selected["ordered_transition"],
                evaluation_year=evaluation_year, horizon=horizon,
            )
            horizon_diagnostics.append({
                "evaluation_snapshot": evaluation_year,
                "horizon": horizon,
                "target_through_year": evaluation_year + horizon,
                "transition_minus_direct_log_loss": (
                    transition["multiclass_log_loss"] - direct["multiclass_log_loss"]
                ),
                "transition_minus_direct_brier": (
                    transition["multiclass_brier"] - direct["multiclass_brier"]
                ),
            })
    return {
        "training_snapshot": 2018, "development_snapshot": 2019,
        "confirmation_snapshot": 2021,
        "selected_regularization": selected,
        "development_grid": development,
        "selected_development": selected_development,
        "development_delta": development_delta,
        "confirmation": confirmation,
        "horizon_diagnostics": horizon_diagnostics,
        **delta,
        "promotion_gate_passed": bool(
            development_delta["transition_minus_direct_log_loss"] < 0
            and development_delta["transition_minus_direct_brier"] <= 0
            and delta["transition_minus_direct_log_loss"] < 0
            and delta["transition_minus_direct_brier"] <= 0
        ),
    }


def main() -> int:
    report = {
        "report_schema_version": "0.1",
        "status": "ordered_four_year_transition_path_test_complete",
        "horizon_years": 4, "current_2026_used": False,
        "hitter": _one("hitter"), "pitcher": _one("pitcher"),
        "production_changed": False,
        "limitations": [
            "The transition fit uses initial prospect features advanced only by age and elapsed year.",
            "Future minor-league production and post-arrival MLB skill are not forecast as covariates.",
            "The 2021 confirmation cohort has appeared in earlier prospect diagnostics.",
        ],
    }
    OUTPUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    def line(name: str) -> str:
        value = report[name]
        direct = value["confirmation"]["direct_endpoint"]
        transition = value["confirmation"]["ordered_transition"]
        return (
            f"| {name.title()} | "
            f"{value['development_delta']['transition_minus_direct_log_loss']:+.6f} | "
            f"{value['development_delta']['transition_minus_direct_brier']:+.6f} | "
            f"{value['transition_minus_direct_log_loss']:+.6f} | "
            f"{value['transition_minus_direct_brier']:+.6f} | "
            f"{'Pass' if value['promotion_gate_passed'] else 'Reject'} |"
        )
    OUTPUT_MD.write_text(f"""# Ordered four-year prospect transition path

Status: research comparison complete; no player value changed.

The challenger fits forward-only annual transitions among no MLB, fringe,
meaningful and established career milestones, then propagates one probability
simplex for four years. It is compared with a direct four-year endpoint model using
the same initial level/exposure features. Regularization was selected on the 2019
cohort; the 2021 cohort and 2022-2025 outcomes were then scored unchanged.

| Group | 2019 log-loss delta | 2019 Brier delta | 2021 log-loss delta | 2021 Brier delta | Decision |
|---|---:|---:|---:|---:|---|
{line('hitter')}
{line('pitcher')}

The path is coherent and cannot move backward. It does not yet model future MiLB
production or post-arrival MLB skill, so it cannot replace the current safeguard
unless both proper scores improve. No outside FV enters the test.

The horizon diagnostic does not support blaming the full reversal on the shortened
2020 season. The hitter path slightly wins the immediate 2020 target and then loses
at years two through four; the pitcher path loses throughout that development cohort.
The likely missing piece is updated development/MLB evidence after the initial
snapshot, not a one-year exception.
""", encoding="utf-8")
    print(json.dumps({name: report[name] for name in ("hitter", "pitcher")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
