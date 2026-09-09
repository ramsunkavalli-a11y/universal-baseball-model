#!/usr/bin/env python3
"""Adapt the 2025 historical value build into the sequential replay contract."""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.historical_replay_inputs import (
    MLB_TEAM_ID_BY_ABBREVIATION,
)
from universal_baseball.sequential_replay import (
    REPLAY_SOURCE_EVIDENCE_SCHEMA,
    replay_value_checkpoints,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


AS_OF_DATE = date(2025, 3, 27)
CHECKPOINT_ID = "phase1-historical-opening-day-2025-03-27"
MODEL_VERSION = "phase1-historical-integrated-value-2025-v1"


def _source_identity(path: Path) -> str:
    return f"local-artifact:{path.as_posix()}:{sha256_file(path)}"


def _bundle_id(paths: tuple[Path, ...]) -> str:
    material = "\n".join(sorted(_source_identity(path) for path in paths)) + "\n"
    return f"phase1-historical-replay-bundle:{sha256(material.encode()).hexdigest()}"


def main() -> int:
    projection_root = Path("reports/generated/historical-projection-paths/2025-03-27")
    value_root = Path("reports/generated/historical-control-value/2025-03-27")
    output = Path("reports/generated/phase1-sequential-replay/2025-03-27")
    hitter_path = projection_root / "tables/hitter-expected-war-paths.parquet"
    pitcher_path = projection_root / "tables/pitcher-expected-war-paths.parquet"
    projection_report_path = projection_root / "report.json"
    owners_path = value_root / "historical-control-owners.parquet"
    annual_input_path = value_root / "annual-contract-economics-inputs.parquet"
    aggregate_path = value_root / "aggregate-contract-economics.parquet"
    value_report_path = value_root / "report.json"
    input_paths = (
        hitter_path,
        pitcher_path,
        projection_report_path,
        owners_path,
        annual_input_path,
        aggregate_path,
        value_report_path,
    )
    for path in input_paths:
        if not path.is_file():
            raise FileNotFoundError(path)

    hitter = pl.read_parquet(hitter_path)
    pitcher = pl.read_parquet(pitcher_path)
    owners = pl.read_parquet(owners_path).with_columns(
        pl.col("team_abbreviation")
        .replace_strict(MLB_TEAM_ID_BY_ABBREVIATION)
        .cast(pl.Int64)
        .alias("organization_id")
    )
    annual = pl.read_parquet(annual_input_path)
    aggregate = pl.read_parquet(aggregate_path)
    whole_player = (
        pl.concat(
            [
                frame.select("player_id", "season", "expected_war")
                for frame in (hitter, pitcher)
            ]
        )
        .group_by("player_id")
        .agg(pl.col("expected_war").sum().alias("expected_remaining_war"))
        .sort("player_id")
    )
    if whole_player.get_column("player_id").n_unique() != whole_player.height:
        raise ValueError("historical projection universe violates player grain")
    owner_lookup = {
        int(row["player_id"]): row for row in owners.iter_rows(named=True)
    }
    aggregate_lookup = {
        int(row["player_id"]): row for row in aggregate.iter_rows(named=True)
    }
    projection_sources = {
        int(group.item(0, "player_id")): "+".join(
            sorted(set(group.get_column("projection_source_id").to_list()))
        )
        for group in annual.partition_by("player_id", maintain_order=True)
    }
    contract_sources = {
        int(group.item(0, "player_id")): "+".join(
            sorted(set(group.get_column("contract_source_id").to_list()))
        )
        for group in annual.partition_by("player_id", maintain_order=True)
    }
    as_of_at = datetime.combine(AS_OF_DATE, time.max, tzinfo=UTC)
    bundle_id = _bundle_id(input_paths)
    universe_rows = []
    record_rows = []
    for projection in whole_player.iter_rows(named=True):
        player_id = int(projection["player_id"])
        owner = owner_lookup.get(player_id)
        economics = aggregate_lookup.get(player_id)
        organization_id = None if owner is None else int(owner["organization_id"])
        rights_state = "unknown_rights" if owner is None else "controlled"
        available = (
            owner is not None
            and economics is not None
            and str(economics["calculation_status"]) == "available"
        )
        universe_rows.append(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "player_id": player_id,
                "organization_id": organization_id,
                "rights_state": rights_state,
            }
        )
        expected_war = float(projection["expected_remaining_war"])
        record_rows.append(
            {
                "checkpoint_id": CHECKPOINT_ID,
                "as_of_at_utc": as_of_at,
                "evidence_cutoff_at_utc": as_of_at,
                "replay_mode": "retrospective_event_cutoff",
                "player_id": player_id,
                "organization_id": organization_id,
                "rights_state": rights_state,
                "last_completed_game_date": None,
                "model_version": MODEL_VERSION,
                "evidence_bundle_id": bundle_id,
                "projection_source_id": projection_sources.get(
                    player_id, "historical_projection_paths_2025_03_27"
                ),
                "contract_source_id": contract_sources.get(
                    player_id,
                    "missing_historical_owner"
                    if owner is None
                    else str(owner["source_snapshot_id"]),
                ),
                "coverage_tier": (
                    "integrated_point_only_no_interval"
                    if available
                    else "review_missing_owner"
                    if owner is None
                    else "review_contract_service_or_control"
                ),
                "calculation_status": "available" if available else "review",
                "expected_remaining_war": expected_war if available else None,
                "expected_remaining_war_lower": expected_war if available else None,
                "expected_remaining_war_upper": expected_war if available else None,
                "expected_remaining_cost_dollars": (
                    float(economics["salary_cost_dollars"]) if available else None
                ),
                "transferable_value_dollars": (
                    float(economics["discounted_contract_value_dollars"])
                    if available
                    else None
                ),
                "transferable_value_lower_dollars": (
                    float(economics["discounted_contract_value_lower_dollars"])
                    if available
                    else None
                ),
                "transferable_value_upper_dollars": (
                    float(economics["discounted_contract_value_upper_dollars"])
                    if available
                    else None
                ),
                "declared_change_reasons": "",
            }
        )

    universes = pl.DataFrame(universe_rows)
    records = pl.DataFrame(record_rows)
    source_evidence = pl.DataFrame(
        [
            {
                "checkpoint_id": CHECKPOINT_ID,
                "source_snapshot_id": _source_identity(projection_report_path),
                "maximum_predictor_event_date": date(2024, 10, 15),
                "knowledge_available_at_utc": None,
            },
            {
                "checkpoint_id": CHECKPOINT_ID,
                "source_snapshot_id": _source_identity(value_report_path),
                "maximum_predictor_event_date": AS_OF_DATE,
                "knowledge_available_at_utc": None,
            },
        ],
        schema=REPLAY_SOURCE_EVIDENCE_SCHEMA,
    )
    result = replay_value_checkpoints(records, universes, source_evidence)

    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "value_records": write_canonical_parquet(
            result.records,
            output / "value-records.parquet",
            table_name="phase1_historical_replay_value_records",
        ).as_record(),
        "checkpoint_summary": write_canonical_parquet(
            result.checkpoints,
            output / "checkpoint-summary.parquet",
            table_name="phase1_historical_replay_checkpoint_summary",
        ).as_record(),
        "delta_ledger": write_canonical_parquet(
            result.deltas,
            output / "delta-ledger.parquet",
            table_name="phase1_historical_replay_delta_ledger",
        ).as_record(),
        "frozen_universe": write_canonical_parquet(
            universes,
            output / "frozen-universe.parquet",
            table_name="phase1_historical_replay_frozen_universe",
        ).as_record(),
        "source_evidence": write_canonical_parquet(
            source_evidence,
            output / "source-evidence.parquet",
            table_name="phase1_historical_replay_source_evidence",
        ).as_record(),
    }
    checkpoint = result.checkpoints.row(0, named=True)
    report = {
        "report_schema_version": "0.1",
        "checkpoint_id": CHECKPOINT_ID,
        "as_of_date": AS_OF_DATE.isoformat(),
        "replay_mode": "retrospective_event_cutoff",
        "status": "historical_opening_day_checkpoint_mechanically_valid",
        "model_version": MODEL_VERSION,
        "evidence_bundle_id": bundle_id,
        "universe_players": int(checkpoint["players"]),
        "available_players": int(checkpoint["available_players"]),
        "review_players": int(checkpoint["review_players"]),
        "unknown_rights_players": records.filter(
            pl.col("rights_state") == "unknown_rights"
        ).height,
        "point_only_players": records.filter(
            pl.col("coverage_tier") == "integrated_point_only_no_interval"
        ).height,
        "totals": {
            "expected_remaining_war": float(checkpoint["expected_remaining_war"]),
            "expected_remaining_cost_dollars": float(
                checkpoint["expected_remaining_cost_dollars"]
            ),
            "transferable_value_dollars": float(
                checkpoint["transferable_value_dollars"]
            ),
        },
        "boundaries": {
            "outcomes_after_cutoff_used": False,
            "vintage_information_claim": False,
            "missing_rights_valued": False,
            "review_rows_valued": False,
            "historical_interval_status": "point_only_not_calibrated",
            "first_checkpoint_has_delta_ledger_rows": False,
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
