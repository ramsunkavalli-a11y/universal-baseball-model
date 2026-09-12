#!/usr/bin/env python3
"""Probe current official pitch-quality coverage by affiliated level."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import requests


BASE = "https://statsapi.mlb.com/api"
SPORTS = {"AAA": 11, "AA": 12, "HIGH_A": 13, "SINGLE_A": 14, "ROOKIE": 16}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-08-15")
    parser.add_argument("--games-per-level", type=int, default=2)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/generated/current-minor-pitch-tracking-probe/report.json"),
    )
    return parser.parse_args()


def _get(session: requests.Session, url: str, **params: object) -> tuple[dict, str]:
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json(), sha256(response.content).hexdigest()


def main() -> int:
    args = _args()
    if args.games_per_level < 1:
        raise ValueError("games-per-level must be positive")
    results = {}
    with requests.Session() as session:
        for level, sport_id in SPORTS.items():
            schedule, schedule_hash = _get(
                session,
                f"{BASE}/v1/schedule",
                sportId=sport_id,
                date=args.date,
            )
            games = [
                game
                for date in schedule.get("dates", [])
                for game in date.get("games", [])
            ][: args.games_per_level]
            rows = []
            for game in games:
                game_id = int(game["gamePk"])
                feed, feed_hash = _get(
                    session,
                    f"{BASE}/v1.1/game/{game_id}/feed/live",
                )
                events = [
                    event
                    for play in feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
                    for event in play.get("playEvents", [])
                    if event.get("isPitch")
                ]
                pitch_data = [event.get("pitchData") or {} for event in events]
                pitch_types = [
                    (event.get("details", {}).get("type") or {}).get("code")
                    for event in events
                ]
                rows.append({
                    "game_pk": game_id,
                    "feed_sha256": feed_hash,
                    "pitch_events": len(events),
                    "start_speed_present": sum(
                        value.get("startSpeed") is not None for value in pitch_data
                    ),
                    "spin_rate_present": sum(
                        (value.get("breaks") or {}).get("spinRate") is not None
                        for value in pitch_data
                    ),
                    "movement_present": sum(
                        bool((value.get("coordinates") or {}).get("pfxX"))
                        for value in pitch_data
                    ),
                    "pitch_type_present": sum(value is not None for value in pitch_types),
                    "pitch_type_counts": dict(Counter(
                        value for value in pitch_types if value is not None
                    )),
                })
            results[level] = {
                "sport_id": sport_id,
                "schedule_sha256": schedule_hash,
                "games": rows,
            }
    report = {
        "report_schema_version": "0.1",
        "status": "current_capability_probe_not_full_season_certification",
        "date": args.date,
        "games_per_level": args.games_per_level,
        "levels": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
