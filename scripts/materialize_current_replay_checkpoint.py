#!/usr/bin/env python3
"""Adapt the current integrated value scenario into the replay contract."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime, time
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.sequential_replay import (
    REPLAY_SOURCE_EVIDENCE_SCHEMA,
    replay_value_checkpoints,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


MODEL_VERSION = "phase1-integrated-value-v2-2026-09-09"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--league-control-root", type=Path, default=Path("reports/generated/league-control")
    )
    parser.add_argument(
        "--economics-root",
        type=Path,
        default=Path("reports/generated/current-and-future-contract-economics-v2"),
    )
    parser.add_argument(
        "--rest-of-season-root",
        type=Path,
        default=Path("reports/generated/current-rest-of-season-v2"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/phase1-sequential-replay"),
    )
    return parser.parse_args()


def _last_completed_game(schedule: dict[str, object], as_of_date: date) -> date | None:
    completed: list[date] = []
    for day in list(schedule.get("dates", [])):
        for game in list(day.get("games", [])):
            official_date = date.fromisoformat(str(game["officialDate"]))
            status = dict(game.get("status", {}))
            if (
                str(game.get("gameType")) == "R"
                and official_date <= as_of_date
                and str(status.get("abstractGameState")) == "Final"
            ):
                completed.append(official_date)
    return max(completed) if completed else None


def _source_identity(path: Path) -> str:
    return f"local-artifact:{path.as_posix()}:{sha256_file(path)}"


def _bundle_id(paths: list[Path]) -> str:
    material = "\n".join(sorted(_source_identity(path) for path in paths)) + "\n"
    return f"phase1-replay-bundle:{sha256(material.encode('utf-8')).hexdigest()}"


def _joined_ids(annual: pl.DataFrame, column: str) -> dict[int, str]:
    return {
        int(group.item(0, "player_id")): "+".join(
            sorted(set(str(value) for value in group.get_column(column).drop_nulls()))
        )
        for group in annual.partition_by("player_id", maintain_order=True)
    }


def main() -> int:
    args = _args()
    dated_control = args.league_control_root / args.as_of_date.isoformat()
    dated_economics = args.economics_root / args.as_of_date.isoformat()
    dated_ros = args.rest_of_season_root / args.as_of_date.isoformat()
    control_path = dated_control / "league-control-snapshot.parquet"
    annual_path = dated_economics / "annual-contract-economics.parquet"
    aggregate_path = dated_economics / "aggregate-contract-economics.parquet"
    schedule_path = dated_ros / "official-mlb-schedule.json"
    inputs = [control_path, annual_path, aggregate_path, schedule_path]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)

    control = pl.read_parquet(control_path)
    annual = pl.read_parquet(annual_path)
    aggregate = pl.read_parquet(aggregate_path)
    schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
    last_game = _last_completed_game(schedule, args.as_of_date)
    checkpoint_id = f"phase1-current-{args.as_of_date.isoformat()}"
    as_of_at = datetime.combine(args.as_of_date, time.max, tzinfo=UTC)
    evidence_bundle_id = _bundle_id(inputs)

    if control.get_column("player_id").n_unique() != control.height:
        raise ValueError("current control snapshot is not one row per player")
    if aggregate.get_column("player_id").n_unique() != aggregate.height:
        raise ValueError("current economics aggregate is not one row per player")

    projection_sources = _joined_ids(annual, "projection_source_id")
    contract_sources = _joined_ids(annual, "contract_source_id")
    annual_war = {
        int(group.item(0, "player_id")): (
            float(group.get_column("projected_war_mean").sum()),
            float(group.get_column("projected_war_lower").sum()),
            float(group.get_column("projected_war_upper").sum()),
        )
        for group in annual.partition_by("player_id", maintain_order=True)
    }
    aggregate_by_player = {
        int(row["player_id"]): row for row in aggregate.iter_rows(named=True)
    }

    universe_rows: list[dict[str, object]] = []
    record_rows: list[dict[str, object]] = []
    missing_economics: list[dict[str, object]] = []
    for row in control.iter_rows(named=True):
        player_id = int(row["player_id"])
        rights_state = "controlled" if row["organization_id"] is not None else "unknown_rights"
        universe_rows.append(
            {
                "checkpoint_id": checkpoint_id,
                "player_id": player_id,
                "organization_id": row["organization_id"],
                "rights_state": rights_state,
            }
        )
        economics = aggregate_by_player.get(player_id)
        status = "review" if economics is None else str(economics["calculation_status"])
        if economics is None:
            missing_economics.append(
                {
                    "player_id": player_id,
                    "player_name": row["player_name"],
                    "organization_id": row["organization_id"],
                    "organization_status": row["organization_status"],
                    "reason": "missing_control_or_economics_path",
                }
            )
        war = annual_war.get(player_id)
        available = status == "available"
        record_rows.append(
            {
                "checkpoint_id": checkpoint_id,
                "as_of_at_utc": as_of_at,
                "evidence_cutoff_at_utc": as_of_at,
                "replay_mode": "retrospective_event_cutoff",
                "player_id": player_id,
                "organization_id": row["organization_id"],
                "rights_state": rights_state,
                "last_completed_game_date": last_game,
                "model_version": MODEL_VERSION,
                "evidence_bundle_id": evidence_bundle_id,
                "projection_source_id": projection_sources.get(player_id, "missing_projection_path"),
                "contract_source_id": contract_sources.get(player_id, "missing_contract_path"),
                "coverage_tier": (
                    "integrated_available"
                    if available
                    else "review_missing_or_blocked_economics"
                ),
                "calculation_status": status,
                "expected_remaining_war": war[0] if available and war else None,
                "expected_remaining_war_lower": war[1] if available and war else None,
                "expected_remaining_war_upper": war[2] if available and war else None,
                "expected_remaining_cost_dollars": (
                    economics["salary_cost_dollars"] if available else None
                ),
                "transferable_value_dollars": (
                    economics["discounted_contract_value_dollars"] if available else None
                ),
                "transferable_value_lower_dollars": (
                    economics["discounted_contract_value_lower_dollars"]
                    if available
                    else None
                ),
                "transferable_value_upper_dollars": (
                    economics["discounted_contract_value_upper_dollars"]
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
                "checkpoint_id": checkpoint_id,
                "source_snapshot_id": _source_identity(path),
                "maximum_predictor_event_date": (
                    last_game if path == schedule_path else args.as_of_date
                ),
                "knowledge_available_at_utc": None,
            }
            for path in inputs
        ],
        schema=REPLAY_SOURCE_EVIDENCE_SCHEMA,
    )
    result = replay_value_checkpoints(records, universes, source_evidence)

    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    storage = {
        "value_records": write_canonical_parquet(
            result.records,
            output / "value-records.parquet",
            table_name="phase1_replay_value_records",
        ).as_record(),
        "checkpoint_summary": write_canonical_parquet(
            result.checkpoints,
            output / "checkpoint-summary.parquet",
            table_name="phase1_replay_checkpoint_summary",
        ).as_record(),
        "delta_ledger": write_canonical_parquet(
            result.deltas,
            output / "delta-ledger.parquet",
            table_name="phase1_replay_delta_ledger",
        ).as_record(),
        "frozen_universe": write_canonical_parquet(
            universes,
            output / "frozen-universe.parquet",
            table_name="phase1_replay_frozen_universe",
        ).as_record(),
        "source_evidence": write_canonical_parquet(
            source_evidence,
            output / "source-evidence.parquet",
            table_name="phase1_replay_source_evidence",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "checkpoint_id": checkpoint_id,
        "as_of_date": args.as_of_date.isoformat(),
        "replay_mode": "retrospective_event_cutoff",
        "status": "current_integration_checkpoint_not_historical_validation",
        "model_version": MODEL_VERSION,
        "evidence_bundle_id": evidence_bundle_id,
        "last_completed_game_date": last_game.isoformat() if last_game else None,
        "universe_players": control.height,
        "available_players": result.checkpoints.item(0, "available_players"),
        "review_players": result.checkpoints.item(0, "review_players"),
        "missing_economics_players": len(missing_economics),
        "missing_economics": missing_economics,
        "totals": {
            "expected_remaining_war": result.checkpoints.item(
                0, "expected_remaining_war"
            ),
            "expected_remaining_cost_dollars": result.checkpoints.item(
                0, "expected_remaining_cost_dollars"
            ),
            "transferable_value_dollars": result.checkpoints.item(
                0, "transferable_value_dollars"
            ),
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
