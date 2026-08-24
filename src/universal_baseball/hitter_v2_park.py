"""Chronology-safe official venue context for Hitter v2."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import polars as pl


def _integer(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def project_schedule_venues(
    payload: Mapping[str, Any],
    *,
    season: int,
    sport_id: int,
) -> pl.DataFrame:
    """Project regular-season official schedule rows to game/venue context."""

    rows: list[dict[str, object]] = []
    for date_row in payload.get("dates") or []:
        for game in date_row.get("games") or []:
            if str(game.get("gameType") or "") != "R":
                continue
            status = game.get("status") or {}
            if str(status.get("codedGameState") or "") != "F":
                continue
            venue = game.get("venue") or {}
            teams = game.get("teams") or {}
            away = (teams.get("away") or {}).get("team") or {}
            home = (teams.get("home") or {}).get("team") or {}
            game_id = _integer(game.get("gamePk"))
            venue_id = _integer(venue.get("id"))
            away_team_id = _integer(away.get("id"))
            home_team_id = _integer(home.get("id"))
            official_date = str(game.get("officialDate") or date_row.get("date") or "")
            complete = all(
                value is not None
                for value in (game_id, venue_id, away_team_id, home_team_id)
            ) and bool(official_date and venue.get("name"))
            rows.append(
                {
                    "season": int(season),
                    "sport_id": int(sport_id),
                    "game_id": game_id,
                    "official_date": official_date or None,
                    "venue_id": venue_id,
                    "venue_name": str(venue.get("name") or "") or None,
                    "away_team_id": away_team_id,
                    "home_team_id": home_team_id,
                    "venue_source_status": (
                        "accepted_official_schedule_venue"
                        if complete
                        else "failed_closed_incomplete_schedule_venue"
                    ),
                }
            )
    if not rows:
        raise ValueError(
            f"official schedule returned no regular-season games for {season}/{sport_id}"
        )
    return pl.DataFrame(rows).with_columns(
        pl.col("season", "sport_id", "game_id", "venue_id", "away_team_id", "home_team_id")
        .cast(pl.Int64, strict=False),
        pl.col("official_date", "venue_name", "venue_source_status").cast(pl.String),
    )


def resolve_schedule_venue_duplicates(schedule: pl.DataFrame) -> pl.DataFrame:
    """Resolve duplicate sport responses, failing closed on material conflicts."""

    required = {
        "season",
        "sport_id",
        "game_id",
        "official_date",
        "venue_id",
        "venue_name",
        "away_team_id",
        "home_team_id",
        "venue_source_status",
    }
    missing = sorted(required - set(schedule.columns))
    if missing:
        raise ValueError(f"schedule venue table missing fields: {missing}")
    return (
        schedule.drop_nulls("game_id")
        .group_by(["season", "game_id"])
        .agg(
            pl.col("sport_id").n_unique().alias("sport_variant_count"),
            pl.col("sport_id").first().alias("sport_id"),
            pl.col("official_date").n_unique().alias("date_variant_count"),
            pl.col("official_date").first().alias("official_date"),
            pl.col("venue_id").drop_nulls().n_unique().alias("venue_variant_count"),
            pl.col("venue_id").drop_nulls().first().alias("venue_id"),
            pl.col("venue_name").drop_nulls().n_unique().alias("venue_name_variant_count"),
            pl.col("venue_name").drop_nulls().first().alias("venue_name"),
            pl.col("away_team_id").drop_nulls().n_unique().alias("away_variant_count"),
            pl.col("away_team_id").drop_nulls().first().alias("away_team_id"),
            pl.col("home_team_id").drop_nulls().n_unique().alias("home_variant_count"),
            pl.col("home_team_id").drop_nulls().first().alias("home_team_id"),
            pl.len().alias("raw_schedule_row_count"),
        )
        .with_columns(
            (
                (pl.col("venue_variant_count") == 1)
                & (pl.col("venue_name_variant_count") == 1)
                & (pl.col("away_variant_count") == 1)
                & (pl.col("home_variant_count") == 1)
            ).alias("venue_context_eligible")
        )
        .with_columns(
            pl.when(pl.col("venue_context_eligible"))
            .then(pl.lit("accepted_unique_official_schedule_venue"))
            .otherwise(pl.lit("failed_closed_schedule_venue_conflict_or_missing"))
            .alias("venue_source_status")
        )
        .select(
            "season",
            "game_id",
            "sport_id",
            "official_date",
            "venue_id",
            "venue_name",
            "away_team_id",
            "home_team_id",
            "venue_context_eligible",
            "venue_source_status",
            "raw_schedule_row_count",
            "date_variant_count",
            "venue_variant_count",
            "venue_name_variant_count",
            "away_variant_count",
            "home_variant_count",
        )
        .sort(["season", "game_id"])
    )
