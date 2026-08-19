#!/usr/bin/env python3
"""Materialize corrected 2025 Savant catcher targets for repaired Defense v1.

Source-only. Uses the exact year-specific query semantics certified before the
repaired pre-2025 catcher refit. No model parameters are loaded, no scoring is
performed, and general Defense is untouched.
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
MINIMUMS = {"throwing": 10, "blocking": 500}
ENDPOINTS = {"throwing": "catcher-throwing", "blocking": "catcher-blocking"}
EXPOSURE = {"throwing": "sb_attempts", "blocking": "pitches"}
TARGET = {"throwing": "cs_aa_per_throw", "blocking": "blocks_above_average_per_game"}
EXPECTED_DIAGNOSTIC_STATUS = "target_min_query_certified"
EXPECTED_REPAIRED_PARAMETER_HASH = "sha256:f4790bc1cb4df63d2ba65757455a4b6753e98d25fe552208d893958bdd19f328"


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


def _params(kind: str) -> dict[str, object]:
    params: dict[str, object] = {
        "game_type": "Regular",
        "n": MINIMUMS[kind],
        "season_start": YEAR,
        "season_end": YEAR,
        "split": "no",
        "team": "",
        "type": "Cat",
        "with_team_only": 1,
        "csv": "true",
    }
    if kind == "throwing":
        params["target_base"] = "All"
    return params


def _fetch(session: requests.Session, kind: str) -> tuple[bytes, str, pl.DataFrame]:
    response = session.get(
        f"https://baseballsavant.mlb.com/leaderboard/{ENDPOINTS[kind]}",
        params=_params(kind),
        timeout=60,
    )
    response.raise_for_status()
    if "csv" not in str(response.headers.get("content-type") or "").lower():
        raise RuntimeError(f"{kind} did not return CSV")
    raw = response.content
    if not raw.strip() or raw.lstrip().startswith(b"<"):
        raise RuntimeError(f"{kind} returned empty/HTML body")
    frame = pl.read_csv(io.BytesIO(raw), infer_schema_length=10000)
    if frame.is_empty():
        raise RuntimeError(f"{kind} returned empty CSV")
    return raw, response.url, frame


def _canonical(frame: pl.DataFrame, kind: str) -> tuple[pl.DataFrame, dict[str, Any]]:
    if "start_year" not in frame.columns:
        raise RuntimeError(f"{kind} missing start_year")
    years = {
        int(v) for v in frame.get_column("start_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
    }
    if years != {YEAR}:
        raise RuntimeError(f"{kind} requested {YEAR}, observed start_year={sorted(years)}")
    if "end_year" in frame.columns:
        ends = frame.get_column("end_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        if ends and {int(v) for v in ends} != {YEAR}:
            raise RuntimeError(f"{kind} requested {YEAR}, observed end_year={ends}")

    exposure, target_col, minimum = EXPOSURE[kind], TARGET[kind], MINIMUMS[kind]
    missing = sorted({"player_id", exposure, target_col} - set(frame.columns))
    if missing:
        raise RuntimeError(f"{kind} 2025 missing columns {missing}")

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
            pl.lit(YEAR).alias("target_year"),
            "player_id",
            pl.col(exposure),
            "target_raw",
        )
        .sort("player_id")
    )
    if out.is_empty() or out.group_by("player_id").len().filter(pl.col("len") > 1).height:
        raise RuntimeError(f"invalid canonical {kind} 2025 target population")
    mean = float(out.get_column("target_raw").mean())
    sd = float(out.get_column("target_raw").std(ddof=0))
    if not math.isfinite(mean) or not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate {kind} 2025 target: mean={mean} sd={sd}")
    out = out.with_columns(
        pl.lit(mean).alias("target_mean"),
        pl.lit(sd).alias("target_sd"),
        ((pl.col("target_raw") - mean) / sd).alias("target_z"),
    )
    if out.filter(~pl.col("target_z").is_finite()).height:
        raise RuntimeError(f"nonfinite {kind} 2025 target z")
    return out, {
        "kind": kind,
        "year": YEAR,
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
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--repaired-parameters", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    diagnostic = json.loads(args.diagnostic.read_text())
    params = json.loads(args.repaired_parameters.read_text())
    if diagnostic.get("status") != EXPECTED_DIAGNOSTIC_STATUS:
        raise RuntimeError("certified catcher query diagnostic is not binding")
    if diagnostic.get("decision", {}).get("ui_snake_target_min_query_is_year_specific") is not True:
        raise RuntimeError("certified query is not year-specific")
    if diagnostic.get("target_minimums") != {"catcher-blocking": 500, "catcher-throwing": 10}:
        raise RuntimeError("certified target minima changed")
    if params.get("parameter_hash") != EXPECTED_REPAIRED_PARAMETER_HASH:
        raise RuntimeError(f"repaired parameter hash changed: {params.get('parameter_hash')}")
    decision = params.get("decision", {})
    boundary = params.get("boundary", {})
    if decision.get("repaired_pre_2025_catcher_parameters_frozen") is not True:
        raise RuntimeError("repaired catcher parameters are not frozen")
    if decision.get("repaired_2025_catcher_target_materialization_authorized_next") is not True:
        raise RuntimeError("repaired 2025 catcher source is not authorized")
    if boundary.get("2025_catcher_target_accessed") is not False:
        raise RuntimeError("repaired parameter freeze unexpectedly accessed 2025")
    if boundary.get("general_range_modified") is not False:
        raise RuntimeError("general Defense boundary changed")

    root = args.output_root
    raw_root, table_root = root / "raw", root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "universal-baseball-model-defense-catcher-repair/0.2"})

    storage: dict[str, Any] = {}
    queries: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {}
    for kind in ("throwing", "blocking"):
        raw, response_url, source = _fetch(session, kind)
        target, diag = _canonical(source, kind)
        diagnostics[kind] = diag

        csv_path = raw_root / f"{ENDPOINTS[kind]}-{YEAR}.csv"
        raw_path = raw_root / f"{ENDPOINTS[kind]}-{YEAR}.parquet"
        target_path = table_root / f"catcher_{kind}_targets_{YEAR}.parquet"
        csv_path.write_bytes(raw)
        source.write_parquet(raw_path, compression="zstd")
        target.write_parquet(target_path, compression="zstd")
        storage[f"raw_csv_{kind}"] = _store(csv_path, f"catcher_repair_2025_raw_csv_{kind}")
        storage[f"raw_{kind}"] = _store(raw_path, f"catcher_repair_2025_raw_{kind}", source.height)
        storage[f"targets_{kind}"] = _store(target_path, f"catcher_repair_2025_targets_{kind}", target.height)
        queries.append({
            "kind": kind,
            "endpoint": ENDPOINTS[kind],
            "requested_params": _params(kind),
            "response_url": response_url,
            "source_row_count": int(source.height),
        })

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_catcher_repair_2025_target_source",
        "status": "repaired_2025_catcher_source_certified_ready_for_confirmation",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "season": YEAR,
        "repaired_parameter_hash": EXPECTED_REPAIRED_PARAMETER_HASH,
        "source": {
            "provider": "Baseball Savant catcher leaderboards",
            "transport": "direct certified current-UI CSV query semantics",
            "queries": queries,
        },
        "diagnostics": diagnostics,
        "storage": storage,
        "decision": {
            "repaired_2025_catcher_target_source_certified": True,
            "repaired_catcher_confirmation_authorized_next": True,
            "general_range_reopened": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "model_parameters_loaded_by_source_materializer": False,
            "model_fit": False,
            "model_scoring": False,
            "confirmation_interpreted": False,
            "general_range_accessed": False,
            "general_range_modified": False,
            "war_calculated": False,
        },
    }
    (root / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"diagnostics": diagnostics}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
