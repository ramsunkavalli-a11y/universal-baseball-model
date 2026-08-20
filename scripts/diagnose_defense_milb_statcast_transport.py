#!/usr/bin/env python3
"""Diagnose MiLB Statcast transport while reusing SportsDataverse OAA."""

from __future__ import annotations

from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

import polars as pl
import requests

from sportsdataverse.mlb.mlb_fielding_oaa import mlb_fielding_oaa
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search_minors


REPORT_ROOT = Path("reports/generated/defense-milb-statcast-transport-diagnostic")
START = "2024-06-10"
END = "2024-06-16"
SEASON = 2024
PACKAGE_VERSION = "0.0.75"
AAA_TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams"
REQUIRED = [
    "hc_x",
    "hc_y",
    "hit_distance_sc",
    "launch_angle",
    "launch_speed",
    "hit_location",
    "events",
] + [f"fielder_{i}" for i in range(2, 10)]


def _bip(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.is_empty():
        return frame
    if "type" in frame.columns:
        return frame.filter(pl.col("type") == "X")
    return frame.filter(pl.col("events").is_not_null()) if "events" in frame.columns else frame.head(0)


def _aaa_abbreviations() -> set[str]:
    response = requests.get(
        AAA_TEAMS_URL,
        params={"sportId": 11, "season": SEASON},
        headers={"User-Agent": "universal-baseball-model-defense-transport-poc/0.1"},
        timeout=60,
    )
    response.raise_for_status()
    teams = response.json().get("teams") or []
    out = {
        str(team.get("abbreviation") or "").strip()
        for team in teams
        if str(team.get("abbreviation") or "").strip()
    }
    if len(out) < 20:
        raise RuntimeError(f"unexpectedly small AAA abbreviation set: {len(out)}")
    return out


def _slice_report(label: str, frame: pl.DataFrame) -> dict[str, Any]:
    bip = _bip(frame)
    missing = [column for column in REQUIRED if column not in bip.columns]
    coverage = {
        column: (
            float(bip.get_column(column).is_not_null().mean() or 0.0)
            if column in bip.columns and bip.height
            else None
        )
        for column in REQUIRED
    }
    if missing or bip.is_empty():
        opportunities = 0
        oaa_rows = 0
        by_position: list[dict[str, Any]] = []
    else:
        oaa = mlb_fielding_oaa(bip)
        opportunities = int(oaa.get_column("opportunities").sum() or 0) if oaa.height else 0
        oaa_rows = int(oaa.height)
        by_position = (
            oaa.group_by("position")
            .agg(
                pl.col("opportunities").sum().alias("opportunities"),
                pl.col("fielder_id").n_unique().alias("fielder_count"),
            )
            .sort("position")
            .to_dicts()
            if oaa.height
            else []
        )
    usable_rate = float(opportunities / bip.height) if bip.height else 0.0
    passed = bool(
        not missing
        and bip.height >= 100
        and opportunities >= 100
        and usable_rate >= 0.50
    )
    return {
        "label": label,
        "pitch_row_count": int(frame.height),
        "bip_row_count": int(bip.height),
        "required_columns_missing": missing,
        "required_field_non_null_rate": coverage,
        "oaa_row_count": oaa_rows,
        "oaa_total_opportunities": opportunities,
        "oaa_bip_usable_rate": usable_rate,
        "oaa_by_position": by_position,
        "passed": passed,
    }


def main() -> int:
    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected SportsDataverse {PACKAGE_VERSION}, observed {installed}")

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"Fetching tracked MiLB pool {START}..{END} with minors=true")
    pool = mlb_statcast_search_minors(
        START,
        END,
        season=SEASON,
        game_type="R",
        minors="true",
    )

    aaa_abbr = _aaa_abbreviations()
    if pool.height and "home_team" not in pool.columns:
        raise RuntimeError("MiLB tracked pool lacks home_team; client-side level split impossible")

    if pool.height:
        pool = pool.with_columns(pl.col("home_team").cast(pl.Utf8).str.strip_chars())
        aaa = pool.filter(pl.col("home_team").is_in(sorted(aaa_abbr)))
        non_aaa = pool.filter(~pl.col("home_team").is_in(sorted(aaa_abbr)))
        observed_home_teams = sorted(
            str(value) for value in pool.get_column("home_team").drop_nulls().unique().to_list()
        )
        observed_non_aaa_home_teams = sorted(
            str(value) for value in non_aaa.get_column("home_team").drop_nulls().unique().to_list()
        )
    else:
        aaa = pl.DataFrame()
        non_aaa = pl.DataFrame()
        observed_home_teams = []
        observed_non_aaa_home_teams = []

    aaa_report = _slice_report("AAA", aaa)
    non_aaa_report = _slice_report("tracked_non_aaa", non_aaa)

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_milb_statcast_transport_diagnostic",
        "contract": "docs/defense-milb-statcast-transport-diagnostic-contract.md",
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "transport_function": "mlb_statcast_search_minors",
            "raw_extra_parameter": {"minors": "true"},
            "oaa_function": "mlb_fielding_oaa",
        },
        "source": {
            "start": START,
            "end": END,
            "season": SEASON,
            "game_type": "R",
            "pool_pitch_row_count": int(pool.height),
            "pool_column_count": len(pool.columns),
            "observed_home_teams": observed_home_teams,
            "official_aaa_abbreviation_count": len(aaa_abbr),
            "observed_non_aaa_home_teams": observed_non_aaa_home_teams,
        },
        "slices": [aaa_report, non_aaa_report],
        "decision": {
            "minors_true_transport_returned_rows": bool(pool.height),
            "aaa_tracked_oaa_execution_feasible": bool(aaa_report["passed"]),
            "tracked_non_aaa_oaa_execution_feasible": bool(non_aaa_report["passed"]),
            "sportsdataverse_oaa_reusable_on_tested_milb_tracking": bool(
                aaa_report["passed"] and non_aaa_report["passed"]
            ),
            "universal_defense_authorized": False,
            "defense_projection_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "production_defense_model_fit": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "untracked_levels_imputed": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# MiLB Statcast transport diagnostic",
        "",
        f"- tracked pool pitches: {pool.height:,}",
        f"- observed home teams: {len(observed_home_teams)}",
        f"- AAA pitches: {aaa_report['pitch_row_count']:,}",
        f"- AAA BIP/OAA opps: {aaa_report['bip_row_count']:,}/{aaa_report['oaa_total_opportunities']:,}",
        f"- AAA gate: {aaa_report['passed']}",
        f"- non-AAA tracked pitches: {non_aaa_report['pitch_row_count']:,}",
        f"- non-AAA BIP/OAA opps: {non_aaa_report['bip_row_count']:,}/{non_aaa_report['oaa_total_opportunities']:,}",
        f"- non-AAA gate: {non_aaa_report['passed']}",
        "- universal defense authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
