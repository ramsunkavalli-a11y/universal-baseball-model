from datetime import date

import polars as pl
import pytest

from universal_baseball.pitcher_opportunity_paths import (
    PITCHER_CONDITIONAL_WAR_RATE_SCHEMA,
    PITCHER_CONTROL_SEASON_SCHEMA,
    PITCHER_OPPORTUNITY_HISTORY_SCHEMA,
    PITCHER_OPPORTUNITY_PATH_SCHEMA,
    compose_pitcher_projection_paths,
    fit_pitcher_opportunity_fallbacks,
    pitcher_role,
    score_pitcher_opportunity_paths,
)


def _history() -> pl.DataFrame:
    rows = []
    for snapshot in (2021, 2022):
        for horizon in (1, 2):
            rows.extend(
                [
                    {"snapshot_year": snapshot, "player_id": snapshot * 100 + horizon * 10 + 1, "age_years": 25.0, "as_of_level_group": "MLB", "as_of_role": "starter", "horizon": horizon, "future_mlb_bf": 700.0, "future_mlb_games": 28, "future_mlb_starts": 28},
                    {"snapshot_year": snapshot, "player_id": snapshot * 100 + horizon * 10 + 2, "age_years": 28.0, "as_of_level_group": "MLB", "as_of_role": "reliever", "horizon": horizon, "future_mlb_bf": 240.0, "future_mlb_games": 60, "future_mlb_starts": 0},
                    {"snapshot_year": snapshot, "player_id": snapshot * 100 + horizon * 10 + 3, "age_years": 22.0, "as_of_level_group": "AA", "as_of_role": "starter", "horizon": horizon, "future_mlb_bf": 300.0 if horizon == 2 else 0.0, "future_mlb_games": 15 if horizon == 2 else 0, "future_mlb_starts": 8 if horizon == 2 else 0},
                    {"snapshot_year": snapshot, "player_id": snapshot * 100 + horizon * 10 + 4, "age_years": None, "as_of_level_group": "INACTIVE", "as_of_role": "unknown", "horizon": horizon, "future_mlb_bf": 0.0, "future_mlb_games": 0, "future_mlb_starts": 0},
                ]
            )
    return pl.DataFrame(rows, schema=PITCHER_OPPORTUNITY_HISTORY_SCHEMA)


def test_role_classification_is_explicit() -> None:
    assert pitcher_role(games=30, starts=20) == "starter"
    assert pitcher_role(games=30, starts=5) == "swingman"
    assert pitcher_role(games=30, starts=0) == "reliever"


def test_every_pitcher_gets_arrival_workload_and_role_path() -> None:
    fit = fit_pitcher_opportunity_fallbacks(_history(), forecast_year=2025, horizons=[1, 2])
    universe = pl.DataFrame(
        {
            "player_id": [1, 2, 3],
            "age_years": [25.0, 22.0, None],
            "as_of_level_group": ["MLB", "AA", "unknown"],
            "as_of_role": ["starter", "starter", "unknown"],
        }
    )
    paths = score_pitcher_opportunity_paths(
        universe, fit, as_of_date=date(2024, 12, 31), forecast_year=2025
    )
    assert paths.schema == PITCHER_OPPORTUNITY_PATH_SCHEMA
    assert paths.height == 6
    assert not paths.get_column("uses_current_team_depth").any()
    assert paths.filter(
        (
            pl.col("starter_probability_if_active")
            + pl.col("swingman_probability_if_active")
            + pl.col("reliever_probability_if_active")
            - 1.0
        ).abs()
        > 1e-12
    ).is_empty()
    assert paths.filter(
        (pl.col("expected_mlb_bf") - pl.col("mlb_active_probability") * pl.col("conditional_mlb_bf")).abs()
        > 1e-12
    ).is_empty()


def test_lower_level_pitcher_can_have_delayed_arrival() -> None:
    fit = fit_pitcher_opportunity_fallbacks(
        _history(), forecast_year=2025, horizons=[1, 2], participation_prior_players=1
    )
    universe = pl.DataFrame(
        {"player_id": [2], "age_years": [22.0], "as_of_level_group": ["AA"], "as_of_role": ["starter"]}
    )
    paths = score_pitcher_opportunity_paths(
        universe, fit, as_of_date=date(2024, 12, 31), forecast_year=2025
    )
    assert paths.item(1, "mlb_active_probability") > paths.item(0, "mlb_active_probability")


def test_future_data_and_inconsistent_outcomes_fail() -> None:
    with pytest.raises(ValueError, match="crosses the forecast cutoff"):
        fit_pitcher_opportunity_fallbacks(_history(), forecast_year=2024, horizons=[1, 2])
    broken = _history().with_columns(
        pl.when(pl.col("player_id") == broken_id())
        .then(pl.lit(1))
        .otherwise(pl.col("future_mlb_games"))
        .alias("future_mlb_games")
    )
    with pytest.raises(ValueError, match="invalid outcomes"):
        fit_pitcher_opportunity_fallbacks(broken, forecast_year=2025, horizons=[1, 2])


def broken_id() -> int:
    return 2021 * 100 + 1 * 10 + 4


def test_pitcher_path_composes_to_shared_war_identity() -> None:
    fit = fit_pitcher_opportunity_fallbacks(_history(), forecast_year=2025, horizons=[1])
    opportunity = score_pitcher_opportunity_paths(
        pl.DataFrame(
            {"player_id": [1], "age_years": [25.0], "as_of_level_group": ["MLB"], "as_of_role": ["starter"]}
        ),
        fit,
        as_of_date=date(2024, 12, 31),
        forecast_year=2025,
    )
    rates = pl.DataFrame(
        [{"player_id": 1, "season": 2025, "conditional_war_per_800_bf": 3.0, "talent_model_id": "pitcher_rate:test"}],
        schema=PITCHER_CONDITIONAL_WAR_RATE_SCHEMA,
    )
    control = pl.DataFrame(
        [{"player_id": 1, "season": 2025, "is_controlled_season": True}],
        schema=PITCHER_CONTROL_SEASON_SCHEMA,
    )
    result = compose_pitcher_projection_paths(opportunity, rates, control)
    assert result.item(0, "projection_component") == "pitcher"
    assert result.item(0, "workload_measure") == "BF"
    assert result.item(0, "expected_war") == pytest.approx(
        result.item(0, "mlb_active_probability")
        * 3.0
        * result.item(0, "conditional_workload")
        / 800.0
    )
