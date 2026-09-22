"""Certify the existing hitter history and version calendar-value targets."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.multiyear_hitter_value import (
    calendar_targets, prepare_features, attach_outcomes,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


DEFAULT_SOURCE = Path(
    "C:/Users/ramav/Documents/Codex/2026-09-07/new-chat-4/work/"
    "universal-baseball-model/reports/generated"
)


def completed_schedule(payload: dict, year: int) -> tuple[int, int]:
    """Final abstract state also includes cancellations; require completed code F."""
    games = {}
    for day in payload["dates"]:
        if not day["date"].startswith(str(year)):
            raise ValueError("Schedule returned another season")
        for game in day["games"]:
            if game["gameType"] == "R" and game["status"].get("codedGameState") == "F":
                games[game["gamePk"]] = game
    teams = {g["teams"][s]["team"]["id"] for g in games.values() for s in ("home", "away")}
    return len(games), len(teams)


def schedule_capture(year: int, output: Path) -> dict:
    if not 2009 <= year <= 2025:
        raise ValueError("Only completed historical schedules allowed")
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"schedule-{year}-completed.json"
    if not path.exists():
        response = requests.get("https://statsapi.mlb.com/api/v1/schedule", params={
            "sportId": 1, "season": year, "gameType": "R",
            "fields": "dates,date,games,gamePk,gameType,status,abstractGameState,codedGameState,detailedState,teams,home,away,team,id",
        }, timeout=90)
        response.raise_for_status()
        payload = response.json()
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    payload = json.loads(path.read_text(encoding="utf-8"))
    games, teams = completed_schedule(payload, year)
    if teams != 30 or not (850 if year == 2020 else 2300) <= games <= 2450:
        raise ValueError(f"Implausible completed schedule for {year}: {games}")
    return {"season": year, "completed_games": games, "teams": teams,
            "source": path.as_posix(), "sha256": sha256_file(path)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=Path("reports/generated/multiyear-hitter-v1"))
    args = parser.parse_args()
    sources = []

    def read(relative: str, *, years=None, season_col="season") -> pl.DataFrame:
        path = args.source_root / relative
        frame = pl.scan_parquet(path)
        if season_col in frame.collect_schema():
            frame = frame.filter(pl.col(season_col) <= 2025)
            if years is not None:
                frame = frame.filter(pl.col(season_col).is_in(years))
        result = frame.collect()
        sources.append({"path": path.as_posix(), "sha256": sha256_file(path),
                        "rows_used": result.height, "year_filter": list(years) if years else "through_2025"})
        return result

    snapshots = pl.concat([
        read("opportunity-history-sources-pre2020/tables/hitter_snapshots.parquet", season_col="snapshot_year"),
        read("opportunity-history-sources-v2/tables/hitter_snapshots.parquet", season_col="snapshot_year"),
    ]).sort("snapshot_year", "player_id")
    stats = pl.concat([
        read("affiliated-skill-source-2003-2007/tables/affiliated_hitting_components.parquet", years=[2007]),
        read("affiliated-skill-source-2008-2017/tables/affiliated_hitting_components.parquet"),
        read("affiliated-skill-source-2018-2022/tables/affiliated_hitting_components.parquet", years=[2018, 2019, 2020, 2021, 2022]),
        read("affiliated-skill-source/tables/affiliated_hitting_components.parquet", years=[2023, 2024, 2025]),
    ], how="vertical_relaxed")
    keys = ["season", "player_id", "sport_id", "team_id"]
    if stats.unique(keys).height != stats.height:
        raise ValueError("Overlapping affiliated source rows")
    membership = pl.concat([
        read("opportunity-40man-pre2020/tables/historical_40man_membership.parquet"),
        read("opportunity-40man-history/tables/historical_40man_membership.parquet"),
    ], how="diagonal_relaxed")
    if membership.group_by("season", "player_id").agg(pl.col("on_40man").n_unique().alias("n")).filter(pl.col("n") > 1).height:
        raise ValueError("Conflicting historical membership flags")
    if membership.filter(pl.col("as_of_date").dt.year() > pl.col("season")).height:
        raise ValueError("Membership capture extends beyond origin cutoff")
    membership = membership.unique(["season", "player_id"])
    batting = read("career-mlb-outcome-inventory-2009-2025/tables/mlb_hitting_components_2009_2025.parquet")
    pitching = read("career-mlb-outcome-inventory-2009-2025/tables/mlb_pitching_2009_2025.parquet")
    old_report_path = args.source_root / "career-mlb-outcome-inventory-2009-2025/report.json"
    old_report = json.loads(old_report_path.read_text(encoding="utf-8"))
    complete = list(range(2009, 2026))
    if old_report["complete_seasons"] != complete:
        raise ValueError("MLB source does not certify all completed seasons")
    # The source's simple sum excludes interference/other rare PA and records
    # sum(AB, BB, HBP, SH, SF) - PA; negative residuals are declared other PA.
    if batting.filter(pl.col("simple_pa_accounting_residual") > 0).height:
        raise ValueError("MLB component counts exceed plate appearances")
    if batting.unique(["season", "player_id"]).height != batting.height:
        raise ValueError("MLB source player-season duplicates")
    totals = batting.group_by("season").agg(pl.col("batting_plate_appearances").sum().alias("pa"))
    totals = totals.join(pitching.group_by("season").agg(pl.col("pitching_bf").sum().alias("bf")), on="season")
    if totals.filter(pl.col("pa") != pl.col("bf")).height:
        raise ValueError(f"League PA/BF conservation fails: {totals.to_dicts()}")
    with ThreadPoolExecutor(max_workers=4) as executor:
        schedules = list(executor.map(lambda y: schedule_capture(y, args.output / "raw"), complete))
    schedule_table = pl.DataFrame(schedules).select("season", "completed_games", "teams")
    targets = calendar_targets(batting, schedule_table)
    features, base_cols, full_cols = prepare_features(snapshots, stats, targets, membership)
    panel = attach_outcomes(features, targets)
    # Display names are from that origin's own history only. Never use current teams as historical inputs.
    names = stats.sort("plate_appearances", descending=True).unique(["season", "player_id"], keep="first").select(
        pl.col("season").alias("origin_year"), "player_id", "player_name", "team_id"
    )
    panel = panel.join(names, on=["origin_year", "player_id"], how="left", validate="1:1")
    artifacts = {}
    for name, frame in (("panel", panel), ("targets", targets), ("schedules", schedule_table)):
        artifacts[name] = write_canonical_parquet(frame, args.output / f"{name}.parquet",
                                                table_name=f"multiyear_hitter_v1_{name}").as_record()
    coverage = panel.group_by("origin_year").agg(
        pl.len().alias("players"), pl.col("age_missing").sum().alias("missing_age"),
        pl.col("missing_lag0").sum().alias("no_current_components"),
        pl.col("on_40man").sum().alias("listed_on_40man"),
        pl.col("war_h1").is_not_null().sum().alias("observed_h1"),
        pl.col("war_c3").is_not_null().sum().alias("observed_c3"),
    ).sort("origin_year")
    report = {
        "status": "m1_calendar_target_and_cohort_certification",
        "generated_at": datetime.now(UTC).isoformat(), "sources": sources,
        "source_certification_report": {"path": old_report_path.as_posix(), "sha256": sha256_file(old_report_path)},
        "schedule_captures": schedules, "league_pa_bf": totals.sort("season").to_dicts(),
        "simple_pa_residuals": batting.group_by("simple_pa_accounting_residual").len().sort("simple_pa_accounting_residual").to_dicts(),
        "annual_target_totals": targets.group_by("season").agg(pl.col("component_war").sum(),
            pl.col("legacy_component_war").sum(), pl.col("schedule_fraction").first()).sort("season").to_dicts(),
        "coverage": coverage.to_dicts(), "base_features": base_cols, "full_features": full_cols,
        "artifacts": artifacts, "outcome_max": 2025, "protected_outcomes_used": False,
        "target": "calendar_batting_plus_replacement_v1",
        "availability": "reconstructed Dec-31 end-of-season vintage; historical season aggregates, not archived publication vintages",
        "scope": "existing historical roster/stat-union hitter snapshots; does not certify all reserve rights",
        "membership": "October-15 reconstructed 40-man lists; absent IDs treated as not listed, matching existing opportunity contract, not missing season coverage",
        "limitations": ["No 2020 origin; canceled MiLB season remains a missing lag.",
            "Current published whole-WAR label files not located in recovered sources; public WAR comparison unavailable.",
            "Position, baserunning and defense are absent from the common long-history target.",
            "Original season source certification reused; complete schedule and MLB PA/BF conservation independently checked."],
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"coverage": report["coverage"], "features": len(full_cols),
                      "2020": [r for r in report["annual_target_totals"] if r["season"] == 2020]}, indent=2))


if __name__ == "__main__":
    main()
