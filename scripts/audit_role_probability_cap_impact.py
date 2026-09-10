#!/usr/bin/env python3
"""Measure the direct-probability safeguard against the prior nested extrapolation."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.model_fv import apply_pre_mlb_three_tier_workload
from universal_baseball.prospect_value import benchmark_value_from_model_fv


def _summary(frame: pl.DataFrame) -> dict[str, object]:
    return {
        "players": frame.height,
        "expected_six_year_war": float(frame["three_tier_expected_six_year_war"].sum()),
        "fv_45_or_higher": int((frame["three_tier_model_fv_display"] >= 45).sum()),
        "fv_50_or_higher": int((frame["three_tier_model_fv_display"] >= 50).sum()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/prospect-role-probability-cap-impact.json"),
    )
    args = parser.parse_args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    current = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    )
    arrival = pl.concat(
        [
            pl.read_parquet(
                root / "phase2-prospect-arrival" / dated
                / f"{player_type}-arrival-probabilities.parquet"
            ).select(
                "player_id",
                "predicted_six_year_nested_meaningful_role_probability",
                "predicted_six_year_nested_established_role_probability",
            ).with_columns(pl.lit(player_type).alias("model_player_type"))
            for player_type in ("hitter", "pitcher")
        ],
        how="vertical",
    )
    raw_input = current.join(
        arrival, on=["player_id", "model_player_type"], how="left", validate="1:1"
    ).with_columns(
        pl.coalesce(
            "predicted_six_year_nested_meaningful_role_probability",
            "model_meaningful_role_probability",
        ).alias("model_meaningful_role_probability"),
        pl.coalesce(
            "predicted_six_year_nested_established_role_probability",
            "model_established_role_probability",
        ).alias("model_established_role_probability"),
    ).drop(
        "predicted_six_year_nested_meaningful_role_probability",
        "predicted_six_year_nested_established_role_probability",
    )
    prospect_ids = set(
        current.filter(pl.col("ordered_arrival_probability").is_not_null())["player_id"]
    )
    counterfactual = apply_pre_mlb_three_tier_workload(
        raw_input,
        pl.read_parquet(
            root / "prospect-outcome-quality" / "post-debut-workload-priors-v2.parquet"
        ),
        pre_mlb_player_ids=prospect_ids,
    )
    joined = current.filter(
        pl.col("ordered_arrival_probability").is_not_null()
    ).select(
        "player_id", "model_player_type", "primary_position",
        pl.col("three_tier_expected_six_year_war").alias("capped_war"),
        pl.col("three_tier_model_fv_display").alias("capped_fv"),
        pl.col("nested_talent_benchmark_value_dollars").alias("capped_value"),
    ).join(
        counterfactual.select(
            "player_id",
            pl.col("three_tier_expected_six_year_war").alias("raw_nested_war"),
            pl.col("three_tier_model_fv_display").alias("raw_nested_fv"),
            pl.col("three_tier_model_fv_granular").alias("raw_nested_fv_granular"),
        ),
        on="player_id", how="inner", validate="1:1",
    )
    joined = joined.with_columns(
        pl.struct("raw_nested_fv_granular", "model_player_type").map_elements(
            lambda row: benchmark_value_from_model_fv(
                float(row["raw_nested_fv_granular"]),
                str(row["model_player_type"]),
            ),
            return_dtype=pl.Float64,
        ).alias("raw_nested_value")
    )
    hitters = joined.filter(pl.col("model_player_type") == "hitter")
    catchers = hitters.filter(pl.col("primary_position") == "C")
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "direct_role_probability_cap_impact_complete",
        "all_hitters": {
            "before": {
                "players": hitters.height,
                "expected_six_year_war": float(hitters["raw_nested_war"].sum()),
                "fv_45_or_higher": int((hitters["raw_nested_fv"] >= 45).sum()),
                "fv_50_or_higher": int((hitters["raw_nested_fv"] >= 50).sum()),
            },
            "after": _summary(
                current.filter(
                    (pl.col("model_player_type") == "hitter")
                    & pl.col("ordered_arrival_probability").is_not_null()
                )
            ),
        },
        "catchers": {
            "before_expected_six_year_war": float(catchers["raw_nested_war"].sum()),
            "after_expected_six_year_war": float(catchers["capped_war"].sum()),
            "before_fv_50_or_higher": int((catchers["raw_nested_fv"] >= 50).sum()),
            "after_fv_50_or_higher": int((catchers["capped_fv"] >= 50).sum()),
            "players": catchers.height,
        },
        "fernando_gonzalez": joined.filter(pl.col("player_id") == 692232).to_dicts()[0],
        "boundaries": {
            "outside_fv_used": False,
            "direct_unconditional_probabilities_are_caps_not_new_predictions": True,
            "year_by_year_state_model_still_required": True,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
