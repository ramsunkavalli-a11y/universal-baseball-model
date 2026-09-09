import math

import polars as pl

from universal_baseball.pitcher_component_aging import (
    apply_fitted_pitcher_aging,
    build_adjacent_pitcher_profiles,
    fit_pitcher_component_aging,
)


def _history() -> tuple[pl.DataFrame, pl.DataFrame]:
    rows = []
    ages = []
    for player_id in range(1, 81):
        for season in (2019, 2020, 2021):
            age = 20 + player_id % 18 + season - 2019
            bf = 200 + player_id
            rows.append(
                {
                    "season": season, "player_id": player_id, "bf": bf,
                    "so": 40 + player_id % 8 - (season - 2019),
                    "ubb": 15 + player_id % 3, "hbp": 2,
                    "hr": 5 + (season - 2019),
                }
            )
            ages.append({"season": season, "player_id": player_id, "age": age})
    return pl.DataFrame(rows), pl.DataFrame(ages)


def test_fitted_pitcher_aging_preserves_coherent_probabilities() -> None:
    history, ages = _history()
    pairs = build_adjacent_pitcher_profiles(history, ages)
    parameters = fit_pitcher_component_aging(
        pairs, maximum_target_season=2021, ridge_weight=100.0
    )
    source = {"so": 0.25, "ubb": 0.08, "hbp": 0.01, "hr": 0.03, "other": 0.63}
    aged = apply_fitted_pitcher_aging(
        source, current_age=26.5, target_age=31.5, parameters=parameters
    )
    assert math.isclose(sum(aged.values()), 1.0)
    assert all(0 < value < 1 for value in aged.values())
    assert aged != source
