#!/usr/bin/env python3
"""Compare frozen separated prospect outcomes with the outside top 50."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", default="2026-09-08")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/prospect-separated-outcome-top50-audit"),
    )
    return parser.parse_args()


def _rank(frame: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for player_type in ("hitter", "pitcher"):
        group = frame.filter(pl.col("player_type") == player_type)
        expected = (
            group.sort("historical_component_war_4y", descending=True)
            .with_row_index("expected_outcome_rank", offset=1)
            .select("player_id", "expected_outcome_rank")
        )
        arrival = (
            group.sort("historical_arrival_rate_4y", descending=True)
            .with_row_index("arrival_rank", offset=1)
            .select("player_id", "arrival_rank")
        )
        ranked = group.join(expected, on="player_id", validate="1:1").join(
            arrival, on="player_id", validate="1:1"
        ).with_columns(
            (
                1.0
                - (pl.col("expected_outcome_rank") - 1)
                / max(group.height - 1, 1)
            ).alias("expected_outcome_percentile"),
            (
                1.0 - (pl.col("arrival_rank") - 1) / max(group.height - 1, 1)
            ).alias("arrival_percentile"),
        )
        if player_type == "hitter":
            supported = group.filter(pl.col("historical_conditional_rate_supported"))
            conditional = (
                supported.sort(
                    "historical_conditional_component_war_rate", descending=True
                )
                .with_row_index("conditional_rate_rank", offset=1)
                .select("player_id", "conditional_rate_rank")
                .with_columns(
                    (
                        1.0
                        - (pl.col("conditional_rate_rank") - 1)
                        / max(supported.height - 1, 1)
                    ).alias("conditional_rate_percentile")
                )
            )
            ranked = ranked.join(conditional, on="player_id", how="left", validate="1:1")
        else:
            ranked = ranked.with_columns(
                pl.lit(None, dtype=pl.UInt32).alias("conditional_rate_rank"),
                pl.lit(None, dtype=pl.Float64).alias("conditional_rate_percentile"),
            )
        rows.append(ranked)
    return pl.concat(rows, how="diagonal_relaxed")


def _assessment(row: dict[str, object]) -> str:
    if row.get("expected_outcome_percentile") is None:
        return str(row.get("model_coverage_status") or "missing_model_data")
    expected = float(row["expected_outcome_percentile"])
    conditional = row.get("conditional_rate_percentile")
    conditional_value = float(conditional) if conditional is not None else -1.0
    if expected >= 0.90 or conditional_value >= 0.90:
        return "broad_agreement"
    if expected >= 0.75 or conditional_value >= 0.75:
        return "partial_agreement"
    return "model_lower_review"


def main() -> int:
    args = _args()
    generated = Path("reports/generated")
    comparable_root = generated / "prospect-historical-comparables" / args.as_of_date
    hitter = pl.read_parquet(comparable_root / "hitter-comparables.parquet").with_columns(
        pl.lit("hitter").alias("player_type")
    )
    pitcher = pl.read_parquet(comparable_root / "pitcher-comparables.parquet").with_columns(
        pl.lit("pitcher").alias("player_type")
    )
    model = _rank(pl.concat([hitter, pitcher], how="diagonal_relaxed"))
    names = pl.read_parquet(
        generated / "league-control" / args.as_of_date / "league-control-snapshot.parquet"
    ).select("player_id", "player_name").unique("player_id")
    arrival = pl.concat([
        pl.read_parquet(
            generated / "phase2-prospect-arrival" / args.as_of_date
            / "hitter-arrival-probabilities.parquet"
        ).with_columns(pl.lit("hitter").alias("player_type")),
        pl.read_parquet(
            generated / "phase2-prospect-arrival" / args.as_of_date
            / "pitcher-arrival-probabilities.parquet"
        ).with_columns(pl.lit("pitcher").alias("player_type")),
    ], how="diagonal_relaxed").select(
        "player_id", "player_type", "age_years", "current_milb_workload"
    )
    current_level = pl.concat([
        pl.read_parquet(
            generated / "current-peak-talent" / args.as_of_date / "tables"
            / "current_peak_hitters.parquet"
        ).select("player_id", "as_of_level_group"),
        pl.read_parquet(
            generated / "current-peak-talent" / args.as_of_date / "tables"
            / "current_peak_pitchers.parquet"
        ).select("player_id", "as_of_level_group"),
    ], how="vertical_relaxed").unique("player_id")
    debut = pl.read_parquet(
        generated / "career-mlb-outcome-inventory-2009-2025" / "tables"
        / "people-debut-dates.parquet"
    )
    outside = pl.read_parquet(
        generated / "phase2-prospect-source" / args.as_of_date
        / "fangraphs-top-100.parquet"
    ).filter(pl.col("rank") <= 50).select(
        pl.col("rank").alias("outside_rank"),
        pl.col("future_value").alias("outside_fv"),
        "player_id", "prospect_type",
    ).rename({"prospect_type": "player_type"})
    audit = (
        outside.join(model, on=["player_id", "player_type"], how="left")
        .join(names, on="player_id", how="left")
        .join(arrival, on=["player_id", "player_type"], how="left")
        .join(current_level, on="player_id", how="left")
        .join(debut, on="player_id", how="left")
        .with_columns(
            pl.when(pl.col("historical_component_war_4y").is_not_null())
            .then(pl.lit("eligible_foundation"))
            .when(
                (pl.col("as_of_level_group") == "MLB")
                | pl.col("mlb_debut_date").is_not_null()
            )
            .then(pl.lit("graduated_or_prior_mlb"))
            .otherwise(pl.lit("missing_model_data"))
            .alias("model_coverage_status")
        )
        .sort("outside_rank")
    )
    audit = audit.with_columns(
        pl.struct(audit.columns).map_elements(
            _assessment, return_dtype=pl.String
        ).alias("assessment")
    )
    output = args.output_root / args.as_of_date
    output.mkdir(parents=True, exist_ok=True)
    audit.write_csv(output / "public-top50-separated-outcomes.csv")

    matched = audit.filter(pl.col("historical_component_war_4y").is_not_null())
    counts = audit.group_by("assessment").len().sort("assessment")
    case_ids = (816113, 829034)
    cases = audit.filter(pl.col("player_id").is_in(case_ids))
    lines = [
        "# Public top-50 separated-outcome audit",
        "",
        "Status: diagnostic only; outside rank and FV are not model inputs.",
        "",
        f"Matched {matched.height} of {audit.height} outside top-50 players to the current pre-MLB foundation.",
        f"The other {audit.height - matched.height} had reached MLB by the current checkpoint or had prior MLB experience; they are graduates, not missing prospect rows.",
        "The comparison uses within-player-type percentiles because hitter and pitcher",
        "partial-WAR scopes are not interchangeable. `model_lower_review` is a review",
        "queue, not proof that either side is wrong.",
        "",
        "| Assessment | Players |",
        "|---|---:|",
    ]
    for row in counts.iter_rows(named=True):
        lines.append(f"| {row['assessment']} | {row['len']} |")
    lines += [
        "",
        "## Willits and Gonzalez",
        "",
        "| Player | Public rank/FV | Exact level | Raw current PA | Arrival | Conditional rate | Expected 4y partial WAR | Assessment |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for row in cases.iter_rows(named=True):
        conditional = row.get("historical_conditional_component_war_rate")
        conditional_text = f"{float(conditional):.2f}" if conditional is not None else "withheld"
        lines.append(
            f"| {row['player_name']} | {row['outside_rank']}/{row['outside_fv']} | "
            f"{row['historical_comparable_level']} | {float(row['current_milb_workload']):.0f} | "
            f"{float(row['historical_arrival_rate_4y']):.1%} | {conditional_text} | "
            f"{float(row['historical_component_war_4y']):.2f} | {row['assessment']} |"
        )
    lines += [
        "",
        "## Model-lower review queue",
        "",
        "| Player | Public rank | Type | Exact level | Raw workload | Arrival | Conditional rate | Basic reason |",
        "|---|---:|---|---|---:|---:|---:|---|",
    ]
    for row in audit.filter(
        pl.col("assessment") == "model_lower_review"
    ).iter_rows(named=True):
        conditional = row.get("historical_conditional_component_war_rate")
        conditional_text = (
            f"{float(conditional):.2f}"
            if row["player_type"] == "hitter" and conditional is not None
            else "withheld"
        )
        reason = (
            "small current sample and low four-year arrival frequency"
            if float(row["current_milb_workload"]) < 100
            else "pitcher quality signal failed validation; arrival remains low"
            if row["player_type"] == "pitcher"
            else "large low-level sample but modest arrival and conditional batting outcomes"
        )
        lines.append(
            f"| {row['player_name']} | {row['outside_rank']} | {row['player_type']} | "
            f"{row['historical_comparable_level']} | {float(row['current_milb_workload']):.0f} | "
            f"{float(row['historical_arrival_rate_4y']):.1%} | {conditional_text} | {reason} |"
        )
    lines += [
        "",
        "## Boundary",
        "",
        "Expected outcome covers only the next four calendar years and includes batting",
        "or pitching plus replacement. It is not six-year controlled WAR. Conditional",
        "pitcher quality is withheld, and hitter conditional quality is shown only with",
        "at least ten neighboring MLB arrivals. No FV inference is permitted from this audit.",
        "",
    ]
    Path("docs/prospect-separated-outcome-top50-audit.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    report = {
        "as_of_date": args.as_of_date,
        "status": "outside_diagnostic_only_not_model_input",
        "outside_top50": audit.height,
        "matched": matched.height,
        "assessment_counts": {
            str(row["assessment"]): int(row["len"])
            for row in counts.iter_rows(named=True)
        },
        "outside_fv_used_as_model_input": False,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
