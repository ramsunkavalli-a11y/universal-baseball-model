from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.authority_adjudication import (
    adjudicate_pitch_conflicts_with_official_pas,
)


LEFT = "a" * 64
RIGHT = "b" * 64


def _observation(
    snapshot: str,
    pitch_number: int,
    *,
    batter_side: str = "R",
    pitcher_hand: str = "R",
) -> dict[str, object]:
    return {
        "source_snapshot_id": snapshot,
        "game_pk": 10,
        "at_bat_index": 5,
        "pitch_number": pitch_number,
        "batter_side": batter_side,
        "pitcher_hand": pitcher_hand,
    }


def _conflicts(fields: list[str]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [10],
            "at_bat_index": [5],
            "pitch_number": [1],
            "conflict_fields": [fields],
        }
    )


def _official(*, batter_side: str | None = "R", pitcher_hand: str | None = "L") -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": ["10"],
            "at_bat_number": ["5"],
            "batter_side": [batter_side],
            "pitcher_hand": [pitcher_hand],
        },
        schema={
            "game_pk": pl.String,
            "at_bat_number": pl.String,
            "batter_side": pl.String,
            "pitcher_hand": pl.String,
        },
    )


def test_adjudication_is_sequence_level_and_can_match_one_snapshot() -> None:
    observations = pl.DataFrame(
        [
            _observation(LEFT, 1, pitcher_hand="R"),
            _observation(LEFT, 2, pitcher_hand="R"),
            _observation(RIGHT, 1, pitcher_hand="L"),
            _observation(RIGHT, 2, pitcher_hand="L"),
        ]
    )

    result = adjudicate_pitch_conflicts_with_official_pas(
        observations,
        _conflicts(["pitcher_hand"]),
        _official(pitcher_hand="L"),
    )
    row = result.to_dicts()[0]

    assert result.height == 1
    assert row["field"] == "pitcher_hand"
    assert row["official_value"] == "L"
    assert row["matching_source_snapshot_ids"] == [RIGHT]
    assert row["status"] == "official_matches_one_source_snapshot"


def test_adjudication_reports_official_unavailable_without_guessing() -> None:
    observations = pl.DataFrame(
        [
            _observation(LEFT, 1, batter_side="L"),
            _observation(RIGHT, 1, batter_side="R"),
        ]
    )
    official = _official().filter(pl.col("game_pk") == "999")

    row = adjudicate_pitch_conflicts_with_official_pas(
        observations,
        _conflicts(["batter_side"]),
        official,
    ).to_dicts()[0]

    assert row["official_sequence_available"] is False
    assert row["official_value"] is None
    assert row["matching_source_snapshot_ids"] == []
    assert row["status"] == "official_unavailable"


def test_adjudication_reports_within_snapshot_candidate_ambiguity() -> None:
    observations = pl.DataFrame(
        [
            _observation(LEFT, 1, pitcher_hand="R"),
            _observation(LEFT, 2, pitcher_hand="L"),
            _observation(RIGHT, 1, pitcher_hand="L"),
        ]
    )

    row = adjudicate_pitch_conflicts_with_official_pas(
        observations,
        _conflicts(["pitcher_hand"]),
        _official(pitcher_hand="L"),
    ).to_dicts()[0]

    assert row["ambiguous_source_snapshot_ids"] == [LEFT]
    assert row["status"] == "source_candidate_ambiguous"


def test_adjudication_rejects_unapproved_fields() -> None:
    observations = pl.DataFrame(
        [
            _observation(LEFT, 1),
            _observation(RIGHT, 1),
        ]
    )
    with pytest.raises(ValueError, match="unsupported"):
        adjudicate_pitch_conflicts_with_official_pas(
            observations,
            _conflicts(["release_speed"]),
            _official(),
            fields=["release_speed"],
        )
