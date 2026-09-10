"""Official season/team league and venue identities for affiliated context work."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.mlb_season_stats import _statsapi_get_with_retry
from universal_baseball.opportunity_history_source import AFFILIATED_SPORT_IDS
from universal_baseball.playing_time_roster_source import STATS_API_BASE


AFFILIATED_TEAM_CONTEXT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "team_id": pl.Int64,
    "team_name": pl.String,
    "sport_id": pl.Int64,
    "league_id": pl.Int64,
    "league_name": pl.String,
    "division_id": pl.Int64,
    "venue_id": pl.Int64,
    "venue_name": pl.String,
}


@dataclass(frozen=True, slots=True)
class TeamContextCapture:
    season: int
    sport_id: int
    returned_teams: int
    response_bytes: bytes
    response_sha256: str


def _optional_id(value: object) -> int | None:
    return int(value) if value is not None else None


def project_team_context_payload(payload: dict[str, Any], *, season: int) -> pl.DataFrame:
    """Project team, league and home venue without guessing missing identities."""

    teams = payload.get("teams")
    if not isinstance(teams, list):
        raise ValueError("team context response missing teams")
    rows = []
    for team in teams:
        sport = team.get("sport") or {}
        league = team.get("league") or {}
        division = team.get("division") or {}
        venue = team.get("venue") or {}
        if team.get("id") is None or sport.get("id") is None:
            raise ValueError("team context response missing team or sport identity")
        rows.append(
            {
                "season": int(season),
                "team_id": int(team["id"]),
                "team_name": str(team.get("name") or ""),
                "sport_id": int(sport["id"]),
                "league_id": _optional_id(league.get("id")),
                "league_name": str(league.get("name") or ""),
                "division_id": _optional_id(division.get("id")),
                "venue_id": _optional_id(venue.get("id")),
                "venue_name": str(venue.get("name") or ""),
            }
        )
    result = pl.DataFrame(rows, schema=AFFILIATED_TEAM_CONTEXT_SCHEMA)
    if result.group_by("season", "team_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("team context response has duplicate season/team identities")
    return result.sort(["season", "sport_id", "team_id"])


def fetch_affiliated_team_context(
    seasons: Iterable[int],
    *,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, list[TeamContextCapture]]:
    """Fetch all teams for each affiliated level in a small fixed request set."""

    requested = tuple(sorted({int(season) for season in seasons}))
    if not requested:
        raise ValueError("team context seasons cannot be empty")
    owned = session is None
    active = session or requests.Session()
    frames = []
    captures = []
    try:
        for season in requested:
            for sport_id in sorted(AFFILIATED_SPORT_IDS):
                response = _statsapi_get_with_retry(
                    active,
                    f"{STATS_API_BASE}/teams",
                    params={
                        "sportId": sport_id,
                        "season": season,
                        "hydrate": "league,division,venue",
                    },
                    timeout_seconds=120,
                )
                frame = project_team_context_payload(response.json(), season=season)
                if frame.filter(pl.col("sport_id") != sport_id).height:
                    raise ValueError("team context response crossed requested sport")
                frames.append(frame)
                captures.append(
                    TeamContextCapture(
                        season=season,
                        sport_id=sport_id,
                        returned_teams=frame.height,
                        response_bytes=response.content,
                        response_sha256=sha256(response.content).hexdigest(),
                    )
                )
    finally:
        if owned:
            active.close()
    result = pl.concat(frames, how="vertical")
    if result.group_by("season", "team_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("affiliated team appears under multiple sports in one season")
    return result.sort(["season", "sport_id", "team_id"]), captures


def audit_skill_context_coverage(
    skill: pl.DataFrame, context: pl.DataFrame
) -> dict[str, int | float]:
    """Measure exact season/team context coverage of an affiliated skill table."""

    required = {"season", "team_id", "sport_id"}
    if missing := sorted(required - set(skill.columns)):
        raise ValueError(f"skill context audit missing fields: {missing}")
    if missing := sorted(set(AFFILIATED_TEAM_CONTEXT_SCHEMA) - set(context.columns)):
        raise ValueError(f"team context audit missing fields: {missing}")
    keys = skill.select("season", "team_id", "sport_id").drop_nulls("team_id").unique()
    joined = keys.join(
        context.select("season", "team_id", "sport_id", "league_id", "venue_id"),
        on=["season", "team_id", "sport_id"],
        how="left",
        validate="1:1",
    )
    matched = joined.filter(pl.col("league_id").is_not_null() & pl.col("venue_id").is_not_null()).height
    return {
        "distinct_skill_team_seasons": keys.height,
        "matched_league_and_venue_team_seasons": matched,
        "coverage_rate": matched / keys.height if keys.height else 0.0,
    }
