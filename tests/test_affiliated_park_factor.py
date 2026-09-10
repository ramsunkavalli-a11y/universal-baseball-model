import polars as pl

from universal_baseball.affiliated_park_factor import (
    build_venue_season_observations,
    fit_park_factors,
    score_park_factors,
)


def _games() -> pl.DataFrame:
    rows = []
    game = 0
    for season in (2023, 2024):
        for index in range(20):
            game += 1
            rows.append((season, game, 11, 50, 1, 2, 6, 4, 9))
            game += 1
            rows.append((season, game, 11, 60, 2, 1, 4, 4, 9))
    return pl.DataFrame(
        rows,
        schema=["season", "game_pk", "sport_id", "venue_id", "home_team_id", "away_team_id", "home_score", "away_score", "scheduled_innings"],
        orient="row",
    )


def test_park_factor_uses_same_team_road_environment_and_shrinks() -> None:
    observations = build_venue_season_observations(_games())
    factors = fit_park_factors(observations, through_season=2023, prior_games=20)
    park = factors.filter(pl.col("venue_id") == 50).row(0, named=True)
    assert 1.0 < park["predicted_park_factor"] < 1.25
    score = score_park_factors(observations, factors, season=2024)
    assert score["candidate_rmse"] < score["baseline_rmse"]
