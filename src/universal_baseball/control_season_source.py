"""Official MLB regular-season windows for control-day calculations."""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.team_control import SEASON_WINDOW_SCHEMA


STATS_API_SEASONS_URL = "https://statsapi.mlb.com/api/v1/seasons"


def project_season_window(payload: dict[str, Any], *, season: int) -> pl.DataFrame:
    rows = payload.get("seasons")
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("StatsAPI season response must contain exactly one season")
    source = rows[0]
    if str(source.get("seasonId")) != str(season):
        raise ValueError("StatsAPI season response does not match requested season")
    try:
        start = date.fromisoformat(str(source["regularSeasonStartDate"]))
        end = date.fromisoformat(str(source["regularSeasonEndDate"]))
    except (KeyError, ValueError) as exc:
        raise ValueError("StatsAPI season response lacks valid regular-season dates") from exc
    if start > end:
        raise ValueError("StatsAPI season response has inverted dates")
    return pl.DataFrame(
        [{"season": season, "start_date": start, "end_date": end}],
        schema=SEASON_WINDOW_SCHEMA,
    )


def fetch_season_windows(
    seasons: Iterable[int], *, session: requests.Session | None = None
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    requested = sorted({int(season) for season in seasons})
    if not requested:
        raise ValueError("seasons must be nonempty")
    own_session = session is None
    http = session or requests.Session()
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    try:
        for season in requested:
            response = http.get(
                f"{STATS_API_SEASONS_URL}/{season}",
                params={"sportId": 1},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("StatsAPI season response must be an object")
            frames.append(project_season_window(payload, season=season))
            captures.append(
                {
                    "season": season,
                    "requested_url": response.url,
                    "status_code": int(response.status_code),
                    "payload": payload,
                }
            )
    finally:
        if own_session:
            http.close()
    return pl.concat(frames).sort("season"), captures
