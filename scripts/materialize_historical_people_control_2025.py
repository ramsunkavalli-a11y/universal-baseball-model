#!/usr/bin/env python3
"""Complete October 2025 people/control evidence from retained and live StatsAPI."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import polars as pl

from universal_baseball.people_control_source import (
    PeopleControlEvidence,
    fetch_people_control_evidence,
    project_people_control_payload,
)
from universal_baseball.source_capture import (
    load_parsed_json_captures,
    persist_parsed_json_captures,
)
from universal_baseball.storage import sha256_file, write_canonical_parquet


AS_OF_DATE = date(2025, 10, 15)


def _project_captures(captures: dict[str, dict[str, object]]) -> PeopleControlEvidence:
    batches = [
        project_people_control_payload(
            capture["payload"],
            as_of_date=AS_OF_DATE,
            source_snapshot_id=str(capture["source_snapshot_id"]),
        )
        for name, capture in sorted(captures.items())
        if name.startswith("people-")
    ]
    if not batches:
        raise ValueError("people-control capture set contains no people batches")
    return PeopleControlEvidence(
        people=pl.concat([batch.people for batch in batches]).sort("player_id"),
        roster_entries=pl.concat(
            [batch.roster_entries for batch in batches], how="vertical_relaxed"
        ).sort(["player_id", "start_date", "team_id"]),
        transactions=pl.concat(
            [batch.transactions for batch in batches], how="vertical_relaxed"
        ).sort(["player_id", "effective_date", "transaction_id"]),
        captures=[],
    )


def _combine(
    retained: PeopleControlEvidence,
    supplement: PeopleControlEvidence,
    universe_ids: set[int],
) -> PeopleControlEvidence:
    frames = []
    for attribute in ("people", "roster_entries", "transactions"):
        frame = pl.concat(
            [getattr(retained, attribute), getattr(supplement, attribute)],
            how="vertical_relaxed",
        ).filter(pl.col("player_id").is_in(sorted(universe_ids)))
        if attribute == "people":
            frame = frame.unique("player_id", keep="first").sort("player_id")
        elif attribute == "roster_entries":
            frame = frame.unique(
                ["player_id", "team_id", "status_code", "start_date", "end_date"],
                keep="first",
            ).sort(["player_id", "start_date", "team_id"])
        else:
            frame = frame.unique(
                ["player_id", "transaction_id"], keep="first"
            ).sort(["player_id", "effective_date", "transaction_id"])
        frames.append(frame)
    people, roster_entries, transactions = frames
    if set(people.get_column("player_id")) != universe_ids:
        missing = sorted(universe_ids - set(people.get_column("player_id")))
        raise ValueError(f"StatsAPI people evidence remains incomplete: {missing[:10]}")
    return PeopleControlEvidence(
        people=people,
        roster_entries=roster_entries,
        transactions=transactions,
        captures=[],
    )


def main() -> int:
    snapshot_root = Path("reports/generated/opportunity-history-sources-v2/tables/2025")
    retained_root = Path("reports/generated/league-control/2026-09-08/source-captures")
    output = Path("reports/generated/historical-people-control/2025-10-15")
    supplement_root = output / "supplemental-source-captures"
    hitter_path = snapshot_root / "hitter_snapshot.parquet"
    pitcher_path = snapshot_root / "pitcher_snapshot.parquet"
    universe_ids = set(
        pl.concat(
            [
                pl.read_parquet(hitter_path).select("player_id"),
                pl.read_parquet(pitcher_path).select("player_id"),
            ]
        ).get_column("player_id")
    )

    retained = _project_captures(load_parsed_json_captures(retained_root))
    retained_ids = set(retained.people.get_column("player_id"))
    missing_ids = sorted(universe_ids - retained_ids)
    if supplement_root.is_dir():
        supplement_captures = load_parsed_json_captures(supplement_root)
        supplement = _project_captures(supplement_captures)
        acquisition = "retained_hash_verified_supplement"
    elif missing_ids:
        supplement = fetch_people_control_evidence(
            missing_ids, as_of_date=AS_OF_DATE, batch_size=50
        )
        persist_parsed_json_captures(
            (
                (f"people-{index:03d}.json", capture)
                for index, capture in enumerate(supplement.captures, start=1)
            ),
            supplement_root,
        )
        acquisition = "live_statsapi_supplement_then_retained"
    else:
        supplement = PeopleControlEvidence(
            people=retained.people.head(0),
            roster_entries=retained.roster_entries.head(0),
            transactions=retained.transactions.head(0),
            captures=[],
        )
        acquisition = "retained_capture_already_complete"
    combined = _combine(retained, supplement, universe_ids)

    output.mkdir(parents=True, exist_ok=True)
    tables = output / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = {
        "people": write_canonical_parquet(
            combined.people,
            tables / "people.parquet",
            table_name="historical_2025_people_control_people",
        ).as_record(),
        "roster_entries": write_canonical_parquet(
            combined.roster_entries,
            tables / "roster-entries.parquet",
            table_name="historical_2025_people_control_roster_entries",
        ).as_record(),
        "transactions": write_canonical_parquet(
            combined.transactions,
            tables / "transactions.parquet",
            table_name="historical_2025_people_control_transactions",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "gate": "historical_2025_people_control_evidence",
        "as_of_date": AS_OF_DATE.isoformat(),
        "acquisition": acquisition,
        "universe_players": len(universe_ids),
        "retained_capture_players_in_universe": len(universe_ids & retained_ids),
        "supplement_requested_players": len(missing_ids),
        "complete_people_players": combined.people.height,
        "roster_entry_rows": combined.roster_entries.height,
        "transaction_rows": combined.transactions.height,
        "later_events_filtered_by_adapter": True,
        "source_files": {
            hitter_path.as_posix(): sha256_file(hitter_path),
            pitcher_path.as_posix(): sha256_file(pitcher_path),
            (retained_root / "manifest.json").as_posix(): sha256_file(
                retained_root / "manifest.json"
            ),
            **(
                {
                    (supplement_root / "manifest.json").as_posix(): sha256_file(
                        supplement_root / "manifest.json"
                    )
                }
                if supplement_root.is_dir()
                else {}
            ),
        },
        "boundaries": {
            "official_statsapi_people_source": True,
            "event_cutoff_enforced": True,
            "retrieval_is_later_than_event_cutoff": True,
            "true_vintage_claim": False,
        },
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in report.items() if key != "storage"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
