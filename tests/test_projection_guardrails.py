from datetime import date

import polars as pl
import pytest

from universal_baseball.projection_guardrails import (
    HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA,
    PROJECTION_PATH_SCHEMA,
    audit_projection_paths,
    build_historical_plausibility_reference,
)


def _history(*, active_rows: int = 40) -> pl.DataFrame:
    rows = []
    for index in range(active_rows):
        rows.append(
            {
                "season": 2020 + index % 5,
                "player_id": index + 1,
                "projection_component": "hitter",
                "role": "position_player",
                "workload_measure": "PA",
                "workload": float(400 + index * 5),
                "workload_unit": 600.0,
                "context_neutral_war": float(1.0 + index / 20),
            }
        )
    return pl.DataFrame(rows, schema=HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA)


def _projections(*, extreme: bool = False, uses_depth: bool = False) -> pl.DataFrame:
    rows = []
    for player_id in (101, 102):
        for season in (2025, 2026):
            probability = 0.8 if player_id == 101 else 0.2
            workload = 800.0 if extreme and player_id == 101 else 500.0
            rate = 9.0 if extreme and player_id == 101 else 2.0
            rows.append(
                {
                    "as_of_date": date(2024, 12, 31),
                    "player_id": player_id,
                    "season": season,
                    "projection_component": "hitter",
                    "role": "position_player",
                    "workload_measure": "PA",
                    "mlb_active_probability": probability,
                    "conditional_war_rate": rate,
                    "conditional_workload": workload,
                    "workload_unit": 600.0,
                    "expected_war": probability * rate * workload / 600.0,
                    "is_controlled_season": season == 2025,
                    "coverage_tier": "full_model" if player_id == 101 else "fallback",
                    "probability_model_id": "arrival:test",
                    "workload_model_id": "workload:test",
                    "talent_model_id": "talent:test",
                    "uses_current_team_depth": uses_depth,
                }
            )
    return pl.DataFrame(rows, schema=PROJECTION_PATH_SCHEMA)


def _reference(*, minimum: int = 30) -> pl.DataFrame:
    return build_historical_plausibility_reference(
        _history(), forecast_year=2025, minimum_active_player_seasons=minimum
    )


def test_historical_reference_is_preforecast_and_role_specific() -> None:
    reference = _reference()
    assert reference.height == 1
    assert reference.item(0, "history_end_season") == 2024
    assert reference.item(0, "active_player_seasons") == 40
    assert reference.item(0, "reference_status") == "available"


def test_projection_identity_and_controlled_war_reconcile() -> None:
    result = audit_projection_paths(
        _projections(),
        pl.DataFrame({"player_id": [101, 102]}),
        _reference(),
        forecast_years=[2025, 2026],
    )
    assert result.reviews.is_empty()
    player = result.paths.filter(pl.col("player_id") == 101).row(0, named=True)
    assert player["expected_war"] == pytest.approx(8 / 3)
    assert player["controlled_expected_war"] == pytest.approx(4 / 3)
    assert player["coverage_tiers"] == "full_model"


def test_historical_extremes_are_flagged_without_clipping() -> None:
    result = audit_projection_paths(
        _projections(extreme=True),
        pl.DataFrame({"player_id": [101, 102]}),
        _reference(),
        forecast_years=[2025, 2026],
    )
    extreme = result.annual.filter(pl.col("player_id") == 101)
    assert extreme.get_column("plausibility_status").unique().to_list() == [
        "review_historical_extreme"
    ]
    assert extreme.item(0, "conditional_workload") == 800.0
    assert extreme.item(0, "conditional_war_rate") == 9.0
    assert extreme.item(0, "expected_war") == pytest.approx(9.6)
    assert extreme.item(0, "workload_above_observed_max")
    assert extreme.item(0, "war_rate_above_high_quantile")


def test_current_team_depth_is_forbidden_from_intrinsic_path() -> None:
    with pytest.raises(ValueError, match="current-team depth"):
        audit_projection_paths(
            _projections(uses_depth=True),
            pl.DataFrame({"player_id": [101, 102]}),
            _reference(),
            forecast_years=[2025, 2026],
        )


def test_missing_player_year_fails_universal_coverage() -> None:
    source = _projections().filter(
        ~((pl.col("player_id") == 102) & (pl.col("season") == 2026))
    )
    with pytest.raises(ValueError, match="every player-year"):
        audit_projection_paths(
            source,
            pl.DataFrame({"player_id": [101, 102]}),
            _reference(),
            forecast_years=[2025, 2026],
        )


def test_expected_war_must_equal_probability_rate_times_workload() -> None:
    source = _projections().with_columns(
        pl.when((pl.col("player_id") == 101) & (pl.col("season") == 2025))
        .then(pl.col("expected_war") + 1.0)
        .otherwise(pl.col("expected_war"))
        .alias("expected_war")
    )
    with pytest.raises(ValueError, match="does not reconcile"):
        audit_projection_paths(
            source,
            pl.DataFrame({"player_id": [101, 102]}),
            _reference(),
            forecast_years=[2025, 2026],
        )


def test_small_historical_role_sample_stays_in_review() -> None:
    result = audit_projection_paths(
        _projections(),
        pl.DataFrame({"player_id": [101, 102]}),
        _reference(minimum=50),
        forecast_years=[2025, 2026],
    )
    assert result.reviews.height == 4
    assert result.paths.get_column("path_status").unique().to_list() == ["review"]


def test_two_way_player_components_sum_without_duplicate_failure() -> None:
    pitcher_history = pl.DataFrame(
        [
            {
                "season": 2020 + index % 5,
                "player_id": 1000 + index,
                "projection_component": "pitcher",
                "role": "starter",
                "workload_measure": "BF",
                "workload": 500.0 + index,
                "workload_unit": 800.0,
                "context_neutral_war": 1.5,
            }
            for index in range(40)
        ],
        schema=HISTORICAL_PLAUSIBILITY_INPUT_SCHEMA,
    )
    reference = build_historical_plausibility_reference(
        pl.concat([_history(), pitcher_history]), forecast_year=2025
    )
    hitter = _projections().filter(
        (pl.col("player_id") == 101) & (pl.col("season") == 2025)
    )
    pitcher = hitter.with_columns(
        pl.lit("pitcher").alias("projection_component"),
        pl.lit("starter").alias("role"),
        pl.lit("BF").alias("workload_measure"),
        pl.lit(0.5).alias("mlb_active_probability"),
        pl.lit(2.0).alias("conditional_war_rate"),
        pl.lit(400.0).alias("conditional_workload"),
        pl.lit(800.0).alias("workload_unit"),
        pl.lit(0.5).alias("expected_war"),
    )
    result = audit_projection_paths(
        pl.concat([hitter, pitcher]),
        pl.DataFrame({"player_id": [101]}),
        reference,
        forecast_years=[2025],
    )
    assert result.paths.item(0, "component_rows") == 2
    assert result.paths.item(0, "expected_war") == pytest.approx(4 / 3 + 0.5)


def test_history_may_not_cross_forecast_cutoff() -> None:
    source = _history().with_columns(
        pl.when(pl.col("player_id") == 1)
        .then(pl.lit(2025))
        .otherwise(pl.col("season"))
        .alias("season")
    )
    with pytest.raises(ValueError, match="crosses the forecast year"):
        build_historical_plausibility_reference(source, forecast_year=2025)
