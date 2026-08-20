#!/usr/bin/env python3
"""Audit pre-2025 Defense z-skill to public seasonal-run calibration.

This diagnostic does not refit Defense skill, select a production run scale, choose
future opportunity forecasts, or calculate positional adjustment / WAR.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import polars as pl
import requests
from sportsdataverse.mlb.mlb_statcast import mlb_statcast_leaderboard_outs_above_average

CONTRACT_SHA256 = "276481bc343245ce0b8ea82373286faa347a17d8d0bda13915865d743f72ad0b"
FIELDING_RUN_ID = 32148467330
FIELDING_ARTIFACT = "position-role-historical-source-2021-2024"
FIELDING_DIGEST = "sha256:908022d38b3652db1c2b68a7ba2768954c32f8973f0ace85c9557d30522adaf3"
YEARS = (2022, 2023, 2024)
GENERAL_POSITIONS = ("1B", "2B", "3B", "SS", "LF", "CF", "RF")
INFIELD = ("1B", "2B", "3B", "SS")
OUTFIELD = ("LF", "CF", "RF")
PUBLIC_METHOD = {
    "infield_oaa_runs_per_out": 0.75,
    "outfield_oaa_runs_per_out": 0.90,
    "catcher_throwing_runs_per_cs_aa": 0.65,
    "catcher_blocking_runs_per_block_aa": 0.25,
    "catcher_framing_run_field": "rv_tot",
}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fielding-root", type=Path, required=True)
    parser.add_argument(
        "--contract-path",
        type=Path,
        default=Path("docs/player-value-v1-defense-native-run-rate-calibration-contract.md"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/player-value-v1-defense-native-run-rate-calibration"),
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
            f"run-rate contract mismatch: expected {CONTRACT_SHA256}, observed {observed}"
        )
    return observed


def _find_one(root: Path, filename: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {filename!r} under {root}; found {len(matches)}")
    return matches[0]


def _number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "--"}:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _standardize(frame: pl.DataFrame, value: str, groups: list[str]) -> pl.DataFrame:
    moments = frame.group_by(groups).agg(
        pl.col(value).mean().alias("target_mean"),
        pl.col(value).std(ddof=0).alias("target_sd"),
        pl.len().alias("target_cell_n"),
    )
    result = frame.join(moments, on=groups, how="left").filter(
        pl.col("target_sd").is_not_null() & (pl.col("target_sd") > 1e-12)
    )
    return result.with_columns(
        ((pl.col(value) - pl.col("target_mean")) / pl.col("target_sd")).alias("target_z")
    )


def _through_origin_metrics(x: Iterable[float], y: Iterable[float]) -> dict[str, object]:
    x_arr = np.asarray(list(x), dtype=np.float64)
    y_arr = np.asarray(list(y), dtype=np.float64)
    mask = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_arr, y_arr = x_arr[mask], y_arr[mask]
    if not len(x_arr):
        raise RuntimeError("empty calibration sample")
    denominator = float(x_arr @ x_arr)
    if denominator <= 1e-12:
        raise RuntimeError("degenerate calibration denominator")
    slope = float((x_arr @ y_arr) / denominator)
    prediction = slope * x_arr
    residual = y_arr - prediction
    return {
        "n": int(len(x_arr)),
        "through_origin_slope": slope,
        "run_mae": float(np.mean(np.abs(residual))),
        "run_rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "run_target_mean": float(np.mean(y_arr)),
        "run_target_population_sd": float(np.std(y_arr, ddof=0)),
        "x_mean": float(np.mean(x_arr)),
        "x_median": float(np.median(x_arr)),
        "x_population_sd": float(np.std(x_arr, ddof=0)),
        "x_mean_abs": float(np.mean(np.abs(x_arr))),
    }


def _calibration(frame: pl.DataFrame, opportunity: str, run_target: str) -> dict[str, object]:
    scored = frame.with_columns((pl.col("target_z") * pl.col(opportunity)).alias("calibration_x"))
    metrics = _through_origin_metrics(
        scored.get_column("calibration_x").to_list(),
        scored.get_column(run_target).to_list(),
    )
    opportunity_values = scored.get_column(opportunity).to_numpy().astype(np.float64)
    metrics.update(
        {
            "opportunity_field": opportunity,
            "opportunity_mean": float(np.mean(opportunity_values)),
            "opportunity_median": float(np.median(opportunity_values)),
        }
    )
    return metrics


def _slope_stability(values: list[float]) -> dict[str, object]:
    array = np.asarray(values, dtype=np.float64)
    if not len(array) or not np.isfinite(array).all():
        raise RuntimeError("invalid slope inventory")
    mean = float(np.mean(array))
    sd = float(np.std(array, ddof=0))
    positive = bool(np.all(array > 0))
    return {
        "year_count": int(len(array)),
        "slopes": [float(value) for value in array],
        "median_slope": float(np.median(array)),
        "mean_slope": mean,
        "population_sd": sd,
        "coefficient_of_variation": float(sd / abs(mean)) if abs(mean) > 1e-12 else None,
        "all_positive": positive,
        "max_to_min_ratio": float(np.max(array) / np.min(array)) if positive else None,
    }


def _identity(lhs: Iterable[float], rhs: Iterable[float]) -> dict[str, object]:
    lhs_arr = np.asarray(list(lhs), dtype=np.float64)
    rhs_arr = np.asarray(list(rhs), dtype=np.float64)
    mask = np.isfinite(lhs_arr) & np.isfinite(rhs_arr)
    residual = lhs_arr[mask] - rhs_arr[mask]
    if not len(residual):
        return {"n": 0, "mae": None, "rmse": None, "max_abs_error": None, "mean_error": None}
    return {
        "n": int(len(residual)),
        "mae": float(np.mean(np.abs(residual))),
        "rmse": float(np.sqrt(np.mean(np.square(residual)))),
        "max_abs_error": float(np.max(np.abs(residual))),
        "mean_error": float(np.mean(residual)),
    }


def _load_fielding(root: Path) -> pl.DataFrame:
    frame = pl.read_parquet(_find_one(root, "historical_fielding_usage.parquet"))
    required = {"season", "level_group", "player_id", "position_abbreviation", "fielding_outs"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"historical fielding source missing {missing}")
    return (
        frame.filter(
            (pl.col("level_group") == "MLB")
            & pl.col("position_abbreviation").is_in(GENERAL_POSITIONS)
        )
        .group_by(["season", "player_id", "position_abbreviation"])
        .agg(pl.col("fielding_outs").sum().cast(pl.Float64).alias("fielding_outs"))
        .filter(pl.col("fielding_outs") > 0)
        .rename({"position_abbreviation": "position"})
    )


def _general_year(year: int, fielding: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, object]]:
    raw = mlb_statcast_leaderboard_outs_above_average(year=year)
    required = {"player_id", "primary_pos_formatted", "diff_success_rate_formatted", "fielding_runs_prevented"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise RuntimeError(f"general target {year} missing {missing}")
    rows: list[dict[str, object]] = []
    for row in raw.select(*sorted(required)).iter_rows(named=True):
        player = _number(row["player_id"])
        position = str(row["primary_pos_formatted"] or "").strip()
        target = _number(row["diff_success_rate_formatted"])
        runs = _number(row["fielding_runs_prevented"])
        if (
            player is None
            or not player.is_integer()
            or position not in GENERAL_POSITIONS
            or target is None
            or runs is None
        ):
            continue
        rows.append(
            {
                "target_year": year,
                "player_id": int(player),
                "position": position,
                "target_raw": target,
                "public_run_total": runs,
            }
        )
    target = pl.DataFrame(rows)
    if target.is_empty():
        raise RuntimeError(f"empty general target {year}")
    target = _standardize(target, "target_raw", ["target_year", "position"])
    joined = target.join(
        fielding.filter(pl.col("season") == year).drop("season"),
        on=["player_id", "position"],
        how="inner",
    )
    if joined.is_empty():
        raise RuntimeError(f"empty general target/fielding join {year}")

    position_metrics: dict[str, object] = {}
    for position in GENERAL_POSITIONS:
        subset = joined.filter(pl.col("position") == position)
        if subset.is_empty():
            raise RuntimeError(f"empty general calibration {year} {position}")
        position_metrics[position] = _calibration(subset, "fielding_outs", "public_run_total")

    group_metrics = {
        "IF": _calibration(joined.filter(pl.col("position").is_in(INFIELD)), "fielding_outs", "public_run_total"),
        "OF": _calibration(joined.filter(pl.col("position").is_in(OUTFIELD)), "fielding_outs", "public_run_total"),
    }
    return joined, {
        "year": year,
        "source_row_count": int(raw.height),
        "eligible_target_count": int(target.height),
        "joined_count": int(joined.height),
        "target_standardization": "within target year x position; population sd ddof=0",
        "public_run_target": "fielding_runs_prevented",
        "opportunity": "official target-year MLB fielding_outs at matching position",
        "by_position": position_metrics,
        "pooled_groups": group_metrics,
    }


def _catcher_params(kind: str, year: int) -> dict[str, object]:
    minimum = 10 if kind == "throwing" else 500
    params: dict[str, object] = {
        "game_type": "Regular",
        "n": minimum,
        "season_start": year,
        "season_end": year,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
    }
    if kind == "throwing":
        params["target_base"] = "All"
    return params


def _fetch_csv(session: requests.Session, endpoint: str, params: dict[str, object]) -> tuple[pl.DataFrame, str]:
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
    return frame, response.url


def _canonical_numeric(raw: pl.DataFrame, fields: tuple[str, ...]) -> list[dict[str, float | int]]:
    rows: list[dict[str, float | int]] = []
    for row in raw.select(*fields).iter_rows(named=True):
        parsed = {field: _number(row[field]) for field in fields}
        if any(value is None for value in parsed.values()):
            continue
        player = parsed.get("player_id")
        if player is not None and not float(player).is_integer():
            continue
        rows.append(
            {
                field: (int(value) if field == "player_id" else float(value))
                for field, value in parsed.items()
                if value is not None
            }
        )
    return rows


def _throwing_year(session: requests.Session, year: int) -> tuple[pl.DataFrame, dict[str, object]]:
    raw, url = _fetch_csv(session, "catcher-throwing", _catcher_params("throwing", year))
    fields = (
        "player_id",
        "sb_attempts",
        "cs_aa_per_throw",
        "caught_stealing_above_average",
        "catcher_stealing_runs",
    )
    missing = sorted(set(fields) - set(raw.columns))
    if missing:
        raise RuntimeError(f"throwing {year} missing {missing}")
    frame = pl.DataFrame(_canonical_numeric(raw, fields)).filter(pl.col("sb_attempts") >= 10).with_columns(
        pl.lit(year).alias("target_year"),
        pl.col("cs_aa_per_throw").alias("target_raw"),
        pl.col("catcher_stealing_runs").alias("public_run_total"),
    )
    frame = _standardize(frame, "target_raw", ["target_year"])
    identity_total = _identity(
        frame.get_column("caught_stealing_above_average"),
        frame.get_column("cs_aa_per_throw") * frame.get_column("sb_attempts"),
    )
    identity_runs = _identity(
        frame.get_column("catcher_stealing_runs"),
        0.65 * frame.get_column("caught_stealing_above_average"),
    )
    return frame, {
        "year": year,
        "response_url": url,
        "n": int(frame.height),
        "target_standardization": "within target year; population sd ddof=0",
        "calibration": _calibration(frame, "sb_attempts", "public_run_total"),
        "identities": {
            "caught_stealing_above_average_equals_rate_times_attempts": identity_total,
            "catcher_stealing_runs_equals_0_65_times_cs_aa": identity_runs,
        },
    }


def _blocking_year(session: requests.Session, year: int) -> tuple[pl.DataFrame, dict[str, object]]:
    raw, url = _fetch_csv(session, "catcher-blocking", _catcher_params("blocking", year))
    fields = (
        "player_id",
        "pitches",
        "n_pbwp",
        "blocks_above_average_per_game",
        "blocks_above_average",
        "catcher_blocking_runs",
    )
    missing = sorted(set(fields) - set(raw.columns))
    if missing:
        raise RuntimeError(f"blocking {year} missing {missing}")
    frame = pl.DataFrame(_canonical_numeric(raw, fields)).filter(pl.col("pitches") >= 500).with_columns(
        pl.lit(year).alias("target_year"),
        pl.col("blocks_above_average_per_game").alias("target_raw"),
        pl.col("catcher_blocking_runs").alias("public_run_total"),
    )
    frame = _standardize(frame, "target_raw", ["target_year"])
    identity_blocks = _identity(
        frame.get_column("blocks_above_average"),
        frame.get_column("blocks_above_average_per_game") * frame.get_column("n_pbwp") / 40.0,
    )
    identity_runs = _identity(
        frame.get_column("catcher_blocking_runs"),
        0.25 * frame.get_column("blocks_above_average"),
    )
    return frame, {
        "year": year,
        "response_url": url,
        "n": int(frame.height),
        "target_standardization": "within target year; population sd ddof=0",
        "calibrations": {
            "n_pbwp": _calibration(frame, "n_pbwp", "public_run_total"),
            "pitches": _calibration(frame, "pitches", "public_run_total"),
        },
        "identities": {
            "blocks_above_average_equals_rate_times_n_pbwp_over_40": identity_blocks,
            "catcher_blocking_runs_equals_0_25_times_blocks_aa": identity_runs,
        },
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


def _framing_year(session: requests.Session, year: int) -> tuple[pl.DataFrame, dict[str, object]]:
    raw, url = _fetch_csv(session, "catcher-framing", _framing_params(year))
    id_col = "id" if "id" in raw.columns else "player_id" if "player_id" in raw.columns else None
    if id_col is None:
        raise RuntimeError(f"framing {year} missing id")
    fields = (id_col, "pitches", "rv_tot")
    rows: list[dict[str, object]] = []
    for row in raw.select(*fields).iter_rows(named=True):
        player = _number(row[id_col])
        pitches = _number(row["pitches"])
        runs = _number(row["rv_tot"])
        if (
            player is None
            or not player.is_integer()
            or pitches is None
            or pitches < 1000
            or runs is None
        ):
            continue
        rows.append(
            {
                "player_id": int(player),
                "target_year": year,
                "pitches": pitches,
                "rv_tot": runs,
                "target_raw": 1000.0 * runs / pitches,
                "public_run_total": runs,
            }
        )
    frame = _standardize(pl.DataFrame(rows), "target_raw", ["target_year"])
    return frame, {
        "year": year,
        "response_url": url,
        "n": int(frame.height),
        "target_standardization": "within target year; population sd ddof=0",
        "calibration": _calibration(frame, "pitches", "public_run_total"),
        "identity": "target_raw = 1000 * rv_tot / pitches by construction",
    }


def _stability_from_years(by_year: dict[str, dict[str, object]], path: tuple[str, ...]) -> dict[str, object]:
    slopes: list[float] = []
    for year in YEARS:
        node: Any = by_year[str(year)]
        for key in path:
            node = node[key]
        slopes.append(float(node["through_origin_slope"]))
    return _slope_stability(slopes)


def _write_markdown(report: dict[str, object], path: Path) -> None:
    lines = [
        "# Player Value v1 Defense native run-rate calibration diagnostic",
        "",
        "Status: **DIAGNOSTIC COMPLETE — NO PRODUCTION RUN SCALE SELECTED**",
        "",
        "2025 accessed: **false**",
        "",
        "## General range slope stability",
        "",
    ]
    for position, metrics in report["general_range"]["stability_by_position"].items():
        lines.append(
            f"- {position}: median={metrics['median_slope']:.8f}; CV={metrics['coefficient_of_variation']}"
        )
    lines.extend(["", "## Catcher slope stability", ""])
    for component in ("catcher_throwing", "catcher_framing"):
        metrics = report[component]["stability"]
        lines.append(
            f"- {component}: median={metrics['median_slope']:.10f}; CV={metrics['coefficient_of_variation']}"
        )
    for basis, metrics in report["catcher_blocking"]["stability_by_opportunity"].items():
        lines.append(
            f"- catcher_blocking/{basis}: median={metrics['median_slope']:.10f}; CV={metrics['coefficient_of_variation']}"
        )
    lines.extend(
        [
            "",
            "This gate does not select pooled/median/grouped production scales, future catcher",
            "opportunity forecasts, positional adjustment, replacement level, runs per win, or WAR.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = _parse_args()
    if max(YEARS) >= 2025:
        raise RuntimeError("2025 boundary violation")
    contract_hash = _verify_contract(args.contract_path)
    fielding = _load_fielding(args.fielding_root)
    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-player-value-run-rate/0.1"})

    general_by_year: dict[str, dict[str, object]] = {}
    general_frames: list[pl.DataFrame] = []
    throwing_by_year: dict[str, dict[str, object]] = {}
    blocking_by_year: dict[str, dict[str, object]] = {}
    framing_by_year: dict[str, dict[str, object]] = {}

    for year in YEARS:
        general_frame, general_result = _general_year(year, fielding)
        general_frames.append(general_frame)
        general_by_year[str(year)] = general_result
        _, throwing_by_year[str(year)] = _throwing_year(session, year)
        _, blocking_by_year[str(year)] = _blocking_year(session, year)
        _, framing_by_year[str(year)] = _framing_year(session, year)

    stability_by_position = {
        position: _slope_stability(
            [
                float(general_by_year[str(year)]["by_position"][position]["through_origin_slope"])
                for year in YEARS
            ]
        )
        for position in GENERAL_POSITIONS
    }
    stability_by_group = {
        group: _slope_stability(
            [
                float(general_by_year[str(year)]["pooled_groups"][group]["through_origin_slope"])
                for year in YEARS
            ]
        )
        for group in ("IF", "OF")
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "player_value_v1_defense_native_run_rate_calibration_diagnostic",
        "status": "diagnostic_complete_no_production_run_scale_selected",
        "contract": "docs/player-value-v1-defense-native-run-rate-calibration-contract.md",
        "contract_sha256": contract_hash,
        "years": list(YEARS),
        "public_methodology_constants": PUBLIC_METHOD,
        "sources": {
            "fielding": {
                "run_id": FIELDING_RUN_ID,
                "artifact_name": FIELDING_ARTIFACT,
                "artifact_digest": FIELDING_DIGEST,
            },
            "general_range": "sportsdataverse==0.0.75 Savant OAA leaderboard",
            "catcher_throwing_blocking": "repaired direct Baseball Savant year-specific CSV semantics",
            "catcher_framing": "repaired direct Baseball Savant framing-specific year semantics",
        },
        "general_range": {
            "by_year": general_by_year,
            "stability_by_position": stability_by_position,
            "stability_by_group": stability_by_group,
            "calibration_form": "fielding_runs_prevented ~ 0 + slope * (target_z * target_year_position_fielding_outs)",
        },
        "catcher_throwing": {
            "by_year": throwing_by_year,
            "stability": _stability_from_years(throwing_by_year, ("calibration",)),
            "calibration_form": "catcher_stealing_runs ~ 0 + slope * (target_z * sb_attempts)",
        },
        "catcher_blocking": {
            "by_year": blocking_by_year,
            "stability_by_opportunity": {
                basis: _slope_stability(
                    [
                        float(blocking_by_year[str(year)]["calibrations"][basis]["through_origin_slope"])
                        for year in YEARS
                    ]
                )
                for basis in ("n_pbwp", "pitches")
            },
            "calibration_forms": {
                "n_pbwp": "catcher_blocking_runs ~ 0 + slope * (target_z * n_pbwp)",
                "pitches": "catcher_blocking_runs ~ 0 + slope * (target_z * pitches)",
            },
        },
        "catcher_framing": {
            "by_year": framing_by_year,
            "stability": _stability_from_years(framing_by_year, ("calibration",)),
            "calibration_form": "rv_tot ~ 0 + slope * (target_z * pitches)",
        },
        "decision": {
            "diagnostic_complete": True,
            "production_run_scale_selected": False,
            "future_catcher_opportunity_forecast_selected": False,
            "future_standardization_rule_selected": False,
            "positional_adjustment_selected": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_data_accessed": False,
            "2025_confirmation_residuals_used": False,
            "defense_refit": False,
            "defense_rescored": False,
            "playing_time_refit": False,
            "position_role_refit": False,
            "run_conversion_selected": False,
            "positional_adjustment_calculated": False,
            "replacement_level_selected": False,
            "runs_per_win_selected": False,
            "war_value_calculated": False,
        },
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    pl.concat(general_frames, how="vertical_relaxed").sort(
        ["target_year", "position", "player_id"]
    ).write_parquet(args.output_root / "general_range_calibration_rows.parquet")
    _write_markdown(report, args.output_root / "report.md")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
