#!/usr/bin/env python3
"""Build the frozen three-tier pre-MLB workload/FV sensitivity."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import (
    apply_pre_mlb_outcome_quality_workload,
    apply_pre_mlb_three_tier_workload,
)
from universal_baseball.prospect_value import numeric_fv
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/phase2-established-tier-fv"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-established-tier-test-result.json"),
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
    war_report = json.loads(
        (root / "phase2-conditional-war-paths" / dated / "report.json").read_text(
            encoding="utf-8"
        )
    )
    pitcher_process_active = (
        war_report.get("pitcher_process_bridge", {}).get("status")
        == "validated_next_year_delta_applied"
    )
    control = pl.read_parquet(
        root / "league-control" / dated / "league-control-snapshot.parquet"
    )
    pre_mlb = control.filter(pl.col("mlb_debut_date").is_null()).select(
        "player_id", "player_name", "organization_id"
    )
    pre_mlb_ids = set(pre_mlb.get_column("player_id").to_list())
    values = pl.read_parquet(root / "phase2-model-fv" / dated / "model-fv.parquet")
    prior_root = root / "prospect-outcome-quality"
    binary = apply_pre_mlb_outcome_quality_workload(
        values,
        pl.read_parquet(prior_root / "post-debut-workload-priors.parquet"),
        pre_mlb_player_ids=pre_mlb_ids,
    ).select(
        "player_id", "outcome_quality_expected_six_year_war",
        "outcome_quality_model_fv_granular", "outcome_quality_model_fv_display",
    )
    challenger = (
        apply_pre_mlb_three_tier_workload(
            values,
            pl.read_parquet(prior_root / "post-debut-workload-priors-v2.parquet"),
            pre_mlb_player_ids=pre_mlb_ids,
        )
        .join(binary, on="player_id", how="left", validate="1:1")
        .join(pre_mlb, on="player_id", how="left", validate="1:1")
    )
    evaluated = challenger.filter(pl.col("player_name").is_not_null())
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        challenger,
        output / "established-tier-model-fv.parquet",
        table_name="phase2_established_tier_model_fv",
    ).as_record()

    by_type = {}
    for player_type in ("hitter", "pitcher"):
        typed = evaluated.filter(pl.col("model_player_type") == player_type)
        by_type[player_type] = {
            "players": typed.height,
            "incumbent_expected_war": float(
                typed.get_column("incumbent_expected_six_year_war").sum()
            ),
            "binary_expected_war": float(
                typed.get_column("outcome_quality_expected_six_year_war").sum()
            ),
            "three_tier_expected_war": float(
                typed.get_column("three_tier_expected_six_year_war").sum()
            ),
            "incumbent_fv_counts": _counts(typed, "model_fv_display"),
            "binary_fv_counts": _counts(typed, "outcome_quality_model_fv_display"),
            "three_tier_fv_counts": _counts(typed, "three_tier_model_fv_display"),
            "mean_ordered_arrival_probability": float(
                typed.get_column("ordered_arrival_probability").mean()
            ),
            "mean_ordered_meaningful_probability": float(
                typed.get_column("ordered_meaningful_probability").mean()
            ),
            "mean_ordered_established_probability": float(
                typed.get_column("ordered_established_probability").mean()
            ),
        }
    ordering = evaluated.select(
        (pl.col("model_meaningful_role_probability") > pl.col("model_arrival_probability"))
        .sum().alias("meaningful_above_arrival"),
        (pl.col("model_established_role_probability") > pl.col("model_meaningful_role_probability"))
        .sum().alias("established_above_meaningful"),
    ).row(0, named=True)
    examples = (
        evaluated.filter(pl.col("player_id").is_in([829034, 657277]))
        .select(
            "player_id", "player_name", "model_player_type",
            "ordered_arrival_probability", "ordered_meaningful_probability",
            "ordered_established_probability", "fringe_probability",
            "meaningful_only_probability", "established_probability",
            "incumbent_expected_six_year_war", "outcome_quality_expected_six_year_war",
            "three_tier_expected_six_year_war", "model_fv_display",
            "outcome_quality_model_fv_display", "three_tier_model_fv_display",
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
            "binary_mae": float(
                (
                    joined["outcome_quality_model_fv_granular"] - joined["external_fv"]
                ).abs().mean()
            ),
            "three_tier_mae": float(
                (joined["three_tier_model_fv_granular"] - joined["external_fv"])
                .abs().mean()
            ),
            "incumbent_bias": float(
                (joined["model_fv_granular"] - joined["external_fv"]).mean()
            ),
            "binary_bias": float(
                (joined["outcome_quality_model_fv_granular"] - joined["external_fv"])
                .mean()
            ),
            "three_tier_bias": float(
                (joined["three_tier_model_fv_granular"] - joined["external_fv"])
                .mean()
            ),
        }
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "private_three_tier_sensitivity_not_promoted",
        "contract": "docs/prospect-established-tier-test-plan.md",
        "method": (
            "ordered disjoint fringe, meaningful-only and established probabilities "
            "times mature six-calendar-year workload priors and existing WAR rates"
        ),
        "boundaries": {
            "publication_grades_used_as_inputs": False,
            "outside_fv_used_for_selection": False,
            "skill_rates_changed": pitcher_process_active,
            "contract_values_changed": False,
            "current_product_values_changed": pitcher_process_active,
            "fresh_confirmation_required": True,
        },
        "probability_ordering_corrections": ordering,
        "by_player_type": by_type,
        "requested_examples": examples,
        "external_fv_check": external_check,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
