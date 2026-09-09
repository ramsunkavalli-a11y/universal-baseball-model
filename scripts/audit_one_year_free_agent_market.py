#!/usr/bin/env python3
"""Audit the internal one-year free-agent check against the public reference."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.free_agent_market import (
    FANGRAPHS_2026_DOLLARS_PER_WAR,
    FANGRAPHS_2026_MARKET_REFERENCE_ID,
    FANGRAPHS_2026_MARKET_SOURCE_URL,
)
from universal_baseball.free_agent_market_diagnostics import (
    build_one_year_market_diagnostics,
)


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--forecast-root",
        type=Path,
        default=Path("reports/generated/one-year-free-agent-war"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/one-year-free-agent-market-audit"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    forecasts = pl.read_parquet(
        args.forecast_root
        / args.as_of_date.isoformat()
        / "tables/signing-time-war.parquet"
    )
    diagnostics = build_one_year_market_diagnostics(forecasts)
    report = {
        "report_schema_version": "0.1",
        "gate": "one_year_free_agent_market_independent_check",
        "as_of_date": args.as_of_date.isoformat(),
        "main_reference_id": FANGRAPHS_2026_MARKET_REFERENCE_ID,
        "main_reference_url": FANGRAPHS_2026_MARKET_SOURCE_URL,
        "main_reference_2026_dollars_per_war": dict(
            FANGRAPHS_2026_DOLLARS_PER_WAR
        ),
        "diagnostics": diagnostics,
    }
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
