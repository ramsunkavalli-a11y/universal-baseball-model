import polars as pl
import pytest

from universal_baseball.hitter_v2_historical_mlb_outcomes import (
    summarize_historical_mlb_terminal_outcomes,
)


def _rows(event: str, player: int, at_bat: int) -> dict[str, object]:
    return {
        "game_year": 2019,
        "game_pk": 1,
        "at_bat_index": at_bat,
        "pitch_number": 1,
        "league_id": 103,
        "batter_mlbam_id": player,
        "events": event,
        "is_plate_appearance_terminal": True,
        "pitch_result_code": "X",
        "result_description": "",
    }


def test_historical_mlb_outcomes_preserve_terminal_power() -> None:
    frame = pl.DataFrame(
        [
            _rows("home_run", 10, 1),
            _rows("double", 10, 2),
            _rows("field_out", 20, 3),
            _rows("walk", 20, 4),
            _rows("intent_walk", 20, 5),
        ]
    )
    result = summarize_historical_mlb_terminal_outcomes(frame).sort("player_id")
    assert result["HR"].to_list() == [1, 0]
    assert result["2B"].to_list() == [1, 0]
    assert result["UBB"].to_list() == [0, 1]
    assert result["IBB"].to_list() == [0, 1]
    assert result["hitter_talent_pa"].to_list() == [2, 2]
    assert result["terminal_pa"].to_list() == [2, 3]


def test_historical_mlb_outcomes_fail_closed_on_unknown_event() -> None:
    with pytest.raises(ValueError, match="unsupported historical MLB terminal"):
        summarize_historical_mlb_terminal_outcomes(
            pl.DataFrame([_rows("future_unknown_event", 10, 1)])
        )
