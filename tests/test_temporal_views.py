from __future__ import annotations

from datetime import UTC, date, datetime

import polars as pl
import pytest

from universal_baseball.temporal_views import (
    retrospective_event_cutoff,
    vintage_information_set,
)


def _observations() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "source_snapshot_id": ["a" * 64, "b" * 64, "c" * 64],
            "value": [10, 20, 30],
        }
    )


def _games() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "game_pk": [1, 2, 3],
            "official_date": [
                date(2023, 6, 1),
                date(2023, 6, 30),
                date(2023, 7, 1),
            ],
        }
    )


def test_retrospective_event_cutoff_uses_baseball_date_only() -> None:
    result = retrospective_event_cutoff(
        _observations(),
        _games(),
        cutoff=date(2023, 6, 30),
    )

    assert result.get_column("game_pk").to_list() == [1, 2]
    assert "official_date" not in result.columns


def test_event_cutoff_fails_if_game_date_is_unknown() -> None:
    games = _games().filter(pl.col("game_pk") != 2)
    with pytest.raises(ValueError, match="unknown game date"):
        retrospective_event_cutoff(
            _observations(),
            games,
            cutoff=date(2023, 6, 30),
        )


def test_vintage_information_set_requires_proven_historical_availability() -> None:
    snapshots = pl.DataFrame(
        {
            "source_snapshot_id": ["a" * 64, "b" * 64, "c" * 64],
            "knowledge_available_at_utc": [
                datetime(2023, 6, 2, tzinfo=UTC),
                None,
                datetime(2023, 7, 2, tzinfo=UTC),
            ],
        },
        schema={
            "source_snapshot_id": pl.String,
            "knowledge_available_at_utc": pl.Datetime(time_unit="us", time_zone="UTC"),
        },
    )

    result = vintage_information_set(
        _observations(),
        _games(),
        snapshots,
        cutoff=datetime(2023, 6, 30, 23, 59, tzinfo=UTC),
    )

    # Game 2 occurred by the cutoff, but its exact source representation has no
    # defensible historical availability timestamp, so it is excluded rather
    # than retroactively treated as an as-of snapshot.
    assert result.get_column("game_pk").to_list() == [1]


def test_vintage_cutoff_requires_utc() -> None:
    snapshots = pl.DataFrame(
        {
            "source_snapshot_id": ["a" * 64],
            "knowledge_available_at_utc": [datetime(2023, 6, 2, tzinfo=UTC)],
        }
    )
    with pytest.raises(ValueError, match="timezone-aware"):
        vintage_information_set(
            _observations().head(1),
            _games().head(1),
            snapshots,
            cutoff=datetime(2023, 6, 30),
        )
