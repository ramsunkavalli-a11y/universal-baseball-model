#!/usr/bin/env python3
"""Materialize the fixed Playing Time v1 predictor matrix at 2024-10-15.

Consumes certified 2024 evidence, the frozen confirmation B2 snapshot, and
certified binary 40-man membership. No 2025 outcomes are read.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from materialize_playing_time_v1_predictor_surface import _b2_ilr, _season_pa
from materialize_projection_batting_v1_development_evidence import _load_one_season
from universal_baseball.playing_time_model import PT_FORM_B0, PT_FORM_C, build_playing_time_design
from universal_baseball.projection_validation import PROJECTION_V1_CONFIRMATION_FOLD
from universal_baseball.storage import write_canonical_parquet


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--snapshot-root", type=Path, required=True)
    parser.add_argument("--membership-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/playing-time-v1-confirmation-predictors"),
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
    table_root = args.output_root / "tables" / PROJECTION_V1_CONFIRMATION_FOLD.label
    table_root.mkdir(parents=True, exist_ok=True)

    summary, _profile, source_report = _load_one_season(args.evidence_root, 2024)
    current_summary = summary.with_columns(
        pl.col("game_date").cast(pl.String).str.to_date(strict=False).alias("_date")
    ).filter(pl.col("_date") < pl.lit(PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date))
    current_pa = _season_pa(current_summary, prefix="current_season")

    snapshot_fold_root = args.snapshot_root / "tables" / PROJECTION_V1_CONFIRMATION_FOLD.label
    context = pl.read_parquet(
        _one(snapshot_fold_root, "player_context.parquet", "confirmation player context")
    )
    b2_profile = pl.read_parquet(
        _one(snapshot_fold_root, "frozen_b2_profile.parquet", "confirmation frozen B2 profile")
    )
    ilr = _b2_ilr(b2_profile)

    membership = pl.read_parquet(
        _one(args.membership_root, "confirmation_40man_membership.parquet", "confirmation 40-man membership")
    )
    if membership.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("confirmation 40-man membership violates player grain")
    membership = membership.select(
        "player_id",
        pl.col("team_id").alias("forty_man_team_id"),
        "on_40man",
        "source_row_count",
        "source_status_conflict",
    )

    predictors = (
        context.join(current_pa, on="player_id", how="left")
        .join(ilr, on="player_id", how="left")
        .join(membership, on="player_id", how="left")
        .with_columns(
            pl.col("current_season_affiliated_pa").fill_null(0).cast(pl.Int64),
            pl.col("current_season_mlb_pa").fill_null(0).cast(pl.Int64),
            pl.col("current_season_milb_pa").fill_null(0).cast(pl.Int64),
            pl.col("current_season_affiliated_games").fill_null(0).cast(pl.Int64),
            pl.col("on_40man").fill_null(False).cast(pl.Boolean),
            pl.col("source_row_count").fill_null(0).cast(pl.Int64),
            pl.col("source_status_conflict").fill_null(False).cast(pl.Boolean),
        )
        .sort("player_id")
    )

    if predictors.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise RuntimeError("confirmation predictor surface violates player grain")
    if predictors.filter(pl.col("age_years").is_null() | pl.col("as_of_level_group").is_null()).height:
        raise RuntimeError("confirmation predictor surface has missing age/level")
    if predictors.filter(pl.col("current_season_affiliated_pa") <= 0).height:
        raise RuntimeError("confirmation snapshot player lacks positive pre-snapshot 2024 PA")
    if predictors.select(pl.col("b2_ilr_00").is_null().sum()).item() != 0:
        raise RuntimeError("confirmation predictor surface lacks frozen B2 state")

    # Fail closed against the exact frozen design contracts before any 2025 target exists.
    b0_design = build_playing_time_design(predictors, form=PT_FORM_B0)
    candidate_design = build_playing_time_design(predictors, form=PT_FORM_C)
    if b0_design.height != predictors.height or candidate_design.height != predictors.height:
        raise RuntimeError("confirmation design coverage differs from predictor surface")

    storage = write_canonical_parquet(
        predictors,
        table_root / "predictors.parquet",
        table_name="playing_time_v1_2024_10_15_confirmation_predictors",
    ).as_record()
    by_level = (
        predictors.group_by("as_of_level_group")
        .agg(
            pl.len().cast(pl.Int64).alias("players"),
            pl.col("on_40man").sum().cast(pl.Int64).alias("on_40man_players"),
            (pl.col("current_season_mlb_pa") > 0).sum().cast(pl.Int64).alias("players_with_current_mlb_pa"),
        )
        .sort("as_of_level_group")
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "playing_time_v1_confirmation_predictors_pre_2025_outcomes",
        "fold": PROJECTION_V1_CONFIRMATION_FOLD.label,
        "snapshot_date": PROJECTION_V1_CONFIRMATION_FOLD.snapshot_date.isoformat(),
        "source_component": source_report,
        "player_count": int(predictors.height),
        "on_40man_player_count": int(predictors.get_column("on_40man").sum()),
        "players_with_current_mlb_pa": int((predictors.get_column("current_season_mlb_pa") > 0).sum()),
        "by_as_of_level": by_level.to_dicts(),
        "design_contracts": {
            "baseline0_form": PT_FORM_B0,
            "candidate_form": PT_FORM_C,
            "baseline0_rows": int(b0_design.height),
            "candidate_rows": int(candidate_design.height),
        },
        "storage": storage,
        "boundary": {
            "2025_outcomes_accessed": False,
            "2025_target_materialized": False,
            "future_team_used": False,
            "future_level_used": False,
            "player_identity_used_as_predictor": False,
            "batting_rate_modified": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Playing-time v1 confirmation predictors",
        "",
        f"- Snapshot players: {predictors.height:,}",
        f"- On 40-man: {int(predictors.get_column('on_40man').sum()):,}",
        f"- Current MLB PA > 0: {int((predictors.get_column('current_season_mlb_pa') > 0).sum()):,}",
        "- Frozen B0/C design contracts: PASS",
        "- 2025 outcomes accessed: False",
        "",
    ]
    (args.output_root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
