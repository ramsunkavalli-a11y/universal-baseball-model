#!/usr/bin/env python3
"""Development diagnostic for Player Value v1 total MLB defensive exposure.

Compares three predeclared total-outs bridges on 2022->2023 and 2023->2024:
B0 prior-year defensive-outs persistence, P1 frozen Playing Time expected MLB PA
times a contemporaneous source-year outs/PA scale, and H1 a fixed 50/50 hybrid.

This script does not access 2025, refit any upstream model, allocate positions,
convert defense to runs, or calculate WAR/value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path

import numpy as np
import polars as pl

CONTRACT_SHA256 = "43c543e6ab0d128bbb68baa5ac5ccefb3eae6d751dd5ec47394df6a261e3ead9"
ELIGIBLE_POSITIONS = ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF")
FOLDS = (
    {
        "name": "projection_2022_to_2023",
        "source_year": 2022,
        "target_year": 2023,
        "scored_filename": "candidate_scored.parquet",
    },
    {
        "name": "projection_2023_to_2024",
        "source_year": 2023,
        "target_year": 2024,
        "scored_filename": "candidate_2024_scored.parquet",
    },
)
FORMS = ("B0_raw_persistence", "P1_projected_pa_global_scale", "H1_fixed_50_50_hybrid")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-root", type=Path, required=True)
    parser.add_argument("--validation-2023-root", type=Path, required=True)
    parser.add_argument("--validation-2024-root", type=Path, required=True)
    parser.add_argument("--fielding-root", type=Path, required=True)
    parser.add_argument("--selection-run-id", type=int, required=True)
    parser.add_argument("--validation-2023-run-id", type=int, required=True)
    parser.add_argument("--validation-2024-run-id", type=int, required=True)
    parser.add_argument("--fielding-run-id", type=int, required=True)
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-defensive-exposure-diagnostic-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-defensive-exposure-diagnostic"),
    )
    return parser.parse_args()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _unique_file(root: Path, filename: str, *, contains_part: str | None = None) -> Path:
    matches = sorted(
        path
        for path in root.rglob(filename)
        if path.is_file() and (contains_part is None or contains_part in path.parts)
    )
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one {filename!r} under {root}"
            + (f" containing path part {contains_part!r}" if contains_part else "")
            + f"; found {len(matches)}: {matches}"
        )
    return matches[0]


def _verify_contract(path: Path) -> str:
    observed = _sha256(path)
    if observed != CONTRACT_SHA256:
        raise RuntimeError(
            f"diagnostic contract hash mismatch: expected {CONTRACT_SHA256}, observed {observed}"
        )
    return observed


def _load_fold(
    *,
    selection_root: Path,
    validation_root: Path,
    fielding_usage: pl.DataFrame,
    fold: dict[str, object],
) -> tuple[pl.DataFrame, float]:
    fold_name = str(fold["name"])
    source_year = int(fold["source_year"])
    target_year = int(fold["target_year"])
    scored_filename = str(fold["scored_filename"])

    predictors = pl.read_parquet(
        _unique_file(selection_root, "predictors.parquet", contains_part=fold_name)
    ).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("current_season_mlb_pa").cast(pl.Int64),
    )
    scored = pl.read_parquet(_unique_file(validation_root, scored_filename)).select(
        pl.col("player_id").cast(pl.Int64),
        pl.col("predicted_expected_mlb_pa").cast(pl.Float64),
    )
    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} predictors violate player grain")
    if scored.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_name} Playing Time scores violate player grain")
    predictor_ids = set(int(v) for v in predictors.get_column("player_id").to_list())
    scored_ids = set(int(v) for v in scored.get_column("player_id").to_list())
    if predictor_ids != scored_ids:
        raise RuntimeError(f"{fold_name} predictor/Playing Time score coverage differs")

    def season_outs(year: int, alias: str) -> pl.DataFrame:
        return (
            fielding_usage.filter(
                (pl.col("season") == year)
                & (pl.col("level_group") == "MLB")
                & pl.col("position_abbreviation").is_in(ELIGIBLE_POSITIONS)
            )
            .group_by("player_id")
            .agg(pl.col("fielding_outs").sum().cast(pl.Int64).alias(alias))
        )

    prior = season_outs(source_year, "prior_mlb_defensive_outs")
    target = season_outs(target_year, "observed_mlb_defensive_outs")
    frame = (
        predictors.join(scored, on="player_id", how="inner")
        .join(prior, on="player_id", how="left")
        .join(target, on="player_id", how="left")
        .with_columns(
            pl.col("prior_mlb_defensive_outs").fill_null(0).cast(pl.Int64),
            pl.col("observed_mlb_defensive_outs").fill_null(0).cast(pl.Int64),
        )
        .sort("player_id")
    )
    total_source_pa = int(frame.get_column("current_season_mlb_pa").sum())
    total_source_outs = int(frame.get_column("prior_mlb_defensive_outs").sum())
    if total_source_pa <= 0:
        raise RuntimeError(f"{fold_name} has nonpositive aggregate source MLB PA")
    source_outs_per_pa = float(total_source_outs / total_source_pa)
    if not np.isfinite(source_outs_per_pa) or source_outs_per_pa <= 0.0:
        raise RuntimeError(f"{fold_name} source outs/PA scale is invalid: {source_outs_per_pa}")

    frame = frame.with_columns(
        pl.lit(fold_name).alias("fold"),
        pl.lit(source_year).cast(pl.Int64).alias("source_year"),
        pl.lit(target_year).cast(pl.Int64).alias("target_year"),
        pl.lit(source_outs_per_pa).alias("source_outs_per_pa"),
        pl.col("prior_mlb_defensive_outs").cast(pl.Float64).alias("B0_raw_persistence"),
        (pl.col("predicted_expected_mlb_pa") * pl.lit(source_outs_per_pa)).alias(
            "P1_projected_pa_global_scale"
        ),
    ).with_columns(
        (
            0.5 * pl.col("B0_raw_persistence")
            + 0.5 * pl.col("P1_projected_pa_global_scale")
        ).alias("H1_fixed_50_50_hybrid")
    )
    return frame, source_outs_per_pa


def _metric_subset(frame: pl.DataFrame, prediction_col: str, mask: pl.Expr) -> dict[str, object]:
    subset = frame.filter(mask)
    n = int(subset.height)
    if n == 0:
        return {"n": 0, "mae": None, "rmse": None}
    observed = np.asarray(
        subset.get_column("observed_mlb_defensive_outs").to_numpy(), dtype=np.float64
    )
    predicted = np.asarray(subset.get_column(prediction_col).to_numpy(), dtype=np.float64)
    error = predicted - observed
    return {
        "n": n,
        "mae": float(np.abs(error).mean()),
        "rmse": float(sqrt(float(np.square(error).mean()))),
    }


def _metrics(frame: pl.DataFrame, prediction_col: str) -> dict[str, object]:
    observed = np.asarray(
        frame.get_column("observed_mlb_defensive_outs").to_numpy(), dtype=np.float64
    )
    predicted = np.asarray(frame.get_column(prediction_col).to_numpy(), dtype=np.float64)
    error = predicted - observed
    overall = {
        "n": int(frame.height),
        "mae": float(np.abs(error).mean()),
        "rmse": float(sqrt(float(np.square(error).mean()))),
        "observed_mean_outs": float(observed.mean()),
        "predicted_mean_outs": float(predicted.mean()),
    }
    subsets = {
        "target_positive": _metric_subset(
            frame, prediction_col, pl.col("observed_mlb_defensive_outs") > 0
        ),
        "incumbent": _metric_subset(
            frame, prediction_col, pl.col("prior_mlb_defensive_outs") > 0
        ),
        "entrant": _metric_subset(
            frame,
            prediction_col,
            (pl.col("prior_mlb_defensive_outs") == 0)
            & (pl.col("observed_mlb_defensive_outs") > 0),
        ),
        "exit": _metric_subset(
            frame,
            prediction_col,
            (pl.col("prior_mlb_defensive_outs") > 0)
            & (pl.col("observed_mlb_defensive_outs") == 0),
        ),
    }
    return {**overall, "subgroups": subsets}


def _equal_fold_means(fold_metrics: dict[str, dict[str, dict[str, object]]]) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for form in FORMS:
        maes = [float(fold_metrics[fold][form]["mae"]) for fold in fold_metrics]
        rmses = [float(fold_metrics[fold][form]["rmse"]) for fold in fold_metrics]
        output[form] = {
            "mae": float(sum(maes) / len(maes)),
            "rmse": float(sum(rmses) / len(rmses)),
        }
    return output


def _recommendation(
    fold_metrics: dict[str, dict[str, dict[str, object]]],
    equal_fold: dict[str, dict[str, float]],
) -> dict[str, object]:
    baseline = "B0_raw_persistence"
    challengers = ("P1_projected_pa_global_scale", "H1_fixed_50_50_hybrid")
    evaluations: dict[str, dict[str, object]] = {}
    passing: list[str] = []

    for challenger in challengers:
        fold_mae_within_2pct = True
        entrant_mae_lower_each_fold = True
        per_fold: dict[str, dict[str, object]] = {}
        for fold_name, metrics in fold_metrics.items():
            b0 = metrics[baseline]
            c = metrics[challenger]
            mae_ok = float(c["mae"]) <= 1.02 * float(b0["mae"])
            fold_mae_within_2pct = fold_mae_within_2pct and mae_ok

            b0_entrant = b0["subgroups"]["entrant"]
            c_entrant = c["subgroups"]["entrant"]
            if int(b0_entrant["n"]) > 0:
                entrant_ok = float(c_entrant["mae"]) < float(b0_entrant["mae"])
                entrant_mae_lower_each_fold = entrant_mae_lower_each_fold and entrant_ok
            else:
                entrant_ok = True
            per_fold[fold_name] = {
                "overall_mae_within_2pct_of_B0": mae_ok,
                "entrant_mae_strictly_lower_than_B0": entrant_ok,
            }

        equal_mae_lower = equal_fold[challenger]["mae"] < equal_fold[baseline]["mae"]
        equal_rmse_lower = equal_fold[challenger]["rmse"] < equal_fold[baseline]["rmse"]
        passed = bool(
            fold_mae_within_2pct
            and equal_mae_lower
            and equal_rmse_lower
            and entrant_mae_lower_each_fold
        )
        evaluations[challenger] = {
            "per_fold": per_fold,
            "fold_specific_overall_mae_within_2pct": fold_mae_within_2pct,
            "equal_fold_mean_mae_strictly_lower": equal_mae_lower,
            "equal_fold_mean_rmse_strictly_lower": equal_rmse_lower,
            "entrant_mae_strictly_lower_each_fold": entrant_mae_lower_each_fold,
            "passes": passed,
        }
        if passed:
            passing.append(challenger)

    if not passing:
        selected = baseline
        reason = "no challenger satisfied all predeclared recommendation gates"
    elif len(passing) == 1:
        selected = passing[0]
        reason = "only challenger satisfying all predeclared recommendation gates"
    else:
        p1, h1 = challengers
        delta = abs(equal_fold[p1]["mae"] - equal_fold[h1]["mae"])
        if delta <= 1e-9:
            selected = p1
            reason = "both challengers passed and MAE tied within 1e-9; simpler P1 wins"
        else:
            selected = min(passing, key=lambda form: equal_fold[form]["mae"])
            reason = "both challengers passed; lower equal-fold mean MAE wins"

    return {
        "recommended_total_outs_form": selected,
        "reason": reason,
        "challenger_evaluations": evaluations,
        "full_production_bridge_frozen": False,
        "position_allocation_still_open": True,
    }


def _write_markdown(report: dict[str, object], path: Path) -> None:
    lines = [
        "# Player Value v1 defensive exposure diagnostic",
        "",
        f"Status: **{report['status']}**",
        "",
        f"Recommended total-outs form: **{report['recommendation']['recommended_total_outs_form']}**",
        "",
        "This is development evidence only; the full exposure bridge is not frozen because",
        "position allocation and component-native opportunity denominators remain open.",
        "",
        "## Fold metrics",
        "",
    ]
    fold_metrics = report["fold_metrics"]
    for fold_name, forms in fold_metrics.items():
        lines.append(f"### {fold_name}")
        lines.append("")
        for form in FORMS:
            m = forms[form]
            lines.append(
                f"- `{form}`: MAE {m['mae']:.3f}; RMSE {m['rmse']:.3f}; "
                f"pred mean {m['predicted_mean_outs']:.3f}; observed mean {m['observed_mean_outs']:.3f}"
            )
        lines.append("")
    lines.extend(
        [
            "## Boundaries",
            "",
            "- 2025 accessed: false",
            "- upstream refit: false",
            "- position allocation selected: false",
            "- run conversion performed: false",
            "- positional adjustment calculated: false",
            "- WAR/value calculated: false",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    contract_sha = _verify_contract(args.contract_path)
    fielding_path = _unique_file(args.fielding_root, "historical_fielding_usage.parquet")
    fielding_usage = pl.read_parquet(fielding_path)
    required_fielding = {
        "season",
        "level_group",
        "player_id",
        "position_abbreviation",
        "fielding_outs",
    }
    missing = sorted(required_fielding - set(fielding_usage.columns))
    if missing:
        raise RuntimeError(f"historical fielding usage missing fields: {missing}")

    fold_metrics: dict[str, dict[str, dict[str, object]]] = {}
    fold_scales: dict[str, float] = {}
    scored_frames: list[pl.DataFrame] = []

    for fold in FOLDS:
        target_year = int(fold["target_year"])
        validation_root = (
            args.validation_2023_root if target_year == 2023 else args.validation_2024_root
        )
        frame, scale = _load_fold(
            selection_root=args.selection_root,
            validation_root=validation_root,
            fielding_usage=fielding_usage,
            fold=fold,
        )
        fold_name = str(fold["name"])
        fold_scales[fold_name] = scale
        fold_metrics[fold_name] = {form: _metrics(frame, form) for form in FORMS}
        scored_frames.append(frame)

    equal_fold = _equal_fold_means(fold_metrics)
    recommendation = _recommendation(fold_metrics, equal_fold)
    scored = pl.concat(scored_frames, how="vertical_relaxed").sort("target_year", "player_id")
    scored_path = table_root / "scored_total_defensive_outs.parquet"
    scored.write_parquet(scored_path)

    report: dict[str, object] = {
        "report_schema_version": "0.1",
        "gate": "player_value_v1_total_defensive_exposure_development_diagnostic",
        "status": "diagnostic_complete_not_production_frozen",
        "contract": {
            "path": str(args.contract_path),
            "sha256": contract_sha,
        },
        "sources": {
            "playing_time_selection": {
                "run_id": int(args.selection_run_id),
                "artifact": "playing-time-v1-candidate-selection",
            },
            "playing_time_validation_2023": {
                "run_id": int(args.validation_2023_run_id),
                "artifact": "playing-time-v1-validation-2023",
            },
            "playing_time_validation_2024": {
                "run_id": int(args.validation_2024_run_id),
                "artifact": "playing-time-v1-validation-2024",
            },
            "historical_fielding": {
                "run_id": int(args.fielding_run_id),
                "artifact": "position-role-historical-source-2021-2024",
                "file_sha256": _sha256(fielding_path),
            },
        },
        "target": {
            "unit": "MLB fielding_outs",
            "positions": list(ELIGIBLE_POSITIONS),
            "excluded_positions": ["DH", "P"],
            "folds": [
                {
                    "name": str(fold["name"]),
                    "source_year": int(fold["source_year"]),
                    "target_year": int(fold["target_year"]),
                }
                for fold in FOLDS
            ],
        },
        "source_outs_per_pa": fold_scales,
        "fold_metrics": fold_metrics,
        "equal_fold_means": equal_fold,
        "recommendation": recommendation,
        "storage": {
            "scored_total_defensive_outs": {
                "path": str(scored_path),
                "row_count": int(scored.height),
                "file_size_bytes": scored_path.stat().st_size,
                "file_sha256": _sha256(scored_path),
            }
        },
        "boundary": {
            "2025_accessed": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "defense_refit": False,
            "position_allocation_selected": False,
            "run_conversion_performed": False,
            "positional_adjustment_calculated": False,
            "war_value_calculated": False,
        },
    }
    report_path = args.output_root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(report, args.output_root / "report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
