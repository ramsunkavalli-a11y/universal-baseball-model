from __future__ import annotations

import polars as pl

from universal_baseball.historical_hitter_baserunning import (
    steal_war_by_player_origin,
)
from universal_baseball.player_value_baserunning_runs import build_baserunning_reference


def test_historical_steal_runs_are_centered_and_scale_2020() -> None:
    reference = build_baserunning_reference(
        season=2024,
        plate_appearances=1000,
        runs=100,
        outs=700,
        steal_opportunity_proxy=200,
        steal_attempts=20,
        stolen_bases=15,
        advancement_opportunities=50,
    )
    hitting = pl.DataFrame(
        {
            "season": [2019, 2019, 2020, 2020],
            "player_id": [1, 2, 1, 2],
            "batting_hits": [20, 20, 20, 20],
            "batting_doubles": [2, 2, 2, 2],
            "batting_triples": [0, 0, 0, 0],
            "batting_home_runs": [2, 2, 2, 2],
            "batting_base_on_balls": [10, 10, 10, 10],
            "batting_intentional_walks": [0, 0, 0, 0],
            "batting_hit_by_pitch": [0, 0, 0, 0],
            "batting_stolen_bases": [5, 0, 5, 0],
            "batting_caught_stealing": [0, 2, 0, 2],
        }
    )

    result = steal_war_by_player_origin(
        hitting,
        origin=2018,
        horizon=2,
        runs_per_win=10.0,
        reference=reference,
    )

    assert abs(result["later_steal_runs"].sum()) < 1e-12
    player_one = result.filter(pl.col("player_id") == 1).item(0, "later_steal_runs")
    player_two = result.filter(pl.col("player_id") == 2).item(0, "later_steal_runs")
    assert player_one > 0
    assert player_two < 0
    assert abs(player_one + player_two) < 1e-12
