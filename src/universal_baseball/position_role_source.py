"""Deterministic official fielding-source projection for position/role work.

This module converts already-fetched Stats API season fielding splits into a
small canonical source table. It does not fit a position model, infer a missing
role, allocate team playing time, or access future seasons.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import polars as pl


POSITION_CODE_ABBREVIATION: dict[str, str] = {
    "1": "P",
    "2": "C",
    "3": "1B",
    "4": "2B",
    "5": "3B",
    "6": "SS",
    "7": "LF",
    "8": "CF",
    "9": "RF",
    "10": "DH",
}

FIELDING_USAGE_SCHEMA: dict[str, pl.DataType] = {
    "season": pl.Int64,
    "league_id": pl.Int64,
    "level_group": pl.String,
    "team_id": pl.Int64,
    "team_name": pl.String,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "position_code": pl.String,
    "position_abbreviation": pl.String,
    "position_name": pl.String,
    "position_type": pl.String,
    "games_played": pl.Int64,
    "games_started": pl.Int64,
    "source_innings": pl.String,
    "fielding_outs": pl.Int64,
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonnegative_integer(value: Any, *, field: str) -> int:
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing required integer-like value for {field}")
    try:
        numeric = float(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer-like value for {field}: {value!r}") from exc
    if not numeric.is_integer():
        raise ValueError(f"non-integer value for {field}: {value!r}")
    result = int(numeric)
    if result < 0:
        raise ValueError(f"negative value for {field}: {result}")
    return result


def baseball_innings_to_outs(value: Any) -> int:
    """Convert baseball innings notation (e.g. 12.2) to exact defensive outs."""

    if value is None:
        raise ValueError("missing fielding innings")
    text = str(value).strip()
    if not text:
        raise ValueError("blank fielding innings")
    if text.startswith("-"):
        raise ValueError(f"negative fielding innings: {text!r}")
    if "." in text:
        whole_text, fraction = text.split(".", 1)
    else:
        whole_text, fraction = text, "0"
    if not whole_text.isdigit():
        raise ValueError(f"invalid fielding innings whole component: {text!r}")
    if fraction not in {"0", "1", "2"}:
        raise ValueError(
            f"invalid baseball innings fractional-out suffix: {text!r}; expected .0/.1/.2"
        )
    return int(whole_text) * 3 + int(fraction)


def project_fielding_usage_splits(
    splits: Sequence[Mapping[str, Any]],
    *,
    season: int,
    league_id: int,
    level_group: str,
) -> pl.DataFrame:
    """Project official fielding splits to exact player/team/position usage rows."""

    rows: list[dict[str, object]] = []
    for split in splits:
        player = _mapping(split.get("player") or split.get("person"))
        team = _mapping(split.get("team"))
        position = _mapping(split.get("position"))
        stat = _mapping(split.get("stat"))

        player_id = _nonnegative_integer(player.get("id"), field="player.id")
        team_id = _nonnegative_integer(team.get("id"), field="team.id")
        position_code = str(position.get("code") or "").strip()
        position_abbreviation = str(position.get("abbreviation") or "").strip()
        position_name = str(position.get("name") or "").strip()
        position_type = str(position.get("type") or "").strip()
        if position_code not in POSITION_CODE_ABBREVIATION:
            raise ValueError(
                f"unsupported position code for player={player_id}: {position_code!r}"
            )
        expected_abbreviation = POSITION_CODE_ABBREVIATION[position_code]
        if position_abbreviation != expected_abbreviation:
            raise ValueError(
                f"position code/abbreviation mismatch for player={player_id}: "
                f"code={position_code!r}, abbreviation={position_abbreviation!r}, "
                f"expected={expected_abbreviation!r}"
            )
        if not position_name:
            raise ValueError(f"missing position name for player={player_id}")

        games = _nonnegative_integer(stat.get("games"), field="stat.games")
        games_played = _nonnegative_integer(
            stat.get("gamesPlayed"), field="stat.gamesPlayed"
        )
        games_started = _nonnegative_integer(
            stat.get("gamesStarted"), field="stat.gamesStarted"
        )
        if games != games_played:
            raise ValueError(
                f"fielding games/gamesPlayed mismatch for player={player_id}, "
                f"position={position_abbreviation}: {games} != {games_played}"
            )
        if games_started > games_played:
            raise ValueError(
                f"fielding gamesStarted exceeds gamesPlayed for player={player_id}, "
                f"position={position_abbreviation}: {games_started} > {games_played}"
            )
        source_innings = str(stat.get("innings") if stat.get("innings") is not None else "").strip()
        fielding_outs = baseball_innings_to_outs(source_innings)
        if position_abbreviation == "DH" and fielding_outs != 0:
            raise ValueError(
                f"DH row has nonzero defensive outs for player={player_id}: {fielding_outs}"
            )

        rows.append(
            {
                "season": int(season),
                "league_id": int(league_id),
                "level_group": str(level_group),
                "team_id": team_id,
                "team_name": str(team.get("name") or ""),
                "player_id": player_id,
                "player_name": str(player.get("fullName") or ""),
                "position_code": position_code,
                "position_abbreviation": position_abbreviation,
                "position_name": position_name,
                "position_type": position_type,
                "games_played": games_played,
                "games_started": games_started,
                "source_innings": source_innings,
                "fielding_outs": fielding_outs,
            }
        )

    frame = (
        pl.DataFrame(rows, schema=FIELDING_USAGE_SCHEMA)
        if rows
        else pl.DataFrame(schema=FIELDING_USAGE_SCHEMA)
    )
    key = ["season", "league_id", "team_id", "player_id", "position_code"]
    duplicates = frame.group_by(key).len().filter(pl.col("len") != 1)
    if not duplicates.is_empty():
        raise ValueError(
            "official fielding source violates season/league/team/player/position grain"
        )
    return frame.sort(key)


def project_hitting_player_ids(splits: Sequence[Mapping[str, Any]]) -> set[int]:
    """Return exact same-league hitting player IDs for fielding coverage diagnostics."""

    player_ids: set[int] = set()
    for split in splits:
        player = _mapping(split.get("player") or split.get("person"))
        player_id = _nonnegative_integer(player.get("id"), field="hitting player.id")
        player_ids.add(player_id)
    return player_ids
