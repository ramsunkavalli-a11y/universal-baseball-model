from datetime import date

import polars as pl
import pytest

from universal_baseball.hitter_opportunity_paths import (
    HITTER_CONDITIONAL_WAR_RATE_SCHEMA,
    HITTER_CONTROL_SEASON_SCHEMA,
    HITTER_OPPORTUNITY_HISTORY_SCHEMA,
    HITTER_OPPORTUNITY_PATH_SCHEMA,
    HITTER_OPPORTUNITY_SNAPSHOT_SCHEMA,
    HITTER_MLB_PA_OUTCOME_SCHEMA,
    build_hitter_opportunity_history,
    compose_hitter_projection_paths,
    fit_hitter_opportunity_fallbacks,
    score_hitter_opportunity_paths,
)
from universal_baseball.projection_guardrails import PROJECTION_PATH_SCHEMA


def _history() -> pl.DataFrame:
    rows = []
    for snapshot_year in (2021, 2022):
        for horizon in (1, 2, 3):
            rows.extend(
                [
                    {
                        "snapshot_year": snapshot_year,
                        "player_id": snapshot_year * 1000 + horizon * 10 + 1,
                        "age_years": 24.0,
                        "as_of_level_group": "MLB",
                        "horizon": horizon,
                        "future_mlb_pa": 600.0 - 20.0 * horizon,
                    },
                    {
                        "snapshot_year": snapshot_year,
                        "player_id": snapshot_year * 1000 + horizon * 10 + 2,
                        "age_years": 24.0,
                        "as_of_level_group": "MLB",
                        "horizon": horizon,
                        "future_mlb_pa": 0.0,
                    },
                    {
                        "snapshot_year": snapshot_year,
                        "player_id": snapshot_year * 1000 + horizon * 10 + 3,
                        "age_years": 20.0,
                        "as_of_level_group": "Single-A",
                        "horizon": horizon,
                        "future_mlb_pa": 100.0 if horizon >= 2 else 0.0,
                    },
                    {
                        "snapshot_year": snapshot_year,
                        "player_id": snapshot_year * 1000 + horizon * 10 + 4,
                        "age_years": None,
                        "as_of_level_group": "INACTIVE",
                        "horizon": horizon,
                        "future_mlb_pa": 0.0,
                    },
                ]
            )
    return pl.DataFrame(rows, schema=HITTER_OPPORTUNITY_HISTORY_SCHEMA)


def _universe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [101, 102, 103, 104],
            "age_years": [25.0, 20.0, None, 31.0],
            "as_of_level_group": ["MLB", "HIGH_A", "INACTIVE", "unclassified"],
        }
    )


def test_history_builder_keeps_non_arrivals_as_observed_zero() -> None:
    snapshots = pl.DataFrame(
        [
            {
                "snapshot_year": 2021,
                "player_id": 1,
                "age_years": 22.0,
                "as_of_level_group": "AA",
            },
            {
                "snapshot_year": 2021,
                "player_id": 2,
                "age_years": 20.0,
                "as_of_level_group": "Single-A",
            },
        ],
        schema=HITTER_OPPORTUNITY_SNAPSHOT_SCHEMA,
    )
    outcomes = pl.DataFrame(
        [{"season": 2023, "player_id": 1, "batting_pa": 125.0}],
        schema=HITTER_MLB_PA_OUTCOME_SCHEMA,
    )
    history = build_hitter_opportunity_history(
        snapshots,
        outcomes,
        horizons=[1, 2],
        completed_seasons=[2022, 2023],
    )
    assert history.height == 4
    assert history.filter(pl.col("player_id") == 2).get_column("future_mlb_pa").to_list() == [
        0.0,
        0.0,
    ]
    assert history.filter(
        (pl.col("player_id") == 1) & (pl.col("horizon") == 2)
    ).item(0, "future_mlb_pa") == 125.0


def test_history_builder_requires_completed_target_seasons() -> None:
    snapshots = pl.DataFrame(
        [{"snapshot_year": 2023, "player_id": 1, "age_years": 22.0, "as_of_level_group": "AA"}],
        schema=HITTER_OPPORTUNITY_SNAPSHOT_SCHEMA,
    )
    outcomes = pl.DataFrame(schema=HITTER_MLB_PA_OUTCOME_SCHEMA)
    with pytest.raises(ValueError, match="not certified complete"):
        build_hitter_opportunity_history(
            snapshots, outcomes, horizons=[1, 2], completed_seasons=[2024]
        )


def test_every_hitter_gets_every_year_without_team_depth() -> None:
    fit = fit_hitter_opportunity_fallbacks(
        _history(), forecast_year=2026, horizons=[1, 2, 3]
    )
    paths = score_hitter_opportunity_paths(
        _universe(), fit, as_of_date=date(2025, 12, 31), forecast_year=2026
    )
    assert paths.schema == HITTER_OPPORTUNITY_PATH_SCHEMA
    assert paths.height == 12
    assert paths.group_by("player_id").len().get_column("len").unique().to_list() == [3]
    assert not paths.get_column("uses_current_team_depth").any()
    assert paths.filter(pl.col("expected_mlb_pa") < 0).is_empty()
    assert paths.filter(
        (pl.col("expected_mlb_pa") - pl.col("mlb_active_probability") * pl.col("conditional_mlb_pa")).abs()
        > 1e-12
    ).is_empty()


def test_selected_model_is_used_only_for_supported_next_year_players() -> None:
    fit = fit_hitter_opportunity_fallbacks(
        _history(), forecast_year=2026, horizons=[1, 2, 3]
    )
    selected = pl.DataFrame(
        {
            "player_id": [101],
            "predicted_any_mlb_pa_probability": [0.8],
            "predicted_positive_mlb_pa_mean": [500.0],
        }
    )
    paths = score_hitter_opportunity_paths(
        _universe(),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
        selected_next_year=selected,
    )
    first = paths.filter((pl.col("player_id") == 101) & (pl.col("horizon") == 1))
    later = paths.filter((pl.col("player_id") == 101) & (pl.col("horizon") > 1))
    assert first.item(0, "expected_mlb_pa") == pytest.approx(400.0)
    assert first.item(0, "coverage_tier") == "selected_next_year_model"
    assert "selected_next_year_model" not in later.get_column("coverage_tier").to_list()


def test_horizon_cohorts_allow_delayed_low_minors_arrival() -> None:
    fit = fit_hitter_opportunity_fallbacks(
        _history(), forecast_year=2026, horizons=[1, 2, 3], participation_prior_players=1
    )
    paths = score_hitter_opportunity_paths(
        _universe().filter(pl.col("player_id") == 102),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
    )
    assert paths.filter(pl.col("horizon") == 2).item(0, "mlb_active_probability") > paths.filter(
        pl.col("horizon") == 1
    ).item(0, "mlb_active_probability")


def test_unknown_player_uses_population_when_no_unknown_history_exists() -> None:
    history = _history().filter(pl.col("as_of_level_group") != "INACTIVE")
    fit = fit_hitter_opportunity_fallbacks(history, forecast_year=2026, horizons=[1, 2, 3])
    paths = score_hitter_opportunity_paths(
        _universe().filter(pl.col("player_id") == 104),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
    )
    assert paths.get_column("coverage_tier").unique().to_list() == [
        "population_historical_fallback"
    ]


def test_forecast_cutoff_and_requested_horizon_are_enforced() -> None:
    with pytest.raises(ValueError, match="crosses the forecast cutoff"):
        fit_hitter_opportunity_fallbacks(_history(), forecast_year=2025, horizons=[1, 2, 3])
    with pytest.raises(ValueError, match="lacks horizons"):
        fit_hitter_opportunity_fallbacks(_history(), forecast_year=2026, horizons=[4])


def test_historical_workload_is_not_arbitrarily_capped() -> None:
    history = _history().with_columns(
        pl.when((pl.col("horizon") == 1) & (pl.col("future_mlb_pa") > 0))
        .then(pl.lit(900.0))
        .otherwise(pl.col("future_mlb_pa"))
        .alias("future_mlb_pa")
    )
    fit = fit_hitter_opportunity_fallbacks(
        history,
        forecast_year=2026,
        horizons=[1],
        workload_prior_positive_players=1,
    )
    paths = score_hitter_opportunity_paths(
        _universe().filter(pl.col("player_id") == 101),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
    )
    assert paths.item(0, "conditional_mlb_pa") > 700.0


def test_opportunity_composes_into_explicit_guardrail_path() -> None:
    fit = fit_hitter_opportunity_fallbacks(_history(), forecast_year=2026, horizons=[1, 2])
    opportunity = score_hitter_opportunity_paths(
        _universe().filter(pl.col("player_id") == 101),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
    )
    rates = pl.DataFrame(
        [
            {
                "player_id": 101,
                "season": season,
                "conditional_war_per_600_pa": 3.0,
                "talent_model_id": "hitter_rate:test",
            }
            for season in (2026, 2027)
        ],
        schema=HITTER_CONDITIONAL_WAR_RATE_SCHEMA,
    )
    controls = pl.DataFrame(
        [
            {"player_id": 101, "season": 2026, "is_controlled_season": True},
            {"player_id": 101, "season": 2027, "is_controlled_season": False},
        ],
        schema=HITTER_CONTROL_SEASON_SCHEMA,
    )
    result = compose_hitter_projection_paths(opportunity, rates, controls)
    assert result.schema == PROJECTION_PATH_SCHEMA
    assert result.item(0, "expected_war") == pytest.approx(
        result.item(0, "mlb_active_probability")
        * 3.0
        * result.item(0, "conditional_workload")
        / 600.0
    )
    assert result.get_column("is_controlled_season").to_list() == [True, False]


def test_composition_rejects_incomplete_rate_coverage() -> None:
    fit = fit_hitter_opportunity_fallbacks(_history(), forecast_year=2026, horizons=[1, 2])
    opportunity = score_hitter_opportunity_paths(
        _universe().filter(pl.col("player_id") == 101),
        fit,
        as_of_date=date(2025, 12, 31),
        forecast_year=2026,
    )
    rates = pl.DataFrame(
        [
            {
                "player_id": 101,
                "season": 2026,
                "conditional_war_per_600_pa": 3.0,
                "talent_model_id": "hitter_rate:test",
            }
        ],
        schema=HITTER_CONDITIONAL_WAR_RATE_SCHEMA,
    )
    controls = pl.DataFrame(
        [
            {"player_id": 101, "season": season, "is_controlled_season": True}
            for season in (2026, 2027)
        ],
        schema=HITTER_CONTROL_SEASON_SCHEMA,
    )
    with pytest.raises(ValueError, match="WAR-rate coverage"):
        compose_hitter_projection_paths(opportunity, rates, controls)
