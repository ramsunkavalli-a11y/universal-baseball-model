#!/usr/bin/env python3
"""Materialize target-free 2024 MLB tracked-framing predictor for Defense v1 confirmation."""
from __future__ import annotations

import argparse
from hashlib import sha256
from importlib.metadata import version
import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from sportsdataverse.mlb.mlb_catcher_framing import mlb_catcher_framing
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search

PACKAGE_VERSION = "0.0.75"
SEASON = 2024
QUERY_START = "2024-03-01"
QUERY_END = "2024-10-15"
CHUNK_DAYS = 7
MIN_TAKES = 500
MIN_CELL = 15


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _storage(path: Path, name: str, rows: int) -> dict[str, Any]:
    return {
        "table_name": name,
        "path": str(path).replace("\\", "/"),
        "row_count": int(rows),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }


def _assert_source_shape(pitches: pl.DataFrame) -> None:
    if pitches.is_empty():
        raise RuntimeError("empty 2024 MLB Statcast framing source")
    required = {
        "description",
        "plate_x",
        "plate_z",
        "sz_top",
        "sz_bot",
        "stand",
        "balls",
        "strikes",
        "delta_run_exp",
        "fielder_2",
    }
    missing = sorted(required - set(pitches.columns))
    if missing:
        raise RuntimeError(f"2024 MLB Statcast framing source missing columns: {missing}")
    if "game_year" in pitches.columns:
        years = {
            int(value)
            for value in pitches.get_column("game_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {SEASON}:
            raise RuntimeError(f"unexpected 2024 framing source game_year values: {sorted(years)}")
    if "game_type" in pitches.columns:
        values = {
            str(value)
            for value in pitches.get_column("game_type").cast(pl.Utf8).drop_nulls().unique().to_list()
        }
        if values and values != {"R"}:
            raise RuntimeError(f"unexpected 2024 framing source game_type values: {sorted(values)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected sportsdataverse {PACKAGE_VERSION}, observed {installed}")

    root = args.output_root
    table_root = root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    print(f"Fetching target-free 2024 MLB framing source: {QUERY_START}..{QUERY_END}", flush=True)
    pitches = mlb_statcast_search(
        QUERY_START,
        QUERY_END,
        season=SEASON,
        game_type="R",
        chunk_days=CHUNK_DAYS,
    )
    _assert_source_shape(pitches)

    take_count = int(
        pitches.filter(
            pl.col("description").is_in(["called_strike", "ball"])
            & pl.col("plate_x").is_not_null()
            & pl.col("plate_z").is_not_null()
            & pl.col("sz_top").is_not_null()
            & pl.col("sz_bot").is_not_null()
        ).height
    )

    raw = mlb_catcher_framing(pitches)
    needed = {"catcher_id", "takes", "framing_runs", "strikes_gained"}
    missing = sorted(needed - set(raw.columns))
    if missing:
        raise RuntimeError(f"mlb_catcher_framing 2024 output missing columns: {missing}")

    proxy = (
        raw.with_columns(
            pl.col("catcher_id").cast(pl.Int64, strict=False).alias("player_id"),
            pl.col("takes").cast(pl.Int64, strict=False),
            pl.col("framing_runs").cast(pl.Float64, strict=False),
            pl.col("strikes_gained").cast(pl.Float64, strict=False),
        )
        .filter(pl.col("player_id").is_not_null())
        .with_columns(
            pl.lit(SEASON).alias("season"),
            pl.lit("MLB").alias("level_group"),
            pl.when(pl.col("takes") > 0)
            .then(1000.0 * pl.col("framing_runs") / pl.col("takes"))
            .otherwise(None)
            .alias("tracked_framing_per_1000_takes"),
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "takes",
            "strikes_gained",
            "framing_runs",
            "tracked_framing_per_1000_takes",
        )
        .sort("player_id")
    )
    if proxy.is_empty():
        raise RuntimeError("empty 2024 MLB framing proxy")
    if proxy.group_by(["season", "level_group", "player_id"]).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("2024 MLB framing proxy violates player grain")

    eligible = proxy.filter(
        (pl.col("takes") >= MIN_TAKES)
        & pl.col("tracked_framing_per_1000_takes").is_not_null()
        & pl.col("tracked_framing_per_1000_takes").is_finite()
    )
    if eligible.height < MIN_CELL:
        raise RuntimeError(f"insufficient 2024 MLB framing standardization cell: {eligible.height} < {MIN_CELL}")

    mean = float(eligible.get_column("tracked_framing_per_1000_takes").mean())
    sd = float(eligible.get_column("tracked_framing_per_1000_takes").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate 2024 MLB framing standardization: mean={mean} sd={sd}")

    moments = pl.DataFrame(
        [
            {
                "season": SEASON,
                "level_group": "MLB",
                "mean": mean,
                "sd": sd,
                "eligible_catcher_count": int(eligible.height),
                "tracked_z_available": True,
            }
        ]
    )
    scored = (
        eligible.with_columns(
            ((pl.col("tracked_framing_per_1000_takes") - mean) / sd).alias("tracked_framing_z")
        )
        .select(
            "season",
            "level_group",
            "player_id",
            "takes",
            "strikes_gained",
            "framing_runs",
            "tracked_framing_per_1000_takes",
            "tracked_framing_z",
        )
        .sort("player_id")
    )
    if scored.filter(~pl.col("tracked_framing_z").is_finite()).height:
        raise RuntimeError("nonfinite 2024 MLB tracked_framing_z")
    if scored.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("duplicate 2024 MLB tracked_framing_z player id")

    proxy_path = table_root / "tracked_framing_proxy_2024_mlb.parquet"
    z_path = table_root / "tracked_framing_z_2024_mlb.parquet"
    moments_path = table_root / "tracked_framing_moments_2024_mlb.parquet"
    proxy.write_parquet(proxy_path, compression="zstd")
    scored.write_parquet(z_path, compression="zstd")
    moments.write_parquet(moments_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2024_mlb_framing_confirmation_predictor_source",
        "status": "source_materialized",
        "contract": "docs/defense-v1-framing-2025-confirmation-contract.md",
        "query": {
            "source": "Baseball Savant MLB Statcast CSV via SportsDataverse",
            "season": SEASON,
            "start": QUERY_START,
            "end": QUERY_END,
            "game_type": "R",
            "chunk_days": CHUNK_DAYS,
            "bounded_envelope_note": "dates bracket the full 2024 season; game_type R is the binding regular-season filter",
        },
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "search_function": "mlb_statcast_search",
            "framing_function": "mlb_catcher_framing",
        },
        "feature_contract": {
            "formula": "tracked_framing_per_1000_takes = 1000 * framing_runs / takes",
            "minimum_takes": MIN_TAKES,
            "standardization": "2024 x MLB mean 0 / population SD 1",
            "minimum_eligible_catchers": MIN_CELL,
            "source_level": "MLB_only",
        },
        "diagnostics": {
            "pitch_row_count": int(pitches.height),
            "column_count": len(pitches.columns),
            "eligible_take_row_count": take_count,
            "framing_proxy_catcher_count": int(proxy.height),
            "framing_total_takes": int(proxy.get_column("takes").sum() or 0),
            "eligible_framing_catcher_count": int(eligible.height),
            "tracked_framing_z_catcher_count": int(scored.height),
            "mean": mean,
            "population_sd": sd,
        },
        "storage": {
            "framing_proxy": _storage(proxy_path, "defense_v1_2024_mlb_tracked_framing_proxy", proxy.height),
            "tracked_framing_z": _storage(z_path, "defense_v1_2024_mlb_tracked_framing_z", scored.height),
            "moments": _storage(moments_path, "defense_v1_2024_mlb_tracked_framing_moments", moments.height),
        },
        "decision": {
            "2024_mlb_framing_confirmation_predictor_materialized": True,
            "2025_framing_target_source_materialized": False,
            "2025_framing_target_materialization_authorized_next": True,
            "confirmation_scoring_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_source_accessed": False,
            "2025_framing_target_accessed": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "model_scoring_performed": False,
            "tracked_milb_2024_accessed": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "pitch_rows": report["diagnostics"]["pitch_row_count"],
            "proxy_catchers": report["diagnostics"]["framing_proxy_catcher_count"],
            "eligible_catchers": report["diagnostics"]["eligible_framing_catcher_count"],
            "mean": mean,
            "sd": sd,
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())