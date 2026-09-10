#!/usr/bin/env python3
"""Build the first Phase 2 current-value preview."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, time
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


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--input-root",
        type=Path,
        default=Path("reports/generated/current-rest-of-season-v2"),
    )
    parser.add_argument(
        "--phase1-replay-root",
        type=Path,
        default=Path("reports/generated/phase1-sequential-replay"),
    )
    parser.add_argument(
        "--control-root", type=Path, default=Path("reports/generated/league-control")
    )
    parser.add_argument(
        "--model-fv-root",
        type=Path,
        default=Path("reports/generated/phase2-model-fv"),
    )
    parser.add_argument(
        "--nested-career-fv-root",
        type=Path,
        default=Path("reports/generated/phase2-nested-career-fv"),
    )
    parser.add_argument(
        "--war-uncertainty-root",
        type=Path,
        default=Path("reports/generated/phase2-war-uncertainty"),
    )
    parser.add_argument(
        "--output-root", type=Path, default=Path("reports/generated/phase2-current-value")
    )
    parser.add_argument(
        "--buyout-assumptions",
        type=Path,
        default=Path("config/contract-buyout-assumptions-2026-09-09.json"),
    )
    return parser.parse_args()


def _assumptions(end_season: int, buyouts: dict[str, object]) -> ContractEconomicsAssumptions:
    market = build_fangraphs_2026_market_scenario(
        start_season=2026, end_season=end_season, annual_growth_rate=0.03
    )
    market.pop(2026)
    return ContractEconomicsAssumptions(
        assumptions_id="phase2_preview_anchor_tier_sequential_decisions_2026_09_09",
        market_model_id=FANGRAPHS_2026_MARKET_REFERENCE_ID + "_first_future_year_proxy",
        arbitration_model_id=FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        dollars_per_war_by_year={
            2026: float(FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[2026])
        },
        arbitration_share_by_class=dict(FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS),
        annual_discount_rate=0.10,
        tiered_dollars_per_war_by_year=market,
        missing_buyout_share_by_status={
            str(row["control_status"]): float(row["buyout_share_of_option_salary"])
            for row in list(buyouts["assumptions"])
        },
        market_tier_assignment="first_full_future_season",
        sequential_non_tender=True,
    )


def main() -> int:
    args = _args()
    dated = args.as_of_date.isoformat()
    source_path = (
        args.input_root / dated / "tables/current-and-future-contract-economics-inputs.parquet"
    )
    source = pl.read_parquet(source_path)
    future_war = pl.read_parquet(
        args.war_uncertainty_root
        / dated
        / "tables/whole-player-war-uncertainty.parquet"
    ).select(
        "player_id", "season",
        pl.col("projected_war_mean").alias("phase2_war_mean"),
        pl.col("projected_war_lower").alias("phase2_war_lower"),
        pl.col("projected_war_upper").alias("phase2_war_upper"),
    )
    source = (
        source.join(future_war, on=["player_id", "season"], how="left")
        .with_columns(
            pl.coalesce("phase2_war_mean", "projected_war_mean").alias("projected_war_mean"),
            pl.coalesce("phase2_war_lower", "projected_war_lower").alias("projected_war_lower"),
            pl.coalesce("phase2_war_upper", "projected_war_upper").alias("projected_war_upper"),
        )
        .drop("phase2_war_mean", "phase2_war_lower", "phase2_war_upper")
    )
    buyouts = json.loads(args.buyout_assumptions.read_text(encoding="utf-8"))
    economics = value_annual_contract_states(
        source,
        cba_ruleset=CBA_2027_2032_PLANNING_SCENARIO,
        assumptions=_assumptions(int(source.get_column("season").max()), buyouts),
    )
    phase1 = pl.read_parquet(args.phase1_replay_root / dated / "value-records.parquet")
    control = pl.read_parquet(args.control_root / dated / "league-control-snapshot.parquet")
    model_fv = pl.read_parquet(args.model_fv_root / dated / "model-fv.parquet")
    nested_fv = pl.read_parquet(
        args.nested_career_fv_root / dated / "nested-career-model-fv.parquet"
    )
    fv_by_id = {
        int(row["player_id"]): row
        for row in model_fv.iter_rows(named=True)
    }
    nested_fv_by_id = {
        int(row["player_id"]): row
        for row in nested_fv.iter_rows(named=True)
    }
    aggregate_by_id = {
        int(row["player_id"]): row for row in economics.aggregate.iter_rows(named=True)
    }
    annual_by_id = {
        int(group.item(0, "player_id")): group
        for group in economics.annual.partition_by("player_id", maintain_order=True)
    }
    phase1_by_id = {int(row["player_id"]): row for row in phase1.iter_rows(named=True)}
    rows: list[dict[str, object]] = []
    for player in control.iter_rows(named=True):
        player_id = int(player["player_id"])
        old = phase1_by_id[player_id]
        fv = fv_by_id.get(player_id)
        nested = nested_fv_by_id.get(player_id)
        no_debut = player["mlb_debut_date"] is None
        released = old["rights_state"] == "no_incumbent_rights"
        annual = annual_by_id.get(player_id)
        aggregate = aggregate_by_id.get(player_id)
        controlled_war = war_lower = war_upper = None
        if annual is not None:
            retained = annual.filter(
                ~pl.col("decision_at_mean").is_in(
                    ["no_incumbent_rights", "prior_non_tender_no_incumbent_rights"]
                )
            )
            controlled_war = float(retained.get_column("projected_war_mean").sum())
            war_lower = float(retained.get_column("projected_war_lower").sum())
            war_upper = float(retained.get_column("projected_war_upper").sum())
        if released:
            status = "available"
            value = lower = upper = cost = controlled_war = war_lower = war_upper = 0.0
            method = "no_incumbent_rights"
            coverage = "talent_only_no_incumbent_rights"
        elif no_debut and fv is not None and nested is not None:
            status = "available"
            value = float(nested["nested_talent_benchmark_value_dollars"])
            lower = upper = None
            war_lower = war_upper = None
            cost = None
            controlled_war = float(nested["three_tier_expected_six_year_war"])
            method = "nested_career_model_fv_pre_mlb_benchmark_value"
            coverage = "phase2_nested_career_model_fv_no_contract_interval"
        elif no_debut:
            status = "review"
            value = lower = upper = cost = controlled_war = war_lower = war_upper = None
            method = "missing_internal_model_fv"
            coverage = "review_non_debuted_without_model_fv"
        elif aggregate is None or aggregate["calculation_status"] != "available":
            status = "review"
            value = lower = upper = cost = war_lower = war_upper = None
            method = "phase2_mlb_contract_economics_review"
            coverage = "review_missing_or_blocked_economics"
        else:
            status = "available"
            value = float(aggregate["discounted_contract_value_dollars"])
            lower = float(aggregate["discounted_contract_value_lower_dollars"])
            upper = float(aggregate["discounted_contract_value_upper_dollars"])
            cost = float(aggregate["salary_cost_dollars"])
            method = "phase2_mlb_anchor_tier_sequential_decisions"
            coverage = "phase2_mlb_integrated_available"
        rows.append(
            {
                **old,
                "checkpoint_id": f"phase2-preview-{dated}",
                "as_of_at_utc": datetime.combine(args.as_of_date, time.max, tzinfo=UTC),
                "calculation_status": status,
                "coverage_tier": coverage,
                "expected_remaining_war": controlled_war,
                "expected_remaining_war_lower": war_lower,
                "expected_remaining_war_upper": war_upper,
                "expected_controlled_war": controlled_war,
                "statsapi_projected_war": (
                    None if fv is None else controlled_war if no_debut else fv["expected_six_year_war"]
                ),
                "expected_remaining_cost_dollars": cost,
                "transferable_value_dollars": value,
                "transferable_value_lower_dollars": lower,
                "transferable_value_upper_dollars": upper,
                "value_method": method,
                "model_fv_granular": (
                    None if fv is None else nested["three_tier_model_fv_granular"]
                    if no_debut and nested is not None else fv["model_fv_granular"]
                ),
                "model_fv_display": (
                    None if fv is None else nested["three_tier_model_fv_display"]
                    if no_debut and nested is not None else fv["model_fv_display"]
                ),
                "model_role": None if fv is None else fv["model_role"],
                "model_player_type": None if fv is None else fv["model_player_type"],
                "model_arrival_probability": (
                    None if fv is None else fv["model_arrival_probability"]
                ),
                "arrival_probability_source": (
                    None if fv is None else fv["arrival_probability_source"]
                ),
                "model_meaningful_role_probability": (
                    None if fv is None else fv["model_meaningful_role_probability"]
                ),
                "model_established_role_probability": (
                    None if fv is None else fv["model_established_role_probability"]
                ),
                "talent_benchmark_value_dollars": (
                    None if fv is None else nested["nested_talent_benchmark_value_dollars"]
                    if no_debut and nested is not None
                    else fv["talent_benchmark_value_dollars"]
                ),
                "star_outcome_probability": (
                    None if fv is None or no_debut else fv["star_outcome_probability"]
                ),
            }
        )
    values = pl.DataFrame(rows, infer_schema_length=None).sort("player_id")
    output = args.output_root / dated
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "values": write_canonical_parquet(
            values, output / "value-records.parquet", table_name="phase2_current_value_records"
        ).as_record(),
        "annual": write_canonical_parquet(
            economics.annual,
            output / "annual-contract-economics.parquet",
            table_name="phase2_current_annual_contract_economics",
        ).as_record(),
        "aggregate": write_canonical_parquet(
            economics.aggregate,
            output / "aggregate-contract-economics.parquet",
            table_name="phase2_current_aggregate_contract_economics",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "phase2_current_value_preview",
        "as_of_date": dated,
        "ranking_status": "private_preview_not_publishable",
        "players": values.height,
        "available_players": values.filter(pl.col("calculation_status") == "available").height,
        "review_players": values.filter(pl.col("calculation_status") == "review").height,
        "internal_model_fv_players": values.filter(
            pl.col("model_fv_granular").is_not_null()
        ).height,
        "nested_career_pre_mlb_players": values.filter(
            pl.col("value_method")
            == "nested_career_model_fv_pre_mlb_benchmark_value"
        ).height,
        "nested_probability_ordering_failures": values.filter(
            pl.col("model_established_role_probability").is_not_null()
            & (
                (pl.col("model_meaningful_role_probability") > pl.col("model_arrival_probability"))
                | (
                    pl.col("model_established_role_probability")
                    > pl.col("model_meaningful_role_probability")
                )
            )
        ).height,
        "pre_mlb_star_probability_nonnull": values.filter(
            (pl.col("value_method") == "nested_career_model_fv_pre_mlb_benchmark_value")
            & pl.col("star_outcome_probability").is_not_null()
        ).height,
        "non_debuted_missing_model_fv": values.filter(
            pl.col("value_method") == "missing_internal_model_fv"
        ).height,
        "boundaries": {
            "publication_player_grades_used_as_inputs": False,
            "model_fv_is_separate_from_contract_status": True,
            "pre_mlb_value_uses_model_fv_benchmark": True,
            "pre_mlb_value_uses_nested_conditional_career_hurdle": True,
            "pre_mlb_star_probability_withheld_pending_uncertainty_refit": True,
            "market_tier_anchor_is_current_first_future_year_proxy": True,
            "successor_cba_is_planning_scenario": True,
            "phase2_workload_correction_included": True,
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
