#!/usr/bin/env python3
"""Import a downloaded FanGraphs Opening Day Tracker workbook."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil

from universal_baseball.fangraphs_opening_day_source import (
    read_opening_day_tracker_xlsx,
)
from universal_baseball.storage import write_canonical_parquet


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/fangraphs-opening-day-workbooks"),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    content = args.input.read_bytes()
    digest = sha256(content).hexdigest()
    source_snapshot_id = (
        f"fangraphs:opening-day-tracker-workbook:{args.season}:{digest}"
    )
    normalized = read_opening_day_tracker_xlsx(
        args.input, season=args.season, source_snapshot_id=source_snapshot_id
    )
    teams = normalized.control.filter(
        normalized.control["team_abbreviation"] != ""
    ).get_column("team_abbreviation").n_unique()
    if teams != 30:
        raise ValueError(f"expected 30 MLB teams, observed {teams}")

    output = args.output_root / str(args.season)
    output.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.input, output / "opening-day-tracker-private.xlsx")
    storage = {
        "control": write_canonical_parquet(
            normalized.control,
            output / "opening-day-control-baseline.parquet",
            table_name="fangraphs_opening_day_workbook_control_baseline",
        ).as_record(),
        "projections": write_canonical_parquet(
            normalized.projections,
            output / "opening-day-projections.parquet",
            table_name="fangraphs_opening_day_workbook_projections",
        ).as_record(),
    }
    report = {
        "report_schema_version": "0.1",
        "season": args.season,
        "imported_at_utc": datetime.now(UTC).isoformat(),
        "source_snapshot_id": source_snapshot_id,
        "raw_workbook_sha256": digest,
        "raw_workbook_bytes": len(content),
        "players": normalized.control.height,
        "teams": teams,
        "service_time_players": normalized.control.filter(
            normalized.control["service_days"].is_not_null()
        ).height,
        "options_players": normalized.control.filter(
            normalized.control["options_remaining"].is_not_null()
        ).height,
        "projected_pa_players": normalized.projections.filter(
            normalized.projections["projected_pa"].is_not_null()
        ).height,
        "projected_ip_players": normalized.projections.filter(
            normalized.projections["projected_ip"].is_not_null()
        ).height,
        "unavailable_workbook_fields": [
            "fangraphs_team_id",
            "on_40man",
            "roster_status",
        ],
        "replay_mode_boundary": (
            "member_downloaded_retrospective_event_cutoff_not_vintage_information_set"
        ),
        "redistribution_boundary": "raw_and_bulk_workbook_private",
        "storage": storage,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
