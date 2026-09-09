#!/usr/bin/env python3
"""Evaluate live contract vesting triggers from retained official MLB totals."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl

from universal_baseball.contract_vesting import (
    evaluate_vesting_triggers,
    load_vesting_trigger_config,
    project_statsapi_vesting_observations,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--trigger-config",
        type=Path,
        default=Path("config/contract-vesting-triggers-2026-09-09.json"),
    )
    parser.add_argument(
        "--mlb-skill-root",
        type=Path,
        default=Path("reports/generated/current-mlb-skill-source"),
    )
    parser.add_argument(
        "--rest-of-season-root",
        type=Path,
        default=Path("reports/generated/current-rest-of-season"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-contract-vesting"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    snapshot = args.as_of_date.isoformat()
    season = args.as_of_date.year
    skill_root = args.mlb_skill_root / snapshot
    schedule_root = args.rest_of_season_root / snapshot
    output_root = args.output_root / snapshot
    table_root = output_root / "tables"
    table_root.mkdir(parents=True, exist_ok=True)

    triggers, trigger_payload = load_vesting_trigger_config(args.trigger_config)
    hitting_path = skill_root / "tables/mlb_hitting_components.parquet"
    pitching_paths = sorted(
        (skill_root / "raw").glob(f"pitching-{season}-league-*-offset-*.json")
    )
    calendar_path = schedule_root / "tables/team-championship-season-calendar.parquet"
    if not hitting_path.exists() or not calendar_path.exists() or not pitching_paths:
        raise FileNotFoundError("current MLB skill or schedule evidence is incomplete")

    hitting = pl.read_parquet(hitting_path)
    pitching_payloads = [
        json.loads(path.read_text(encoding="utf-8")) for path in pitching_paths
    ]
    calendar = pl.read_parquet(calendar_path)
    current_calendar = calendar.filter(pl.col("season") == season)
    if current_calendar.height != 30:
        raise ValueError(f"expected 30 MLB team calendar rows, got {current_calendar.height}")
    season_complete = bool(
        current_calendar.filter(
            pl.col("completed_games") < pl.col("scheduled_games")
        ).is_empty()
    )
    observations = project_statsapi_vesting_observations(
        triggers,
        hitting,
        pitching_payloads,
        season=season,
        season_complete=season_complete,
    )
    evaluation = evaluate_vesting_triggers(triggers, observations)
    storage = {
        "observations": write_canonical_parquet(
            observations,
            table_root / "contract-vesting-observations.parquet",
            table_name="contract_vesting_observations",
        ).as_record(),
        "evaluations": write_canonical_parquet(
            evaluation.rows,
            table_root / "contract-vesting-evaluations.parquet",
            table_name="contract_vesting_evaluations",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "current_contract_vesting",
        "as_of_date": snapshot,
        "season": season,
        "season_complete": season_complete,
        "trigger_snapshot_id": trigger_payload["snapshot_id"],
        "source": "retained official MLB StatsAPI regular-season totals",
        "boundary": (
            "Scalar PA, pitching-out and games-pitched paths only. Medical, "
            "award, multi-season and catching-position clauses remain pending."
        ),
        "coverage": evaluation.coverage,
        "inputs": {
            "trigger_config": args.trigger_config.as_posix(),
            "hitting_table": hitting_path.as_posix(),
            "pitching_raw": [
                {
                    "path": path.as_posix(),
                    "sha256": sha256(path.read_bytes()).hexdigest(),
                }
                for path in pitching_paths
            ],
            "calendar_table": calendar_path.as_posix(),
        },
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["coverage"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
