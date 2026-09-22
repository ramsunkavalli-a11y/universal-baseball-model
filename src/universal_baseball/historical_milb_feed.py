"""Project historical MiLB game feeds into auditable game context and batting rows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl


OFFICIAL_BATTING_MAP = {
    "batting_PA": "plateAppearances",
    "batting_AB": "atBats",
    "batting_H": "hits",
    "batting_2B": "doubles",
    "batting_3B": "triples",
    "batting_HR": "homeRuns",
    "batting_BB": "baseOnBalls",
    "batting_IBB": "intentionalWalks",
    "batting_HBP": "hitByPitch",
    "batting_SO": "strikeOuts",
    "batting_SF": "sacFlies",
    "batting_SH": "sacBunts",
    "batting_CI": "catchersInterference",
    "batting_GiDP": "groundIntoDoublePlay",
    "batting_GiTP": "groundIntoTriplePlay",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _integer(value: Any, *, field: str) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} is not integer-like: {value!r}") from exc
    if not numeric.is_integer():
        raise ValueError(f"{field} is not integer-like: {value!r}")
    return int(numeric)


def _season_year(value: Any, *, official_date: str) -> int:
    """Normalize historical Stats API sub-season labels such as ``2018.1``."""

    try:
        numeric = float(value)
        date_year = int(str(official_date)[:4])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"game season/date is not usable: {value!r}/{official_date!r}") from exc
    season_year = int(numeric)
    if season_year != date_year or numeric < season_year or numeric >= season_year + 1:
        raise ValueError(
            f"game season disagrees with official date: {value!r}/{official_date!r}"
        )
    return season_year


def _collapse_player_team_stints(player_frame: pl.DataFrame, *, game_id: int) -> pl.DataFrame:
    """Collapse rare suspended-game rows where a player appears for both clubs."""

    if not player_frame.select("game_id", "player_id").is_duplicated().any():
        return player_frame

    rows: list[dict[str, Any]] = []
    for group in player_frame.partition_by("player_id", maintain_order=True):
        values = group.to_dicts()
        if len(values) == 1:
            rows.append(values[0])
            continue
        for field in ("game_id", "game_date", "game_type", "league_id", "player_id"):
            if len({row[field] for row in values}) != 1:
                raise ValueError(
                    f"historical game {game_id} has conflicting duplicate-player {field}"
                )
        positive = [row for row in values if int(row.get("batting_PA") or 0) > 0]
        positive_teams = {row["team_id"] for row in positive}
        selected_team = next(iter(positive_teams)) if len(positive_teams) == 1 else None
        selected_side = next(
            (row["side"] for row in positive if row["team_id"] == selected_team),
            None,
        )
        combined = values[0].copy()
        combined["team_id"] = selected_team
        combined["side"] = selected_side
        for field in OFFICIAL_BATTING_MAP:
            observed = [row[field] for row in values if row[field] is not None]
            combined[field] = sum(int(value) for value in observed) if observed else None
        rows.append(combined)
    return pl.DataFrame(rows, schema=player_frame.schema).sort(
        "game_id", "team_id", "player_id", nulls_last=True
    )


def project_historical_milb_game_feed(
    payload: Mapping[str, Any],
    *,
    expected_game_id: int | None = None,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Return player-game batting authority and one game-context row.

    The official feed is independent of the archived PBP CSV. Missing identity,
    league, or venue fields remain an error rather than being inferred from a
    filename level or home-team convention.
    """

    game_data = _mapping(payload.get("gameData"))
    game = _mapping(game_data.get("game"))
    game_id = _integer(game.get("pk"), field="gameData.game.pk")
    if game_id is None:
        raise ValueError("historical game feed lacks gameData.game.pk")
    if expected_game_id is not None and game_id != int(expected_game_id):
        raise ValueError(
            f"historical game feed id mismatch: expected={expected_game_id}, actual={game_id}"
        )

    game_type = str(game.get("type") or "").strip()
    official_date = str(
        _mapping(game_data.get("datetime")).get("officialDate") or ""
    ).strip()
    season = _season_year(game.get("season"), official_date=official_date)
    venue = _mapping(game_data.get("venue"))
    venue_id = _integer(venue.get("id"), field="gameData.venue.id")
    if not game_type or not official_date or venue_id is None:
        raise ValueError(
            f"historical game {game_id} lacks season, type, official date, or venue"
        )

    teams = _mapping(game_data.get("teams"))
    boxscore_teams = _mapping(
        _mapping(_mapping(payload.get("liveData")).get("boxscore")).get("teams")
    )
    player_rows: list[dict[str, Any]] = []
    context: dict[str, Any] = {
        "season": season,
        "game_id": game_id,
        "game_date": official_date,
        "game_type": game_type,
        "venue_id": venue_id,
        "venue_name": str(venue.get("name") or "").strip() or None,
    }

    for side in ("away", "home"):
        team = _mapping(teams.get(side))
        team_id = _integer(team.get("id"), field=f"gameData.teams.{side}.id")
        league_id = _integer(
            _mapping(team.get("league")).get("id"),
            field=f"gameData.teams.{side}.league.id",
        )
        if team_id is None or league_id is None:
            raise ValueError(
                f"historical game {game_id} lacks {side} team or league identity"
            )
        context[f"{side}_team_id"] = team_id
        context[f"{side}_league_id"] = league_id

        players = _mapping(_mapping(boxscore_teams.get(side)).get("players"))
        for raw_player in players.values():
            player = _mapping(raw_player)
            person = _mapping(player.get("person"))
            player_id = _integer(person.get("id"), field="boxscore player id")
            batting = _mapping(_mapping(player.get("stats")).get("batting"))
            if player_id is None or not batting:
                continue
            row: dict[str, Any] = {
                "game_id": game_id,
                "game_date": official_date,
                "game_type": game_type,
                "league_id": league_id,
                "team_id": team_id,
                "player_id": player_id,
                "side": side,
            }
            for output, source in OFFICIAL_BATTING_MAP.items():
                row[output] = _integer(
                    batting.get(source), field=f"player={player_id} {source}"
                )
            player_rows.append(row)

    if not player_rows:
        raise ValueError(f"historical game {game_id} has no player batting rows")
    player_frame = _collapse_player_team_stints(
        pl.DataFrame(player_rows).sort("game_id", "team_id", "player_id"),
        game_id=game_id,
    )
    return player_frame, pl.DataFrame([context])
