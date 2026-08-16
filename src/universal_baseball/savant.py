"""Thin Baseball Savant / Statcast CSV adapter for MLB Performance evidence.

Baseball Savant is the official MLB source. The query shape follows the mature
MIT-licensed pybaseball Statcast adapter rather than inventing a separate search
contract. We intentionally do not take a pandas/pybaseball runtime dependency:
exact CSV response bytes are retained by the caller and this module projects
only the small, explicitly typed surface needed by the universal Performance
layer.

Upstream references:
- Baseball Savant Statcast CSV documentation: https://baseballsavant.mlb.com/csv-docs
- pybaseball Statcast adapter: https://github.com/jldbc/pybaseball/blob/master/pybaseball/statcast.py
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import io
from urllib.parse import quote

import polars as pl
import requests


SAVANT_ROOT = "https://baseballsavant.mlb.com"
# Keep the mature pybaseball search surface, then apply our own explicit regular-
# season and field projection. This avoids relying on undocumented minimalist
# parameter combinations that may change behavior.
_SAVANT_DETAIL_TEMPLATE = (
    "/statcast_search/csv?all=true&hfPT=&hfAB=&hfBBT=&hfPR=&hfZ=&stadium="
    "&hfBBL=&hfNewZones=&hfGT=R%7CPO%7CS%7C=&hfSea=&hfSit="
    "&player_type=pitcher&hfOuts=&opponent=&pitcher_throws=&batter_stands="
    "&hfSA=&game_date_gt={start_date}&game_date_lt={end_date}&team={team}"
    "&position=&hfRO=&home_road=&hfFlag=&metric_1=&hfInn=&min_pitches=0"
    "&min_results=0&group_by=name&sort_col=pitches"
    "&player_event_sort=h_launch_speed&sort_order=desc&min_abs=0&type=details&"
)

SAVANT_PERFORMANCE_SCHEMA: dict[str, pl.DataType] = {
    "game_date": pl.String,
    "game_year": pl.Int64,
    "game_pk": pl.Int64,
    "at_bat_index": pl.Int64,
    "pitch_number": pl.Int64,
    "game_type": pl.String,
    "batter_mlbam_id": pl.Int64,
    "pitcher_mlbam_id": pl.Int64,
    "batter_side": pl.String,
    "pitcher_hand": pl.String,
    "events": pl.String,
    "pitch_description": pl.String,
    "result_description": pl.String,
    "pitch_result_code": pl.String,
    "bb_type": pl.String,
    "hit_location": pl.String,
    "hc_x": pl.Float64,
    "hc_y": pl.Float64,
    "home_team": pl.String,
    "away_team": pl.String,
    "is_terminal_event": pl.Boolean,
    "is_contact": pl.Boolean,
}


@dataclass(frozen=True)
class SavantCsvCapture:
    request_path: str
    response_bytes: bytes
    retrieved_url: str
    status_code: int


def savant_detail_request_path(
    start_date: date | str,
    end_date: date | str,
    *,
    team: str | None = None,
) -> str:
    """Return the stable Savant detail CSV request path used by pybaseball."""

    return _SAVANT_DETAIL_TEMPLATE.format(
        start_date=str(start_date),
        end_date=str(end_date),
        team=quote(team or ""),
    )


def fetch_savant_csv(
    start_date: date | str,
    end_date: date | str,
    *,
    team: str | None = None,
    session: requests.Session | None = None,
    timeout_seconds: int = 120,
) -> SavantCsvCapture:
    """Fetch exact Baseball Savant CSV bytes for a date range.

    The function intentionally returns exact response bytes rather than a parsed
    DataFrame so source-snapshot identity can be established before
    normalization. Caller-owned sessions are never closed.
    """

    path = savant_detail_request_path(start_date, end_date, team=team)
    owned = session is None
    active = session or requests.Session()
    try:
        response = active.get(SAVANT_ROOT + path, timeout=timeout_seconds)
        response.raise_for_status()
        return SavantCsvCapture(
            request_path=path,
            response_bytes=response.content,
            retrieved_url=response.url,
            status_code=int(response.status_code),
        )
    finally:
        if owned:
            active.close()


def read_savant_csv_bytes(content: bytes) -> pl.DataFrame:
    """Read Savant CSV losslessly enough for explicit downstream projection.

    All raw columns are initially strings so sparse/late values cannot drive
    inferred numeric types at the source boundary. Numeric meaning is applied
    only by :func:`project_savant_performance_rows`.
    """

    if not content.strip():
        return pl.DataFrame()
    return pl.read_csv(
        io.BytesIO(content),
        infer_schema=False,
        null_values=["", "null", "NA"],
        ignore_errors=False,
    )


def _integer_like(column: str, alias: str | None = None) -> pl.Expr:
    numeric = pl.col(column).cast(pl.Float64, strict=False)
    return (
        pl.when(numeric.is_not_null() & (numeric == numeric.floor()))
        .then(numeric.cast(pl.Int64, strict=False))
        .otherwise(None)
        .alias(alias or column)
    )


def _nonblank(column: str) -> pl.Expr:
    return pl.col(column).is_not_null() & (
        pl.col(column).cast(pl.String).str.strip_chars() != ""
    )


def project_savant_performance_rows(
    raw: pl.DataFrame,
    *,
    regular_season_only: bool = True,
) -> pl.DataFrame:
    """Project Savant pitches to the MLB Performance evidence surface."""

    required = {
        "game_date",
        "game_year",
        "game_pk",
        "at_bat_number",
        "pitch_number",
        "game_type",
        "batter",
        "pitcher",
        "stand",
        "p_throws",
        "events",
        "description",
        "des",
        "type",
        "bb_type",
        "hit_location",
        "hc_x",
        "hc_y",
        "home_team",
        "away_team",
    }
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Savant CSV missing Performance fields: {missing}")
    if raw.is_empty():
        return pl.DataFrame(schema=SAVANT_PERFORMANCE_SCHEMA)

    contact = (
        (pl.col("type").cast(pl.String).str.strip_chars().str.to_uppercase() == "X")
        | _nonblank("bb_type")
        | _nonblank("hc_x")
        | _nonblank("hc_y")
    )
    projected = raw.select(
        pl.col("game_date").cast(pl.String),
        _integer_like("game_year"),
        _integer_like("game_pk"),
        _integer_like("at_bat_number", "at_bat_index"),
        _integer_like("pitch_number"),
        pl.col("game_type").cast(pl.String),
        _integer_like("batter", "batter_mlbam_id"),
        _integer_like("pitcher", "pitcher_mlbam_id"),
        pl.col("stand").cast(pl.String).alias("batter_side"),
        pl.col("p_throws").cast(pl.String).alias("pitcher_hand"),
        pl.col("events").cast(pl.String),
        pl.col("description").cast(pl.String).alias("pitch_description"),
        pl.col("des").cast(pl.String).alias("result_description"),
        pl.col("type").cast(pl.String).alias("pitch_result_code"),
        pl.col("bb_type").cast(pl.String),
        pl.col("hit_location").cast(pl.String),
        pl.col("hc_x").cast(pl.Float64, strict=False),
        pl.col("hc_y").cast(pl.Float64, strict=False),
        pl.col("home_team").cast(pl.String),
        pl.col("away_team").cast(pl.String),
        _nonblank("events").alias("is_terminal_event"),
        contact.alias("is_contact"),
    ).drop_nulls(["game_pk", "at_bat_index", "pitch_number"])

    if regular_season_only:
        projected = projected.filter(pl.col("game_type") == "R")
    return (
        projected.cast(SAVANT_PERFORMANCE_SCHEMA, strict=True)
        .sort(["game_date", "game_pk", "at_bat_index", "pitch_number"])
    )
