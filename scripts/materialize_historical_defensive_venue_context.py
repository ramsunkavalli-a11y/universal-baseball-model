#!/usr/bin/env python
"""Materialize official venue identities for the historical defense PBP window."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_baseball.affiliated_game_context_source import (
    MINOR_SPORT_IDS,
    fetch_affiliated_game_context,
)
from universal_baseball.storage import write_canonical_parquet


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-season", type=int, default=2016)
    parser.add_argument("--end-season", type=int, default=2024)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("reports/generated/defensive-venue-context-v1"),
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.end_season < args.start_season:
        raise ValueError("end season precedes start season")
    seasons = range(args.start_season, args.end_season + 1)
    games, captures = fetch_affiliated_game_context(seasons)
    args.output_root.mkdir(parents=True, exist_ok=True)
    table = args.output_root / "affiliated-game-context.parquet"
    storage = write_canonical_parquet(
        games,
        table,
        table_name="historical_defensive_venue_context",
    ).as_record()
    report = {
        "report_schema_version": "0.1",
        "seasons": list(seasons),
        "sport_ids": list(MINOR_SPORT_IDS),
        "requests": len(captures),
        "games": games.height,
        "venues": games.get_column("venue_id").n_unique(),
        "storage": storage,
        "captures": [
            {
                "season": item.season,
                "sport_id": item.sport_id,
                "returned_games": item.returned_games,
                "sha256": item.response_sha256,
            }
            for item in captures
        ],
        "boundaries": {
            "official_statsapi_only": True,
            "regular_season_only": True,
            "physical_venue_id_available": True,
            "weather_surface_timing_and_umpires_available": True,
            "weather_is_game_baseline_not_play_varying": True,
            "official_scorer_or_datacaster_available_in_bulk": False,
            "protected_2026_accessed": False,
        },
    }
    (args.output_root / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in ("games", "venues", "requests")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
