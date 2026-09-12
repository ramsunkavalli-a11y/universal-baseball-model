#!/usr/bin/env python3
"""Build empirical peak-rate intervals from rolling historical player errors."""

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
from universal_baseball.hitter_v2_evaluation import (
    NEUTRAL_WOBA_SCALE,
    NEUTRAL_WOBA_WEIGHTS,
)
from universal_baseball.projection_composition import sequential_helmert_ilr_basis


ROOT = Path("reports/generated/age-to-peak-talent")
REPLAY_END_YEARS = (2018, 2019, 2023, 2024, 2025)


def _run_residuals(
    predicted: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    *,
    player_type: str,
    pitcher_other_weight: float | None = None,
) -> np.ndarray:
    counts = np.asarray([
        [float(row[f"target_{component}"]) for component in components] for row in rows
    ])
    target = counts / counts.sum(axis=1)[:, None]
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
        return (target - predicted) @ weights * 600.0 / NEUTRAL_WOBA_SCALE
    if pitcher_other_weight is None:
        raise ValueError("pitcher residual conversion requires other-BF run weight")
    weights = np.asarray([
        0.0,
        NEUTRAL_WOBA_WEIGHTS["UBB"],
        NEUTRAL_WOBA_WEIGHTS["HBP"],
        NEUTRAL_WOBA_WEIGHTS["HR"],
        float(pitcher_other_weight),
    ])
    return -(target - predicted) @ weights * 800.0 / NEUTRAL_WOBA_SCALE


def _replay_errors(
    examples: pl.DataFrame,
    components: tuple[str, ...],
    decision: dict[str, object],
    *,
    player_type: str,
    pitcher_other_weight: float | None = None,
) -> pl.DataFrame:
    basis = sequential_helmert_ilr_basis(len(components))
    frames = []
    for end_year in REPLAY_END_YEARS:
        train = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        target = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
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
        frames.append(pl.DataFrame({
            "player_id": [int(row["player_id"]) for row in target],
            "peak_window_end_year": [end_year] * len(target),
            "level_group": [str(row["level_group"]) for row in target],
            "origin_age_band": [str(row["origin_age_band"]) for row in target],
            "run_rate_residual": _run_residuals(
                predicted,
                target,
                components,
                player_type=player_type,
                pitcher_other_weight=pitcher_other_weight,
            ),
        }))
    return pl.concat(frames, how="vertical_relaxed").with_columns(
        pl.lit(player_type).alias("player_type")
    )


def _quantiles(errors: pl.DataFrame) -> pl.DataFrame:
    return (
        errors.group_by("player_type", "origin_age_band")
        .agg(
            pl.len().alias("historical_players"),
            pl.col("run_rate_residual").quantile(0.10).alias("residual_p10"),
            pl.col("run_rate_residual").median().alias("residual_p50"),
            pl.col("run_rate_residual").quantile(0.90).alias("residual_p90"),
        )
        .sort("player_type", "origin_age_band")
    )


def _leave_one_cohort_out_coverage(errors: pl.DataFrame) -> list[dict[str, object]]:
    rows = []
    for player_type in errors.get_column("player_type").unique().sort():
        typed = errors.filter(pl.col("player_type") == player_type)
        for end_year in REPLAY_END_YEARS:
            train = typed.filter(pl.col("peak_window_end_year") != end_year)
            test = typed.filter(pl.col("peak_window_end_year") == end_year)
            quantiles = _quantiles(train).select(
                "origin_age_band", "residual_p10", "residual_p90"
            )
            joined = test.join(quantiles, on="origin_age_band", how="left")
            covered = joined.filter(
                pl.col("run_rate_residual").is_between(
                    pl.col("residual_p10"), pl.col("residual_p90"), closed="both"
                )
            ).height
            rows.append({
                "player_type": str(player_type),
                "peak_window_end_year": end_year,
                "players": joined.height,
                "empirical_80_interval_coverage": covered / joined.height,
            })
    return rows


def _run_calibration_test(
    examples: pl.DataFrame,
    components: tuple[str, ...],
    decision: dict[str, object],
    *,
    player_type: str,
    pitcher_other_weight: float | None = None,
) -> dict[str, object]:
    basis = sequential_helmert_ilr_basis(len(components))
    train = examples.filter(pl.col("peak_window_end_year") <= 2014).to_dicts()
    development = examples.filter(
        pl.col("peak_window_end_year").is_between(2015, 2017, closed="both")
    ).to_dicts()
    development_model = _fit_peak(
        train,
        components,
        str(decision["form"]),
        float(decision["alpha"]),
        basis,
    )
    development_residual = _run_residuals(
        _predict(
            development_model,
            development,
            components,
            str(decision["form"]),
            basis,
        ),
        development,
        components,
        player_type=player_type,
        pitcher_other_weight=pitcher_other_weight,
    )
    development_frame = pl.DataFrame({
        "origin_age_band": [str(row["origin_age_band"]) for row in development],
        "residual": development_residual,
    })
    corrections = {
        str(row["origin_age_band"]): float(row["correction"])
        for row in development_frame.group_by("origin_age_band").agg(
            pl.col("residual").median().alias("correction")
        ).to_dicts()
    }
    replay = []
    for end_year in REPLAY_END_YEARS:
        prior = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        target = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
        model = _fit_peak(
            prior,
            components,
            str(decision["form"]),
            float(decision["alpha"]),
            basis,
        )
        candidate = _predict(
            model,
            target,
            components,
            str(decision["form"]),
            basis,
        )
        baseline = np.asarray([
            [float(row[f"p_{component}"]) for component in components] for row in target
        ])
        candidate_residual = _run_residuals(
            candidate,
            target,
            components,
            player_type=player_type,
            pitcher_other_weight=pitcher_other_weight,
        )
        baseline_residual = _run_residuals(
            baseline,
            target,
            components,
            player_type=player_type,
            pitcher_other_weight=pitcher_other_weight,
        )
        correction = np.asarray([
            corrections[str(row["origin_age_band"])] for row in target
        ])
        calibrated_residual = candidate_residual - correction

        def metrics(residual: np.ndarray) -> dict[str, float]:
            return {
                "mae": float(np.mean(np.abs(residual))),
                "rmse": float(np.sqrt(np.mean(residual**2))),
                "mean_error": float(np.mean(residual)),
            }

        replay.append({
            "peak_window_end_year": end_year,
            "players": len(target),
            "carry_forward": metrics(baseline_residual),
            "uncalibrated": metrics(candidate_residual),
            "development_age_band_calibrated": metrics(calibrated_residual),
        })
    return {
        "development_age_band_corrections": corrections,
        "replay": replay,
        "calibrated_mae_wins_vs_uncalibrated": sum(
            row["development_age_band_calibrated"]["mae"]
            < row["uncalibrated"]["mae"]
            for row in replay
        ),
        "calibrated_rmse_wins_vs_uncalibrated": sum(
            row["development_age_band_calibrated"]["rmse"]
            < row["uncalibrated"]["rmse"]
            for row in replay
        ),
        "calibrated_mae_wins_vs_carry": sum(
            row["development_age_band_calibrated"]["mae"]
            < row["carry_forward"]["mae"]
            for row in replay
        ),
        "calibrated_rmse_wins_vs_carry": sum(
            row["development_age_band_calibrated"]["rmse"]
            < row["carry_forward"]["rmse"]
            for row in replay
        ),
    }


def main() -> int:
    report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    hitters = _replay_errors(
        pl.read_parquet(ROOT / "tables" / "plate_appearances_examples.parquet"),
        HITTER_COMPONENTS,
        report["hitters"]["selected"],
        player_type="hitter",
    )
    current_pitchers = pl.read_parquet(
        "reports/generated/current-basic-talent/2026-09-08/tables/current_pitcher_talent.parquet"
    )
    known = (
        current_pitchers.get_column("predicted_ubb_rate").to_numpy()
        * NEUTRAL_WOBA_WEIGHTS["UBB"]
        + current_pitchers.get_column("predicted_hbp_rate").to_numpy()
        * NEUTRAL_WOBA_WEIGHTS["HBP"]
        + current_pitchers.get_column("predicted_hr_rate").to_numpy()
        * NEUTRAL_WOBA_WEIGHTS["HR"]
    )
    other = current_pitchers.get_column("predicted_other_rate").to_numpy()
    present_runs = current_pitchers.get_column(
        "present_pitching_runs_per_800_bf"
    ).to_numpy()
    implied_other = (
        0.3188 - present_runs * NEUTRAL_WOBA_SCALE / 800.0 - known
    ) / other
    pitcher_other_weight = float(np.median(implied_other[np.isfinite(implied_other)]))
    pitchers = _replay_errors(
        pl.read_parquet(ROOT / "tables" / "batters_faced_examples.parquet"),
        PITCHER_COMPONENTS,
        report["pitchers"]["selected"],
        player_type="pitcher",
        pitcher_other_weight=pitcher_other_weight,
    )
    errors = pl.concat([hitters, pitchers], how="vertical_relaxed")
    quantiles = _quantiles(errors)
    output = ROOT / "uncertainty"
    output.mkdir(parents=True, exist_ok=True)
    errors.write_parquet(output / "replay_player_errors.parquet")
    quantiles.write_csv(output / "age_band_run_rate_intervals.csv")
    uncertainty_report = {
        "report_schema_version": "0.1",
        "status": "empirical_peak_rate_uncertainty",
        "interval": "10th to 90th percentile held-out player run-rate residual",
        "point_estimate_changed": False,
        "pitcher_other_bf_run_weight": pitcher_other_weight,
        "leave_one_peak_cohort_out_coverage": _leave_one_cohort_out_coverage(errors),
        "age_band_intervals": quantiles.to_dicts(),
        "run_rate_calibration": {
            "hitters": _run_calibration_test(
                pl.read_parquet(
                    ROOT / "tables" / "plate_appearances_examples.parquet"
                ),
                HITTER_COMPONENTS,
                report["hitters"]["selected"],
                player_type="hitter",
            ),
            "pitchers": _run_calibration_test(
                pl.read_parquet(ROOT / "tables" / "batters_faced_examples.parquet"),
                PITCHER_COMPONENTS,
                report["pitchers"]["selected"],
                player_type="pitcher",
                pitcher_other_weight=pitcher_other_weight,
            ),
        },
    }
    (output / "report.json").write_text(
        json.dumps(uncertainty_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(uncertainty_report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
