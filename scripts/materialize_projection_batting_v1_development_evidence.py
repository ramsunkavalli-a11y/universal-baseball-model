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

A central output is history-coverage accounting. Projection Baseline 0 must
reproduce the frozen Baseline-2 rule: current season plus prior *certified*
seasons where available, capped at 1,095 days and weighted with the frozen
180-day half-life. The certified universal B2 source epoch begins in 2021, so
calendar left-censoring before that epoch is reported but is not permission to
extend B2 into an unvalidated pre-2021 source era.
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
FROZEN_B2_CERTIFIED_SOURCE_START_SEASON = 2021
FROZEN_B2_HISTORY_POLICY = "current_plus_prior_certified_seasons_up_to_1095d_v1"
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

    observed_certified_seasons = sorted(
        int(value) for value in pre_snapshot.get_column("season").cast(pl.Int64).unique().to_list()
    )
    expected_certified_seasons = [
        int(season)
        for season in SOURCE_SEASONS
        if FROZEN_B2_CERTIFIED_SOURCE_START_SEASON <= int(season) <= int(snapshot_date.year)
    ]
    frozen_b2_certified_history_policy_satisfied = (
        observed_certified_seasons == expected_certified_seasons
    )
    if not frozen_b2_certified_history_policy_satisfied:
        raise RuntimeError(
            "Projection snapshot does not contain the expected frozen-B2 certified seasons: "
            f"snapshot={snapshot_date}, observed={observed_certified_seasons}, "
            f"expected={expected_certified_seasons}"
        )

    prior_certified_seasons = [
        season for season in observed_certified_seasons if season < int(snapshot_date.year)
    ]
    return {
        "history_policy": FROZEN_B2_HISTORY_POLICY,
        "certified_source_start_season": FROZEN_B2_CERTIFIED_SOURCE_START_SEASON,
        "requested_history_start": requested_start.isoformat(),
        "requested_history_end_exclusive": snapshot_date.isoformat(),
        "earliest_available_pre_snapshot_event": observed_start.isoformat(),
        "latest_available_pre_snapshot_event": observed_end.isoformat(),
        "calendar_max_lookback_fully_observed": not bool(source_left_censored),
        "source_left_censored_by_calendar": bool(source_left_censored),
        "leading_calendar_days_without_certified_source_surface": int(missing_leading_calendar_days),
        "observed_certified_seasons_before_snapshot": observed_certified_seasons,
        "expected_certified_seasons_through_snapshot": expected_certified_seasons,
        "prior_certified_seasons_before_snapshot": prior_certified_seasons,
        "prior_certified_season_count": len(prior_certified_seasons),
        "available_player_game_rows_inside_requested_window": int(requested_window.height),
        "available_plate_appearances_inside_requested_window": int(
            requested_window.get_column("batting_plate_appearances").sum() or 0
        ),
        "frozen_b2_certified_history_policy_satisfied": True,
        "pre_2021_backfill_authorized": False,
        "history_extension_required_for_frozen_b2_reproduction": False,
        "interpretation": (
            "The 1,095-day value is a maximum cap, not a requirement to invent or backfill "
            "uncertified pre-2021 evidence. Frozen B2 was developed and confirmed on the "
            "certified 2021-source-epoch bundle: current season plus prior certified seasons "
            "where available. Calendar left-censoring remains visible as a diagnostic."
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

    frozen_b2_history_contract_satisfied = all(
        bool(row["history_coverage"]["frozen_b2_certified_history_policy_satisfied"])
        for row in fold_reports
    )
    report = {
        "report_schema_version": "0.2",
        "gate": "projection_batting_v1_development_evidence_pre_model",
        "source_seasons": list(SOURCE_SEASONS),
        "window": {
            "label": WINDOW.label,
            "lookback_days": WINDOW.lookback_days,
            "half_life_days": WINDOW.half_life_days,
        },
        "frozen_b2_history_contract": {
            "policy": FROZEN_B2_HISTORY_POLICY,
            "certified_source_start_season": FROZEN_B2_CERTIFIED_SOURCE_START_SEASON,
            "satisfied": frozen_b2_history_contract_satisfied,
            "pre_2021_backfill_authorized": False,
            "history_extension_required_before_frozen_b2": False,
            "governing_record": "docs/projection-b2-history-reproduction-contract.md",
        },
        "source_components": source_reports,
        "universal_source_metrics": universal_metrics,
        "folds": fold_reports,
        "history_extension_required_before_frozen_b2": False,
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
        f"- Frozen B2 certified-history contract satisfied: {frozen_b2_history_contract_satisfied}",
        "- Pre-2021 backfill authorized: False",
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
                f"- Requested max-history start: {coverage['requested_history_start']}",
                f"- Earliest certified event: {coverage['earliest_available_pre_snapshot_event']}",
                f"- Certified seasons: {coverage['observed_certified_seasons_before_snapshot']}",
                f"- Prior certified seasons: {coverage['prior_certified_seasons_before_snapshot']}",
                f"- Calendar full 1,095-day span observed: {coverage['calendar_max_lookback_fully_observed']}",
                f"- Frozen B2 certified-history policy satisfied: {coverage['frozen_b2_certified_history_policy_satisfied']}",
                "",
            ]
        )
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
