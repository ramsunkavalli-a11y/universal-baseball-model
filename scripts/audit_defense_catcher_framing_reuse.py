#!/usr/bin/env python3
"""Run the frozen catcher-framing reuse feasibility POC."""

from __future__ import annotations

from importlib.metadata import version
import json
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import requests

from sportsdataverse.mlb.mlb_catcher_framing import mlb_catcher_framing
from sportsdataverse.mlb.mlb_statcast import mlb_statcast_leaderboard_catcher_framing
from sportsdataverse.mlb.mlb_statcast_extra import mlb_statcast_search, mlb_statcast_search_minors


REPORT_ROOT = Path("reports/generated/defense-catcher-framing-reuse-poc")
PACKAGE_VERSION = "0.0.75"
MLB_START, MLB_END = "2024-06-01", "2024-06-30"
MILB_START, MILB_END = "2024-06-10", "2024-06-16"
SEASON = 2024
REQUIRED = [
    "description",
    "plate_x",
    "plate_z",
    "sz_top",
    "sz_bot",
    "stand",
    "balls",
    "strikes",
    "fielder_2",
]
_TAKES = ["called_strike", "ball"]


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _eligible_takes(frame: pl.DataFrame) -> pl.DataFrame:
    if frame.is_empty() or "description" not in frame.columns:
        return frame.head(0)
    needed_zone = [c for c in ("plate_x", "plate_z", "sz_top", "sz_bot") if c in frame.columns]
    if len(needed_zone) != 4:
        return frame.head(0)
    return frame.filter(
        pl.col("description").is_in(_TAKES)
        & pl.all_horizontal([pl.col(c).is_not_null() for c in needed_zone])
    )


def _framing_execution(label: str, frame: pl.DataFrame) -> dict[str, Any]:
    missing = [column for column in REQUIRED if column not in frame.columns]
    eligible = _eligible_takes(frame)
    fielder2_rate = (
        float(eligible.get_column("fielder_2").is_not_null().mean() or 0.0)
        if eligible.height and "fielder_2" in eligible.columns
        else 0.0
    )
    delta_run_exp_rate = (
        float(frame.get_column("delta_run_exp").is_not_null().mean() or 0.0)
        if frame.height and "delta_run_exp" in frame.columns
        else None
    )
    error: str | None = None
    if missing or eligible.is_empty():
        output = pl.DataFrame()
    else:
        try:
            output = mlb_catcher_framing(frame)
        except Exception as exc:  # persisted diagnostic; do not hide package failures
            output = pl.DataFrame()
            error = f"{type(exc).__name__}: {exc}"

    finite = bool(
        output.height
        and output.get_column("framing_runs").is_finite().all()
        and output.get_column("strikes_gained").is_finite().all()
    ) if output.height else False
    positive_take_catchers = (
        int(output.filter(pl.col("takes") > 0).height) if output.height else 0
    )
    total_output_takes = int(output.get_column("takes").sum() or 0) if output.height else 0
    passed = bool(
        not missing
        and eligible.height >= 1000
        and positive_take_catchers >= 10
        and finite
        and fielder2_rate >= 0.90
        and error is None
    )
    return {
        "label": label,
        "pitch_row_count": int(frame.height),
        "eligible_take_count": int(eligible.height),
        "fielder_2_non_null_rate_on_eligible_takes": fielder2_rate,
        "delta_run_exp_non_null_rate": delta_run_exp_rate,
        "required_columns_missing": missing,
        "framing_output_catcher_count": int(output.height),
        "positive_take_catcher_count": positive_take_catchers,
        "framing_output_total_takes": total_output_takes,
        "framing_output_finite": finite,
        "execution_error": error,
        "passed": passed,
    }


def _aaa_abbreviations() -> set[str]:
    response = requests.get(
        "https://statsapi.mlb.com/api/v1/teams",
        params={"sportId": 11, "season": SEASON},
        headers={"User-Agent": "universal-baseball-model-catcher-framing-poc/0.1"},
        timeout=60,
    )
    response.raise_for_status()
    out = {
        str(team.get("abbreviation") or "").strip()
        for team in (response.json().get("teams") or [])
        if str(team.get("abbreviation") or "").strip()
    }
    if len(out) < 20:
        raise RuntimeError(f"unexpectedly small AAA abbreviation set: {len(out)}")
    return out


def _mlb_oracle(pitches: pl.DataFrame) -> dict[str, Any]:
    error: str | None = None
    try:
        mine = mlb_catcher_framing(pitches).filter(pl.col("takes") >= 500)
        sav = mlb_statcast_leaderboard_catcher_framing(year=SEASON).with_columns(
            pl.col("id").cast(pl.Int64, strict=False).cast(pl.Utf8).alias("catcher_id"),
            pl.col("rv_tot").cast(pl.Float64, strict=False),
        )
        joined = mine.join(
            sav.select("catcher_id", "rv_tot"),
            on="catcher_id",
            how="inner",
        ).drop_nulls(["framing_runs", "rv_tot"])
        corr = _pearson(
            joined.get_column("framing_runs").to_numpy(),
            joined.get_column("rv_tot").to_numpy(),
        )
    except Exception as exc:
        mine = pl.DataFrame()
        sav = pl.DataFrame()
        joined = pl.DataFrame()
        corr = float("nan")
        error = f"{type(exc).__name__}: {exc}"
    passed = bool(
        error is None
        and joined.height >= 20
        and np.isfinite(corr)
        and corr >= 0.50
    )
    return {
        "minimum_takes_per_catcher": 500,
        "candidate_catcher_count": int(mine.height),
        "savant_row_count": int(sav.height),
        "matched_catcher_count": int(joined.height),
        "pearson_correlation": corr if np.isfinite(corr) else None,
        "frozen_minimum_correlation": 0.50,
        "execution_error": error,
        "passed": passed,
    }


def main() -> int:
    installed = version("sportsdataverse")
    if installed != PACKAGE_VERSION:
        raise RuntimeError(f"expected SportsDataverse {PACKAGE_VERSION}, observed {installed}")
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)

    print("Fetching MLB framing oracle month")
    mlb = mlb_statcast_search(MLB_START, MLB_END, season=SEASON, game_type="R")
    mlb_execution = _framing_execution("MLB", mlb)
    mlb_oracle = _mlb_oracle(mlb)

    print("Fetching tracked MiLB framing pool")
    pool = mlb_statcast_search_minors(
        MILB_START,
        MILB_END,
        season=SEASON,
        game_type="R",
        minors="true",
    )
    aaa_abbr = _aaa_abbreviations()
    if pool.height and "home_team" not in pool.columns:
        raise RuntimeError("tracked MiLB pool lacks home_team")
    if pool.height:
        pool = pool.with_columns(pl.col("home_team").cast(pl.Utf8).str.strip_chars())
        aaa = pool.filter(pl.col("home_team").is_in(sorted(aaa_abbr)))
        non_aaa = pool.filter(~pl.col("home_team").is_in(sorted(aaa_abbr)))
        non_aaa_teams = sorted(
            str(value) for value in non_aaa.get_column("home_team").drop_nulls().unique().to_list()
        )
    else:
        aaa = pl.DataFrame()
        non_aaa = pl.DataFrame()
        non_aaa_teams = []

    aaa_execution = _framing_execution("AAA", aaa)
    non_aaa_execution = _framing_execution("tracked_non_aaa", non_aaa)

    report = {
        "report_schema_version": "0.1",
        "gate": "defense_catcher_framing_reuse_poc",
        "contract": "docs/defense-catcher-framing-reuse-poc-contract.md",
        "upstream": {
            "package": "sportsdataverse",
            "package_version": installed,
            "function": "mlb_catcher_framing",
        },
        "mlb": {
            "source_window": {"start": MLB_START, "end": MLB_END, "season": SEASON},
            "execution": mlb_execution,
            "oracle": mlb_oracle,
        },
        "milb": {
            "source_window": {"start": MILB_START, "end": MILB_END, "season": SEASON},
            "transport": {"minors": "true", "server_level_filter": False},
            "pool_pitch_row_count": int(pool.height),
            "observed_non_aaa_home_teams": non_aaa_teams,
            "aaa": aaa_execution,
            "tracked_non_aaa": non_aaa_execution,
        },
        "decision": {
            "mlb_framing_reuse_candidate": bool(mlb_oracle["passed"]),
            "aaa_framing_execution_feasible": bool(aaa_execution["passed"]),
            "tracked_non_aaa_framing_execution_feasible": bool(non_aaa_execution["passed"]),
            "tracked_milb_framing_execution_feasible": bool(
                aaa_execution["passed"] and non_aaa_execution["passed"]
            ),
            "production_catcher_framing_authorized": False,
            "catcher_blocking_authorized": False,
            "catcher_throwing_authorized": False,
            "universal_defense_authorized": False,
            "war_value_authorized": False,
        },
        "boundary": {
            "defense_projection_fit": False,
            "playing_time_v1_modified": False,
            "position_role_v1_modified": False,
            "blocking_scored": False,
            "throwing_scored": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Catcher framing reuse POC",
        "",
        f"- MLB matched catchers: {mlb_oracle['matched_catcher_count']}",
        f"- MLB Pearson: {mlb_oracle['pearson_correlation']}",
        f"- MLB oracle passed: {mlb_oracle['passed']}",
        f"- AAA eligible takes: {aaa_execution['eligible_take_count']:,}",
        f"- AAA execution passed: {aaa_execution['passed']}",
        f"- tracked non-AAA eligible takes: {non_aaa_execution['eligible_take_count']:,}",
        f"- tracked non-AAA execution passed: {non_aaa_execution['passed']}",
        "- production catcher framing authorized: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
