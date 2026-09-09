#!/usr/bin/env python3
"""Compare transaction-replayed current IL state with official roster status."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.injury_return import (
    build_injury_return_cohort,
    normalize_injury_transaction_payload,
)
from universal_baseball.playing_time_roster_source import STATS_API_BASE
from universal_baseball.rights_transactions import project_transaction_payload
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument(
        "--rest-of-season-root",
        type=Path,
        default=Path("reports/generated/current-rest-of-season"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/current-injury-return-state-audit"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    rest = args.rest_of_season_root / args.as_of_date.isoformat()
    output = args.output_root / args.as_of_date.isoformat()
    output.mkdir(parents=True, exist_ok=True)
    capture_path = output / "official-mlb-transactions.json"
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-il-state-audit/0.1"
        response = session.get(
            f"{STATS_API_BASE}/transactions",
            params={
                "sportId": 1,
                "startDate": f"01/01/{args.as_of_date.year}",
                "endDate": args.as_of_date.strftime("%m/%d/%Y"),
            },
            timeout=120,
        )
        response.raise_for_status()
    capture_path.write_bytes(response.content)
    payload, normalization = normalize_injury_transaction_payload(
        response.json(), season=args.as_of_date.year
    )
    transactions = project_transaction_payload(
        payload,
        as_of_date=args.as_of_date,
        source_snapshot_id=(
            f"statsapi:transactions:mlb:{args.as_of_date.isoformat()}"
        ),
    )
    calendar = pl.read_parquet(
        rest / "tables" / "team-championship-season-calendar.parquet"
    )
    season_end = calendar.get_column("championship_season_end").max()
    assert isinstance(season_end, date)
    replay = build_injury_return_cohort(
        transactions,
        cutoff_date=args.as_of_date,
        season_end_date=season_end,
    )
    statuses = pl.read_parquet(
        rest / "tables" / "current-availability-status.parquet"
    )
    official_injury = statuses.filter(
        pl.col("availability_category") == "injured_return_date_unresolved"
    )
    replay_ids = set(replay.get_column("player_id").to_list())
    official_ids = set(official_injury.get_column("player_id").to_list())
    salary = pl.read_parquet(
        rest / "tables" / "salary-rights-reconciliation.parquet"
    ).filter(pl.col("rights_join_status") == "matched_current_rights")
    salary_ids = set(salary.get_column("player_id").to_list())
    salary_injury_ids = salary_ids & official_ids
    storage = write_canonical_parquet(
        replay,
        output / "transaction-replayed-current-il.parquet",
        table_name="transaction_replayed_current_injured_list",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "gate": "current_injury_return_state_source_agreement",
        "as_of_date": args.as_of_date.isoformat(),
        "status": "source_validation_not_point_model",
        "official_injury_status_players": len(official_ids),
        "transaction_replayed_il_players": len(replay_ids),
        "exact_player_overlap": len(replay_ids & official_ids),
        "transaction_only_players": len(replay_ids - official_ids),
        "official_status_only_players": len(official_ids - replay_ids),
        "matched_salary_injury_players": len(salary_injury_ids),
        "matched_salary_injury_with_transaction_start": len(
            salary_injury_ids & replay_ids
        ),
        "normalization": normalization,
        "capture": {
            "path": capture_path.as_posix(),
            "sha256": sha256(capture_path.read_bytes()).hexdigest(),
            "requested_url": response.url,
        },
        "storage": storage,
        "decision_boundary": (
            "transaction replay may supply IL start/type only where it agrees with "
            "the current official roster status; unmatched rows keep the existing "
            "zero-to-baseline sensitivity"
        ),
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "gate", "status", "official_injury_status_players",
        "transaction_replayed_il_players", "exact_player_overlap",
        "transaction_only_players", "official_status_only_players",
        "matched_salary_injury_players",
        "matched_salary_injury_with_transaction_start",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
