#!/usr/bin/env python3
"""Test validated high-minors process inputs directly against peak outcomes."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from audit_age_to_peak_talent import (
    PITCHER_COMPONENTS,
    _player_score,
    _player_uncertainty,
)
from audit_one_year_talent_development import _score
from audit_one_year_talent_development import _serialize_fitted_model
from audit_pitcher_process_challenger import (
    _fit,
    _load_process,
    _predict,
    _process_features,
)
from universal_baseball.projection_composition import sequential_helmert_ilr_basis


ORIGINS = (2018, 2019, 2021, 2022)
OUT = Path("reports/generated/peak-pitcher-process")
ARTIFACT = Path("model_artifacts/peak-pitcher-process-v1.json")


def _cohorts() -> dict[int, pl.DataFrame]:
    examples = pl.read_parquet(
        "reports/generated/age-to-peak-talent/tables/batters_faced_examples.parquet"
    ).filter(pl.col("peak_window_end_year") < 2026)
    process = _process_features(_load_process())
    return {
        origin: examples.filter(pl.col("origin_year") == origin).join(
            process.filter(pl.col("season") == origin).drop("season"),
            on=["player_id", "level_group"], how="inner", validate="m:1",
        )
        for origin in ORIGINS
    }


def _metrics(prediction, rows: list[dict[str, object]]) -> dict[str, float]:
    player = _player_score(prediction, rows, PITCHER_COMPONENTS)
    event = _score(prediction, rows, PITCHER_COMPONENTS)
    return {
        "player_log_loss": float(player["log_loss"]),
        "player_brier": float(player["brier"]),
        "event_log_loss": float(event["log_loss"]),
        "event_brier": float(event["brier"]),
    }


def _evaluate(
    cohorts: dict[int, pl.DataFrame], *, target_origin: int, basis
) -> dict[str, object]:
    target_frame = cohorts[target_origin]
    target_ids = set(target_frame.get_column("player_id").to_list())
    training_frame = pl.concat([
        frame.filter(~pl.col("player_id").is_in(target_ids))
        for origin, frame in cohorts.items() if origin < target_origin
    ])
    training = training_frame.to_dicts()
    target = target_frame.to_dicts()
    baseline_model = _fit(training, basis, 100.0, None)
    candidate_model = _fit(training, basis, 100.0, "all_process")
    baseline_prediction = _predict(baseline_model, target, basis, None)
    candidate_prediction = _predict(candidate_model, target, basis, "all_process")
    baseline = _metrics(baseline_prediction, target)
    candidate = _metrics(candidate_prediction, target)
    return {
        "target_origin": target_origin,
        "training_rows": training_frame.height,
        "target_players": target_frame.height,
        "same_player_training_rows_excluded": sum(
            frame.filter(pl.col("player_id").is_in(target_ids)).height
            for origin, frame in cohorts.items() if origin < target_origin
        ),
        "delta": {key: candidate[key] - baseline[key] for key in baseline},
        "uncertainty": _player_uncertainty(
            candidate_prediction, baseline_prediction, target, PITCHER_COMPONENTS
        ),
    }


def main() -> int:
    cohorts = _cohorts()
    basis = sequential_helmert_ilr_basis(len(PITCHER_COMPONENTS))
    development = _evaluate(cohorts, target_origin=2019, basis=basis)
    replay = [
        _evaluate(cohorts, target_origin=origin, basis=basis)
        for origin in (2021, 2022)
    ]
    keys = ("player_log_loss", "player_brier", "event_log_loss", "event_brier")
    development_passed = all(development["delta"][key] < 0 for key in keys)
    wins = {key: sum(row["delta"][key] < 0 for row in replay) for key in keys}
    uncertainty_passes = sum(
        row["uncertainty"]["log_loss_delta_p975"] <= 0
        and row["uncertainty"]["brier_delta_p975"] <= 0
        for row in replay
    )
    passed = (
        development_passed
        and all(value == len(replay) for value in wins.values())
        and uncertainty_passes >= 1
    )
    final_rows = pl.concat([cohorts[origin] for origin in ORIGINS]).to_dicts()
    final_model = _fit(final_rows, basis, 100.0, "all_process")
    final_reference_model = _fit(final_rows, basis, 100.0, None)
    current_fit = _serialize_fitted_model(
        final_model,
        form="component_development",
        alpha=100.0,
        basis=basis,
        training_rows=len(final_rows),
        training_origins=list(ORIGINS),
    )
    current_fit.update({
        "feature_family": "component_development_plus_pitch_process",
        "process_feature_set": "all_process",
    })
    current_reference_fit = _serialize_fitted_model(
        final_reference_model,
        form="component_development",
        alpha=100.0,
        basis=basis,
        training_rows=len(final_rows),
        training_origins=list(ORIGINS),
    )
    report = {
        "report_schema_version": "0.1",
        "baseline": "frozen component_development with alpha 100",
        "candidate": "same model plus validated all_process features with alpha 100",
        "development": development,
        "replay": replay,
        "wins": wins,
        "uncertainty_passes": uncertainty_passes,
        "promotion": "pass" if passed else "reject",
        "public_rank_or_fv_used": False,
        "future_workload_or_arrival_used": False,
        "player_overlap_between_fit_and_score": False,
        "cohort_rows": {str(origin): frame.height for origin, frame in cohorts.items()},
        "current_fit": current_fit,
        "current_reference_fit": current_reference_fit,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    if passed:
        ARTIFACT.write_text(
            json.dumps({
                "artifact_schema_version": "0.1",
                "status": "promoted_optional_high_minors_peak_input",
                "source_report": str(OUT / "report.json"),
                "source_boundary": "certified full-season high-minors process only",
                "fallback": "frozen results-only peak pitcher model",
                "fit": current_fit,
                "same_cohort_reference_fit": current_reference_fit,
            }, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
