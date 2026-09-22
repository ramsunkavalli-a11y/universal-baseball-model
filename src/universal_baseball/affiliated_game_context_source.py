"""Official affiliated game results for home/away environment research."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from hashlib import sha256
import re
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.mlb_season_stats import _statsapi_get_with_retry
from universal_baseball.opportunity_history_source import AFFILIATED_SPORT_IDS
from universal_baseball.playing_time_roster_source import STATS_API_BASE


# Sport 15 was the former affiliated Short-Season A classification. It no longer
# appears in current-season level inventories but is required for historical work.
MINOR_SPORT_IDS = tuple(
    sorted({*(value for value in AFFILIATED_SPORT_IDS if value != 1), 15})
)
GAME_CONTEXT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "game_date": pl.Date,
    "scheduled_datetime_utc": pl.Datetime("us", "UTC"),
    "first_pitch_datetime_utc": pl.Datetime("us", "UTC"),
    "game_pk": pl.Int64,
    "sport_id": pl.Int64,
    "game_type": pl.String,
    "status_code": pl.String,
    "day_night": pl.String,
    "home_team_id": pl.Int64,
    "away_team_id": pl.Int64,
    "venue_id": pl.Int64,
    "venue_name": pl.String,
    "venue_city": pl.String,
    "venue_state": pl.String,
    "venue_country": pl.String,
    "venue_latitude": pl.Float64,
    "venue_longitude": pl.Float64,
    "turf_type": pl.String,
    "roof_type": pl.String,
    "venue_capacity": pl.Int64,
    "left_field_line_ft": pl.Int64,
    "center_field_ft": pl.Int64,
    "right_field_line_ft": pl.Int64,
    "weather_condition": pl.String,
    "temperature_f": pl.Float64,
    "wind_raw": pl.String,
    "wind_mph": pl.Float64,
    "wind_direction": pl.String,
    "attendance": pl.Int64,
    "game_duration_minutes": pl.Int64,
    "delay_duration_minutes": pl.Int64,
    "home_plate_umpire_id": pl.Int64,
    "first_base_umpire_id": pl.Int64,
    "second_base_umpire_id": pl.Int64,
    "third_base_umpire_id": pl.Int64,
    "scheduled_innings": pl.Int64,
    "home_score": pl.Int64,
    "away_score": pl.Int64,
}


def _optional_int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _optional_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _wind_parts(value: Any) -> tuple[str | None, float | None, str | None]:
    if value in (None, ""):
        return None, None, None
    raw = str(value).strip()
    speed_match = re.search(r"(\d+(?:\.\d+)?)\s*mph", raw, flags=re.IGNORECASE)
    speed = float(speed_match.group(1)) if speed_match else (0.0 if raw.lower() == "calm" else None)
    direction = raw.split(",", maxsplit=1)[1].strip() if "," in raw else None
    return raw, speed, direction


def _official_id(game: dict[str, Any], official_type: str) -> int | None:
    for record in game.get("officials") or []:
        if str(record.get("officialType") or "").casefold() == official_type.casefold():
            return _optional_int((record.get("official") or {}).get("id"))
    return None


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
            venue_location = venue.get("location") or {}
            venue_coordinates = venue_location.get("defaultCoordinates") or {}
            field_info = venue.get("fieldInfo") or {}
            weather = game.get("weather") or {}
            game_info = game.get("gameInfo") or {}
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
            wind_raw, wind_mph, wind_direction = _wind_parts(weather.get("wind"))
            rows.append(
                {
                    "season": int(season),
                    "game_date": date.fromisoformat(str(game["officialDate"])),
                    "scheduled_datetime_utc": _optional_datetime(game.get("gameDate")),
                    "first_pitch_datetime_utc": _optional_datetime(game_info.get("firstPitch")),
                    "game_pk": int(game["gamePk"]),
                    "sport_id": int(sport_id),
                    "game_type": str(game.get("gameType") or ""),
                    "status_code": str(status.get("statusCode") or ""),
                    "day_night": str(game.get("dayNight") or ""),
                    "home_team_id": int(home["team"]["id"]),
                    "away_team_id": int(away["team"]["id"]),
                    "venue_id": int(venue["id"]),
                    "venue_name": str(venue.get("name") or ""),
                    "venue_city": str(venue_location.get("city") or ""),
                    "venue_state": str(
                        venue_location.get("stateAbbrev")
                        or venue_location.get("state")
                        or ""
                    ),
                    "venue_country": str(venue_location.get("country") or ""),
                    "venue_latitude": _optional_float(venue_coordinates.get("latitude")),
                    "venue_longitude": _optional_float(venue_coordinates.get("longitude")),
                    "turf_type": str(field_info.get("turfType") or ""),
                    "roof_type": str(field_info.get("roofType") or ""),
                    "venue_capacity": _optional_int(field_info.get("capacity")),
                    "left_field_line_ft": _optional_int(field_info.get("leftLine")),
                    "center_field_ft": _optional_int(field_info.get("center")),
                    "right_field_line_ft": _optional_int(field_info.get("rightLine")),
                    "weather_condition": str(weather.get("condition") or ""),
                    "temperature_f": _optional_float(weather.get("temp")),
                    "wind_raw": wind_raw or "",
                    "wind_mph": wind_mph,
                    "wind_direction": wind_direction or "",
                    "attendance": _optional_int(game_info.get("attendance")),
                    "game_duration_minutes": _optional_int(
                        game_info.get("gameDurationMinutes")
                    ),
                    "delay_duration_minutes": _optional_int(
                        game_info.get("delayDurationMinutes")
                    ),
                    "home_plate_umpire_id": _official_id(game, "Home Plate"),
                    "first_base_umpire_id": _official_id(game, "First Base"),
                    "second_base_umpire_id": _official_id(game, "Second Base"),
                    "third_base_umpire_id": _official_id(game, "Third Base"),
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
                        "hydrate": (
                            "weather,venue(location,fieldInfo),officials,gameInfo"
                        ),
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
