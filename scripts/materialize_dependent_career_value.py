#!/usr/bin/env python3
"""Materialize the first dependent pre-MLB career-value research distribution."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)
from universal_baseball.cba_rules import build_post_2026_cba_planning_scenario
from universal_baseball.dependent_career_value import (
    DEFAULT_DRAWS,
    MODEL_ID,
    simulate_dependent_pre_mlb_value,
)
from universal_baseball.free_agent_market import build_fangraphs_2026_market_scenario
from universal_baseball.storage import sha256_file, write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--draws", type=int, default=DEFAULT_DRAWS)
    parser.add_argument(
        "--generated-root", type=Path, default=Path("reports/generated")
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("docs/dependent-career-path-value-result.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    root = args.generated_root
    nested_path = (
        root / "phase2-nested-career-fv" / dated / "nested-career-model-fv.parquet"
    )
    annual_path = (
        root
        / "prospect-outcome-quality-2009-2025"
        / "post-debut-annual-workload-paths.parquet"
    )
    rate_root = root / "phase2-conditional-war-paths" / dated / "tables"
    hitter_rate_path = rate_root / "hitter_conditional_war_rates.parquet"
    pitcher_rate_path = rate_root / "pitcher_conditional_war_rates.parquet"
    conditional_report_path = root / "phase2-conditional-war-paths" / dated / "report.json"
    old_value_path = root / "phase2-current-value" / dated / "value-records.parquet"
    source_paths = (
        nested_path,
        annual_path,
        hitter_rate_path,
        pitcher_rate_path,
        conditional_report_path,
        old_value_path,
    )
    if missing := [path for path in source_paths if not path.exists()]:
        raise FileNotFoundError(f"dependent career-value inputs missing: {missing}")
    annual = pl.read_parquet(annual_path)
    first_forecast_year = args.as_of_date.year + 1
    if annual.filter(pl.col("window_end_year") >= first_forecast_year).height:
        raise ValueError("historical path outcome extends into the forecast period")
    conditional_report = json.loads(
        conditional_report_path.read_text(encoding="utf-8")
    )
    source_forecast_seasons = tuple(
        int(value) for value in conditional_report["forecast_seasons"]
    )
    if source_forecast_seasons != tuple(
        range(first_forecast_year, first_forecast_year + 6)
    ):
        raise ValueError("dependent career simulation requires six source projection years")
    forecast_seasons = tuple(range(first_forecast_year, first_forecast_year + 11))
    cba_scenario = build_post_2026_cba_planning_scenario(
        end_year=forecast_seasons[-1]
    )
    result = simulate_dependent_pre_mlb_value(
        pl.read_parquet(nested_path),
        annual,
        pl.read_parquet(hitter_rate_path),
        pl.read_parquet(pitcher_rate_path),
        forecast_seasons=forecast_seasons,
        cba_ruleset=cba_scenario,
        market_rates=build_fangraphs_2026_market_scenario(
            start_season=forecast_seasons[0],
            end_season=forecast_seasons[-1],
            annual_growth_rate=0.03,
        ),
        arbitration_shares=FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
        runs_per_win=float(conditional_report["reference_environment"]["runs_per_win"]),
        draws=args.draws,
    )
    old = pl.read_parquet(old_value_path).select(
        "player_id",
        pl.col("transferable_value_dollars").alias("old_benchmark_value_dollars"),
        pl.col("expected_controlled_war").alias("old_expected_controlled_war"),
    )
    comparison = result.join(old, on="player_id", how="left", validate="1:1")
    output = root / "phase2-dependent-career-value" / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result,
        output / "dependent-career-value.parquet",
        table_name="phase2_dependent_pre_mlb_career_value",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "as_of_date": dated,
        "status": "dependent_career_value_research_not_promoted",
        "contract": "docs/dependent-career-path-value-plan.md",
        "model_id": MODEL_ID,
        "players": result.height,
        "simulation_draws_per_player": args.draws,
        "forecast_calendar_years": list(forecast_seasons),
        "historical_path_players": annual.get_column("path_player_id").n_unique(),
        "historical_path_player_components": annual.select(
            "path_player_id", "player_type"
        ).unique().height,
        "historical_annual_rows": annual.height,
        "maximum_historical_window_end_year": int(
            annual.get_column("window_end_year").max()
        ),
        "summary": {
            "mean_value_dollars": float(
                result.get_column("mean_discounted_surplus_value_dollars").mean()
            ),
            "median_player_median_value_dollars": float(
                result.get_column("median_discounted_surplus_value_dollars").median()
            ),
            "mean_controlled_war": float(
                result.get_column("mean_controlled_war").mean()
            ),
            "mean_expected_cost_dollars": float(
                result.get_column("expected_discounted_cost_dollars").mean()
            ),
            "mean_star_probability": float(
                result.get_column("star_probability").mean()
            ),
            "players_with_zero_median_value": result.filter(
                pl.col("median_discounted_surplus_value_dollars") == 0.0
            ).height,
            "mean_value_to_old_benchmark_ratio": float(
                comparison.get_column("mean_discounted_surplus_value_dollars").sum()
                / comparison.get_column("old_benchmark_value_dollars").sum()
            ),
            "mean_war_to_old_point_ratio": float(
                comparison.get_column("mean_controlled_war").sum()
                / comparison.get_column("old_expected_controlled_war").sum()
            ),
        },
        "boundaries": {
            "production_values_changed": False,
            "publication_fv_or_rank_used": False,
            "2026_partial_outcomes_used": False,
            "historical_failures_and_zero_years_retained": True,
            "whole_historical_paths_resampled": True,
            "arrival_timing_constant_annual_hazard_provisional": True,
            "performance_posterior_shock_persistent_across_years": True,
            "season_event_noise_independent_conditional_on_path": True,
            "control_accrues_only_in_simulated_active_seasons": True,
            "full_six_year_post_arrival_path_retained": True,
            "full_active_season_service_approximation": True,
            "super_two_simulation_pending": True,
            "forecast_time_non_tender_policy_pending": True,
            "same_season_realized_war_never_drives_tender_decision": True,
            "guaranteed_contract_and_option_overlays_pending": True,
            "successor_cba_is_planning_scenario": True,
            "market_value_uses_path_annual_war_tiers": True,
            "2025_is_development_not_confirmation": True,
        },
        "source_files": {
            path.as_posix(): sha256_file(path) for path in source_paths
        },
        "storage": storage,
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "source_files"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
