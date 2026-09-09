#!/usr/bin/env python3
"""Collect exact-date historical 40-man membership for opportunity modeling."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import gzip
import json
from pathlib import Path

import polars as pl

from universal_baseball.playing_time_roster_source import (
    fetch_mlb_teams,
    fetch_team_40man_membership_as_of,
)
from universal_baseball.storage import write_canonical_parquet


def parse_seasons(value: str) -> tuple[int, ...]:
    seasons = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not seasons:
        raise argparse.ArgumentTypeError("expected comma-separated seasons")
    return seasons


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=parse_seasons, required=True)
    parser.add_argument("--snapshot-month", type=int, default=10)
    parser.add_argument("--snapshot-day", type=int, default=15)
    parser.add_argument("--workers", type=int, default=10)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/opportunity-40man-history"),
    )
    return parser.parse_args()


def _capture(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as target:
        json.dump(payload, target, sort_keys=True, default=str)


def main() -> int:
    args = _args()
    if not 1 <= args.workers <= 10:
        raise ValueError("workers must be between 1 and 10")
    tables = args.output_root / "tables"
    captures = args.output_root / "captures"
    tables.mkdir(parents=True, exist_ok=True)
    frames: list[pl.DataFrame] = []
    season_reports: list[dict[str, object]] = []

    for season in args.seasons:
        snapshot = date(season, args.snapshot_month, args.snapshot_day)
        teams, teams_capture = fetch_mlb_teams(season)
        if teams.height != 30:
            raise RuntimeError(f"expected 30 MLB teams in {season}, found {teams.height}")
        _capture(captures / str(season) / "teams.json.gz", teams_capture)

        def fetch(team_id: int):
            return fetch_team_40man_membership_as_of(
                team_id, season=season, as_of_date=snapshot
            )

        team_ids = [int(value) for value in teams.get_column("team_id").to_list()]
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(fetch, team_ids))
        season_frame = pl.concat([result[0] for result in results]).sort(
            ["team_id", "player_id"]
        )
        if season_frame.group_by("player_id").agg(
            pl.col("team_id").n_unique().alias("team_count")
        ).filter(pl.col("team_count") > 1).height:
            raise RuntimeError(f"{season} 40-man membership has cross-team conflicts")
        for team_id, (_membership, capture) in zip(team_ids, results, strict=True):
            _capture(
                captures / str(season) / f"team-{team_id}.json.gz",
                capture,
            )
        frames.append(season_frame)
        season_reports.append(
            {
                "season": season,
                "snapshot_date": snapshot.isoformat(),
                "team_count": len(team_ids),
                "membership_rows": season_frame.height,
                "membership_players": season_frame.get_column("player_id").n_unique(),
                "duplicate_source_members": season_frame.filter(
                    pl.col("source_row_count") > 1
                ).height,
                "conflicting_status_members": season_frame.filter(
                    pl.col("source_status_conflict")
                ).height,
            }
        )

    combined = pl.concat(frames).sort(["season", "team_id", "player_id"])
    storage = write_canonical_parquet(
        combined,
        tables / "historical_40man_membership.parquet",
        table_name="opportunity_historical_40man_membership",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "opportunity_historical_40man_source",
        "source": "official_mlb_statsapi_40Man",
        "authorized_semantic": "binary membership at exact snapshot date only",
        "snapshots": season_reports,
        "future_team_or_depth_used": False,
        "row_status_used_as_feature": False,
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
