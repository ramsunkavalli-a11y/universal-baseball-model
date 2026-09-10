#!/usr/bin/env python3
"""Audit minor-to-MLB position transitions for arriving hitter prospects."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.prospect_position_transition import (
    POSITION_GROUPS,
    fit_transition_probabilities,
    multiclass_scores,
    position_group,
    predict_transition,
)


PRIOR_WEIGHTS = (10.0, 25.0, 50.0)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--historical-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/historical/reports/generated/"
            "position-role-historical-source/tables/historical_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--confirmation-path",
        type=Path,
        default=Path(
            "reports/generated/position-capacity-source/2025/reports/generated/"
            "position-role-2025-confirmation-source/tables/"
            "position_role_2025_fielding_usage.parquet"
        ),
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-position-transition-result.json"),
    )
    return parser.parse_args()


def _dominant(frame: pl.DataFrame) -> pl.DataFrame:
    return (
        frame.with_columns(
            pl.col("position_abbreviation").map_elements(
                position_group, return_dtype=pl.String
            ).alias("position_group"),
            pl.when(pl.col("games_started") > 0)
            .then(pl.col("games_started"))
            .otherwise(pl.col("games_played"))
            .alias("position_exposure"),
        )
        .filter(pl.col("position_group").is_not_null())
        .group_by("player_id", "position_group")
        .agg(pl.col("position_exposure").sum())
        .with_columns(
            pl.col("position_group")
            .replace_strict(
                {value: index for index, value in enumerate(POSITION_GROUPS)},
                return_dtype=pl.Int64,
            )
            .alias("group_order")
        )
        .sort(
            ["player_id", "position_exposure", "group_order"],
            descending=[False, True, False],
        )
        .unique("player_id", keep="first", maintain_order=True)
        .select("player_id", "position_group", "position_exposure")
    )


def _cohort(usage: pl.DataFrame, origin_year: int) -> pl.DataFrame:
    origin = _dominant(
        usage.filter(
            (pl.col("season") == origin_year) & (pl.col("level_group") != "MLB")
        )
    ).rename(
        {
            "position_group": "origin_group",
            "position_exposure": "origin_exposure",
        }
    )
    destination = _dominant(
        usage.filter(
            pl.col("season").is_between(origin_year + 1, origin_year + 2)
            & (pl.col("level_group") == "MLB")
        )
    ).rename(
        {
            "position_group": "destination_group",
            "position_exposure": "destination_exposure",
        }
    )
    return (
        origin.join(destination, on="player_id", how="inner", validate="1:1")
        .with_columns(pl.lit(origin_year).alias("origin_year"))
        .sort("player_id")
    )


def _fit_score(training: pl.DataFrame, evaluation: pl.DataFrame, weight: float) -> dict:
    origins = training.get_column("origin_group").to_list()
    destinations = training.get_column("destination_group").to_list()
    marginal, transition, counts = fit_transition_probabilities(
        origins, destinations, prior_weight=weight
    )
    evaluation_origins = evaluation.get_column("origin_group").to_list()
    evaluation_destinations = evaluation.get_column("destination_group").to_list()
    baseline_probability, candidate_probability = predict_transition(
        evaluation_origins, marginal=marginal, transition=transition
    )
    return {
        "prior_weight": weight,
        "baseline": multiclass_scores(evaluation_destinations, baseline_probability),
        "candidate": multiclass_scores(evaluation_destinations, candidate_probability),
        "marginal": dict(zip(POSITION_GROUPS, marginal.tolist(), strict=True)),
        "transition_probabilities": {
            origin: dict(zip(POSITION_GROUPS, transition[index].tolist(), strict=True))
            for index, origin in enumerate(POSITION_GROUPS)
        },
        "transition_counts": {
            origin: {
                destination: int(counts[row, column])
                for column, destination in enumerate(POSITION_GROUPS)
            }
            for row, origin in enumerate(POSITION_GROUPS)
        },
        "baseline_probability": baseline_probability,
        "candidate_probability": candidate_probability,
    }


def _bootstrap(destinations: list[str], baseline: np.ndarray, candidate: np.ndarray) -> dict:
    lookup = {value: index for index, value in enumerate(POSITION_GROUPS)}
    observed = np.asarray([lookup[value] for value in destinations], dtype=int)
    one_hot = np.eye(len(POSITION_GROUPS))[observed]
    brier_delta = np.square(candidate - one_hot).sum(axis=1) - np.square(
        baseline - one_hot
    ).sum(axis=1)
    log_delta = -np.log(np.clip(candidate[np.arange(len(observed)), observed], 1e-12, 1)) + np.log(
        np.clip(baseline[np.arange(len(observed)), observed], 1e-12, 1)
    )
    rng = np.random.default_rng(20260909)
    indices = rng.integers(0, len(observed), size=(2_000, len(observed)))

    def summarize(values: np.ndarray) -> dict:
        samples = values[indices].mean(axis=1)
        return {
            "difference": float(values.mean()),
            "ci_low": float(np.quantile(samples, 0.025)),
            "ci_high": float(np.quantile(samples, 0.975)),
            "probability_candidate_better": float(np.mean(samples < 0)),
        }

    return {"resamples": 2_000, "log_loss": summarize(log_delta), "brier": summarize(brier_delta)}


def _calibration_bins(destinations: list[str], probability: np.ndarray) -> list[dict]:
    lookup = {value: index for index, value in enumerate(POSITION_GROUPS)}
    observed_index = np.asarray([lookup[value] for value in destinations], dtype=int)
    observed = np.eye(len(POSITION_GROUPS))[observed_index].ravel()
    predicted = probability.ravel()
    ordered = np.argsort(predicted, kind="stable")
    rows = []
    for number, indices in enumerate(np.array_split(ordered, 5), start=1):
        rows.append(
            {
                "bin": number,
                "predictions": int(len(indices)),
                "mean_probability": float(predicted[indices].mean()),
                "observed_rate": float(observed[indices].mean()),
            }
        )
    return rows


def _serializable(result: dict) -> dict:
    return {key: value for key, value in result.items() if not key.endswith("_probability")}


def main() -> int:
    args = _args()
    usage = pl.concat(
        [pl.read_parquet(args.historical_path), pl.read_parquet(args.confirmation_path)],
        how="vertical_relaxed",
    )
    cohorts = {year: _cohort(usage, year) for year in (2021, 2022, 2023)}
    development = [
        _fit_score(cohorts[2021], cohorts[2022], weight) for weight in PRIOR_WEIGHTS
    ]
    passing = [
        result
        for result in development
        if result["candidate"]["log_loss"] < result["baseline"]["log_loss"]
        and result["candidate"]["brier"] <= result["baseline"]["brier"]
    ]
    selected = min(passing, key=lambda result: result["candidate"]["log_loss"], default=None)
    selected_weight = selected["prior_weight"] if selected else PRIOR_WEIGHTS[-1]
    outer_training = pl.concat([cohorts[2021], cohorts[2022]])
    outer = _fit_score(outer_training, cohorts[2023], selected_weight)
    destinations = cohorts[2023].get_column("destination_group").to_list()
    bootstrap = _bootstrap(
        destinations, outer["baseline_probability"], outer["candidate_probability"]
    )
    retained = (
        cohorts[2023]
        .with_columns((pl.col("origin_group") == pl.col("destination_group")).alias("retained"))
        .group_by("origin_group")
        .agg(pl.len().alias("players"), pl.col("retained").mean().alias("retention_rate"))
        .sort("origin_group")
        .to_dicts()
    )
    promoted = bool(
        outer["candidate"]["log_loss"] < outer["baseline"]["log_loss"]
        and outer["candidate"]["brier"] < outer["baseline"]["brier"]
    )
    report = {
        "report_schema_version": "0.1",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "prospect_position_transition_outer_test_complete",
        "contract": "docs/prospect-position-transition-plan.md",
        "chronology": {
            "development_train_origin_years": [2021],
            "development_evaluate_origin_year": 2022,
            "outer_train_origin_years": [2021, 2022],
            "outer_evaluate_origin_year": 2023,
            "destination_horizon_years": 2,
        },
        "cohort_players": {str(year): cohort.height for year, cohort in cohorts.items()},
        "development": [_serializable(result) for result in development],
        "selected_prior_weight": selected_weight,
        "development_candidate_passed": selected is not None,
        "outer": _serializable(outer),
        "outer_paired_bootstrap": bootstrap,
        "outer_candidate_calibration": _calibration_bins(
            destinations, outer["candidate_probability"]
        ),
        "outer_retention_by_origin": retained,
        "decision": {
            "private_transition_sensitivity_authorized": promoted,
            "published_value_change_authorized": False,
        },
        "boundaries": {
            "outside_fv_used": False,
            "non_arrivals_included": False,
            "organization_or_depth_used": False,
            "subjective_position_adjustment_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
