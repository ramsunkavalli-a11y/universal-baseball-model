import polars as pl
import pytest

from universal_baseball.model_fv import (
    apply_pre_mlb_outcome_quality_workload,
    apply_pre_mlb_three_tier_workload,
    build_model_fv,
)


def test_model_fv_combines_two_way_production_and_keeps_role() -> None:
    hitters = pl.DataFrame(
        {
            "player_id": [1, 1, 2], "season": [2027, 2028, 2027],
            "expected_war": [3.0, 4.0, 0.0], "primary_position": ["SS", "SS", None],
            "mlb_active_probability": [1.0, 1.0, 0.0],
            "conditional_war_per_600_pa": [3.0, 4.0, 0.0],
        }
    )
    pitchers = pl.DataFrame(
        {
            "player_id": [1, 2, 2], "season": [2027, 2027, 2028],
            "expected_war": [0.0, 2.5, 2.5],
            "starter_probability_if_active": [0.0, 0.8, 0.8],
            "swingman_probability_if_active": [0.0, 0.0, 0.0],
            "reliever_probability_if_active": [1.0, 0.2, 0.2],
            "mlb_active_probability": [0.0, 1.0, 1.0],
            "conditional_war_per_800_bf": [0.0, 2.5, 2.5],
        }
    )
    uncertainty = pl.DataFrame(
        {
            "player_id": [1, 1, 2, 2], "season": [2027, 2028, 2027, 2028],
            "annual_war_variance": [1.0, 1.0, 1.0, 1.0],
        }
    )
    result = build_model_fv(hitters, pitchers, uncertainty)
    hitter = result.filter(pl.col("player_id") == 1).row(0, named=True)
    pitcher = result.filter(pl.col("player_id") == 2).row(0, named=True)
    assert hitter["expected_six_year_war"] == 7.0
    assert hitter["model_fv_display"] == 50
    assert hitter["model_role"] == "SS"
    assert pitcher["model_fv_display"] == 50
    assert pitcher["model_role"] == "starter"


def test_pre_mlb_fv_uses_six_control_years_after_arrival() -> None:
    hitters = pl.DataFrame(
        {
            "player_id": [3, 3], "season": [2027, 2028],
            "expected_war": [0.1, 0.2], "primary_position": ["CF", "CF"],
            "mlb_active_probability": [0.2, 0.25],
            "conditional_war_per_600_pa": [3.0, 3.0],
        }
    )
    pitchers = pl.DataFrame(
        schema={
            "player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64,
            "mlb_active_probability": pl.Float64,
            "conditional_war_per_800_bf": pl.Float64,
            "starter_probability_if_active": pl.Float64,
            "swingman_probability_if_active": pl.Float64,
            "reliever_probability_if_active": pl.Float64,
        }
    )
    uncertainty = pl.DataFrame(
        {"player_id": [3, 3], "season": [2027, 2028], "annual_war_variance": [1.0, 1.0]}
    )
    result = build_model_fv(
        hitters, pitchers, uncertainty, pre_mlb_player_ids={3}
    ).row(0, named=True)
    assert abs(result["expected_six_year_war"] - 1.375) < 1e-12
    assert result["outcome_method"] == "six_control_years_after_probabilistic_arrival"
    assert result["model_arrival_probability"] == 0.25
    assert result["arrival_probability_source"] == "maximum_annual_probability_fallback"


def test_negative_pitcher_path_cannot_turn_pitcher_into_hitter() -> None:
    hitters = pl.DataFrame(
        schema={
            "player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64,
            "primary_position": pl.String, "mlb_active_probability": pl.Float64,
            "conditional_war_per_600_pa": pl.Float64,
        }
    )
    pitchers = pl.DataFrame(
        {
            "player_id": [4], "season": [2027], "expected_war": [-0.5],
            "starter_probability_if_active": [0.2],
            "swingman_probability_if_active": [0.1],
            "reliever_probability_if_active": [0.7],
            "mlb_active_probability": [0.5],
            "conditional_war_per_800_bf": [-1.0],
        }
    )
    uncertainty = pl.DataFrame(
        {"player_id": [4], "season": [2027], "annual_war_variance": [1.0]}
    )
    result = build_model_fv(hitters, pitchers, uncertainty).row(0, named=True)
    assert result["model_player_type"] == "pitcher"
    assert result["model_role"] == "reliever"


def test_pre_mlb_fv_prefers_historical_arrival_probability() -> None:
    hitters = pl.DataFrame(
        {
            "player_id": [3, 3], "season": [2027, 2028],
            "expected_war": [0.1, 0.2], "primary_position": ["CF", "CF"],
            "mlb_active_probability": [0.2, 0.25],
            "conditional_war_per_600_pa": [3.0, 3.0],
        }
    )
    pitchers = pl.DataFrame(
        schema={
            "player_id": pl.Int64, "season": pl.Int64, "expected_war": pl.Float64,
            "mlb_active_probability": pl.Float64,
            "conditional_war_per_800_bf": pl.Float64,
            "starter_probability_if_active": pl.Float64,
            "swingman_probability_if_active": pl.Float64,
            "reliever_probability_if_active": pl.Float64,
        }
    )
    uncertainty = pl.DataFrame(
        {"player_id": [3, 3], "season": [2027, 2028], "annual_war_variance": [1.0, 1.0]}
    )
    result = build_model_fv(
        hitters,
        pitchers,
        uncertainty,
        pre_mlb_player_ids={3},
        pre_mlb_arrival_probabilities={("hitter", 3): 0.5},
        pre_mlb_meaningful_role_probabilities={("hitter", 3): 0.3},
    ).row(0, named=True)
    assert abs(result["expected_six_year_war"] - 2.75) < 1e-12
    assert result["model_arrival_probability"] == 0.5
    assert result["model_meaningful_role_probability"] == 0.3
    assert result["arrival_probability_source"] == "historical_two_year_arrival_survival"


def test_outcome_quality_challenger_uses_disjoint_fringe_and_meaningful_paths() -> None:
    values = pl.DataFrame(
        {
            "player_id": [3], "model_player_type": ["hitter"],
            "model_arrival_probability": [0.5],
            "model_meaningful_role_probability": [0.2],
            "expected_six_year_war": [3.0],
            "hitter_six_control_year_war_if_arrived": [6.0],
            "pitcher_six_control_year_war_if_arrived": [None],
            "primary_position": ["CF"], "starter_probability": [None],
            "reliever_probability": [None], "model_fv_granular": [45.0],
            "model_fv_display": [45],
        }
    )
    priors = pl.DataFrame(
        {
            "player_type": ["hitter", "hitter"],
            "outcome_tier": ["fringe", "meaningful"],
            "career_role": ["hitter", "hitter"],
            "players": [200, 200],
            "mean_workload": [60.0, 2_000.0],
        }
    )
    result = apply_pre_mlb_outcome_quality_workload(
        values, priors, pre_mlb_player_ids={3}
    ).row(0, named=True)
    expected_workload = 0.3 * 60.0 + 0.2 * 2_000.0
    assert result["outcome_quality_expected_workload"] == expected_workload
    assert result["outcome_quality_expected_six_year_war"] == (
        6.0 / 3_300.0 * expected_workload
    )
    assert result["outcome_quality_expected_six_year_war"] < 3.0


def test_three_tier_challenger_orders_probabilities_and_uses_disjoint_paths() -> None:
    values = pl.DataFrame(
        {
            "player_id": [3], "model_player_type": ["hitter"],
            "model_arrival_probability": [0.5],
            "model_meaningful_role_probability": [0.4],
            # Deliberately above meaningful; logical ordering must constrain it.
            "model_established_role_probability": [0.45],
            "expected_six_year_war": [3.0],
            "hitter_six_control_year_war_if_arrived": [6.0],
            "pitcher_six_control_year_war_if_arrived": [None],
            "primary_position": ["CF"], "starter_probability": [None],
            "reliever_probability": [None], "model_fv_granular": [45.0],
            "model_fv_display": [45],
        }
    )
    priors = pl.DataFrame(
        {
            "player_type": ["hitter"] * 3,
            "outcome_tier": ["fringe", "meaningful_only", "established"],
            "career_role": ["hitter"] * 3,
            "players": [200, 100, 100],
            "mean_workload": [60.0, 600.0, 2_500.0],
        }
    )
    result = apply_pre_mlb_three_tier_workload(
        values, priors, pre_mlb_player_ids={3}
    ).row(0, named=True)
    assert result["fringe_probability"] == pytest.approx(0.1)
    assert result["meaningful_only_probability"] == 0.0
    assert result["established_probability"] == 0.4
    expected_workload = 0.1 * 60.0 + 0.4 * 2_500.0
    assert result["three_tier_expected_workload"] == expected_workload
    assert result["three_tier_expected_six_year_war"] == (
        6.0 / 3_300.0 * expected_workload
    )
