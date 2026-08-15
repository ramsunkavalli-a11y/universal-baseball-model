from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.game_observation import (
    normalize_armstjc_game_observations,
    normalize_level_name,
    validate_unique_resolved_game_metadata,
)


SNAPSHOT = "a" * 64
NORMALIZATION = "b" * 64


def test_level_normalization_is_conservative_and_preserves_unknown_labels() -> None:
    assert normalize_level_name("Triple-A") == "AAA"
    assert normalize_level_name("Double-A") == "AA"
    assert normalize_level_name("High-A") == "A+"
    assert normalize_level_name("Single-A") == "A"
    assert normalize_level_name("Rookie") == "Rookie"
    assert normalize_level_name("Short-Season A") == "A-"
    assert normalize_level_name("Historical Oddball Class") == "Historical Oddball Class"


def test_armstjc_game_adapter_collapses_repeated_pitch_row_metadata() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": ["10", "10", "10"],
            "game_date": ["2023-08-05"] * 3,
            "game_year": ["2023"] * 3,
            "game_type": ["R"] * 3,
            "league_id": ["121"] * 3,
            "league_name": ["Arizona Complex League"] * 3,
            "league_level_id": ["16"] * 3,
            "league_level_name": ["Rookie"] * 3,
            "home_team": ["ACL A"] * 3,
            "away_team": ["ACL B"] * 3,
            "home_team_org_id": ["100"] * 3,
            "home_team_org_name": ["Org A"] * 3,
            "away_team_org_id": ["200"] * 3,
            "away_team_org_name": ["Org B"] * 3,
        }
    )

    result = normalize_armstjc_game_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    assert result.height == 1
    row = result.to_dicts()[0]
    assert row["evidence_row_count"] == 3
    assert str(row["official_date"]) == "2023-08-05"
    assert row["season"] == 2023
    assert row["normalized_level"] == "Rookie"
    validate_unique_resolved_game_metadata(result)


def test_armstjc_game_adapter_handles_known_2023_leauge_alias() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": ["11"],
            "game_date": ["2023-08-06"],
            "game_year": ["2023"],
            "leauge_id": ["130"],
            "leauge_name": ["Dominican Summer League"],
            "league_level_id": ["16"],
            "league_level_name": ["Rookie"],
        }
    )

    result = normalize_armstjc_game_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    row = result.to_dicts()[0]
    assert row["league_id"] == 130
    assert row["league_name"] == "Dominican Summer League"
    assert row["normalized_level"] == "Rookie"


def test_game_adapter_preserves_conflicting_metadata_variants() -> None:
    raw = pl.DataFrame(
        {
            "game_pk": ["12", "12"],
            "game_date": ["2023-08-07", "2023-08-07"],
            "game_year": ["2023", "2023"],
            "league_name": ["League A", "League B"],
            "league_level_name": ["Double-A", "Double-A"],
        }
    )

    result = normalize_armstjc_game_observations(
        raw,
        source_snapshot_id=SNAPSHOT,
        normalization_id=NORMALIZATION,
    )

    assert result.height == 2
    assert result.get_column("payload_hash").n_unique() == 2
    with pytest.raises(ValueError, match="conflicting game payload"):
        validate_unique_resolved_game_metadata(result)
