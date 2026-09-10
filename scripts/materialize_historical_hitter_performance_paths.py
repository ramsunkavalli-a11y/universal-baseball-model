#!/usr/bin/env python3
"""Build linked historical hitter workload and component-performance paths."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)
from universal_baseball.mlb_season_stats import (
    MLB_BATTING_BACKBONE_SCHEMA,
    project_mlb_hitting_splits,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _load_hitting_captures(report_path: Path) -> tuple[pl.DataFrame, list[Path]]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    frames = []
    paths = []
    for capture in report["captures"]:
        if capture["group"] != "hitting":
            continue
        path = Path(capture["raw_path"])
        if sha256_file(path) != capture["response_sha256"]:
            raise ValueError(f"historical hitting capture hash mismatch: {path}")
        payload = json.loads(path.read_bytes())
        stats = payload.get("stats") or []
        if len(stats) != 1:
            raise ValueError(f"historical hitting capture has invalid stats body: {path}")
        frames.append(
            project_mlb_hitting_splits(
                stats[0].get("splits") or [],
                season=int(capture["season"]),
                league_id=int(capture["league_id"]),
            )
        )
        paths.append(path)
    if not frames:
        raise ValueError("historical inventory contains no hitting captures")
    source = pl.concat(frames, how="vertical")
    count_columns = [
        column
        for column, dtype in MLB_BATTING_BACKBONE_SCHEMA.items()
        if dtype == pl.Int64 and column not in {"season", "league_id", "player_id"}
    ]
    hitting = (
        source.group_by("season", "player_id")
        .agg(
            pl.col("player_name").filter(pl.col("player_name") != "").first(),
            *(pl.col(column).sum().alias(column) for column in count_columns),
        )
        .sort("season", "player_id")
    )
    return hitting, paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--annual-paths",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-annual-workload-paths.parquet"
        ),
    )
    parser.add_argument(
        "--inventory-report",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/report.json"
        ),
    )
    parser.add_argument(
        "--conditional-report",
        type=Path,
        default=Path(
            "reports/generated/phase2-conditional-war-paths/2026-09-08/report.json"
        ),
    )
    parser.add_argument(
        "--hitting-output",
        type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_hitting_components_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--path-output",
        type=Path,
        default=Path(
            "reports/generated/prospect-outcome-quality-2009-2025/"
            "post-debut-hitter-performance-paths.parquet"
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/historical-hitter-performance-paths-result.json"),
    )
    args = parser.parse_args()
    reference = json.loads(args.conditional_report.read_text(encoding="utf-8"))[
        "reference_environment"
    ]
    hitting, capture_paths = _load_hitting_captures(args.inventory_report)
    hitting_storage = write_canonical_parquet(
        hitting,
        args.hitting_output,
        table_name="historical_mlb_hitting_components",
    ).as_record()
    paths = build_historical_hitter_performance_paths(
        pl.read_parquet(args.annual_paths),
        hitting,
        runs_per_win=float(reference["runs_per_win"]),
    )
    path_storage = write_canonical_parquet(
        paths,
        args.path_output,
        table_name="historical_hitter_component_performance_paths",
    ).as_record()
    careers = paths.group_by("path_player_id", "outcome_tier_v2").agg(
        pl.col("observed_component_war").sum().alias("six_year_component_war"),
        pl.col("adjusted_workload").sum().alias("six_year_pa"),
    )
    report = {
        "report_schema_version": 1,
        "status": "linked_hitter_performance_path_source_ready_not_model_promoted",
        "players": careers.height,
        "annual_rows": paths.height,
        "active_rows": paths.filter(pl.col("adjusted_workload") > 0).height,
        "source_seasons": [
            int(paths["source_season"].min()),
            int(paths["source_season"].max()),
        ],
        "by_tier": careers.group_by("outcome_tier_v2")
        .agg(
            pl.len().alias("players"),
            pl.col("six_year_pa").mean().alias("mean_six_year_pa"),
            pl.col("six_year_component_war")
            .mean()
            .alias("mean_six_year_component_war"),
            pl.col("six_year_component_war")
            .median()
            .alias("median_six_year_component_war"),
        )
        .sort("outcome_tier_v2")
        .to_dicts(),
        "method": (
            "annual league-relative neutral-wOBA batting runs plus replacement; "
            "intentional walks restored from original hashed StatsAPI captures and "
            "2020 workload adjusted"
        ),
        "excluded_components": ["baserunning", "defense", "position"],
        "model_effect": "none",
        "sources": {
            args.annual_paths.as_posix(): sha256_file(args.annual_paths),
            args.inventory_report.as_posix(): sha256_file(args.inventory_report),
            args.conditional_report.as_posix(): sha256_file(args.conditional_report),
            **{path.as_posix(): sha256_file(path) for path in capture_paths},
        },
        "storage": {"hitting": hitting_storage, "paths": path_storage},
    }
    args.report.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "sources"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
