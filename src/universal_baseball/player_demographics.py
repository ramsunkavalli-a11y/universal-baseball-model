"""Objective player demographics from official StatsAPI people records."""

from __future__ import annotations

from datetime import date
import re
from typing import Any

import polars as pl


DEMOGRAPHIC_SCHEMA: dict[str, pl.DataType] = {
    "player_id": pl.Int64,
    "birth_date": pl.Date,
    "birth_city": pl.String,
    "birth_state_province": pl.String,
    "birth_country": pl.String,
    "height_inches": pl.Float64,
    "weight_pounds": pl.Float64,
    "bat_side": pl.String,
    "pitch_hand": pl.String,
    "primary_position_code": pl.String,
    "strike_zone_top": pl.Float64,
    "strike_zone_bottom": pl.Float64,
    "gender": pl.String,
}

_HEIGHT = re.compile(r"^\s*(\d+)\s*'\s*(\d+)\s*\"?\s*$")

# StatsAPI currently mixes display names and legacy three-letter baseball codes.
# Keep the reported value in the source table, but use this canonical form in
# downstream grouping so one country cannot silently become two model features.
_BIRTH_COUNTRY_ALIASES = {
    "BAH": "Bahamas",
    "CAN": "Canada",
    "COL": "Colombia",
    "CUB": "Cuba",
    "CUW": "Curacao",
    "DOM": "Dominican Republic",
    "ESP": "Spain",
    "HKG": "Hong Kong",
    "KUW": "Kuwait",
    "MEX": "Mexico",
    "NCA": "Nicaragua",
    "PAN": "Panama",
    "PUR": "Puerto Rico",
    "Republic of Korea": "South Korea",
    "United States of America": "USA",
    "VEN": "Venezuela",
}


def normalize_birth_country(value: object) -> str:
    """Return a stable country group without changing the reported source field."""

    if value is None:
        return "UNKNOWN"
    reported = str(value).strip()
    if not reported:
        return "UNKNOWN"
    return _BIRTH_COUNTRY_ALIASES.get(reported, reported)


def parse_height_inches(value: object) -> float | None:
    if value in (None, ""):
        return None
    match = _HEIGHT.match(str(value))
    if match is None:
        raise ValueError(f"unsupported StatsAPI height: {value!r}")
    feet, inches = map(int, match.groups())
    if feet == 0 and inches == 0:
        return None
    if feet < 4 or feet > 8 or inches > 11:
        raise ValueError(f"invalid StatsAPI height: {value!r}")
    return float(feet * 12 + inches)


def _date(value: object) -> date | None:
    return None if value in (None, "") else date.fromisoformat(str(value))


def project_people_demographics(payload: dict[str, Any]) -> pl.DataFrame:
    """Project only reported fields; never infer missing demographics."""

    people = payload.get("people")
    if not isinstance(people, list):
        raise ValueError("StatsAPI people response missing people list")
    rows: list[dict[str, object]] = []
    for person in people:
        if not isinstance(person, dict) or person.get("id") is None:
            raise ValueError("StatsAPI people row missing identity")
        rows.append(
            {
                "player_id": int(person["id"]),
                "birth_date": _date(person.get("birthDate")),
                "birth_city": person.get("birthCity"),
                "birth_state_province": person.get("birthStateProvince"),
                "birth_country": person.get("birthCountry"),
                "height_inches": parse_height_inches(person.get("height")),
                "weight_pounds": person.get("weight"),
                "bat_side": (person.get("batSide") or {}).get("code"),
                "pitch_hand": (person.get("pitchHand") or {}).get("code"),
                "primary_position_code": (
                    person.get("primaryPosition") or {}
                ).get("code"),
                "strike_zone_top": person.get("strikeZoneTop"),
                "strike_zone_bottom": person.get("strikeZoneBottom"),
                "gender": person.get("gender"),
            }
        )
    frame = pl.DataFrame(rows, schema=DEMOGRAPHIC_SCHEMA)
    if frame.group_by("player_id").len().filter(pl.col("len") != 1).height:
        raise ValueError("StatsAPI people response has duplicate identities")
    return frame.sort("player_id")
