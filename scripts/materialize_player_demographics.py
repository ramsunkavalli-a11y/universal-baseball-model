#!/usr/bin/env python3
"""Collect objective demographics for every historical/current affiliated player."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import sleep

import polars as pl
import requests

from universal_baseball.player_demographics import project_people_demographics
from universal_baseball.storage import write_canonical_parquet


PEOPLE_URL = "https://statsapi.mlb.com/api/v1/people"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--history-root", type=Path,
        default=Path("reports/generated/opportunity-history-sources-v2/tables"),
    )
    parser.add_argument(
        "--current-root", type=Path,
        default=Path("reports/generated/opportunity-current-source-2026-09-08/tables/2026"),
    )
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/player-demographics"),
    )
    parser.add_argument("--batch-size", type=int, default=50)
    return parser.parse_args()


def _player_ids(history_root: Path, current_root: Path) -> list[int]:
    paths = [
        history_root / "hitter_snapshots.parquet",
        history_root / "pitcher_snapshots.parquet",
        current_root / "hitter_snapshot.parquet",
        current_root / "pitcher_snapshot.parquet",
    ]
    ids: set[int] = set()
    for path in paths:
        ids.update(pl.read_parquet(path).get_column("player_id").to_list())
    return sorted(map(int, ids))


def main() -> int:
    args = _args()
    if args.batch_size < 1 or args.batch_size > 50:
        raise ValueError("batch size must be between 1 and 50")
    ids = _player_ids(args.history_root, args.current_root)
    captures = args.output_root / "captures"
    captures.mkdir(parents=True, exist_ok=True)
    frames = []
    with requests.Session() as session:
        session.headers["User-Agent"] = "universal-baseball-model-demographics/0.1"
        for offset in range(0, len(ids), args.batch_size):
            batch_number = offset // args.batch_size + 1
            batch = ids[offset : offset + args.batch_size]
            path = captures / f"people-{batch_number:04d}.json"
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))["payload"]
            else:
                response = session.get(
                    PEOPLE_URL,
                    params={"personIds": ",".join(map(str, batch))},
                    timeout=60,
                )
                response.raise_for_status()
                payload = response.json()
                path.write_text(
                    json.dumps(
                        {"requested_url": response.url, "payload": payload},
                        separators=(",", ":"), ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                sleep(0.02)
            frame = project_people_demographics(payload)
            returned = set(frame.get_column("player_id").to_list())
            if returned != set(batch):
                raise ValueError(f"people batch {batch_number} has incomplete identities")
            frames.append(frame)
    demographics = pl.concat(frames).sort("player_id")
    tables = args.output_root / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    storage = write_canonical_parquet(
        demographics, tables / "player-demographics.parquet",
        table_name="official_player_demographics",
    ).as_record()
    coverage = {
        column: float(demographics.get_column(column).is_not_null().mean())
        for column in demographics.columns if column != "player_id"
    }
    report = {
        "report_schema_version": "0.1",
        "players": demographics.height,
        "source": "official_statsapi_people",
        "coverage": coverage,
        "boundaries": {
            "race_or_ethnicity_inferred": False,
            "birthplace_used_only_as_reported": True,
            "people_profiles_are_not_historical_vintages": True,
            "height_weight_and_position_require_leakage_review": True,
        },
        "storage": storage,
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
