#!/usr/bin/env python3
"""Materialize the untouched 2025 MLB-PA target for Playing Time v1.

This is the first authorized Playing Time v1 access to 2025 outcomes. It does
not load model parameters, compute predictions, or compare candidate scores.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.mlb_season_stats import MLB_LEAGUE_IDS, fetch_mlb_hitting_backbone
from universal_baseball.storage import write_canonical_parquet


CONFIRMATION_SEASON = 2025
CONFIRMATION_FOLD = "projection_2024_to_2025_confirmation"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirmation-input-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-confirmation-target-2025"),
    )
    parser.add_argument(
        "--capture-root",
        type=Path,
        default=Path("data/quarantine/playing-time-v1-confirmation-target-2025"),
    )
    return parser.parse_args()


def _one(root: Path, filename: str, label: str) -> Path:
    matches = sorted(path for path in root.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label} named {filename}, found {len(matches)}: {matches}")
    return matches[0]


def _capture_records(captures, capture_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for capture in captures:
        path = capture_root / f"league_{capture.league_id}" / f"offset_{capture.offset}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(capture.response_bytes)
        records.append(
            {
                "season": int(capture.season),
                "league_id": int(capture.league_id),
                "offset": int(capture.offset),
                "requested_limit": int(capture.requested_limit),
                "returned_split_count": int(capture.returned_split_count),
                "total_splits": int(capture.total_splits) if capture.total_splits is not None else None,
                "response_sha256": capture.response_sha256,
                "response_byte_count": len(capture.response_bytes),
                "capture_path": str(path),
            }
        )
    return records


def _validate_complete_pagination(capture_records: list[dict[str, object]]) -> dict[str, object]:
    by_league: dict[int, list[dict[str, object]]] = {}
    for record in capture_records:
        by_league.setdefault(int(record["league_id"]), []).append(record)
    if set(by_league) != set(MLB_LEAGUE_IDS):
        raise RuntimeError(f"2025 target source did not return both MLB leagues: {sorted(by_league)}")

    diagnostics: dict[str, object] = {}
    for league_id in MLB_LEAGUE_IDS:
        rows = sorted(by_league[int(league_id)], key=lambda row: int(row["offset"]))
        if not rows or int(rows[0]["offset"]) != 0:
            raise RuntimeError(f"2025 target league {league_id} pagination does not start at zero")
        returned = sum(int(row["returned_split_count"]) for row in rows)
        totals = {int(row["total_splits"]) for row in rows if row["total_splits"] is not None}
        if len(totals) > 1:
            raise RuntimeError(f"2025 target league {league_id} changed totalSplits across pages: {totals}")
        expected = next(iter(totals)) if totals else None
        if expected is not None and returned != expected:
            raise RuntimeError(
                f"2025 target league {league_id} pagination incomplete: returned={returned}, expected={expected}"
            )
        diagnostics[str(league_id)] = {
            "page_count": len(rows),
            "returned_split_count": returned,
            "reported_total_splits": expected,
            "complete": expected is None or returned == expected,
        }
    return diagnostics


def main() -> int:
    args = _parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    args.capture_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables" / CONFIRMATION_FOLD
    table_root.mkdir(parents=True, exist_ok=True)

    predictors = pl.read_parquet(
        _one(args.confirmation_input_root, "predictors.parquet", "frozen confirmation predictors")
    ).select("player_id")
    if predictors.is_empty():
        raise RuntimeError("confirmation predictor population is empty")
    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("confirmation predictor population violates player grain")

    backbone, captures = fetch_mlb_hitting_backbone(CONFIRMATION_SEASON)
    capture_records = _capture_records(captures, args.capture_root)
    pagination = _validate_complete_pagination(capture_records)

    if backbone.is_empty():
        raise RuntimeError("2025 MLB hitting backbone is empty")
    if set(int(value) for value in backbone.get_column("season").unique().to_list()) != {CONFIRMATION_SEASON}:
        raise RuntimeError("2025 MLB hitting backbone contains another season")
    if set(int(value) for value in backbone.get_column("league_id").unique().to_list()) != set(MLB_LEAGUE_IDS):
        raise RuntimeError("2025 MLB hitting backbone does not contain both actual MLB leagues")
    if backbone.group_by(["season", "league_id", "player_id"]).len().filter(pl.col("len") != 1).height:
        raise RuntimeError("2025 MLB hitting backbone violates player-league-season grain")
    if backbone.filter(pl.col("batting_plate_appearances") < 0).height:
        raise RuntimeError("2025 MLB hitting backbone contains negative PA")

    observed = (
        backbone.group_by("player_id")
        .agg(pl.col("batting_plate_appearances").sum().cast(pl.Int64).alias("next_year_mlb_pa"))
        .sort("player_id")
    )
    targets = (
        predictors.join(observed, on="player_id", how="left")
        .with_columns(pl.col("next_year_mlb_pa").fill_null(0).cast(pl.Int64))
        .sort("player_id")
    )
    if targets.height != predictors.height:
        raise RuntimeError("2025 confirmation target coverage differs from frozen predictor population")
    if targets.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("2025 confirmation target violates player grain")
    if targets.filter(pl.col("next_year_mlb_pa") < 0).height:
        raise RuntimeError("2025 confirmation target contains negative MLB PA")

    storage = write_canonical_parquet(
        targets,
        table_root / "next_year_mlb_pa_targets.parquet",
        table_name="playing_time_v1_2025_confirmation_mlb_pa_targets",
    ).as_record()
    positive = targets.filter(pl.col("next_year_mlb_pa") > 0)
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_2025_confirmation_target_source",
        "status": "source_certified_target_materialized_unscored",
        "season": CONFIRMATION_SEASON,
        "fold": CONFIRMATION_FOLD,
        "source": "official_mlb_stats_api_bulk_regular_season_hitting",
        "source_contract": {
            "stats": "season",
            "group": "hitting",
            "sportIds": 1,
            "league_ids": list(MLB_LEAGUE_IDS),
            "playerPool": "ALL",
            "gameType": "R",
        },
        "source_capture_records": capture_records,
        "pagination": pagination,
        "source_player_league_rows": int(backbone.height),
        "source_unique_players": int(backbone.get_column("player_id").n_unique()),
        "source_total_mlb_pa": int(backbone.get_column("batting_plate_appearances").sum()),
        "target_player_count": int(targets.height),
        "target_positive_player_count": int(positive.height),
        "target_zero_player_count": int(targets.height - positive.height),
        "target_positive_rate": float(positive.height / targets.height),
        "target_positive_mean_mlb_pa": float(positive.get_column("next_year_mlb_pa").mean()) if positive.height else 0.0,
        "target_total_mlb_pa": int(targets.get_column("next_year_mlb_pa").sum()),
        "storage": storage,
        "boundary": {
            "2025_outcomes_accessed": True,
            "2025_target_materialized": True,
            "model_parameters_loaded": False,
            "model_predictions_computed": False,
            "candidate_vs_baseline_scores_computed": False,
            "model_refit": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 — untouched 2025 confirmation target",
        "",
        f"- Frozen snapshot players: {targets.height:,}",
        f"- Players with 2025 MLB PA > 0: {positive.height:,}",
        f"- Zero-MLB-PA players: {targets.height - positive.height:,}",
        f"- Target total MLB PA: {int(targets.get_column('next_year_mlb_pa').sum()):,}",
        "- Source capture hashes persisted: True",
        "- Model parameters loaded: False",
        "- Candidate/B0 scores computed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
