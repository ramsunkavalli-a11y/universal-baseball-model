import polars as pl
import pytest

from universal_baseball.mlb_usage_window import (
    project_mlb_usage_date_range_payload,
)


def test_usage_window_aggregates_traded_player_splits() -> None:
    payload = {
        "stats": [
            {
                "totalSplits": 2,
                "splits": [
                    {
                        "player": {"id": 1},
                        "stat": {"plateAppearances": 10, "gamesPlayed": 3},
                    },
                    {
                        "player": {"id": 1},
                        "stat": {"plateAppearances": 8, "gamesPlayed": 2},
                    },
                ],
            }
        ]
    }
    result = project_mlb_usage_date_range_payload(payload, group="hitting")
    assert result.schema == {
        "player_id": pl.Int64,
        "workload": pl.Float64,
        "games": pl.Int64,
        "starts": pl.Int64,
    }
    assert result.row(0, named=True) == {
        "player_id": 1,
        "workload": 18.0,
        "games": 5,
        "starts": 0,
    }


def test_usage_window_rejects_partial_page() -> None:
    with pytest.raises(ValueError, match="missing or paginated"):
        project_mlb_usage_date_range_payload(
            {"stats": [{"totalSplits": 2, "splits": []}]}, group="pitching"
        )
