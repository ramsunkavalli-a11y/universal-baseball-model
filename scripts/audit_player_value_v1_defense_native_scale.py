#!/usr/bin/env python3
"""Audit pre-2025 Defense target native scales for Player Value v1.

This script is diagnostic only. It reads the already-frozen Defense parameter
artifact, summarizes the raw target scales used in 2022-2024 development, and
produces candidate reference-scale diagnostics. It does not access 2025 data,
fit a model, select a run conversion, or calculate WAR.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import polars as pl

EXPECTED_PARAMETER_HASH = "sha256:cba6b7ebe4b2598db2c4d9ef360b0784f23a94ad61385f87149b08c46e0390d5"
EXPECTED_DEVELOPMENT_TARGET_SHA = "1c0a6361420c282db0a9e2c1400341be6cbd5305802422232cffae27a22eae61"
EXPECTED_FREEZE_RUN = 32198603779
DEVELOPMENT_YEARS = (2022, 2023, 2024)
GENERAL_POSITIONS = ("1B", "2B", "3B", "SS", "LF", "CF", "RF")


def _sha_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_one(root: Path, name: str) -> Path:
    matches = list(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one {name} under {root}; observed={matches}")
    return matches[0]


def _summary(frame: pl.DataFrame) -> dict[str, Any]:
    values = frame.get_column("target_raw").cast(pl.Float64)
    n = frame.height
    if n < 2:
        raise RuntimeError("target-scale cell has fewer than two rows")
    mean = float(values.mean())
    sd = float(values.std(ddof=0))
    if not math.isfinite(sd) or sd <= 1e-12:
        raise RuntimeError(f"degenerate target-scale cell n={n} mean={mean} sd={sd}")
    return {
        "count": int(n),
        "mean": mean,
        "population_sd": sd,
        "min": float(values.min()),
        "median": float(values.median()),
        "max": float(values.max()),
        "q10": float(values.quantile(0.10, interpolation="linear")),
        "q90": float(values.quantile(0.90, interpolation="linear")),
    }


def _stability(sds: list[float]) -> dict[str, Any]:
    if not sds or any(not math.isfinite(value) or value <= 0 for value in sds):
        raise RuntimeError(f"invalid SD list: {sds}")
    mean_sd = sum(sds) / len(sds)
    variance = sum((value - mean_sd) ** 2 for value in sds) / len(sds)
    sd_of_sds = math.sqrt(variance)
    return {
        "yearly_population_sds": sds,
        "mean_yearly_sd": mean_sd,
        "median_yearly_sd": float(median(sds)),
        "min_yearly_sd": min(sds),
        "max_yearly_sd": max(sds),
        "max_to_min_ratio": max(sds) / min(sds),
        "coefficient_of_variation": sd_of_sds / mean_sd if mean_sd > 0 else None,
        "diagnostic_candidate_reference_sd": float(median(sds)),
        "candidate_status": "diagnostic_only_not_frozen",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--freeze-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()

    report_path = _find_one(args.freeze_root, "report.json")
    targets_path = _find_one(args.freeze_root, "development_targets.parquet")
    freeze = json.loads(report_path.read_text(encoding="utf-8"))

    if int(freeze.get("freeze_run_id")) != EXPECTED_FREEZE_RUN:
        raise RuntimeError(f"unexpected freeze run {freeze.get('freeze_run_id')}")
    if freeze.get("parameter_hash") != EXPECTED_PARAMETER_HASH:
        raise RuntimeError(f"unexpected parameter hash {freeze.get('parameter_hash')}")
    expected_from_report = freeze.get("storage", {}).get("development_targets", {}).get("sha256")
    actual_target_sha = _sha_file(targets_path)
    if expected_from_report != EXPECTED_DEVELOPMENT_TARGET_SHA:
        raise RuntimeError(f"freeze report development-target SHA changed: {expected_from_report}")
    if actual_target_sha != EXPECTED_DEVELOPMENT_TARGET_SHA:
        raise RuntimeError(f"development-target parquet SHA mismatch: {actual_target_sha}")
    boundary = freeze.get("boundary", {})
    if boundary.get("2025_defensive_targets_accessed") is not False:
        raise RuntimeError("freeze artifact crossed the 2025 target boundary")

    targets = pl.read_parquet(targets_path)
    required = {"component", "target_year", "player_id", "position", "target_raw", "target_z"}
    missing = sorted(required - set(targets.columns))
    if missing:
        raise RuntimeError(f"development targets missing columns: {missing}")
    years = sorted(int(v) for v in targets.get_column("target_year").unique().to_list())
    if years != list(DEVELOPMENT_YEARS):
        raise RuntimeError(f"unexpected development target years: {years}")
    if targets.filter(pl.col("target_raw").is_null() | ~pl.col("target_raw").is_finite()).height:
        raise RuntimeError("nonfinite raw development target")

    general = targets.filter(pl.col("component") == "general_range")
    throwing = targets.filter(pl.col("component") == "catcher_throwing")

    general_by_year_position: dict[str, dict[str, Any]] = {}
    general_stability: dict[str, dict[str, Any]] = {}
    for position in GENERAL_POSITIONS:
        yearly_sds: list[float] = []
        for year in DEVELOPMENT_YEARS:
            cell = general.filter((pl.col("target_year") == year) & (pl.col("position") == position))
            summary = _summary(cell)
            general_by_year_position[f"{year}:{position}"] = summary
            yearly_sds.append(float(summary["population_sd"]))
        general_stability[position] = _stability(yearly_sds)

    throwing_by_year: dict[str, Any] = {}
    throwing_sds: list[float] = []
    for year in DEVELOPMENT_YEARS:
        cell = throwing.filter(pl.col("target_year") == year)
        summary = _summary(cell)
        throwing_by_year[str(year)] = summary
        throwing_sds.append(float(summary["population_sd"]))
    throwing_stability = _stability(throwing_sds)

    result = {
        "report_schema_version": "0.1",
        "gate": "player_value_v1_defense_native_scale_audit",
        "status": "diagnostic_complete_no_scale_frozen",
        "architecture_contract": "docs/player-value-v1-architecture-contract.md",
        "source": {
            "defense_parameter_freeze_run_id": EXPECTED_FREEZE_RUN,
            "parameter_hash": EXPECTED_PARAMETER_HASH,
            "development_targets_sha256": actual_target_sha,
            "development_target_years": list(DEVELOPMENT_YEARS),
            "2025_data_used": False,
        },
        "general_range": {
            "native_target": "Savant diff_success_rate_formatted / Success Rate Added",
            "raw_unit_note": "raw numeric source scale preserved by frozen development target materialization; interpret exact display units from the source contract before final conversion",
            "by_year_position": general_by_year_position,
            "pre_2025_scale_stability": general_stability,
            "candidate_reference_rule": "median of 2022-2024 position-specific population SDs",
            "candidate_rule_status": "diagnostic_only_not_selected",
        },
        "catcher_throwing": {
            "native_target": "Savant cs_aa_per_throw",
            "by_year": throwing_by_year,
            "pre_2025_scale_stability": throwing_stability,
            "candidate_reference_rule": "median of 2022-2024 population SDs",
            "candidate_rule_status": "diagnostic_only_not_selected",
        },
        "decision": {
            "native_scale_audit_complete": True,
            "defense_run_conversion_frozen": False,
            "defensive_exposure_mapping_frozen": False,
            "positional_adjustment_frozen": False,
            "replacement_level_frozen": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "2025_defense_confirmation_targets_accessed": False,
            "2025_confirmation_residuals_used_for_scaling": False,
            "model_fit": False,
            "upstream_model_modified": False,
            "run_conversion_selected": False,
            "war_calculated": False,
        },
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Player Value v1 Defense native-scale audit",
        "",
        "Status: **DIAGNOSTIC COMPLETE — NO RUN SCALE FROZEN.**",
        "",
        f"Source: frozen Defense parameter artifact run `{EXPECTED_FREEZE_RUN}`; 2025 data used: **no**.",
        "",
        "## General range — pre-2025 raw target SD by position",
        "",
        "| Position | 2022 SD | 2023 SD | 2024 SD | Median SD | Max/min | CV |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for position in GENERAL_POSITIONS:
        stats = general_stability[position]
        sds = stats["yearly_population_sds"]
        lines.append(
            f"| {position} | {sds[0]:.6f} | {sds[1]:.6f} | {sds[2]:.6f} | "
            f"{stats['median_yearly_sd']:.6f} | {stats['max_to_min_ratio']:.3f} | "
            f"{stats['coefficient_of_variation']:.3f} |"
        )
    lines.extend([
        "",
        "## Catcher throwing — pre-2025 raw target scale",
        "",
        "| Year | n | Mean | Population SD |",
        "|---|---:|---:|---:|",
    ])
    for year in DEVELOPMENT_YEARS:
        stats = throwing_by_year[str(year)]
        lines.append(f"| {year} | {stats['count']} | {stats['mean']:.6f} | {stats['population_sd']:.6f} |")
    lines.extend([
        "",
        f"Diagnostic median throwing SD: `{throwing_stability['median_yearly_sd']:.6f}`.",
        "",
        "## Interpretation boundary",
        "",
        "The median-year SD rules above are diagnostics only. This audit does not select a conversion, does not use 2025 confirmation residuals, and does not calculate defensive runs or WAR.",
        "",
    ])
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "general_positions": len(general_stability),
        "throwing_years": len(throwing_by_year),
        "output_json": str(args.output_json),
        "output_md": str(args.output_md),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
