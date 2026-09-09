#!/usr/bin/env python3
"""Materialize official affiliated hitter and pitcher component evidence."""

from __future__ import annotations

import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_skill_source import (
    AffiliatedSkillCapture,
    fetch_affiliated_skill_stats,
)
from universal_baseball.storage import write_canonical_parquet


def _seasons(raw: str) -> tuple[int, ...]:
    values = tuple(sorted({int(value.strip()) for value in raw.split(",") if value.strip()}))
    if not values:
        raise argparse.ArgumentTypeError("seasons must not be empty")
    return values


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", type=_seasons, required=True)
    parser.add_argument("--current-predictor-season", type=int, required=True)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/affiliated-skill-source"),
    )
    return parser.parse_args()


def _write_capture(capture: AffiliatedSkillCapture, root: Path) -> dict[str, object]:
    path = root / str(capture.season) / (
        f"{capture.stat_group}-offset-{capture.offset}.json.gz"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wb") as handle:
        handle.write(capture.response_bytes)
    with gzip.open(path, "rb") as handle:
        observed = sha256(handle.read()).hexdigest()
    if observed != capture.response_sha256:
        raise RuntimeError(f"affiliated capture hash mismatch: {path}")
    return {
        "season": capture.season, "stat_group": capture.stat_group,
        "offset": capture.offset, "requested_limit": capture.requested_limit,
        "returned_rows": capture.returned_rows,
        "reported_total_splits": capture.reported_total_splits,
        "response_sha256": capture.response_sha256, "path": path.as_posix(),
    }


def main() -> int:
    args = _args()
    if args.current_predictor_season not in args.seasons:
        raise ValueError("current-predictor-season must be included in seasons")
    tables = args.output_root / "tables"
    captures_root = args.output_root / "captures"
    tables.mkdir(parents=True, exist_ok=True)
    hitter_frames: list[pl.DataFrame] = []
    pitcher_frames: list[pl.DataFrame] = []
    capture_records: list[dict[str, object]] = []
    seasonal: list[dict[str, object]] = []
    for season in args.seasons:
        hitters, hitter_captures = fetch_affiliated_skill_stats(
            season, stat_group="hitting"
        )
        pitchers, pitcher_captures = fetch_affiliated_skill_stats(
            season, stat_group="pitching"
        )
        if hitters.is_empty() or pitchers.is_empty():
            raise RuntimeError(f"affiliated skill source is empty for {season}")
        hitter_frames.append(hitters)
        pitcher_frames.append(pitchers)
        capture_records.extend(
            _write_capture(capture, captures_root)
            for capture in (*hitter_captures, *pitcher_captures)
        )
        seasonal.append(
            {
                "season": season,
                "status": "partial_predictor"
                if season == args.current_predictor_season
                else "completed_predictor",
                "hitting_rows": hitters.height,
                "pitching_rows": pitchers.height,
                "hitting_players": hitters.get_column("player_id").n_unique(),
                "pitching_players": pitchers.get_column("player_id").n_unique(),
            }
        )
    hitters = pl.concat(hitter_frames).sort(["season", "player_id", "sport_id", "team_id"])
    pitchers = pl.concat(pitcher_frames).sort(["season", "player_id", "sport_id", "team_id"])
    storage = {
        "hitting": write_canonical_parquet(
            hitters, tables / "affiliated_hitting_components.parquet",
            table_name="affiliated_hitting_components",
        ).as_record(),
        "pitching": write_canonical_parquet(
            pitchers, tables / "affiliated_pitching_components.parquet",
            table_name="affiliated_pitching_components",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "official_affiliated_skill_predictor_source",
        "seasons": list(args.seasons),
        "current_predictor_season": args.current_predictor_season,
        "current_season_used_as_evaluation_target": False,
        "reported_total_splits_trusted": False,
        "team_depth_used": False,
        "seasonal": seasonal,
        "captures": capture_records,
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "seasonal": seasonal}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
