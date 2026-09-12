#!/usr/bin/env python3
"""Audit whether current affiliated playEvents contain genuine pitch sequences."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import requests

from universal_baseball.pitch_sequence_fidelity import (
    summarize_game_pitch_sequences,
    summarize_league,
)


BASE = "https://statsapi.mlb.com/api"
SPORTS = {"AAA": 11, "AA": 12, "HIGH_A": 13, "SINGLE_A": 14, "ROOKIE": 16}


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", default="2026-08-01")
    parser.add_argument("--end-date", default="2026-08-31")
    parser.add_argument("--games-per-level", type=int, default=20)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "reports/generated/current-pitch-sequence-fidelity/report.json"
        ),
    )
    return parser.parse_args()


def _get(session: requests.Session, url: str, **params: object) -> tuple[dict, str]:
    response = session.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json(), sha256(response.content).hexdigest()


def _spread_sample(games: list[dict], amount: int) -> list[dict]:
    ordered = sorted(games, key=lambda game: (game["gameDate"], game["gamePk"]))
    if len(ordered) <= amount:
        return ordered
    if amount == 1:
        return [ordered[len(ordered) // 2]]
    indices = [round(index * (len(ordered) - 1) / (amount - 1)) for index in range(amount)]
    return [ordered[index] for index in indices]


def _league(feed: dict) -> tuple[int | None, str | None]:
    teams = feed.get("gameData", {}).get("teams", {})
    for side in ("away", "home"):
        league = teams.get(side, {}).get("league") or {}
        if league.get("id") is not None:
            return int(league["id"]), str(league.get("name") or league["id"])
    return None, None


def main() -> int:
    args = _args()
    start_year = int(args.start_date[:4])
    end_year = int(args.end_date[:4])
    if start_year != end_year:
        raise ValueError("fidelity audit date range must stay within one season")
    if args.games_per_level < 1:
        raise ValueError("games-per-level must be positive")
    environments: dict[str, list[dict]] = {}
    captures = []
    with requests.Session() as session:
        for level, sport_id in SPORTS.items():
            schedule, schedule_hash = _get(
                session,
                f"{BASE}/v1/schedule",
                sportId=sport_id,
                startDate=args.start_date,
                endDate=args.end_date,
                gameType="R",
            )
            games = [
                game
                for date in schedule.get("dates", [])
                for game in date.get("games", [])
                if game.get("status", {}).get("codedGameState") == "F"
            ]
            for game in _spread_sample(games, args.games_per_level):
                game_pk = int(game["gamePk"])
                feed, feed_hash = _get(
                    session, f"{BASE}/v1.1/game/{game_pk}/feed/live"
                )
                league_id, league_name = _league(feed)
                environment = f"{level}|{league_id or 'unknown'}"
                rows = summarize_game_pitch_sequences(
                    game_pk,
                    feed.get("liveData", {}).get("plays", {}),
                    season=start_year,
                    league_id=league_id,
                    league_name=league_name,
                )
                environments.setdefault(environment, []).extend(rows)
                captures.append({
                    "level": level,
                    "sport_id": sport_id,
                    "game_pk": game_pk,
                    "game_date": str(game["officialDate"]),
                    "league_id": league_id,
                    "league_name": league_name,
                    "feed_sha256": feed_hash,
                    "true_pa": len(rows),
                    "schedule_sha256": schedule_hash,
                })
    report = {
        "report_schema_version": "0.1",
        "status": "source_fidelity_audit_not_model_promotion",
        "date_range": [args.start_date, args.end_date],
        "games_per_level": args.games_per_level,
        "interpretation": (
            "High 3-pitch K, 4-pitch BB and 1-pitch BIP shares indicate synthetic "
            "outcome-minimal entry; results do not themselves promote whiff features."
        ),
        "environments": {
            key: summarize_league(rows) for key, rows in sorted(environments.items())
        },
        "captures": captures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": report["status"],
        "environments": report["environments"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
