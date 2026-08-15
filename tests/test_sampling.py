from __future__ import annotations

import polars as pl

from universal_baseball.sampling import select_game_ids_by_group


def test_grouped_sampling_selects_games_from_each_observed_league() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "2", "3", "4", "5", "6"],
            "game_date": [
                "2024-06-01",
                "2024-06-02",
                "2024-06-03",
                "2024-06-04",
                "2024-06-05",
                "2024-06-06",
            ],
            "league_name": ["DSL", "DSL", "ACL", "ACL", "FCL", "FCL"],
        }
    )

    result = select_game_ids_by_group(frame, "league_name", per_group=1)

    assert result == {"ACL": [3], "DSL": [1], "FCL": [5]}


def test_grouped_sampling_ignores_blank_group_labels() -> None:
    frame = pl.DataFrame(
        {
            "game_pk": ["1", "2", "3"],
            "game_date": ["2024-06-01", "2024-06-02", "2024-06-03"],
            "league_name": ["DSL", None, ""],
        }
    )

    assert select_game_ids_by_group(frame, "league_name") == {"DSL": [1]}
