#!/usr/bin/env python3
"""Materialize pre-registered Projection-v1 ILR training responses.

Consumes immutable Projection development-target surfaces and frozen B2 October
snapshots. Produces one response row per snapshot player with observed next-year
core events. No candidate is fit, selected, or scored here; 2025 is inaccessible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.projection_ridge import projection_cv_fold
from universal_baseball.projection_training import build_projection_training_response
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS
from universal_baseball.storage import write_canonical_parquet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-training-responses"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    fold_reports: list[dict[str, object]] = []
    for fold in PROJECTION_V1_DEVELOPMENT_FOLDS:
        target_root = args.development_evidence_root / "tables" / fold.label
        snapshot_fold_root = args.snapshot_root / "tables" / fold.label

        target_summary = pl.read_parquet(
            _one(target_root, "target_summary.parquet", f"{fold.label} target summary")
        )
        target_profile = pl.read_parquet(
            _one(target_root, "target_profile.parquet", f"{fold.label} target profile")
        )
        snapshot_profile = pl.read_parquet(
            _one(snapshot_fold_root, "frozen_b2_profile.parquet", f"{fold.label} B2 profile")
        )
        player_context = pl.read_parquet(
            _one(snapshot_fold_root, "player_context.parquet", f"{fold.label} player context")
        )
        translation_offsets = pl.read_parquet(
            _one(snapshot_fold_root, "translation_offsets.parquet", f"{fold.label} translation")
        )

        built = build_projection_training_response(
            snapshot_profile,
            target_summary,
            target_profile,
            translation_offsets,
            fold=fold,
        )
        training_rows = (
            built.responses.join(player_context, on="player_id", how="left")
            .with_columns(
                pl.col("player_id")
                .map_elements(projection_cv_fold, return_dtype=pl.Int64)
                .alias("cv_fold")
            )
            .sort("player_id")
        )
        if training_rows.filter(
            pl.col("age_years").is_null() | pl.col("as_of_level_group").is_null()
        ).height:
            raise RuntimeError(f"{fold.label} training responses lack snapshot age/level context")

        fold_dir = table_root / fold.label
        fold_dir.mkdir(parents=True, exist_ok=True)
        storage = {
            "training_rows": write_canonical_parquet(
                training_rows,
                fold_dir / "training_rows.parquet",
                table_name=f"{fold.label}_projection_training_rows",
            ).as_record(),
            "latent_target_profile": write_canonical_parquet(
                built.latent_target_profile,
                fold_dir / "latent_target_profile.parquet",
                table_name=f"{fold.label}_latent_target_profile",
            ).as_record(),
        }
        fold_reports.append(
            {
                "fold": fold.label,
                "snapshot_date": fold.snapshot_date.isoformat(),
                "target_start": fold.target_start.isoformat(),
                "target_end": fold.target_end.isoformat(),
                "response_metrics": built.metrics,
                "training_row_count": int(training_rows.height),
                "cv_fold_counts": {
                    str(row["cv_fold"]): int(row["len"])
                    for row in training_rows.group_by("cv_fold").len().sort("cv_fold").iter_rows(named=True)
                },
                "storage": storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_training_responses_pre_selection",
        "development_evidence_source_run": 32097702869,
        "frozen_b2_snapshot_source_run": 32099733186,
        "folds": fold_reports,
        "boundary": {
            "accessed_2025": False,
            "projection_candidate_fit": False,
            "projection_candidate_selected": False,
            "proper_scores_computed": False,
            "playing_time_modeled": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection v1 ILR training responses",
        "",
        "- 2025 accessed: False",
        "- Candidate fit/selected: False",
        "- Proper scores computed: False",
        "",
    ]
    for row in fold_reports:
        metrics = row["response_metrics"]
        lines.extend(
            [
                f"## {row['fold']}",
                f"- Response players: {row['training_row_count']:,}",
                f"- Future core events: {metrics['future_core_events_in_responses']:,}",
                f"- Snapshot without future core target: {metrics['snapshot_without_future_core_target_count']:,}",
                f"- Future core target without snapshot: {metrics['future_core_target_without_snapshot_count']:,}",
                f"- CV fold counts: {row['cv_fold_counts']}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
