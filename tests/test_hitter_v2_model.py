import polars as pl
import pytest

from universal_baseball.hitter_v2_model import (
    marcel_age_factor,
    nested_empirical_bayes_probabilities,
    nested_empirical_bayes_probabilities_componentwise,
    NESTED_NODES,
    predict_b0_one_year_eb,
    predict_b1_marcel_345_k1200,
    predict_c0_nested_eb,
)
from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES


def _counts(**updates: int) -> dict[str, int]:
    values = {outcome: 0 for outcome in HITTER_TALENT_OUTCOMES}
    values.update({"K": 20, "UBB": 10, "HBP": 2, "OTHER_OUT": 68})
    values.update(updates)
    return values


def _history() -> pl.DataFrame:
    rows = []
    for player_id, season, counts in (
        (1, 2021, _counts(**{"HR": 20, "OTHER_OUT": 48})),
        (2, 2021, _counts(**{"1B": 20, "OTHER_OUT": 48})),
        (3, 2020, _counts()),
    ):
        rows.append(
            {
                "player_id": player_id,
                "season": season,
                "league_id": 103,
                "level_group": "MLB",
                "hitter_talent_pa": sum(counts.values()),
                "modeling_eligible": True,
                **counts,
            }
        )
    return pl.DataFrame(rows)


def test_nested_estimator_returns_complete_normalized_simplex() -> None:
    probabilities = nested_empirical_bayes_probabilities(_counts(), _counts())
    assert set(probabilities) == set(HITTER_TALENT_OUTCOMES)
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert all(value >= 0.0 for value in probabilities.values())


def test_terminal_power_history_changes_contact_quality_with_same_k_and_walks() -> None:
    predictions = predict_c0_nested_eb(
        _history(),
        [1, 2],
        predictor_cutoff_season=2021,
        half_life_seasons=2.0,
        component_prior_pa={"contact": 50.0, "hit_in_play": 50.0},
    )
    power = predictions.filter(pl.col("player_id") == 1).row(0, named=True)
    singles = predictions.filter(pl.col("player_id") == 2).row(0, named=True)

    assert power["p_K"] == pytest.approx(singles["p_K"])
    assert power["p_UBB"] == pytest.approx(singles["p_UBB"])
    assert power["p_HR"] > singles["p_HR"]
    assert singles["p_1B"] > power["p_1B"]


def test_future_history_is_rejected_before_prediction() -> None:
    with pytest.raises(ValueError, match="after the predictor cutoff"):
        predict_c0_nested_eb(
            _history(),
            [1],
            predictor_cutoff_season=2020,
            half_life_seasons=2.0,
        )


def test_unseen_player_receives_pooled_prior_without_zero_fill() -> None:
    prediction = predict_c0_nested_eb(
        _history().filter(pl.col("season") <= 2021),
        [999],
        predictor_cutoff_season=2021,
        half_life_seasons=2.0,
    ).row(0, named=True)

    assert prediction["prior_history_available"] is False
    assert prediction["prior_hitter_talent_pa"] == 0.0
    assert sum(prediction[f"p_{outcome}"] for outcome in HITTER_TALENT_OUTCOMES) == pytest.approx(1.0)


def test_b0_uses_only_the_prior_season() -> None:
    prediction = predict_b0_one_year_eb(
        _history(),
        [3],
        predictor_cutoff_season=2021,
    ).row(0, named=True)

    assert prediction["prior_history_available"] is False
    assert prediction["model_id"] == "B0_ONE_YEAR_EB"


def test_marcel_is_coherent_and_uses_fixed_age_rule() -> None:
    predictions = predict_b1_marcel_345_k1200(
        _history(),
        [1, 999],
        predictor_cutoff_season=2021,
        ages_at_target={1: 24.0},
    )
    known = predictions.filter(pl.col("player_id") == 1).row(0, named=True)
    unseen = predictions.filter(pl.col("player_id") == 999).row(0, named=True)

    assert known["marcel_age_factor"] == pytest.approx(1.03)
    assert marcel_age_factor(34.0) == pytest.approx(0.985)
    assert unseen["age_fallback"] == "neutral_missing_age"
    for row in (known, unseen):
        assert sum(row[f"p_{outcome}"] for outcome in HITTER_TALENT_OUTCOMES) == pytest.approx(1.0)


def test_component_specific_history_and_half_life_remain_coherent() -> None:
    common = _counts()
    power = _counts(**{"HR": 20, "OTHER_OUT": 48})
    histories = {node.name: common for node in NESTED_NODES}
    histories["contact"] = power
    probabilities = nested_empirical_bayes_probabilities_componentwise(
        histories,
        common,
        component_prior_pa={"contact": 50.0},
    )
    assert sum(probabilities.values()) == pytest.approx(1.0)
    assert probabilities["HR"] > nested_empirical_bayes_probabilities(
        common, common, component_prior_pa={"contact": 50.0}
    )["HR"]

    half_lives = {node.name: 3.0 for node in NESTED_NODES}
    half_lives["contact"] = 1.0
    prediction = predict_c0_nested_eb(
        _history(),
        [1],
        predictor_cutoff_season=2021,
        half_life_seasons=half_lives,
    ).row(0, named=True)
    assert sum(
        prediction[f"p_{outcome}"] for outcome in HITTER_TALENT_OUTCOMES
    ) == pytest.approx(1.0)
