#!/usr/bin/env python3
"""Materialize frozen Current Talent B2 at the three Projection-v1 dev snapshots.

Consumes only certified 2021-2024 universal player-game evidence and the pinned
Chadwick identity/age snapshot. It reproduces frozen B2 at each October 15
snapshot, but deliberately does not fit/score a Projection model or access 2025.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_projection_batting_v1_development_evidence import _load_one_season
from universal_baseball.certification import download_file
from universal_baseball.chadwick import (
    CHADWICK_ARCHIVE_URL,
    CHADWICK_SNAPSHOT_SHA,
    build_mlbam_age_as_of,
    read_chadwick_people_archive,
)
from universal_baseball.current_talent_evidence import EvidenceWindow, build_predictor_snapshot
from universal_baseball.current_talent_universal_evidence import combine_universal_player_game_evidence
from universal_baseball.current_talent_validation_dataset import _build_as_of_context
from universal_baseball.projection_current_talent import (
    build_projection_frozen_b2_snapshot,
)
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS
from universal_baseball.storage import write_canonical_parquet


SOURCE_SEASONS = (2021, 2022, 2023, 2024)
CURRENT_SEASON_CONTEXT_WINDOW = EvidenceWindow(
    label="projection_current_season_context_180d",
    lookback_days=None,
    half_life_days=180.0,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-current-talent-snapshots"),
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=Path("data/quarantine/projection-batting-v1-current-talent-snapshots"),
    )
    return parser.parse_args()


def _context_with_age(
    summary: pl.DataFrame,
    profile: pl.DataFrame,
    people: pl.DataFrame,
    *,
    cutoff,
) -> pl.DataFrame:
    predictor_summary, _ = build_predictor_snapshot(
        summary,
        profile,
        cutoff=cutoff,
        window=CURRENT_SEASON_CONTEXT_WINDOW,
    )
    context = _build_as_of_context(summary, cutoff=cutoff)
    predictor_ids = sorted(int(value) for value in predictor_summary.get_column("player_id").to_list())
    ages = build_mlbam_age_as_of(people, predictor_ids, as_of_date=cutoff)
    if ages.filter(pl.col("age_source_status") != "exact_birth_date").height:
        bad = ages.filter(pl.col("age_source_status") != "exact_birth_date")
        raise RuntimeError(
            f"Projection frozen B2 requires exact age at {cutoff}; unresolved={bad.height}"
        )
    joined = (
        predictor_summary.select("player_id", "effective_core_events")
        .join(context, on="player_id", how="left")
        .join(ages.select("player_id", "age_years"), on="player_id", how="left")
        .sort("player_id")
    )
    if joined.filter(pl.col("age_years").is_null()).height:
        raise RuntimeError(f"Projection frozen B2 context has missing age at {cutoff}")
    return joined


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    season_data: dict[int, tuple[pl.DataFrame, pl.DataFrame]] = {}
    source_reports: list[dict[str, object]] = []
    for season in SOURCE_SEASONS:
        summary, profile, source_report = _load_one_season(args.input_root, season)
        season_data[season] = (summary, profile)
        source_reports.append(source_report)

    archive_path = args.work_root / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    archive_capture = download_file(CHADWICK_ARCHIVE_URL, archive_path)
    people = read_chadwick_people_archive(archive_path)

    fold_reports: list[dict[str, object]] = []
    for fold in PROJECTION_V1_DEVELOPMENT_FOLDS:
        snapshot_season = fold.snapshot_date.year
        authorized_seasons = tuple(season for season in SOURCE_SEASONS if season <= snapshot_season)
        current_summary, current_profile = season_data[snapshot_season]
        history_summary, history_profile, history_metrics = combine_universal_player_game_evidence(
            [season_data[season][0] for season in authorized_seasons],
            [season_data[season][1] for season in authorized_seasons],
            expected_seasons=set(authorized_seasons),
            require_all_universal_leagues=True,
        )
        context = _context_with_age(
            current_summary,
            current_profile,
            people,
            cutoff=fold.snapshot_date,
        )
        snapshot = build_projection_frozen_b2_snapshot(
            history_summary,
            history_profile,
            current_summary,
            current_profile,
            context,
            fold=fold,
        )

        fold_dir = table_root / fold.label
        fold_dir.mkdir(parents=True, exist_ok=True)
        storage = {
            "profile": write_canonical_parquet(
                snapshot.profile,
                fold_dir / "frozen_b2_profile.parquet",
                table_name=f"{fold.label}_frozen_b2_profile",
            ).as_record(),
            "player_context": write_canonical_parquet(
                snapshot.player_context,
                fold_dir / "player_context.parquet",
                table_name=f"{fold.label}_player_context",
            ).as_record(),
            "translation_offsets": write_canonical_parquet(
                snapshot.translation_offsets,
                fold_dir / "translation_offsets.parquet",
                table_name=f"{fold.label}_translation_offsets",
            ).as_record(),
        }
        fold_reports.append(
            {
                "fold": fold.label,
                "snapshot_date": fold.snapshot_date.isoformat(),
                "authorized_history_seasons": list(authorized_seasons),
                "history_metrics": history_metrics,
                "snapshot_metrics": snapshot.metrics,
                "storage": storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_frozen_current_talent_snapshots_pre_model",
        "source_seasons_available": list(SOURCE_SEASONS),
        "chadwick_snapshot_sha": CHADWICK_SNAPSHOT_SHA,
        "chadwick_capture": archive_capture,
        "source_components": source_reports,
        "folds": fold_reports,
        "boundary": {
            "accessed_2025": False,
            "projection_model_fit": False,
            "projection_predictions_computed": False,
            "future_outcomes_scored": False,
            "candidate_selected": False,
            "playing_time_modeled": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Projection v1 frozen Current Talent snapshots",
        "",
        "- 2025 accessed: False",
        "- Projection model fit/scored: False",
        "",
    ]
    for row in fold_reports:
        metrics = row["snapshot_metrics"]
        lines.extend(
            [
                f"## {row['fold']}",
                f"- Snapshot: {row['snapshot_date']}",
                f"- Authorized history seasons: {row['authorized_history_seasons']}",
                f"- B2 players: {metrics['player_count']:,}",
                f"- B2 profile rows: {metrics['profile_row_count']:,}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
