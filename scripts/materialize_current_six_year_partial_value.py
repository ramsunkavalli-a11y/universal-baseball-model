#!/usr/bin/env python3
"""Materialize validated six-year partial prospect outcomes for current players."""

from __future__ import annotations

import argparse
from datetime import date
import json
import math
from pathlib import Path

import polars as pl

try:
    from scripts.audit_prospect_comparable_chronology import (
        _deduplicate,
        _sources,
    )
    from scripts.audit_prospect_six_year_strict import _cohort
    from scripts.score_prospect_six_year_hitter_blend_confirmation import (
        LOCAL_CONDITIONAL_WEIGHT,
    )
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from audit_prospect_comparable_chronology import _deduplicate, _sources
    from audit_prospect_six_year_strict import _cohort
    from score_prospect_six_year_hitter_blend_confirmation import (
        LOCAL_CONDITIONAL_WEIGHT,
    )
from universal_baseball.prospect_historical_comparables import (
    DEFAULT_COMPARABLES,
    primary_exact_level,
    score_hitter_comparables,
    score_pitcher_comparables,
)
from universal_baseball.storage import write_canonical_parquet


REFERENCE_ORIGINS = (2003, 2008, 2013, 2016, 2018)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--arrival-root",
        type=Path,
        default=Path("reports/generated/phase2-prospect-arrival/2026-09-08"),
    )
    parser.add_argument(
        "--current-skill-root",
        type=Path,
        default=Path("reports/generated/affiliated-skill-source/tables"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-six-year-partial-value"),
    )
    return parser.parse_args()


def _current_targets(
    args: argparse.Namespace, *, player_type: str
) -> pl.DataFrame:
    hitter = player_type == "hitter"
    exposure = "plate_appearances" if hitter else "batters_faced"
    skill_name = (
        "affiliated_hitting_components.parquet"
        if hitter
        else "affiliated_pitching_components.parquet"
    )
    skill = pl.read_parquet(args.current_skill_root / skill_name)
    return (
        pl.read_parquet(args.arrival_root / f"{player_type}-arrival-probabilities.parquet")
        .join(
            primary_exact_level(skill, season=args.as_of_date.year, exposure=exposure),
            on="player_id",
            how="left",
            validate="1:1",
        )
        .with_columns(
            pl.col("primary_level_group").fill_null(pl.col("primary_level_tier")),
            pl.col("primary_exact_level_workload_share").fill_null(
                pl.col("primary_level_workload_share")
            ),
        )
    )


def _materialize_type(
    args: argparse.Namespace, *, player_type: str, runs_per_win: float
) -> pl.DataFrame:
    root = Path("reports/generated")
    snapshots, skill, outcomes, debut = _sources(root, player_type)
    references = [
        _cohort(
            snapshots,
            skill,
            outcomes,
            debut,
            origin=origin,
            player_type=player_type,
            runs_per_win=runs_per_win,
        )
        for origin in REFERENCE_ORIGINS
    ]
    target = _current_targets(args, player_type=player_type)
    reference = _deduplicate(references).join(
        target.select("player_id"), on="player_id", how="anti"
    )
    scorer = (
        score_hitter_comparables
        if player_type == "hitter"
        else score_pitcher_comparables
    )
    scored = scorer(
        reference, target, comparable_count=DEFAULT_COMPARABLES
    )
    arrived = reference.filter(pl.col("later_mlb_workload") > 0)
    arrived_values = arrived.sort("player_id")["later_component_war"].to_list()
    global_conditional = math.fsum(arrived_values) / len(arrived_values)
    if player_type == "hitter":
        scored = scored.with_columns(
            (
                LOCAL_CONDITIONAL_WEIGHT
                * pl.col("historical_conditional_component_war_4y")
                + (1.0 - LOCAL_CONDITIONAL_WEIGHT) * global_conditional
            ).alias("conditional_partial_war_6y")
        ).with_columns(
            (
                pl.col("historical_arrival_rate_4y")
                * pl.col("conditional_partial_war_6y")
            ).alias("expected_partial_war_6y")
        )
        method = "local_arrival_40pct_local_60pct_global_conditional"
    else:
        scored = scored.with_columns(
            pl.col("historical_conditional_component_war_4y").alias(
                "conditional_partial_war_6y"
            ),
            pl.col("historical_component_war_4y").alias(
                "expected_partial_war_6y"
            ),
        )
        method = "local_six_year_comparable_mean"
    return (
        target.select(
            "player_id",
            "predicted_six_year_arrival_probability",
            "primary_level_group",
        )
        .join(scored, on="player_id", validate="1:1")
        .select(
            "player_id",
            pl.lit(player_type).alias("player_type"),
            pl.col("historical_arrival_rate_4y").alias(
                "comparable_arrival_probability_6y"
            ),
            "predicted_six_year_arrival_probability",
            "conditional_partial_war_6y",
            "expected_partial_war_6y",
            "historical_conditional_arrival_support",
            "historical_comparable_players",
            "historical_comparable_level",
            "primary_level_group",
            pl.lit(global_conditional).alias("global_conditional_partial_war_6y"),
            pl.lit(method).alias("six_year_value_method"),
        )
        # Parallel historical reductions can differ below machine-meaningful
        # precision.  Freeze the public interface at twelve decimal places so
        # identical baseball inputs produce identical rows and artifact hashes.
        .with_columns(pl.col(pl.Float64).round(12))
        .with_columns(
            (
                pl.col("expected_partial_war_6y")
                - pl.col("comparable_arrival_probability_6y")
                * pl.col("conditional_partial_war_6y")
            )
            .abs()
            .round(12)
            .alias("expectation_identity_error")
        )
        .sort("player_id")
    )


def main() -> int:
    args = _args()
    runs_per_win = float(
        json.loads(Path("docs/prospect-component-uncertainty-result.json").read_text())[
            "runs_per_win"
        ]
    )
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    tables = {}
    summaries = {}
    for player_type in ("hitter", "pitcher"):
        frame = _materialize_type(
            args, player_type=player_type, runs_per_win=runs_per_win
        )
        if frame["expectation_identity_error"].max() > 1e-10:
            raise RuntimeError("six-year expectation identity does not reconcile")
        tables[player_type] = write_canonical_parquet(
            frame,
            output / f"{player_type}-six-year-partial-value.parquet",
            table_name=f"current_{player_type}_six_year_partial_value",
        ).as_record()
        summaries[player_type] = {
            "players": frame.height,
            "mean_comparable_arrival_probability": round(
                math.fsum(frame["comparable_arrival_probability_6y"].to_list())
                / frame.height,
                12,
            ),
            "mean_expected_partial_war": round(
                math.fsum(frame["expected_partial_war_6y"].to_list())
                / frame.height,
                12,
            ),
            "maximum_expected_partial_war": round(
                float(frame["expected_partial_war_6y"].max()), 12
            ),
        }
    report = {
        "status": "current_six_year_partial_value_materialized",
        "as_of_date": args.as_of_date.isoformat(),
        "reference_origins": list(REFERENCE_ORIGINS),
        "reference_outcomes_end_by": 2024,
        "summaries": summaries,
        "storage": tables,
        "boundaries": {
            "whole_player_war": False,
            "full_control_horizon": False,
            "salary_or_dollars": False,
            "fv_assigned": False,
            "outside_fv_used": False,
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    Path("docs/current-six-year-partial-value-result.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    Path("docs/current-six-year-partial-value-result.md").write_text(
        "\n".join(
            [
                "# Current six-year partial prospect value",
                "",
                "The current output now separates six-year MLB arrival probability, production conditional on arrival, and risk-adjusted expected production.",
                "",
                f"- Hitters: {summaries['hitter']['players']:,}; mean expected partial WAR {summaries['hitter']['mean_expected_partial_war']:.3f}.",
                f"- Pitchers: {summaries['pitcher']['players']:,}; mean expected partial WAR {summaries['pitcher']['mean_expected_partial_war']:.3f}.",
                "",
                "Hitter conditional production uses the confirmed 40% local / 60% global shrinkage. Pitchers use the local six-year comparable mean, which passed all four strict folds.",
                "",
                "This remains batting/pitching plus replacement only. It is not whole-player WAR, full controlled WAR, dollar value or FV.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
