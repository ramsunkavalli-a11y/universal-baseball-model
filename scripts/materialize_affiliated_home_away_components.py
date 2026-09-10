#!/usr/bin/env python3
"""Materialize official minor-league player home/away component splits."""

from __future__ import annotations

import json
from pathlib import Path

from universal_baseball.affiliated_home_away_component_source import (
    fetch_affiliated_home_away_components,
)
from universal_baseball.storage import write_canonical_parquet


OUTPUT = Path("reports/generated/affiliated-home-away-components")


def main() -> int:
    hitters, pitchers, captures = fetch_affiliated_home_away_components(
        range(2021, 2026)
    )
    tables = OUTPUT / "tables"
    raw = OUTPUT / "captures"
    tables.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    capture_records = []
    for capture in captures:
        path = raw / (
            f"stat-splits-{capture.group_name}-{capture.season}-"
            f"sport-{capture.sport_id}.json"
        )
        path.write_bytes(capture.response_bytes)
        capture_records.append({
            "season": capture.season, "sport_id": capture.sport_id,
            "group_name": capture.group_name, "rows": capture.rows,
            "path": path.as_posix(), "sha256": capture.response_sha256,
        })
    storage = [
        write_canonical_parquet(
            hitters, tables / "affiliated-hitter-home-away.parquet",
            table_name="official_affiliated_hitter_home_away",
        ).as_record(),
        write_canonical_parquet(
            pitchers, tables / "affiliated-pitcher-home-away.parquet",
            table_name="official_affiliated_pitcher_home_away",
        ).as_record(),
    ]
    report = {
        "report_schema_version": "0.1",
        "status": "affiliated_home_away_component_source_ready",
        "seasons": list(range(2021, 2026)), "requests": len(captures),
        "hitter_rows": hitters.height, "pitcher_rows": pitchers.height,
        "storage": storage, "captures": capture_records,
        "boundaries": {
            "official_statsapi_only": True, "regular_season_only": True,
            "home_away_situation_codes": ["h", "a"],
            "outside_fv_used": False, "production_changed": False,
        },
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "status", "requests", "hitter_rows", "pitcher_rows"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
