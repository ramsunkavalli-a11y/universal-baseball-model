#!/usr/bin/env python3
"""Rerun the original Defense v1 catcher development gate on repaired targets.

This is a source-repair rerun only. Candidate families, predictor evidence,
normalization, folds, and promotion rules are imported from the original frozen
implementation. No 2025 target is read and general range is not evaluated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl

from develop_defense_v1_universal import _evaluate_catcher, _load_profiles

TARGET_YEARS = (2022, 2023, 2024)
EXPECTED_HISTORICAL_RUN = 32148467330
EXPECTED_SOURCE_STATUS = "source_materialized_ready_for_repaired_development"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} under {root}; observed={matches}")
    return matches[0]


def _load_targets(root: Path, source_result: dict[str, Any], kind: str) -> dict[int, pl.DataFrame]:
    out: dict[int, pl.DataFrame] = {}
    for year in TARGET_YEARS:
        name = f"catcher_{kind}_targets_{year}.parquet"
        path = _find_one(root, name)
        expected = source_result["storage"][f"targets_{kind}_{year}"]
        if _sha(path) != expected["sha256"]:
            raise RuntimeError(f"repaired {kind} target SHA mismatch for {year}")
        frame = pl.read_parquet(path)
        if frame.height != int(expected["row_count"]):
            raise RuntimeError(f"repaired {kind} target row-count mismatch for {year}")
        required = {"component", "target_year", "player_id", "target_raw", "target_z"}
        missing = sorted(required - set(frame.columns))
        if missing:
            raise RuntimeError(f"repaired {kind} target {year} missing {missing}")
        if set(frame.get_column("target_year").unique().to_list()) != {year}:
            raise RuntimeError(f"repaired {kind} target contains wrong year for {year}")
        if set(frame.get_column("component").unique().to_list()) != {kind}:
            raise RuntimeError(f"repaired target component mismatch for {kind} {year}")
        if frame.filter(pl.col("target_z").is_null() | ~pl.col("target_z").is_finite()).height:
            raise RuntimeError(f"nonfinite repaired {kind} target z for {year}")
        out[year] = frame.select("player_id", "target_raw", "target_z")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--repaired-source-root", type=Path, required=True)
    parser.add_argument("--repaired-source-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_result = json.loads(args.repaired_source_result.read_text())
    if source_result.get("status") != EXPECTED_SOURCE_STATUS:
        raise RuntimeError(f"repaired source not certified: {source_result.get('status')}")
    if source_result.get("years") != list(TARGET_YEARS):
        raise RuntimeError(f"unexpected repaired target years: {source_result.get('years')}")
    decision = source_result.get("decision", {})
    boundary = source_result.get("boundary", {})
    if decision.get("repaired_catcher_development_authorized_next") is not True:
        raise RuntimeError("repaired catcher development not authorized")
    if boundary.get("2025_catcher_target_accessed") is not False:
        raise RuntimeError("repaired development source crossed 2025 boundary")
    if boundary.get("model_fit") is not False or boundary.get("model_scoring") is not False:
        raise RuntimeError("repaired target source was not source-only")
    if boundary.get("general_range_modified") is not False:
        raise RuntimeError("general range boundary changed")

    throwing_targets = _load_targets(args.repaired_source_root, source_result, "throwing")
    blocking_targets = _load_targets(args.repaired_source_root, source_result, "blocking")

    _, profile_meta = _load_profiles(args.historical_root)
    catcher = profile_meta["catcher"]

    throwing = _evaluate_catcher(catcher, throwing_targets, "throwing", "caught_stealing_pct")
    blocking = _evaluate_catcher(catcher, blocking_targets, "blocking", "passed_balls_per_9")

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_catcher_repair_development",
        "status": "repaired_development_complete",
        "contract": "docs/defense-v1-catcher-source-repair-contract.md",
        "original_development_contract": "docs/defense-v1-development-contract.md",
        "source": {
            "historical_source_run_id": EXPECTED_HISTORICAL_RUN,
            "historical_artifact_name": "position-role-historical-source-2021-2024",
            "repaired_target_source_run_id": source_result.get("source_run_id"),
            "repaired_target_source_sha": source_result.get("source_sha"),
            "target_years": list(TARGET_YEARS),
            "throwing_target_rows": {str(y): int(throwing_targets[y].height) for y in TARGET_YEARS},
            "blocking_target_rows": {str(y): int(blocking_targets[y].height) for y in TARGET_YEARS},
        },
        "catcher_throwing": throwing,
        "catcher_blocking": blocking,
        "decision": {
            "catcher_throwing_selected_family": throwing["selected"],
            "catcher_throwing_passed": bool(throwing["component_passed"]),
            "catcher_blocking_selected_family": blocking["selected"],
            "catcher_blocking_passed": bool(blocking["component_passed"]),
            "repaired_catcher_development_complete": True,
            "repaired_pre_2025_catcher_refit_authorized_next": bool(throwing["component_passed"] or blocking["component_passed"]),
            "repaired_2025_catcher_target_materialization_authorized": False,
            "general_range_reopened": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_catcher_target_accessed": False,
            "2025_confirmation_residuals_used": False,
            "new_candidate_family_added": False,
            "development_threshold_changed": False,
            "general_range_evaluated": False,
            "general_range_modified": False,
            "war_calculated": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
