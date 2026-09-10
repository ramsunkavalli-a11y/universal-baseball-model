#!/usr/bin/env python3
"""Test a transparent survivor-bias correction for pitcher component aging."""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
import json
import math
from pathlib import Path

import polars as pl

from fit_modern_pitcher_component_aging import _ages, _history
from universal_baseball.conditional_war_rates import apply_tango_pitcher_aging
from universal_baseball.pitcher_component_aging import (
    apply_fitted_pitcher_aging,
    attach_pitcher_survivorship_weights,
    build_adjacent_pitcher_profiles,
    build_pitcher_return_history,
    component_log_loss,
    fit_pitcher_component_aging,
    fit_pitcher_return_model,
)


AS_OF_DATE = date(2026, 9, 8)
DEVELOPMENT_MAX_TARGET = 2021
VALIDATION_START = 2022
OUTPUT = Path("docs/survivorship-adjusted-pitcher-aging-result.json")


def _return_scores(rows: pl.DataFrame, fit) -> dict[str, float | int]:
    predicted = []
    observed = []
    for row in rows.iter_rows(named=True):
        probe = pl.DataFrame(
            [{"source_age": row["source_age"], "source_bf": row["source_bf"]}]
        )
        probability = float(
            attach_pitcher_survivorship_weights(probe, fit).item(
                0, "predicted_pitcher_return_probability"
            )
        )
        predicted.append(probability)
        observed.append(float(row["returned_pitching"]))
    population = fit.population_probability
    epsilon = 1e-12

    def log_loss(probabilities: list[float]) -> float:
        return sum(
            -(outcome * math.log(max(epsilon, probability))
              + (1.0 - outcome) * math.log(max(epsilon, 1.0 - probability)))
            for probability, outcome in zip(probabilities, observed, strict=True)
        ) / len(observed)

    return {
        "rows": len(observed),
        "return_rate": sum(observed) / len(observed),
        "model_brier": sum(
            (probability - outcome) ** 2
            for probability, outcome in zip(predicted, observed, strict=True)
        ) / len(observed),
        "population_brier": sum((population - outcome) ** 2 for outcome in observed)
        / len(observed),
        "model_log_loss": log_loss(predicted),
        "population_log_loss": log_loss([population] * len(observed)),
    }


def _losses(pairs: pl.DataFrame, parameters, *, weighted: bool) -> dict[str, float]:
    weight_column = "survivorship_weight" if weighted else None
    predictors = {
        "no_aging": lambda source, _source_age, _target_age: source,
        "tango": lambda source, source_age, target_age: apply_tango_pitcher_aging(
            source, current_age=source_age, target_age=target_age
        ),
        "fitted": lambda source, source_age, target_age: apply_fitted_pitcher_aging(
            source,
            current_age=source_age,
            target_age=target_age,
            parameters=parameters,
        ),
    }
    return {
        name: component_log_loss(
            pairs, predictor, selection_weight_column=weight_column
        )
        for name, predictor in predictors.items()
    }


def main() -> int:
    career_root = Path("reports/generated/career-mlb-outcome-inventory")
    current_root = Path("reports/generated/current-mlb-skill-source")
    current_dated = current_root / AS_OF_DATE.isoformat()
    history = _history(career_root, current_root, AS_OF_DATE)
    ages = _ages((career_root / "raw", current_dated / "raw"))
    latest_completed = AS_OF_DATE.year - 1
    returns = build_pitcher_return_history(
        history,
        ages,
        complete_target_seasons=range(int(history["season"].min()) + 1, latest_completed + 1),
    )
    return_fit = fit_pitcher_return_model(
        returns,
        maximum_target_season=DEVELOPMENT_MAX_TARGET,
        age_band_width=3,
        prior_players=50.0,
        minimum_probability=0.05,
        maximum_weight=4.0,
    )
    pairs = attach_pitcher_survivorship_weights(
        build_adjacent_pitcher_profiles(history, ages, regression_bf=200.0),
        return_fit,
    )
    unweighted = fit_pitcher_component_aging(
        pairs,
        maximum_target_season=DEVELOPMENT_MAX_TARGET,
        regression_bf=200.0,
        ridge_weight=20_000.0,
        model_id="pitcher_adjacent_clr_unweighted_development_v1",
    )
    adjusted = fit_pitcher_component_aging(
        pairs,
        maximum_target_season=DEVELOPMENT_MAX_TARGET,
        regression_bf=200.0,
        ridge_weight=20_000.0,
        model_id="pitcher_adjacent_clr_survivorship_adjusted_development_v1",
        selection_weight_column="survivorship_weight",
    )
    validation = pairs.filter(pl.col("target_season") >= VALIDATION_START)
    return_validation = returns.filter(pl.col("target_season") >= VALIDATION_START)
    raw_unweighted = _losses(validation, unweighted, weighted=False)
    raw_adjusted = _losses(validation, adjusted, weighted=False)
    standardized_unweighted = _losses(validation, unweighted, weighted=True)
    standardized_adjusted = _losses(validation, adjusted, weighted=True)
    return_scores = _return_scores(return_validation, return_fit)
    selected = (
        standardized_adjusted["fitted"] < standardized_unweighted["fitted"]
        and standardized_adjusted["fitted"] < standardized_adjusted["no_aging"]
        and standardized_adjusted["fitted"] <= standardized_adjusted["tango"]
        and raw_adjusted["fitted"] <= min(raw_adjusted["no_aging"], raw_adjusted["tango"]) * 1.0005
        and return_scores["model_brier"] <= return_scores["population_brier"]
    )
    report = {
        "report_schema_version": "0.1",
        "status": "survivorship_adjusted_pitcher_aging_test_complete",
        "as_of_date": AS_OF_DATE.isoformat(),
        "development_target_seasons": [
            int(returns["target_season"].min()),
            DEVELOPMENT_MAX_TARGET,
        ],
        "validation_target_seasons": [VALIDATION_START, latest_completed],
        "return_model": {
            "method": "age-by-source-BF cells shrink to BF band, then population",
            "development_rows": returns.filter(
                pl.col("target_season") <= DEVELOPMENT_MAX_TARGET
            ).height,
            "validation": return_scores,
            "fit": {
                "population_probability": return_fit.population_probability,
                "age_band_width": return_fit.age_band_width,
                "prior_players": return_fit.prior_players,
                "minimum_probability": return_fit.minimum_probability,
                "maximum_weight": return_fit.maximum_weight,
            },
        },
        "validation_pairs": validation.height,
        "validation_pitchers": validation["player_id"].n_unique(),
        "survivorship_weight": {
            "minimum": float(validation["survivorship_weight"].min()),
            "median": float(validation["survivorship_weight"].median()),
            "maximum": float(validation["survivorship_weight"].max()),
        },
        "raw_returner_log_loss": {
            "unweighted_curve_scoreboard": raw_unweighted,
            "adjusted_curve_scoreboard": raw_adjusted,
        },
        "survival_standardized_log_loss": {
            "unweighted_curve_scoreboard": standardized_unweighted,
            "adjusted_curve_scoreboard": standardized_adjusted,
        },
        "adjusted_parameters": asdict(adjusted),
        "selection_rule": (
            "adjusted curve must beat the unweighted fitted curve, no aging and Tango "
            "on the survival-standardized score; avoid material raw-score damage; and "
            "the frozen return model must beat its population baseline"
        ),
        "adjusted_selected": selected,
        "estimand_boundary": (
            "inverse-return weighting changes the mix of observed adjacent rate pairs; "
            "non-returners remain zero only in the separate joint production score"
        ),
        "outside_fv_used": False,
        "production_changed": False,
    }
    OUTPUT.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
