#!/usr/bin/env python3
"""Capture and normalize one historical FanGraphs Opening Day Tracker page."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path

import requests

from universal_baseball.fangraphs_opening_day_source import (
    extract_next_data_document,
    project_opening_day_control_baseline,
)
from universal_baseball.storage import write_canonical_parquet


URL = "https://www.fangraphs.com/roster-resource/opening-day-tracker"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/fangraphs-opening-day-control"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    response = requests.get(
        URL,
        params={"season": args.season},
        headers={"User-Agent": "universal-baseball-model-source-audit/0.1"},
        timeout=60,
    )
    response.raise_for_status()
    content = response.content
    response_hash = sha256(content).hexdigest()
    source_snapshot_id = (
        f"fangraphs:opening-day-tracker:{args.season}:{response_hash}"
    )
    document = extract_next_data_document(response.text)
    baseline = project_opening_day_control_baseline(
        document, season=args.season, source_snapshot_id=source_snapshot_id
    )
    teams = baseline.filter(baseline["team_abbreviation"] != "").get_column(
        "team_abbreviation"
    ).n_unique()
    if teams != 30:
        raise ValueError(f"expected 30 MLB teams, observed {teams}")

    output = args.output_root / str(args.season)
    output.mkdir(parents=True, exist_ok=True)
    raw_path = output / "opening-day-tracker.html"
    raw_path.write_bytes(content)
    storage = write_canonical_parquet(
        baseline,
        output / "opening-day-control-baseline.parquet",
        table_name="fangraphs_opening_day_control_baseline",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "season": args.season,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "requested_url": response.url,
        "source_snapshot_id": source_snapshot_id,
        "raw_response_sha256": response_hash,
        "raw_response_bytes": len(content),
        "players": baseline.height,
        "teams": teams,
        "service_time_players": baseline.filter(
            baseline["service_days"].is_not_null()
        ).height,
        "options_players": baseline.filter(
            baseline["options_remaining"].is_not_null()
        ).height,
        "forty_man_players": baseline.filter(baseline["on_40man"]).height,
        "replay_mode_boundary": "retrospective_event_cutoff_not_vintage_information_set",
        "redistribution_boundary": "raw_and_bulk_capture_private_pending_terms_review",
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
