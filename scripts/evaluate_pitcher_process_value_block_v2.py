#!/usr/bin/env python3
"""Test the validated high-minors pitch-process block on whole pitcher value."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import polars as pl

from universal_baseball.certification import download_file
from universal_baseball.hitter_target_architecture import (
    expanding_year_folds,
    paired_cluster_rmse_delta,
    regression_metrics,
)
from universal_baseball.pitcher_model_tournament import run_pitcher_engine_fold
from universal_baseball.pitcher_process_value import (
    add_neutral_process_features,
    build_pitcher_process_features,
)
from universal_baseball.pitcher_value_panel import MODEL_ORIGINS, build_pitcher_value_panel
from universal_baseball.storage import write_canonical_parquet


YEARS = (2018, 2019, 2021, 2022, 2023, 2024)
LEVELS = ("aaa", "aa", "a+", "a")
LEVEL_GROUP = {"aaa": "AAA", "aa": "AA", "a+": "HIGH_A", "a": "SINGLE_A"}
BASE_URL = (
    "https://github.com/armstjc/milb-data-repository/releases/download/"
    "season_player_pitching"
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-panel-root",
        type=Path,
        default=Path("reports/generated/pitcher-value-panel-v2"),
    )
    parser.add_argument(
        "--cache-root",
        type=Path,
        default=Path("data/quarantine/pitcher-process-season"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-process-value-block-v2"),
    )
    parser.add_argument("--engines", default="ridge,catboost,lightgbm")
    return parser.parse_args()


def _load_process(cache_root: Path) -> tuple[pl.DataFrame, list[Path]]:
    frames: list[pl.DataFrame] = []
    paths: list[Path] = []
    cache_root.mkdir(parents=True, exist_ok=True)
    for year in YEARS:
        for slug in LEVELS:
            name = f"{year}_{slug}_season_pitching_stats.csv"
            path = cache_root / name
            if not path.exists():
                download_file(f"{BASE_URL}/{name}", path, timeout_seconds=120)
            raw = pl.read_csv(path, infer_schema_length=10_000, ignore_errors=False)
            frames.append(
                raw.select(
                    pl.col("season").cast(pl.Int64),
                    pl.col("player_id").cast(pl.Int64),
                    pl.lit(LEVEL_GROUP[slug]).alias("level_group"),
                    pl.col("pitching_BF").cast(pl.Float64).alias("bf"),
                    pl.col("pitching_PI").cast(pl.Float64).alias("pitches"),
                    pl.col("pitching_total_swings").cast(pl.Float64).alias("swings"),
                    pl.col("pitching_swing_and_misses").cast(pl.Float64).alias("whiffs"),
                    pl.col("pitching_PI_strikes").cast(pl.Float64).alias("strikes"),
                    pl.col("pitching_PI_balls").cast(pl.Float64).alias("balls"),
                )
            )
            paths.append(path)
    return pl.concat(frames, how="vertical_relaxed"), paths


def _score(panel: pl.DataFrame, engine: str) -> pl.DataFrame:
    folds = expanding_year_folds(
        panel["origin_year"].unique().to_list(), minimum_train_years=8
    )
    return pl.concat(
        [run_pitcher_engine_fold(panel, fold, engine)[0] for fold in folds]
    ).sort("origin_year", "player_id")


def _metrics(frame: pl.DataFrame, prediction: str) -> dict[str, float]:
    return regression_metrics(
        frame["actual_component_war"].to_numpy(), frame[prediction].to_numpy()
    )


def main() -> int:
    args = _args()
    stat_features = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-stat-features.parquet"
    )
    targets = pl.read_parquet(
        args.base_panel_root / "tables/pitcher-value-targets.parquet"
    )
    process, source_paths = _load_process(args.cache_root)
    process_features = build_pitcher_process_features(process)
    detailed_features = add_neutral_process_features(stat_features, process_features)
    base_panel = build_pitcher_value_panel(stat_features, targets, origins=MODEL_ORIGINS)
    process_panel = build_pitcher_value_panel(
        detailed_features, targets, origins=MODEL_ORIGINS
    )

    args.output_root.mkdir(parents=True, exist_ok=True)
    table_root = args.output_root / "tables"
    report: dict[str, Any] = {
        "schema_version": "0.1",
        "status": "pitcher_process_value_block_complete",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "protected_2026_outcomes_used": False,
        "target": "next-season zero-inclusive defense-independent pitcher component WAR",
        "feature_block": [
            "regressed level-relative whiffs per swing",
            "strikes per pitch",
            "swings per pitch",
            "pitches per batter faced",
        ],
        "source_years": list(YEARS),
        "source_files": len(source_paths),
        "process_player_seasons": process_features.height,
        "engines": {},
    }
    engines = [value.strip() for value in args.engines.split(",") if value.strip()]
    for engine in engines:
        print(f"starting process-value engine {engine}", flush=True)
        base = _score(base_panel, engine)
        candidate = _score(process_panel, engine)
        comparison = base.select(
            "origin_year",
            "target_season",
            "player_id",
            "actual_component_war",
            "active_probability",
            pl.col("predicted_component_war").alias("prediction_base"),
        ).join(
            candidate.select(
                "origin_year",
                "target_season",
                "player_id",
                pl.col("predicted_conditional_war").alias(
                    "process_conditional_war"
                ),
                pl.col("predicted_component_war").alias("prediction_process"),
            ),
            on=["origin_year", "target_season", "player_id"],
            validate="1:1",
        ).with_columns(
            (pl.col("active_probability") * pl.col("process_conditional_war")).alias(
                "prediction_process_conditional_only"
            )
        ).join(
            process_panel.select(
                "origin_year",
                "player_id",
                pl.col("lag0__process_available").alias("process_available"),
            ),
            on=["origin_year", "player_id"],
            validate="1:1",
        )
        modern = comparison.filter(pl.col("origin_year").is_in([2021, 2022, 2023, 2024]))
        covered = modern.filter(pl.col("process_available") == 1)
        actual = modern["actual_component_war"].to_numpy()
        report["engines"][engine] = {
            "modern_all": {
                "players": modern.height,
                "base": _metrics(modern, "prediction_base"),
                "process": _metrics(modern, "prediction_process"),
                "process_conditional_only": _metrics(
                    modern, "prediction_process_conditional_only"
                ),
                "process_minus_base": paired_cluster_rmse_delta(
                    actual,
                    modern["prediction_process"].to_numpy(),
                    modern["prediction_base"].to_numpy(),
                    modern["player_id"].to_numpy(),
                    bootstrap_samples=5_000,
                ),
                "process_conditional_only_minus_base": paired_cluster_rmse_delta(
                    actual,
                    modern["prediction_process_conditional_only"].to_numpy(),
                    modern["prediction_base"].to_numpy(),
                    modern["player_id"].to_numpy(),
                    bootstrap_samples=5_000,
                ),
            },
            "covered_current_process": {
                "players": covered.height,
                "base": _metrics(covered, "prediction_base"),
                "process": _metrics(covered, "prediction_process"),
                "process_conditional_only": _metrics(
                    covered, "prediction_process_conditional_only"
                ),
            },
            "folds": [
                {
                    "origin_year": int(origin[0]),
                    "base_rmse": _metrics(fold, "prediction_base")["rmse"],
                    "process_rmse": _metrics(fold, "prediction_process")["rmse"],
                    "process_conditional_only_rmse": _metrics(
                        fold, "prediction_process_conditional_only"
                    )["rmse"],
                    "covered": int(fold["process_available"].sum()),
                }
                for origin, fold in modern.partition_by("origin_year", as_dict=True).items()
            ],
        }
        write_canonical_parquet(
            comparison,
            table_root / f"{engine}-predictions.parquet",
            table_name=f"pitcher_process_value_v2_{engine}_predictions",
        )
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["engines"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
