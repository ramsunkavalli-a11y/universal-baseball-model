#!/usr/bin/env python3
"""Materialize corrected 2022-2024 Savant catcher targets for Defense v1 repair.

Source-only. Uses the year-specific Savant query semantics certified in
`docs/savant-catcher-year-filter-diagnostic.json`. It cannot query 2025,
contains no model fitting/scoring, and preserves the original target definitions.
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
THROWING_MIN = 10
BLOCKING_MIN = 500
USER_AGENT = "universal-baseball-model-defense-catcher-repair/0.1"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _storage(path: Path, table_name: str, row_count: int | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "table_name": table_name,
        "path": str(path).replace("\\", "/"),
        "file_size_bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }
    if row_count is not None:
        result["row_count"] = int(row_count)
    return result


def _params(endpoint: str, year: int) -> dict[str, object]:
    if year not in YEARS:
        raise RuntimeError(f"repair development source may not query year={year}")
    minimum = THROWING_MIN if endpoint == "catcher-throwing" else BLOCKING_MIN
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
    if endpoint == "catcher-throwing":
        params["target_base"] = "All"
    return params


def _request(session: requests.Session, endpoint: str, year: int) -> tuple[bytes, str, pl.DataFrame]:
    url = f"https://baseballsavant.mlb.com/leaderboard/{endpoint}"
    response = session.get(url, params=_params(endpoint, year), timeout=60)
    response.raise_for_status()
    content_type = str(response.headers.get("content-type") or "")
    if "csv" not in content_type.lower():
        raise RuntimeError(f"{endpoint} {year} unexpected content type: {content_type}")
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"{endpoint} {year} returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000, ignore_errors=False)
    if frame.is_empty():
        raise RuntimeError(f"{endpoint} {year} returned empty CSV")
    return raw, response.url, frame


def _assert_year(frame: pl.DataFrame, year: int, label: str) -> None:
    if "start_year" not in frame.columns:
        raise RuntimeError(f"{label} missing start_year")
    observed = {
        int(value)
        for value in frame.get_column("start_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    if observed != {year}:
        raise RuntimeError(f"{label} returned start_year values {sorted(observed)} for requested {year}")
    if "end_year" in frame.columns:
        end_values = frame.get_column("end_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        if end_values and {int(value) for value in end_values} != {year}:
            raise RuntimeError(f"{label} returned end_year values {end_values} for requested {year}")


def _target(frame: pl.DataFrame, *, year: int, kind: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    if kind == "throwing":
        exposure = "sb_attempts"
        target_column = "cs_aa_per_throw"
        minimum = THROWING_MIN
    elif kind == "blocking":
        exposure = "pitches"
        target_column = "blocks_above_average_per_game"
        minimum = BLOCKING_MIN
    else:
        raise ValueError(kind)

    required = {"player_id", "start_year", exposure, target_column}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise RuntimeError(f"{kind} {year} missing columns: {missing}")

    canonical = (
        frame.with_columns(
            pl.col("player_id").cast(pl.Int64, strict=False),
            pl.col(exposure).cast(pl.Float64, strict=False),
            pl.col(target_column).cast(pl.Float64, strict=False).alias("target_raw"),
        )
        .filter(
            pl.col("player_id").is_not_null()
            & pl.col(exposure).is_not_null()
            & (pl.col(exposure) >= float(minimum))
            & pl.col("target_raw").is_not_null()
            & pl.col("target_raw").is_finite()
        )
        .select(
            pl.lit(int(year)).alias("target_year"),
            "player_id",
            pl.col(exposure),
            "target_raw",
        )
        .sort("player_id")
    )
    if canonical.is_empty():
        raise RuntimeError(f"empty eligible repaired {kind} target {year}")
    duplicates = canonical.group_by("player_id").len().filter(pl.col("len") > 1)
    if duplicates.height:
        raise RuntimeError(f"duplicate {kind} player IDs {year}: {duplicates.head(10).to_dicts()}")

    mean = float(canonical.get_column("target_raw").mean())
    sd = float(canonical.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate repaired {kind} target {year}: mean={mean} sd={sd}")
    canonical = canonical.with_columns(
        pl.lit(mean).alias("target_mean"),
        pl.lit(sd).alias("target_sd"),
        ((pl.col("target_raw") - mean) / sd).alias("target_z"),
    )
    if canonical.filter(~pl.col("target_z").is_finite()).height:
        raise RuntimeError(f"nonfinite repaired {kind} target z {year}")
    return canonical, {
        "year": year,
        "kind": kind,
        "source_row_count": int(frame.height),
        "eligible_row_count": int(canonical.height),
        "minimum_exposure": minimum,
        "exposure_column": exposure,
        "target_column": target_column,
        "target_mean": mean,
        "target_population_sd": sd,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    if 2025 in YEARS or max(YEARS) >= 2025:
        raise RuntimeError("development source year boundary includes 2025")

    root = args.output_root
    raw_root = root / "raw"
    table_root = root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    query_records: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    storage: dict[str, Any] = {}
    canonical_frames: list[pl.DataFrame] = []
    payload_hashes: dict[str, list[str]] = {"throwing": [], "blocking": []}

    for year in YEARS:
        for endpoint, kind in (("catcher-throwing", "throwing"), ("catcher-blocking", "blocking")):
            raw, response_url, frame = _request(session, endpoint, year)
            _assert_year(frame, year, f"{endpoint} {year}")
            raw_path = raw_root / f"{endpoint}-{year}.csv"
            raw_path.write_bytes(raw)
            raw_parquet_path = raw_root / f"{endpoint}-{year}.parquet"
            frame.write_parquet(raw_parquet_path, compression="zstd")

            target, diag = _target(frame, year=year, kind=kind)
            target = target.with_columns(pl.lit(kind).alias("component"))
            target_path = table_root / f"catcher_{kind}_targets_{year}.parquet"
            target.write_parquet(target_path, compression="zstd")
            canonical_frames.append(target)
            diagnostics.append(diag)
            payload_hashes[kind].append(_sha_bytes(raw))
            query_records.append(
                {
                    "year": year,
                    "kind": kind,
                    "endpoint": endpoint,
                    "requested_params": _params(endpoint, year),
                    "response_url": response_url,
                    "raw_csv_sha256": _sha_bytes(raw),
                    "source_row_count": int(frame.height),
                }
            )
            storage[f"raw_csv_{kind}_{year}"] = _storage(raw_path, f"defense_v1_catcher_repair_raw_csv_{kind}_{year}")
            storage[f"raw_parquet_{kind}_{year}"] = _storage(raw_parquet_path, f"defense_v1_catcher_repair_raw_{kind}_{year}", frame.height)
            storage[f"targets_{kind}_{year}"] = _storage(target_path, f"defense_v1_catcher_repair_targets_{kind}_{year}", target.height)

    for kind, hashes in payload_hashes.items():
        if len(set(hashes)) != len(YEARS):
            raise RuntimeError(f"repaired {kind} source payloads are not year-specific: {hashes}")

    all_targets = pl.concat(canonical_frames, how="vertical_relaxed").select(
        "component", "target_year", "player_id", "target_raw", "target_z",
        pl.exclude("component", "target_year", "player_id", "target_raw", "target_z"),
    ).sort(["component", "target_year", "player_id"])
    all_path = table_root / "catcher_repair_development_targets_2022_2024.parquet"
    all_targets.write_parquet(all_path, compression="zstd")
    storage["all_targets"] = _storage(all_path, "defense_v1_catcher_repair_development_targets_2022_2024", all_targets.height)

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_catcher_repair_development_source",
        "status": "source_materialized_ready_for_repaired_development",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "diagnostic": "docs/savant-catcher-year-filter-diagnostic.json",
        "years": list(YEARS),
        "source": {
            "provider": "Baseball Savant catcher leaderboards",
            "transport": "direct requests to certified current-UI CSV query semantics",
            "queries": query_records,
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
    print(json.dumps({
        "rows": int(all_targets.height),
        "diagnostics": diagnostics,
        "report": str(report_path),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
