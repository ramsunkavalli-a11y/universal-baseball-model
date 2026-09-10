#!/usr/bin/env python3
"""Build the frozen nested conditional prospect-career FV sensitivity."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import apply_pre_mlb_three_tier_workload
from universal_baseball.prospect_value import benchmark_value_from_model_fv, numeric_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-nested-career-value-result.json"),
    )
    return parser.parse_args()


def _counts(frame: pl.DataFrame, column: str) -> dict[str, int]:
    return {
        str(threshold): frame.filter(pl.col(column) >= threshold).height
        for threshold in (40, 45, 50, 55, 60)
    }


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    pre_mlb = (
        pl.read_parquet(root / "league-control" / dated / "league-control-snapshot.parquet")
        .filter(pl.col("mlb_debut_date").is_null())
        .select("player_id", "player_name", "organization_id")
    )
    values = pl.read_parquet(root / "phase2-model-fv" / dated / "model-fv.parquet")
    challenger = apply_pre_mlb_three_tier_workload(
        values,
        pl.read_parquet(
            root / "prospect-outcome-quality/post-debut-workload-priors-v2.parquet"
        ),
        pre_mlb_player_ids=set(pre_mlb.get_column("player_id").to_list()),
    ).join(pre_mlb, on="player_id", how="left", validate="1:1").with_columns(
        pl.struct("three_tier_model_fv_granular", "model_player_type").map_elements(
            lambda row: benchmark_value_from_model_fv(
                float(row["three_tier_model_fv_granular"]),
                str(row["model_player_type"]),
            ),
            return_dtype=pl.Float64,
        ).alias("nested_talent_benchmark_value_dollars")
    )
    evaluated = challenger.filter(pl.col("player_name").is_not_null())
    output = root / "phase2-nested-career-fv" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        challenger,
        output / "nested-career-model-fv.parquet",
        table_name="phase2_nested_career_model_fv",
    ).as_record()
    by_type = {}
    for player_type in ("hitter", "pitcher"):
        typed = evaluated.filter(pl.col("model_player_type") == player_type)
        by_type[player_type] = {
            "players": typed.height,
            "incumbent_expected_war": float(
                typed.get_column("incumbent_expected_six_year_war").sum()
            ),
            "nested_expected_war": float(
                typed.get_column("three_tier_expected_six_year_war").sum()
            ),
            "incumbent_fv_counts": _counts(typed, "model_fv_display"),
            "nested_fv_counts": _counts(typed, "three_tier_model_fv_display"),
            "mean_arrival_probability": float(
                typed.get_column("ordered_arrival_probability").mean()
            ),
            "mean_meaningful_probability": float(
                typed.get_column("ordered_meaningful_probability").mean()
            ),
            "mean_established_probability": float(
                typed.get_column("ordered_established_probability").mean()
            ),
        }
    ordering_failures = evaluated.filter(
        (pl.col("ordered_meaningful_probability") > pl.col("ordered_arrival_probability"))
        | (pl.col("ordered_established_probability") > pl.col("ordered_meaningful_probability"))
        | (pl.col("fringe_probability") < 0)
        | (pl.col("meaningful_only_probability") < 0)
        | (pl.col("established_probability") < 0)
    ).height
    examples = (
        evaluated.filter(pl.col("player_id").is_in([829034, 657277]))
        .select(
            "player_id", "player_name", "model_player_type",
            "ordered_arrival_probability", "ordered_meaningful_probability",
            "ordered_established_probability", "fringe_probability",
            "meaningful_only_probability", "established_probability",
            "incumbent_expected_six_year_war", "three_tier_expected_six_year_war",
            "model_fv_display", "three_tier_model_fv_display",
        )
        .to_dicts()
    )
    external_check = None
    external_path = root / "phase2-prospect-source/2026-09-08/fangraphs-top-100.parquet"
    if external_path.exists():
        external = (
            pl.read_parquet(external_path)
            .filter(pl.col("player_id").is_not_null())
            .with_columns(
                pl.col("future_value").map_elements(
                    numeric_fv, return_dtype=pl.Float64
                ).alias("external_fv")
            )
        )
        joined = external.join(evaluated, on="player_id", how="inner")
        external_check = {
            "role": "diagnostic_only_not_model_input",
            "players": joined.height,
            "incumbent_mae": float(
                (joined["model_fv_granular"] - joined["external_fv"]).abs().mean()
            ),
            "nested_mae": float(
                (joined["three_tier_model_fv_granular"] - joined["external_fv"])
                .abs().mean()
            ),
            "incumbent_bias": float(
                (joined["model_fv_granular"] - joined["external_fv"]).mean()
            ),
            "nested_bias": float(
                (joined["three_tier_model_fv_granular"] - joined["external_fv"])
                .mean()
            ),
        }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "private_nested_career_value_sensitivity_complete",
        "contract": "docs/prospect-nested-career-value-plan.md",
        "method": (
            "arrival times meaningful-given-arrival times established-given-meaningful; "
            "disjoint tiers use mature workload priors and existing conditional WAR rates"
        ),
        "by_player_type": by_type,
        "probability_ordering_failures": ordering_failures,
        "requested_examples": examples,
        "external_fv_check": external_check,
        "boundaries": {
            "outside_fv_used_for_selection": False,
            "skill_or_role_rates_changed": False,
            "contracts_or_costs_changed": False,
            "organization_neutral_product_values_changed": False,
            "six_year_conditional_hazards_are_approximate": True,
            "fresh_confirmation_required": True,
        },
        "storage": storage,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
