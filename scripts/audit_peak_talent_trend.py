#!/usr/bin/env python3
"""Test whether prior-to-current component direction improves peak talent."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from audit_age_to_peak_talent import (
    INVALID_PEAK_END_YEARS,
    _fit_peak,
    _player_score,
    _player_uncertainty,
)
from audit_one_year_talent_development import (
    HITTER_COMPONENTS,
    PITCHER_COMPONENTS,
    _composition,
    _features,
    _hitter_components,
    _load_sources,
    _pitcher_components,
    _responses,
    _score,
    _serialize_fitted_model,
)
from audit_peak_talent_uncertainty import _run_residuals
from universal_baseball.level_component_translation import (
    build_translated_affiliated_profiles,
    fit_same_season_component_translation,
)
from universal_baseball.projection_composition import (
    ilr_transform,
    inverse_ilr_transform,
    sequential_helmert_ilr_basis,
)


ROOT = Path("reports/generated/age-to-peak-talent")
OUTPUT = Path("reports/generated/peak-talent-trend")
REPLAY_END_YEARS = (2018, 2019, 2023, 2024, 2025)


def _add_trend(
    examples: pl.DataFrame,
    source: pl.DataFrame,
    components: tuple[str, ...],
    *,
    exposure: str,
    regression: float,
) -> pl.DataFrame:
    frames = []
    for origin in examples.get_column("origin_year").unique().sort().to_list():
        current = examples.filter(pl.col("origin_year") == origin)
        players = current.select("player_id")
        if int(origin) - 1 == 2020:
            frames.append(
                current.with_columns(
                    pl.lit(0.0).alias("prior_effective_evidence"),
                    *(
                        pl.col(f"p_{name}").alias(f"prior_{name}")
                        for name in components
                    ),
                )
            )
            continue
        completed = tuple(
            year
            for year in range(int(source.get_column("season").min()), int(origin))
            if year != 2020
        )
        offsets = fit_same_season_component_translation(
            source,
            exposure_column=exposure,
            component_columns=components,
            completed_seasons=completed,
            minimum_level_exposure=30,
        ).offsets
        prior = build_translated_affiliated_profiles(
            players,
            source.filter(pl.col("season") != 2020),
            offsets,
            exposure_column=exposure,
            component_columns=components,
            current_season=int(origin) - 1,
            reference_season=int(origin) - 1,
            regression_exposure=regression,
        ).rename({
            "weighted_affiliated_exposure": "prior_effective_evidence",
            **{f"p_{name}": f"prior_{name}" for name in components},
        }).select(
            "player_id",
            "prior_effective_evidence",
            *(f"prior_{name}" for name in components),
        )
        frames.append(current.join(prior, on="player_id", how="left", validate="m:1"))
    joined = pl.concat(frames, how="vertical_relaxed")
    basis = sequential_helmert_ilr_basis(len(components))
    rows = []
    for row in joined.to_dicts():
        has_prior = float(row.get("prior_effective_evidence") or 0.0) > 0.0
        if has_prior:
            current_ilr = np.asarray(
                ilr_transform(_composition(row, components, "p_"), basis=basis)
            )
            prior_ilr = np.asarray(
                ilr_transform(
                    np.asarray([float(row[f"prior_{name}"]) for name in components]),
                    basis=basis,
                )
            )
            trend = current_ilr - prior_ilr
        else:
            trend = np.zeros(len(components) - 1)
        rows.append({
            **row,
            "has_prior_profile": float(has_prior),
            **{f"trend_ilr_{index}": float(value) for index, value in enumerate(trend)},
        })
    return pl.from_dicts(rows, infer_schema_length=None)


def _trend_features(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    basis: np.ndarray,
) -> np.ndarray:
    base = _features(rows, components, form, basis)
    trend = np.asarray([
        [
            float(row["has_prior_profile"]),
            *(float(row[f"trend_ilr_{index}"]) for index in range(len(components) - 1)),
        ]
        for row in rows
    ])
    return np.column_stack([base, trend])


def _fit_trend(
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    alpha: float,
    basis: np.ndarray,
) -> object:
    return make_pipeline(StandardScaler(), Ridge(alpha=alpha)).fit(
        _trend_features(rows, components, form, basis),
        _responses(rows, components, basis),
    )


def _predict_trend(
    model: object,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    basis: np.ndarray,
) -> np.ndarray:
    delta = model.predict(_trend_features(rows, components, form, basis))
    return np.asarray([
        inverse_ilr_transform(
            np.asarray(ilr_transform(_composition(row, components, "p_"), basis=basis))
            + delta[index],
            basis=basis,
        )
        for index, row in enumerate(rows)
    ])


def _comparison(
    candidate: np.ndarray,
    incumbent: np.ndarray,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
) -> dict[str, object]:
    candidate_player = _player_score(candidate, rows, components)
    incumbent_player = _player_score(incumbent, rows, components)
    candidate_event = _score(candidate, rows, components)
    incumbent_event = _score(incumbent, rows, components)
    return {
        "players": len(rows),
        "log_loss_delta": candidate_player["log_loss"] - incumbent_player["log_loss"],
        "brier_delta": candidate_player["brier"] - incumbent_player["brier"],
        "event_log_loss_delta": candidate_event["log_loss"] - incumbent_event["log_loss"],
        "event_brier_delta": candidate_event["brier"] - incumbent_event["brier"],
        "uncertainty": _player_uncertainty(
            candidate, incumbent, rows, components
        ),
    }


def _evaluate(
    examples: pl.DataFrame,
    components: tuple[str, ...],
    decision: dict[str, object],
    *,
    run_calibration: dict[str, float] | None = None,
) -> dict[str, object]:
    basis = sequential_helmert_ilr_basis(len(components))
    form = str(decision["form"])
    alpha = float(decision["alpha"])

    def compare(train_rows: list[dict], target_rows: list[dict]) -> dict[str, object]:
        incumbent_model = _fit_peak(train_rows, components, form, alpha, basis)
        candidate_model = _fit_trend(train_rows, components, form, alpha, basis)
        return _comparison(
            _predict_trend(candidate_model, target_rows, components, form, basis),
            _predict_incumbent(
                incumbent_model, target_rows, components, form, basis
            ),
            target_rows,
            components,
        )

    train = examples.filter(pl.col("peak_window_end_year") <= 2014).to_dicts()
    development = examples.filter(
        pl.col("peak_window_end_year").is_between(2015, 2017, closed="both")
    ).to_dicts()
    development_result = compare(train, development)
    replay = []
    for end_year in REPLAY_END_YEARS:
        target = examples.filter(pl.col("peak_window_end_year") == end_year).to_dicts()
        prior = examples.filter(pl.col("peak_window_end_year") < end_year).to_dicts()
        replay.append({"peak_window_end_year": end_year, **compare(prior, target)})
    wins = {
        "log_loss": sum(row["log_loss_delta"] < 0 for row in replay),
        "brier": sum(row["brier_delta"] < 0 for row in replay),
        "event_log_loss": sum(row["event_log_loss_delta"] <= 0 for row in replay),
        "event_brier": sum(row["event_brier_delta"] <= 0 for row in replay),
        "uncertainty": sum(
            row["uncertainty"]["log_loss_delta_p975"] <= 0
            and row["uncertainty"]["brier_delta_p975"] <= 0
            for row in replay
        ),
    }
    development_passed = (
        development_result["log_loss_delta"] < 0
        and development_result["brier_delta"] < 0
    )
    calibration_guardrail = None
    if run_calibration is not None:
        calibration_rows = []
        for end_year in REPLAY_END_YEARS:
            target = examples.filter(
                pl.col("peak_window_end_year") == end_year
            ).to_dicts()
            prior = examples.filter(
                pl.col("peak_window_end_year") < end_year
            ).to_dicts()
            model = _fit_trend(prior, components, form, alpha, basis)
            residual = _run_residuals(
                _predict_trend(model, target, components, form, basis),
                target,
                components,
                player_type="hitter",
            )
            correction = np.asarray([
                float(run_calibration[str(row["origin_age_band"])]) for row in target
            ])
            calibrated = residual - correction
            calibration_rows.append({
                "peak_window_end_year": end_year,
                "uncalibrated_mae": float(np.mean(np.abs(residual))),
                "calibrated_mae": float(np.mean(np.abs(calibrated))),
                "uncalibrated_rmse": float(np.sqrt(np.mean(residual**2))),
                "calibrated_rmse": float(np.sqrt(np.mean(calibrated**2))),
            })
        calibration_guardrail = {
            "replay": calibration_rows,
            "mae_wins": sum(
                row["calibrated_mae"] < row["uncalibrated_mae"]
                for row in calibration_rows
            ),
            "rmse_wins": sum(
                row["calibrated_rmse"] < row["uncalibrated_rmse"]
                for row in calibration_rows
            ),
        }
    calibration_passed = calibration_guardrail is None or (
        calibration_guardrail["mae_wins"] >= 4
        and calibration_guardrail["rmse_wins"] >= 4
    )
    promoted = (
        development_passed
        and all(value >= 4 for value in wins.values())
        and calibration_passed
    )
    final_rows = examples.to_dicts()
    final_model = _fit_trend(final_rows, components, form, alpha, basis)
    current_fit = _serialize_fitted_model(
        final_model,
        form=form,
        alpha=alpha,
        basis=basis,
        training_rows=len(final_rows),
        training_origins=sorted(set(int(row["origin_year"]) for row in final_rows)),
    )
    current_fit["feature_family"] = "component_development_plus_one_year_trend"
    return {
        "development": development_result,
        "development_gate_passed": development_passed,
        "replay": replay,
        "wins": wins,
        "run_calibration_guardrail": calibration_guardrail,
        "promoted": promoted,
        "current_fit": current_fit,
    }


def _predict_incumbent(
    model: object,
    rows: list[dict[str, object]],
    components: tuple[str, ...],
    form: str,
    basis: np.ndarray,
) -> np.ndarray:
    delta = model.predict(_features(rows, components, form, basis))
    return np.asarray([
        inverse_ilr_transform(
            np.asarray(ilr_transform(_composition(row, components, "p_"), basis=basis))
            + delta[index],
            basis=basis,
        )
        for index, row in enumerate(rows)
    ])


def main() -> int:
    peak_report = json.loads((ROOT / "report.json").read_text(encoding="utf-8"))
    run_calibration = json.loads(
        Path("model_artifacts/peak-talent-run-calibration-v1.json").read_text(
            encoding="utf-8"
        )
    )
    specs = {
        "hitters": (
            _hitter_components(_load_sources("affiliated_hitting_components.parquet")),
            pl.read_parquet(ROOT / "tables" / "plate_appearances_examples.parquet"),
            HITTER_COMPONENTS,
            "plate_appearances",
            1200.0,
        ),
        "pitchers": (
            _pitcher_components(_load_sources("affiliated_pitching_components.parquet")),
            pl.read_parquet(ROOT / "tables" / "batters_faced_examples.parquet"),
            PITCHER_COMPONENTS,
            "batters_faced",
            800.0,
        ),
    }
    report = {
        "report_schema_version": "0.1",
        "status": "skill_direction_challenger",
        "invalid_peak_end_years": sorted(INVALID_PEAK_END_YEARS),
        "outside_rank_or_fv_used": False,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for player_type, (source, examples, components, exposure, regression) in specs.items():
        trended = _add_trend(
            examples,
            source,
            components,
            exposure=exposure,
            regression=regression,
        )
        trended.write_parquet(OUTPUT / f"{player_type}_examples.parquet")
        report[player_type] = _evaluate(
            trended,
            components,
            peak_report[player_type]["selected"],
            run_calibration=(
                run_calibration["hitters"] if player_type == "hitters" else None
            ),
        )
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        player_type: {
            "development_gate_passed": report[player_type]["development_gate_passed"],
            "wins": report[player_type]["wins"],
            "promoted": report[player_type]["promoted"],
        }
        for player_type in ("hitters", "pitchers")
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
