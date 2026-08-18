#!/usr/bin/env python3
"""Certify binary 40-man membership at the 2024-10-15 confirmation snapshot."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.playing_time_roster_source import (
    fetch_mlb_teams,
    fetch_team_40man_membership_as_of,
)
from universal_baseball.storage import write_canonical_parquet


SNAPSHOT = date(2024, 10, 15)
REPORT_ROOT = Path("reports/generated/playing-time-confirmation-40man-membership")
CAPTURE_ROOT = Path("data/quarantine/playing-time-confirmation-40man-membership")


def _write_capture(path: Path, capture: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-confirmation-40man/0.1"
    frames: list[pl.DataFrame] = []
    failed_teams: list[int] = []
    errors: list[dict[str, str]] = []
    try:
        teams, teams_capture = fetch_mlb_teams(2024, session=session)
        _write_capture(CAPTURE_ROOT / "teams.json", teams_capture)
        for team in teams.iter_rows(named=True):
            team_id = int(team["team_id"])
            try:
                membership, capture = fetch_team_40man_membership_as_of(
                    team_id,
                    season=2024,
                    as_of_date=SNAPSHOT,
                    session=session,
                )
                _write_capture(CAPTURE_ROOT / f"team_{team_id}.json", capture)
                if membership.is_empty():
                    raise RuntimeError("confirmation 40-man membership set is empty")
                frames.append(membership)
            except Exception as exc:
                failed_teams.append(team_id)
                errors.append(
                    {
                        "team_id": str(team_id),
                        "type": type(exc).__name__,
                        "message": str(exc),
                    }
                )
    finally:
        session.close()

    combined = (
        pl.concat(frames, how="vertical_relaxed").sort(["team_id", "player_id"])
        if frames
        else pl.DataFrame()
    )
    duplicate_across_teams = (
        combined.group_by("player_id")
        .agg(pl.col("team_id").n_unique().alias("team_count"))
        .filter(pl.col("team_count") > 1)
        if not combined.is_empty()
        else pl.DataFrame()
    )
    source_duplicates = (
        combined.filter(pl.col("source_row_count") > 1) if not combined.is_empty() else pl.DataFrame()
    )
    source_status_conflicts = (
        combined.filter(pl.col("source_status_conflict")) if not combined.is_empty() else pl.DataFrame()
    )
    team_counts = (
        combined.group_by("team_id").len().get_column("len").to_list()
        if not combined.is_empty()
        else []
    )

    accepted = bool(
        len(frames) == 30
        and not failed_teams
        and not errors
        and not combined.is_empty()
        and duplicate_across_teams.is_empty()
    )
    storage = None
    if not combined.is_empty():
        storage = write_canonical_parquet(
            combined,
            table_root / "confirmation_40man_membership.parquet",
            table_name="playing_time_confirmation_2024_10_15_40man_membership",
        ).as_record()

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_confirmation_40man_membership_certification",
        "snapshot_date": SNAPSHOT.isoformat(),
        "season": 2024,
        "source": "official_mlb_stats_api_40Man",
        "authorized_semantic": "binary_team_40man_membership_as_of_date",
        "unauthorized_semantics": [
            "active_status_from_40Man_response",
            "minor_league_assignment_status_from_40Man_response",
            "injured_list_status_from_40Man_response",
            "option_status",
            "future_roster_role",
        ],
        "successful_team_count": len(frames),
        "failed_team_ids": failed_teams,
        "membership_player_rows": int(combined.height),
        "team_membership_count_min": min(team_counts) if team_counts else None,
        "team_membership_count_max": max(team_counts) if team_counts else None,
        "cross_team_duplicate_player_count": int(duplicate_across_teams.height),
        "players_with_duplicate_source_rows": int(source_duplicates.height),
        "players_with_conflicting_source_status_rows": int(source_status_conflicts.height),
        "conflicting_status_player_ids": source_status_conflicts.get_column("player_id").to_list()
        if not source_status_conflicts.is_empty()
        else [],
        "source_errors": errors,
        "accepted": accepted,
        "storage": storage,
        "boundary": {
            "2025_roster_queried": False,
            "2025_outcomes_accessed": False,
            "row_level_status_used_as_predictor": False,
        },
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time confirmation 40-man membership",
        "",
        f"- Snapshot: {SNAPSHOT.isoformat()}",
        f"- Accepted: {accepted}",
        f"- Successful teams: {len(frames)}/30",
        f"- Membership rows: {combined.height:,}",
        f"- Cross-team duplicate players: {duplicate_across_teams.height}",
        "- Authorized semantic: binary membership only",
        "- 2025 outcomes accessed: False",
        "",
    ]
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not accepted:
        raise RuntimeError("confirmation 40-man membership certification failed closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
