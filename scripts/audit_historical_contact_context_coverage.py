#!/usr/bin/env python3
"""Verify that historical contact events have official game and venue context."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path

import polars as pl


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", type=int, default=[2016, 2017, 2018])
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "reports/generated/historical-contact-context-coverage/report.json"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = _args()
    seasons: list[dict[str, object]] = []
    for season in args.seasons:
        events_path = Path(
            f"reports/generated/historical-contact-panel-{season}/tables/"
            "hitter_full_bip_event_outcomes.parquet"
        )
        context_path = Path(
            f"reports/generated/hitter-v2-{season}-game-authority/tables/"
            f"hitter_v2_game_context_{season}_recovered.parquet"
        )
        events = pl.read_parquet(events_path)
        contexts = pl.read_parquet(context_path)
        joined = events.join(
            contexts.select("game_id", "venue_id"),
            left_on="game_pk",
            right_on="game_id",
            how="left",
        )
        missing = joined.filter(pl.col("venue_id").is_null())
        seasons.append(
            {
                "season": season,
                "contact_events": events.height,
                "contact_games": events.get_column("game_pk").n_unique(),
                "official_context_games": contexts.height,
                "matched_contact_events": joined.height - missing.height,
                "missing_contact_events": missing.height,
                "missing_game_ids": sorted(
                    int(value)
                    for value in missing.get_column("game_pk").unique().to_list()
                ),
                "venue_coverage_rate": (joined.height - missing.height) / joined.height,
                "events_path": str(events_path),
                "context_path": str(context_path),
            }
        )
    report = {
        "schema_version": "0.1",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "scope": "historical_hitter_contact_to_official_venue_coverage",
        "seasons": seasons,
        "total_contact_events": sum(int(row["contact_events"]) for row in seasons),
        "total_missing_contact_events": sum(
            int(row["missing_contact_events"]) for row in seasons
        ),
        "accepted": all(int(row["missing_contact_events"]) == 0 for row in seasons),
        "candidate_fit": False,
        "candidate_scored": False,
        "protected_2026_opened": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
