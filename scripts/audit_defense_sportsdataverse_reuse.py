#!/usr/bin/env python3
"""Run the frozen SportsDataverse defensive-range reuse feasibility POC.

This script executes an upstream public implementation for source/reuse
validation only. It does not promote a production defense model.
"""

from __future__ import annotations

from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from sportsdataverse.mlb.mlb_fielding_oaa import mlb_fielding_oaa
from sportsdataverse.mlb.mlb_statcast import mlb_statcast_leaderboard_outs_above_average
from sportsdataverse.mlb.mlb_statcast_extra import (
    mlb_statcast_search,
    mlb_statcast_search_minors,
)


REPORT_ROOT = Path("reports/generated/defense-sportsdataverse-reuse-poc")
PACKAGE_VERSION = "0.0.75"
UPSTREAM_COMMIT = "1dafadb38c5240d8e29a0f818efbabe04cd6c417"
MLB_START = "2024-06-01"
MLB_END = "2024-06-30"
MILB_START = "2024-06-10"
MILB_END = "2024-06-16"
REQUIRED_TRAJECTORY_COLUMNS = [
    "hc_x",
    "hc_y",
    "hit_distance_sc",
    "launch_angle",
    "launch_speed",
    "hit_location",
    "events",
]
REQUIRED_FIELDER_COLUMNS = [f"fielder_{i}" for i in range(2, 10)]
REQUIRED_BIP_COLUMNS = REQUIRED_TRAJECTORY_COLUMNS + REQUIRED_FIELDER_COLUMNS
COVERAGE_COLUMNS = REQUIRED_TRAJECTORY_COLUMNS + [f"fielder_{i}" for i in range(1, 10)]


def _bip(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.is_empty():
        return frame
    if "type" in frame.columns:
        return frame.filter(pl.col("type") == "X")
    if "description" in frame.columns:
        return frame.filter(pl.col("description").str.contains("(?i)hit_into_play"))
    return frame.filter(pl.col("events").is_not_null()) if "events" in frame.columns else frame.head(0)


def _field_coverage(frame: pl.DataFrame) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for column in COVERAGE_COLUMNS:
        if column not in frame.columns or frame.height == 0:
            out[column] = None
        else:
            out[column] = float(frame.get_column(column).is_not_null().mean() or 0.0)
    return out


def _empty_oaa() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "fielder_id": pl.Utf8,
            "position": pl.Int64,
            "opportunities": pl.Int64,
            "oaa": pl.Float64,
        }
    )


def _oaa_summary(label: str, pitches: pl.DataFrame) -> tuple[dict[str, Any], pl.DataFrame]:
    bip = _bip(pitches)
    missing = [column for column in REQUIRED_BIP_COLUMNS if column not in bip.columns]
    coverage = _field_coverage(bip)

    oaa = _empty_oaa() if missing or bip.is_empty() else mlb_fielding_oaa(bip)

    opportunities = int(oaa.get_column("opportunities").sum() or 0) if not oaa.is_empty() else 0
    usable_rate = float(opportunities / bip.height) if bip.height else 0.0
    by_position = (
        oaa.group_by("position")
        .agg(
            pl.col("opportunities").sum().alias("opportunities"),
            pl.col("fielder_id").n_unique().alias("fielder_count"),
        )
        .sort("position")
        .to_dicts()
        if not oaa.is_empty()
        else []
    )
    report = {
        "label": label,
        "pitch_row_count": int(pitches.height),
        "column_count": len(pitches.columns),
        "bip_row_count": int(bip.height),
        "required_columns_missing": missing,
        "optional_fielder_1_present": "fielder_1" in bip.columns,
        "required_field_non_null_rate": coverage,
        "oaa_row_count": int(oaa.height),
        "oaa_total_opportunities": opportunities,
        "oaa_bip_usable_rate": usable_rate,
        "oaa_by_position": by_position,
    }
    return report, oaa


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _mlb_oracle(oaa: pl.DataFrame) -> dict[str, Any]:
    savant = mlb_statcast_leaderboard_outs_above_average(year=2024)
    required = {"player_id", "outs_above_average"}
    missing = sorted(required - set(savant.columns))
    if missing or oaa.is_empty():
        return {
            "savant_row_count": int(savant.height),
            "savant_columns_missing": missing,
            "matched_fielder_count": 0,
            "pearson_correlation": None,
            "frozen_minimum_correlation": 0.30,
            "passed": False,
        }

    mine = oaa.group_by("fielder_id").agg(
        pl.col("oaa").sum().alias("oaa"),
        pl.col("opportunities").sum().alias("opportunities"),
    )
    savant = savant.with_columns(
        pl.col("player_id").cast(pl.Int64, strict=False).cast(pl.Utf8).alias("fielder_id"),
        pl.col("outs_above_average").cast(pl.Float64, strict=False),
    )
    joined = mine.join(
        savant.select("fielder_id", "outs_above_average"),
        on="fielder_id",
        how="inner",
    ).drop_nulls(["oaa", "outs_above_average"])
    corr = _pearson(
        joined.get_column("oaa").to_numpy(),
        joined.get_column("outs_above_average").to_numpy(),
    )
    passed = bool(joined.height >= 50 and np.isfinite(corr) and corr >= 0.30)
    return {
        "savant_row_count": int(savant.height),
        "savant_columns_missing": [],
        "matched_fielder_count": int(joined.height),
        "pearson_correlation": corr if np.isfinite(corr) else None,
        "frozen_minimum_correlation": 0.30,
        "passed": passed,
    }


def _milb_pass(report: dict[str, Any]) -> bool:
    return bool(
        not report["required_columns_missing"]
        and report["bip_row_count"] >= 100
        and report["oaa_total_opportunities"] >= 100
        and report["oaa_bip_usable_rate"] >= 0.50
    )


def _fetch_milb_level(label: str, candidates: tuple[str, ...]) -> tuple[pl.DataFrame, list[dict[str, Any]], str | None]:
    attempts: list[dict[str, Any]] = []
    for level_filter in candidates:
        print(f"Fetching MiLB Statcast {label} with hfLevel={level_filter!r} {MILB_START}..{MILB_END}")
        pitches = mlb_statcast_search_minors(
            MILB_START,
            MILB_END,
            game_type="R",
            hfLevel=level_filter,
        )
        attempts.append(
            {
                "hfLevel": level_filter,
                "pitch_row_count": int(pitches.height),
                "column_count": len(pitches.columns),
            }
        )
        if pitches.height:
            return pitches, attempts, level_filter
    return pl.DataFrame(), attempts, None


def main() -> int:
    installed_version = version("sportsdataverse")
    if installed_version != PACKAGE_VERSION:
        raise RuntimeError(
            f"SportsDataverse version mismatch: expected {PACKAGE_VERSION}, observed {installed_version}"
        )

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"Fetching MLB Statcast {MLB_START}..{MLB_END}")
    mlb_pitches = mlb_statcast_search(
        MLB_START,
        MLB_END,
        season=2024,
        game_type="R",
    )
    mlb_report, mlb_oaa = _oaa_summary("MLB", mlb_pitches)
    oracle = _mlb_oracle(mlb_oaa)
    mlb_report["oracle"] = oracle
    mlb_passed = bool(
        not mlb_report["required_columns_missing"]
        and mlb_report["bip_row_count"] > 0
        and oracle["passed"]
    )

    milb_reports: list[dict[str, Any]] = []
    for label, candidates in (("AAA", ("AAA|", "AAA")), ("A", ("A|", "A"))):
        pitches, attempts, selected = _fetch_milb_level(label, candidates)
        level_report, _ = _oaa_summary(label, pitches)
        level_report["hfLevel_attempts"] = attempts
        level_report["hfLevel_selected"] = selected
        level_report["passed"] = _milb_pass(level_report)
        milb_reports.append(level_report)

    aaa_passed = next(row["passed"] for row in milb_reports if row["label"] == "AAA")
    a_passed = next(row["passed"] for row in milb_reports if row["label"] == "A")

    report = {
        "report_schema_version": "0.2",
        "gate": "defense_sportsdataverse_reuse_feasibility_poc",
        "contract": "docs/defense-sportsdataverse-reuse-poc-contract.md",
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed_version,
            "inspected_commit": UPSTREAM_COMMIT,
        },
        "source_windows": {
            "mlb": {"start": MLB_START, "end": MLB_END, "season": 2024, "game_type": "R"},
            "milb": {"start": MILB_START, "end": MILB_END, "game_type": "R"},
        },
        "mlb": mlb_report,
        "milb": milb_reports,
        "decision": {
            "mlb_oaa_reuse_candidate": mlb_passed,
            "aaa_tracked_oaa_reuse_feasible": aaa_passed,
            "single_a_tracked_oaa_reuse_feasible": a_passed,
            "tracked_milb_oaa_reuse_feasible_for_tested_tiers": bool(aaa_passed and a_passed),
            "universal_defense_authorized": False,
            "catcher_defense_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "production_defense_model_fit": False,
            "defense_projection_fit": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "team_allocator_fit": False,
            "war_value_computed": False,
        },
    }

    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# SportsDataverse defense reuse POC",
        "",
        f"- SportsDataverse: {installed_version}",
        f"- MLB June BIP: {mlb_report['bip_row_count']:,}",
        f"- MLB OAA/Savant matched fielders: {oracle['matched_fielder_count']:,}",
        f"- MLB OAA/Savant Pearson: {oracle['pearson_correlation']}",
        f"- MLB reuse gate passed: {mlb_passed}",
    ]
    for row in milb_reports:
        lines.extend(
            [
                f"- {row['label']} selected hfLevel: {row['hfLevel_selected']}",
                f"- {row['label']} BIP: {row['bip_row_count']:,}",
                f"- {row['label']} OAA opportunities: {row['oaa_total_opportunities']:,}",
                f"- {row['label']} usable rate: {row['oaa_bip_usable_rate']:.3f}",
                f"- {row['label']} execution/coverage gate passed: {row['passed']}",
            ]
        )
    lines.extend(
        [
            "- Universal defense authorized: False",
            "- WAR/value authorized: False",
            "",
        ]
    )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
