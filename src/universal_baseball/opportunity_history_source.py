"""Official aggregate sources for zero-inclusive historical opportunity cohorts."""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl
import requests

from universal_baseball.playing_time_roster_source import STATS_API_BASE


AFFILIATED_SPORT_IDS = (1, 11, 12, 13, 14, 16)
SPORT_LEVEL = {1: "MLB", 11: "AAA", 12: "AA", 13: "HIGH_A", 14: "SINGLE_A", 16: "ROOKIE_COMPLEX"}
LEVEL_RANK = {value: index for index, value in enumerate(reversed(tuple(SPORT_LEVEL.values())))}

AFFILIATED_SEASON_STAT_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "stat_group": pl.String,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "sport_id": pl.Int64,
    "level_group": pl.String,
    "team_id": pl.Int64,
    "position_code": pl.String,
    "reported_age": pl.Float64,
    "plate_appearances": pl.Int64,
    "games": pl.Int64,
    "starts": pl.Int64,
    "batters_faced": pl.Int64,
}

HISTORICAL_ROSTER_DETAIL_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_date": pl.Date,
    "snapshot_year": pl.Int64,
    "candidate_organization_id": pl.Int64,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "position_codes": pl.String,
    "source_row_count": pl.Int64,
}

HISTORICAL_HITTER_SNAPSHOT_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_year": pl.Int64,
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
}

HISTORICAL_PITCHER_SNAPSHOT_SCHEMA: dict[str, pl.DataType] = {
    "snapshot_year": pl.Int64,
    "player_id": pl.Int64,
    "age_years": pl.Float64,
    "as_of_level_group": pl.String,
    "as_of_role": pl.String,
}


def project_affiliated_season_stats_payload(
    payload: dict[str, Any], *, season: int, stat_group: str
) -> pl.DataFrame:
    """Project one StatsAPI aggregate-stat page without trusting totalSplits."""

    if stat_group not in {"hitting", "pitching"}:
        raise ValueError("affiliated stat group must be hitting or pitching")
    blocks = payload.get("stats")
    if not isinstance(blocks, list) or len(blocks) != 1:
        raise ValueError("affiliated stats payload must contain exactly one stats block")
    splits = blocks[0].get("splits")
    if not isinstance(splits, list):
        raise ValueError("affiliated stats payload missing splits")
    rows: list[dict[str, object]] = []
    for split in splits:
        if not isinstance(split, dict):
            raise ValueError("affiliated stats split must be an object")
        player = split.get("player") or {}
        sport = split.get("sport") or {}
        team = split.get("team") or {}
        position = split.get("position") or {}
        stat = split.get("stat") or {}
        player_id = player.get("id")
        sport_id = sport.get("id")
        if player_id is None or sport_id is None or int(sport_id) not in SPORT_LEVEL:
            raise ValueError("affiliated stats split has unsupported identity or sport")
        rows.append(
            {
                "season": int(season),
                "stat_group": stat_group,
                "player_id": int(player_id),
                "player_name": str(player.get("fullName") or ""),
                "sport_id": int(sport_id),
                "level_group": SPORT_LEVEL[int(sport_id)],
                "team_id": int(team["id"]) if team.get("id") is not None else None,
                "position_code": str(position.get("code") or ""),
                "reported_age": float(stat["age"]) if stat.get("age") is not None else None,
                "plate_appearances": int(stat.get("plateAppearances") or 0),
                "games": int(stat.get("gamesPlayed") or 0),
                "starts": int(stat.get("gamesStarted") or 0),
                "batters_faced": int(stat.get("battersFaced") or 0),
            }
        )
    result = pl.DataFrame(rows, schema=AFFILIATED_SEASON_STAT_SCHEMA)
    if result.filter(
        (pl.col("plate_appearances") < 0)
        | (pl.col("games") < 0)
        | (pl.col("starts") < 0)
        | (pl.col("batters_faced") < 0)
        | (pl.col("starts") > pl.col("games"))
    ).height:
        raise ValueError("affiliated stats split has invalid counts")
    return result


def fetch_affiliated_season_stats(
    season: int,
    *,
    stat_group: str,
    page_size: int = 5000,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, list[dict[str, object]]]:
    """Fetch every aggregate split, paging until the API returns a short page."""

    if not 1 <= page_size <= 5000:
        raise ValueError("affiliated stat page size must be between 1 and 5000")
    own_session = session is None
    http = session or requests.Session()
    frames: list[pl.DataFrame] = []
    captures: list[dict[str, object]] = []
    seen_page_signatures: set[tuple[tuple[int, int, int | None], ...]] = set()
    try:
        for page in range(20):
            offset = page * page_size
            response = http.get(
                f"{STATS_API_BASE}/stats",
                params={
                    "stats": "season",
                    "group": stat_group,
                    "playerPool": "ALL",
                    "season": int(season),
                    "sportIds": ",".join(str(value) for value in AFFILIATED_SPORT_IDS),
                    "limit": page_size,
                    "offset": offset,
                },
                timeout=120,
            )
            response.raise_for_status()
            payload = response.json()
            frame = project_affiliated_season_stats_payload(
                payload, season=int(season), stat_group=stat_group
            )
            signature = tuple(
                frame.select("player_id", "sport_id", "team_id").iter_rows()
            )
            if signature and signature in seen_page_signatures:
                raise ValueError("affiliated stats pagination repeated a page")
            seen_page_signatures.add(signature)
            frames.append(frame)
            captures.append(
                {
                    "season": int(season),
                    "stat_group": stat_group,
                    "offset": offset,
                    "returned_rows": frame.height,
                    "reported_total_splits": (payload.get("stats") or [{}])[0].get(
                        "totalSplits"
                    ),
                    "requested_url": response.url,
                    "status_code": int(response.status_code),
                }
            )
            if frame.height < page_size:
                break
        else:
            raise ValueError("affiliated stats pagination exceeded the safety limit")
    finally:
        if own_session:
            http.close()
    result = pl.concat(frames) if frames else pl.DataFrame(schema=AFFILIATED_SEASON_STAT_SCHEMA)
    key = ["stat_group", "season", "player_id", "sport_id", "team_id"]
    if result.group_by(key).len().filter(pl.col("len") != 1).height:
        raise ValueError("affiliated stats pages contain duplicate split keys")
    return result.sort(["player_id", "sport_id", "team_id"]), captures


def project_historical_full_roster_payload(
    payload: dict[str, Any], *, team_id: int, snapshot_date: date
) -> pl.DataFrame:
    """Keep player and position identity; do not interpret status or ownership."""

    roster = payload.get("roster")
    if not isinstance(roster, list):
        raise ValueError("historical fullRoster payload missing roster")
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in roster:
        player_id = (row.get("person") or {}).get("id") if isinstance(row, dict) else None
        if player_id is None:
            raise ValueError("historical fullRoster row missing player identity")
        grouped.setdefault(int(player_id), []).append(row)
    rows = []
    for player_id, player_rows in sorted(grouped.items()):
        names = {str((row.get("person") or {}).get("fullName") or "") for row in player_rows}
        if len(names) != 1:
            raise ValueError("historical fullRoster duplicate has conflicting identity")
        position_codes = sorted(
            {str((row.get("position") or {}).get("code") or "") for row in player_rows}
        )
        rows.append(
            {
                "snapshot_date": snapshot_date,
                "snapshot_year": snapshot_date.year,
                "candidate_organization_id": int(team_id),
                "player_id": player_id,
                "player_name": next(iter(names)),
                "position_codes": ",".join(position_codes),
                "source_row_count": len(player_rows),
            }
        )
    return pl.DataFrame(rows, schema=HISTORICAL_ROSTER_DETAIL_SCHEMA)


def fetch_historical_full_roster_detail(
    team_id: int,
    *,
    snapshot_date: date,
    session: requests.Session | None = None,
) -> tuple[pl.DataFrame, dict[str, object]]:
    """Fetch one official historical fullRoster while retaining position evidence."""

    own_session = session is None
    http = session or requests.Session()
    try:
        response = http.get(
            f"{STATS_API_BASE}/teams/{int(team_id)}/roster",
            params={
                "rosterType": "fullRoster",
                "season": snapshot_date.year,
                "date": snapshot_date.isoformat(),
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("historical fullRoster response must be an object")
        return (
            project_historical_full_roster_payload(
                payload, team_id=int(team_id), snapshot_date=snapshot_date
            ),
            {
                "team_id": int(team_id),
                "snapshot_date": snapshot_date.isoformat(),
                "requested_url": response.url,
                "status_code": int(response.status_code),
                "payload": payload,
            },
        )
    finally:
        if own_session:
            http.close()


def _highest_level(group: pl.DataFrame) -> str:
    return max(group.get_column("level_group").to_list(), key=LEVEL_RANK.__getitem__)


def build_opportunity_snapshots(
    roster_details: pl.DataFrame,
    season_stats: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Build hitter and pitcher snapshot denominators from roster plus season use."""

    roster = roster_details.select(list(HISTORICAL_ROSTER_DETAIL_SCHEMA)).cast(
        HISTORICAL_ROSTER_DETAIL_SCHEMA, strict=True
    )
    stats = season_stats.select(list(AFFILIATED_SEASON_STAT_SCHEMA)).cast(
        AFFILIATED_SEASON_STAT_SCHEMA, strict=True
    )
    if roster.is_empty() or roster.get_column("snapshot_year").n_unique() != 1:
        raise ValueError("opportunity snapshot requires one nonempty roster year")
    snapshot_year = int(roster.item(0, "snapshot_year"))
    if stats.filter(pl.col("season") != snapshot_year).height:
        raise ValueError("opportunity snapshot stats differ from roster year")
    roster_players = (
        roster.group_by("player_id")
        .agg(
            pl.col("position_codes")
            .str.split(",")
            .explode(empty_as_null=True)
            .unique()
            .sort()
            .str.join(",")
            .alias("position_codes")
        )
        .sort("player_id")
    )
    roster_codes = {
        int(row["player_id"]): {
            value for value in str(row["position_codes"]).split(",") if value
        }
        for row in roster_players.iter_rows(named=True)
    }
    stats_by_player = {
        int(group.item(0, "player_id")): group
        for group in stats.partition_by("player_id", maintain_order=False)
    }
    empty_stats = pl.DataFrame(schema=AFFILIATED_SEASON_STAT_SCHEMA)
    player_ids = sorted(set(roster_codes) | set(stats_by_player))
    hitter_rows = []
    pitcher_rows = []
    for player_id in player_ids:
        player_stats = stats_by_player.get(player_id, empty_stats)
        codes = set(roster_codes.get(player_id, set())) | set(
            player_stats.get_column("position_code").to_list()
        )
        codes.discard("")
        hitting = player_stats.filter(pl.col("stat_group") == "hitting")
        pitching = player_stats.filter(pl.col("stat_group") == "pitching")
        reported_ages = player_stats.get_column("reported_age").drop_nulls()
        age = float(reported_ages.median()) if len(reported_ages) else None
        informative_codes = codes - {"X"}
        is_pitcher = bool({"1", "Y"} & informative_codes)
        is_hitter = bool(informative_codes - {"1"})
        if not informative_codes:
            is_pitcher = not pitching.is_empty()
            is_hitter = not hitting.is_empty()
        if is_hitter:
            hitter_rows.append(
                {
                    "snapshot_year": snapshot_year,
                    "player_id": player_id,
                    "age_years": age,
                    "as_of_level_group": _highest_level(hitting)
                    if not hitting.is_empty()
                    else "INACTIVE",
                }
            )
        if is_pitcher:
            if pitching.is_empty():
                level = "INACTIVE"
                role = "unknown"
            else:
                level = _highest_level(pitching)
                at_level = pitching.filter(pl.col("level_group") == level)
                games = int(at_level.get_column("games").sum())
                starts = int(at_level.get_column("starts").sum())
                if games <= 0:
                    role = "unknown"
                elif starts == 0:
                    role = "reliever"
                elif starts * 2 >= games:
                    role = "starter"
                else:
                    role = "swingman"
            pitcher_rows.append(
                {
                    "snapshot_year": snapshot_year,
                    "player_id": player_id,
                    "age_years": age,
                    "as_of_level_group": level,
                    "as_of_role": role,
                }
            )
    return (
        pl.DataFrame(hitter_rows, schema=HISTORICAL_HITTER_SNAPSHOT_SCHEMA).sort("player_id"),
        pl.DataFrame(pitcher_rows, schema=HISTORICAL_PITCHER_SNAPSHOT_SCHEMA).sort("player_id"),
    )
