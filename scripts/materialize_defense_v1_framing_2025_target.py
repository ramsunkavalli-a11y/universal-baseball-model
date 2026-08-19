#!/usr/bin/env python3
"""Materialize untouched 2025 Baseball Savant catcher-framing target for Defense v1 confirmation."""
from __future__ import annotations

import argparse
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from typing import Any

import polars as pl
import requests

YEAR = 2025
ENDPOINT = "catcher-framing"
SOURCE_MIN = 1
LOCAL_MIN_PITCHES = 1000


def _sha_bytes(value: bytes) -> str:
    return sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _storage(path: Path, name: str, rows: int | None = None) -> dict[str, Any]:
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
        "min": SOURCE_MIN,
        "sortColumn": "rv_tot",
        "sortDirection": "desc",
        "csv": "true",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    root = args.output_root
    raw_root = root / "raw"
    table_root = root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-defense-framing-2025-target/0.1"})
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{ENDPOINT}",
        params=_params(),
        timeout=60,
    )
    response.raise_for_status()
    content_type = str(response.headers.get("content-type") or "").lower()
    if "csv" not in content_type and "text/plain" not in content_type:
        raise RuntimeError(f"2025 framing target did not return CSV-like content: {content_type}")
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError("2025 framing target returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError("2025 framing target returned empty CSV")

    id_candidates = [column for column in ("id", "player_id") if column in frame.columns]
    if len(id_candidates) != 1:
        raise RuntimeError(f"expected exactly one framing id column, observed={id_candidates}")
    id_col = id_candidates[0]
    required = {id_col, "rv_tot", "pitches"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"2025 framing target missing {missing}")

    embedded: dict[str, list[int]] = {}
    for column in ("start_year", "end_year", "season", "year", "season_start", "season_end"):
        if column not in frame.columns:
            continue
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
            embedded[column] = ints
            if set(ints) != {YEAR}:
                raise RuntimeError(f"2025 framing requested, observed {column}={ints}")

    target = (
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
    if target.is_empty():
        raise RuntimeError("empty eligible 2025 framing target population")
    if target.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise RuntimeError("duplicate player id in 2025 framing target")

    mean = float(target.get_column("target_raw").mean())
    sd = float(target.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate 2025 framing target: mean={mean} sd={sd}")
    target = target.with_columns(
        pl.lit(mean).alias("target_mean"),
        pl.lit(sd).alias("target_sd"),
        ((pl.col("target_raw") - mean) / sd).alias("target_z"),
    )
    if target.filter(~pl.col("target_z").is_finite()).height:
        raise RuntimeError("nonfinite 2025 framing target z")

    csv_path = raw_root / "catcher-framing-2025.csv"
    raw_parquet = raw_root / "catcher-framing-2025.parquet"
    target_path = table_root / "catcher_framing_targets_2025.parquet"
    csv_path.write_bytes(raw)
    frame.write_parquet(raw_parquet, compression="zstd")
    target.write_parquet(target_path, compression="zstd")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_2025_framing_target_source",
        "status": "source_materialized",
        "contract": "docs/defense-v1-framing-2025-confirmation-contract.md",
        "source": {
            "provider": "Baseball Savant catcher-framing leaderboard",
            "endpoint": f"https://baseballsavant.mlb.com/leaderboard/{ENDPOINT}",
            "requested_params": _params(),
            "response_url": response.url,
            "raw_csv_sha256": _sha_bytes(raw),
            "embedded_year_values": embedded,
        },
        "target_contract": {
            "minimum_pitches": LOCAL_MIN_PITCHES,
            "formula": "1000 * rv_tot / pitches",
            "standardization": "within eligible 2025 population; population sd ddof=0",
        },
        "diagnostics": {
            "source_row_count": int(frame.height),
            "eligible_target_row_count": int(target.height),
            "target_mean": mean,
            "target_population_sd": sd,
        },
        "storage": {
            "raw_csv": _storage(csv_path, "framing_2025_raw_csv"),
            "raw_parquet": _storage(raw_parquet, "framing_2025_raw", frame.height),
            "target": _storage(target_path, "framing_2025_target", target.height),
        },
        "decision": {
            "2025_framing_target_source_materialized": True,
            "2025_framing_confirmation_scoring_authorized_next": True,
            "war_value_authorized": False,
        },
        "boundary": {
            "model_parameters_loaded": False,
            "2024_predictor_loaded": False,
            "model_fit": False,
            "model_scoring_performed": False,
            "confirmation_interpreted": False,
            "alternate_target_queried": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["diagnostics"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())