#!/usr/bin/env python3
"""Materialize corrected 2022-2024 Savant catcher targets for Defense v1 repair.

Source-only. Uses certified year-specific Savant query semantics, cannot query
2025, and contains no model fitting/scoring.
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

YEARS = (2022, 2023, 2024)
MINIMUMS = {"throwing": 10, "blocking": 500}
ENDPOINTS = {"throwing": "catcher-throwing", "blocking": "catcher-blocking"}
EXPOSURE = {"throwing": "sb_attempts", "blocking": "pitches"}
TARGET = {"throwing": "cs_aa_per_throw", "blocking": "blocks_above_average_per_game"}


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


def _params(kind: str, year: int) -> dict[str, object]:
    if year not in YEARS:
        raise RuntimeError(f"development repair may not query year={year}")
    params: dict[str, object] = {
        "game_type": "Regular",
        "n": MINIMUMS[kind],
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


def _fetch(session: requests.Session, kind: str, year: int) -> tuple[bytes, str, pl.DataFrame]:
    endpoint = ENDPOINTS[kind]
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{endpoint}",
        params=_params(kind, year),
        timeout=60,
    )
    response.raise_for_status()
    if "csv" not in str(response.headers.get("content-type") or "").lower():
        raise RuntimeError(f"{kind} {year} did not return CSV")
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"{kind} {year} returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError(f"{kind} {year} returned empty CSV")
    return raw, response.url, frame


def _validate_year(frame: pl.DataFrame, year: int, kind: str) -> None:
    if "start_year" not in frame.columns:
        raise RuntimeError(f"{kind} {year} missing start_year")
    starts = {
        int(v) for v in frame.get_column("start_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    if starts != {year}:
        raise RuntimeError(f"{kind} requested {year}, observed start_year={sorted(starts)}")
    if "end_year" in frame.columns:
        ends = frame.get_column("end_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        if ends and {int(v) for v in ends} != {year}:
            raise RuntimeError(f"{kind} requested {year}, observed end_year={ends}")


def _canonical(frame: pl.DataFrame, kind: str, year: int) -> tuple[pl.DataFrame, dict[str, Any]]:
    exposure, target_col, minimum = EXPOSURE[kind], TARGET[kind], MINIMUMS[kind]
    required = {"player_id", exposure, target_col}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"{kind} {year} missing columns {missing}")
    out = (
        frame.with_columns(
            pl.col("player_id").cast(pl.Int64, strict=False),
            pl.col(exposure).cast(pl.Float64, strict=False),
            pl.col(target_col).cast(pl.Float64, strict=False).alias("target_raw"),
        )
        .filter(
            pl.col("player_id").is_not_null()
            & pl.col(exposure).is_not_null()
            & (pl.col(exposure) >= float(minimum))
            & pl.col("target_raw").is_not_null()
            & pl.col("target_raw").is_finite()
        )
        .select(
            pl.lit(kind).alias("component"),
            pl.lit(year).alias("target_year"),
            "player_id",
            pl.col(exposure),
            "target_raw",
        )
        .sort("player_id")
    )
    if out.is_empty() or out.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise RuntimeError(f"invalid canonical {kind} target population {year}")
    mean = float(out.get_column("target_raw").mean())
    sd = float(out.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate {kind} target {year}: mean={mean} sd={sd}")
    out = out.with_columns(
        pl.lit(mean).alias("target_mean"),
        pl.lit(sd).alias("target_sd"),
        ((pl.col("target_raw") - mean) / sd).alias("target_z"),
    )
    return out, {
        "kind": kind,
        "year": year,
        "source_row_count": int(frame.height),
        "eligible_row_count": int(out.height),
        "minimum_exposure": minimum,
        "exposure_column": exposure,
        "target_column": target_col,
        "target_mean": mean,
        "target_population_sd": sd,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if max(YEARS) >= 2025:
        raise RuntimeError("2025 boundary violation in development source")

    root = args.output_root
    raw_root, table_root = root / "raw", root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-defense-catcher-repair/0.1"})

    queries: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    frames: list[pl.DataFrame] = []
    storage: dict[str, Any] = {}
    hashes: dict[str, list[str]] = {kind: [] for kind in ENDPOINTS}

    for year in YEARS:
        for kind, endpoint in ENDPOINTS.items():
            raw, response_url, source = _fetch(session, kind, year)
            _validate_year(source, year, kind)
            canonical, diag = _canonical(source, kind, year)
            diagnostics.append(diag)
            frames.append(canonical)
            hashes[kind].append(_sha_bytes(raw))

            csv_path = raw_root / f"{endpoint}-{year}.csv"
            pq_path = raw_root / f"{endpoint}-{year}.parquet"
            target_path = table_root / f"catcher_{kind}_targets_{year}.parquet"
            csv_path.write_bytes(raw)
            source.write_parquet(pq_path, compression="zstd")
            canonical.write_parquet(target_path, compression="zstd")
            storage[f"raw_csv_{kind}_{year}"] = _store(csv_path, f"catcher_repair_raw_csv_{kind}_{year}")
            storage[f"raw_parquet_{kind}_{year}"] = _store(pq_path, f"catcher_repair_raw_{kind}_{year}", source.height)
            storage[f"targets_{kind}_{year}"] = _store(target_path, f"catcher_repair_targets_{kind}_{year}", canonical.height)
            queries.append({
                "kind": kind,
                "year": year,
                "endpoint": endpoint,
                "requested_params": _params(kind, year),
                "response_url": response_url,
                "raw_csv_sha256": _sha_bytes(raw),
                "source_row_count": int(source.height),
            })

    for kind, values in hashes.items():
        if len(set(values)) != len(YEARS):
            raise RuntimeError(f"{kind} repaired payloads not year-specific")

    all_targets = pl.concat(frames, how="diagonal_relaxed").sort(["component", "target_year", "player_id"])
    all_path = table_root / "catcher_repair_development_targets_2022_2024.parquet"
    all_targets.write_parquet(all_path, compression="zstd")
    storage["all_targets"] = _store(all_path, "catcher_repair_development_targets_2022_2024", all_targets.height)

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_catcher_repair_development_source",
        "status": "source_materialized_ready_for_repaired_development",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "diagnostic": "docs/savant-catcher-year-filter-diagnostic.json",
        "years": list(YEARS),
        "source": {
            "provider": "Baseball Savant catcher leaderboards",
            "transport": "direct current-UI CSV query semantics",
            "queries": queries,
        },
        "diagnostics": diagnostics,
        "storage": storage,
        "decision": {
            "year_specific_source_certified": True,
            "repaired_2022_2024_targets_materialized": True,
            "repaired_catcher_development_authorized_next": True,
            "repaired_2025_target_materialization_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_catcher_target_accessed": False,
            "2025_defense_confirmation_accessed": False,
            "model_fit": False,
            "model_scoring": False,
            "general_range_modified": False,
            "source_thresholds_changed_from_original_contract": False,
            "war_calculated": False,
        },
    }
    report_path = root / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"diagnostics": diagnostics, "row_count": all_targets.height}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
