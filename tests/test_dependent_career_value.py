import polars as pl
import pytest

from universal_baseball.cba_rules import build_post_2026_cba_planning_scenario
from universal_baseball.dependent_career_value import (
    simulate_dependent_pre_mlb_value,
)


def _annual_paths() -> pl.DataFrame:
    rows = []
    for player_id, tier, workload in (
        (10, "fringe", [50, 0, 0, 0, 0, 0]),
        (11, "meaningful_only", [200, 0, 200, 0, 0, 0]),
        (12, "established", [550, 550, 550, 550, 550, 550]),
    ):
        for index, value in enumerate(workload, 1):
            rows.append(
                {
                    "path_player_id": player_id,
                    "player_type": "hitter",
                    "outcome_tier_v2": tier,
                    "career_role": "hitter",
                    "path_year": index,
                    "adjusted_workload": float(value),
                    "annual_role": "hitter" if value else "inactive",
                    "window_end_year": 2020,
                }
            )
    return pl.DataFrame(rows)


def _nested(arrival: float = 1.0) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1],
            "model_player_type": ["hitter"],
            "primary_position": ["1B"],
            "ordered_arrival_probability": [arrival],
            "fringe_probability": [0.0],
            "meaningful_only_probability": [0.0],
            "established_probability": [arrival],
            "starter_probability": [0.0],
            "reliever_probability": [0.0],
            "hitter_six_control_year_war_if_arrived": [6.6],
            "pitcher_six_control_year_war_if_arrived": [0.0],
        }
    )


def _nested_for_tier(tier: str, *, full_war: float = 6.6) -> pl.DataFrame:
    result = _nested().with_columns(
        pl.lit(full_war).alias("hitter_six_control_year_war_if_arrived")
    )
    for name in ("fringe", "meaningful_only", "established"):
        result = result.with_columns(
            pl.lit(1.0 if name == tier else 0.0).alias(f"{name}_probability")
        )
    return result


def _rates() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1],
            "event_run_variance": [0.0],
            "posterior_run_rate_variance": [0.0],
        }
    )


def test_dependent_simulation_preserves_whole_career_shape_and_is_repeatable() -> None:
    market = {
        season: {"0-1": 10_000_000.0, "1-2": 10_000_000.0, "2+": 10_000_000.0}
        for season in range(2027, 2038)
    }
    kwargs = {
        "forecast_seasons": tuple(range(2027, 2038)),
        "cba_ruleset": build_post_2026_cba_planning_scenario(end_year=2037),
        "market_rates": market,
        "arbitration_shares": {1: 0.15, 2: 0.35, 3: 0.50, 4: 0.75},
        "runs_per_win": 10.0,
        "annual_discount_rate": 0.0,
        "minimum_role_players": 1,
        "draws": 64,
    }
    first = simulate_dependent_pre_mlb_value(
        _nested(), _annual_paths(), _rates(), _rates(), **kwargs
    )
    second = simulate_dependent_pre_mlb_value(
        _nested(), _annual_paths(), _rates(), _rates(), **kwargs
    )
    assert first.equals(second)
    assert first.item(0, "mean_controlled_war") == pytest.approx(6.6)
    assert first.item(0, "arrival_probability") == 1.0
    assert first.item(0, "no_arrival_probability") == 0.0
    assert first.item(0, "regular_probability") == 1.0
    assert first.item(0, "conditional_mean_arrival_year") == 2027.0
    assert first.item(0, "mean_discounted_surplus_value_dollars") > 0.0


def test_zero_arrival_produces_zero_war_cost_and_value() -> None:
    market = {
        season: {"0-1": 1.0, "1-2": 1.0, "2+": 1.0}
        for season in range(2027, 2038)
    }
    result = simulate_dependent_pre_mlb_value(
        _nested(0.0),
        _annual_paths(),
        _rates(),
        _rates(),
        forecast_seasons=tuple(range(2027, 2038)),
        cba_ruleset=build_post_2026_cba_planning_scenario(end_year=2037),
        market_rates=market,
        arbitration_shares={1: 0.15, 2: 0.35, 3: 0.50, 4: 0.75},
        runs_per_win=10.0,
        minimum_role_players=1,
        draws=32,
    )
    assert result.item(0, "mean_controlled_war") == 0.0
    assert result.item(0, "expected_discounted_cost_dollars") == 0.0
    assert result.item(0, "mean_discounted_surplus_value_dollars") == 0.0
    assert result.item(0, "bust_probability") == 1.0


def test_inactive_year_does_not_consume_control_and_later_return_is_kept() -> None:
    market = {
        season: {"0-1": 10_000_000.0, "1-2": 10_000_000.0, "2+": 10_000_000.0}
        for season in range(2027, 2038)
    }
    rules = build_post_2026_cba_planning_scenario(end_year=2037)
    result = simulate_dependent_pre_mlb_value(
        _nested_for_tier("meaningful_only"),
        _annual_paths(),
        _rates(),
        _rates(),
        forecast_seasons=tuple(range(2027, 2038)),
        cba_ruleset=rules,
        market_rates=market,
        arbitration_shares={1: 0.15, 2: 0.35, 3: 0.50, 4: 0.75},
        runs_per_win=10.0,
        annual_discount_rate=0.0,
        minimum_role_players=1,
        draws=32,
    )
    assert result.item(0, "mean_controlled_war") == pytest.approx(0.8)
    assert result.item(0, "expected_discounted_cost_dollars") == pytest.approx(
        rules.minimum_salary(2027) + rules.minimum_salary(2029)
    )


def test_negative_war_is_not_clipped_and_creates_negative_surplus() -> None:
    market = {
        season: {"0-1": 10_000_000.0, "1-2": 10_000_000.0, "2+": 10_000_000.0}
        for season in range(2027, 2038)
    }
    result = simulate_dependent_pre_mlb_value(
        _nested_for_tier("established", full_war=-6.6),
        _annual_paths(),
        _rates(),
        _rates(),
        forecast_seasons=tuple(range(2027, 2038)),
        cba_ruleset=build_post_2026_cba_planning_scenario(end_year=2037),
        market_rates=market,
        arbitration_shares={1: 0.15, 2: 0.35, 3: 0.50, 4: 0.75},
        runs_per_win=10.0,
        annual_discount_rate=0.0,
        minimum_role_players=1,
        draws=32,
    )
    assert result.item(0, "mean_controlled_war") == pytest.approx(-6.6)
    assert result.item(0, "mean_discounted_surplus_value_dollars") < 0.0


def test_extended_cba_scenario_preserves_declared_three_percent_path() -> None:
    scenario = build_post_2026_cba_planning_scenario(end_year=2037)
    assert scenario.ruleset_kind == "research_planning_scenario_not_cba_fact"
    assert scenario.minimum_salary(2027) == 803_400
    assert scenario.minimum_salary(2037) > scenario.minimum_salary(2032)
