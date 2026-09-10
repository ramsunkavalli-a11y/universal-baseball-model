"""Official affiliated game results for home/away environment research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.mlb_season_stats import _statsapi_get_with_retry
from universal_baseball.opportunity_history_source import AFFILIATED_SPORT_IDS
from universal_baseball.playing_time_roster_source import STATS_API_BASE


MINOR_SPORT_IDS = tuple(value for value in AFFILIATED_SPORT_IDS if value != 1)
GAME_CONTEXT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "game_date": pl.Date,
    "game_pk": pl.Int64,
    "sport_id": pl.Int64,
    "game_type": pl.String,
    "status_code": pl.String,
    "home_team_id": pl.Int64,
    "away_team_id": pl.Int64,
    "venue_id": pl.Int64,
    "scheduled_innings": pl.Int64,
    "home_score": pl.Int64,
    "away_score": pl.Int64,
}


@dataclass(frozen=True, slots=True)
class GameContextCapture:
    season: int
    sport_id: int
    returned_games: int
    response_bytes: bytes
    response_sha256: str


def project_schedule_payload(
    payload: dict[str, Any], *, season: int, sport_id: int
) -> pl.DataFrame:
    """Project completed regular-season game context without imputing scores."""

    rows = []
    for date_record in payload.get("dates") or []:
        for game in date_record.get("games") or []:
            teams = game.get("teams") or {}
            home = teams.get("home") or {}
            away = teams.get("away") or {}
            venue = game.get("venue") or {}
            status = game.get("status") or {}
            if any(
                value is None
                for value in (
                    game.get("gamePk"), home.get("score"), away.get("score"),
                    (home.get("team") or {}).get("id"),
                    (away.get("team") or {}).get("id"), venue.get("id"),
                )
            ):
                continue
            rows.append(
                {
                    "season": int(season),
                    "game_date": date.fromisoformat(str(game["officialDate"])),
                    "game_pk": int(game["gamePk"]),
                    "sport_id": int(sport_id),
                    "game_type": str(game.get("gameType") or ""),
                    "status_code": str(status.get("statusCode") or ""),
                    "home_team_id": int(home["team"]["id"]),
                    "away_team_id": int(away["team"]["id"]),
                    "venue_id": int(venue["id"]),
                    "scheduled_innings": int(game.get("scheduledInnings") or 9),
                    "home_score": int(home["score"]),
                    "away_score": int(away["score"]),
                }
            )
    # StatsAPI can repeat the same unchanged game under multiple date buckets after
    # postponements. Exact duplicates are harmless; conflicting game identities fail.
    result = pl.DataFrame(rows, schema=GAME_CONTEXT_SCHEMA).unique(maintain_order=True)
    duplicate_ids = result.group_by("game_pk").len().filter(pl.col("len") != 1)
    if duplicate_ids.height:
        # Suspended games can begin and resume in different venues. The schedule
        # repeats one gamePk with both venues but does not split the final score.
        # Exclude those games rather than assigning all runs to either park.
        result = result.filter(
            ~pl.col("game_pk").is_in(duplicate_ids.get_column("game_pk"))
        )
    return result.sort(["game_date", "game_pk"])


def fetch_affiliated_game_context(
    seasons: Iterable[int], *, session: requests.Session | None = None
) -> tuple[pl.DataFrame, list[GameContextCapture]]:
    """Fetch one schedule response per season and minor-league level."""

    requested = tuple(sorted({int(value) for value in seasons}))
    if not requested:
        raise ValueError("game context seasons cannot be empty")
    owned = session is None
    active = session or requests.Session()
    frames = []
    captures = []
    try:
        for season in requested:
            for sport_id in MINOR_SPORT_IDS:
                response = _statsapi_get_with_retry(
                    active,
                    f"{STATS_API_BASE}/schedule",
                    params={
                        "sportId": sport_id,
                        "startDate": f"{season}-03-01",
                        "endDate": f"{season}-11-30",
                        "gameTypes": "R",
                    },
                    timeout_seconds=180,
                )
                frame = project_schedule_payload(
                    response.json(), season=season, sport_id=sport_id
                )
                frames.append(frame)
                captures.append(
                    GameContextCapture(
                        season, sport_id, frame.height, response.content,
                        sha256(response.content).hexdigest(),
                    )
                )
    finally:
        if owned:
            active.close()
    result = pl.concat(frames, how="vertical")
    if result.group_by("game_pk").len().filter(pl.col("len") != 1).height:
        raise ValueError("game identity appears in multiple affiliated schedule cells")
    return result.sort(["season", "sport_id", "game_date", "game_pk"]), captures
