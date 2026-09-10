import polars as pl
import pytest

from universal_baseball.historical_hitter_performance import (
    build_historical_hitter_performance_paths,
)


def _paths() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "path_player_id": [1, 1],
            "player_type": ["hitter", "hitter"],
            "outcome_tier_v2": ["fringe", "fringe"],
            "career_role": ["hitter", "hitter"],
            "path_year": [1, 2],
            "source_season": [2019, 2020],
            "adjusted_workload": [100.0, 0.0],
            "annual_role": ["hitter", "inactive"],
        }
    )


def _hitting() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "season": [2019, 2019],
            "player_id": [1, 2],
            "batting_plate_appearances": [100, 100],
            "batting_hits": [25, 20],
            "batting_doubles": [5, 4],
            "batting_triples": [1, 0],
            "batting_home_runs": [4, 2],
            "batting_base_on_balls": [12, 8],
            "batting_intentional_walks": [2, 0],
            "batting_hit_by_pitch": [1, 1],
        }
    )


def test_historical_hitter_paths_keep_inactive_year_at_zero_war() -> None:
    result = build_historical_hitter_performance_paths(
        _paths(), _hitting(), runs_per_win=10.0
    )
    assert result.height == 2
    assert result.row(1, named=True)["observed_component_war"] == 0.0
    assert result.row(0, named=True)["observed_conditional_war_per_600"] is not None


def test_historical_hitter_paths_reject_invalid_intentional_walks() -> None:
    invalid = _hitting().with_columns(
        pl.when(pl.col("player_id") == 1)
        .then(pl.lit(13))
        .otherwise(pl.col("batting_intentional_walks"))
        .alias("batting_intentional_walks")
    )
    with pytest.raises(ValueError, match="event accounting"):
        build_historical_hitter_performance_paths(
            _paths(), invalid, runs_per_win=10.0
        )


def test_active_hitter_path_requires_matching_component_outcome() -> None:
    empty = _hitting().clear()
    with pytest.raises(ValueError, match="active hitter paths"):
        build_historical_hitter_performance_paths(
            _paths(), empty, runs_per_win=10.0
        )
