#!/usr/bin/env python3
"""Audit numerical stability and broad segments of dependent career value."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import numpy as np
import polars as pl

from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)
from universal_baseball.cba_rules import build_post_2026_cba_planning_scenario
from universal_baseball.dependent_career_value import (
    MASTER_SEED,
    simulate_dependent_pre_mlb_value,
)
from universal_baseball.free_agent_market import build_fangraphs_2026_market_scenario


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--sample-players", type=int, default=300)
    parser.add_argument("--draws", type=int, default=8192)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dependent-career-path-value-audit-result.json"),
    )
    return parser.parse_args()


def _segment(frame: pl.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    return (
        frame.group_by(columns)
        .agg(
            pl.len().alias("players"),
            pl.col("arrival_probability").mean().alias("mean_arrival_probability"),
            pl.col("mean_controlled_war").mean().alias("mean_controlled_war"),
            pl.col("mean_discounted_surplus_value_dollars")
            .mean()
            .alias("mean_research_value_dollars"),
            pl.col("old_value_dollars").mean().alias("mean_old_value_dollars"),
        )
        .with_columns(
            (
                pl.col("mean_research_value_dollars")
                / pl.col("mean_old_value_dollars")
            ).alias("research_to_old_value_ratio")
        )
        .sort(columns)
        .to_dicts()
    )


def _top_composition(frame: pl.DataFrame, value_column: str) -> dict[str, object]:
    top = frame.sort(value_column, descending=True).head(100)
    hitters = top.filter(pl.col("model_player_type") == "hitter")
    return {
        "player_type_counts": (
            top.group_by("model_player_type")
            .len()
            .sort("len", descending=True)
            .to_dicts()
        ),
        "hitter_position_counts": (
            hitters.group_by("primary_position")
            .len()
            .with_columns((pl.col("len") / hitters.height).alias("share_of_hitters"))
            .sort("len", descending=True)
            .to_dicts()
            if hitters.height
            else []
        ),
    }


def main() -> int:
    args = _args()
    if args.sample_players < 1 or args.draws < 2 or args.draws % 2:
        raise ValueError("sample players must be positive and draws must be even")
    dated = args.as_of_date.isoformat()
    root = Path("reports/generated")
    nested = pl.read_parquet(
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    )
    annual = pl.read_parquet(
        root / "prospect-outcome-quality-2009-2025"
        / "post-debut-annual-workload-paths.parquet"
    )
    rate_root = root / "phase2-conditional-war-paths" / dated / "tables"
    hitter_rates = pl.read_parquet(rate_root / "hitter_conditional_war_rates.parquet")
    pitcher_rates = pl.read_parquet(rate_root / "pitcher_conditional_war_rates.parquet")
    conditional_report = json.loads(
        (root / "phase2-conditional-war-paths" / dated / "report.json").read_text(
            encoding="utf-8"
        )
    )
    current = pl.read_parquet(
        root / "phase2-dependent-career-value" / dated
        / "dependent-career-value.parquet"
    )
    old = pl.read_parquet(
        root / "phase2-current-value" / dated / "value-records.parquet"
    ).select(
        "player_id",
        pl.col("transferable_value_dollars").alias("old_value_dollars"),
    )
    joined = current.join(
        nested.select("player_id", "primary_position"),
        on="player_id",
        how="left",
        validate="1:1",
    ).join(old, on="player_id", how="left", validate="1:1")
    joined = joined.with_columns(
        pl.when(pl.col("arrival_probability") < 0.1)
        .then(pl.lit("00-10%"))
        .when(pl.col("arrival_probability") < 0.25)
        .then(pl.lit("10-25%"))
        .when(pl.col("arrival_probability") < 0.5)
        .then(pl.lit("25-50%"))
        .when(pl.col("arrival_probability") < 0.75)
        .then(pl.lit("50-75%"))
        .otherwise(pl.lit("75-100%"))
        .alias("arrival_band")
    )

    top_ids = joined.sort(
        "mean_discounted_surplus_value_dollars", descending=True
    ).head(min(100, joined.height)).get_column("player_id").to_list()
    remaining = joined.filter(~pl.col("player_id").is_in(top_ids)).sort("player_id")
    needed = max(0, min(args.sample_players, joined.height) - len(top_ids))
    if needed:
        indices = np.linspace(0, remaining.height - 1, needed, dtype=int).tolist()
        spread_ids = (
            remaining.with_row_index("sample_index")
            .filter(pl.col("sample_index").is_in(indices))
            .get_column("player_id")
            .to_list()
        )
    else:
        spread_ids = []
    sample_ids = top_ids + spread_ids
    forecast_seasons = tuple(range(args.as_of_date.year + 1, args.as_of_date.year + 12))
    alternate = simulate_dependent_pre_mlb_value(
        nested.filter(pl.col("player_id").is_in(sample_ids)),
        annual,
        hitter_rates,
        pitcher_rates,
        forecast_seasons=forecast_seasons,
        cba_ruleset=build_post_2026_cba_planning_scenario(
            end_year=forecast_seasons[-1]
        ),
        market_rates=build_fangraphs_2026_market_scenario(
            start_season=forecast_seasons[0],
            end_season=forecast_seasons[-1],
            annual_growth_rate=0.03,
        ),
        arbitration_shares=FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
        runs_per_win=float(
            conditional_report["reference_environment"]["runs_per_win"]
        ),
        draws=args.draws,
        master_seed=MASTER_SEED + 1,
    )
    comparison = current.filter(pl.col("player_id").is_in(sample_ids)).join(
        alternate,
        on="player_id",
        how="inner",
        validate="1:1",
        suffix="_alternate",
    )
    value_diff = (
        comparison.get_column("mean_discounted_surplus_value_dollars_alternate")
        - comparison.get_column("mean_discounted_surplus_value_dollars")
    ).abs()
    war_diff = (
        comparison.get_column("mean_controlled_war_alternate")
        - comparison.get_column("mean_controlled_war")
    ).abs()
    base_rank = comparison.get_column(
        "mean_discounted_surplus_value_dollars"
    ).rank("average")
    alternate_rank = comparison.get_column(
        "mean_discounted_surplus_value_dollars_alternate"
    ).rank("average")
    rank_correlation = float(np.corrcoef(base_rank, alternate_rank)[0, 1])

    report = {
        "as_of_date": dated,
        "status": "research_sensitivity_not_model_selection",
        "confirmation_outcomes_accessed": False,
        "outside_fv_or_rank_used": False,
        "base_draws": int(current.item(0, "simulation_draws")),
        "alternate_draws": args.draws,
        "alternate_seed": MASTER_SEED + 1,
        "sample_players": comparison.height,
        "sample_design": "top_100_by_research_value_plus_even_player_id_spread",
        "numerical_stability": {
            "mean_absolute_value_difference_dollars": float(value_diff.mean()),
            "p90_absolute_value_difference_dollars": float(value_diff.quantile(0.9)),
            "mean_absolute_controlled_war_difference": float(war_diff.mean()),
            "p90_absolute_controlled_war_difference": float(war_diff.quantile(0.9)),
            "value_rank_correlation": rank_correlation,
        },
        "segments_by_player_type": _segment(joined, ["model_player_type"]),
        "segments_by_arrival_band": _segment(joined, ["arrival_band"]),
        "segments_by_position": _segment(joined, ["model_player_type", "primary_position"]),
        "top_100_research_composition": _top_composition(
            joined, "mean_discounted_surplus_value_dollars"
        ),
        "top_100_old_composition": _top_composition(joined, "old_value_dollars"),
        "limits": [
            "This checks numerical stability and mechanical subgroup behavior, not predictive accuracy.",
            "No later outcome is used to choose a model or assumption.",
            "Position differences may reflect real role/workload differences and are not causal effects.",
        ],
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["numerical_stability"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
