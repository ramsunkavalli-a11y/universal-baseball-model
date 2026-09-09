from datetime import date

import polars as pl
import pytest

from universal_baseball.war_uncertainty_paths import (
    build_component_war_uncertainty,
    build_whole_player_war_uncertainty,
)


def _path(player_id: int, expected_war: float) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "as_of_date": [date(2026, 9, 8)],
            "player_id": [player_id],
            "season": [2027],
            "horizon": [1],
            "mlb_active_probability": [0.5],
            "conditional_mlb_pa": [400.0],
            "conditional_mlb_pa_variance": [10_000.0],
            "conditional_war_per_600_pa": [expected_war * 3.0],
            "expected_war": [expected_war],
            "event_run_variance": [0.6],
            "posterior_run_rate_variance": [0.001],
        }
    )


def test_component_uncertainty_preserves_point_and_has_real_spread() -> None:
    result = build_component_war_uncertainty(
        _path(1, 1.0),
        component="hitter",
        conditional_workload_column="conditional_mlb_pa",
        conditional_workload_variance_column="conditional_mlb_pa_variance",
        conditional_war_rate_column="conditional_war_per_600_pa",
        workload_unit=600.0,
        runs_per_win=10.0,
    )
    assert result.item(0, "projected_war_mean") == 1.0
    assert result.item(0, "projected_war_lower") < 1.0
    assert result.item(0, "projected_war_upper") > 1.0
    assert result.item(0, "annual_war_variance") == pytest.approx(
        result.item(0, "opportunity_war_variance")
        + result.item(0, "performance_war_variance")
    )


def test_whole_player_adds_two_way_variance_not_component_bounds() -> None:
    hitter = build_component_war_uncertainty(
        _path(1, 1.0), component="hitter",
        conditional_workload_column="conditional_mlb_pa",
        conditional_workload_variance_column="conditional_mlb_pa_variance",
        conditional_war_rate_column="conditional_war_per_600_pa",
        workload_unit=600.0, runs_per_win=10.0,
    )
    pitcher_input = _path(1, 0.5).rename(
        {
            "conditional_mlb_pa": "conditional_mlb_bf",
            "conditional_mlb_pa_variance": "conditional_mlb_bf_variance",
            "conditional_war_per_600_pa": "conditional_war_per_800_bf",
        }
    ).with_columns(pl.lit(800.0).alias("conditional_mlb_bf"))
    pitcher_input = pitcher_input.with_columns(
        pl.lit(1.0).alias("conditional_war_per_800_bf")
    )
    pitcher = build_component_war_uncertainty(
        pitcher_input, component="pitcher",
        conditional_workload_column="conditional_mlb_bf",
        conditional_workload_variance_column="conditional_mlb_bf_variance",
        conditional_war_rate_column="conditional_war_per_800_bf",
        workload_unit=800.0, runs_per_win=10.0,
    )
    whole = build_whole_player_war_uncertainty(pl.concat([hitter, pitcher]))
    assert whole.item(0, "projected_war_mean") == pytest.approx(1.5)
    assert whole.item(0, "annual_war_variance") == pytest.approx(
        hitter.item(0, "annual_war_variance")
        + pitcher.item(0, "annual_war_variance")
    )
