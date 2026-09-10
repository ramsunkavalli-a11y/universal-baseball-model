import math

import polars as pl

from universal_baseball.league_component_translation import (
    build_league_translated_affiliated_profiles,
    fit_same_season_league_translation,
)


COMPONENTS = ("good", "other")


def _history() -> pl.DataFrame:
    rows = []
    for season in (2023, 2024):
        for player_id in range(1, 7):
            rows.extend(
                [
                    {
                        "season": season,
                        "player_id": player_id,
                        "level_group": "AAA",
                        "league_id": 10 + player_id % 2,
                        "pa": 100,
                        "good": 20 + player_id % 2,
                        "other": 80 - player_id % 2,
                    },
                    {
                        "season": season,
                        "player_id": player_id,
                        "level_group": "MLB",
                        "league_id": 103 + player_id % 2,
                        "pa": 100,
                        "good": 30 + player_id % 2,
                        "other": 70 - player_id % 2,
                    },
                ]
            )
    return pl.DataFrame(rows)


def test_league_fit_is_centered_and_shrinks_to_level() -> None:
    fit = fit_same_season_league_translation(
        _history(),
        exposure_column="pa",
        component_columns=COMPONENTS,
        completed_seasons=(2023,),
        league_prior_exposure=500.0,
    )
    sums = fit.offsets.group_by("league_id").agg(
        pl.col("clr_environment_effect").sum().alias("total")
    )
    assert sums.filter(pl.col("total").abs() > 1e-9).is_empty()
    assert fit.offsets.filter(pl.col("level_group") == "MLB").get_column(
        "league_residual_clr_effect"
    ).sum() == 0


def test_league_profiles_preserve_probability_and_player_coverage() -> None:
    history = _history()
    fit = fit_same_season_league_translation(
        history,
        exposure_column="pa",
        component_columns=COMPONENTS,
        completed_seasons=(2023,),
    )
    result = build_league_translated_affiliated_profiles(
        pl.DataFrame({"player_id": [1, 99]}),
        history.filter(pl.col("season") == 2023),
        fit.offsets,
        exposure_column="pa",
        component_columns=COMPONENTS,
        current_season=2023,
        reference_season=2023,
        regression_exposure=100.0,
    )
    assert result.height == 2
    for row in result.iter_rows(named=True):
        assert math.isclose(row["p_good"] + row["p_other"], 1.0)
    assert result.filter(pl.col("player_id") == 99).item(0, "weighted_affiliated_exposure") == 0
