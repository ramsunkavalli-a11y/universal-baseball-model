#!/usr/bin/env python3
"""Materialize current prospect peak-rate talent without public-rank inputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from audit_one_year_talent_development import HITTER_COMPONENTS, PITCHER_COMPONENTS
from audit_one_year_talent_development import _hitter_components, _load_sources
from audit_peak_talent_trend import _add_trend
from audit_pitcher_process_challenger import _load_process, _process_features
from materialize_current_future_talent import (
    _hitter_runs,
    _model_predict,
    _pitcher_runs,
    _prepare,
)
from universal_baseball.storage import write_canonical_parquet
from universal_baseball.projection_composition import ilr_transform, inverse_ilr_transform


BASIC_ROOT = Path("reports/generated/current-basic-talent/2026-09-08/tables")
PEAK_REPORT = Path("reports/generated/age-to-peak-talent/report.json")
CALIBRATION_PATH = Path("model_artifacts/peak-talent-run-calibration-v1.json")
TREND_REPORT = Path("reports/generated/peak-talent-trend/report.json")
OUTPUT_ROOT = Path("reports/generated/current-peak-talent/2026-09-08")
PITCHER_ROLE_PATH = Path(
    "reports/generated/current-pitcher-opportunity-v2/2026-09-08/predictors.parquet"
)
PITCHER_PROCESS_ARTIFACT = Path("model_artifacts/peak-pitcher-process-v1.json")
FIELDING_PROFILE_PATH = Path(
    "reports/generated/current-defense-rates/2026-09-08/tables/"
    "current-fielding-profiles.parquet"
)
DEFENSE_RATE_PATH = Path(
    "reports/generated/current-defense-rates/2026-09-08/tables/"
    "hitter-defense-rates.parquet"
)


def _rank_prospects(
    frame: pl.DataFrame,
    score_column: str = "peak_runs_rate",
) -> pl.DataFrame:
    eligible = (
        frame.filter(
            (pl.col("ranking_status") == "ranked")
            & (pl.col("as_of_level_group") != "MLB")
            & pl.col("age_years").is_not_null()
            & (pl.col("age_years") <= 23)
        )
        .sort(
            [score_column, "effective_evidence", "player_id"],
            descending=[True, True, False],
        )
        .with_row_index("prospect_peak_rate_rank", offset=1)
    )
    if "as_of_role" in eligible.columns:
        eligible = eligible.with_columns(
            pl.col(score_column)
            .rank(method="ordinal", descending=True)
            .over("as_of_role")
            .cast(pl.UInt32)
            .alias("prospect_role_peak_rate_rank")
        )
    other = frame.join(
        eligible.select("player_id"),
        on="player_id",
        how="anti",
    ).with_columns(pl.lit(None, dtype=pl.UInt32).alias("prospect_peak_rate_rank"))
    if "as_of_role" in other.columns:
        other = other.with_columns(
            pl.lit(None, dtype=pl.UInt32).alias("prospect_role_peak_rate_rank")
        )
    return pl.concat([eligible, other], how="diagonal_relaxed")


def _age_band(age: np.ndarray) -> np.ndarray:
    return np.where(age < 20, "under_20", np.where(age < 22, "20_to_21", "22_to_23"))


def _run_calibration(
    age: np.ndarray,
    apply_model: np.ndarray,
    calibration: dict[str, float],
) -> np.ndarray:
    bands = _age_band(age)
    adjustment = np.asarray([float(calibration[str(band)]) for band in bands])
    return np.where(apply_model, adjustment, 0.0)


def _apply_process_residual(
    production_peak: np.ndarray,
    process_peak: np.ndarray,
    same_cohort_reference_peak: np.ndarray,
    basis: np.ndarray,
) -> np.ndarray:
    """Apply only the incremental process signal, not a cohort intercept shift."""

    return np.asarray([
        inverse_ilr_transform(
            np.asarray(ilr_transform(production_peak[index], basis=basis))
            + np.asarray(ilr_transform(process_peak[index], basis=basis))
            - np.asarray(
                ilr_transform(same_cohort_reference_peak[index], basis=basis)
            ),
            basis=basis,
        )
        for index in range(len(production_peak))
    ])


def _materialize(
    frame: pl.DataFrame,
    components: tuple[str, ...],
    fit: dict[str, object],
    *,
    player_type: str,
    calibration: dict[str, float],
    ranking_fit: dict[str, object] | None = None,
    fallback_fit: dict[str, object] | None = None,
    process_reference_fit: dict[str, object] | None = None,
) -> pl.DataFrame:
    present = frame.select([f"p_{name}" for name in components]).to_numpy()
    peak = _model_predict(frame, components, fit)
    process_applied = np.zeros(frame.height, dtype=bool)
    process_runs_change = np.zeros(frame.height, dtype=float)
    if fallback_fit is not None:
        process_applied = frame.get_column("pitch_process_available").to_numpy()
        fallback_peak = _model_predict(frame, components, fallback_fit)
        if process_reference_fit is None:
            process_peak = peak
        else:
            reference_peak = _model_predict(frame, components, process_reference_fit)
            basis = np.asarray(fit["ilr_basis"], dtype=float)
            process_peak = _apply_process_residual(
                fallback_peak, peak, reference_peak, basis
            )
        if player_type == "pitcher":
            process_runs_change = (
                _pitcher_runs(process_peak, present, np.zeros(frame.height))
                - _pitcher_runs(fallback_peak, present, np.zeros(frame.height))
            )
        peak = np.where(process_applied[:, None], process_peak, fallback_peak)
    age = frame.get_column("age_years").to_numpy()
    minor = frame.get_column("as_of_level_group").to_numpy() != "MLB"
    if player_type == "hitter":
        apply_model = minor & (age >= 16) & (age <= 23)
        present_runs = frame.get_column("present_offense_runs_per_600_pa").to_numpy()
        model_runs = _hitter_runs(peak, present, present_runs)
        status = "historical_gate_passed"
    else:
        apply_model = minor & (age >= 16) & (age <= 23)
        present_runs = frame.get_column("present_pitching_runs_per_800_bf").to_numpy()
        model_runs = _pitcher_runs(peak, present, present_runs)
        status = "historical_gate_passed"
    peak[~apply_model] = present[~apply_model]
    component_peak_runs = np.where(apply_model, model_runs, present_runs)
    run_calibration = _run_calibration(age, apply_model, calibration)
    peak_runs = component_peak_runs + run_calibration
    age_level_peak_runs = np.full(frame.height, np.nan)
    if player_type == "pitcher" and ranking_fit is not None:
        age_level_peak = _model_predict(frame, components, ranking_fit)
        age_level_model_runs = _pitcher_runs(age_level_peak, present, present_runs)
        age_level_peak_runs = np.where(
            apply_model,
            age_level_model_runs + run_calibration,
            present_runs,
        )
    model_name = str(fit.get("feature_family") or fit["form"])
    if fallback_fit is None:
        policy = np.where(
            apply_model,
            f"age_24_to_26_{model_name}",
            "carry_forward_outside_supported_age",
        )
    else:
        fallback_name = str(
            fallback_fit.get("feature_family") or fallback_fit["form"]
        )
        policy = np.where(
            apply_model,
            np.where(
                process_applied,
                f"age_24_to_26_{model_name}",
                f"age_24_to_26_{fallback_name}_missing_process_fallback",
            ),
            "carry_forward_outside_supported_age",
        )
    recent_direction = np.full(frame.height, np.nan)
    if player_type == "hitter" and "has_prior_profile" in frame.columns:
        prior = frame.select([f"prior_{name}" for name in components]).to_numpy()
        recent_direction = _hitter_runs(present, prior, np.zeros(frame.height))
    output = frame.select(
        "player_id",
        "player_name",
        "player_type",
        "as_of_level_group",
        "age_years",
        "age_relative_to_level",
        "effective_evidence",
        "reliability",
        "evidence_band",
        "ranking_status",
        *(column for column in ("as_of_role",) if column in frame.columns),
        *(
            column
            for column in (
                "current_primary_position",
                "current_defense_runs_per_600",
                "defense_evidence_tier",
            )
            if column in frame.columns
        ),
        *(
            column
            for column in ("external_rank_audit_only", "external_fv_audit_only")
            if column in frame.columns
        ),
        *(
            column
            for column in (
                "process_whiff",
                "process_strike",
                "process_swing",
                "process_ppbf",
            )
            if column in frame.columns
        ),
    ).with_columns(
        pl.Series("present_runs_rate", present_runs),
        pl.Series("component_peak_runs_rate", component_peak_runs),
        pl.Series("peak_run_calibration", run_calibration),
        pl.Series("peak_runs_rate", peak_runs),
        pl.Series("age_level_peak_runs_rate", age_level_peak_runs),
        pl.Series("peak_runs_change", peak_runs - present_runs),
        pl.Series("recent_component_direction_runs", recent_direction),
        pl.Series("pitch_process_applied", process_applied & apply_model),
        pl.Series(
            "pitch_process_runs_change",
            np.where(process_applied & apply_model, process_runs_change, 0.0),
        ),
        pl.Series("peak_policy", policy),
        pl.lit(status).alias("peak_validation_status"),
        *(pl.Series(f"present_{name}_rate", present[:, index]) for index, name in enumerate(components)),
        *(pl.Series(f"peak_{name}_rate", peak[:, index]) for index, name in enumerate(components)),
    )
    return _rank_prospects(output)


def main() -> int:
    report = json.loads(PEAK_REPORT.read_text(encoding="utf-8"))
    calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
    trend_report = json.loads(TREND_REPORT.read_text(encoding="utf-8"))
    hitter_fit = (
        trend_report["hitters"]["current_fit"]
        if trend_report["hitters"]["promoted"]
        else report["hitters"]["current_fit"]
    )
    hitter_source = _hitter_components(
        _load_sources("affiliated_hitting_components.parquet")
    )
    hitter_frame = _prepare(
        BASIC_ROOT / "current_hitter_talent.parquet",
        HITTER_COMPONENTS,
        player_type="hitter",
    ).with_columns(pl.lit(2026).alias("origin_year"))
    if trend_report["hitters"]["promoted"]:
        hitter_frame = _add_trend(
            hitter_frame,
            hitter_source,
            HITTER_COMPONENTS,
            exposure="plate_appearances",
            regression=1200.0,
        )
    if FIELDING_PROFILE_PATH.exists():
        primary_position = (
            pl.read_parquet(FIELDING_PROFILE_PATH)
            .sort(
                ["player_id", "fielding_outs", "position_order"],
                descending=[False, True, False],
            )
            .unique("player_id", keep="first")
            .select(
                "player_id",
                pl.col("position").alias("current_primary_position"),
            )
        )
        hitter_frame = hitter_frame.join(
            primary_position, on="player_id", how="left", validate="1:1"
        )
    if DEFENSE_RATE_PATH.exists():
        defense = (
            pl.read_parquet(DEFENSE_RATE_PATH)
            .filter(pl.col("season") == 2027)
            .select(
                "player_id",
                pl.col("defense_runs_per_600").alias(
                    "current_defense_runs_per_600"
                ),
                "defense_evidence_tier",
            )
        )
        hitter_frame = hitter_frame.join(
            defense, on="player_id", how="left", validate="1:1"
        )
    hitters = _materialize(
        hitter_frame,
        HITTER_COMPONENTS,
        hitter_fit,
        player_type="hitter",
        calibration=calibration["hitters"],
    )
    pitcher_source = _prepare(
            BASIC_ROOT / "current_pitcher_talent.parquet",
            PITCHER_COMPONENTS,
            player_type="pitcher",
        )
    pitcher_fit = report["pitchers"]["current_fit"]
    pitcher_fallback_fit = None
    pitcher_process_reference_fit = None
    if PITCHER_PROCESS_ARTIFACT.exists():
        process_artifact = json.loads(
            PITCHER_PROCESS_ARTIFACT.read_text(encoding="utf-8")
        )
        if process_artifact.get("status") == "promoted_optional_high_minors_peak_input":
            current_process = (
                _process_features(_load_process())
                .filter(pl.col("season") == 2026)
                .drop("season", "bf")
                .with_columns(pl.lit(True).alias("pitch_process_available"))
            )
            pitcher_source = pitcher_source.join(
                current_process,
                on=["player_id", "level_group"],
                how="left",
                validate="m:1",
            ).with_columns(
                pl.col("pitch_process_available").fill_null(False),
                pl.col(
                    "process_whiff", "process_strike", "process_swing", "process_ppbf"
                ).fill_null(0.0),
            )
            pitcher_fit = process_artifact["fit"]
            pitcher_fallback_fit = report["pitchers"]["current_fit"]
            pitcher_process_reference_fit = process_artifact[
                "same_cohort_reference_fit"
            ]
    if PITCHER_ROLE_PATH.exists():
        pitcher_source = pitcher_source.join(
            pl.read_parquet(PITCHER_ROLE_PATH).select("player_id", "as_of_role"),
            on="player_id",
            how="left",
            validate="1:1",
        )
    pitchers = _materialize(
        pitcher_source,
        PITCHER_COMPONENTS,
        pitcher_fit,
        player_type="pitcher",
        calibration=calibration["pitchers"],
        ranking_fit=report["pitchers"]["age_level_current_fit"],
        fallback_fit=pitcher_fallback_fit,
        process_reference_fit=pitcher_process_reference_fit,
    )
    tables = OUTPUT_ROOT / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {}
    for name, frame in (("hitters", hitters), ("pitchers", pitchers)):
        path = tables / f"current_peak_{name}.parquet"
        storage[name] = write_canonical_parquet(
            frame,
            path,
            table_name=f"current_peak_{name}_talent",
        ).as_record()
        frame.write_csv(path.with_suffix(".csv"))
        frame.filter(pl.col("prospect_peak_rate_rank") <= 100).sort(
            "prospect_peak_rate_rank"
        ).write_csv(tables / f"current_peak_{name}_top100.csv")
    output_report = {
        "report_schema_version": "0.1",
        "status": "inspectable_prospect_peak_rate",
        "ranking_universe": (
            "ranked non-MLB players age 23 or younger, separately for hitters and pitchers"
        ),
        "hitters": {
            "validation": report["hitters"]["promotion"],
            "under_20": "modeled; explicit strikeout component passes supported subgroup breadth",
            "skill_direction": {
                "promoted": trend_report["hitters"]["promoted"],
                "wins": trend_report["hitters"]["wins"],
            },
        },
        "pitchers": {
            "validation": report["pitchers"]["promotion"],
            "ordering_policy": (
                "component-development peak mean remains the provisional inspection "
                "order; no ranking blend passed the separate top-tail gate"
            ),
            "pitch_process": (
                "validated high-minors optional input with results-only fallback"
                if pitcher_fallback_fit is not None
                else "not applied"
            ),
        },
        "public_rank_role": "joined after scoring for audit only",
        "hitter_position_and_defense_role": (
            "visible current context only; excluded from peak offense rank because "
            "prospect positional-run validation failed"
        ),
        "run_rate_calibration": {
            "artifact": str(CALIBRATION_PATH),
            "method": calibration["method"],
            "promotion_gate": calibration["promotion_gate"],
        },
        "excluded": ["playing time", "arrival", "position", "defense", "contracts"],
        "storage": storage,
    }
    (OUTPUT_ROOT / "report.json").write_text(
        json.dumps(output_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": output_report["status"],
        "hitter_top": hitters.filter(
            pl.col("prospect_peak_rate_rank").is_not_null()
        ).sort("prospect_peak_rate_rank").select(
            "prospect_peak_rate_rank", "player_name", "peak_runs_rate"
        ).head(10).to_dicts(),
        "pitcher_top": pitchers.filter(
            pl.col("prospect_peak_rate_rank").is_not_null()
        ).sort("prospect_peak_rate_rank").select(
            "prospect_peak_rate_rank", "player_name", "peak_runs_rate"
        ).head(10).to_dicts(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
