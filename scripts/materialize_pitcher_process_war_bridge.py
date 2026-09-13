#!/usr/bin/env python3
"""Apply the validated next-year pitch-process delta to current pitcher WAR paths."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from materialize_current_conditional_war_paths import (
    _pitcher_process_next_year_profiles,
)
from universal_baseball.conditional_war_rates import (
    apply_pitcher_next_year_profiles_to_rate_table,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--conditional-root",
        type=Path,
        default=Path("reports/generated/phase2-conditional-war-paths"),
    )
    parser.add_argument(
        "--base-root",
        type=Path,
        default=Path("reports/generated/phase2-conditional-war-paths-no-pitcher-demo"),
        help="Immutable results-only rate baseline; keeps repeated bridge runs idempotent.",
    )
    parser.add_argument(
        "--opportunity-root",
        type=Path,
        default=Path("reports/generated/phase2-workload-paths"),
    )
    parser.add_argument(
        "--control-path",
        type=Path,
        default=Path("reports/generated/league-control/2026-09-08/future-control-path.parquet"),
    )
    parser.add_argument(
        "--current-basic-root",
        type=Path,
        default=Path("reports/generated/current-basic-talent/2026-09-08/tables"),
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=Path("model_artifacts/pitcher-next-year-process-v1.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.conditional_root / dated
    tables = root / "tables"
    base_tables = args.base_root / dated / "tables"
    report_path = root / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    profiles = _pitcher_process_next_year_profiles(
        args.current_basic_root / "current_pitcher_talent.parquet",
        args.artifact,
        current_season=args.as_of_date.year,
    )
    if profiles is None:
        raise ValueError("validated pitcher process artifact is unavailable")
    rates_path = tables / "pitcher_conditional_war_rates.parquet"
    paths_path = tables / "pitcher_expected_war_paths.parquet"
    old_rates = pl.read_parquet(base_tables / "pitcher_conditional_war_rates.parquet")
    rates = apply_pitcher_next_year_profiles_to_rate_table(
        old_rates,
        profiles,
        current_season=args.as_of_date.year,
        runs_per_win=float(report["reference_environment"]["runs_per_win"]),
    )
    opportunity = pl.read_parquet(
        args.opportunity_root / dated / "tables/pitcher_opportunity_paths.parquet"
    )
    control = pl.read_parquet(args.control_path).select(
        "player_id", pl.col("control_year").alias("season"), "control_status"
    ).with_columns(
        (~pl.col("control_status").is_in(
            ["free_agent", "free_agent_eligible"]
        )).alias("is_controlled_season")
    )
    rate_columns = [
        column for column in rates.columns if column not in {"player_id", "season"}
    ]
    paths = (
        opportunity.drop(*[
            column for column in rate_columns if column in opportunity.columns
        ])
        .join(rates, on=["player_id", "season"], how="inner", validate="1:1")
        .with_columns(
            (
                pl.col("mlb_active_probability")
                * pl.col("conditional_mlb_bf")
                * pl.col("conditional_war_per_800_bf") / 800.0
            ).alias("expected_war")
        )
        .join(control, on=["player_id", "season"], how="left")
        .with_columns(
            pl.when(pl.col("control_status").is_null())
            .then(pl.lit("missing"))
            .otherwise(pl.lit("matched"))
            .alias("control_coverage")
        )
        .with_columns(
            pl.when(pl.col("control_coverage") == "missing")
            .then(None)
            .when(pl.col("is_controlled_season"))
            .then(pl.col("expected_war"))
            .otherwise(0.0)
            .alias("controlled_expected_war")
        )
        .sort(["player_id", "season"])
    )
    if paths.height != opportunity.height:
        raise RuntimeError("pitcher process bridge changed path coverage")
    rate_storage = write_canonical_parquet(
        rates, rates_path, table_name="pitcher_conditional_war_rates"
    ).as_record()
    path_storage = write_canonical_parquet(
        paths, paths_path, table_name="pitcher_expected_war_paths"
    ).as_record()
    report["storage"]["pitcher_rates"] = rate_storage
    report["storage"]["pitcher_paths"] = path_storage
    report["pitcher_process_bridge"] = {
        "status": "validated_next_year_delta_applied",
        "artifact": str(args.artifact),
        "base_root": str(args.base_root),
        "opportunity_root": str(args.opportunity_root),
        "source_profile_players": profiles.height,
        "covered_players": rates.filter(
            pl.col("pitch_process_applied")
        ).get_column("player_id").n_unique(),
        "covered_player_years": rates.filter(pl.col("pitch_process_applied")).height,
        "public_rank_or_fv_used": False,
        "missing_process_policy": "preserve_prior_rate_path_exactly",
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(report["pitcher_process_bridge"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
