import polars as pl

from universal_baseball.affiliated_component_park_factor import (
    build_component_park_observations,
    build_park_neutral_player_rows,
    build_schedule_opponent_adjustments,
    fit_component_park_factors,
    score_component_park_factors,
)


COMPONENTS = ("hit", "out")


def _source() -> tuple[pl.DataFrame, pl.DataFrame]:
    rows = []
    for season in (2022, 2023, 2024):
        for team, venue, home_hit, away_hit in (
            (1, 10, 30, 20), (2, 20, 20, 30),
        ):
            rows.extend([
                {"season": season, "sport_id": 11, "team_id": team,
                 "player_id": team * 10, "split_code": "h", "pa": 100,
                 "hit": home_hit, "out": 100 - home_hit},
                {"season": season, "sport_id": 11, "team_id": team,
                 "player_id": team * 10, "split_code": "a", "pa": 100,
                 "hit": away_hit, "out": 100 - away_hit},
            ])
    context = pl.DataFrame([
        {"season": season, "sport_id": 11, "team_id": team,
         "league_id": 100, "venue_id": venue}
        for season in (2022, 2023, 2024)
        for team, venue in ((1, 10), (2, 20))
    ])
    return pl.DataFrame(rows), context


def test_component_park_factor_improves_repeating_home_split() -> None:
    source, context = _source()
    observations = build_component_park_observations(
        source, context, exposure_column="pa", component_columns=COMPONENTS
    )
    factors = fit_component_park_factors(
        observations, through_season=2023,
        component_columns=COMPONENTS, prior_exposure=10,
    )
    score = score_component_park_factors(
        observations, factors, season=2024, component_columns=COMPONENTS
    )

    assert score["candidate_log_loss"] < score["baseline_log_loss"]
    assert score["candidate_brier"] < score["baseline_brier"]
    assert factors.filter(pl.col("venue_id") == 10).filter(
        pl.col("component") == "hit"
    ).item(0, "park_clr_effect") > 0


def test_player_neutralization_changes_home_only_and_preserves_exposure() -> None:
    source, context = _source()
    observations = build_component_park_observations(
        source, context, exposure_column="pa", component_columns=COMPONENTS
    )
    factors = fit_component_park_factors(
        observations, through_season=2023,
        component_columns=COMPONENTS, prior_exposure=0,
    )
    result = build_park_neutral_player_rows(
        source.filter((pl.col("season") == 2023) & (pl.col("team_id") == 1)),
        context, factors, exposure_column="pa", component_columns=COMPONENTS,
        level_by_sport={11: "AAA"},
    ).row(0, named=True)

    assert result["pa"] == 200
    assert result["hit"] < 50  # the hitter-friendly home split is neutralized
    assert abs(result["hit"] + result["out"] - 200) < 1e-9


def test_schedule_opponent_adjustment_uses_home_and_away_mix() -> None:
    games = pl.DataFrame([
        {"season": 2024, "sport_id": 11, "home_team_id": 1, "away_team_id": 2},
        {"season": 2024, "sport_id": 11, "home_team_id": 3, "away_team_id": 1},
    ])
    opponents = pl.DataFrame([
        {"season": 2024, "sport_id": 11, "team_id": 2, "pa": 100, "hit": 10, "out": 90},
        {"season": 2024, "sport_id": 11, "team_id": 3, "pa": 100, "hit": 40, "out": 60},
    ])
    result = build_schedule_opponent_adjustments(
        games, opponents, exposure_column="pa", component_columns=COMPONENTS
    ).filter(pl.col("team_id") == 1)

    assert result.height == 1
    assert result.item(0, "opponent_effect_hit") < 0
