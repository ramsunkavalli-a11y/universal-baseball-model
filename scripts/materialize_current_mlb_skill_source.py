#!/usr/bin/env python3
"""Materialize recent official MLB component counts for current forecasting.

Completed seasons and the current partial season are predictor evidence only.
This runner does not score a model or inspect a future target season.
"""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.mlb_season_stats import (
    MlbBulkStatsCapture,
    fetch_mlb_hitting_backbone,
    fetch_mlb_pitching_backbone,
)
from universal_baseball.player_value_mlb_run_environment import fetch_mlb_run_environment
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--lookback-seasons", type=int, default=4)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    return parser.parse_args()


def _capture_record(capture: MlbBulkStatsCapture, *, group: str) -> dict[str, object]:
    return {
        "group": group,
        "season": capture.season,
        "league_id": capture.league_id,
        "offset": capture.offset,
        "requested_limit": capture.requested_limit,
        "returned_split_count": capture.returned_split_count,
        "reported_total_splits": capture.total_splits,
        "response_byte_count": len(capture.response_bytes),
        "response_sha256": capture.response_sha256,
    }


def _write_raw(
    capture: MlbBulkStatsCapture,
    *,
    group: str,
    raw_root: Path,
) -> Path:
    path = raw_root / (
        f"{group}-{capture.season}-league-{capture.league_id}"
        f"-offset-{capture.offset}.json"
    )
    path.write_bytes(capture.response_bytes)
    if sha256(path.read_bytes()).hexdigest() != capture.response_sha256:
        raise RuntimeError(f"persisted source hash mismatch: {path}")
    return path


def main() -> int:
    args = _args()
    if args.lookback_seasons < 1:
        raise ValueError("lookback-seasons must be positive")
    start = args.as_of_date.year - args.lookback_seasons + 1
    seasons = tuple(range(start, args.as_of_date.year + 1))
    output_root = args.output_root / args.as_of_date.isoformat()
    raw_root = output_root / "raw"
    table_root = output_root / "tables"
    raw_root.mkdir(parents=True, exist_ok=True)
    table_root.mkdir(parents=True, exist_ok=True)

    hitting_frames: list[pl.DataFrame] = []
    pitching_frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    for season in seasons:
        hitting, hitting_captures = fetch_mlb_hitting_backbone(season)
        pitching, pitching_captures = fetch_mlb_pitching_backbone(season)
        if hitting.is_empty() or pitching.is_empty():
            raise RuntimeError(f"official MLB skill source is empty for {season}")
        hitting_frames.append(hitting)
        pitching_frames.append(pitching)
        for group, group_captures in (
            ("hitting", hitting_captures),
            ("pitching", pitching_captures),
        ):
            for capture in group_captures:
                path = _write_raw(capture, group=group, raw_root=raw_root)
                record = _capture_record(capture, group=group)
                record["raw_path"] = path.as_posix()
                captures.append(record)

    hitting_all = pl.concat(hitting_frames).sort(["season", "league_id", "player_id"])
    pitching_all = pl.concat(pitching_frames).sort(["season", "league_id", "player_id"])
    reference_season = args.as_of_date.year - 1
    environment = fetch_mlb_run_environment(reference_season)
    storage = {
        "hitting": write_canonical_parquet(
            hitting_all,
            table_root / "mlb_hitting_components.parquet",
            table_name="current_mlb_hitting_components",
        ).as_record(),
        "pitching": write_canonical_parquet(
            pitching_all,
            table_root / "mlb_pitching_components.parquet",
            table_name="current_mlb_pitching_components",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_mlb_skill_predictor_source",
        "as_of_date": args.as_of_date.isoformat(),
        "seasons": list(seasons),
        "current_season_status": "partial_as_of_date",
        "use": "forecast predictor evidence only",
        "future_target_or_model_scoring": False,
        "team_depth_used": False,
        "source": "official MLB StatsAPI bulk regular-season statistics",
        "reference_environment": {
            "season": reference_season,
            "regular_season_games": environment.regular_season_games,
            "batting_runs_scored": environment.batting_runs_scored,
            "batting_plate_appearances": environment.batting_plate_appearances,
            "pitching_batters_faced": int(
                pitching_all.filter(pl.col("season") == reference_season)
                .get_column("pitching_batters_faced")
                .sum()
            ),
            "pitching_outs": environment.pitching_outs,
            "runs_per_win": environment.runs_per_win.runs_per_win,
        },
        "hitting_rows": hitting_all.height,
        "pitching_rows": pitching_all.height,
        "captures": captures,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({key: report[key] for key in ("gate", "seasons", "hitting_rows", "pitching_rows")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
