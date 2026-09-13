from __future__ import annotations

import polars as pl

from universal_baseball.historical_hitter_position import (
    origin_position_profiles,
    position_war_by_player_origin,
)
from universal_baseball.player_value_positional_adjustment import (
    FULL_SEASON_DEFENSIVE_OUTS,
)


def test_position_war_uses_outs_dh_starts_and_shortened_season_scale() -> None:
    fielding = pl.DataFrame(
        {
            "season": [2019, 2019, 2020, 2020, 2019],
            "player_id": [1, 1, 2, 2, 3],
            "position_abbreviation": ["SS", "DH", "CF", "DH", "P"],
            "games_started": [162, 10, 0, 10, 20],
            "fielding_outs": [int(FULL_SEASON_DEFENSIVE_OUTS), 0, 540, 0, 540],
        }
    )

    result = position_war_by_player_origin(
        fielding, origin=2018, horizon=2, runs_per_win=10.0
    )

    rows = {row["player_id"]: row for row in result.iter_rows(named=True)}
    assert abs(rows[1]["later_position_runs"] - (7.5 - 17.5 * 10 / 162)) < 1e-9
    assert abs(
        rows[2]["later_position_runs"]
        - (2.5 * 540 * 2.7 / FULL_SEASON_DEFENSIVE_OUTS - 17.5 * 10 * 2.7 / 162)
    ) < 1e-9
    assert 3 not in rows


def test_origin_position_uses_comparable_exposure_for_dh() -> None:
    fielding = pl.DataFrame(
        {
            "season": [2021, 2021, 2021, 2020],
            "player_id": [1, 1, 2, 1],
            "position_abbreviation": ["SS", "DH", "C", "C"],
            "games_started": [8, 12, 20, 100],
            "fielding_outs": [300, 0, 400, 2000],
        }
    )

    result = origin_position_profiles(fielding, season=2021)

    assert result.select("player_id", "origin_position").to_dicts() == [
        {"player_id": 1, "origin_position": "DH"},
        {"player_id": 2, "origin_position": "C"},
    ]
