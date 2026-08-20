#!/usr/bin/env python3
"""Select pre-2025 catcher native-opportunity forecasts for Player Value v1."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import requests

CONTRACT_SHA256 = "f7d8dfc15ca3df26a1b19c94b2d37b310dd4a0b1c7391c540ddb846aef952d30"
SELECTION_RUN_ID = 32141616127
SELECTION_ARTIFACT = "playing-time-v1-candidate-selection"
SELECTION_DIGEST = "sha256:a8719576ef7ed7377a6376556d34e1fd377d5e27ca88535543a43c615f4cb5d8"
VALIDATION_2023_RUN_ID = 32141934868
VALIDATION_2023_ARTIFACT = "playing-time-v1-validation-2023"
VALIDATION_2023_DIGEST = "sha256:738c631f5b4fbaa7875219ee452996e487799c4a323b0cafa57a7500583c5b39"
VALIDATION_2024_RUN_ID = 32142089669
VALIDATION_2024_ARTIFACT = "playing-time-v1-validation-2024"
VALIDATION_2024_DIGEST = "sha256:979386377b5c2fa7f8f411bcd3284c6f4e68d532a5585e002b493f3cfffe0366"
RUN_CONVERSION_PARAMETERS = "docs/player-value-v1-defense-native-run-conversion-parameters.json"
FORMS = ("B0_raw_persistence", "P1_playing_time_ratio", "H1_fixed_50_50_hybrid")
FOLDS = (
    {
        "name": "projection_2022_to_2023",
        "source_year": 2022,
        "target_year": 2023,
        "validation_file": "candidate_scored.parquet",
    },
    {
        "name": "projection_2023_to_2024",
        "source_year": 2023,
        "target_year": 2024,
        "validation_file": "candidate_2024_scored.parquet",
    },
)
COMPONENTS = {
    "catcher_throwing": {"field": "sb_attempts", "source_min": 10.0},
    "catcher_blocking": {"field": "pitches", "source_min": 500.0},
    "catcher_framing": {"field": "pitches", "source_min": 1000.0},
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-root", type=Path, required=True)
    parser.add_argument("--validation-2023-root", type=Path, required=True)
    parser.add_argument("--validation-2024-root", type=Path, required=True)
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-catcher-native-opportunity-selection-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-catcher-native-opportunity-selection"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_contract(path: Path) -> str:
    observed = _sha256(path)
    if observed != CONTRACT_SHA256:
        raise RuntimeError(
            f"catcher-opportunity contract mismatch: expected {CONTRACT_SHA256}, observed {observed}"
        )
    return observed


def _find_one(root: Path, filename: str, *, path_part: str | None = None) -> Path:
    matches = sorted(
        path
        for path in root.rglob(filename)
        if path.is_file() and (path_part is None or path_part in path.parts)
    )
    if len(matches) != 1:
        raise RuntimeError(f"expected one {filename} under {root}; found {matches}")
    return matches[0]


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "--"}:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _fetch_csv(session: requests.Session, endpoint: str, params: dict[str, object]) -> pl.DataFrame:
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{endpoint}",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"{endpoint} returned empty/HTML")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError(f"{endpoint} returned empty CSV")
    return frame


def _throwing_params(year: int) -> dict[str, object]:
    return {
        "game_type": "Regular",
        "n": 1,
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
        "target_base": "All",
    }


def _blocking_params(year: int) -> dict[str, object]:
    return {
        "game_type": "Regular",
        "n": 1,
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
    }


def _framing_params(year: int) -> dict[str, object]:
    return {
        "type": "catcher",
        "seasonStart": year,
        "seasonEnd": year,
        "team": "",
        "min": 1,
        "sortColumn": "rv_tot",
        "sortDirection": "desc",
        "csv": "true",
    }


def _component_source(session: requests.Session, component: str, year: int) -> pl.DataFrame:
    if component == "catcher_throwing":
        raw = _fetch_csv(session, "catcher-throwing", _throwing_params(year))
        id_col, value_col = "player_id", "sb_attempts"
    elif component == "catcher_blocking":
        raw = _fetch_csv(session, "catcher-blocking", _blocking_params(year))
        id_col, value_col = "player_id", "pitches"
    elif component == "catcher_framing":
        raw = _fetch_csv(session, "catcher-framing", _framing_params(year))
        id_col = "id" if "id" in raw.columns else "player_id" if "player_id" in raw.columns else ""
        value_col = "pitches"
    else:
        raise RuntimeError(f"unknown component {component}")
    if not id_col or id_col not in raw.columns or value_col not in raw.columns:
        raise RuntimeError(f"{component} {year} missing id/opportunity columns")

    rows: list[dict[str, object]] = []
    for row in raw.select(id_col, value_col).iter_rows(named=True):
        player = _number(row[id_col])
        value = _number(row[value_col])
        if player is None or not player.is_integer() or value is None or value < 0:
            continue
        rows.append({"player_id": int(player), "opportunity": float(value)})
    frame = pl.DataFrame(rows) if rows else pl.DataFrame({"player_id": [], "opportunity": []})
    if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{component} {year} violates player grain")
    return frame


def _load_playing_time_fold(
    selection_root: Path,
    validation_root: Path,
    fold: dict[str, object],
) -> pl.DataFrame:
    fold_name = str(fold["name"])
    predictors = pl.read_parquet(
        _find_one(selection_root, "predictors.parquet", path_part=fold_name)
    ).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("current_season_mlb_pa").cast(pl.Float64),
    )
    scored = pl.read_parquet(
        _find_one(validation_root, str(fold["validation_file"]))
    ).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("predicted_expected_mlb_pa").cast(pl.Float64),
    )
    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} predictors violate player grain")
    if scored.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} validation violates player grain")
    frame = predictors.join(scored, on="player_id", how="inner")
    if frame.height != predictors.height or frame.height != scored.height:
        raise RuntimeError(f"{fold_name} Playing Time coverage differs")
    if frame.filter(pl.col("predicted_expected_mlb_pa") < 0).height:
        raise RuntimeError(f"{fold_name} has negative projected PA")
    return frame


def _metric(frame: pl.DataFrame, prediction: str, mask: pl.Expr | None = None) -> dict[str, object]:
    subset = frame if mask is None else frame.filter(mask)
    if subset.is_empty():
        return {"n": 0, "mae": None, "rmse": None}
    observed = subset.get_column("observed_opportunity").to_numpy().astype(np.float64)
    predicted = subset.get_column(prediction).to_numpy().astype(np.float64)
    error = predicted - observed
    result = {
        "n": int(subset.height),
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
    }
    if mask is None:
        result["observed_mean"] = float(np.mean(observed))
        result["predicted_mean"] = float(np.mean(predicted))
    return result


def _build_component_fold(
    *,
    component: str,
    source_year: int,
    target_year: int,
    playing_time: pl.DataFrame,
    source: pl.DataFrame,
    target: pl.DataFrame,
) -> tuple[pl.DataFrame, dict[str, object]]:
    minimum = float(COMPONENTS[component]["source_min"])
    prior = source.filter(pl.col("opportunity") >= minimum).rename(
        {"opportunity": "prior_opportunity"}
    )
    observed = target.rename({"opportunity": "observed_opportunity"})
    frame = (
        prior.join(playing_time, on="player_id", how="inner")
        .join(observed, on="player_id", how="left")
        .with_columns(pl.col("observed_opportunity").fill_null(0.0))
        .with_columns(
            pl.lit(component).alias("component"),
            pl.lit(source_year).alias("source_year"),
            pl.lit(target_year).alias("target_year"),
            pl.col("prior_opportunity").alias("B0_raw_persistence"),
            (pl.col("current_season_mlb_pa") <= 0).alias("P1_zero_pa_fallback"),
        )
        .with_columns(
            pl.when(pl.col("current_season_mlb_pa") > 0)
            .then(
                pl.col("prior_opportunity")
                * pl.col("predicted_expected_mlb_pa")
                / pl.col("current_season_mlb_pa")
            )
            .otherwise(pl.col("prior_opportunity"))
            .alias("P1_playing_time_ratio")
        )
        .with_columns(
            (0.5 * pl.col("B0_raw_persistence") + 0.5 * pl.col("P1_playing_time_ratio")).alias(
                "H1_fixed_50_50_hybrid"
            )
        )
        .sort("player_id")
    )
    if frame.is_empty():
        raise RuntimeError(f"empty {component} fold {source_year}->{target_year}")
    metrics = {
        form: {
            **_metric(frame, form),
            "continuing": _metric(frame, form, pl.col("observed_opportunity") > 0),
            "exit": _metric(frame, form, pl.col("observed_opportunity") == 0),
        }
        for form in FORMS
    }
    diagnostics = {
        "source_eligible_rows": int(prior.height),
        "playing_time_joined_rows": int(frame.height),
        "P1_zero_pa_fallback_count": int(frame.get_column("P1_zero_pa_fallback").sum()),
        "target_positive_count": int(frame.filter(pl.col("observed_opportunity") > 0).height),
        "target_zero_count": int(frame.filter(pl.col("observed_opportunity") == 0).height),
    }
    return frame, {"metrics": metrics, "diagnostics": diagnostics}


def _equal_fold(component_result: dict[str, object]) -> dict[str, dict[str, float]]:
    folds = component_result["folds"]
    return {
        form: {
            "mae": float(np.mean([folds[name]["metrics"][form]["mae"] for name in folds])),
            "rmse": float(np.mean([folds[name]["metrics"][form]["rmse"] for name in folds])),
        }
        for form in FORMS
    }


def _select(component_result: dict[str, object]) -> dict[str, object]:
    baseline = "B0_raw_persistence"
    challengers = ("P1_playing_time_ratio", "H1_fixed_50_50_hybrid")
    folds = component_result["folds"]
    equal = component_result["equal_fold_means"]
    evaluations: dict[str, object] = {}
    passing: list[str] = []
    for challenger in challengers:
        fold_mae_guard = True
        continuing_guard = True
        per_fold: dict[str, object] = {}
        for fold_name, fold in folds.items():
            b0 = fold["metrics"][baseline]
            c = fold["metrics"][challenger]
            mae_ok = float(c["mae"]) <= 1.02 * float(b0["mae"])
            b0_cont = b0["continuing"]
            c_cont = c["continuing"]
            cont_ok = (
                True
                if int(b0_cont["n"]) == 0
                else float(c_cont["mae"]) <= 1.02 * float(b0_cont["mae"])
            )
            fold_mae_guard = fold_mae_guard and mae_ok
            continuing_guard = continuing_guard and cont_ok
            per_fold[fold_name] = {
                "overall_mae_within_2pct": mae_ok,
                "continuing_mae_within_2pct": cont_ok,
            }
        mean_mae_lower = float(equal[challenger]["mae"]) < float(equal[baseline]["mae"])
        mean_rmse_lower = float(equal[challenger]["rmse"]) < float(equal[baseline]["rmse"])
        passes = bool(fold_mae_guard and mean_mae_lower and mean_rmse_lower and continuing_guard)
        evaluations[challenger] = {
            "per_fold": per_fold,
            "fold_mae_guard": fold_mae_guard,
            "equal_fold_mae_strictly_lower": mean_mae_lower,
            "equal_fold_rmse_strictly_lower": mean_rmse_lower,
            "continuing_mae_guard": continuing_guard,
            "passes": passes,
        }
        if passes:
            passing.append(challenger)

    if not passing:
        selected, reason = baseline, "no challenger passed all predeclared gates"
    elif len(passing) == 1:
        selected, reason = passing[0], "only challenger passing all predeclared gates"
    else:
        p1, h1 = challengers
        delta = abs(float(equal[p1]["mae"]) - float(equal[h1]["mae"]))
        if delta <= 1e-9:
            selected, reason = p1, "both passed and MAE tied; simpler P1 wins"
        else:
            selected = min(passing, key=lambda form: float(equal[form]["mae"]))
            reason = "both passed; lower equal-fold MAE wins"
    return {
        "selected_form": selected,
        "reason": reason,
        "challenger_evaluations": evaluations,
    }


def _formula(component: str, selected: str) -> str:
    native = str(COMPONENTS[component]["field"])
    if selected == "B0_raw_persistence":
        return f"projected_{native} = prior_{native}"
    if selected == "P1_playing_time_ratio":
        return f"projected_{native} = prior_{native} * projected_expected_mlb_pa / source_year_mlb_pa; zero-PA fallback to prior_{native}"
    return f"projected_{native} = 0.5 * prior_{native} + 0.5 * (prior_{native} * projected_expected_mlb_pa / source_year_mlb_pa); zero-PA fallback collapses to prior_{native}"


def main() -> int:
    args = _parse_args()
    contract_hash = _verify_contract(args.contract_path)
    run_conversion = json.loads(Path(RUN_CONVERSION_PARAMETERS).read_text())
    if run_conversion.get("status") != "player_value_v1_defense_native_run_conversion_frozen":
        raise RuntimeError("Defense run conversion is not frozen")
    if run_conversion.get("catcher_opportunity_forecasting_frozen") is not False:
        raise RuntimeError("unexpected catcher opportunity state")

    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-catcher-opportunity/0.1"})
    source_data = {
        component: {year: _component_source(session, component, year) for year in (2022, 2023, 2024)}
        for component in COMPONENTS
    }

    component_results: dict[str, object] = {}
    scored_frames: list[pl.DataFrame] = []
    for component in COMPONENTS:
        folds_out: dict[str, object] = {}
        for fold in FOLDS:
            source_year = int(fold["source_year"])
            target_year = int(fold["target_year"])
            validation_root = (
                args.validation_2023_root if target_year == 2023 else args.validation_2024_root
            )
            playing_time = _load_playing_time_fold(args.selection_root, validation_root, fold)
            scored, result = _build_component_fold(
                component=component,
                source_year=source_year,
                target_year=target_year,
                playing_time=playing_time,
                source=source_data[component][source_year],
                target=source_data[component][target_year],
            )
            fold_name = f"{source_year}_to_{target_year}"
            folds_out[fold_name] = result
            scored_frames.append(scored.with_columns(pl.lit(fold_name).alias("fold")))
        component_result: dict[str, object] = {"folds": folds_out}
        component_result["equal_fold_means"] = _equal_fold(component_result)
        component_result["selection"] = _select(component_result)
        component_result["selected_formula"] = _formula(
            component, component_result["selection"]["selected_form"]
        )
        component_results[component] = component_result

    report = {
        "schema_version": "0.1",
        "status": "player_value_v1_catcher_native_opportunity_forecasts_frozen",
        "contract": "docs/player-value-v1-catcher-native-opportunity-selection-contract.md",
        "contract_sha256": contract_hash,
        "playing_time_provenance": {
            "selection": {
                "run_id": SELECTION_RUN_ID,
                "artifact_name": SELECTION_ARTIFACT,
                "artifact_digest": SELECTION_DIGEST,
            },
            "validation_2023": {
                "run_id": VALIDATION_2023_RUN_ID,
                "artifact_name": VALIDATION_2023_ARTIFACT,
                "artifact_digest": VALIDATION_2023_DIGEST,
            },
            "validation_2024": {
                "run_id": VALIDATION_2024_RUN_ID,
                "artifact_name": VALIDATION_2024_ARTIFACT,
                "artifact_digest": VALIDATION_2024_DIGEST,
            },
        },
        "run_conversion_provenance": {
            "parameters": RUN_CONVERSION_PARAMETERS,
            "source_run_id": run_conversion.get("source_run_id"),
            "source_sha": run_conversion.get("source_sha"),
        },
        "components": component_results,
        "boundary": {
            "2025_data_accessed": False,
            "defense_refit": False,
            "defense_rescored": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "run_conversion_changed": False,
            "general_defensive_exposure_changed": False,
            "positional_adjustment_calculated": False,
            "replacement_level_selected": False,
            "runs_per_win_selected": False,
            "war_value_calculated": False,
        },
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    pl.concat(scored_frames, how="vertical_relaxed").write_parquet(
        args.output_root / "scored_opportunities.parquet"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
