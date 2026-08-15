from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from universal_baseball.historical_materialization import write_event_table_by_game_month


def test_partitioning_uses_resolved_game_date_without_adding_date_to_rows(tmp_path) -> None:
    frame = pl.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "value": ["a", "b", "c"],
        }
    )
    games = pl.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "official_date": [
                date(2025, 3, 31),
                date(2025, 4, 1),
                date(2025, 4, 23),
            ],
        }
    )

    artifacts = write_event_table_by_game_month(
        frame,
        games,
        tmp_path / "events",
        table_name="test_events",
    )

    assert len(artifacts) == 2
    march = pl.read_parquet(tmp_path / "events/year=2025/month=03/part-00000.parquet")
    april = pl.read_parquet(tmp_path / "events/year=2025/month=04/part-00000.parquet")
    assert march.get_column("game_pk").to_list() == [1]
    assert sorted(april.get_column("game_pk").to_list()) == [2, 3]
    assert "official_date" not in march.columns
    assert "official_date" not in april.columns


def test_partitioning_fails_when_game_date_is_unresolved(tmp_path) -> None:
    frame = pl.DataFrame({"game_pk": [1], "value": ["a"]})
    games = pl.DataFrame(
        {"game_pk": [1], "official_date": [None]},
        schema={"game_pk": pl.Int64, "official_date": pl.Date},
    )

    with pytest.raises(ValueError, match="without resolved official_date"):
        write_event_table_by_game_month(
            frame,
            games,
            tmp_path / "events",
            table_name="test_events",
        )
