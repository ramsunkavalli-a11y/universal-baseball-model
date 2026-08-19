#!/usr/bin/env python3
"""Materialize the frozen Defense v1 completed-2025 target surfaces only.

This is a source-only step. It contains no fitted Defense parameters and no
model scorer. The only transformations are the target eligibility and
standardization rules frozen in docs/defense-v1-2025-confirmation-contract.md.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from sportsdataverse.mlb.mlb_statcast import (
    mlb_statcast_leaderboard_catcher_blocking,
    mlb_statcast_leaderboard_catcher_throwing,
    mlb_statcast_leaderboard_outs_above_average,
)


YEAR = 2025
PINNED_SPORTSDATAVERSE = "0.0.75"
GENERAL_POSITIONS = {"1B", "2B", "3B", "SS", "LF", "CF", "RF"}
CONTRACT = "docs/defense-v1-2025-confirmation-contract.md"


def _float_text(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"nan", "none", "null", "--"}:
        return None
    if text.endswith("%"):
        text = text[:-1].strip()
    try:
        result = float(text)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _table_record(path: Path, frame: pl.DataFrame, table_name: str) -> dict[str, Any]:
    return {
        "table_name": table_name,
        "path": path.as_posix(),
        "row_count": int(frame.height),
        "column_count": int(frame.width),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _write_table(root: Path, relative: str, frame: pl.DataFrame, table_name: str) -> dict[str, Any]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)
    return _table_record(path, frame, table_name)


def _require_columns(frame: pl.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"{label} missing required columns: {missing}")


def _require_unique(frame: pl.DataFrame, keys: list[str], label: str) -> None:
    duplicates = frame.group_by(keys).len().filter(pl.col("len") > 1)
    if duplicates.height:
        preview = duplicates.sort(keys).head(10).to_dicts()
        raise RuntimeError(f"{label} duplicate keys {keys}: count={duplicates.height} preview={preview}")


def _require_finite(frame: pl.DataFrame, columns: list[str], label: str) -> None:
    for column in columns:
        values = frame.get_column(column).to_list()
        bad = [value for value in values if value is None or not math.isfinite(float(value))]
        if bad:
            raise RuntimeError(f"{label} has {len(bad)} nonfinite/null values in {column}")


def _general_targets(raw: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    needed = {"player_id", "primary_pos_formatted", "diff_success_rate_formatted"}
    _require_columns(raw, needed, "2025 OAA leaderboard")

    rows: list[dict[str, Any]] = []
    for row in raw.select(*sorted(needed)).iter_rows(named=True):
        player = _float_text(row["player_id"])
        target = _float_text(row["diff_success_rate_formatted"])
        position = str(row["primary_pos_formatted"] or "").strip()
        if (
            player is None
            or not float(player).is_integer()
            or target is None
            or position not in GENERAL_POSITIONS
        ):
            continue
        rows.append(
            {
                "season": YEAR,
                "player_id": int(player),
                "position": position,
                "target_raw": float(target),
            }
        )

    frame = pl.DataFrame(
        rows,
        schema={"season": pl.Int64, "player_id": pl.Int64, "position": pl.Utf8, "target_raw": pl.Float64},
    )
    if frame.is_empty():
        raise RuntimeError("empty eligible 2025 OAA target surface")
    _require_unique(frame, ["player_id", "position"], "2025 general range target")
    _require_finite(frame, ["target_raw"], "2025 general range target")

    moments = (
        frame.group_by("position")
        .agg(
            pl.col("target_raw").mean().alias("target_mean"),
            pl.col("target_raw").std(ddof=0).alias("target_sd"),
            pl.len().alias("target_position_count"),
        )
        .sort("position")
    )
    _require_finite(moments, ["target_mean", "target_sd"], "2025 general range moments")
    degenerate = moments.filter(pl.col("target_sd") <= 1e-12)
    if degenerate.height:
        raise RuntimeError(f"degenerate 2025 general target SD: {degenerate.to_dicts()}")

    canonical = (
        frame.join(moments, on="position", how="left")
        .with_columns(((pl.col("target_raw") - pl.col("target_mean")) / pl.col("target_sd")).alias("range_target_z"))
        .sort(["position", "player_id"])
    )
    _require_finite(canonical, ["target_raw", "target_mean", "target_sd", "range_target_z"], "2025 general range canonical target")
    return canonical, moments


def _catcher_target(raw: pl.DataFrame, kind: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    if kind == "throwing":
        exposure_column = "sb_attempts"
        target_column = "cs_aa_per_throw"
        minimum_exposure = 10.0
        target_z_name = "throwing_target_z"
        label = "2025 catcher throwing"
    elif kind == "blocking":
        exposure_column = "pitches"
        target_column = "blocks_above_average_per_game"
        minimum_exposure = 500.0
        target_z_name = "blocking_target_z"
        label = "2025 catcher blocking"
    else:
        raise ValueError(kind)

    needed = {"player_id", exposure_column, target_column}
    _require_columns(raw, needed, f"{label} leaderboard")

    rows: list[dict[str, Any]] = []
    for row in raw.select(*sorted(needed)).iter_rows(named=True):
        player = _float_text(row["player_id"])
        exposure = _float_text(row[exposure_column])
        target = _float_text(row[target_column])
        if (
            player is None
            or not float(player).is_integer()
            or exposure is None
            or exposure < minimum_exposure
            or target is None
        ):
            continue
        rows.append(
            {
                "season": YEAR,
                "player_id": int(player),
                exposure_column: float(exposure),
                "target_raw": float(target),
            }
        )

    schema = {
        "season": pl.Int64,
        "player_id": pl.Int64,
        exposure_column: pl.Float64,
        "target_raw": pl.Float64,
    }
    frame = pl.DataFrame(rows, schema=schema)
    if frame.is_empty():
        raise RuntimeError(f"empty eligible {label} target surface")
    _require_unique(frame, ["player_id"], f"{label} target")
    _require_finite(frame, [exposure_column, "target_raw"], f"{label} target")

    mean = float(frame.get_column("target_raw").mean())
    sd = float(frame.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate {label} target moments mean={mean} sd={sd}")

    canonical = (
        frame.with_columns(
            pl.lit(mean).alias("target_mean"),
            pl.lit(sd).alias("target_sd"),
            pl.lit(frame.height).cast(pl.Int64).alias("target_count"),
            ((pl.col("target_raw") - mean) / sd).alias(target_z_name),
        )
        .sort("player_id")
    )
    _require_finite(canonical, ["target_raw", "target_mean", "target_sd", target_z_name], f"{label} canonical target")
    return canonical, {
        "mean": mean,
        "sd": sd,
        "count": int(frame.height),
        "minimum_exposure": minimum_exposure,
        "exposure_column": exposure_column,
        "target_column": target_column,
        "target_z_column": target_z_name,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=Path("reports/generated/defense-v1-2025-target-source"))
    args = parser.parse_args()
    root = args.output_root
    root.mkdir(parents=True, exist_ok=True)

    package_version = importlib.metadata.version("sportsdataverse")
    if package_version != PINNED_SPORTSDATAVERSE:
        raise RuntimeError(f"sportsdataverse version mismatch: {package_version} != {PINNED_SPORTSDATAVERSE}")

    raw_general = mlb_statcast_leaderboard_outs_above_average(year=YEAR)
    raw_throwing = mlb_statcast_leaderboard_catcher_throwing(year=YEAR)
    raw_blocking = mlb_statcast_leaderboard_catcher_blocking(year=YEAR)
    for label, frame in {
        "general": raw_general,
        "throwing": raw_throwing,
        "blocking": raw_blocking,
    }.items():
        if not isinstance(frame, pl.DataFrame):
            raise RuntimeError(f"{label} source returned {type(frame)!r}, expected polars.DataFrame")
        if frame.is_empty():
            raise RuntimeError(f"{label} source returned an empty dataframe")

    general, general_moments = _general_targets(raw_general)
    throwing, throwing_moments = _catcher_target(raw_throwing, "throwing")
    blocking, blocking_moments = _catcher_target(raw_blocking, "blocking")

    storage = {
        "raw_general": _write_table(root, "raw/oaa_leaderboard_2025.parquet", raw_general, "defense_v1_2025_raw_oaa_leaderboard"),
        "raw_throwing": _write_table(root, "raw/catcher_throwing_leaderboard_2025.parquet", raw_throwing, "defense_v1_2025_raw_catcher_throwing_leaderboard"),
        "raw_blocking": _write_table(root, "raw/catcher_blocking_leaderboard_2025.parquet", raw_blocking, "defense_v1_2025_raw_catcher_blocking_leaderboard"),
        "general_targets": _write_table(root, "tables/general_range_targets_2025.parquet", general, "defense_v1_2025_general_range_targets"),
        "general_target_moments": _write_table(root, "tables/general_range_target_moments_2025.parquet", general_moments, "defense_v1_2025_general_range_target_moments"),
        "throwing_targets": _write_table(root, "tables/catcher_throwing_targets_2025.parquet", throwing, "defense_v1_2025_catcher_throwing_targets"),
        "blocking_targets": _write_table(root, "tables/catcher_blocking_targets_2025.parquet", blocking, "defense_v1_2025_catcher_blocking_targets"),
    }

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2025_target_source_materialization",
        "contract": CONTRACT,
        "status": "certified_source_ready_for_confirmation_scoring",
        "season": YEAR,
        "source": {
            "package": "sportsdataverse",
            "package_version": package_version,
            "queries": [
                {"function": "mlb_statcast_leaderboard_outs_above_average", "year": YEAR, "surface": "Outs Above Average leaderboard"},
                {"function": "mlb_statcast_leaderboard_catcher_throwing", "year": YEAR, "surface": "Catcher Throwing leaderboard"},
                {"function": "mlb_statcast_leaderboard_catcher_blocking", "year": YEAR, "surface": "Catcher Blocking leaderboard"},
            ],
            "raw_row_counts": {
                "general": int(raw_general.height),
                "throwing": int(raw_throwing.height),
                "blocking": int(raw_blocking.height),
            },
        },
        "targets": {
            "general_range": {
                "target_column": "diff_success_rate_formatted",
                "positions": sorted(GENERAL_POSITIONS),
                "canonical_row_count": int(general.height),
                "position_counts": {
                    str(row["position"]): int(row["target_position_count"])
                    for row in general_moments.iter_rows(named=True)
                },
                "standardization": "within 2025 x target position, population SD",
            },
            "catcher_throwing": {
                "canonical_row_count": int(throwing.height),
                "standardization": "within eligible 2025 catchers, population SD",
                **throwing_moments,
            },
            "catcher_blocking": {
                "canonical_row_count": int(blocking.height),
                "standardization": "within eligible 2025 catchers, population SD",
                **blocking_moments,
            },
        },
        "storage": storage,
        "boundary": {
            "2025_defensive_targets_accessed": True,
            "2025_target_source_materialized": True,
            "2025_predictor_used": False,
            "frozen_model_parameters_loaded_by_materializer": False,
            "model_fit": False,
            "model_scoring": False,
            "confirmation_interpreted": False,
            "run_value_conversion_performed": False,
            "war_value_authorized": False,
        },
        "decision": {
            "target_source_certified": True,
            "confirmation_scoring_authorized_only_after_required_predictor_source_certification": True,
            "war_value_authorized": False,
        },
    }
    report_path = root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "general_targets": general.height,
        "throwing_targets": throwing.height,
        "blocking_targets": blocking.height,
        "report": report_path.as_posix(),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
