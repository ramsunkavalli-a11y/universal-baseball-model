#!/usr/bin/env python3
"""Certify historical binary 40-man membership for playing-time/role v1.

Uses the fail-closed membership projector: one row per team/player/date. Duplicate
source rows are permitted only when player identity and parent-team membership
are unambiguous; conflicting source status values are retained as diagnostics and
never interpreted as active/minors/IL state.

No 2025 endpoint is queried.
"""

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


SNAPSHOTS = (date(2021, 10, 15), date(2022, 10, 15), date(2023, 10, 15))
DATE_SENSITIVITY_TEAM = 137
DATE_SENSITIVITY_EARLY = date(2021, 4, 1)
REPORT_ROOT = Path("reports/generated/playing-time-historical-40man-membership")
CAPTURE_ROOT = Path("data/quarantine/playing-time-historical-40man-membership")


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
    session.headers["User-Agent"] = "universal-baseball-model-40man-membership-audit/0.1"
    season_reports: list[dict[str, object]] = []
    frames: list[pl.DataFrame] = []
    errors: list[dict[str, str]] = []

    try:
        for snapshot in SNAPSHOTS:
            season = snapshot.year
            teams, teams_capture = fetch_mlb_teams(season, session=session)
            _write_capture(CAPTURE_ROOT / str(season) / "teams.json", teams_capture)
            if teams.height != 30:
                errors.append(
                    {
                        "label": f"teams:{season}",
                        "type": "TeamCountMismatch",
                        "message": f"expected 30 MLB teams, observed {teams.height}",
                    }
                )

            team_memberships: list[pl.DataFrame] = []
            failed_teams: list[int] = []
            for team in teams.iter_rows(named=True):
                team_id = int(team["team_id"])
                try:
                    membership, capture = fetch_team_40man_membership_as_of(
                        team_id,
                        season=season,
                        as_of_date=snapshot,
                        session=session,
                    )
                    _write_capture(
                        CAPTURE_ROOT / str(season) / f"team_{team_id}.json", capture
                    )
                    if membership.is_empty():
                        raise RuntimeError("historical 40-man membership set is empty")
                    team_memberships.append(membership)
                    frames.append(membership)
                except Exception as exc:
                    failed_teams.append(team_id)
                    errors.append(
                        {
                            "label": f"40man_membership:{season}:{team_id}",
                            "type": type(exc).__name__,
                            "message": str(exc),
                        }
                    )

            combined = (
                pl.concat(team_memberships, how="vertical_relaxed")
                if team_memberships
                else pl.DataFrame()
            )
            duplicate_across_teams = (
                combined.group_by("player_id")
                .agg(pl.col("team_id").n_unique().alias("team_count"))
                .filter(pl.col("team_count") > 1)
                if not combined.is_empty()
                else pl.DataFrame()
            )
            source_duplicate_members = (
                combined.filter(pl.col("source_row_count") > 1)
                if not combined.is_empty()
                else pl.DataFrame()
            )
            source_status_conflicts = (
                combined.filter(pl.col("source_status_conflict"))
                if not combined.is_empty()
                else pl.DataFrame()
            )
            team_counts = (
                combined.group_by("team_id").len().get_column("len").to_list()
                if not combined.is_empty()
                else []
            )
            season_reports.append(
                {
                    "season": season,
                    "snapshot_date": snapshot.isoformat(),
                    "mlb_team_count": int(teams.height),
                    "successful_team_count": len(team_memberships),
                    "failed_team_ids": failed_teams,
                    "membership_player_rows": int(combined.height),
                    "team_membership_count_min": min(team_counts) if team_counts else None,
                    "team_membership_count_max": max(team_counts) if team_counts else None,
                    "cross_team_duplicate_player_count": int(duplicate_across_teams.height)
                    if not combined.is_empty()
                    else None,
                    "players_with_duplicate_source_rows": int(source_duplicate_members.height)
                    if not combined.is_empty()
                    else None,
                    "players_with_conflicting_source_status_rows": int(source_status_conflicts.height)
                    if not combined.is_empty()
                    else None,
                    "conflicting_status_player_ids": source_status_conflicts.get_column(
                        "player_id"
                    ).to_list()
                    if not source_status_conflicts.is_empty()
                    else [],
                }
            )

        early, early_capture = fetch_team_40man_membership_as_of(
            DATE_SENSITIVITY_TEAM,
            season=2021,
            as_of_date=DATE_SENSITIVITY_EARLY,
            session=session,
        )
        late, late_capture = fetch_team_40man_membership_as_of(
            DATE_SENSITIVITY_TEAM,
            season=2021,
            as_of_date=SNAPSHOTS[0],
            session=session,
        )
        _write_capture(CAPTURE_ROOT / "date_sensitivity_2021_early.json", early_capture)
        _write_capture(CAPTURE_ROOT / "date_sensitivity_2021_late.json", late_capture)
        early_ids = set(int(value) for value in early.get_column("player_id").to_list())
        late_ids = set(int(value) for value in late.get_column("player_id").to_list())
        date_sensitive = early_ids != late_ids
        symmetric_difference = sorted(early_ids ^ late_ids)
    except Exception as exc:
        errors.append(
            {
                "label": "date_sensitivity_or_outer_source",
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )
        date_sensitive = False
        early_ids = set()
        late_ids = set()
        symmetric_difference = []
    finally:
        session.close()

    combined_all = (
        pl.concat(frames, how="vertical_relaxed").sort(
            ["season", "team_id", "player_id"]
        )
        if frames
        else pl.DataFrame()
    )
    if not combined_all.is_empty():
        combined_all.write_parquet(table_root / "historical_40man_membership.parquet")

    all_teams_succeeded = len(season_reports) == len(SNAPSHOTS) and all(
        row["mlb_team_count"] == 30
        and row["successful_team_count"] == 30
        and not row["failed_team_ids"]
        for row in season_reports
    )
    no_cross_team_duplicates = all(
        row["cross_team_duplicate_player_count"] == 0 for row in season_reports
    ) if season_reports else False
    accepted = bool(
        all_teams_succeeded and no_cross_team_duplicates and date_sensitive and not errors
    )

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_historical_40man_membership_certification",
        "snapshots": [snapshot.isoformat() for snapshot in SNAPSHOTS],
        "queried_2025": False,
        "source": "official_mlb_stats_api_40Man",
        "authorized_semantic": "binary_team_40man_membership_as_of_date",
        "unauthorized_semantics": [
            "active_status_from_40Man_response",
            "minor_league_assignment_status_from_40Man_response",
            "injured_list_status_from_40Man_response",
            "option_status",
            "future_roster_role"
        ],
        "season_reports": season_reports,
        "source_errors": errors,
        "date_sensitivity_control": {
            "team_id": DATE_SENSITIVITY_TEAM,
            "season": 2021,
            "early_date": DATE_SENSITIVITY_EARLY.isoformat(),
            "late_date": SNAPSHOTS[0].isoformat(),
            "early_membership_count": len(early_ids),
            "late_membership_count": len(late_ids),
            "membership_sets_differ": date_sensitive,
            "symmetric_difference_player_count": len(symmetric_difference),
            "symmetric_difference_player_ids": symmetric_difference,
        },
        "acceptance": {
            "all_30_teams_succeeded_each_snapshot": all_teams_succeeded,
            "no_cross_team_duplicate_membership_within_snapshot": no_cross_team_duplicates,
            "historical_date_parameter_changes_membership": date_sensitive,
            "accepted_for_playing_time_feature_contract": accepted,
        },
        "interpretation": (
            "Binary 40-man membership is the only certified roster fact from this gate. "
            "Duplicate source rows with conflicting status remain visible diagnostics and "
            "are collapsed only because membership itself is identical and identity/team "
            "checks pass. Row-level status is explicitly not authorized."
        ),
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Historical 40-man membership certification",
        "",
        f"- Accepted for playing-time feature contract: {accepted}",
        "- Authorized semantic: binary 40-man membership only",
        "- 2025 queried: False",
        f"- All 30 teams succeeded each snapshot: {all_teams_succeeded}",
        f"- No cross-team duplicate membership: {no_cross_team_duplicates}",
        f"- Historical date sensitivity proven: {date_sensitive}",
        "",
    ]
    for row in season_reports:
        lines.extend(
            [
                f"## {row['snapshot_date']}",
                f"- membership rows: {row['membership_player_rows']:,}",
                f"- team membership range: {row['team_membership_count_min']}–{row['team_membership_count_max']}",
                f"- duplicate source-row members: {row['players_with_duplicate_source_rows']}",
                f"- conflicting source-status members: {row['players_with_conflicting_source_status_rows']}",
                "",
            ]
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not accepted:
        raise RuntimeError("historical 40-man membership certification failed closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
