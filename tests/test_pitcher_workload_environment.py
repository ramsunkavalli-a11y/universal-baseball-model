import polars as pl
import pytest

from scripts.audit_pitcher_workload_environment import summarize_environment


def test_pitcher_environment_uses_positive_bf_and_unique_player_seasons() -> None:
    source = pl.DataFrame(
        {
            "season": [2023, 2023, 2023],
            "player_id": [1, 2, 3],
            "pitching_bf": [100, 300, 0],
            "pitching_games": [10, 20, 1],
            "pitching_starts": [0, 10, 0],
        }
    )
    result = summarize_environment(source).row(0, named=True)
    assert result["active_pitchers"] == 2
    assert result["league_bf"] == 400
    assert result["mean_bf_per_pitcher"] == 200
    assert result["median_bf_per_pitcher"] == 200
    assert result["pitchers_with_start"] == 1

    with pytest.raises(ValueError, match="player-season grain"):
        summarize_environment(pl.concat([source, source.head(1)]))
