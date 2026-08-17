#!/usr/bin/env python3
"""Audit exact Chadwick DOB coverage for a Current Talent training population."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--as-of-date", type=str, required=True)
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("data/quarantine/current-talent-age-coverage"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/generated/current-talent-age-coverage"),
    )
    return parser.parse_args()


def _load_training_player_ids(root: Path, season: int, cutoff: date) -> list[int]:
    paths = sorted(root.rglob(f"current_talent_game_summary_{season}_*.parquet"))
    if len(paths) != 6:
        raise ValueError(
            "age coverage audit expects exactly six universal level summary files "
            f"(five affiliated MiLB + MLB); found {len(paths)}: {[str(path) for path in paths]}"
        )

    frames: list[pl.DataFrame] = []
    for path in paths:
        frame = pl.read_parquet(path).select("season", "game_date", "player_id", "level_group")
        frames.append(frame)
    combined = pl.concat(frames, how="vertical_relaxed").with_columns(
        pl.col("game_date").cast(pl.Date),
        pl.col("player_id").cast(pl.Int64),
    )
    observed_seasons = sorted(
        int(value) for value in combined.get_column("season").unique().to_list()
    )
    if observed_seasons != [int(season)]:
        raise ValueError(
            f"age coverage input season mismatch: observed={observed_seasons}, expected={[season]}"
        )
    training = combined.filter(pl.col("game_date") < cutoff)
    if training.is_empty():
        raise ValueError("age coverage audit found no training player-game evidence before cutoff")
    return sorted(
        int(value) for value in training.get_column("player_id").unique().to_list()
    )


def main() -> int:
    args = _parse_args()
    cutoff = date.fromisoformat(args.as_of_date)
    player_ids = _load_training_player_ids(args.input_root, int(args.season), cutoff)

    archive_path = args.work_dir / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_metadata = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)
    ages = build_mlbam_age_as_of(people, player_ids, as_of_date=cutoff)

    status_counts = Counter(str(value) for value in ages.get_column("age_source_status").to_list())
    exact = ages.filter(pl.col("age_source_status") == "exact_birth_date")
    missing = ages.filter(pl.col("age_source_status") != "exact_birth_date")
    exact_count = int(exact.height)
    player_count = len(player_ids)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    ages.write_csv(args.output_dir / "player_age_as_of.csv")
    missing.write_csv(args.output_dir / "missing_exact_age.csv")
    report = {
        "report_schema_version": "0.1",
        "season": int(args.season),
        "as_of_date": cutoff.isoformat(),
        "temporal_rule": "training games strictly before as_of_date; age derived at as_of_date",
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_archive": archive_metadata,
        "training_player_count": player_count,
        "exact_birth_date_count": exact_count,
        "exact_birth_date_coverage_rate": exact_count / player_count,
        "age_source_status_counts": dict(sorted(status_counts.items())),
        "missing_exact_age_count": int(missing.height),
        "missing_exact_age_player_ids": [
            int(value) for value in missing.get_column("player_id").to_list()
        ],
        "exact_age_min_years": float(exact.get_column("age_years").min()) if exact_count else None,
        "exact_age_max_years": float(exact.get_column("age_years").max()) if exact_count else None,
        "interpretation": (
            "Coverage diagnostic only. Partial/missing DOB is not imputed. Duplicate requested "
            "MLBAM identities or invalid complete DOBs fail closed in the age derivation layer."
        ),
    }
    (args.output_dir / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
