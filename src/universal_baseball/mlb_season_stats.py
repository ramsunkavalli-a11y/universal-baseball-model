"""Bulk MLB season-hitting backbone for the Performance layer.

The Stats API ``/stats`` endpoint supports ``playerPool=ALL`` with pagination
and league filtering. Completed-2024 certification established that AL (103) and
NL (104) player-season rows sum exactly to the MLB-wide result for every player
and required standard count. This module promotes that bulk path into production
without introducing per-player requests.

The canonical output intentionally mirrors the standardized affiliated MiLB
batting backbone consumed by :mod:`universal_baseball.performance_season`.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping

import polars as pl
import requests


MLB_STATS_URL = "https://statsapi.mlb.com/api/v1/stats"
MLB_TEAM_URL = "https://statsapi.mlb.com/api/v1/teams"
MLB_LEAGUE_IDS = (103, 104)
_REQUIRED_FIELDS = (
    "plateAppearances",
    "atBats",
    "baseOnBalls",
    "intentionalWalks",
    "hitByPitch",
    "strikeOuts",
    "sacBunts",
    "sacFlies",
)

MLB_BATTING_BACKBONE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "batting_plate_appearances": pl.Int64,
    "batting_at_bats": pl.Int64,
    "batting_base_on_balls": pl.Int64,
    "batting_intentional_walks": pl.Int64,
    "batting_hit_by_pitch": pl.Int64,
    "batting_strike_outs": pl.Int64,
    "batting_sac_bunts": pl.Int64,
    "batting_sac_flies": pl.Int64,
    "batting_balls_in_play": pl.Int64,
    "simple_pa_accounting_residual": pl.Int64,
}


@dataclass(frozen=True)
class MlbBulkStatsCapture:
    season: int
    league_id: int
    offset: int
    requested_limit: int
    response_bytes: bytes
    response_sha256: str
    returned_split_count: int
    total_splits: int | None


@dataclass(frozen=True)
class MlbTeamLeague:
    team_id: int
    abbreviation: str
    league_id: int
    league_name: str


def _integer_like(value: Any, *, field: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing required integer-like value for {field}")
    numeric = float(str(value))
    if not numeric.is_integer():
        raise ValueError(f"non-integer value for {field}: {value!r}")
    result = int(numeric)
    if result < 0:
        raise ValueError(f"negative count for {field}: {result}")
    return result


def project_mlb_hitting_splits(
    splits: list[Mapping[str, Any]],
    *,
    season: int,
    league_id: int,
) -> pl.DataFrame:
    """Project one league-filtered Stats API season result to canonical counts."""

    if int(league_id) not in MLB_LEAGUE_IDS:
        raise ValueError(f"unsupported MLB actual league_id: {league_id}")
    rows: list[dict[str, Any]] = []
    for split in splits:
        person = split.get("player") or split.get("person") or {}
        stat = split.get("stat") or {}
        player_id = _integer_like(person.get("id"), field="player.id")
        missing = [field for field in _REQUIRED_FIELDS if field not in stat]
        if missing:
            raise ValueError(
                f"MLB bulk hitting split for {player_id} missing fields: {missing}"
            )
        plate_appearances = _integer_like(stat.get("plateAppearances"), field="plateAppearances")
        at_bats = _integer_like(stat.get("atBats"), field="atBats")
        base_on_balls = _integer_like(stat.get("baseOnBalls"), field="baseOnBalls")
        intentional_walks = _integer_like(stat.get("intentionalWalks"), field="intentionalWalks")
        hit_by_pitch = _integer_like(stat.get("hitByPitch"), field="hitByPitch")
        strikeouts = _integer_like(stat.get("strikeOuts"), field="strikeOuts")
        sac_bunts = _integer_like(stat.get("sacBunts"), field="sacBunts")
        sac_flies = _integer_like(stat.get("sacFlies"), field="sacFlies")
        broad_contacts = at_bats - strikeouts + sac_bunts + sac_flies
        if broad_contacts < 0:
            raise ValueError(f"negative derived broad contacts for MLBAM {player_id}")
        simple_residual = (
            at_bats
            + base_on_balls
            + hit_by_pitch
            + sac_bunts
            + sac_flies
            - plate_appearances
        )
        rows.append(
            {
                "season": int(season),
                "league_id": int(league_id),
                "player_id": player_id,
                "player_name": str(person.get("fullName") or ""),
                "batting_plate_appearances": plate_appearances,
                "batting_at_bats": at_bats,
                "batting_base_on_balls": base_on_balls,
                "batting_intentional_walks": intentional_walks,
                "batting_hit_by_pitch": hit_by_pitch,
                "batting_strike_outs": strikeouts,
                "batting_sac_bunts": sac_bunts,
                "batting_sac_flies": sac_flies,
                "batting_balls_in_play": broad_contacts,
                "simple_pa_accounting_residual": simple_residual,
            }
        )
    if not rows:
        return pl.DataFrame(schema=MLB_BATTING_BACKBONE_SCHEMA)
    result = (
        pl.DataFrame(rows, schema=MLB_BATTING_BACKBONE_SCHEMA)
        .sort(["league_id", "player_id"])
    )
    duplicates = result.group_by(["season", "league_id", "player_id"]).len().filter(
        pl.col("len") > 1
    )
    if not duplicates.is_empty():
        raise ValueError("MLB bulk hitting projection has duplicate player-league-season keys")
    return result


def fetch_mlb_hitting_backbone(
    season: int,
    *,
    league_ids: tuple[int, ...] = MLB_LEAGUE_IDS,
    page_limit: int = 500,
    session: requests.Session | None = None,
    timeout_seconds: int = 120,
) -> tuple[pl.DataFrame, list[MlbBulkStatsCapture]]:
    """Fetch completed regular-season batting counts at actual AL/NL grain."""

    if page_limit <= 0:
        raise ValueError("page_limit must be positive")
    owned = session is None
    active = session or requests.Session()
    captures: list[MlbBulkStatsCapture] = []
    frames: list[pl.DataFrame] = []
    try:
        for league_id in league_ids:
            offset = 0
            splits_for_league: list[Mapping[str, Any]] = []
            while True:
                params = {
                    "stats": "season",
                    "group": "hitting",
                    "season": int(season),
                    "sportIds": 1,
                    "leagueId": int(league_id),
                    "playerPool": "ALL",
                    "gameType": "R",
                    "limit": int(page_limit),
                    "offset": int(offset),
                }
                response = active.get(MLB_STATS_URL, params=params, timeout=timeout_seconds)
                response.raise_for_status()
                content = response.content
                payload = response.json()
                groups = payload.get("stats") or []
                if len(groups) != 1:
                    raise RuntimeError(
                        f"expected one MLB stats group for league {league_id}, found {len(groups)}"
                    )
                group = groups[0]
                splits = group.get("splits") or []
                total = group.get("totalSplits")
                total_int = int(total) if total is not None else None
                captures.append(
                    MlbBulkStatsCapture(
                        season=int(season),
                        league_id=int(league_id),
                        offset=int(offset),
                        requested_limit=int(page_limit),
                        response_bytes=content,
                        response_sha256=sha256(content).hexdigest(),
                        returned_split_count=len(splits),
                        total_splits=total_int,
                    )
                )
                splits_for_league.extend(splits)
                if total_int is not None and len(splits_for_league) >= total_int:
                    break
                if not splits or len(splits) < page_limit:
                    break
                offset += len(splits)
                if offset > 5000:
                    raise RuntimeError("MLB bulk hitting pagination exceeded safety bound")
            frames.append(
                project_mlb_hitting_splits(
                    splits_for_league,
                    season=int(season),
                    league_id=int(league_id),
                )
            )
    finally:
        if owned:
            active.close()

    if not frames:
        return pl.DataFrame(schema=MLB_BATTING_BACKBONE_SCHEMA), captures
    combined = pl.concat(frames, how="vertical_relaxed").sort(
        ["season", "league_id", "player_id"]
    )
    duplicates = combined.group_by(["season", "league_id", "player_id"]).len().filter(
        pl.col("len") > 1
    )
    if not duplicates.is_empty():
        raise RuntimeError("MLB bulk hitting backbone contains duplicate canonical keys")
    return combined, captures


def fetch_mlb_team_leagues(
    season: int,
    *,
    session: requests.Session | None = None,
    timeout_seconds: int = 60,
) -> tuple[list[MlbTeamLeague], bytes]:
    """Fetch MLB team abbreviation -> actual league authority for one season."""

    owned = session is None
    active = session or requests.Session()
    try:
        response = active.get(
            MLB_TEAM_URL,
            params={"sportId": 1, "season": int(season)},
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        content = response.content
        payload = response.json()
    finally:
        if owned:
            active.close()

    rows: list[MlbTeamLeague] = []
    for team in payload.get("teams") or []:
        league = team.get("league") or {}
        league_id = league.get("id")
        if league_id not in MLB_LEAGUE_IDS:
            continue
        abbreviation = str(team.get("abbreviation") or "").strip()
        if not abbreviation:
            raise RuntimeError("MLB team metadata missing abbreviation")
        rows.append(
            MlbTeamLeague(
                team_id=_integer_like(team.get("id"), field="team.id"),
                abbreviation=abbreviation,
                league_id=int(league_id),
                league_name=str(league.get("name") or ""),
            )
        )
    if len(rows) != 30:
        raise RuntimeError(f"expected 30 MLB AL/NL teams, found {len(rows)}")
    if len({row.abbreviation for row in rows}) != len(rows):
        raise RuntimeError("MLB team metadata contains duplicate abbreviations")
    return sorted(rows, key=lambda row: row.team_id), content


def capture_manifest(captures: list[MlbBulkStatsCapture]) -> str:
    """Compact JSON provenance helper for generated reports/artifacts."""

    return json.dumps(
        [
            {
                "season": capture.season,
                "league_id": capture.league_id,
                "offset": capture.offset,
                "requested_limit": capture.requested_limit,
                "response_sha256": capture.response_sha256,
                "response_byte_count": len(capture.response_bytes),
                "returned_split_count": capture.returned_split_count,
                "total_splits": capture.total_splits,
            }
            for capture in captures
        ],
        separators=(",", ":"),
        sort_keys=True,
    )
