#!/usr/bin/env python3
"""Join the 2025 historical projections, control and contract economics."""

from __future__ import annotations

from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.arbitration_market import (
    FANGRAPHS_2026_ARBITRATION_MODEL_ID,
    FANGRAPHS_2026_ARBITRATION_SHARE_BY_CLASS,
)
from universal_baseball.cba_rules import (
    CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO,
)
from universal_baseball.contract_economics import (
    ContractEconomicsAssumptions,
    value_annual_contract_states,
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
from universal_baseball.rights_transactions import project_transaction_payload
from universal_baseball.storage import sha256_file, write_canonical_parquet


AS_OF_DATE = date(2025, 3, 27)
MARKET_GROWTH_RATE = 0.03
NOMINAL_DISCOUNT_RATE = 0.10


def _transaction_rows(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for row in payload["transactions"]:
        if (
            row.get("id") is None
            or (row.get("person") or {}).get("id") is None
            or not str(row.get("typeCode") or "").strip()
        ):
            continue
        transaction_date = date.fromisoformat(str(row["date"]))
        effective = date.fromisoformat(str(row.get("effectiveDate") or row["date"]))
        resolution_text = row.get("resolutionDate")
        resolution = (
            None if not resolution_text else date.fromisoformat(str(resolution_text))
        )
        if (
            date(2024, 10, 15) < effective <= AS_OF_DATE
            and transaction_date <= AS_OF_DATE
            and (
            resolution is None or resolution <= AS_OF_DATE
            )
        ):
            rows.append(row)
    return rows


def _historical_control_owners(
    opening: pl.DataFrame,
    hitter: pl.DataFrame,
    pitcher: pl.DataFrame,
    *,
    roster_path: Path,
    forty_path: Path,
    people_path: Path,
    transaction_paths: tuple[Path, ...],
) -> pl.DataFrame:
    roster = pl.read_parquet(roster_path).select(
        pl.col("snapshot_date").alias("as_of_date"),
        pl.col("snapshot_year").alias("season"),
        "candidate_organization_id",
        "player_id",
        "player_name",
        "source_row_count",
        pl.lit("").alias("source_status_codes"),
        pl.lit(False).alias("source_status_conflict"),
    ).cast(FULL_ROSTER_CANDIDATE_SCHEMA, strict=True)
    forty = pl.read_parquet(forty_path).filter(pl.col("season") == 2024).select(
        list(FORTY_MAN_MEMBERSHIP_SCHEMA)
    )
    transaction_rows = []
    for path in transaction_paths:
        transaction_rows.extend(_transaction_rows(path))
    transaction_source_id = "official_transactions_through_2025_03_27:" + sha256(
        "".join(sha256_file(path) for path in transaction_paths).encode()
    ).hexdigest()
    transactions = project_transaction_payload(
        {"transactions": transaction_rows},
        as_of_date=AS_OF_DATE,
        source_snapshot_id=transaction_source_id,
    )
    resolved = resolve_current_organizations(
        roster,
        forty,
        transactions,
        as_of_date=AS_OF_DATE,
        mlb_team_ids=set(MLB_TEAM_ID_BY_ABBREVIATION.values()),
    )
    prior = resolved.filter(pl.col("organization_id").is_not_null()).select(
        "player_id",
        "organization_id",
        "organization_status",
        "organization_evidence",
    )
    opening_owner = opening.filter(pl.col("team_abbreviation") != "").select(
        "player_id",
        pl.col("team_abbreviation")
        .replace_strict(MLB_TEAM_ID_BY_ABBREVIATION)
        .cast(pl.Int64)
        .alias("opening_organization_id"),
        "service_days",
        "source_snapshot_id",
    )
    people = pl.read_parquet(people_path).select("player_id", "mlb_debut_date")
    players = pl.concat(
        [
            hitter.select("player_id"),
            pitcher.select("player_id"),
        ]
    ).unique()
    abbreviations = {
        organization_id: abbreviation
        for abbreviation, organization_id in MLB_TEAM_ID_BY_ABBREVIATION.items()
    }
    return (
        players.join(opening_owner, on="player_id", how="left", validate="1:1")
        .join(prior, on="player_id", how="left", validate="1:1")
        .join(people, on="player_id", how="left", validate="1:1")
        .with_columns(
            pl.coalesce("opening_organization_id", "organization_id").alias(
                "resolved_organization_id"
            )
        )
        .filter(pl.col("resolved_organization_id").is_not_null())
        .with_columns(
            pl.col("resolved_organization_id")
            .replace_strict(abbreviations)
            .alias("team_abbreviation"),
            pl.when(pl.col("service_days").is_not_null())
            .then(pl.col("service_days"))
            .when(
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date") >= pl.lit(AS_OF_DATE))
            )
            .then(pl.lit(0, dtype=pl.Int64))
            .otherwise(pl.lit(None, dtype=pl.Int64))
            .alias("service_days"),
            pl.when(pl.col("source_snapshot_id").is_not_null())
            .then(pl.col("source_snapshot_id"))
            .otherwise(pl.col("organization_evidence"))
            .alias("source_snapshot_id"),
            pl.when(pl.col("opening_organization_id").is_not_null())
            .then(pl.lit("fangraphs_opening_day"))
            .otherwise(pl.col("organization_status"))
            .alias("owner_basis"),
            pl.when(pl.col("service_days").is_not_null())
            .then(pl.lit("fangraphs_opening_day"))
            .when(
                pl.col("mlb_debut_date").is_null()
                | (pl.col("mlb_debut_date") >= pl.lit(AS_OF_DATE))
            )
            .then(pl.lit("official_no_pre_cutoff_mlb_debut_zero"))
            .otherwise(pl.lit("missing_prior_mlb_service"))
            .alias("service_basis"),
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


def main() -> int:
    projection_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    opening_path = Path(
        "reports/generated/fangraphs-opening-day-control/2025/"
        "opening-day-control-baseline.parquet"
    )
    term_path = Path(
        "reports/generated/historical-contract-bridge/2025/"
        "valuation-ready-terms.parquet"
    )
    roster_path = Path(
        "reports/generated/opportunity-history-sources-v2/tables/2024/"
        "full_roster_details.parquet"
    )
    forty_path = Path(
        "reports/generated/opportunity-40man-history/tables/"
        "historical_40man_membership.parquet"
    )
    people_path = Path(
        "reports/generated/league-control/2026-09-08/league-control-snapshot.parquet"
    )
    transaction_paths = (
        Path("reports/generated/injury-return-history/captures/transactions-2024.json"),
        Path("reports/generated/injury-return-history/captures/transactions-2025.json"),
    )
    output = Path("reports/generated/historical-control-value/2025-03-27")
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"

    hitter = pl.read_parquet(hitter_path)
    pitcher = pl.read_parquet(pitcher_path)
    opening = pl.read_parquet(opening_path)
    terms = pl.read_parquet(term_path)
    control_owners = _historical_control_owners(
        opening,
        hitter,
        pitcher,
        roster_path=roster_path,
        forty_path=forty_path,
        people_path=people_path,
        transaction_paths=transaction_paths,
    )
    build = build_historical_replay_economics_inputs(
        hitter,
        pitcher,
        control_owners,
        terms,
        as_of_date=AS_OF_DATE,
        projection_source_id="historical_projection_paths_2025_03_27",
    )

    base_rate = float(FANGRAPHS_HISTORICAL_OVERALL_DOLLARS_PER_WAR[2025])
    market = {
        season: base_rate * (1.0 + MARKET_GROWTH_RATE) ** (season - 2025)
        for season in range(2025, 2030)
    }
    assumptions = ContractEconomicsAssumptions(
        assumptions_id="historical_2025_replay_market3pct_discount10pct",
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
        "annual_inputs": write_canonical_parquet(
            build.annual_inputs,
            output / "annual-contract-economics-inputs.parquet",
            table_name="historical_2025_annual_contract_economics_inputs",
        ).as_record(),
        "coverage_reviews": write_canonical_parquet(
            build.reviews,
            output / "historical-control-coverage-reviews.parquet",
            table_name="historical_2025_control_coverage_reviews",
        ).as_record(),
        "annual_value": write_canonical_parquet(
            valued.annual,
            output / "annual-contract-economics.parquet",
            table_name="historical_2025_annual_contract_economics",
        ).as_record(),
        "aggregate_value": write_canonical_parquet(
            valued.aggregate,
            output / "aggregate-contract-economics.parquet",
            table_name="historical_2025_aggregate_contract_economics",
        ).as_record(),
        "value_reviews": write_canonical_parquet(
            valued.reviews,
            output / "contract-economics-reviews.parquet",
            table_name="historical_2025_contract_economics_reviews",
        ).as_record(),
    }
    available = valued.annual.filter(pl.col("calculation_status") == "available")
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_control_value_join",
        "as_of_date": AS_OF_DATE.isoformat(),
        "ranking_status": "retrospective_phase1_replay_not_publishable_ranking",
        "coverage": build.coverage,
        "owner_basis": control_owners.group_by("owner_basis")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "service_basis": control_owners.group_by("service_basis")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "official_transaction_rows_used": sum(
            len(_transaction_rows(path)) for path in transaction_paths
        ),
        "available_annual_rows": available.height,
        "review_annual_rows": valued.reviews.height,
        "available_players": valued.aggregate.filter(
            pl.col("calculation_status") == "available"
        ).height,
        "review_players": valued.aggregate.filter(
            pl.col("calculation_status") == "review"
        ).height,
        "known_salary_rows": build.coverage["known_salary_rows"],
        "contract_source_identity_review_rows": terms.filter(
            pl.col("contract_status") == "identity_unresolved"
        ).height,
        "review_reasons": valued.reviews.group_by("review_reason")
        .len()
        .sort("len", descending=True)
        .to_dicts(),
        "available_discounted_control_value_dollars": float(
            available.get_column("discounted_contract_value_dollars").sum()
        ),
        "market_reference_2025_dollars_per_war": base_rate,
        "market_growth_rate": MARKET_GROWTH_RATE,
        "nominal_discount_rate": NOMINAL_DISCOUNT_RATE,
        "ruleset_id": CBA_2025_2029_HISTORICAL_REPLAY_SCENARIO.ruleset_id,
        "boundaries": {
            "opening_team_assumed_constant_during_incumbent_control": True,
            "missing_opening_owner_valued": False,
            "missing_opening_service_invented": False,
            "unresolved_options_valued": False,
            "contract_identity_reviews_applied": False,
            "post_2026_cba": "explicit_3pct_planning_scenario_not_fact",
            "market_reference": "later_retrospective_evidence_not_vintage_input",
        },
        "source_files": {
            path.as_posix(): sha256_file(path)
            for path in (
                hitter_path,
                pitcher_path,
                opening_path,
                term_path,
                roster_path,
                forty_path,
                people_path,
                *transaction_paths,
            )
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "storage"},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
