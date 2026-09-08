#!/usr/bin/env python
"""Run one repeatable StatsAPI team-control source audit."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.control_events import (
    classify_control_transactions,
    materialize_control_stints,
)
from universal_baseball.control_season_source import fetch_season_windows
from universal_baseball.people_control_source import fetch_people_control_evidence
from universal_baseball.playing_time_roster_source import (
    fetch_mlb_teams,
    fetch_team_full_roster_candidates_as_of,
)
from universal_baseball.roster_entry_source import build_opening_control_states
from universal_baseball.team_control import calculate_control_years


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--team-id", type=int, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, required=True)
    parser.add_argument("--report-dir", type=Path, default=Path("reports/generated/team-control"))
    parser.add_argument("--capture-dir", type=Path, default=Path("data/quarantine/team-control"))
    return parser.parse_args()


def _capture(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )


def main() -> int:
    args = parse_args()
    roster, roster_capture = fetch_team_full_roster_candidates_as_of(
        args.team_id, season=args.season, as_of_date=args.as_of
    )
    teams, teams_capture = fetch_mlb_teams(args.season)
    windows, season_captures = fetch_season_windows([args.season])
    people = fetch_people_control_evidence(
        roster.get_column("player_id"), as_of_date=args.as_of
    )
    mlb_team_ids = set(teams.get_column("team_id").to_list())
    openings = build_opening_control_states(
        people.roster_entries, windows, mlb_team_ids=mlb_team_ids
    )
    events = classify_control_transactions(
        people.transactions, mlb_team_ids=mlb_team_ids
    ).filter(pl.col("season") == args.season)
    materialized = materialize_control_stints(
        openings.opening_states, events, windows, as_of_date=args.as_of
    )
    years = calculate_control_years(
        materialized.stints, windows, as_of_date=args.as_of
    )
    review_details = materialized.review_events.join(
        people.transactions.select(
            "transaction_id", "type_code", "type_description", "description"
        ),
        on=["player_id", "transaction_id"],
    )
    report = {
        "report_schema_version": 1,
        "team_id": args.team_id,
        "season": args.season,
        "as_of_date": args.as_of.isoformat(),
        "candidate_players": roster.height,
        "people_returned": people.people.height,
        "roster_entries": people.roster_entries.height,
        "transactions": people.transactions.height,
        "opening_states": openings.opening_states.height,
        "opening_review_players": openings.review_players.height,
        "season_events": events.height,
        "transaction_review_events": materialized.review_events.height,
        "transaction_review_rate": materialized.review_events.height / events.height
        if events.height
        else None,
        "control_stints": materialized.stints.height,
        "control_year_players": years.height,
        "players_with_service_days": years.filter(pl.col("service_days") > 0).height,
        "players_using_option_year": years.filter(pl.col("option_year_used")).height,
        "opening_review": openings.review_players.to_dicts(),
        "transaction_review": review_details.to_dicts(),
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / f"team-{args.team_id}-{args.season}-{args.as_of}.json"
    _capture(report_path, report)
    _capture(args.capture_dir / "roster.json", roster_capture)
    _capture(args.capture_dir / "teams.json", teams_capture)
    _capture(args.capture_dir / "seasons.json", season_captures)
    for index, capture in enumerate(people.captures, start=1):
        _capture(args.capture_dir / f"people-{index:02d}.json", capture)
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
