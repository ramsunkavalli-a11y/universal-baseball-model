import polars as pl
import pytest

from universal_baseball.historical_pitcher_performance import (
    build_historical_pitcher_performance_paths,
)


def _paths() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "path_player_id": [1, 1],
            "player_type": ["pitcher", "pitcher"],
            "outcome_tier_v2": ["fringe", "fringe"],
            "career_role": ["reliever", "reliever"],
            "path_year": [1, 2],
            "source_season": [2019, 2020],
            "adjusted_workload": [100.0, 0.0],
            "annual_role": ["reliever", "inactive"],
        }
    )


def test_historical_pitcher_paths_keep_inactive_year_at_zero_war() -> None:
    pitching = pl.DataFrame(
        {
            "season": [2019],
            "player_id": [1],
            "pitching_bf": [100],
            "pitching_so": [25],
            "pitching_ubb": [8],
            "pitching_hbp": [1],
            "pitching_hr": [3],
        }
    )
    result = build_historical_pitcher_performance_paths(
        _paths(), pitching, runs_per_win=10.0
    )
    assert result.height == 2
    assert result.row(1, named=True)["observed_component_war"] == 0.0
    assert result.row(0, named=True)["observed_conditional_war_per_800"] is not None


def test_active_path_requires_matching_component_outcome() -> None:
    empty = pl.DataFrame(
        schema={
            "season": pl.Int64,
            "player_id": pl.Int64,
            "pitching_bf": pl.Int64,
            "pitching_so": pl.Int64,
            "pitching_ubb": pl.Int64,
            "pitching_hbp": pl.Int64,
            "pitching_hr": pl.Int64,
        }
    )
    with pytest.raises(ValueError, match="active pitcher paths"):
        build_historical_pitcher_performance_paths(_paths(), empty, runs_per_win=10.0)
