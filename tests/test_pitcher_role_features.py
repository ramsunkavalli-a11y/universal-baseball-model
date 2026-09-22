from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.pitcher_role_features import add_pitcher_role_features


def test_pitcher_role_features_capture_interruption_and_level_change() -> None:
    values: dict[str, list[object]] = {}
    for lag, bf, games, starts, mlb, level in (
        (0, 40.0, 10.0, 2.0, 0.0, "AA"),
        (1, 200.0, 25.0, 20.0, 0.0, "A+"),
        (2, 180.0, 30.0, 25.0, 0.0, "A"),
    ):
        values[f"lag{lag}__start_share"] = [starts / games]
        values[f"lag{lag}__games"] = [games]
        values[f"lag{lag}__starts"] = [starts]
        values[f"lag{lag}__batters_faced"] = [bf]
        values[f"lag{lag}__log_batters_faced"] = [bf]
        values[f"lag{lag}__bf_level__MLB"] = [mlb]
        values[f"lag{lag}__highest_level"] = [level]
        values[f"lag{lag}__missing"] = [0]
    result = add_pitcher_role_features(pl.DataFrame(values)).row(0, named=True)
    assert result["workload_interrupted"] == 1
    assert result["level_rank_trend"] == pytest.approx(1.0)
    assert result["role_start_share_trend"] == pytest.approx(-0.6)
