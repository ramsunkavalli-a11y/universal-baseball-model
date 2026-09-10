#!/usr/bin/env python3
"""Materialize official league and venue identities for affiliated skill rows."""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

from universal_baseball.affiliated_team_context_source import (
    audit_skill_context_coverage,
    fetch_affiliated_team_context,
)
from universal_baseball.storage import write_canonical_parquet


OUTPUT = Path("reports/generated/affiliated-team-context")
SKILL = Path("reports/generated/affiliated-skill-source/tables")


def main() -> int:
    context, captures = fetch_affiliated_team_context((2023, 2024, 2025))
    tables = OUTPUT / "tables"
    raw = OUTPUT / "captures"
    tables.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    capture_records = []
    for capture in captures:
        path = raw / f"teams-{capture.season}-sport-{capture.sport_id}.json"
        path.write_bytes(capture.response_bytes)
        capture_records.append(
            {
                "season": capture.season,
                "sport_id": capture.sport_id,
                "returned_teams": capture.returned_teams,
                "path": path.as_posix(),
                "sha256": capture.response_sha256,
            }
        )
    storage = write_canonical_parquet(
        context,
        tables / "affiliated-team-context.parquet",
        table_name="official_affiliated_team_league_venue_context",
    ).as_record()
    hitting = pl.read_parquet(SKILL / "affiliated_hitting_components.parquet").filter(
        pl.col("season") <= 2025
    )
    pitching = pl.read_parquet(SKILL / "affiliated_pitching_components.parquet").filter(
        pl.col("season") <= 2025
    )
    report = {
        "report_schema_version": "0.1",
        "status": "league_venue_identity_source_ready",
        "seasons": [2023, 2024, 2025],
        "requests": len(captures),
        "hitting_coverage": audit_skill_context_coverage(hitting, context),
        "pitching_coverage": audit_skill_context_coverage(pitching, context),
        "storage": storage,
        "captures": capture_records,
        "boundary": (
            "league and venue identity only; no league-strength or park factor is "
            "estimated from team identity alone"
        ),
        "production_changed": False,
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "requests": report["requests"],
                "hitting_coverage": report["hitting_coverage"],
                "pitching_coverage": report["pitching_coverage"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
