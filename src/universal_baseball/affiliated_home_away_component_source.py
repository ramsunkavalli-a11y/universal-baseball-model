"""Official player home/away component splits for affiliated park research."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable

import polars as pl
import requests

from universal_baseball.mlb_season_stats import _statsapi_get_with_retry
from universal_baseball.opportunity_history_source import AFFILIATED_SPORT_IDS
from universal_baseball.playing_time_roster_source import STATS_API_BASE


MINOR_SPORT_IDS = tuple(value for value in AFFILIATED_SPORT_IDS if value != 1)
KEY_SCHEMA = {
    "season": pl.Int64,
    "sport_id": pl.Int64,
    "team_id": pl.Int64,
    "player_id": pl.Int64,
    "split_code": pl.String,
}
HITTER_FIELDS = {
    "plateAppearances": "plate_appearances",
    "hits": "hits",
    "doubles": "doubles",
    "triples": "triples",
    "homeRuns": "home_runs",
    "baseOnBalls": "base_on_balls",
    "intentionalWalks": "intentional_walks",
    "hitByPitch": "hit_by_pitch",
    "strikeOuts": "strike_outs",
}
PITCHER_FIELDS = {
    "battersFaced": "batters_faced",
    "hits": "hits",
    "doubles": "doubles",
    "triples": "triples",
    "strikeOuts": "strike_outs",
    "baseOnBalls": "base_on_balls",
    "intentionalWalks": "intentional_walks",
    "hitBatsmen": "hit_batters",
    "homeRuns": "home_runs",
}


@dataclass(frozen=True, slots=True)
class HomeAwayCapture:
    season: int
    sport_id: int
    group_name: str
    rows: int
    response_bytes: bytes
    response_sha256: str


def _empty(fields: dict[str, str]) -> pl.DataFrame:
    return pl.DataFrame(
        schema={**KEY_SCHEMA, **{name: pl.Int64 for name in fields.values()}}
    )


def _project_group(
    payload: dict[str, Any], *, season: int, sport_id: int,
    group_name: str, fields: dict[str, str],
) -> pl.DataFrame:
    groups = [
        value for value in payload.get("stats") or []
        if (value.get("group") or {}).get("displayName") == group_name
    ]
    if len(groups) != 1:
        raise ValueError(f"expected one {group_name} split group")
    group = groups[0]
    splits = group.get("splits") or []
    if int(group.get("totalSplits", len(splits))) != len(splits):
        raise ValueError(f"{group_name} split response is truncated")
    rows = []
    for split in splits:
        code = str((split.get("split") or {}).get("code") or "")
        team_id = (split.get("team") or {}).get("id")
        player_id = (split.get("player") or {}).get("id")
        stat = split.get("stat") or {}
        if code not in {"h", "a"} or team_id is None or player_id is None:
            continue
        rows.append({
            "season": int(season),
            "sport_id": int(sport_id),
            "team_id": int(team_id),
            "player_id": int(player_id),
            "split_code": code,
            **{target: int(stat.get(source) or 0) for source, target in fields.items()},
        })
    result = pl.DataFrame(rows, schema=_empty(fields).schema) if rows else _empty(fields)
    keys = ["season", "sport_id", "team_id", "player_id", "split_code"]
    if result.group_by(keys).len().filter(pl.col("len") != 1).height:
        raise ValueError(f"duplicate {group_name} player home/away rows")
    return result.sort(keys)


def project_home_away_payload(
    payload: dict[str, Any], *, season: int, sport_id: int
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Project one complete StatsAPI statSplits response."""

    hitters = _project_group(
        payload, season=season, sport_id=sport_id,
        group_name="hitting", fields=HITTER_FIELDS,
    )
    pitchers = _project_group(
        payload, season=season, sport_id=sport_id,
        group_name="pitching", fields=PITCHER_FIELDS,
    )
    return hitters, pitchers


def fetch_affiliated_home_away_components(
    seasons: Iterable[int], *, session: requests.Session | None = None
) -> tuple[pl.DataFrame, pl.DataFrame, list[HomeAwayCapture]]:
    """Fetch one complete hitter/pitcher split response per season and level."""

    requested = tuple(sorted({int(value) for value in seasons}))
    if not requested:
        raise ValueError("home/away component seasons cannot be empty")
    owned = session is None
    active = session or requests.Session()
    hitter_frames = []
    pitcher_frames = []
    captures = []
    try:
        for season in requested:
            for sport_id in MINOR_SPORT_IDS:
                for group_name, fields, frames in (
                    ("hitting", HITTER_FIELDS, hitter_frames),
                    ("pitching", PITCHER_FIELDS, pitcher_frames),
                ):
                    # Combined hitting,pitching requests intermittently return 500
                    # for older MiLB seasons. Separate bounded requests are stable.
                    response = _statsapi_get_with_retry(
                        active,
                        f"{STATS_API_BASE}/stats",
                        params={
                            "stats": "statSplits",
                            "group": group_name,
                            "season": season,
                            "sportIds": sport_id,
                            "gameType": "R",
                            "sitCodes": "h,a",
                            "playerPool": "ALL",
                            "limit": 10000,
                        },
                        timeout_seconds=180,
                    )
                    frame = _project_group(
                        response.json(), season=season, sport_id=sport_id,
                        group_name=group_name, fields=fields,
                    )
                    frames.append(frame)
                    captures.append(HomeAwayCapture(
                        season, sport_id, group_name, frame.height,
                        response.content, sha256(response.content).hexdigest(),
                    ))
    finally:
        if owned:
            active.close()
    return (
        pl.concat(hitter_frames, how="vertical").sort(list(KEY_SCHEMA)),
        pl.concat(pitcher_frames, how="vertical").sort(list(KEY_SCHEMA)),
        captures,
    )
