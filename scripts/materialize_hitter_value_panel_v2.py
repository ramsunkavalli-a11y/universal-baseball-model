#!/usr/bin/env python3
"""Materialize a clean-slate hitter panel across every usable PBP season."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl

from universal_baseball.hitter_value_panel import (
    MODEL_ORIGINS,
    build_hitter_contact_features,
    build_hitter_stat_features,
    build_hitter_value_panel,
    build_neutral_mlb_value_targets,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


HISTORY_YEARS = (2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generated-root", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/hitter-value-panel-v2"),
    )
    return parser.parse_args()


def _load_stats(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    specifications = (
        (
            root
            / "affiliated-skill-source-2008-2017/tables/"
            "affiliated_hitting_components.parquet",
            (2015, 2016, 2017),
        ),
        (
            root
            / "affiliated-skill-source-2018-2022/tables/"
            "affiliated_hitting_components.parquet",
            (2018, 2019),
        ),
        (
            root
            / "phase2-arrival-skill-source/tables/"
            "affiliated_hitting_components.parquet",
            (2021, 2022, 2023, 2024, 2025),
        ),
    )
    frames = [
        pl.read_parquet(path).filter(pl.col("season").is_in(years))
        for path, years in specifications
    ]
    result = pl.concat(frames, how="vertical_relaxed")
    if set(result["season"].unique()) != set(HISTORY_YEARS):
        raise ValueError("affiliated batting statistics do not cover history years")
    return result, [path for path, _ in specifications]


def _load_contacts(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root
        / f"full-bip-context-{year}/tables/hitter_full_bip_event_outcomes.parquet"
        for year in HISTORY_YEARS
    ]
    result = pl.concat(
        [pl.read_parquet(path) for path in paths], how="diagonal_relaxed"
    )
    if set(result["season"].unique()) != set(HISTORY_YEARS):
        raise ValueError("contact events do not cover history years")
    return result, paths


def _load_ages(root: Path) -> tuple[pl.DataFrame, list[Path]]:
    paths = [
        root / f"hitter-multiyear-age-level-base/tables/annual-{year}.parquet"
        for year in HISTORY_YEARS
    ]
    frames = [
        pl.read_parquet(path)
        .select("player_id", "age", "relative_age", "age_missing")
        .with_columns(pl.lit(year).alias("season"))
        for year, path in zip(HISTORY_YEARS, paths, strict=True)
    ]
    return pl.concat(frames, how="vertical_relaxed"), paths


def main() -> int:
    args = _args()
    stats, stat_paths = _load_stats(args.generated_root)
    contacts, contact_paths = _load_contacts(args.generated_root)
    ages, age_paths = _load_ages(args.generated_root)
    mlb_path = (
        args.generated_root
        / "career-mlb-outcome-inventory-2009-2025/tables/"
        "mlb_hitting_components_2009_2025.parquet"
    )
    mlb = pl.read_parquet(mlb_path).filter(
        pl.col("season").is_between(min(HISTORY_YEARS), max(HISTORY_YEARS))
    )

    stat_features = build_hitter_stat_features(stats)
    contact_features = build_hitter_contact_features(contacts)
    value_targets = build_neutral_mlb_value_targets(mlb)
    panel = build_hitter_value_panel(
        stat_features,
        contact_features,
        ages,
        value_targets,
        origins=MODEL_ORIGINS,
    )
    if panel.filter(pl.col("target_season") >= 2026).height:
        raise RuntimeError("protected 2026 target entered the clean-slate panel")

    table_root = args.output_root / "tables"
    artifacts = {
        "stat_features": write_canonical_parquet(
            stat_features,
            table_root / "hitter-stat-features.parquet",
            table_name="hitter_value_v2_stat_features",
        ).as_record(),
        "contact_features": write_canonical_parquet(
            contact_features,
            table_root / "hitter-contact-features.parquet",
            table_name="hitter_value_v2_contact_features",
        ).as_record(),
        "value_targets": write_canonical_parquet(
            value_targets,
            table_root / "hitter-value-targets.parquet",
            table_name="hitter_value_v2_targets",
        ).as_record(),
        "modeling_panel": write_canonical_parquet(
            panel,
            table_root / "modeling-panel.parquet",
            table_name="hitter_value_v2_modeling_panel",
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
                "target_mlb_pa": int(frame["target_mlb_pa"].sum()),
                "target_component_war": float(frame["target_component_war"].sum()),
                "lag1_available": int((frame["lag1__missing"] == 0).sum()),
                "lag2_available": int((frame["lag2__missing"] == 0).sum()),
            }
        )
    source_paths = [*stat_paths, *contact_paths, *age_paths, mlb_path]
    report = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "clean_slate_hitter_value_panel_materialized",
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
            "primary": "next-season zero-inclusive MLB batting-plus-replacement WAR",
            "diagnostics": [
                "MLB active probability",
                "MLB plate appearances",
                "conditional batting-plus-replacement WAR per 600 PA",
            ],
            "excluded_for_now": ["defense", "baserunning", "positional adjustment"],
        },
        "counts": {
            "raw_contact_events": contacts.height,
            "stat_player_seasons": stat_features.height,
            "contact_player_seasons": contact_features.height,
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
