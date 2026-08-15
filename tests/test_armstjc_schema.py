from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.armstjc_schema import normalize_known_schema_aliases


def test_old_leauge_columns_are_renamed_in_standardized_view() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1"],
            "leauge_id": ["130"],
            "leauge_name": ["Dominican Summer League"],
        }
    )

    result, report = normalize_known_schema_aliases(frame)

    assert "leauge_id" not in result.columns
    assert "leauge_name" not in result.columns
    assert result.get_column("league_id").to_list() == ["130"]
    assert result.get_column("league_name").to_list() == ["Dominican Summer League"]
    assert report["action_count"] == 2


def test_coexisting_aliases_are_coalesced_when_values_do_not_conflict() -> None:
    frame = pl.DataFrame(
        {
            "league_name": [None, "Florida Complex League"],
            "leauge_name": ["Dominican Summer League", "Florida Complex League"],
        }
    )

    result, report = normalize_known_schema_aliases(frame)

    assert result.get_column("league_name").to_list() == [
        "Dominican Summer League",
        "Florida Complex League",
    ]
    assert "leauge_name" not in result.columns
    assert report["actions"][0]["action"] == "coalesced_and_dropped_alias"


def test_coexisting_aliases_fail_on_disagreement() -> None:
    frame = pl.DataFrame(
        {
            "league_name": ["Florida Complex League"],
            "leauge_name": ["Dominican Summer League"],
        }
    )

    with pytest.raises(ValueError, match="disagree"):
        normalize_known_schema_aliases(frame)
