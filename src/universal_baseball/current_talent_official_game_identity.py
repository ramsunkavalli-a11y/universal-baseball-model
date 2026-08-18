"""Exact official game identity for rare same-game league-map gaps.

Historical MiLB PBP normally inherits actual league identity only from the unique
same-game structured player-game map.  Rarely, a real PBP game can be absent
from that reusable player-game surface.  This module provides a narrow official
fallback using the exact Stats API game feed.

A fallback is accepted only when the official game is regular season, both teams
report the same non-null league, both teams report the same expected sport, and
the league belongs to the already-certified era/filename-level league set.
Filename level is never itself used as league identity.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Any

import polars as pl


@dataclass(frozen=True, slots=True)
class OfficialGameLeagueIdentity:
    game_pk: int
    game_date: date
    game_type: str
    league_id: int
    sport_id: int
    away_team_id: int
    home_team_id: int


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return int(numeric) if numeric.is_integer() else None


def _date(value: Any) -> date | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def project_official_game_league_identity(
    game_id: int,
    payload: Mapping[str, Any],
) -> OfficialGameLeagueIdentity:
    """Project one exact Stats API live-feed payload to unambiguous game league identity."""

    game_data = _mapping(payload.get("gameData"))
    game = _mapping(game_data.get("game"))
    datetime_data = _mapping(game_data.get("datetime"))
    teams = _mapping(game_data.get("teams"))
    away = _mapping(teams.get("away"))
    home = _mapping(teams.get("home"))

    game_type = str(game.get("type") or "").strip()
    official_date = _date(datetime_data.get("officialDate"))
    away_team = _int(away.get("id"))
    home_team = _int(home.get("id"))
    away_league = _int(_mapping(away.get("league")).get("id"))
    home_league = _int(_mapping(home.get("league")).get("id"))
    away_sport = _int(_mapping(away.get("sport")).get("id"))
    home_sport = _int(_mapping(home.get("sport")).get("id"))

    if game_type != "R":
        raise ValueError(f"official game {game_id} is not regular season: {game_type!r}")
    if official_date is None:
        raise ValueError(f"official game {game_id} lacks officialDate")
    if away_team is None or home_team is None:
        raise ValueError(f"official game {game_id} lacks team identity")
    if away_league is None or home_league is None or away_league != home_league:
        raise ValueError(
            f"official game {game_id} lacks one unambiguous team league: "
            f"away={away_league}, home={home_league}"
        )
    if away_sport is None or home_sport is None or away_sport != home_sport:
        raise ValueError(
            f"official game {game_id} lacks one unambiguous team sport: "
            f"away={away_sport}, home={home_sport}"
        )

    return OfficialGameLeagueIdentity(
        game_pk=int(game_id),
        game_date=official_date,
        game_type="R",
        league_id=int(away_league),
        sport_id=int(away_sport),
        away_team_id=int(away_team),
        home_team_id=int(home_team),
    )


def augment_game_league_map_with_official_identity(
    game_league_map: pl.DataFrame,
    identities: list[OfficialGameLeagueIdentity],
    *,
    expected_league_ids: frozenset[int],
    expected_sport_id: int,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Append exact official identities only for games absent from the same-game map."""

    required = {"game_pk", "league_id"}
    missing = sorted(required - set(game_league_map.columns))
    if missing:
        raise ValueError(f"same-game league map missing fields: {missing}")
    duplicate = game_league_map.group_by("game_pk").len().filter(pl.col("len") > 1)
    if not duplicate.is_empty():
        raise ValueError("same-game league map is not unique by game_pk")

    existing = {
        int(row["game_pk"]): int(row["league_id"])
        for row in game_league_map.select("game_pk", "league_id").iter_rows(named=True)
    }
    additions: list[dict[str, int]] = []
    accepted_games: list[int] = []
    for identity in identities:
        if identity.game_type != "R":
            raise ValueError(f"official fallback game {identity.game_pk} is not regular season")
        if identity.sport_id != int(expected_sport_id):
            raise ValueError(
                f"official fallback game {identity.game_pk} sport {identity.sport_id} "
                f"!= expected {expected_sport_id}"
            )
        if identity.league_id not in expected_league_ids:
            raise ValueError(
                f"official fallback game {identity.game_pk} league {identity.league_id} "
                f"outside expected {sorted(expected_league_ids)}"
            )
        if identity.game_pk in existing:
            if existing[identity.game_pk] != identity.league_id:
                raise ValueError(
                    f"official fallback league disagrees with existing same-game map for "
                    f"game {identity.game_pk}: {identity.league_id} vs {existing[identity.game_pk]}"
                )
            continue
        additions.append({"game_pk": identity.game_pk, "league_id": identity.league_id})
        accepted_games.append(identity.game_pk)
        existing[identity.game_pk] = identity.league_id

    if additions:
        addition_frame = pl.DataFrame(
            additions,
            schema={"game_pk": pl.Int64, "league_id": pl.Int64},
            strict=True,
        )
        augmented = pl.concat(
            [
                game_league_map.select(
                    pl.col("game_pk").cast(pl.Int64),
                    pl.col("league_id").cast(pl.Int64),
                ),
                addition_frame,
            ],
            how="vertical",
        ).sort("game_pk")
    else:
        augmented = game_league_map.select(
            pl.col("game_pk").cast(pl.Int64),
            pl.col("league_id").cast(pl.Int64),
        ).sort("game_pk")

    return augmented, {
        "official_exact_game_identity_added_count": len(accepted_games),
        "official_exact_game_identity_game_ids": accepted_games,
        "league_id_authority": "official_exact_game_team_league",
        "filename_level_used_as_league_identity": False,
    }
