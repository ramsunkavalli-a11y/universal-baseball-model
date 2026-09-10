#!/usr/bin/env python3
"""Build a player-level casebook after the private position sensitivity."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from audit_prospect_top50_rankings import _arrivals, _rates
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--generated-root", type=Path, default=Path("reports/generated"))
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/prospect-position-adjusted-casebook-result.json"),
    )
    return parser.parse_args()


def _issue(row: dict[str, object]) -> str:
    if row["comparison_status"] == "agreement":
        return "agreement"
    if row["comparison_status"] == "source_higher":
        if row["model_player_type"] == "pitcher":
            return "P0 pitcher translated skill"
        if float(row.get("skill_reliability") or 0.0) < 0.20:
            return "P1 sparse hitter evidence"
        return "P1 low-level upside or cumulative model"
    if row["model_player_type"] == "pitcher":
        return "P0 pitcher translated skill"
    if row.get("batting_runs_per_600") is None:
        return "P1 missing hitter skill evidence"
    if float(row["batting_runs_per_600"]) <= 0.0:
        return "P0 opportunity outweighs weak batting"
    if (
        row.get("level_tier") in {"AA", "AAA"}
        and float(row.get("ordered_arrival_probability") or 0.0) >= 0.90
    ):
        return "P0 proximity and opportunity"
    if float(row.get("skill_reliability") or 0.0) < 0.20:
        return "P1 sparse hitter evidence"
    return "P1 strong translated batting or cumulative model"


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    sensitivity = pl.read_parquet(
        root / "prospect-shortstop-sensitivity" / dated
        / "prospect-shortstop-sensitivity.parquet"
    )
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    ).select(
        "player_id",
        "ordered_arrival_probability",
        "ordered_meaningful_probability",
        "ordered_established_probability",
        "three_tier_expected_workload",
    )
    model = (
        sensitivity.join(nested, on="player_id", how="left", validate="1:1")
        .join(_arrivals(root, dated), on="player_id", how="left", validate="1:m")
        .filter(pl.col("model_player_type") == pl.col("arrival_player_type"))
        .join(
            _rates(root, dated),
            left_on=["player_id", "model_player_type"],
            right_on=["player_id", "rate_player_type"],
            how="left",
            validate="1:1",
        )
    )
    source = pl.read_parquet(
        root / "phase2-prospect-source" / dated / "fangraphs-top-100.parquet"
    ).select(
        "player_id",
        pl.col("rank").alias("source_rank"),
        pl.col("future_value").alias("source_fv"),
    )
    model = model.join(source, on="player_id", how="left", validate="1:1")
    model_top = model.filter(pl.col("adjusted_rank") <= 50).with_columns(
        pl.when(pl.col("source_rank") <= 50)
        .then(pl.lit("agreement"))
        .otherwise(pl.lit("model_higher"))
        .alias("comparison_status")
    )
    control = pl.read_parquet(
        root / "league-control" / dated / "league-control-snapshot.parquet"
    ).select("player_id", "mlb_debut_date")
    source_top = (
        source.filter((pl.col("source_rank") <= 50) & pl.col("player_id").is_not_null())
        .join(control, on="player_id", how="left", validate="1:1")
        .filter(pl.col("mlb_debut_date").is_null())
        .join(model, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.when(pl.col("adjusted_rank") <= 50)
            .then(pl.lit("agreement"))
            .otherwise(pl.lit("source_higher"))
            .alias("comparison_status")
        )
    )
    casebook = pl.concat(
        [
            model_top.filter(pl.col("comparison_status") == "model_higher"),
            source_top.filter(pl.col("comparison_status") == "source_higher"),
        ],
        how="diagonal_relaxed",
    ).with_columns(
        pl.struct(pl.all()).map_elements(_issue, return_dtype=pl.String).alias("issue")
    ).sort(["issue", "adjusted_rank", "source_rank"], nulls_last=True)
    columns = [
        "issue",
        "comparison_status",
        "player_id",
        "player_name",
        "model_player_type",
        "source_rank",
        "incumbent_rank",
        "adjusted_rank",
        "age_years",
        "level_tier",
        "ordered_arrival_probability",
        "ordered_meaningful_probability",
        "ordered_established_probability",
        "three_tier_expected_workload",
        "conditional_skill_war_rate",
        "batting_runs_per_600",
        "baserunning_runs_per_600",
        "defense_runs_per_600",
        "incumbent_position_runs_per_600",
        "predicted_position_runs_per_600",
        "adjusted_expected_six_year_war",
        "adjusted_value_dollars",
        "skill_reliability",
        "skill_evidence_tier",
        "rule4_drafted",
        "draft_pick_quality",
    ]
    casebook = casebook.select(columns)
    output = root / "prospect-position-adjusted-casebook" / dated
    output.mkdir(parents=True, exist_ok=True)
    casebook.write_csv(output / "casebook.csv")
    model_top.select(columns[1:]).sort("adjusted_rank").write_csv(
        output / "adjusted-top-50.csv"
    )
    storage = write_canonical_parquet(
        casebook,
        output / "casebook.parquet",
        table_name="prospect_position_adjusted_casebook",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "position_adjusted_player_casebook_complete",
        "model_top_50_players": model_top.height,
        "still_eligible_source_top_50_players": source_top.height,
        "overlap": model_top.filter(pl.col("source_rank") <= 50).height,
        "disagreement_players": casebook.height,
        "issue_counts": casebook.group_by("issue").len().sort(
            ["issue", "len"]
        ).to_dicts(),
        "boundaries": {
            "outside_rank_used_as_model_input": False,
            "position_sensitivity_is_private": True,
            "named_player_adjustment_used": False,
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
