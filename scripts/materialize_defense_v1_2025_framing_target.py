#!/usr/bin/env python3
"""Materialize the repaired 2025 Savant catcher-framing target for Defense v1.

Source-only. Reuses the certified framing-specific Savant query and target
construction from repaired 2022-2024 development. Contains no model fitting or
scoring.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any

import polars as pl
import requests

YEAR = 2025
ENDPOINT = "catcher-framing"
LOCAL_MIN_PITCHES = 1000
SOURCE_MIN_CALLED_PITCHES = 1


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _store(path: Path, name: str, rows: int | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "table_name": name,
        "path": str(path).replace("\\", "/"),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }
    if rows is not None:
        out["row_count"] = int(rows)
    return out


def _params() -> dict[str, object]:
    return {
        "type": "catcher",
        "seasonStart": YEAR,
        "seasonEnd": YEAR,
        "team": "",
        "min": SOURCE_MIN_CALLED_PITCHES,
        "sortColumn": "rv_tot",
        "sortDirection": "desc",
        "csv": "true",
    }


def _fetch(session: requests.Session) -> tuple[bytes, str, pl.DataFrame]:
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{ENDPOINT}",
        params=_params(),
        timeout=60,
    )
    response.raise_for_status()
    content_type = str(response.headers.get("content-type") or "").lower()
    if "csv" not in content_type and "text/plain" not in content_type:
        raise RuntimeError(f"framing {YEAR} did not return CSV-like content: {content_type}")
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"framing {YEAR} returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError(f"framing {YEAR} returned empty CSV")
    return raw, response.url, frame


def _resolve_id_column(frame: pl.DataFrame) -> str:
    candidates = [column for column in ("id", "player_id") if column in frame.columns]
    if len(candidates) != 1:
        raise RuntimeError(f"framing {YEAR} expected exactly one id/player_id column, observed={candidates}")
    return candidates[0]


def _validate_embedded_year(frame: pl.DataFrame) -> dict[str, Any]:
    candidates = [
        column
        for column in ("start_year", "end_year", "season", "year", "season_start", "season_end")
        if column in frame.columns
    ]
    observed: dict[str, list[int]] = {}
    for column in candidates:
        values = (
            frame.get_column(column)
            .cast(pl.Int64, strict=False)
            .drop_nulls()
            .unique()
            .sort()
            .to_list()
        )
        if values:
            ints = [int(value) for value in values]
            observed[column] = ints
            if set(ints) != {YEAR}:
                raise RuntimeError(f"framing requested {YEAR}, observed {column}={ints}")
    return {
        "embedded_year_columns_checked": candidates,
        "embedded_year_values": observed,
    }


def _canonical(frame: pl.DataFrame) -> tuple[pl.DataFrame, dict[str, Any]]:
    id_col = _resolve_id_column(frame)
    required = {id_col, "rv_tot", "pitches"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"framing {YEAR} missing columns {missing}")

    out = (
        frame.with_columns(
            pl.col(id_col).cast(pl.Int64, strict=False).alias("player_id"),
            pl.col("rv_tot").cast(pl.Float64, strict=False),
            pl.col("pitches").cast(pl.Float64, strict=False),
        )
        .filter(
            pl.col("player_id").is_not_null()
            & pl.col("rv_tot").is_not_null()
            & pl.col("rv_tot").is_finite()
            & pl.col("pitches").is_not_null()
            & pl.col("pitches").is_finite()
            & (pl.col("pitches") >= float(LOCAL_MIN_PITCHES))
        )
        .with_columns((1000.0 * pl.col("rv_tot") / pl.col("pitches")).alias("target_raw"))
        .filter(pl.col("target_raw").is_not_null() & pl.col("target_raw").is_finite())
        .select(
            pl.lit(YEAR).alias("target_year"),
            "player_id",
            "pitches",
            "rv_tot",
            "target_raw",
        )
        .sort("player_id")
    )

    if out.is_empty():
        raise RuntimeError(f"empty canonical framing target population {YEAR}")
    duplicates = out.group_by("player_id").len().filter(pl.col("len") > 1)
    if duplicates.height:
        raise RuntimeError(f"duplicate canonical framing player ids {YEAR}: {duplicates.height}")

    mean = float(out.get_column("target_raw").mean())
    sd = float(out.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate framing target {YEAR}: mean={mean} sd={sd}")

    out = out.with_columns(
        pl.lit(mean).alias("target_mean"),
        pl.lit(sd).alias("target_sd"),
        ((pl.col("target_raw") - mean) / sd).alias("target_z"),
    )
    if not out.get_column("target_z").is_finite().all():
        raise RuntimeError(f"nonfinite framing target z values {YEAR}")

    return out, {
        "year": YEAR,
        "source_row_count": int(frame.height),
        "eligible_row_count": int(out.height),
        "local_minimum_pitches": LOCAL_MIN_PITCHES,
        "source_minimum_called_pitches": SOURCE_MIN_CALLED_PITCHES,
        "target_formula": "1000 * rv_tot / pitches",
        "target_standardization": "within target season, population sd ddof=0",
        "target_mean": mean,
        "target_population_sd": sd,
        "id_column": id_col,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    root = args.output_root
    raw_root, table_root = root / "raw", root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-defense-framing-2025-target/0.1"})

    raw, response_url, source = _fetch(session)
    year_validation = _validate_embedded_year(source)
    canonical, diagnostic = _canonical(source)
    diagnostic.update(year_validation)

    raw_sha = _sha_bytes(raw)
    csv_path = raw_root / f"{ENDPOINT}-{YEAR}.csv"
    pq_path = raw_root / f"{ENDPOINT}-{YEAR}.parquet"
    target_path = table_root / "catcher_framing_target_2025.parquet"
    csv_path.write_bytes(raw)
    source.write_parquet(pq_path, compression="zstd")
    canonical.write_parquet(target_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_repaired_framing_2025_target_source",
        "status": "source_materialized",
        "contract": "docs/defense-v1-framing-2025-confirmation-contract.md",
        "source": {
            "provider": "Baseball Savant catcher-framing leaderboard",
            "transport": "direct framing-specific CSV query semantics",
            "endpoint": f"https://baseballsavant.mlb.com/leaderboard/{ENDPOINT}",
            "query": {
                "year": YEAR,
                "requested_params": _params(),
                "response_url": response_url,
                "raw_csv_sha256": raw_sha,
                "source_row_count": int(source.height),
            },
            "known_invalid_prior_transport": "SportsDataverse 0.0.75 generic year query parameter",
        },
        "diagnostics": diagnostic,
        "storage": {
            "raw_csv": _store(csv_path, "framing_2025_raw_csv"),
            "raw_parquet": _store(pq_path, "framing_2025_raw", source.height),
            "target": _store(target_path, "framing_2025_target", canonical.height),
        },
        "decision": {
            "2025_framing_target_source_materialized": True,
            "framing_confirmation_scoring_authorized_next": True,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_framing_target_accessed": True,
            "2025_nonframing_defense_target_accessed": False,
            "2025_framing_predictor_accessed": False,
            "model_parameters_loaded": False,
            "model_fit": False,
            "model_scoring": False,
            "confirmation_interpreted": False,
            "general_range_modified": False,
            "catcher_throwing_modified": False,
            "catcher_blocking_modified": False,
            "tracked_framing_predictor_modified": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"diagnostics": diagnostic, "raw_sha256": raw_sha}, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
