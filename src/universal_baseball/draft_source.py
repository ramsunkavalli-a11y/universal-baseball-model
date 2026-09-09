"""Official StatsAPI Rule 4 draft evidence."""

from __future__ import annotations

from typing import Any

import polars as pl
import requests


STATS_API_DRAFT_URL = "https://statsapi.mlb.com/api/v1/draft/{year}"

DRAFT_SCHEMA: dict[str, pl.DataType] = {
    "draft_year": pl.Int64,
    "player_id": pl.Int64,
    "player_name": pl.String,
    "pick_number": pl.Int64,
    "round_pick_number": pl.Int64,
    "pick_round": pl.String,
    "pick_value_dollars": pl.Int64,
    "signing_bonus_dollars": pl.Int64,
    "school_class": pl.String,
    "drafted": pl.Boolean,
    "source_snapshot_id": pl.String,
}


def _integer(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(str(value).replace(",", ""))


def project_draft_payload(
    payload: dict[str, Any], *, draft_year: int, source_snapshot_id: str
) -> pl.DataFrame:
    """Project one draft response without using its narrative scouting text."""

    draft = payload.get("drafts")
    if not isinstance(draft, dict):
        raise ValueError("StatsAPI draft response missing drafts object")
    rounds = draft.get("rounds")
    if not isinstance(rounds, list):
        raise ValueError("StatsAPI draft response missing rounds")
    rows: list[dict[str, object]] = []
    for round_data in rounds:
        if not isinstance(round_data, dict):
            raise ValueError("StatsAPI draft round must be an object")
        for pick in round_data.get("picks") or []:
            person = pick.get("person") or {}
            if person.get("id") is None or pick.get("pickNumber") is None:
                continue
            school = pick.get("school") or {}
            rows.append(
                {
                    "draft_year": int(pick.get("year") or draft_year),
                    "player_id": int(person["id"]),
                    "player_name": str(person.get("fullName") or ""),
                    "pick_number": _integer(pick.get("pickNumber")),
                    "round_pick_number": _integer(pick.get("roundPickNumber")),
                    "pick_round": str(pick.get("pickRound") or ""),
                    "pick_value_dollars": _integer(pick.get("pickValue")),
                    "signing_bonus_dollars": _integer(pick.get("signingBonus")),
                    "school_class": str(school.get("schoolClass") or ""),
                    "drafted": bool(pick.get("isDrafted", True)),
                    "source_snapshot_id": source_snapshot_id,
                }
            )
    result = pl.DataFrame(rows, schema=DRAFT_SCHEMA)
    if not result.is_empty():
        result = result.sort(["player_id", "draft_year", "pick_number"])
    return result


def fetch_draft_year(
    draft_year: int, *, session: requests.Session | None = None
) -> tuple[pl.DataFrame, dict[str, Any], str]:
    """Fetch and project one complete Rule 4 draft."""

    if not 1965 <= draft_year <= 2100:
        raise ValueError("draft_year is outside the Rule 4 era")
    own_session = session is None
    http = session or requests.Session()
    try:
        response = http.get(STATS_API_DRAFT_URL.format(year=draft_year), timeout=60)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("StatsAPI draft response must be an object")
        snapshot_id = f"statsapi:draft:{draft_year}"
        return (
            project_draft_payload(
                payload, draft_year=draft_year, source_snapshot_id=snapshot_id
            ),
            payload,
            response.url,
        )
    finally:
        if own_session:
            http.close()


def draft_pedigree_as_of(history: pl.DataFrame, snapshot_year: int) -> pl.DataFrame:
    """Return era-neutral structured draft evidence known by a year-end cutoff."""

    required = {
        "draft_year", "player_id", "pick_number", "signing_bonus_dollars",
        "school_class", "drafted",
    }
    if missing := sorted(required - set(history.columns)):
        raise ValueError(f"draft history missing columns: {missing}")
    eligible = history.filter(
        (pl.col("draft_year") <= snapshot_year) & pl.col("drafted")
    )
    if eligible.is_empty():
        return pl.DataFrame(
            schema={
                "player_id": pl.Int64, "rule4_drafted": pl.Boolean,
                "draft_pick_quality": pl.Float64,
                "signing_bonus_percentile": pl.Float64,
                "signing_bonus_known": pl.Boolean,
                "high_school_draftee": pl.Boolean,
            }
        )
    max_pick = eligible.group_by("draft_year").agg(
        pl.col("pick_number").max().alias("year_max_pick")
    )
    ranked_bonus = eligible.with_columns(
        pl.col("signing_bonus_dollars")
        .rank(method="average")
        .over("draft_year")
        .alias("bonus_rank"),
        pl.col("signing_bonus_dollars").count().over("draft_year").alias("bonus_n"),
    )
    return (
        ranked_bonus.join(max_pick, on="draft_year", how="left")
        .with_columns(
            (
                1.0
                - pl.col("pick_number").cast(pl.Float64).log()
                / pl.col("year_max_pick").cast(pl.Float64).log()
            ).clip(0.0, 1.0).alias("draft_pick_quality"),
            pl.when(pl.col("signing_bonus_dollars").is_not_null())
            .then(
                pl.when(pl.col("bonus_n") <= 1).then(0.5)
                .otherwise((pl.col("bonus_rank") - 1.0) / (pl.col("bonus_n") - 1.0))
            )
            .otherwise(None)
            .alias("signing_bonus_percentile"),
        )
        .sort(["player_id", "draft_year", "pick_number"])
        .group_by("player_id", maintain_order=True)
        .last()
        .select(
            "player_id",
            pl.lit(True).alias("rule4_drafted"),
            "draft_pick_quality",
            "signing_bonus_percentile",
            pl.col("signing_bonus_dollars").is_not_null().alias("signing_bonus_known"),
            pl.col("school_class").str.contains("HS").alias("high_school_draftee"),
        )
        .sort("player_id")
    )
