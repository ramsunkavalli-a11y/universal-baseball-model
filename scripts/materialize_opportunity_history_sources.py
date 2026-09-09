#!/usr/bin/env python3
"""Collect official historical roster/level inputs for opportunity paths."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import gzip
import json
from pathlib import Path

import polars as pl

from universal_baseball.opportunity_history_source import (
    build_opportunity_snapshots,
    fetch_affiliated_season_stats,
    fetch_historical_full_roster_detail,
)
from universal_baseball.playing_time_roster_source import fetch_mlb_teams
from universal_baseball.storage import write_canonical_parquet


def _seasons(value: str) -> tuple[int, ...]:
    result = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not result:
        raise argparse.ArgumentTypeError("expected comma-separated seasons")
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=_seasons, required=True)
    parser.add_argument("--snapshot-month", type=int, default=10)
    parser.add_argument("--snapshot-day", type=int, default=15)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-history-sources"),
    )
    return parser.parse_args()


def _write_capture(path: Path, capture: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(capture, handle, sort_keys=True, default=str)


def main() -> int:
    args = _parse_args()
    if not 1 <= args.workers <= 10:
        raise ValueError("workers must be between 1 and 10")
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    capture_root = args.output_root / "captures"
    table_root.mkdir(parents=True, exist_ok=True)
    reports = []
    all_hitters = []
    all_pitchers = []

    for season in args.seasons:
        snapshot = date(season, args.snapshot_month, args.snapshot_day)
        teams, team_capture = fetch_mlb_teams(season)
        _write_capture(capture_root / str(season) / "teams.json.gz", team_capture)
        team_ids = teams.get_column("team_id").to_list()

        def fetch(team_id: int):
            return fetch_historical_full_roster_detail(team_id, snapshot_date=snapshot)

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(fetch, team_ids))
        roster = pl.concat([result[0] for result in results]).sort(
            ["candidate_organization_id", "player_id"]
        )
        for _frame, capture in results:
            _write_capture(
                capture_root / str(season) / f"full-roster-{capture['team_id']}.json.gz",
                capture,
            )
        hitting, hitting_captures = fetch_affiliated_season_stats(
            season, stat_group="hitting"
        )
        pitching, pitching_captures = fetch_affiliated_season_stats(
            season, stat_group="pitching"
        )
        stats = pl.concat([hitting, pitching])
        hitters, pitchers = build_opportunity_snapshots(roster, stats)
        all_hitters.append(hitters)
        all_pitchers.append(pitchers)

        year_root = table_root / str(season)
        year_root.mkdir(parents=True, exist_ok=True)
        storage = {
            "roster": write_canonical_parquet(
                roster, year_root / "full_roster_details.parquet", table_name=f"opportunity_full_roster_{season}"
            ).as_record(),
            "stats": write_canonical_parquet(
                stats, year_root / "affiliated_season_stats.parquet", table_name=f"opportunity_affiliated_stats_{season}"
            ).as_record(),
            "hitters": write_canonical_parquet(
                hitters, year_root / "hitter_snapshot.parquet", table_name=f"opportunity_hitter_snapshot_{season}"
            ).as_record(),
            "pitchers": write_canonical_parquet(
                pitchers, year_root / "pitcher_snapshot.parquet", table_name=f"opportunity_pitcher_snapshot_{season}"
            ).as_record(),
        }
        reports.append(
            {
                "season": season,
                "snapshot_date": snapshot.isoformat(),
                "teams": len(team_ids),
                "roster_rows": roster.height,
                "distinct_roster_players": roster.get_column("player_id").n_unique(),
                "hitting_splits": hitting.height,
                "pitching_splits": pitching.height,
                "hitting_pages": len(hitting_captures),
                "pitching_pages": len(pitching_captures),
                "hitter_players": hitters.height,
                "pitcher_players": pitchers.height,
                "inactive_hitter_players": hitters.filter(
                    pl.col("as_of_level_group") == "INACTIVE"
                ).height,
                "inactive_pitcher_players": pitchers.filter(
                    pl.col("as_of_level_group") == "INACTIVE"
                ).height,
                "storage": storage,
            }
        )

    combined_storage = {
        "hitters": write_canonical_parquet(
            pl.concat(all_hitters).sort(["snapshot_year", "player_id"]),
            table_root / "hitter_snapshots.parquet",
            table_name="opportunity_hitter_snapshots",
        ).as_record(),
        "pitchers": write_canonical_parquet(
            pl.concat(all_pitchers).sort(["snapshot_year", "player_id"]),
            table_root / "pitcher_snapshots.parquet",
            table_name="opportunity_pitcher_snapshots",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_historical_source_materialization",
        "source": "official_mlb_statsapi_fullRoster_and_affiliated_season_stats",
        "seasons": list(args.seasons),
        "reported_total_splits_trusted": False,
        "future_team_or_depth_used": False,
        "rights_owner_inferred_from_full_roster": False,
        "season_reports": reports,
        "combined_storage": combined_storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
