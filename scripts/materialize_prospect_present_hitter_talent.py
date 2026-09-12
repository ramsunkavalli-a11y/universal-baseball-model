#!/usr/bin/env python3
"""Materialize the partial-coverage, rate-only present hitter talent table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

from universal_baseball.chadwick import CHADWICK_SNAPSHOT_SHA, read_chadwick_people_archive
from universal_baseball.player_value_batting_runs import build_v1_mlb_batting_reference
from universal_baseball.prospect_hitter_talent import build_present_hitter_talent
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--current-talent-root",
        type=Path,
        default=Path("reports/generated/prospect-supported-hitter-current-talent/2024-10-15"),
    )
    parser.add_argument(
        "--performance-root",
        type=Path,
        default=Path("reports/generated/mlb-batting-performance-2024"),
    )
    parser.add_argument(
        "--chadwick-root",
        type=Path,
        default=Path("data/quarantine/prospect-supported-hitter-current-talent"),
    )
    parser.add_argument(
        "--external-audit",
        type=Path,
        default=Path("reports/generated/phase2-prospect-source/2026-09-08/fangraphs-top-100.parquet"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-present-hitter-talent/2024-10-15"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    table_root = args.output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)
    b2_profile = pl.read_parquet(
        args.current_talent_root / "tables/supported_frozen_b2_profile.parquet"
    )
    context = pl.read_parquet(
        args.current_talent_root / "tables/supported_player_context.parquet"
    )
    reference = build_v1_mlb_batting_reference(
        pl.read_parquet(args.performance_root / "tables/batting_performance_summary_2024_mlb.parquet"),
        pl.read_parquet(args.performance_root / "tables/batting_performance_bins_2024_mlb.parquet"),
        pl.read_parquet(args.performance_root / "tables/league_bin_values_2024_mlb.parquet"),
        season=2024,
    )
    register_path = args.chadwick_root / f"register-{CHADWICK_SNAPSHOT_SHA}.zip"
    people = read_chadwick_people_archive(register_path).filter(pl.col("key_mlbam").is_not_null())
    names = {
        int(row["key_mlbam"]): " ".join(
            part for part in (str(row["name_first"] or "").strip(), str(row["name_last"] or "").strip()) if part
        )
        for row in people.select("key_mlbam", "name_first", "name_last").iter_rows(named=True)
    }
    talent = build_present_hitter_talent(b2_profile, context, reference, names=names)

    # Publication ranks are attached after scoring for audit only. They never enter the score.
    if args.external_audit.exists():
        external = pl.read_parquet(args.external_audit).select(
            "player_id",
            pl.col("rank").alias("external_rank_audit_only"),
            pl.col("future_value").alias("external_fv_audit_only"),
        )
        talent = talent.join(external, on="player_id", how="left")

    storage = write_canonical_parquet(
        talent,
        table_root / "present_hitter_talent.parquet",
        table_name="prospect_present_hitter_talent_partial_2024",
    ).as_record()
    talent.write_csv(table_root / "present_hitter_talent.csv")
    ranked = talent.filter(pl.col("ranking_status") == "ranked")
    external_supported = talent.filter(
        pl.col("external_rank_audit_only").is_not_null()
        & (pl.col("ranking_status") == "ranked")
    ) if "external_rank_audit_only" in talent.columns else pl.DataFrame()
    report = {
        "report_schema_version": "0.1",
        "status": "diagnostic_partial_coverage_not_future_ceiling",
        "as_of_date": "2024-10-15",
        "player_count": talent.height,
        "ranked_player_count": ranked.height,
        "unresolved_player_count": talent.height - ranked.height,
        "external_top100_supported_count": external_supported.height,
        "storage": storage,
        "score_includes": [
            "translated current batting component profile",
            "recency weighting",
            "empirical-Bayes regression",
            "MLB-neutral RE24 rate conversion",
        ],
        "score_excludes": [
            "playing time", "position", "defense", "running", "age projection",
            "arrival", "public rank or FV", "contract", "replacement runs",
        ],
        "limitations": [
            "Rookie/complex evidence is not included.",
            "Historical 2021-2023 MLB evidence is not included.",
            "This estimates present batting skill, not future prospect ceiling.",
            "Pitchers require a separate component model.",
        ],
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "status", "player_count", "ranked_player_count", "unresolved_player_count",
        "external_top100_supported_count",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
