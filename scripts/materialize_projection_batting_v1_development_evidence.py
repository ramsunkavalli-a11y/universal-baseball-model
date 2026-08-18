#!/usr/bin/env python3
"""Materialize Projection v1 development evidence without fitting or scoring.

This gate consumes already-certified Current Talent player-game evidence for
2021-2024, combines MLB + all affiliated levels on the universal contract, and
materializes the three frozen Projection v1 predictor/next-calendar-year target
surfaces.

It deliberately does NOT:
- fit or apply an aging/development adjustment;
- materialize frozen Baseline-2 probabilities;
- compute log loss, Brier, calibration, or promotion decisions;
- infer playing time or future role;
- access 2025 evidence.

A central output is history-coverage accounting. Projection Baseline 0 must be
the actual frozen 1,095-day Baseline-2 Current Talent estimator, so early folds
may require older certified evidence rather than silently shortening history.
"""

from __future__ import annotations

import argparse
from datetime import timedelta
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.current_talent_evidence import EvidenceWindow
from universal_baseball.current_talent_universal_evidence import (
    combine_universal_player_game_evidence,
)
from universal_baseball.projection_dataset import build_projection_snapshot_dataset
from universal_baseball.projection_validation import PROJECTION_V1_DEVELOPMENT_FOLDS
from universal_baseball.storage import write_canonical_parquet


SOURCE_SEASONS = (2021, 2022, 2023, 2024)
LEVEL_SLUGS = ("aaa", "aa", "aplus", "a", "rk")
WINDOW = EvidenceWindow(
    label="projection_v1_frozen_b2_1095d_180d",
    lookback_days=1095,
    half_life_days=180.0,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-root",
        type=Path,
        required=True,
        help="Root containing seeded/<season>/{milb,mlb} artifact trees.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/projection-batting-v1-development-evidence"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}")
    return matches[0]


def _load_one_season(root: Path, season: int) -> tuple[pl.DataFrame, pl.DataFrame, dict[str, Any]]:
    year_root = root / str(season)
    milb_root = year_root / "milb"
    mlb_root = year_root / "mlb"
    summaries: list[pl.DataFrame] = []
    profiles: list[pl.DataFrame] = []
    inputs: list[dict[str, Any]] = []

    for slug in LEVEL_SLUGS:
        summary_path = _one(
            milb_root,
            f"current_talent_game_summary_{season}_{slug}.parquet",
            f"{season} {slug} summary",
        )
        profile_path = _one(
            milb_root,
            f"current_talent_game_profile_{season}_{slug}.parquet",
            f"{season} {slug} profile",
        )
        summaries.append(pl.read_parquet(summary_path))
        profiles.append(pl.read_parquet(profile_path))
        inputs.append(
            {
                "component": slug,
                "summary_path": str(summary_path),
                "profile_path": str(profile_path),
            }
        )

    mlb_summary_path = _one(
        mlb_root,
        f"current_talent_game_summary_{season}_mlb.parquet",
        f"{season} MLB summary",
    )
    mlb_profile_path = _one(
        mlb_root,
        f"current_talent_game_profile_{season}_mlb.parquet",
        f"{season} MLB profile",
    )
    summaries.append(pl.read_parquet(mlb_summary_path))
    profiles.append(pl.read_parquet(mlb_profile_path))
    inputs.append(
        {
            "component": "mlb",
            "summary_path": str(mlb_summary_path),
            "profile_path": str(mlb_profile_path),
        }
    )

    summary, profile, metrics = combine_universal_player_game_evidence(
        summaries,
        profiles,
        expected_seasons={season},
        require_all_universal_leagues=True,
    )
    return summary, profile, {"season": season, "inputs": inputs, "metrics": metrics}


def _history_coverage(summary: pl.DataFrame, *, snapshot_date) -> dict[str, Any]:
    requested_start = snapshot_date - timedelta(days=WINDOW.lookback_days)
    pre_snapshot = summary.filter(pl.col("game_date") < pl.lit(snapshot_date))
    if pre_snapshot.is_empty():
        raise RuntimeError(f"no predictor evidence before Projection snapshot {snapshot_date}")
    observed_start = pre_snapshot.get_column("game_date").min()
    observed_end = pre_snapshot.get_column("game_date").max()
    source_left_censored = observed_start > requested_start
    missing_leading_calendar_days = max((observed_start - requested_start).days, 0)
    requested_window = pre_snapshot.filter(pl.col("game_date") >= pl.lit(requested_start))
    return {
        "requested_history_start": requested_start.isoformat(),
        "requested_history_end_exclusive": snapshot_date.isoformat(),
        "earliest_available_pre_snapshot_event": observed_start.isoformat(),
        "latest_available_pre_snapshot_event": observed_end.isoformat(),
        "source_left_censored_by_calendar": bool(source_left_censored),
        "leading_calendar_days_without_certified_source_surface": int(missing_leading_calendar_days),
        "available_player_game_rows_inside_requested_window": int(requested_window.height),
        "available_plate_appearances_inside_requested_window": int(
            requested_window.get_column("batting_plate_appearances").sum() or 0
        ),
        "frozen_b2_full_history_proven": not source_left_censored,
        "interpretation": (
            "Calendar censoring is a source-coverage diagnostic, not an assertion that baseball "
            "events actually occurred in every uncovered day. Any early fold that is not proven "
            "full-history must be adjudicated before Baseline-2 probabilities are materialized."
        ),
    }


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    season_summaries: list[pl.DataFrame] = []
    season_profiles: list[pl.DataFrame] = []
    source_reports: list[dict[str, Any]] = []
    for season in SOURCE_SEASONS:
        summary, profile, source_report = _load_one_season(args.input_root, season)
        season_summaries.append(summary)
        season_profiles.append(profile)
        source_reports.append(source_report)

    universal_summary, universal_profile, universal_metrics = combine_universal_player_game_evidence(
        season_summaries,
        season_profiles,
        expected_seasons=set(SOURCE_SEASONS),
        require_all_universal_leagues=True,
    )
    if set(universal_summary.get_column("season").unique().to_list()) != set(SOURCE_SEASONS):
        raise RuntimeError("Projection development source spans unexpected seasons")
    if universal_summary.filter(pl.col("game_date").dt.year() > 2024).height:
        raise RuntimeError("Projection development evidence accessed post-2024 events")

    fold_reports: list[dict[str, Any]] = []
    for fold in PROJECTION_V1_DEVELOPMENT_FOLDS:
        dataset = build_projection_snapshot_dataset(
            universal_summary,
            universal_profile,
            fold=fold,
            window=WINDOW,
        )
        fold_dir = table_root / fold.label
        fold_dir.mkdir(parents=True, exist_ok=True)
        storage = {
            "predictor_summary": write_canonical_parquet(
                dataset.predictor_summary,
                fold_dir / "predictor_summary.parquet",
                table_name=f"{fold.label}_predictor_summary",
            ).as_record(),
            "predictor_profile": write_canonical_parquet(
                dataset.predictor_profile,
                fold_dir / "predictor_profile.parquet",
                table_name=f"{fold.label}_predictor_profile",
            ).as_record(),
            "target_summary": write_canonical_parquet(
                dataset.target_summary,
                fold_dir / "target_summary.parquet",
                table_name=f"{fold.label}_target_summary",
            ).as_record(),
            "target_profile": write_canonical_parquet(
                dataset.target_profile,
                fold_dir / "target_profile.parquet",
                table_name=f"{fold.label}_target_profile",
            ).as_record(),
            "scoring_rows": write_canonical_parquet(
                dataset.scoring_rows,
                fold_dir / "scoring_rows.parquet",
                table_name=f"{fold.label}_scoring_rows",
            ).as_record(),
        }
        history = _history_coverage(universal_summary, snapshot_date=fold.snapshot_date)
        fold_reports.append(
            {
                "fold": fold.label,
                "snapshot_date": fold.snapshot_date.isoformat(),
                "target_start": fold.target_start.isoformat(),
                "target_end": fold.target_end.isoformat(),
                "history_coverage": history,
                "dataset_metrics": dataset.metrics,
                "storage": storage,
            }
        )

    report = {
        "report_schema_version": "0.1",
        "gate": "projection_batting_v1_development_evidence_pre_model",
        "source_seasons": list(SOURCE_SEASONS),
        "window": {
            "label": WINDOW.label,
            "lookback_days": WINDOW.lookback_days,
            "half_life_days": WINDOW.half_life_days,
        },
        "source_components": source_reports,
        "universal_source_metrics": universal_metrics,
        "folds": fold_reports,
        "history_extension_required_before_frozen_b2": any(
            not bool(row["history_coverage"]["frozen_b2_full_history_proven"])
            for row in fold_reports
        ),
        "boundary": {
            "accessed_2025": False,
            "baseline2_probabilities_materialized": False,
            "age_curve_fit": False,
            "projection_model_fit": False,
            "projection_predictions_computed": False,
            "log_loss_computed": False,
            "brier_computed": False,
            "calibration_computed": False,
            "promotion_decision_computed": False,
            "playing_time_modeled": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Projection batting v1 development evidence",
        "",
        f"- Universal player-games, 2021-2024: {universal_summary.height:,}",
        f"- Universal PA, 2021-2024: {universal_metrics['total_plate_appearances']:,}",
        "- 2025 accessed: False",
        "- Projection model fit/scored: False",
        "",
    ]
    for row in fold_reports:
        coverage = row["history_coverage"]
        metrics = row["dataset_metrics"]
        lines.extend(
            [
                f"## {row['fold']}",
                f"- Predictor players: {metrics['predictor_player_count']:,}",
                f"- Target players: {metrics['target_player_count']:,}",
                f"- Scored players: {metrics['scored_player_count']:,}",
                f"- Future PA: {metrics['future_plate_appearances']:,}",
                f"- Requested B2 history start: {coverage['requested_history_start']}",
                f"- Earliest certified event: {coverage['earliest_available_pre_snapshot_event']}",
                f"- Full frozen-B2 history proven: {coverage['frozen_b2_full_history_proven']}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
