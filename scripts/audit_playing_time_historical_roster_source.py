#!/usr/bin/env python3
"""Audit official historical roster snapshots for playing-time/role v1.

This is a source-feasibility gate, not a model-development run. It checks whether
MLB Stats API date-specific 40-man rosters can be reproduced at all three
pre-2025 Oct. 15 snapshots across every MLB club, plus smaller active-roster,
transaction, and date-sensitivity diagnostics.

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
    fetch_team_roster_as_of,
    fetch_team_transactions_around,
)


SNAPSHOTS = (
    date(2021, 10, 15),
    date(2022, 10, 15),
    date(2023, 10, 15),
)
ACTIVE_SAMPLE_TEAMS = (110, 137, 147)
DATE_SENSITIVITY_TEAM = 137
DATE_SENSITIVITY_EARLY = date(2021, 4, 1)
REPORT_ROOT = Path("reports/generated/playing-time-historical-roster-source")
CAPTURE_ROOT = Path("data/quarantine/playing-time-historical-roster-source")


def _write_capture(path: Path, capture: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _roster_keys(frame: pl.DataFrame) -> set[tuple[int, int]]:
    return {
        (int(row["team_id"]), int(row["player_id"]))
        for row in frame.select("team_id", "player_id").iter_rows(named=True)
    }


def main() -> int:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    CAPTURE_ROOT.mkdir(parents=True, exist_ok=True)
    table_root = REPORT_ROOT / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model-playing-time-source-audit/0.1"

    season_reports: list[dict[str, object]] = []
    forty_man_frames: list[pl.DataFrame] = []
    active_frames: list[pl.DataFrame] = []
    all_calls_2xx = True
    all_teams_nonempty = True
    all_seasons_30_teams = True

    try:
        for snapshot in SNAPSHOTS:
            season = snapshot.year
            teams, teams_capture = fetch_mlb_teams(season, session=session)
            _write_capture(CAPTURE_ROOT / str(season) / "teams.json", teams_capture)
            team_count = int(teams.height)
            all_seasons_30_teams = all_seasons_30_teams and team_count == 30

            season_40: list[pl.DataFrame] = []
            team_rows: list[dict[str, object]] = []
            for team in teams.iter_rows(named=True):
                team_id = int(team["team_id"])
                roster, capture = fetch_team_roster_as_of(
                    team_id,
                    season=season,
                    as_of_date=snapshot,
                    roster_type="40Man",
                    session=session,
                )
                _write_capture(
                    CAPTURE_ROOT / str(season) / "40Man" / f"team_{team_id}.json",
                    capture,
                )
                all_calls_2xx = all_calls_2xx and int(capture["status_code"]) == 200
                all_teams_nonempty = all_teams_nonempty and roster.height > 0
                season_40.append(roster)
                forty_man_frames.append(roster)
                team_rows.append(
                    {
                        "season": season,
                        "snapshot_date": snapshot.isoformat(),
                        "team_id": team_id,
                        "team_name": str(team["team_name"]),
                        "forty_man_count": int(roster.height),
                    }
                )

            combined_40 = pl.concat(season_40, how="vertical_relaxed")
            duplicate_across_teams = (
                combined_40.group_by("player_id")
                .agg(pl.col("team_id").n_unique().alias("team_count"))
                .filter(pl.col("team_count") > 1)
            )

            active_not_40_count = 0
            active_sample_rows: list[dict[str, object]] = []
            forty_keys = _roster_keys(combined_40)
            for team_id in ACTIVE_SAMPLE_TEAMS:
                active, capture = fetch_team_roster_as_of(
                    team_id,
                    season=season,
                    as_of_date=snapshot,
                    roster_type="active",
                    session=session,
                )
                _write_capture(
                    CAPTURE_ROOT / str(season) / "active" / f"team_{team_id}.json",
                    capture,
                )
                active_frames.append(active)
                missing_from_40 = [
                    row
                    for row in active.select("team_id", "player_id").iter_rows(named=True)
                    if (int(row["team_id"]), int(row["player_id"])) not in forty_keys
                ]
                active_not_40_count += len(missing_from_40)
                active_sample_rows.append(
                    {
                        "team_id": team_id,
                        "active_count": int(active.height),
                        "active_not_in_40man_count": len(missing_from_40),
                    }
                )

            transactions, transaction_capture = fetch_team_transactions_around(
                DATE_SENSITIVITY_TEAM,
                as_of_date=snapshot,
                days_each_side=2,
                session=session,
            )
            _write_capture(
                CAPTURE_ROOT / str(season) / f"team_{DATE_SENSITIVITY_TEAM}_transactions_pm2d.json",
                transaction_capture,
            )

            counts = pl.DataFrame(team_rows)
            season_reports.append(
                {
                    "season": season,
                    "snapshot_date": snapshot.isoformat(),
                    "mlb_team_count": team_count,
                    "forty_man_team_count_min": int(counts.get_column("forty_man_count").min()),
                    "forty_man_team_count_max": int(counts.get_column("forty_man_count").max()),
                    "forty_man_team_count_mean": float(counts.get_column("forty_man_count").mean()),
                    "forty_man_player_rows": int(combined_40.height),
                    "cross_team_duplicate_player_count": int(duplicate_across_teams.height),
                    "active_sample": active_sample_rows,
                    "active_not_in_same_date_40man_count": active_not_40_count,
                    "transactions_pm2d_for_team_137": len(transactions),
                }
            )

        # Explicit test that the `date` parameter is not merely ignored for a
        # historical 40-man query. Compare one team's early-season and Oct. 15
        # rosters within the same season.
        early, early_capture = fetch_team_roster_as_of(
            DATE_SENSITIVITY_TEAM,
            season=2021,
            as_of_date=DATE_SENSITIVITY_EARLY,
            roster_type="40Man",
            session=session,
        )
        late, late_capture = fetch_team_roster_as_of(
            DATE_SENSITIVITY_TEAM,
            season=2021,
            as_of_date=SNAPSHOTS[0],
            roster_type="40Man",
            session=session,
        )
        _write_capture(CAPTURE_ROOT / "date_sensitivity_2021_early.json", early_capture)
        _write_capture(CAPTURE_ROOT / "date_sensitivity_2021_late.json", late_capture)
        early_ids = set(int(value) for value in early.get_column("player_id").to_list())
        late_ids = set(int(value) for value in late.get_column("player_id").to_list())
        date_sensitive = early_ids != late_ids
        symmetric_difference = sorted(early_ids ^ late_ids)

    finally:
        session.close()

    forty_man = pl.concat(forty_man_frames, how="vertical_relaxed").sort(
        ["season", "team_id", "player_id"]
    )
    active_sample = pl.concat(active_frames, how="vertical_relaxed").sort(
        ["season", "team_id", "player_id"]
    )
    forty_man.write_parquet(table_root / "historical_40man_rosters.parquet")
    active_sample.write_parquet(table_root / "historical_active_roster_sample.parquet")

    no_cross_team_duplicates = all(
        int(row["cross_team_duplicate_player_count"]) == 0 for row in season_reports
    )
    accepted = bool(
        all_calls_2xx
        and all_teams_nonempty
        and all_seasons_30_teams
        and no_cross_team_duplicates
        and date_sensitive
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_historical_roster_source_feasibility",
        "snapshots": [snapshot.isoformat() for snapshot in SNAPSHOTS],
        "queried_2025": False,
        "roster_source": "official_mlb_stats_api_team_roster",
        "roster_type_primary": "40Man",
        "season_reports": season_reports,
        "date_sensitivity_control": {
            "team_id": DATE_SENSITIVITY_TEAM,
            "season": 2021,
            "early_date": DATE_SENSITIVITY_EARLY.isoformat(),
            "late_date": SNAPSHOTS[0].isoformat(),
            "early_count": int(early.height),
            "late_count": int(late.height),
            "roster_sets_differ": date_sensitive,
            "symmetric_difference_player_count": len(symmetric_difference),
            "symmetric_difference_player_ids": symmetric_difference,
        },
        "acceptance": {
            "all_http_calls_2xx": all_calls_2xx,
            "all_historical_40man_team_rosters_nonempty": all_teams_nonempty,
            "all_snapshot_seasons_have_30_mlb_teams": all_seasons_30_teams,
            "no_cross_team_duplicate_40man_player_ids_within_snapshot": no_cross_team_duplicates,
            "historical_date_parameter_changes_roster_membership": date_sensitive,
            "accepted_for_feature_contract_consideration": accepted,
        },
        "interpretation": (
            "Source-feasibility only. Acceptance authorizes historical 40-man status "
            "for consideration in the later frozen feature contract; it does not by "
            "itself authorize active-roster, IL, options, transaction, team-depth, or "
            "other roster-derived predictors. Active-roster and transaction calls are diagnostics."
        ),
    }
    (REPORT_ROOT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        "# Playing-time historical roster source audit",
        "",
        f"- Accepted for feature-contract consideration: {accepted}",
        "- 2025 queried: False",
        f"- All snapshots have 30 MLB teams: {all_seasons_30_teams}",
        f"- All 40-man team/date rosters nonempty: {all_teams_nonempty}",
        f"- Cross-team duplicate 40-man IDs absent: {no_cross_team_duplicates}",
        f"- Historical date parameter changes membership: {date_sensitive}",
        "",
    ]
    for row in season_reports:
        lines.extend(
            [
                f"## {row['snapshot_date']}",
                f"- 40-man rows: {row['forty_man_player_rows']:,}",
                f"- team count range: {row['forty_man_team_count_min']}–{row['forty_man_team_count_max']}",
                f"- cross-team duplicate players: {row['cross_team_duplicate_player_count']}",
                f"- sample active players absent from same-date 40-man: {row['active_not_in_same_date_40man_count']}",
                "",
            ]
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not accepted:
        raise RuntimeError("historical 40-man source feasibility gate failed closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
