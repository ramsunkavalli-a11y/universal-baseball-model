#!/usr/bin/env python3
"""Materialize next-season MLB PA targets for playing-time/role v1.

Consumes immutable pre-2025 Projection development targets and frozen B2 snapshot
populations. Every eligible snapshot player receives a next-season MLB PA target,
including explicit zero. No playing-time model is fit or scored and no 2025 data
is accessed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS
from universal_baseball.storage import write_canonical_parquet



def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--development-evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-target-surface"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def _fold_target(
    development_root: Path,
    snapshot_root: Path,
    *,
    fold_label: str,
) -> tuple[pl.DataFrame, dict[str, object]]:
    target_summary = pl.read_parquet(
        _one(
            development_root / "tables" / fold_label,
            "target_summary.parquet",
            f"{fold_label} target summary",
        )
    )
    context = pl.read_parquet(
        _one(
            snapshot_root / "tables" / fold_label,
            "player_context.parquet",
            f"{fold_label} player context",
        )
    )
    if context.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError(f"{fold_label} snapshot context violates player grain")

    future_any = target_summary.group_by("player_id").agg(
        pl.col("future_plate_appearances").sum().cast(pl.Int64).alias("next_year_affiliated_pa")
    )
    future_mlb = (
        target_summary.filter(pl.col("target_level_group") == "MLB")
        .group_by("player_id")
        .agg(pl.col("future_plate_appearances").sum().cast(pl.Int64).alias("next_year_mlb_pa"))
    )

    target = (
        context.join(future_any, on="player_id", how="left")
        .join(future_mlb, on="player_id", how="left")
        .with_columns(
            pl.col("next_year_affiliated_pa").fill_null(0).cast(pl.Int64),
            pl.col("next_year_mlb_pa").fill_null(0).cast(pl.Int64),
        )
        .with_columns(
            (pl.col("next_year_mlb_pa") > 0).alias("has_next_year_mlb_pa"),
            (pl.col("next_year_affiliated_pa") > 0).alias("has_next_year_affiliated_pa"),
        )
        .sort("player_id")
    )
    if target.filter(pl.col("next_year_mlb_pa") < 0).height:
        raise RuntimeError(f"{fold_label} contains negative future MLB PA")
    if target.filter(pl.col("next_year_mlb_pa") > pl.col("next_year_affiliated_pa")).height:
        raise RuntimeError(f"{fold_label} MLB PA exceeds total affiliated PA")

    positive = target.filter(pl.col("next_year_mlb_pa") > 0)
    positive_mean = float(positive.get_column("next_year_mlb_pa").mean()) if positive.height else 0.0
    positive_variance = (
        float(positive.get_column("next_year_mlb_pa").var(ddof=0)) if positive.height else 0.0
    )
    level_metrics = (
        target.group_by("as_of_level_group")
        .agg(
            pl.len().alias("snapshot_players"),
            pl.col("has_next_year_mlb_pa").sum().cast(pl.Int64).alias("players_with_mlb_pa"),
            pl.col("next_year_mlb_pa").sum().cast(pl.Int64).alias("mlb_pa"),
            pl.col("next_year_mlb_pa").mean().alias("mean_mlb_pa"),
        )
        .with_columns(
            (pl.col("players_with_mlb_pa") / pl.col("snapshot_players")).alias("mlb_participation_rate")
        )
        .sort("as_of_level_group")
    )
    metrics: dict[str, object] = {
        "snapshot_player_count": int(target.height),
        "players_with_next_year_affiliated_pa": int(
            target.get_column("has_next_year_affiliated_pa").sum()
        ),
        "players_with_next_year_mlb_pa": int(target.get_column("has_next_year_mlb_pa").sum()),
        "zero_next_year_mlb_pa_count": int((target.get_column("next_year_mlb_pa") == 0).sum()),
        "zero_next_year_mlb_pa_share": float((target.get_column("next_year_mlb_pa") == 0).mean()),
        "mean_next_year_mlb_pa_all_snapshot_players": float(
            target.get_column("next_year_mlb_pa").mean()
        ),
        "positive_mlb_pa_mean": positive_mean,
        "positive_mlb_pa_median": float(positive.get_column("next_year_mlb_pa").median())
        if positive.height
        else 0.0,
        "positive_mlb_pa_p90": float(
            positive.get_column("next_year_mlb_pa").quantile(0.90, interpolation="nearest")
        )
        if positive.height
        else 0.0,
        "positive_mlb_pa_max": int(positive.get_column("next_year_mlb_pa").max())
        if positive.height
        else 0,
        "positive_mlb_pa_variance": positive_variance,
        "positive_mlb_pa_variance_to_mean": positive_variance / positive_mean
        if positive_mean > 0
        else None,
        "as_of_level_metrics": level_metrics.to_dicts(),
    }
    return target, metrics


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    fold_reports: list[dict[str, object]] = []
    for fold in PROJECTION_V1_DEVELOPMENT_FOLDS:
        target, metrics = _fold_target(
            args.development_evidence_root,
            args.snapshot_root,
            fold_label=fold.label,
        )
        fold_dir = table_root / fold.label
        fold_dir.mkdir(parents=True, exist_ok=True)
        storage = write_canonical_parquet(
            target,
            fold_dir / "next_year_mlb_pa_targets.parquet",
            table_name=f"{fold.label}_playing_time_mlb_pa_targets",
        ).as_record()
        fold_reports.append(
            {
                "fold": fold.label,
                "snapshot_date": fold.snapshot_date.isoformat(),
                "target_year": fold.target_start.year,
                "metrics": metrics,
                "storage": storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_target_surface_pre_model",
        "development_evidence_source_run": 32097702869,
        "frozen_b2_snapshot_source_run": 32099733186,
        "folds": fold_reports,
        "boundary": {
            "2025_accessed": False,
            "playing_time_model_fit": False,
            "playing_time_predictions_computed": False,
            "role_thresholds_applied": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        "# Playing-time v1 target surface",
        "",
        "- 2025 accessed: False",
        "- Playing-time model fit: False",
        "",
    ]
    for row in fold_reports:
        metrics = row["metrics"]
        lines.extend(
            [
                f"## {row['fold']}",
                f"- snapshot players: {metrics['snapshot_player_count']:,}",
                f"- players with next-year MLB PA: {metrics['players_with_next_year_mlb_pa']:,}",
                f"- zero-MLB-PA share: {metrics['zero_next_year_mlb_pa_share']:.3%}",
                f"- positive MLB PA mean: {metrics['positive_mlb_pa_mean']:.1f}",
                f"- positive MLB PA median: {metrics['positive_mlb_pa_median']:.1f}",
                f"- positive variance/mean: {metrics['positive_mlb_pa_variance_to_mean']:.2f}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
