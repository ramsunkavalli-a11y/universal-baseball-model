#!/usr/bin/env python3
"""Rerun the frozen Defense v1 catcher-framing F0/F1 gate on repaired targets.

No live source calls. Reuses the original tracked-framing evaluator verbatim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import polars as pl

from audit_defense_v1_tracked_challenger import _evaluate_framing, _find_one, _z_framing
from develop_defense_v1_universal import _load_profiles

REPAIR_CONTRACT = Path("docs/defense-v1-framing-source-repair-contract.md")
REPAIR_SOURCE_RESULT = Path("docs/defense-v1-framing-repair-development-source-result.json")
TRACKED_SOURCE_RESULT = Path("docs/defense-v1-tracked-source-result.json")
TARGET_YEARS = (2022, 2023, 2024)


def _sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_file(path: Path, expected_sha: str, label: str) -> None:
    observed = _sha_file(path)
    if observed != expected_sha:
        raise RuntimeError(f"{label} sha256 mismatch: expected={expected_sha} observed={observed}")


def _load_targets(root: Path, source_result: dict[str, Any]) -> dict[int, pl.DataFrame]:
    targets: dict[int, pl.DataFrame] = {}
    storage = source_result.get("storage", {})
    for year in TARGET_YEARS:
        path = _find_one(root, f"catcher_framing_targets_{year}.parquet")
        expected = str(storage.get(f"targets_{year}", {}).get("sha256") or "")
        if not expected:
            raise RuntimeError(f"missing certified framing target hash {year}")
        _verify_file(path, expected, f"repaired framing target {year}")
        frame = pl.read_parquet(path)
        needed = {"target_year", "player_id", "target_z"}
        missing = sorted(needed - set(frame.columns))
        if missing:
            raise RuntimeError(f"repaired framing target {year} missing columns {missing}")
        if frame.is_empty():
            raise RuntimeError(f"empty repaired framing target {year}")
        years = {
            int(value)
            for value in frame.get_column("target_year").cast(pl.Int64, strict=False).drop_nulls().unique().to_list()
        }
        if years != {year}:
            raise RuntimeError(f"repaired framing target file {year} contains years={sorted(years)}")
        if frame.group_by("player_id").len().filter(pl.col("len") > 1).height:
            raise RuntimeError(f"duplicate repaired framing target player id {year}")
        if not frame.get_column("target_z").cast(pl.Float64, strict=False).is_finite().all():
            raise RuntimeError(f"nonfinite repaired framing target z {year}")
        targets[year] = frame.select(
            pl.col("player_id").cast(pl.Int64),
            pl.col("target_z").cast(pl.Float64),
        ).sort("player_id")
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-root", type=Path, required=True)
    parser.add_argument("--tracked-root", type=Path, required=True)
    parser.add_argument("--repaired-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repair_source = json.loads(REPAIR_SOURCE_RESULT.read_text())
    if repair_source.get("status") != "source_materialized_ready_for_repaired_framing_development":
        raise RuntimeError("repaired framing source is not certified")
    decision = repair_source.get("decision", {})
    boundary = repair_source.get("boundary", {})
    if decision.get("year_specific_source_certified") is not True:
        raise RuntimeError("repaired framing source did not certify year-specific targets")
    if decision.get("repaired_framing_development_authorized_next") is not True:
        raise RuntimeError("repaired framing development is not authorized")
    if boundary.get("2025_framing_target_accessed") is not False:
        raise RuntimeError("repaired framing source crossed 2025 boundary")
    if boundary.get("model_fit") is not False or boundary.get("model_scoring") is not False:
        raise RuntimeError("repaired framing source was not source-only")

    tracked_source = json.loads(TRACKED_SOURCE_RESULT.read_text())
    if tracked_source.get("decision", {}).get("tracked_source_materialized") is not True:
        raise RuntimeError("tracked framing predictor source is not certified")
    if tracked_source.get("boundary", {}).get("2025_source_accessed") is not False:
        raise RuntimeError("tracked framing predictor source crossed 2025 boundary")

    targets = _load_targets(args.repaired_source_root, repair_source)

    framing_path = _find_one(args.tracked_root, "tracked_framing_proxy_2021_2023.parquet")
    expected_tracked_sha = str(tracked_source.get("storage", {}).get("framing", {}).get("sha256") or "")
    if not expected_tracked_sha:
        raise RuntimeError("missing certified tracked framing artifact hash")
    _verify_file(framing_path, expected_tracked_sha, "tracked framing predictor")
    framing_frame = pl.read_parquet(framing_path)
    framing_z = _z_framing(framing_frame)
    if not framing_z:
        raise RuntimeError("no eligible tracked framing z values")

    _, historical_meta = _load_profiles(args.historical_root)
    catcher = historical_meta.pop("catcher")
    result = _evaluate_framing(catcher, targets, framing_z)

    tier_a = bool(result["tier_a_gate"]["passed"])
    tier_b = bool(result["tier_b_transfer"]["passed"])
    report = {
        "report_schema_version": "0.1",
        "gate": "defense_v1_framing_source_repair_development",
        "status": "repaired_framing_development_scored",
        "contract": str(REPAIR_CONTRACT),
        "source": {
            "repaired_target_source_run_id": repair_source.get("source_run_id"),
            "repaired_target_source_sha": repair_source.get("source_sha"),
            "repaired_target_combined_sha256": repair_source.get("storage", {}).get("all_targets", {}).get("sha256"),
            "tracked_source_run_id": tracked_source.get("source_run_id"),
            "tracked_source_sha": tracked_source.get("source_sha"),
            "tracked_framing_sha256": expected_tracked_sha,
            "historical_fielding_source_run_id": 32148467330,
            "eligible_tracked_framing_z_count": len(framing_z),
            **historical_meta,
        },
        "catcher_tracked_framing_repaired": result,
        "decision": {
            "tier_a_tracked_framing_passed": tier_a,
            "tier_b_tracked_framing_transfer_passed": tier_b,
            "mlb_framing_family_after_repair": "F1" if tier_a else "F0",
            "milb_tracked_framing_transfer_authorized": tier_b,
            "framing_repair_development_closed": True,
            "framing_parameter_freeze_authorized_next": tier_a,
            "2025_framing_confirmation_authorized": False,
            "additional_framing_development_challenger_authorized": False,
            "old_invalid_target_result_preserved_as_audit_history": True,
            "war_value_authorized": False,
        },
        "boundary": {
            "live_source_query_performed": False,
            "2025_defensive_targets_accessed": False,
            "tracked_framing_predictor_modified": False,
            "framing_feature_search_reopened": False,
            "regularization_reselected": False,
            "thresholds_changed": False,
            "catcher_throwing_modified": False,
            "catcher_blocking_modified": False,
            "general_range_modified": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "run_value_conversion_performed": False,
            "war_calculated": False,
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())