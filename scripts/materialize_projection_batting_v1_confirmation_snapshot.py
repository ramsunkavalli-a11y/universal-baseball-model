#!/usr/bin/env python3
"""Materialize the frozen 2024-10-15 B2 predictor snapshot for confirmation.

This script is authorized only after Playing Time v1 development promotion and
pre-2025 refit freeze. It consumes certified 2021-2024 evidence only and never
opens or scores 2025 outcomes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from materialize_projection_batting_v1_current_talent_snapshots import _context_with_age
from materialize_projection_batting_v1_development_evidence import _load_one_season
from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_universal_evidence import combine_universal_player_game_evidence
from universal_baseball.projection_current_talent import build_projection_frozen_b2_snapshot
from universal_baseball.projection_validation import PROJECTION_V1_CONFIRMATION_FOLD
from universal_baseball.storage import write_canonical_parquet


SOURCE_SEASONS = (2021, 2022, 2023, 2024)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-confirmation-snapshot"),
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/projection-batting-v1-confirmation-snapshot"),
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables" / PROJECTION_V1_CONFIRMATION_FOLD.label
    table_root.mkdir(parents=True, exist_ok=True)

    season_data = {}
    source_reports: list[dict[str, object]] = []
    for season in SOURCE_SEASONS:
        summary, profile, source_report = _load_one_season(args.input_root, season)
        season_data[season] = (summary, profile)
        source_reports.append(source_report)

    archive_path = args.work_root / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_capture = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    current_summary, current_profile = season_data[2024]
    history_summary, history_profile, history_metrics = combine_universal_player_game_evidence(
        [season_data[season][0] for season in SOURCE_SEASONS],
        [season_data[season][1] for season in SOURCE_SEASONS],
        expected_seasons=set(SOURCE_SEASONS),
        require_all_universal_leagues=True,
    )
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

    storage = {
        "profile": write_canonical_parquet(
            snapshot.profile,
            table_root / "frozen_b2_profile.parquet",
            table_name="projection_2024_to_2025_confirmation_frozen_b2_profile",
        ).as_record(),
        "player_context": write_canonical_parquet(
            snapshot.player_context,
            table_root / "player_context.parquet",
            table_name="projection_2024_to_2025_confirmation_player_context",
        ).as_record(),
        "translation_offsets": write_canonical_parquet(
            snapshot.translation_offsets,
            table_root / "translation_offsets.parquet",
            table_name="projection_2024_to_2025_confirmation_translation_offsets",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_confirmation_snapshot_pre_2025_outcomes",
        "fold": PROJECTION_V1_CONFIRMATION_FOLD.label,
        "snapshot_date": PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date.isoformat(),
        "authorized_history_seasons": list(SOURCE_SEASONS),
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_capture": archive_capture,
        "source_components": source_reports,
        "history_metrics": history_metrics,
        "snapshot_metrics": snapshot.metrics,
        "storage": storage,
        "boundary": {
            "2025_outcomes_accessed": False,
            "2025_target_materialized": False,
            "playing_time_model_fit": False,
            "playing_time_predictions_computed": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection confirmation frozen B2 snapshot",
        "",
        f"- Snapshot: {PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date.isoformat()}",
        f"- B2 players: {snapshot.metrics['player_count']:,}",
        f"- B2 profile rows: {snapshot.metrics['profile_row_count']:,}",
        "- 2025 outcomes accessed: False",
        "- Playing-time model scored: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
