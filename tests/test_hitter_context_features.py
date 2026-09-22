import polars as pl
import pytest

from universal_baseball.hitter_context_features import (
    CONTEXT_COLUMNS,
    add_context_history,
)


def _context_row(season: int, player_id: int, value: float) -> dict[str, object]:
    row: dict[str, object] = {"season": season, "player_id": player_id}
    row.update({column: value for column in CONTEXT_COLUMNS})
    return row


def test_context_history_uses_exact_calendar_lags_and_missing_flags() -> None:
    panel = pl.DataFrame(
        {"origin_year": [2021, 2022], "player_id": [1, 1], "feature": [4, 5]}
    )
    context = pl.DataFrame([_context_row(2021, 1, 0.25)])
    result = add_context_history(panel, context)
    assert result["lag0__context__available"].to_list() == [1, 0]
    assert result["lag1__context__available"].to_list() == [0, 1]
    assert result["lag1__context__park_effect__hr"].to_list() == [None, 0.25]


def test_context_rejects_duplicate_player_seasons() -> None:
    panel = pl.DataFrame({"origin_year": [2021], "player_id": [1]})
    context = pl.DataFrame([_context_row(2021, 1, 0.1)] * 2)
    with pytest.raises(ValueError, match="unique"):
        add_context_history(panel, context)
