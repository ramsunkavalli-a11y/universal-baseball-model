#!/usr/bin/env python
"""Materialize completed-season MLB batting and pitching career backbones.

This is an outcome/source inventory, not a fitted model. It deliberately stops
at completed 2025 so protected and incomplete 2026 outcomes cannot enter
career-label development through this runner.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.career_outcomes import (
    project_mlb_batting_backbone,
    project_mlb_pitching_backbone,
)
from universal_baseball.mlb_season_stats import (
    MlbBulkStatsCapture,
    fetch_mlb_hitting_backbone,
    fetch_mlb_pitching_backbone,
)


MAX_AUTHORIZED_OUTCOME_SEASON = 2025


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-season", type=int, default=2015)
    parser.add_argument("--end-season", type=int, default=MAX_AUTHORIZED_OUTCOME_SEASON)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory"),
    )
    return parser.parse_args()


def _write_capture(
    capture: MlbBulkStatsCapture,
    *,
    group: str,
    raw_dir: Path,
) -> dict[str, object]:
    name = (
        f"{group}-{capture.season}-league-{capture.league_id}"
        f"-offset-{capture.offset}.json"
    )
    path = raw_dir / name
    path.write_bytes(capture.response_bytes)
    observed = sha256(path.read_bytes()).hexdigest()
    if observed != capture.response_sha256:
        raise RuntimeError(f"persisted source capture hash mismatch: {path}")
    return {
        "group": group,
        "season": capture.season,
        "league_id": capture.league_id,
        "offset": capture.offset,
        "returned_split_count": capture.returned_split_count,
        "total_splits": capture.total_splits,
        "response_byte_count": len(capture.response_bytes),
        "response_sha256": capture.response_sha256,
        "raw_path": path.as_posix(),
    }


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def materialize_inventory(
    *,
    start_season: int,
    end_season: int,
    output_dir: Path,
) -> dict[str, object]:
    if start_season > end_season:
        raise ValueError("start-season cannot exceed end-season")
    if end_season > MAX_AUTHORIZED_OUTCOME_SEASON:
        raise ValueError(
            f"end-season exceeds authorized completed outcome boundary "
            f"{MAX_AUTHORIZED_OUTCOME_SEASON}"
        )
    if start_season < 1901:
        raise ValueError("start-season predates modern MLB scope")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    table_dir = output_dir / "tables"
    raw_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)

    batting_frames: list[pl.DataFrame] = []
    pitching_frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    seasonal: list[dict[str, object]] = []

    for season in range(start_season, end_season + 1):
        batting_raw, batting_captures = fetch_mlb_hitting_backbone(season)
        pitching_raw, pitching_captures = fetch_mlb_pitching_backbone(season)
        if batting_raw.is_empty() or pitching_raw.is_empty():
            raise RuntimeError(f"completed MLB source backbone is empty for {season}")
        batting = project_mlb_batting_backbone(batting_raw)
        pitching = project_mlb_pitching_backbone(pitching_raw)
        batting_frames.append(batting)
        pitching_frames.append(pitching)
        captures.extend(
            _write_capture(capture, group="hitting", raw_dir=raw_dir)
            for capture in batting_captures
        )
        captures.extend(
            _write_capture(capture, group="pitching", raw_dir=raw_dir)
            for capture in pitching_captures
        )

        hitters = batting.select("player_id").unique()
        pitchers = pitching.select("player_id").unique()
        seasonal.append(
            {
                "season": season,
                "hitter_count": hitters.height,
                "pitcher_count": pitchers.height,
                "batting_and_pitching_outcome_count": hitters.join(
                    pitchers, on="player_id", how="inner"
                ).height,
                "batting_pa": int(batting.get_column("batting_pa").sum()),
                "pitching_bf": int(pitching.get_column("pitching_bf").sum()),
            }
        )

    batting_all = pl.concat(batting_frames, how="vertical").sort(["season", "player_id"])
    pitching_all = pl.concat(pitching_frames, how="vertical").sort(["season", "player_id"])
    batting_path = table_dir / f"mlb_batting_{start_season}_{end_season}.parquet"
    pitching_path = table_dir / f"mlb_pitching_{start_season}_{end_season}.parquet"
    batting_all.write_parquet(batting_path)
    pitching_all.write_parquet(pitching_path)

    player_seasons = pl.concat(
        [
            batting_all.select("season", "player_id"),
            pitching_all.select("season", "player_id"),
        ]
    ).unique()
    careers = player_seasons.group_by("player_id").agg(
        pl.col("season").min().alias("first_observed_mlb_season"),
        pl.col("season").max().alias("last_observed_mlb_season"),
        pl.col("season").n_unique().alias("observed_mlb_season_count"),
    ).sort("player_id")
    careers_path = table_dir / f"mlb_observed_careers_{start_season}_{end_season}.parquet"
    careers.write_parquet(careers_path)

    report: dict[str, object] = {
        "report_schema_version": 1,
        "status": "completed_mlb_career_outcome_inventory",
        "season_start": start_season,
        "season_end": end_season,
        "complete_seasons": list(range(start_season, end_season + 1)),
        "protected_2026_accessed": False,
        "incomplete_current_season_accessed": False,
        "source": "official MLB Stats API regular-season bulk stats",
        "source_mode": "current-corrected historical outcomes; not vintage-as-of evidence",
        "captures": captures,
        "seasonal": seasonal,
        "combined": {
            "batting_player_season_rows": batting_all.height,
            "pitching_player_season_rows": pitching_all.height,
            "distinct_observed_players": careers.height,
            "batting_pa": int(batting_all.get_column("batting_pa").sum()),
            "pitching_bf": int(pitching_all.get_column("pitching_bf").sum()),
        },
        "outputs": {
            "batting": {
                "path": batting_path.as_posix(),
                "sha256": _sha256_file(batting_path),
            },
            "pitching": {
                "path": pitching_path.as_posix(),
                "sha256": _sha256_file(pitching_path),
            },
            "observed_careers": {
                "path": careers_path.as_posix(),
                "sha256": _sha256_file(careers_path),
            },
        },
        "limitations": [
            "This inventory contains observed MLB outcomes, not the pre-MLB cohort denominator.",
            "No observed career end is inferred from a player's last season in this window.",
            "A complete zero/non-arrival panel requires a dated historical player universe.",
            "Calendar follow-up seasons are not service-time seasons or team-control years.",
        ],
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    args = _parse_args()
    report = materialize_inventory(
        start_season=args.start_season,
        end_season=args.end_season,
        output_dir=args.output_dir,
    )
    print(json.dumps({"status": report["status"], "combined": report["combined"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
