from datetime import date

import polars as pl

from universal_baseball.hitter_level_path_features import (
    add_level_path_features,
    build_level_path_features,
    build_terminal_level_evidence,
)


def test_terminal_level_uses_last_dated_contact_not_highest_level() -> None:
    contacts = pl.DataFrame(
        {
            "season": [2024, 2024],
            "game_pk": [1, 2],
            "at_bat_index": [3, 1],
            "player_id": [10, 10],
            "source_level": ["aaa", "aa"],
        }
    )
    games = pl.DataFrame(
        {
            "season": [2024, 2024],
            "game_pk": [1, 2],
            "game_date": [date(2024, 5, 1), date(2024, 8, 20)],
        }
    )

    result = build_terminal_level_evidence(contacts, games)

    assert result.item(0, "terminal_level_rank") == 4
    assert result.item(0, "terminal_contact_date") == date(2024, 8, 20)


def test_partial_promotion_return_differs_from_full_level_repeat() -> None:
    stats = pl.DataFrame(
        {
            "season": [2022, 2023, 2023, 2024, 2023, 2024],
            "player_id": [10, 10, 10, 10, 20, 20],
            "level_group": ["ROOKIE_COMPLEX", "SINGLE_A", "HIGH_A", "HIGH_A", "SINGLE_A", "SINGLE_A"],
            "plate_appearances": [400, 300, 40, 450, 400, 350],
        }
    )
    terminal = pl.DataFrame(
        {
            "season": [2022, 2023, 2024, 2023, 2024],
            "player_id": [10, 10, 10, 20, 20],
            "terminal_level_rank": [0, 3, 3, 2, 2],
        }
    )

    result = build_level_path_features(stats, terminal)
    promoted_return = result.filter(
        (pl.col("player_id") == 10) & (pl.col("season") == 2024)
    ).row(0, named=True)
    full_repeat = result.filter(
        (pl.col("player_id") == 20) & (pl.col("season") == 2024)
    ).row(0, named=True)

    assert promoted_return["level_path__returned_to_prior_terminal"] == 1
    assert promoted_return["level_path__returned_after_partial_promotion"] == 1
    assert promoted_return["level_path__same_primary_as_prior"] == 0
    assert promoted_return["level_path__prior_terminal_level_share"] == 40 / 340
    assert promoted_return["level_path__prior_seasons_at_primary"] == 1
    assert promoted_return["level_path__career_pa_at_primary"] == 490
    assert full_repeat["level_path__substantial_same_level_repeat"] == 1
    assert full_repeat["level_path__returned_after_partial_promotion"] == 0


def test_level_path_features_do_not_change_when_future_rows_change() -> None:
    through_2024 = pl.DataFrame(
        {
            "season": [2023, 2024],
            "player_id": [10, 10],
            "level_group": ["SINGLE_A", "HIGH_A"],
            "plate_appearances": [400, 350],
        }
    )
    with_future = pl.concat(
        [
            through_2024,
            pl.DataFrame(
                {
                    "season": [2025],
                    "player_id": [10],
                    "level_group": ["AAA"],
                    "plate_appearances": [600],
                }
            ),
        ]
    )

    expected = build_level_path_features(through_2024).filter(pl.col("season") == 2024)
    actual = build_level_path_features(with_future).filter(pl.col("season") == 2024)

    assert actual.equals(expected)


def test_add_level_path_features_joins_only_the_origin_season() -> None:
    panel = pl.DataFrame(
        {"origin_year": [2023, 2024], "player_id": [10, 10], "target_value": [1.0, 2.0]}
    )
    features = pl.DataFrame(
        {
            "season": [2023, 2024],
            "player_id": [10, 10],
            "level_path__seasons_at_primary": [1, 2],
        }
    )

    result = add_level_path_features(panel, features)

    assert result["level_path__seasons_at_primary"].to_list() == [1, 2]
