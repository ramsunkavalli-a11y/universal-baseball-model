#!/usr/bin/env python3
"""Audit official full-roster responses as a dated affiliated-player source.

The endpoint describes ``fullRoster`` as active and inactive players. The source
is accepted for primary candidate discovery when all teams succeed and a date
control changes membership. Cross-organization rows are retained as reconciliation
outliers and do not prevent candidate coverage.
"""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.player_rights_universe import (
    build_player_candidate_inventory,
    project_full_roster_to_player_candidates,
)
from universal_baseball.playing_time_roster_source import (
    fetch_mlb_teams,
    fetch_team_full_roster_candidates_as_of,
)


SNAPSHOT = date(2024, 10, 15)
DATE_CONTROL_TEAM = 137
DATE_CONTROL_EARLY = date(2024, 4, 1)
REPORT_ROOT = Path("reports/generated/affiliated-full-roster-source-audit")


def _fetch(session: requests.Session, team_id: int, as_of_date: date) -> list[dict]:
    response = session.get(
        f"https://statsapi.mlb.com/api/v1/teams/{team_id}/roster",
        params={
            "rosterType": "fullRoster",
            "season": as_of_date.year,
            "date": as_of_date.isoformat(),
        },
        timeout=30,
    )
    response.raise_for_status()
    rows = response.json().get("roster")
    if not isinstance(rows, list) or not rows:
        raise ValueError("fullRoster response missing nonempty roster")
    return rows


def _profile_ids(rows: list[dict]) -> tuple[set[int], int]:
    result: set[int] = set()
    row_count = 0
    for row in rows:
        player_id = (row.get("person") or {}).get("id")
        if player_id is None:
            raise ValueError("fullRoster row missing person.id")
        result.add(int(player_id))
        row_count += 1
    return result, row_count - len(result)


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-full-roster-audit/0.1"
    errors: list[dict[str, object]] = []
    team_counts: dict[int, int] = {}
    duplicate_counts: dict[int, int] = {}
    organizations_by_player: dict[int, list[int]] = {}
    source_frames: list[pl.DataFrame] = []
    try:
        teams, _ = fetch_mlb_teams(SNAPSHOT.year, session=session)
        for team_id in teams.get_column("team_id").to_list():
            try:
                source_frame, _ = fetch_team_full_roster_candidates_as_of(
                    int(team_id),
                    season=SNAPSHOT.year,
                    as_of_date=SNAPSHOT,
                    session=session,
                )
                source_frames.append(source_frame)
                player_ids = set(source_frame.get_column("player_id").to_list())
                duplicate_count = int(
                    source_frame.get_column("source_row_count").sum() - source_frame.height
                )
                team_counts[int(team_id)] = len(player_ids)
                duplicate_counts[int(team_id)] = duplicate_count
                for player_id in player_ids:
                    organizations_by_player.setdefault(player_id, []).append(int(team_id))
            except Exception as exc:
                errors.append(
                    {"team_id": int(team_id), "type": type(exc).__name__, "message": str(exc)}
                )
        early, early_duplicate_count = _profile_ids(
            _fetch(session, DATE_CONTROL_TEAM, DATE_CONTROL_EARLY)
        )
        late, late_duplicate_count = _profile_ids(
            _fetch(session, DATE_CONTROL_TEAM, SNAPSHOT)
        )
    finally:
        session.close()

    conflicts = {
        str(player_id): sorted(team_ids)
        for player_id, team_ids in organizations_by_player.items()
        if len(set(team_ids)) > 1
    }
    date_difference = sorted(early ^ late)
    accepted = bool(len(team_counts) == 30 and not errors and date_difference)
    combined_source = pl.concat(source_frames).sort(
        ["candidate_organization_id", "player_id"]
    )
    generic_candidates = project_full_roster_to_player_candidates(combined_source)
    inventory = build_player_candidate_inventory(
        generic_candidates,
        as_of_date=SNAPSHOT,
    )
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    source_path = table_root / "full_roster_candidates.parquet"
    inventory_path = table_root / "player_candidate_inventory.parquet"
    combined_source.write_parquet(source_path)
    inventory.write_parquet(inventory_path)
    uncontested = len(organizations_by_player) - len(conflicts)
    report = {
        "gate": "affiliated_full_roster_source_feasibility",
        "source": "official_mlb_stats_api_fullRoster",
        "snapshot": SNAPSHOT.isoformat(),
        "protected_2026_accessed": False,
        "team_count": len(team_counts),
        "player_rows": sum(team_counts.values()),
        "distinct_players": len(organizations_by_player),
        "team_player_count_min": min(team_counts.values()) if team_counts else None,
        "team_player_count_max": max(team_counts.values()) if team_counts else None,
        "teams_with_duplicate_source_rows": sum(
            count > 0 for count in duplicate_counts.values()
        ),
        "within_team_duplicate_source_row_count": sum(duplicate_counts.values()),
        "cross_organization_conflict_count": len(conflicts),
        "cross_organization_conflicts": conflicts,
        "date_control": {
            "team_id": DATE_CONTROL_TEAM,
            "early_date": DATE_CONTROL_EARLY.isoformat(),
            "late_date": SNAPSHOT.isoformat(),
            "early_count": len(early),
            "late_count": len(late),
            "early_duplicate_source_row_count": early_duplicate_count,
            "late_duplicate_source_row_count": late_duplicate_count,
            "symmetric_difference_count": len(date_difference),
            "symmetric_difference_player_ids": date_difference,
        },
        "errors": errors,
        "accepted_as_primary_candidate_discovery_source": accepted,
        "accepted_as_direct_rights_evidence": False,
        "uncontested_candidate_organization_count": uncontested,
        "uncontested_candidate_organization_rate": (
            uncontested / len(organizations_by_player) if organizations_by_player else None
        ),
        "outputs": {
            "full_roster_candidates_sha256": sha256(source_path.read_bytes()).hexdigest(),
            "player_candidate_inventory_sha256": sha256(
                inventory_path.read_bytes()
            ).hexdigest(),
        },
        "interpretation": (
            "Accepted as the primary player-candidate source. A unique organization entry is "
            "provisional and must be strengthened by 40-man or transaction evidence before "
            "final rights valuation. Multi-organization players require reconciliation. Row "
            "status, option state, level and future role remain unauthorized."
        ),
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
