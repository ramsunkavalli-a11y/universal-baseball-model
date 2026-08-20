#!/usr/bin/env python3
"""Audit official historical roster snapshots for playing-time/role v1.

Source-feasibility only. Every live endpoint failure is captured into the report
so the gate fails closed with diagnostics instead of aborting before persistence.
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


SNAPSHOTS = (date(2021, 10, 15), date(2022, 10, 15), date(2023, 10, 15))
ACTIVE_SAMPLE_TEAMS = (110, 137, 147)
DATE_SENSITIVITY_TEAM = 137
DATE_SENSITIVITY_EARLY = date(2021, 4, 1)
REPORT_ROOT = Path("reports/generated/playing-time-historical-roster-source")
CAPTURE_ROOT = Path("data/quarantine/playing-time-historical-roster-source")


def _write_capture(path: Path, capture: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(capture, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _error(label: str, exc: Exception) -> dict[str, str]:
    return {"label": label, "type": type(exc).__name__, "message": str(exc)}


def _roster_keys(frame: pl.DataFrame) -> set[tuple[int, int]]:
    if frame.is_empty():
        return set()
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
    session.headers["User-Agent"] = "universal-baseball-model-playing-time-source-audit/0.2"

    errors: list[dict[str, str]] = []
    season_reports: list[dict[str, object]] = []
    forty_man_frames: list[pl.DataFrame] = []
    active_frames: list[pl.DataFrame] = []
    all_teams_nonempty = True
    all_seasons_30_teams = True

    try:
        for snapshot in SNAPSHOTS:
            season = snapshot.year
            try:
                teams, teams_capture = fetch_mlb_teams(season, session=session)
                _write_capture(CAPTURE_ROOT / str(season) / "teams.json", teams_capture)
            except Exception as exc:  # live-source audit must persist the failure
                errors.append(_error(f"teams:{season}", exc))
                all_seasons_30_teams = False
                all_teams_nonempty = False
                season_reports.append(
                    {
                        "season": season,
                        "snapshot_date": snapshot.isoformat(),
                        "mlb_team_count": 0,
                        "successful_40man_team_count": 0,
                        "failed_40man_team_count": None,
                        "forty_man_player_rows": 0,
                        "cross_team_duplicate_player_count": None,
                        "active_sample": [],
                        "active_not_in_same_date_40man_count": None,
                        "transactions_pm2d_for_team_137": None,
                    }
                )
                continue

            team_count = int(teams.height)
            all_seasons_30_teams = all_seasons_30_teams and team_count == 30
            season_40: list[pl.DataFrame] = []
            team_rows: list[dict[str, object]] = []
            failed_team_count = 0

            for team in teams.iter_rows(named=True):
                team_id = int(team["team_id"])
                try:
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
                    if roster.is_empty():
                        all_teams_nonempty = False
                        errors.append(
                            {
                                "label": f"40Man:{season}:{team_id}",
                                "type": "EmptyRoster",
                                "message": "historical 40-man response was empty",
                            }
                        )
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
                except Exception as exc:
                    failed_team_count += 1
                    all_teams_nonempty = False
                    errors.append(_error(f"40Man:{season}:{team_id}", exc))

            combined_40 = (
                pl.concat(season_40, how="vertical_relaxed")
                if season_40
                else pl.DataFrame()
            )
            duplicate_across_teams = (
                combined_40.group_by("player_id")
                .agg(pl.col("team_id").n_unique().alias("team_count"))
                .filter(pl.col("team_count") > 1)
                if not combined_40.is_empty()
                else pl.DataFrame()
            )

            active_not_40_count = 0
            active_sample_rows: list[dict[str, object]] = []
            forty_keys = _roster_keys(combined_40)
            for team_id in ACTIVE_SAMPLE_TEAMS:
                try:
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
                            "source_error": None,
                        }
                    )
                except Exception as exc:
                    errors.append(_error(f"active:{season}:{team_id}", exc))
                    active_sample_rows.append(
                        {
                            "team_id": team_id,
                            "active_count": None,
                            "active_not_in_40man_count": None,
                            "source_error": str(exc),
                        }
                    )

            transaction_count: int | None
            try:
                transactions, transaction_capture = fetch_team_transactions_around(
                    DATE_SENSITIVITY_TEAM,
                    as_of_date=snapshot,
                    days_each_side=2,
                    session=session,
                )
                _write_capture(
                    CAPTURE_ROOT
                    / str(season)
                    / f"team_{DATE_SENSITIVITY_TEAM}_transactions_pm2d.json",
                    transaction_capture,
                )
                transaction_count = len(transactions)
            except Exception as exc:
                errors.append(_error(f"transactions:{season}:{DATE_SENSITIVITY_TEAM}", exc))
                transaction_count = None

            count_values = [int(row["forty_man_count"]) for row in team_rows]
            season_reports.append(
                {
                    "season": season,
                    "snapshot_date": snapshot.isoformat(),
                    "mlb_team_count": team_count,
                    "successful_40man_team_count": len(team_rows),
                    "failed_40man_team_count": failed_team_count,
                    "forty_man_team_count_min": min(count_values) if count_values else None,
                    "forty_man_team_count_max": max(count_values) if count_values else None,
                    "forty_man_team_count_mean": sum(count_values) / len(count_values)
                    if count_values
                    else None,
                    "forty_man_player_rows": int(combined_40.height),
                    "cross_team_duplicate_player_count": int(duplicate_across_teams.height)
                    if not combined_40.is_empty()
                    else None,
                    "active_sample": active_sample_rows,
                    "active_not_in_same_date_40man_count": active_not_40_count,
                    "transactions_pm2d_for_team_137": transaction_count,
                }
            )

        date_sensitive = False
        early_count: int | None = None
        late_count: int | None = None
        symmetric_difference: list[int] = []
        try:
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
            early_count = int(early.height)
            late_count = int(late.height)
            symmetric_difference = sorted(early_ids ^ late_ids)
        except Exception as exc:
            errors.append(_error("date_sensitivity:2021:137", exc))

    finally:
        session.close()

    if forty_man_frames:
        pl.concat(forty_man_frames, how="vertical_relaxed").sort(
            ["season", "team_id", "player_id"]
        ).write_parquet(table_root / "historical_40man_rosters.parquet")
    if active_frames:
        pl.concat(active_frames, how="vertical_relaxed").sort(
            ["season", "team_id", "player_id"]
        ).write_parquet(table_root / "historical_active_roster_sample.parquet")

    no_cross_team_duplicates = bool(season_reports) and all(
        row["cross_team_duplicate_player_count"] == 0
        for row in season_reports
        if row["cross_team_duplicate_player_count"] is not None
    )
    all_primary_calls_succeeded = all(
        int(row["successful_40man_team_count"]) == 30
        and int(row["failed_40man_team_count"] or 0) == 0
        for row in season_reports
    )
    accepted = bool(
        all_primary_calls_succeeded
        and all_teams_nonempty
        and all_seasons_30_teams
        and no_cross_team_duplicates
        and date_sensitive
    )
    report = {
        "report_schema_version": "0.2",
        "gate": "playing_time_historical_roster_source_feasibility",
        "snapshots": [snapshot.isoformat() for snapshot in SNAPSHOTS],
        "queried_2025": False,
        "roster_source": "official_mlb_stats_api_team_roster",
        "roster_type_primary": "40Man",
        "season_reports": season_reports,
        "source_errors": errors,
        "date_sensitivity_control": {
            "team_id": DATE_SENSITIVITY_TEAM,
            "season": 2021,
            "early_date": DATE_SENSITIVITY_EARLY.isoformat(),
            "late_date": SNAPSHOTS[0].isoformat(),
            "early_count": early_count,
            "late_count": late_count,
            "roster_sets_differ": date_sensitive,
            "symmetric_difference_player_count": len(symmetric_difference),
            "symmetric_difference_player_ids": symmetric_difference,
        },
        "acceptance": {
            "all_primary_40man_calls_succeeded": all_primary_calls_succeeded,
            "all_historical_40man_team_rosters_nonempty": all_teams_nonempty,
            "all_snapshot_seasons_have_30_mlb_teams": all_seasons_30_teams,
            "no_cross_team_duplicate_40man_player_ids_within_snapshot": no_cross_team_duplicates,
            "historical_date_parameter_changes_roster_membership": date_sensitive,
            "accepted_for_feature_contract_consideration": accepted,
        },
        "interpretation": (
            "Source-feasibility only. Acceptance authorizes historical 40-man status "
            "for consideration in the later frozen feature contract; active roster, "
            "IL/options/transactions/team-depth require separate authorization."
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
        f"- Source errors captured: {len(errors)}",
        f"- All snapshot seasons have 30 MLB teams: {all_seasons_30_teams}",
        f"- All primary 40-man calls succeeded: {all_primary_calls_succeeded}",
        f"- Historical date parameter changes membership: {date_sensitive}",
        "",
    ]
    for row in season_reports:
        lines.extend(
            [
                f"## {row['snapshot_date']}",
                f"- successful 40-man teams: {row['successful_40man_team_count']}",
                f"- failed 40-man teams: {row['failed_40man_team_count']}",
                f"- 40-man rows: {row['forty_man_player_rows']:,}",
                f"- team count range: {row.get('forty_man_team_count_min')}–{row.get('forty_man_team_count_max')}",
                f"- cross-team duplicate players: {row['cross_team_duplicate_player_count']}",
                "",
            ]
        )
    (REPORT_ROOT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    if not accepted:
        raise RuntimeError("historical 40-man source feasibility gate failed closed; see persisted report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
