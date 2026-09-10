#!/usr/bin/env python3
"""Fetch exact MLB debut dates for an observed career-outcome universe."""

from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.storage import write_canonical_parquet


URL = "https://statsapi.mlb.com/api/v1/people"


def project_debut_people(payload: dict[str, object]) -> pl.DataFrame:
    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("StatsAPI people payload missing people list")
    rows = []
    for person in people:
        if not isinstance(person, dict) or person.get("id") is None:
            raise ValueError("StatsAPI people row missing player ID")
        raw_debut = person.get("mlbDebutDate")
        rows.append(
            {
                "player_id": int(person["id"]),
                "mlb_debut_date": (
                    date.fromisoformat(str(raw_debut)) if raw_debut else None
                ),
            }
        )
    result = pl.DataFrame(
        rows, schema={"player_id": pl.Int64, "mlb_debut_date": pl.Date}
    ).sort("player_id")
    if result.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("StatsAPI people payload contains duplicate IDs")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--careers", type=Path,
        default=Path(
            "reports/generated/career-mlb-outcome-inventory-2009-2025/tables/"
            "mlb_observed_careers_2009_2025.parquet"
        ),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/career-mlb-outcome-inventory-2009-2025"),
    )
    parser.add_argument(
        "--output-json", type=Path,
        default=Path("docs/career-debut-date-source-result.json"),
    )
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 100:
        raise ValueError("batch-size must be between 1 and 100")
    ids = sorted(
        pl.read_parquet(args.careers)["player_id"].unique().to_list()
    )
    raw_root = args.output_root / "debut-date-captures"
    raw_root.mkdir(parents=True, exist_ok=True)
    frames = []
    captures = []
    with requests.Session() as session:
        for offset in range(0, len(ids), args.batch_size):
            batch = ids[offset : offset + args.batch_size]
            response = session.get(
                URL,
                params={"personIds": ",".join(map(str, batch))},
                timeout=60,
            )
            response.raise_for_status()
            body = response.content
            path = raw_root / f"people-{offset // args.batch_size + 1:03d}.json"
            path.write_bytes(body)
            payload = response.json()
            frame = project_debut_people(payload)
            returned = set(frame["player_id"].to_list())
            if returned != set(batch):
                raise ValueError(
                    f"StatsAPI debut batch mismatch: missing={sorted(set(batch)-returned)[:10]}"
                )
            frames.append(frame)
            captures.append(
                {
                    "batch": offset // args.batch_size + 1,
                    "requested_players": len(batch),
                    "response_sha256": sha256(body).hexdigest(),
                    "raw_path": path.as_posix(),
                }
            )
    people = pl.concat(frames).sort("player_id")
    if people.height != len(ids) or people["player_id"].n_unique() != len(ids):
        raise ValueError("debut people coverage is incomplete")
    table = args.output_root / "tables" / "people-debut-dates.parquet"
    storage = write_canonical_parquet(
        people, table, table_name="career_outcome_people_debut_dates"
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "career_debut_date_source_complete",
        "source": "official MLB StatsAPI people endpoint",
        "players": len(ids),
        "debut_date_players": int(people["mlb_debut_date"].is_not_null().sum()),
        "missing_debut_date_players": int(people["mlb_debut_date"].is_null().sum()),
        "exact_requested_id_coverage": True,
        "captures": captures,
        "storage": storage,
        "boundaries": {
            "current_corrected_stable_profile_field": True,
            "true_historical_retrieval_vintage": False,
            "roster_contract_transaction_hydration_used": False,
            "current_2026_outcomes_used": False,
        },
    }
    args.output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "players": len(ids),
        "debut_date_players": report["debut_date_players"],
        "missing_debut_date_players": report["missing_debut_date_players"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
