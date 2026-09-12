#!/usr/bin/env python3
"""Fit simple MLB-anchored component translations from affiliated movers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.level_component_translation import (
    fit_same_season_component_translation,
)
from universal_baseball.storage import write_canonical_parquet


HITTER_COMPONENTS = ("so", "ubb", "hbp", "single", "double", "triple", "hr", "other")
PITCHER_COMPONENTS = ("so", "ubb", "hbp", "hr", "other")


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-root", type=Path,
        default=Path("reports/generated/affiliated-skill-source/tables"),
    )
    parser.add_argument("--completed-seasons", default="2023,2024,2025")
    parser.add_argument("--minimum-exposure", type=int, default=30)
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/affiliated-level-translations"),
    )
    return parser.parse_args()


def _seasons(raw: str) -> tuple[int, ...]:
    return tuple(sorted({int(value.strip()) for value in raw.split(",") if value.strip()}))


def _hitter_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        (pl.col("hits") - pl.col("doubles") - pl.col("triples") - pl.col("home_runs")).alias("single"),
        pl.col("doubles").alias("double"), pl.col("triples").alias("triple"),
        pl.col("home_runs").alias("hr"), pl.col("hit_by_pitch").alias("hbp"),
    ).with_columns(
        (pl.col("plate_appearances") - pl.sum_horizontal(*HITTER_COMPONENTS[:-1])).alias("other")
    )


def _pitcher_components(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(
        pl.col("strike_outs").alias("so"),
        (pl.col("base_on_balls") - pl.col("intentional_walks")).alias("ubb"),
        pl.col("hit_batters").alias("hbp"), pl.col("home_runs").alias("hr"),
    ).with_columns(
        (pl.col("batters_faced") - pl.sum_horizontal(*PITCHER_COMPONENTS[:-1])).alias("other")
    )


def main() -> int:
    args = _args()
    seasons = _seasons(args.completed_seasons)
    if not seasons:
        raise ValueError("completed-seasons must not be empty")
    hitters = _hitter_components(
        pl.read_parquet(args.source_root / "affiliated_hitting_components.parquet")
    )
    pitchers = _pitcher_components(
        pl.read_parquet(args.source_root / "affiliated_pitching_components.parquet")
    )
    hitter_fit = fit_same_season_component_translation(
        hitters, exposure_column="plate_appearances", component_columns=HITTER_COMPONENTS,
        completed_seasons=seasons, minimum_level_exposure=args.minimum_exposure,
    )
    pitcher_fit = fit_same_season_component_translation(
        pitchers, exposure_column="batters_faced", component_columns=PITCHER_COMPONENTS,
        completed_seasons=seasons, minimum_level_exposure=args.minimum_exposure,
    )
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "hitter": write_canonical_parquet(
            hitter_fit.offsets, tables / "hitter_level_offsets.parquet",
            table_name="hitter_level_component_offsets",
        ).as_record(),
        "pitcher": write_canonical_parquet(
            pitcher_fit.offsets, tables / "pitcher_level_offsets.parquet",
            table_name="pitcher_level_component_offsets",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "same_player_same_season_affiliated_level_translation",
        "completed_seasons": list(seasons),
        "future_or_current_incomplete_target_used": False,
        "hitter": hitter_fit.metrics,
        "pitcher": pitcher_fit.metrics,
        "limitations": [
            "Mover selection can still differ from the full player population.",
            "Level groups pool individual leagues and parks for the Phase 1 baseline.",
            "Offsets are a skill-input translation, not an MLB-arrival forecast.",
        ],
        "storage": storage,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "hitter": report["hitter"], "pitcher": report["pitcher"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
