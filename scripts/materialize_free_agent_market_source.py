#!/usr/bin/env python3
"""Capture public historical FanGraphs free-agent tracker facts."""

from __future__ import annotations

import argparse
from datetime import date
import gzip
from hashlib import sha256
import json
from pathlib import Path

import polars as pl
import requests

from universal_baseball.free_agent_market_source import (
    parse_fangraphs_free_agent_tracker_html,
)
from universal_baseball.storage import write_canonical_parquet


def _years(value: str) -> tuple[int, ...]:
    years = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not years:
        raise argparse.ArgumentTypeError("expected comma-separated years")
    return years


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of-date", type=date.fromisoformat, required=True)
    parser.add_argument("--years", type=_years, default=tuple(range(2020, 2027)))
    parser.add_argument(
        "--output-root", type=Path,
        default=Path("reports/generated/free-agent-market-source"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    output_root = args.output_root / args.as_of_date.isoformat()
    captures = output_root / "captures"
    tables = output_root / "tables"
    captures.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    frames = []
    capture_records = []
    session = requests.Session()
    session.headers["User-Agent"] = "universal-baseball-model/1.0 public research"
    for year in args.years:
        url = (
            "https://www.fangraphs.com/roster-resource/free-agent-tracker"
            f"?season={year}"
        )
        response = session.get(url, timeout=60)
        response.raise_for_status()
        content = response.content
        digest = sha256(content).hexdigest()
        capture_path = captures / f"free-agent-tracker-{year}.html.gz"
        capture_path.write_bytes(gzip.compress(content, mtime=0))
        snapshot_id = (
            f"fangraphs:free-agent-tracker:{year}:{args.as_of_date}:{digest}"
        )
        frame = parse_fangraphs_free_agent_tracker_html(
            response.text,
            free_agent_year=year,
            source_url=url,
            source_snapshot_id=snapshot_id,
        )
        frames.append(frame)
        capture_records.append(
            {
                "free_agent_year": year,
                "requested_url": url,
                "response_bytes": len(content),
                "response_sha256": digest,
                "normalized_rows": frame.height,
                "capture_path": str(capture_path),
            }
        )
    market = pl.concat(frames).sort(["free_agent_year", "source_row_sequence"])
    storage = write_canonical_parquet(
        market,
        tables / "fangraphs-free-agent-tracker.parquet",
        table_name="fangraphs_free_agent_tracker_history",
    ).as_record()
    signed = market.filter(
        pl.col("contract_years").is_not_null()
        & pl.col("contract_effective_total_dollars").is_not_null()
        & (pl.col("signing_team") != "")
    )
    report = {
        "report_schema_version": "0.1",
        "gate": "free_agent_market_public_source_capture",
        "as_of_date": args.as_of_date.isoformat(),
        "years": list(args.years),
        "rows": market.height,
        "distinct_fangraphs_ids": market.get_column("fangraphs_id").n_unique(),
        "signed_contract_rows": signed.height,
        "projected_war_rows": market.filter(
            pl.col("projected_war").is_not_null()
        ).height,
        "multiple_contract_player_years": (
            signed.group_by("free_agent_year", "fangraphs_id")
            .len()
            .filter(pl.col("len") > 1)
            .height
        ),
        "source_boundary": (
            "mutable current pages preserve historical contract facts but are not "
            "treated as archived signing-date projection snapshots"
        ),
        "identity_boundary": (
            "FanGraphs IDs retained; MLBAM attachment requires the pinned Chadwick "
            "crosswalk and rejects ambiguous or missing IDs"
        ),
        "capture": capture_records,
        "storage": storage,
    }
    (output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "gate": report["gate"],
                "rows": report["rows"],
                "signed_contract_rows": report["signed_contract_rows"],
                "projected_war_rows": report["projected_war_rows"],
                "multiple_contract_player_years": report[
                    "multiple_contract_player_years"
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
