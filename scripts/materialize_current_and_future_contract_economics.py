#!/usr/bin/env python3
"""Value current remaining rights and future control in one research scenario."""

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
    FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR,
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
        default=Path("reports/generated/current-rest-of-season"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-and-future-contract-economics"),
    )
    parser.add_argument(
        "--buyout-assumptions",
        type=Path,
        default=Path("config/contract-buyout-assumptions-2026-09-09.json"),
    )
    return parser.parse_args()


def build_assumptions(
    *, as_of_year: int, end_season: int, buyout_payload: dict[str, object]
) -> ContractEconomicsAssumptions:
    if as_of_year != 2026:
        raise ValueError("current integrated Phase 1 scenario is anchored to 2026")
    market = build_fangraphs_2026_market_scenario(
        start_season=as_of_year,
        end_season=end_season,
        annual_growth_rate=MARKET_GROWTH_RATE,
    )
    market.pop(as_of_year)
    missing_buyout_shares = {
        str(row["control_status"]): float(row["buyout_share_of_option_salary"])
        for row in list(buyout_payload["assumptions"])
    }
    return ContractEconomicsAssumptions(
        assumptions_id="phase1_current_future_market3pct_discount10pct_2026_09_09",
        market_model_id=(
            FANGRAPHS_2026_MARKET_REFERENCE_ID
            + "_current_overall_future_tiers_growth_0.03"
        ),
        arbitration_model_id=FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        dollars_per_war_by_year={
            as_of_year: float(
                FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[as_of_year]
            )
        },
        arbitration_share_by_class=dict(FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS),
        annual_discount_rate=NOMINAL_DISCOUNT_RATE,
        tiered_dollars_per_war_by_year=market,
        missing_buyout_share_by_status=missing_buyout_shares,
    )


def main() -> int:
    args = _args()
    source_path = (
        args.input_root
        / args.as_of_date.isoformat()
        / "tables"
        / "current-and-future-contract-economics-inputs.parquet"
    )
    source = pl.read_parquet(source_path)
    if source.get_column("season").min() != args.as_of_date.year:
        raise ValueError("integrated economics input lacks the current-season row set")
    buyout_payload = json.loads(args.buyout_assumptions.read_text(encoding="utf-8"))
    assumptions = build_assumptions(
        as_of_year=args.as_of_date.year,
        end_season=int(source.get_column("season").max()),
        buyout_payload=buyout_payload,
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
            table_name="phase1_current_and_future_annual_contract_economics",
        ).as_record(),
        "aggregate": write_canonical_parquet(
            result.aggregate,
            output / "aggregate-contract-economics.parquet",
            table_name="phase1_current_and_future_aggregate_contract_economics",
        ).as_record(),
        "reviews": write_canonical_parquet(
            result.reviews,
            output / "contract-economics-reviews.parquet",
            table_name="phase1_current_and_future_contract_economics_reviews",
        ).as_record(),
    }
    available_annual = result.annual.filter(pl.col("calculation_status") == "available")
    available_players = result.aggregate.filter(pl.col("calculation_status") == "available")
    report = {
        "report_schema_version": "0.1",
        "gate": "phase1_current_and_future_contract_economics_research_scenario",
        "as_of_date": args.as_of_date.isoformat(),
        "ranking_status": "research_scenario_not_publishable_model",
        "annual_rows": result.annual.height,
        "current_season_rows": result.annual.filter(
            pl.col("season") == args.as_of_date.year
        ).height,
        "future_rows": result.annual.filter(
            pl.col("season") > args.as_of_date.year
        ).height,
        "available_annual_rows": available_annual.height,
        "review_annual_rows": result.reviews.height,
        "available_players": available_players.height,
        "review_players": result.aggregate.filter(
            pl.col("calculation_status") == "review"
        ).height,
        "review_reasons": result.reviews.group_by("review_reason")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "available_totals": {
            "remaining_and_future_war": float(
                available_annual.get_column("projected_war_mean").sum()
            ),
            "fa_equivalent_value_dollars": float(
                available_annual.get_column("fa_equivalent_value_dollars").sum()
            ),
            "salary_cost_dollars": float(
                available_annual.get_column("salary_cost_dollars").sum()
            ),
            "discounted_contract_value_dollars": float(
                available_players.get_column(
                    "discounted_contract_value_dollars"
                ).sum()
            ),
            "discounted_contract_value_lower_dollars": float(
                available_players.get_column(
                    "discounted_contract_value_lower_dollars"
                ).sum()
            ),
            "discounted_contract_value_upper_dollars": float(
                available_players.get_column(
                    "discounted_contract_value_upper_dollars"
                ).sum()
            ),
        },
        "current_year_market_method": (
            "FanGraphs published 2026 overall dollars per WAR; partial remaining-season "
            "WAR is not assigned to a full-season player tier"
        ),
        "current_year_dollars_per_war": float(
            FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[args.as_of_date.year]
        ),
        "future_market_method": (
            "FanGraphs 2026 three-tier rates grown 3% annually as a named scenario"
        ),
        "ruleset_id": CBA_2027_2032_PLANNING_SCENARIO.ruleset_id,
        "ruleset_kind": CBA_2027_2032_PLANNING_SCENARIO.ruleset_kind,
        "arbitration_model_id": FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        "nominal_discount_rate": NOMINAL_DISCOUNT_RATE,
        "buyout_assumption_id": buyout_payload["snapshot_id"],
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
