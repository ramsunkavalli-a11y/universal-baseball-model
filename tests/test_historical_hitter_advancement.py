from __future__ import annotations

import polars as pl

from universal_baseball.historical_hitter_advancement import (
    advancement_war_by_player_origin,
)


def test_historical_advancement_war_filters_horizon_and_scales_2020() -> None:
    advancement = pl.DataFrame(
        {
            "season": [2019, 2020, 2020, 2021],
            "player_id": [1, 1, 2, 1],
            "runner_runs_xb": [7.0, 1.0, -2.0, 9.0],
        }
    )

    result = advancement_war_by_player_origin(
        advancement,
        origin=2019,
        horizon=1,
        runs_per_win=10.0,
    )

    assert result.to_dicts() == [
        {
            "player_id": 1,
            "later_advancement_runs": 2.7,
            "later_advancement_war": 0.27,
        },
        {
            "player_id": 2,
            "later_advancement_runs": -5.4,
            "later_advancement_war": -0.54,
        },
    ]
