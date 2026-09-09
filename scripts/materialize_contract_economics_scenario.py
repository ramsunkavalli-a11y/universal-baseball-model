#!/usr/bin/env python3
"""Materialize the complete Phase 1 research economics scenario."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_MODEL_ID,
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)
from universal_baseball.cba_rules import CBA_2027_2032_PLANNING_SCENARIO
from universal_baseball.contract_economics import (
    ContractEconomicsAssumptions,
    value_annual_contract_states,
)
from universal_baseball.free_agent_market import (
    FANGRAPHS_2026_MARKET_REFERENCE_ID,
    build_fangraphs_2026_market_scenario,
)
from universal_baseball.storage import write_canonical_parquet


MARKET_GROWTH_RATE = 0.03
NOMINAL_DISCOUNT_RATE = 0.10


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("reports/generated/current-contract-economics-inputs"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-contract-economics-scenario"),
    )
    parser.add_argument(
        "--buyout-assumptions",
        type=Path,
        default=Path("config/contract-buyout-assumptions-2026-09-09.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    source = pl.read_parquet(
        args.input_root
        / args.as_of_date.isoformat()
        / "annual-contract-economics-inputs.parquet"
    )
    start_season = int(source.get_column("season").min())
    end_season = int(source.get_column("season").max())
    market = build_fangraphs_2026_market_scenario(
        start_season=start_season,
        end_season=end_season,
        annual_growth_rate=MARKET_GROWTH_RATE,
    )
    buyout_payload = json.loads(args.buyout_assumptions.read_text(encoding="utf-8"))
    missing_buyout_shares = {
        str(row["control_status"]): float(row["buyout_share_of_option_salary"])
        for row in buyout_payload["assumptions"]
    }
    assumptions = ContractEconomicsAssumptions(
        assumptions_id=(
            "phase1_research_market3pct_nominal_discount10pct_2026_09_09"
        ),
        market_model_id=(
            FANGRAPHS_2026_MARKET_REFERENCE_ID + "_growth_0.03"
        ),
        arbitration_model_id=FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        dollars_per_war_by_year={},
        arbitration_share_by_class=dict(
            FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS
        ),
        annual_discount_rate=NOMINAL_DISCOUNT_RATE,
        tiered_dollars_per_war_by_year=market,
        missing_buyout_share_by_status=missing_buyout_shares,
    )
    result = value_annual_contract_states(
        source,
        cba_ruleset=CBA_2027_2032_PLANNING_SCENARIO,
        assumptions=assumptions,
    )
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "annual": write_canonical_parquet(
            result.annual,
            output / "annual-contract-economics.parquet",
            table_name="phase1_research_annual_contract_economics",
        ).as_record(),
        "aggregate": write_canonical_parquet(
            result.aggregate,
            output / "aggregate-contract-economics.parquet",
            table_name="phase1_research_aggregate_contract_economics",
        ).as_record(),
        "reviews": write_canonical_parquet(
            result.reviews,
            output / "contract-economics-reviews.parquet",
            table_name="phase1_research_contract_economics_reviews",
        ).as_record(),
    }
    available = result.annual.filter(pl.col("calculation_status") == "available")
    imputed_buyouts = available.filter(
        pl.col("salary_basis").str.contains("_assumed_.*_buyout_share$")
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "phase1_future_contract_economics_research_scenario",
        "as_of_date": args.as_of_date.isoformat(),
        "ranking_status": "research_scenario_not_publishable_model",
        "annual_rows": result.annual.height,
        "available_annual_rows": available.height,
        "review_annual_rows": result.reviews.height,
        "available_players": result.aggregate.filter(
            pl.col("calculation_status") == "available"
        ).height,
        "review_players": result.aggregate.filter(
            pl.col("calculation_status") == "review"
        ).height,
        "review_reasons": result.reviews.group_by("review_reason")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "ruleset_id": CBA_2027_2032_PLANNING_SCENARIO.ruleset_id,
        "ruleset_kind": CBA_2027_2032_PLANNING_SCENARIO.ruleset_kind,
        "market_reference_id": FANGRAPHS_2026_MARKET_REFERENCE_ID,
        "market_growth_rate": MARKET_GROWTH_RATE,
        "arbitration_model_id": FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        "nominal_discount_rate": NOMINAL_DISCOUNT_RATE,
        "missing_buyout_assumption_id": buyout_payload["snapshot_id"],
        "missing_buyout_assumption_rows": imputed_buyouts.height,
        "missing_buyout_assumption": buyout_payload["boundary"],
        "discount_boundary": (
            "market rates and minimum salaries grow 3%; nominal cash/value is "
            "discounted 10%, equivalent to roughly 7% net before interaction"
        ),
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
                    "ranking_status",
                    "annual_rows",
                    "available_annual_rows",
                    "review_annual_rows",
                    "available_players",
                    "review_players",
                    "review_reasons",
                )
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
