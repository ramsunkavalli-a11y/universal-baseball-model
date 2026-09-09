from datetime import date

import polars as pl
import pytest

from universal_baseball.player_demographics import (
    normalize_birth_country,
    parse_height_inches,
    project_people_demographics,
)


def test_project_people_demographics_keeps_reported_fields() -> None:
    result = project_people_demographics(
        {
            "people": [
                {
                    "id": 10,
                    "birthDate": "2001-02-03",
                    "birthCity": "City",
                    "birthCountry": "Country",
                    "height": "6' 2\"",
                    "weight": 205,
                    "batSide": {"code": "L"},
                    "pitchHand": {"code": "R"},
                    "primaryPosition": {"code": "6"},
                    "strikeZoneTop": 3.4,
                    "strikeZoneBottom": 1.6,
                    "gender": "M",
                }
            ]
        }
    )
    assert result.item(0, "birth_date") == date(2001, 2, 3)
    assert result.item(0, "height_inches") == 74.0
    assert result.item(0, "bat_side") == "L"
    assert result.schema["weight_pounds"] == pl.Float64


def test_height_parser_fails_closed() -> None:
    assert parse_height_inches(None) is None
    assert parse_height_inches("0' 0\"") is None
    with pytest.raises(ValueError, match="unsupported"):
        parse_height_inches("unknown")


@pytest.mark.parametrize(
    ("reported", "expected"),
    [
        ("VEN", "Venezuela"),
        ("DOM", "Dominican Republic"),
        ("MEX", "Mexico"),
        ("Republic of Korea", "South Korea"),
        ("United States of America", "USA"),
        ("Curacao", "Curacao"),
        (None, "UNKNOWN"),
    ],
)
def test_birth_country_normalization_preserves_canonical_group(
    reported: object, expected: str
) -> None:
    assert normalize_birth_country(reported) == expected
