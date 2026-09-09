#!/usr/bin/env python3
"""Materialize the named FanGraphs 2026 tier reference and a future scenario."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.free_agent_market import (
    FANGRAPHS_2026_MARKET_REFERENCE_ID,
    FANGRAPHS_2026_MARKET_SOURCE_URL,
    build_fangraphs_2026_market_scenario,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--start-season", type=int, default=2026)
    parser.add_argument("--end-season", type=int, default=2032)
    parser.add_argument("--annual-growth-rate", type=float, default=0.03)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/free-agent-market-assumptions"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    scenario = build_fangraphs_2026_market_scenario(
        start_season=args.start_season,
        end_season=args.end_season,
        annual_growth_rate=args.annual_growth_rate,
    )
    scenario_id = (
        f"{FANGRAPHS_2026_MARKET_REFERENCE_ID}_growth_"
        f"{args.annual_growth_rate:.4f}"
    )
    rows = [
        {
            "season": season,
            "war_tier": tier,
            "dollars_per_war": rate,
            "reference_season": 2026,
            "reference_id": FANGRAPHS_2026_MARKET_REFERENCE_ID,
            "scenario_id": scenario_id,
            "annual_growth_rate": args.annual_growth_rate,
            "source_url": FANGRAPHS_2026_MARKET_SOURCE_URL,
        }
        for season, tiers in scenario.items()
        for tier, rate in tiers.items()
    ]
    frame = pl.DataFrame(rows).sort(["season", "war_tier"])
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        frame,
        output / "free-agent-market-assumptions.parquet",
        table_name="free_agent_market_assumptions",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "free_agent_market_tier_reference_and_scenario",
        "as_of_date": args.as_of_date.isoformat(),
        "scenario_id": scenario_id,
        "reference_is_observed_2026": True,
        "future_rates_are_scenario_not_fact": True,
        "annual_growth_rate": args.annual_growth_rate,
        "rest_of_season_tiering_allowed": False,
        "post_2026_cba_cost_rules_resolved": False,
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
