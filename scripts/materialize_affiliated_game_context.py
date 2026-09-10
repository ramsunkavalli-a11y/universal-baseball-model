#!/usr/bin/env python3
"""Materialize official minor-league game, venue, score and home/away context."""

from __future__ import annotations

import json
from pathlib import Path

from universal_baseball.affiliated_game_context_source import (
    fetch_affiliated_game_context,
)
from universal_baseball.storage import write_canonical_parquet


OUTPUT = Path("reports/generated/affiliated-game-context")


def main() -> int:
    games, captures = fetch_affiliated_game_context(range(2021, 2026))
    tables = OUTPUT / "tables"
    raw = OUTPUT / "captures"
    tables.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    records = []
    for capture in captures:
        path = raw / f"schedule-{capture.season}-sport-{capture.sport_id}.json"
        path.write_bytes(capture.response_bytes)
        records.append(
            {
                "season": capture.season,
                "sport_id": capture.sport_id,
                "returned_games": capture.returned_games,
                "path": path.as_posix(),
                "sha256": capture.response_sha256,
            }
        )
    storage = write_canonical_parquet(
        games, tables / "affiliated-game-context.parquet",
        table_name="official_affiliated_game_context",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "status": "affiliated_game_context_source_ready",
        "seasons": [2021, 2022, 2023, 2024, 2025],
        "requests": len(captures),
        "games": games.height,
        "venues": games.get_column("venue_id").n_unique(),
        "teams": len(set(games.get_column("home_team_id")) | set(games.get_column("away_team_id"))),
        "storage": storage,
        "captures": records,
        "boundaries": {
            "official_statsapi_only": True,
            "regular_season_only": True,
            "completed_scored_games_only": True,
            "conflicting_suspended_resumed_venue_games_excluded": True,
            "park_effect_estimated": False,
            "production_changed": False,
        },
    }
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in ("status", "requests", "games", "venues", "teams")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
