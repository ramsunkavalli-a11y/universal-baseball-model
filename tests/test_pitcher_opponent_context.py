from __future__ import annotations

import polars as pl

from universal_baseball.historical_matchup_profiles import PROFILE_SPECS
from universal_baseball.pitcher_opponent_context import (
    aggregate_pitcher_opponent_context,
)


def test_aggregate_pitcher_opponent_context_uses_actual_batters() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024],
            "pitcher_id": [10, 10],
            "batter_id": [20, 21],
            "pitcher_hand": ["R", "R"],
            "batter_side": ["L", "R"],
            "level_rank": [5, 5],
        }
    )
    overall = pl.DataFrame(
        {
            "target_season": [2024, 2024],
            "player_id": [20, 21],
            "h_history_pa": [100.0, 200.0],
            "h_last_level_rank": [4.0, 5.0],
            **{f"h_{name}": [0.1, -0.1] for name in PROFILE_SPECS},
        }
    )
    split = pl.DataFrame(
        {
            "target_season": [2024, 2024],
            "player_id": [20, 21],
            "pitcher_hand": ["R", "R"],
            "hs_history_pa": [50.0, 50.0],
            **{f"hs_{name}": [0.2, 0.0] for name in PROFILE_SPECS},
        }
    )
    result = aggregate_pitcher_opponent_context(events, overall, split)
    assert result.height == 1
    assert result.item(0, "opponent_overall_k") == 0.0
    assert result.item(0, "opponent_split_k") == 0.1
    assert result.item(0, "opponent_left_batter_share") == 0.5
