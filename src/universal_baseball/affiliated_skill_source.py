"""Official bulk affiliated component counts for universal skill baselines."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping

import polars as pl
import requests

from universal_baseball.mlb_season_stats import _statsapi_get_with_retry
from universal_baseball.opportunity_history_source import AFFILIATED_SPORT_IDS, SPORT_LEVEL
from universal_baseball.playing_time_roster_source import STATS_API_BASE


AFFILIATED_HITTING_SKILL_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64, "player_id": pl.Int64, "player_name": pl.String,
    "sport_id": pl.Int64, "level_group": pl.String, "team_id": pl.Int64,
    "reported_age": pl.Float64, "plate_appearances": pl.Int64, "at_bats": pl.Int64,
    "hits": pl.Int64, "doubles": pl.Int64, "triples": pl.Int64,
    "home_runs": pl.Int64, "base_on_balls": pl.Int64,
    "intentional_walks": pl.Int64, "hit_by_pitch": pl.Int64,
    "strike_outs": pl.Int64, "sac_bunts": pl.Int64, "sac_flies": pl.Int64,
    "stolen_bases": pl.Int64, "caught_stealing": pl.Int64,
    "ground_into_double_play": pl.Int64,
}

AFFILIATED_PITCHING_SKILL_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64, "player_id": pl.Int64, "player_name": pl.String,
    "sport_id": pl.Int64, "level_group": pl.String, "team_id": pl.Int64,
    "reported_age": pl.Float64, "games": pl.Int64, "starts": pl.Int64,
    "batters_faced": pl.Int64, "strike_outs": pl.Int64,
    "base_on_balls": pl.Int64, "intentional_walks": pl.Int64,
    "hit_batters": pl.Int64, "home_runs": pl.Int64,
}

_HITTING_FIELDS = {
    "plate_appearances": "plateAppearances", "at_bats": "atBats",
    "hits": "hits", "doubles": "doubles", "triples": "triples",
    "home_runs": "homeRuns", "base_on_balls": "baseOnBalls",
    "intentional_walks": "intentionalWalks", "hit_by_pitch": "hitByPitch",
    "strike_outs": "strikeOuts", "sac_bunts": "sacBunts",
    "sac_flies": "sacFlies", "stolen_bases": "stolenBases",
    "caught_stealing": "caughtStealing", "ground_into_double_play": "groundIntoDoublePlay",
}
_PITCHING_FIELDS = {
    "games": "gamesPlayed", "starts": "gamesStarted",
    "batters_faced": "battersFaced", "strike_outs": "strikeOuts",
    "base_on_balls": "baseOnBalls", "intentional_walks": "intentionalWalks",
    "hit_batters": "hitBatsmen", "home_runs": "homeRuns",
}


@dataclass(frozen=True, slots=True)
class AffiliatedSkillCapture:
    season: int
    stat_group: str
    offset: int
    requested_limit: int
    returned_rows: int
    reported_total_splits: int | None
    response_bytes: bytes
    response_sha256: str


def _count(stat: Mapping[str, Any], field: str) -> int:
    if field not in stat or stat[field] in (None, ""):
        raise ValueError(f"affiliated skill split missing {field}")
    numeric = float(str(stat[field]))
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"affiliated skill split has invalid {field}")
    return int(numeric)


def project_affiliated_skill_splits(
    splits: list[Mapping[str, Any]], *, season: int, stat_group: str
) -> pl.DataFrame:
    """Project one official response page without silently filling absent fields."""

    if stat_group not in {"hitting", "pitching"}:
        raise ValueError("stat_group must be hitting or pitching")
    fields = _HITTING_FIELDS if stat_group == "hitting" else _PITCHING_FIELDS
    schema = (
        AFFILIATED_HITTING_SKILL_SCHEMA
        if stat_group == "hitting"
        else AFFILIATED_PITCHING_SKILL_SCHEMA
    )
    rows: list[dict[str, object]] = []
    for split in splits:
        player = split.get("player") or split.get("person") or {}
        sport = split.get("sport") or {}
        team = split.get("team") or {}
        stat = split.get("stat") or {}
        player_id = player.get("id")
        sport_id = sport.get("id")
        if player_id is None or sport_id is None or int(sport_id) not in SPORT_LEVEL:
            raise ValueError("affiliated skill split has unsupported identity or sport")
        row: dict[str, object] = {
            "season": int(season), "player_id": int(player_id),
            "player_name": str(player.get("fullName") or ""),
            "sport_id": int(sport_id), "level_group": SPORT_LEVEL[int(sport_id)],
            "team_id": int(team["id"]) if team.get("id") is not None else None,
            "reported_age": float(stat["age"]) if stat.get("age") is not None else None,
            **{name: _count(stat, source) for name, source in fields.items()},
        }
        rows.append(row)
    result = pl.DataFrame(rows, schema=schema)
    if stat_group == "hitting" and result.filter(
        (pl.col("hits") > pl.col("at_bats"))
        | (pl.col("doubles") + pl.col("triples") + pl.col("home_runs") > pl.col("hits"))
        | (pl.col("intentional_walks") > pl.col("base_on_balls"))
    ).height:
        raise ValueError("affiliated hitting skill counts violate accounting")
    if stat_group == "pitching" and result.filter(
        (pl.col("starts") > pl.col("games"))
        | (pl.col("intentional_walks") > pl.col("base_on_balls"))
        | (pl.col("strike_outs") + pl.col("base_on_balls") - pl.col("intentional_walks")
           + pl.col("hit_batters") + pl.col("home_runs") > pl.col("batters_faced"))
    ).height:
        raise ValueError("affiliated pitching skill counts violate accounting")
    return result


def fetch_affiliated_skill_stats(
    season: int,
    *,
    stat_group: str,
    page_size: int = 5000,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, list[AffiliatedSkillCapture]]:
    """Fetch all affiliated player/team/level component splits."""

    if not 1 <= page_size <= 5000:
        raise ValueError("page_size must be between 1 and 5000")
    if stat_group not in {"hitting", "pitching"}:
        raise ValueError("stat_group must be hitting or pitching")
    owned = session is None
    active = session or requests.Session()
    frames: list[pl.DataFrame] = []
    captures: list[AffiliatedSkillCapture] = []
    seen: set[tuple[tuple[int, int, int | None], ...]] = set()
    try:
        for page in range(20):
            offset = page * page_size
            response = _statsapi_get_with_retry(
                active, f"{STATS_API_BASE}/stats",
                params={
                    "stats": "season", "group": stat_group, "playerPool": "ALL",
                    "season": int(season),
                    "sportIds": ",".join(str(value) for value in AFFILIATED_SPORT_IDS),
                    "gameType": "R", "limit": page_size, "offset": offset,
                },
                timeout_seconds=120,
            )
            payload = response.json()
            blocks = payload.get("stats") or []
            if len(blocks) != 1:
                raise ValueError("affiliated skill response must contain one stats block")
            splits = blocks[0].get("splits") or []
            frame = project_affiliated_skill_splits(
                splits, season=int(season), stat_group=stat_group
            )
            signature = tuple(frame.select("player_id", "sport_id", "team_id").iter_rows())
            if signature and signature in seen:
                raise ValueError("affiliated skill pagination repeated a page")
            seen.add(signature)
            frames.append(frame)
            total = blocks[0].get("totalSplits")
            captures.append(
                AffiliatedSkillCapture(
                    season=int(season), stat_group=stat_group, offset=offset,
                    requested_limit=page_size, returned_rows=frame.height,
                    reported_total_splits=int(total) if total is not None else None,
                    response_bytes=response.content,
                    response_sha256=sha256(response.content).hexdigest(),
                )
            )
            if frame.height < page_size:
                break
        else:
            raise ValueError("affiliated skill pagination exceeded safety limit")
    finally:
        if owned:
            active.close()
    schema = AFFILIATED_HITTING_SKILL_SCHEMA if stat_group == "hitting" else AFFILIATED_PITCHING_SKILL_SCHEMA
    result = pl.concat(frames) if frames else pl.DataFrame(schema=schema)
    key = ["season", "player_id", "sport_id", "team_id"]
    if result.group_by(key).len().filter(pl.col("len") != 1).height:
        raise ValueError("affiliated skill pages contain duplicate split keys")
    return result.sort(["season", "player_id", "sport_id", "team_id"]), captures
