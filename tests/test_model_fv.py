import polars as pl

from universal_baseball.model_fv import build_model_fv


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
