"""Canonical game-grain observations and reusable-source adapter."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import polars as pl

from universal_baseball.armstjc_schema import normalize_known_schema_aliases
from universal_baseball.canonical_adapters import stable_payload_hash


GAME_OBSERVATION_SCHEMA: dict[str, pl.DataType] = {
    "normalization_id": pl.String,
    "source_snapshot_id": pl.String,
    "game_pk": pl.Int64,
    "payload_hash": pl.String,
    "evidence_row_count": pl.Int64,
    "official_date": pl.Date,
    "season": pl.Int64,
    "game_type": pl.String,
    "league_id": pl.Int64,
    "league_name": pl.String,
    "level_id": pl.Int64,
    "level_name": pl.String,
    "normalized_level": pl.String,
    "home_team": pl.String,
    "away_team": pl.String,
    "home_parent_org_id": pl.Int64,
    "home_parent_org_name": pl.String,
    "away_parent_org_id": pl.Int64,
    "away_parent_org_name": pl.String,
}
_HEX64_PATTERN = r"^[0-9a-f]{64}$"

_LEVEL_ALIASES = {
    "major league baseball": "MLB",
    "major league": "MLB",
    "triple-a": "AAA",
    "triple a": "AAA",
    "double-a": "AA",
    "double a": "AA",
    "high-a": "A+",
    "high a": "A+",
    "class a advanced": "A+",
    "a advanced": "A+",
    "single-a": "A",
    "single a": "A",
    "class a": "A",
    "low-a": "A",
    "low a": "A",
    "short-season a": "A-",
    "short season a": "A-",
    "a short season": "A-",
    "rookie": "Rookie",
}


def normalize_level_name(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return _LEVEL_ALIASES.get(text.lower(), text)


def _text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _date(value: Any) -> date | None:
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def validate_game_observation(frame: pl.DataFrame) -> pl.DataFrame:
    missing = sorted(
        {"normalization_id", "source_snapshot_id", "game_pk", "payload_hash", "evidence_row_count", "official_date"}
        - set(frame.columns)
    )
    if missing:
        raise ValueError(f"game_observation missing required columns: {missing}")
    extra = sorted(set(frame.columns) - set(GAME_OBSERVATION_SCHEMA))
    if extra:
        raise ValueError(f"game_observation has undeclared columns: {extra}")

    result = frame
    for column, dtype in GAME_OBSERVATION_SCHEMA.items():
        if column not in result.columns:
            result = result.with_columns(pl.lit(None, dtype=dtype).alias(column))
    result = result.select(list(GAME_OBSERVATION_SCHEMA)).cast(
        GAME_OBSERVATION_SCHEMA, strict=True
    )

    required = [
        "normalization_id",
        "source_snapshot_id",
        "game_pk",
        "payload_hash",
        "evidence_row_count",
        "official_date",
    ]
    if not result.filter(
        pl.any_horizontal([pl.col(column).is_null() for column in required])
    ).is_empty():
        raise ValueError("game_observation contains null required values")
    for column in ("normalization_id", "source_snapshot_id", "payload_hash"):
        if not result.filter(~pl.col(column).str.contains(_HEX64_PATTERN)).is_empty():
            raise ValueError(f"game_observation contains invalid {column}")
    if not result.filter(pl.col("evidence_row_count") < 1).is_empty():
        raise ValueError("game_observation evidence_row_count must be >= 1")
    duplicates = (
        result.group_by(["normalization_id", "game_pk", "payload_hash"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not duplicates.is_empty():
        raise ValueError("game_observation contains duplicate observation keys")
    wrong_season = result.filter(
        pl.col("season").is_not_null()
        & (pl.col("season") != pl.col("official_date").dt.year())
    )
    if not wrong_season.is_empty():
        raise ValueError("game_observation season disagrees with official_date")
    return result


def normalize_armstjc_game_observations(
    frame: pl.DataFrame,
    *,
    source_snapshot_id: str,
    normalization_id: str,
) -> pl.DataFrame:
    """Project repeated pitch-row game metadata into immutable game observations.

    A single source asset repeats game metadata on every pitch. We count those
    supporting rows but hash only the game-grain metadata projection. If metadata
    differs within one game, multiple payload variants survive rather than an
    arbitrary row winning.
    """

    standardized, _ = normalize_known_schema_aliases(frame)
    required = {"game_pk", "game_date"}
    missing = sorted(required - set(standardized.columns))
    if missing:
        raise ValueError(f"armstjc game metadata missing columns: {missing}")

    rows_by_payload: dict[tuple[int, str], dict[str, Any]] = {}
    for raw in standardized.to_dicts():
        game_pk = _int(raw.get("game_pk"))
        official_date = _date(raw.get("game_date"))
        if game_pk is None or official_date is None:
            raise ValueError("armstjc row has invalid game_pk/game_date")
        level_name = _text(raw.get("league_level_name"))
        payload = {
            "official_date": official_date.isoformat(),
            "season": _int(raw.get("game_year")) or official_date.year,
            "game_type": _text(raw.get("game_type")),
            "league_id": _int(raw.get("league_id")),
            "league_name": _text(raw.get("league_name")),
            "level_id": _int(raw.get("league_level_id")),
            "level_name": level_name,
            "normalized_level": normalize_level_name(level_name),
            "home_team": _text(raw.get("home_team")),
            "away_team": _text(raw.get("away_team")),
            "home_parent_org_id": _int(raw.get("home_team_org_id")),
            "home_parent_org_name": _text(raw.get("home_team_org_name")),
            "away_parent_org_id": _int(raw.get("away_team_org_id")),
            "away_parent_org_name": _text(raw.get("away_team_org_name")),
        }
        payload_hash = stable_payload_hash(payload)
        key = (game_pk, payload_hash)
        if key in rows_by_payload:
            rows_by_payload[key]["evidence_row_count"] += 1
            continue
        rows_by_payload[key] = {
            "normalization_id": normalization_id,
            "source_snapshot_id": source_snapshot_id,
            "game_pk": game_pk,
            "payload_hash": payload_hash,
            "evidence_row_count": 1,
            "official_date": official_date,
            **{key_name: value for key_name, value in payload.items() if key_name != "official_date"},
        }

    if not rows_by_payload:
        raise ValueError("armstjc game adapter received no rows")
    return validate_game_observation(pl.DataFrame(list(rows_by_payload.values())))


def validate_unique_resolved_game_metadata(frame: pl.DataFrame) -> None:
    """Fail when a source normalization has multiple metadata payloads per game."""

    validated = validate_game_observation(frame)
    conflicts = (
        validated.group_by(["normalization_id", "game_pk"])
        .len()
        .filter(pl.col("len") > 1)
    )
    if not conflicts.is_empty():
        raise ValueError(
            f"game metadata contains {conflicts.height} conflicting game payload groups"
        )
