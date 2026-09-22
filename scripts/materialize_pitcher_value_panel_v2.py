#!/usr/bin/env python3
"""Materialize a clean-slate pitcher panel across the full affiliated history."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.pitcher_value_panel import (
    MODEL_ORIGINS,
    build_neutral_mlb_pitcher_value_targets,
    build_pitcher_stat_features,
    build_pitcher_value_panel,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


HISTORY_YEARS = tuple(
    year for year in range(2007, 2026) if year != 2020
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/pitcher-value-panel-v2"),
    )
    return parser.parse_args()


def _load_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    specifications = (
        (
            root
            / "affiliated-skill-source-2003-2007/tables/"
            "affiliated_pitching_components.parquet",
            (2007,),
        ),
        (
            root
            / "affiliated-skill-source-2008-2017/tables/"
            "affiliated_pitching_components.parquet",
            tuple(range(2008, 2018)),
        ),
        (
            root
            / "affiliated-skill-source-2018-2022/tables/"
            "affiliated_pitching_components.parquet",
            (2018, 2019, 2021, 2022),
        ),
        (
            root
            / "affiliated-skill-source/tables/"
            "affiliated_pitching_components.parquet",
            (2023, 2024, 2025),
        ),
    )
    frames = [
        pl.read_parquet(path).filter(pl.col("season").is_in(years))
        for path, years in specifications
    ]
    result = pl.concat(frames, how="vertical_relaxed")
    if set(result["season"].unique()) != set(HISTORY_YEARS):
        raise ValueError("affiliated pitching statistics do not cover history years")
    return result, [path for path, _ in specifications]


def main() -> int:
    args = _args()
    stats, stat_paths = _load_stats(args.generated_root)
    mlb_path = (
        args.generated_root
        / "career-mlb-outcome-inventory-2009-2025/tables/"
        "mlb_pitching_2009_2025.parquet"
    )
    mlb = pl.read_parquet(mlb_path).filter(
        pl.col("season").is_between(min(MODEL_ORIGINS) + 1, 2025)
    )

    stat_features = build_pitcher_stat_features(stats)
    value_targets = build_neutral_mlb_pitcher_value_targets(mlb)
    panel = build_pitcher_value_panel(
        stat_features,
        value_targets,
        origins=MODEL_ORIGINS,
    )
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise RuntimeError("protected 2026 target entered the clean-slate panel")

    table_root = args.output_root / "tables"
    artifacts = {
        "stat_features": write_canonical_parquet(
            stat_features,
            table_root / "pitcher-stat-features.parquet",
            table_name="pitcher_value_v2_stat_features",
        ).as_record(),
        "value_targets": write_canonical_parquet(
            value_targets,
            table_root / "pitcher-value-targets.parquet",
            table_name="pitcher_value_v2_targets",
        ).as_record(),
        "modeling_panel": write_canonical_parquet(
            panel,
            table_root / "modeling-panel.parquet",
            table_name="pitcher_value_v2_modeling_panel",
        ).as_record(),
    }
    fold_population = []
    for origin, frame in panel.partition_by("origin_year", as_dict=True).items():
        year = int(origin[0])
        fold_population.append(
            {
                "origin_year": year,
                "target_year": year + 1,
                "players": frame.height,
                "target_mlb_active": int(frame["target_mlb_active"].sum()),
                "target_mlb_bf": int(frame["target_mlb_bf"].sum()),
                "target_component_war": float(frame["target_component_war"].sum()),
                "lag1_available": int((frame["lag1__missing"] == 0).sum()),
                "lag2_available": int((frame["lag2__missing"] == 0).sum()),
            }
        )
    source_paths = [*stat_paths, mlb_path]
    report = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "clean_slate_pitcher_value_panel_materialized",
        "history_years": list(HISTORY_YEARS),
        "development_origins": list(MODEL_ORIGINS),
        "development_targets": [year + 1 for year in MODEL_ORIGINS],
        "excluded_transitions": ["2019_to_2020", "2020_to_2021"],
        "structural_handling": {
            "2020": (
                "no synthetic MiLB season; exact lag-1 is missing for 2021 and "
                "2019 remains available as lag-2"
            ),
            "short_season_a": (
                "retained as A- in pre-reorganization level exposure; never mapped "
                "onto a modern level"
            ),
        },
        "target_contract": {
            "primary": "next-season zero-inclusive MLB pitcher component WAR",
            "diagnostics": [
                "MLB active probability",
                "MLB batters faced",
                "conditional pitcher component WAR per 800 BF",
            ],
            "included_events": ["strikeout", "unintentional walk", "HBP", "HR", "other BF"],
            "excluded_for_now": [
                "fielding-dependent contact detail",
                "pitch-process block",
                "future role",
                "future team",
            ],
        },
        "counts": {
            "raw_affiliated_rows": stats.height,
            "stat_player_seasons": stat_features.height,
            "modeling_rows": panel.height,
            "modeling_columns": panel.width,
        },
        "fold_population": sorted(fold_population, key=lambda row: row["origin_year"]),
        "sources": [
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
            for path in source_paths
        ],
        "artifacts": artifacts,
        "protected_2026_outcomes_used": False,
        "candidate_fit": False,
        "candidate_scored": False,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
