#!/usr/bin/env python3
"""Build pre-signing WAR forecasts for clean one-year free-agent deals."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.free_agent_market_projection import (
    ONE_YEAR_MARKET_PROJECTION_ID,
    build_one_year_signing_time_war,
    classify_one_year_market_rows,
)
from universal_baseball.player_value_mlb_run_environment import (
    fetch_mlb_run_environment,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--market-root",
        type=Path,
        default=Path("reports/generated/free-agent-market-identity"),
    )
    parser.add_argument(
        "--skill-root",
        type=Path,
        default=Path("reports/generated/free-agent-historical-skill-source/2025-12-31"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/one-year-free-agent-war"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    market = pl.read_parquet(
        args.market_root
        / args.as_of_date.isoformat()
        / "tables/free-agent-market-identities.parquet"
    )
    hitting = pl.read_parquet(args.skill_root / "tables/mlb_hitting_components.parquet")
    pitching = pl.read_parquet(
        args.skill_root / "tables/mlb_pitching_components.parquet"
    )
    classified = classify_one_year_market_rows(market)
    reference_years = sorted(
        {
            int(year) - 1
            for year in classified.filter(pl.col("sample_eligible"))
            .get_column("free_agent_year")
            .to_list()
        }
    )
    environments: dict[int, dict[str, float]] = {}
    environment_reports = []
    for reference_year in reference_years:
        environment = fetch_mlb_run_environment(reference_year)
        actual_reference_bf = int(
            pitching.filter(pl.col("season") == reference_year)
            .get_column("pitching_batters_faced")
            .sum()
        )
        schedule_factor = 162.0 / 60.0 if reference_year == 2020 else 1.0
        normalized_reference_pa = int(
            round(environment.batting_plate_appearances * schedule_factor)
        )
        normalized_reference_bf = int(round(actual_reference_bf * schedule_factor))
        environments[reference_year] = {
            "batting_plate_appearances": float(normalized_reference_pa),
            "pitching_batters_faced": float(normalized_reference_bf),
            "runs_per_win": environment.runs_per_win.runs_per_win,
        }
        environment_reports.append(
            {
                "season": reference_year,
                "actual_batting_plate_appearances": (
                    environment.batting_plate_appearances
                ),
                "actual_pitching_batters_faced": actual_reference_bf,
                "schedule_normalization_factor": schedule_factor,
                "reference_batting_plate_appearances": normalized_reference_pa,
                "reference_pitching_batters_faced": normalized_reference_bf,
                "runs_per_win": environment.runs_per_win.runs_per_win,
                "regular_season_games": environment.regular_season_games,
                "source_captures": [asdict(capture) for capture in environment.captures],
                "schedule_capture": asdict(environment.schedule_capture),
            }
        )
    forecasts = build_one_year_signing_time_war(
        classified,
        hitting,
        pitching,
        reference_environments=environments,
    )

    output = args.output_root / args.as_of_date.isoformat()
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "classified_market": write_canonical_parquet(
            classified,
            tables / "classified-market.parquet",
            table_name="one_year_free_agent_market_classification",
        ).as_record(),
        "forecasts": write_canonical_parquet(
            forecasts,
            tables / "signing-time-war.parquet",
            table_name="one_year_free_agent_signing_time_war",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "one_year_free_agent_signing_time_war",
        "as_of_date": args.as_of_date.isoformat(),
        "projection_model_id": ONE_YEAR_MARKET_PROJECTION_ID,
        "source_rows": market.height,
        "sample_status": classified.group_by("sample_status")
        .len()
        .sort("sample_status")
        .to_dicts(),
        "forecast_status": forecasts.group_by("forecast_status")
        .len()
        .sort("forecast_status")
        .to_dicts(),
        "market_fit_rows": forecasts.filter(pl.col("market_fit_eligible")).height,
        "market_fit_rows_by_year": forecasts.filter(pl.col("market_fit_eligible"))
        .group_by("free_agent_year")
        .len()
        .sort("free_agent_year")
        .to_dicts(),
        "chronology": "each target uses only StatsAPI seasons ending target minus one",
        "workload_method": (
            "fixed-denominator 3/2/1 prior-three-season MLB PA or BF; missing "
            "seasons zero; 2020 exposure normalized from 60 to 162 games"
        ),
        "component_boundary": (
            "team-neutral hitter/pitcher rates; position value included; historical "
            "defense skill and baserunning neutral"
        ),
        "team_depth_used": False,
        "reference_environments": environment_reports,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "gate",
                    "sample_status",
                    "forecast_status",
                    "market_fit_rows",
                    "market_fit_rows_by_year",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
