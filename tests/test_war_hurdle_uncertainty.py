from datetime import date

import polars as pl
import pytest

from universal_baseball.war_hurdle_uncertainty import (
    build_component_hurdle_war_uncertainty,
    build_component_simulated_war_uncertainty,
    build_whole_player_from_component_intervals,
    hurdle_normal_quantile,
)


def test_hurdle_quantile_exposes_zero_mass() -> None:
    assert hurdle_normal_quantile(
        0.5,
        active_probability=0.2,
        active_mean=1.0,
        active_standard_deviation=0.2,
    ) == 0.0
    assert hurdle_normal_quantile(
        0.9,
        active_probability=0.2,
        active_mean=1.0,
        active_standard_deviation=0.2,
    ) == pytest.approx(1.0)


def test_hurdle_builder_preserves_point_and_variance_identity() -> None:
    paths = pl.DataFrame(
        {
            "as_of_date": [date(2025, 3, 27)],
            "player_id": [1],
            "season": [2025],
            "horizon": [1],
            "mlb_active_probability": [0.25],
            "conditional_pa": [400.0],
            "conditional_pa_variance": [100.0],
            "conditional_war_per_600": [3.0],
            "expected_war": [0.5],
            "event_run_variance": [1.0],
            "posterior_run_rate_variance": [0.01],
        }
    )
    result = build_component_hurdle_war_uncertainty(
        paths,
        component="hitter",
        conditional_workload_column="conditional_pa",
        conditional_workload_variance_column="conditional_pa_variance",
        conditional_war_rate_column="conditional_war_per_600",
        workload_unit=600.0,
        runs_per_win=10.0,
    )
    assert result.item(0, "projected_war_mean") == pytest.approx(0.5)
    assert result.item(0, "projected_war_lower") == 0.0
    assert result.item(0, "annual_war_variance") == pytest.approx(
        result.item(0, "opportunity_war_variance")
        + result.item(0, "performance_war_variance")
    )


def test_performance_scale_changes_variance_but_not_point() -> None:
    paths = pl.DataFrame(
        {
            "as_of_date": [date(2025, 3, 27)],
            "player_id": [1],
            "season": [2025],
            "horizon": [1],
            "mlb_active_probability": [0.8],
            "conditional_pa": [400.0],
            "conditional_pa_variance": [100.0],
            "conditional_war_per_600": [3.0],
            "expected_war": [1.6],
            "event_run_variance": [1.0],
            "posterior_run_rate_variance": [0.01],
        }
    )
    common = {
        "component": "hitter",
        "conditional_workload_column": "conditional_pa",
        "conditional_workload_variance_column": "conditional_pa_variance",
        "conditional_war_rate_column": "conditional_war_per_600",
        "workload_unit": 600.0,
        "runs_per_win": 10.0,
    }
    raw = build_component_hurdle_war_uncertainty(paths, **common)
    scaled = build_component_hurdle_war_uncertainty(
        paths, performance_standard_deviation_multiplier=1.25, **common
    )
    assert scaled.item(0, "projected_war_mean") == raw.item(0, "projected_war_mean")
    assert scaled.item(0, "performance_war_variance") > raw.item(
        0, "performance_war_variance"
    )


def test_exact_simulation_is_repeatable_and_preserves_point() -> None:
    paths = pl.DataFrame(
        {
            "as_of_date": [date(2025, 3, 27)],
            "player_id": [1],
            "season": [2025],
            "horizon": [1],
            "mlb_active_probability": [0.25],
            "conditional_pa": [400.0],
            "conditional_pa_variance": [50_000.0],
            "conditional_war_per_600": [3.0],
            "expected_war": [0.5],
            "event_run_variance": [1.0],
            "posterior_run_rate_variance": [0.01],
        }
    )
    kwargs = {
        "component": "hitter",
        "conditional_workload_column": "conditional_pa",
        "conditional_workload_variance_column": "conditional_pa_variance",
        "conditional_war_rate_column": "conditional_war_per_600",
        "workload_unit": 600.0,
        "runs_per_win": 10.0,
        "nb_alpha": 0.7,
        "draws": 10_000,
    }
    first = build_component_simulated_war_uncertainty(paths, **kwargs)
    second = build_component_simulated_war_uncertainty(paths, **kwargs)
    assert first.equals(second)
    assert first.item(0, "projected_war_mean") == pytest.approx(0.5)
    assert first.item(0, "projected_war_lower") == 0.0
    assert first.item(0, "projected_war_upper") >= first.item(
        0, "projected_war_mean"
    )
    assert first.item(0, "annual_war_variance") == pytest.approx(
        first.item(0, "opportunity_war_variance")
        + first.item(0, "performance_war_variance")
    )


def test_gamma_workload_and_single_component_whole_player_preserve_range() -> None:
    paths = pl.DataFrame(
        {
            "as_of_date": [date(2025, 3, 27)],
            "player_id": [1],
            "season": [2025],
            "horizon": [1],
            "mlb_active_probability": [0.8],
            "conditional_pa": [400.0],
            "conditional_pa_variance": [50_000.0],
            "conditional_war_per_600": [3.0],
            "expected_war": [1.6],
            "event_run_variance": [1.0],
            "posterior_run_rate_variance": [0.01],
        }
    )
    component = build_component_simulated_war_uncertainty(
        paths,
        component="hitter",
        conditional_workload_column="conditional_pa",
        conditional_workload_variance_column="conditional_pa_variance",
        conditional_war_rate_column="conditional_war_per_600",
        workload_unit=600.0,
        runs_per_win=10.0,
        draws=10_000,
    )
    whole = build_whole_player_from_component_intervals(component)
    assert whole.item(0, "projected_war_mean") == component.item(
        0, "projected_war_mean"
    )
    assert whole.item(0, "projected_war_lower") == component.item(
        0, "projected_war_lower"
    )
    assert whole.item(0, "projected_war_upper") == component.item(
        0, "projected_war_upper"
    )
