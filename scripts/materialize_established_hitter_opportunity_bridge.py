#!/usr/bin/env python3
"""Apply the validated incumbent-hitter active-probability challenger."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.established_hitter_opportunity import (
    MODEL_ID,
    apply_established_hitter_probabilities,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--conditional-root", type=Path,
        default=Path("reports/generated/phase2-conditional-war-paths"),
    )
    parser.add_argument(
        "--opportunity-root", type=Path,
        default=Path("reports/generated/phase2-workload-paths"),
    )
    parser.add_argument(
        "--control-path", type=Path,
        default=Path("reports/generated/league-control/2026-09-08/future-control-path.parquet"),
    )
    parser.add_argument(
        "--audit-root", type=Path,
        default=Path("reports/generated/established-hitter-opportunity-audit"),
    )
    parser.add_argument(
        "--artifact", type=Path,
        default=Path("model_artifacts/established-hitter-opportunity-v1.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    if artifact.get("status") != "promoted_established_hitter_active_probability_challenger":
        raise ValueError("established hitter probability artifact is not promoted")
    dated = args.as_of_date.isoformat()
    root = args.conditional_root / dated
    output_path = root / "tables/hitter_expected_war_paths.parquet"
    opportunity = pl.read_parquet(
        args.opportunity_root / dated / "tables/hitter_opportunity_paths.parquet"
    )
    rates = pl.read_parquet(root / "tables/hitter_conditional_war_rates.parquet")
    control = pl.read_parquet(args.control_path).select(
        "player_id", pl.col("control_year").alias("season"), "control_status"
    ).with_columns(
        (~pl.col("control_status").is_in(
            ["free_agent", "free_agent_eligible"]
        )).alias("is_controlled_season")
    )
    base = (
        opportunity.join(rates, on=["player_id", "season"], validate="1:1")
        .with_columns(
            (
                pl.col("mlb_active_probability")
                * pl.col("conditional_mlb_pa")
                * pl.col("conditional_war_per_600_pa")
                / 600.0
            ).alias("expected_war")
        )
        .join(control, on=["player_id", "season"], how="left")
        .with_columns(
            pl.when(pl.col("control_status").is_null())
            .then(pl.lit("missing"))
            .otherwise(pl.lit("matched"))
            .alias("control_coverage")
        )
    )
    scores = pl.read_parquet(args.audit_root / "current_scores.parquet")
    paths = apply_established_hitter_probabilities(base, scores).with_columns(
        pl.when(pl.col("control_coverage") == "missing")
        .then(None)
        .when(pl.col("is_controlled_season"))
        .then(pl.col("expected_war"))
        .otherwise(0.0)
        .alias("controlled_expected_war")
    )
    storage = write_canonical_parquet(
        paths, output_path, table_name="hitter_expected_war_paths"
    ).as_record()
    report_path = root / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["storage"]["hitter_paths"] = storage
    report["established_hitter_opportunity_bridge"] = {
        "status": "validated_active_probability_applied",
        "model_id": MODEL_ID,
        "artifact": str(args.artifact),
        "opportunity_root": str(args.opportunity_root),
        "covered_players": paths.filter(
            pl.col("established_probability_applied")
        ).get_column("player_id").n_unique(),
        "covered_player_years": paths.filter(
            pl.col("established_probability_applied")
        ).height,
        "conditional_workload_changed": False,
        "talent_rate_changed": False,
        "contract_or_public_fv_used": False,
    }
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(report["established_hitter_opportunity_bridge"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
