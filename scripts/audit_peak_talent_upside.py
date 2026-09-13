#!/usr/bin/env python3
"""Validate and materialize peak-rate upside probabilities around shrunken means."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_age_to_peak_talent import _fit_peak
from audit_one_year_talent_development import (
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    _predict,
)
from audit_peak_talent_ranking import _run_weights as _pitcher_run_weights
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA,
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.projection_composition import sequential_helmert_ilr_basis


ROOT = Path("reports/generated/age-to-peak-talent")
CURRENT_ROOT = Path("reports/generated/current-peak-talent/2026-09-08/tables")
OUTPUT = Path("reports/generated/peak-talent-upside")
CALIBRATION = Path("model_artifacts/peak-talent-run-calibration-v1.json")
CONFIRMATION_YEARS = (2023, 2024, 2025)
SELECTION_YEARS = (2018, 2019)
THRESHOLDS = {"above_average": 0.0, "impact": 10.0}
MIN_LIBRARY_ROWS = 500
MIN_GROUP_ROWS = 150


def _run_scores(probabilities: np.ndarray, *, player_type: str) -> np.ndarray:
    if player_type == "hitter":
        weights = np.asarray([
            0.0,
            NEUTRAL_WOBA_WEIGHTS["UBB"],
            NEUTRAL_WOBA_WEIGHTS["HBP"],
            NEUTRAL_WOBA_WEIGHTS["1B"],
            NEUTRAL_WOBA_WEIGHTS["2B"],
            NEUTRAL_WOBA_WEIGHTS["3B"],
            NEUTRAL_WOBA_WEIGHTS["HR"],
            0.0,
        ])
        return (probabilities @ weights - NEUTRAL_WOBA) * 600.0 / NEUTRAL_WOBA_SCALE
    return -(
        probabilities @ _pitcher_run_weights() - NEUTRAL_WOBA
    ) * 800.0 / NEUTRAL_WOBA_SCALE


def _target_probabilities(
    rows: list[dict[str, object]], components: tuple[str, ...]
) -> np.ndarray:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in components]
        for row in rows
    ])
    return counts / counts.sum(axis=1, keepdims=True)


def _evidence_band(value: float) -> str:
    if value < 200.0:
        return "under_200"
    if value < 500.0:
        return "200_to_499"
    return "500_plus"


def _rolling_errors(
    examples: pl.DataFrame,
    components: tuple[str, ...],
    decision: dict[str, object],
    calibration: dict[str, float],
    *,
    player_type: str,
) -> pl.DataFrame:
    basis = sequential_helmert_ilr_basis(len(components))
    frames: list[pl.DataFrame] = []
    years = sorted(examples.get_column("peak_window_end_year").unique().to_list())
    for year in years:
        if int(year) > 2025:
            continue
        train = examples.filter(pl.col("peak_window_end_year") < year).to_dicts()
        target = examples.filter(pl.col("peak_window_end_year") == year).to_dicts()
        if len(train) < MIN_LIBRARY_ROWS or not target:
            continue
        model = _fit_peak(
            train,
            components,
            str(decision["form"]),
            float(decision["alpha"]),
            basis,
        )
        predicted = _predict(
            model,
            target,
            components,
            str(decision["form"]),
            basis,
        )
        predicted_runs = _run_scores(predicted, player_type=player_type)
        predicted_runs += np.asarray([
            float(calibration[str(row["origin_age_band"])]) for row in target
        ])
        actual_runs = _run_scores(
            _target_probabilities(target, components), player_type=player_type
        )
        frames.append(pl.DataFrame({
            "player_id": [int(row["player_id"]) for row in target],
            "peak_window_end_year": [int(year)] * len(target),
            "origin_age_band": [str(row["origin_age_band"]) for row in target],
            "evidence_band": [
                _evidence_band(float(row["weighted_affiliated_exposure"]))
                for row in target
            ],
            "predicted_runs": predicted_runs,
            "actual_runs": actual_runs,
            "residual": actual_runs - predicted_runs,
        }))
    return pl.concat(frames, how="vertical_relaxed")


def _probability(
    library: pl.DataFrame,
    row: dict[str, object],
    threshold: float,
    method: str,
) -> float:
    pool = library
    if method in {"age_band", "age_evidence"}:
        candidate = pool.filter(
            pl.col("origin_age_band") == str(row["origin_age_band"])
        )
        if candidate.height >= MIN_GROUP_ROWS:
            pool = candidate
    if method == "age_evidence":
        candidate = pool.filter(pl.col("evidence_band") == str(row["evidence_band"]))
        if candidate.height >= MIN_GROUP_ROWS:
            pool = candidate
    needed = threshold - float(row["predicted_runs"])
    successes = pool.filter(pl.col("residual") > needed).height
    return (successes + 1.0) / (pool.height + 2.0)


def _score(probability: np.ndarray, outcome: np.ndarray) -> dict[str, float]:
    clipped = np.clip(probability, 1e-9, 1.0 - 1e-9)
    return {
        "brier": float(np.mean((clipped - outcome) ** 2)),
        "log_loss": float(
            -np.mean(outcome * np.log(clipped) + (1.0 - outcome) * np.log(1.0 - clipped))
        ),
        "mean_probability": float(np.mean(clipped)),
        "outcome_rate": float(np.mean(outcome)),
    }


def _evaluate(errors: pl.DataFrame, threshold: float) -> list[dict[str, object]]:
    replay = []
    for year in (*SELECTION_YEARS, *CONFIRMATION_YEARS):
        library = errors.filter(pl.col("peak_window_end_year") < year)
        test = errors.filter(pl.col("peak_window_end_year") == year)
        rows = test.to_dicts()
        outcome = (test.get_column("actual_runs").to_numpy() > threshold).astype(float)
        library_successes = library.filter(pl.col("actual_runs") > threshold).height
        constant = (library_successes + 1.0) / (library.height + 2.0)
        models = {"constant": _score(np.full(test.height, constant), outcome)}
        for method in ("global", "age_band", "age_evidence"):
            probability = np.asarray([
                _probability(library, row, threshold, method) for row in rows
            ])
            models[method] = _score(probability, outcome)
        replay.append({
            "peak_window_end_year": year,
            "players": test.height,
            "historical_library_rows": library.height,
            "models": models,
        })
    return replay


def _select(replay: list[dict[str, object]]) -> str:
    selection = [row for row in replay if row["peak_window_end_year"] in SELECTION_YEARS]
    return min(
        ("global", "age_band", "age_evidence"),
        key=lambda method: (
            np.mean([row["models"][method]["brier"] for row in selection]),
            np.mean([row["models"][method]["log_loss"] for row in selection]),
        ),
    )


def _promotion(
    replay: list[dict[str, object]], selected: str
) -> tuple[str, dict[str, object]]:
    confirmation = [
        row for row in replay if row["peak_window_end_year"] in CONFIRMATION_YEARS
    ]
    baseline = "global"
    deltas = {
        metric: [
            row["models"][selected][metric] - row["models"][baseline][metric]
            for row in confirmation
        ]
        for metric in ("brier", "log_loss")
    }
    passes = selected == baseline or all(
        sum(delta < 0 for delta in values) >= 2 and float(np.mean(values)) <= 0
        for values in deltas.values()
    )
    promoted = selected if passes else baseline
    return promoted, {
        "selected_method": selected,
        "promoted_method": promoted,
        "confirmation_rule": (
            "beat global residual distribution in at least two of three years and "
            "on pooled-mean delta for both Brier and log loss"
        ),
        "candidate_passed": passes,
        "mean_brier_delta_vs_global": float(np.mean(deltas["brier"])),
        "mean_log_loss_delta_vs_global": float(np.mean(deltas["log_loss"])),
    }


def _current_probabilities(
    current: pl.DataFrame,
    errors: pl.DataFrame,
    threshold: float,
    method: str,
) -> pl.Series:
    library = errors.filter(pl.col("peak_window_end_year") <= 2025)
    rows = current.select(
        pl.col("peak_runs_rate").alias("predicted_runs"),
        pl.when(pl.col("age_years") < 20)
        .then(pl.lit("under_20"))
        .when(pl.col("age_years") < 22)
        .then(pl.lit("20_to_21"))
        .otherwise(pl.lit("22_to_23"))
        .alias("origin_age_band"),
        pl.col("effective_evidence").map_elements(
            _evidence_band, return_dtype=pl.String
        ).alias("evidence_band"),
    ).to_dicts()
    return pl.Series([
        _probability(library, row, threshold, method) for row in rows
    ])


def main() -> int:
    peak_report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    configs = {
        "hitter": (
            ROOT / "tables" / "plate_appearances_examples.parquet",
            HITTER_COMPONENTS,
            CURRENT_ROOT / "current_peak_hitters.parquet",
        ),
        "pitcher": (
            ROOT / "tables" / "batters_faced_examples.parquet",
            PITCHER_COMPONENTS,
            CURRENT_ROOT / "current_peak_pitchers.parquet",
        ),
    }
    report: dict[str, object] = {
        "report_schema_version": "0.1",
        "status": "peak_upside_probability_audit",
        "public_rank_or_fv_used": False,
        "future_workload_used_as_weight": False,
        "thresholds_runs_above_average": THRESHOLDS,
        "player_types": {},
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for player_type, (example_path, components, current_path) in configs.items():
        examples = pl.read_parquet(example_path)
        errors = _rolling_errors(
            examples,
            components,
            peak_report[f"{player_type}s"]["selected"],
            calibration[f"{player_type}s"],
            player_type=player_type,
        )
        errors.write_parquet(OUTPUT / f"{player_type}_rolling_errors.parquet")
        current = pl.read_parquet(current_path)
        threshold_reports = {}
        added = []
        for name, threshold in THRESHOLDS.items():
            replay = _evaluate(errors, threshold)
            selected = _select(replay)
            promoted, promotion = _promotion(replay, selected)
            confirmation = [
                {
                    "peak_window_end_year": row["peak_window_end_year"],
                    "brier_delta_vs_global": (
                        row["models"][selected]["brier"]
                        - row["models"]["global"]["brier"]
                    ),
                    "log_loss_delta_vs_global": (
                        row["models"][selected]["log_loss"]
                        - row["models"]["global"]["log_loss"]
                    ),
                }
                for row in replay
                if row["peak_window_end_year"] in CONFIRMATION_YEARS
            ]
            global_vs_constant = {
                metric: [
                    row["models"]["global"][metric]
                    - row["models"]["constant"][metric]
                    for row in replay
                    if row["peak_window_end_year"] in CONFIRMATION_YEARS
                ]
                for metric in ("brier", "log_loss")
            }
            threshold_reports[name] = {
                **promotion,
                "global_probability_passed": all(
                    sum(delta < 0 for delta in values) >= 2
                    and float(np.mean(values)) < 0
                    for values in global_vs_constant.values()
                ),
                "global_vs_constant": {
                    metric: {
                        "wins": sum(delta < 0 for delta in values),
                        "mean_delta": float(np.mean(values)),
                    }
                    for metric, values in global_vs_constant.items()
                },
                "replay": replay,
                "confirmation": confirmation,
            }
            added.append(
                _current_probabilities(current, errors, threshold, promoted).alias(
                    f"peak_{name}_probability"
                )
            )
        current = current.with_columns(*added)
        supported = (
            (pl.col("as_of_level_group") != "MLB")
            & pl.col("age_years").is_not_null()
            & pl.col("age_years").is_between(16, 23, closed="both")
        )
        current = current.with_columns(
            *(
                pl.when(supported)
                .then(pl.col(f"peak_{name}_probability"))
                .otherwise(None)
                .alias(f"peak_{name}_probability")
                for name in THRESHOLDS
            )
        )
        current.write_parquet(OUTPUT / f"current_{player_type}_upside.parquet")
        current.write_csv(OUTPUT / f"current_{player_type}_upside.csv")
        current.filter(pl.col("prospect_peak_rate_rank") <= 100).sort(
            "prospect_peak_rate_rank"
        ).write_csv(OUTPUT / f"current_{player_type}_upside_top100.csv")
        report["player_types"][player_type] = {
            "rolling_error_rows": errors.height,
            "thresholds": threshold_reports,
        }
    report["status"] = (
        "validated_conditional_peak_upside"
        if all(
            threshold["global_probability_passed"]
            for details in report["player_types"].values()
            for threshold in details["thresholds"].values()
        )
        else "diagnostic_peak_upside"
    )
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        player_type: {
            name: {
                "selected": value["selected_method"],
                "promoted": value["promoted_method"],
            }
            for name, value in details["thresholds"].items()
        }
        for player_type, details in report["player_types"].items()
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
