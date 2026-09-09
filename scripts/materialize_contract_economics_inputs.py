#!/usr/bin/env python3
"""Materialize current whole-player WAR, control, and known contract inputs."""

from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.contract_buyouts import link_option_buyouts
from universal_baseball.contract_economics_inputs import (
    UNCERTAINTY_PROJECTION_SOURCE_ID,
    build_future_contract_economics_inputs,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--uncertainty-root", type=Path,
        default=Path("reports/generated/current-war-uncertainty"),
    )
    parser.add_argument(
        "--war-root", type=Path,
        default=Path("reports/generated/current-conditional-war-paths"),
    )
    parser.add_argument(
        "--control-root", type=Path,
        default=Path("reports/generated/league-control"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/current-contract-economics-inputs"),
    )
    parser.add_argument(
        "--secondary-contract-terms",
        type=Path,
        default=Path("config/secondary-contract-terms-2026-09-09.json"),
    )
    parser.add_argument(
        "--secondary-contract-reviews",
        type=Path,
        default=Path("config/secondary-contract-structure-reviews-2026-09-09.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    dated_war_root = args.war_root / args.as_of_date.isoformat() / "tables"
    dated_control_root = args.control_root / args.as_of_date.isoformat()
    contract_years = pl.read_parquet(
        dated_control_root / "contract-year-liabilities.parquet"
    )
    buyout_links = link_option_buyouts(
        contract_years,
        pl.read_parquet(dated_control_root / "payroll-other-payments.parquet"),
    )
    secondary_payload = json.loads(
        args.secondary_contract_terms.read_text(encoding="utf-8")
    )
    secondary_terms = pl.DataFrame(secondary_payload["terms"]).with_columns(
        pl.lit(secondary_payload["snapshot_id"]).alias("source_snapshot_id")
    )
    secondary_review_payload = json.loads(
        args.secondary_contract_reviews.read_text(encoding="utf-8")
    )
    secondary_reviews = pl.DataFrame(
        secondary_review_payload["reviews"]
    ).with_columns(
        pl.lit(secondary_review_payload["snapshot_id"]).alias("source_snapshot_id")
    )
    result = build_future_contract_economics_inputs(
        pl.read_parquet(dated_war_root / "hitter_expected_war_paths.parquet"),
        pl.read_parquet(dated_war_root / "pitcher_expected_war_paths.parquet"),
        pl.read_parquet(dated_control_root / "future-control-path.parquet"),
        contract_years,
        pl.read_parquet(
            args.uncertainty_root / args.as_of_date.isoformat()
            / "tables/whole-player-war-uncertainty.parquet"
        ),
        option_buyouts=buyout_links.links,
        secondary_contract_terms=secondary_terms,
        secondary_contract_reviews=secondary_reviews,
    )
    output_root = args.output_root / args.as_of_date.isoformat()
    output_root.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        result.annual_inputs,
        output_root / "annual-contract-economics-inputs.parquet",
        table_name="annual_contract_economics_inputs",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "current_whole_player_contract_economics_inputs",
        "as_of_date": args.as_of_date.isoformat(),
        "projection_source_id": UNCERTAINTY_PROJECTION_SOURCE_ID,
        "coverage": result.coverage,
        "war_policy": "hitter plus pitcher expected WAR; two-way production is summed",
        "salary_policy": "accepted player-linked payroll terms only; missing is null",
        "buyout_policy": (
            "contingent option buyouts linked by exact team/name within the same "
            "FanGraphs payroll workbook, plus a small fail-closed Spotrac exception "
            "overlay; non-contingent paid buyouts are not option rights"
        ),
        "secondary_contract_terms": {
            "snapshot_id": secondary_payload["snapshot_id"],
            "retrieved_date": secondary_payload["retrieved_date"],
            "rows": len(secondary_payload["terms"]),
            "boundary": secondary_payload["boundary"],
        },
        "secondary_contract_structure_reviews": {
            "snapshot_id": secondary_review_payload["snapshot_id"],
            "retrieved_date": secondary_review_payload["retrieved_date"],
            "rows": len(secondary_review_payload["reviews"]),
            "boundary": secondary_review_payload["boundary"],
        },
        "buyout_link_coverage": buyout_links.coverage,
        "ranking_status": "not_publishable_inputs_only",
        "remaining_economics_inputs": [
            "chronologically fitted free-agent dollars per WAR",
            "chronologically fitted arbitration shares",
            "post-2026 CBA minimum salary rules",
            "player-ID-linked option buyouts and unresolved option triggers",
        ],
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"gate": report["gate"], "coverage": result.coverage}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
