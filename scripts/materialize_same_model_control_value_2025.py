#!/usr/bin/env python3
"""Join October 2025 same-model projections to cutoff-safe control and value."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_MODEL_ID,
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)
from universal_baseball.cba_rules import CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO
from universal_baseball.contract_economics import (
    ContractEconomicsAssumptions,
    value_annual_contract_states,
)
from universal_baseball.control_events import (
    classify_control_transactions,
    materialize_control_stints,
)
from universal_baseball.free_agent_market import (
    FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR,
)
from universal_baseball.historical_replay_inputs import (
    MLB_TEAM_ID_BY_ABBREVIATION,
    build_historical_replay_economics_inputs,
)
from universal_baseball.organization_rights import resolve_current_organizations
from universal_baseball.playing_time_roster_source import (
    FORTY_MAN_MEMBERSHIP_SCHEMA,
    FULL_ROSTER_CANDIDATE_SCHEMA,
)
from universal_baseball.roster_entry_source import build_opening_control_states
from universal_baseball.storage import sha256_file, write_canonical_parquet
from universal_baseball.team_control import (
    SEASON_WINDOW_SCHEMA,
    calculate_control_years,
)


AS_OF_DATE = date(2025, 10, 15)
SEASON_START = date(2025, 3, 27)
SEASON_END = date(2025, 9, 28)
THROUGH_YEAR = 2029
MARKET_GROWTH_RATE = 0.03
NOMINAL_DISCOUNT_RATE = 0.10


def _service_snapshot(
    opening: pl.DataFrame,
    people: pl.DataFrame,
    roster_entries: pl.DataFrame,
    transactions: pl.DataFrame,
    *,
    mlb_team_ids: set[int],
    source_id: str,
) -> tuple[pl.DataFrame, dict[str, int]]:
    window = pl.DataFrame(
        [{"season": 2025, "start_date": SEASON_START, "end_date": SEASON_END}],
        schema=SEASON_WINDOW_SCHEMA,
    )
    openings = build_opening_control_states(
        roster_entries, window, mlb_team_ids=mlb_team_ids
    )
    events = classify_control_transactions(
        transactions, mlb_team_ids=mlb_team_ids
    ).filter(pl.col("season") == 2025)
    materialized = materialize_control_stints(
        openings.opening_states, events, window, as_of_date=AS_OF_DATE
    )
    current = calculate_control_years(
        materialized.stints, window, as_of_date=AS_OF_DATE
    ).select(
        "player_id", pl.col("service_days").alias("current_service_days")
    )
    opening_service = opening.select(
        "player_id",
        pl.col("service_days").alias("opening_service_days"),
        pl.col("source_snapshot_id").alias("opening_source_snapshot_id"),
    )
    service = (
        people.select("player_id", "mlb_debut_date", "source_snapshot_id")
        .join(opening_service, on="player_id", how="left", validate="1:1")
        .join(current, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.when(pl.col("opening_service_days").is_not_null())
            .then(pl.col("opening_service_days"))
            .when(
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date") >= pl.lit(SEASON_START))
            )
            .then(pl.lit(0, dtype=pl.Int64))
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("resolved_opening_service_days"),
            pl.when(pl.col("current_service_days").is_not_null())
            .then(pl.col("current_service_days"))
            .when(
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date") > pl.lit(SEASON_END))
            )
            .then(pl.lit(0, dtype=pl.Int64))
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("resolved_current_service_days"),
        )
        .with_columns(
            pl.when(
                pl.col("resolved_opening_service_days").is_not_null()
                & pl.col("resolved_current_service_days").is_not_null()
            )
            .then(
                pl.col("resolved_opening_service_days")
                + pl.col("resolved_current_service_days")
            )
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("service_days"),
            pl.when(pl.col("opening_service_days").is_not_null())
            .then(pl.lit("fangraphs_opening_plus_official_2025_intervals"))
            .when(
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date") >= pl.lit(SEASON_START))
            )
            .then(pl.lit("official_zero_opening_plus_official_2025_intervals"))
            .otherwise(pl.lit("missing_prior_mlb_service"))
            .alias("service_basis"),
            pl.concat_str(
                pl.col("opening_source_snapshot_id").fill_null("no_opening_baseline"),
                pl.lit("+"),
                pl.lit(source_id),
            ).alias("service_source_snapshot_id"),
        )
        .select(
            "player_id",
            "service_days",
            "service_basis",
            "service_source_snapshot_id",
        )
        .sort("player_id")
    )
    return service, {
        "opening_state_players": openings.opening_states.get_column(
            "player_id"
        ).n_unique(),
        "opening_state_review_players": openings.review_players.get_column(
            "player_id"
        ).n_unique(),
        "classified_transaction_rows": events.height,
        "unmapped_transaction_rows": materialized.review_events.height,
        "calculated_current_service_players": current.height,
        "resolved_total_service_players": service.filter(
            pl.col("service_days").is_not_null()
        ).height,
        "missing_total_service_players": service.filter(
            pl.col("service_days").is_null()
        ).height,
    }


def _control_owners(
    hitter: pl.DataFrame,
    pitcher: pl.DataFrame,
    roster: pl.DataFrame,
    forty: pl.DataFrame,
    transactions: pl.DataFrame,
    service: pl.DataFrame,
    *,
    source_id: str,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    mlb_team_ids = set(MLB_TEAM_ID_BY_ABBREVIATION.values())
    roster_candidates = roster.select(
        pl.col("snapshot_date").alias("as_of_date"),
        pl.col("snapshot_year").alias("season"),
        "candidate_organization_id",
        "player_id",
        "player_name",
        "source_row_count",
        pl.lit("").alias("source_status_codes"),
        pl.lit(False).alias("source_status_conflict"),
    ).cast(FULL_ROSTER_CANDIDATE_SCHEMA, strict=True)
    forty = forty.filter(pl.col("season") == 2025).select(
        list(FORTY_MAN_MEMBERSHIP_SCHEMA)
    )
    resolved = resolve_current_organizations(
        roster_candidates,
        forty,
        transactions,
        as_of_date=AS_OF_DATE,
        mlb_team_ids=mlb_team_ids,
    )
    universe = pl.concat(
        [hitter.select("player_id"), pitcher.select("player_id")]
    ).unique()
    abbreviations = {
        organization_id: abbreviation
        for abbreviation, organization_id in MLB_TEAM_ID_BY_ABBREVIATION.items()
    }
    owners = (
        universe.join(resolved, on="player_id", how="left", validate="1:1")
        .join(service, on="player_id", how="left", validate="1:1")
        .filter(pl.col("organization_id").is_not_null())
        .with_columns(
            pl.col("organization_id")
            .replace_strict(abbreviations)
            .alias("team_abbreviation"),
            pl.concat_str(
                pl.col("organization_evidence"),
                pl.lit("+"),
                pl.col("service_source_snapshot_id"),
                pl.lit("+"),
                pl.lit(source_id),
            ).alias("source_snapshot_id"),
            pl.col("organization_status").alias("owner_basis"),
        )
        .select(
            "player_id",
            "team_abbreviation",
            "service_days",
            "source_snapshot_id",
            "owner_basis",
            "service_basis",
        )
        .sort("player_id")
    )
    return owners, resolved


def main() -> int:
    projection_root = Path("reports/generated/historical-projection-paths/2025-10-15")
    people_root = Path("reports/generated/historical-people-control/2025-10-15")
    opening_path = Path(
        "reports/generated/fangraphs-opening-day-control/2025/"
        "opening-day-control-baseline.parquet"
    )
    term_path = Path(
        "reports/generated/historical-contract-bridge/2025/valuation-ready-terms.parquet"
    )
    roster_path = Path(
        "reports/generated/opportunity-history-sources-v2/tables/2025/"
        "full_roster_details.parquet"
    )
    forty_path = Path(
        "reports/generated/opportunity-40man-history/tables/"
        "historical_40man_membership.parquet"
    )
    output = Path("reports/generated/historical-control-value/2025-10-15")
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"
    people_path = people_root / "tables/people.parquet"
    roster_entries_path = people_root / "tables/roster-entries.parquet"
    transactions_path = people_root / "tables/transactions.parquet"
    people_report_path = people_root / "report.json"

    hitter = pl.read_parquet(hitter_path).filter(pl.col("season") <= THROUGH_YEAR)
    pitcher = pl.read_parquet(pitcher_path).filter(pl.col("season") <= THROUGH_YEAR)
    opening = pl.read_parquet(opening_path)
    people = pl.read_parquet(people_path)
    roster_entries = pl.read_parquet(roster_entries_path)
    transactions = pl.read_parquet(transactions_path)
    source_id = f"historical_people_control_2025_10_15:{sha256_file(people_report_path)}"
    service, service_coverage = _service_snapshot(
        opening,
        people,
        roster_entries,
        transactions,
        mlb_team_ids=set(MLB_TEAM_ID_BY_ABBREVIATION.values()),
        source_id=source_id,
    )
    owners, organization_resolution = _control_owners(
        hitter,
        pitcher,
        pl.read_parquet(roster_path),
        pl.read_parquet(forty_path),
        transactions,
        service,
        source_id=source_id,
    )
    build = build_historical_replay_economics_inputs(
        hitter,
        pitcher,
        owners,
        pl.read_parquet(term_path),
        as_of_date=AS_OF_DATE,
        projection_source_id="same_model_projection_paths_2025_10_15",
    )

    base_rate = float(FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[2025])
    market = {
        season: base_rate * (1.0 + MARKET_GROWTH_RATE) ** (season - 2025)
        for season in range(2026, THROUGH_YEAR + 1)
    }
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="historical_2025_10_15_same_market3pct_discount10pct",
        market_model_id="fangraphs_2025_historical_overall_growth_0.03",
        arbitration_model_id=FANGRAPHS_2026_ARBITRATION_MODEL_ID,
        dollars_per_war_by_year=market,
        arbitration_share_by_class=dict(
            FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS
        ),
        annual_discount_rate=NOMINAL_DISCOUNT_RATE,
    )
    valued = value_annual_contract_states(
        build.annual_inputs,
        cba_ruleset=CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO,
        assumptions=assumptions,
    )

    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "service": write_canonical_parquet(
            service,
            output / "historical-service-snapshot.parquet",
            table_name="historical_2025_10_15_service_snapshot",
        ).as_record(),
        "organization_resolution": write_canonical_parquet(
            organization_resolution,
            output / "historical-organization-resolution.parquet",
            table_name="historical_2025_10_15_organization_resolution",
        ).as_record(),
        "control_owners": write_canonical_parquet(
            owners,
            output / "historical-control-owners.parquet",
            table_name="historical_2025_10_15_control_owners",
        ).as_record(),
        "annual_inputs": write_canonical_parquet(
            build.annual_inputs,
            output / "annual-contract-economics-inputs.parquet",
            table_name="historical_2025_10_15_annual_inputs",
        ).as_record(),
        "coverage_reviews": write_canonical_parquet(
            build.reviews,
            output / "historical-control-coverage-reviews.parquet",
            table_name="historical_2025_10_15_control_reviews",
        ).as_record(),
        "annual_value": write_canonical_parquet(
            valued.annual,
            output / "annual-contract-economics.parquet",
            table_name="historical_2025_10_15_annual_value",
        ).as_record(),
        "aggregate_value": write_canonical_parquet(
            valued.aggregate,
            output / "aggregate-contract-economics.parquet",
            table_name="historical_2025_10_15_aggregate_value",
        ).as_record(),
        "value_reviews": write_canonical_parquet(
            valued.reviews,
            output / "contract-economics-reviews.parquet",
            table_name="historical_2025_10_15_value_reviews",
        ).as_record(),
    }
    available = valued.annual.filter(pl.col("calculation_status") == "available")
    source_paths = (
        hitter_path,
        pitcher_path,
        people_path,
        roster_entries_path,
        transactions_path,
        people_report_path,
        opening_path,
        term_path,
        roster_path,
        forty_path,
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "same_model_2025_10_15_control_value_join",
        "as_of_date": AS_OF_DATE.isoformat(),
        "forecast_seasons": list(range(2026, THROUGH_YEAR + 1)),
        "ranking_status": "retrospective_phase1_replay_not_publishable_ranking",
        "coverage": build.coverage,
        "service_coverage": service_coverage,
        "owner_basis": owners.group_by("owner_basis")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "service_basis": owners.group_by("service_basis")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "available_annual_rows": available.height,
        "review_annual_rows": valued.reviews.height,
        "available_players": valued.aggregate.filter(
            pl.col("calculation_status") == "available"
        ).height,
        "review_players": valued.aggregate.filter(
            pl.col("calculation_status") == "review"
        ).height,
        "review_reasons": valued.reviews.group_by("review_reason")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "available_discounted_control_value_dollars": float(
            available.get_column("discounted_contract_value_dollars").sum()
        ),
        "ruleset_id": CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO.ruleset_id,
        "boundaries": {
            "2026_outcomes_used": False,
            "future_team_depth_used": False,
            "owner_uses_2025_10_15_official_roster_state": True,
            "service_uses_2025_opening_balance_plus_official_intervals": True,
            "contract_terms_frozen_from_march_replay": True,
            "post_cutoff_contract_changes_invented": False,
            "missing_owner_or_service_valued": False,
            "contract_source_is_later_retrieved_not_true_vintage": True,
            "post_2026_cba": "explicit_3pct_planning_scenario_not_fact",
        },
        "source_files": {path.as_posix(): sha256_file(path) for path in source_paths},
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
