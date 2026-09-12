#!/usr/bin/env python3
"""Build a transparent partial-coverage 2024-10-15 hitter B2 snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_projection_batting_v1_current_talent_snapshots import _context_with_age
from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.projection_current_talent import build_projection_frozen_b2_snapshot
from universal_baseball.projection_validation import PROJECTION_V1_CONFIRMATION_FOLD
from universal_baseball.storage import write_canonical_parquet


HISTORICAL_SEASONS = (2021, 2022, 2023)
HISTORICAL_LEVELS = ("aaa", "aa", "a+", "a")
CURRENT_LEVELS = ("aaa", "aa", "aplus", "a")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--historical-root",
        type=Path,
        default=Path("reports/generated/prospect-pbp-hurdle-source"),
    )
    parser.add_argument(
        "--affiliated-2024-root",
        type=Path,
        default=Path("reports/generated/prospect-talent-current-evidence/2024"),
    )
    parser.add_argument(
        "--mlb-2024-root",
        type=Path,
        default=Path("reports/generated/prospect-talent-mlb-evidence/2024"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-supported-hitter-current-talent/2024-10-15"),
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/prospect-supported-hitter-current-talent"),
    )
    return parser.parse_args()


def _one(root: Path, name: str) -> Path:
    matches = sorted(root.rglob(name))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {name} below {root}, found {len(matches)}")
    return matches[0]


def _pair(root: Path, season: int, slug: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    return (
        pl.read_parquet(_one(root, f"current_talent_game_summary_{season}_{slug}.parquet")),
        pl.read_parquet(_one(root, f"current_talent_game_profile_{season}_{slug}.parquet")),
    )


def main() -> int:
    args = _args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)

    history_summaries: list[pl.DataFrame] = []
    history_profiles: list[pl.DataFrame] = []
    for season in HISTORICAL_SEASONS:
        for level in HISTORICAL_LEVELS:
            summary, profile = _pair(args.historical_root / str(season), season, level.replace("+", "plus"))
            history_summaries.append(summary)
            history_profiles.append(profile)

    current_summaries: list[pl.DataFrame] = []
    current_profiles: list[pl.DataFrame] = []
    for level in CURRENT_LEVELS:
        summary, profile = _pair(args.affiliated_2024_root / level, 2024, level)
        current_summaries.append(summary)
        current_profiles.append(profile)
    mlb_summary, mlb_profile = _pair(args.mlb_2024_root, 2024, "mlb")
    current_summaries.append(mlb_summary)
    current_profiles.append(mlb_profile)
    history_summaries.extend(current_summaries)
    history_profiles.extend(current_profiles)

    current_summary, current_profile, current_metrics = combine_universal_player_game_evidence(
        current_summaries,
        current_profiles,
        expected_seasons={2024},
        require_all_universal_leagues=False,
    )
    history_summary, history_profile, history_metrics = combine_universal_player_game_evidence(
        history_summaries,
        history_profiles,
        expected_seasons={2021, 2022, 2023, 2024},
        require_all_universal_leagues=False,
    )

    archive = args.work_root / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_capture = download_file(CHADWICK_ARCHIVE_URL, archive)
    people = read_chadwick_people_archive(archive)
    context = _context_with_age(
        current_summary,
        current_profile,
        people,
        cutoff=PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date,
    )
    snapshot = build_projection_frozen_b2_snapshot(
        history_summary,
        history_profile,
        current_summary,
        current_profile,
        context,
        fold=PROJECTION_V1_CONFIRMATION_FOLD,
        allow_confirmation_snapshot=True,
    )

    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    storage = {
        "profile": write_canonical_parquet(
            snapshot.profile,
            table_root / "supported_frozen_b2_profile.parquet",
            table_name="prospect_supported_2024_frozen_b2_profile",
        ).as_record(),
        "player_context": write_canonical_parquet(
            snapshot.player_context,
            table_root / "supported_player_context.parquet",
            table_name="prospect_supported_2024_player_context",
        ).as_record(),
        "translation_offsets": write_canonical_parquet(
            snapshot.translation_offsets,
            table_root / "supported_translation_offsets.parquet",
            table_name="prospect_supported_2024_translation_offsets",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "prospect_supported_hitter_current_talent_2024",
        "status": "diagnostic_partial_coverage_not_production",
        "snapshot_date": PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date.isoformat(),
        "current_levels": ["MLB", "AAA", "AA", "HIGH_A", "SINGLE_A"],
        "missing_current_level": "ROOKIE_COMPLEX",
        "missing_historical_level": "ROOKIE_COMPLEX",
        "missing_historical_mlb_seasons": [2021, 2022, 2023],
        "current_metrics": current_metrics,
        "history_metrics": history_metrics,
        "snapshot_metrics": snapshot.metrics,
        "chadwick_capture": archive_capture,
        "storage": storage,
        "boundary": {
            "current_talent_method_changed": False,
            "future_aging_applied": False,
            "playing_time_modeled": False,
            "future_outcomes_accessed": False,
            "public_rank_or_fv_used": False,
            "production_authorized": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "players": snapshot.metrics["player_count"],
                "profile_rows": snapshot.metrics["profile_row_count"],
                "missing_current_level": report["missing_current_level"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
