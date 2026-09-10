import polars as pl

from universal_baseball.opportunity_v2_confirmation import (
    evaluate_opportunity_confirmation,
)


def _predictions(probability: list[float], positive_mean: list[float]) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "player_id": [1, 2, 3, 4],
            "predicted_any_mlb_pa_probability": probability,
            "predicted_positive_mlb_pa_mean": positive_mean,
            "predicted_expected_mlb_pa": [
                probability[index] * positive_mean[index] for index in range(4)
            ],
            "model_nb_alpha": [0.7] * 4,
        }
    )


def test_fixed_confirmation_rule_passes_better_selected_model() -> None:
    targets = pl.DataFrame(
        {"player_id": [1, 2, 3, 4], "observed_mlb_pa": [0, 100, 200, 0]}
    )
    selected = _predictions([0.05, 0.9, 0.9, 0.05], [100, 110, 220, 100])
    baseline = _predictions([0.2, 0.7, 0.7, 0.2], [150, 150, 200, 150])
    incumbent = _predictions([0.3, 0.6, 0.6, 0.3], [100, 100, 180, 100]).drop(
        "model_nb_alpha"
    )

    result = evaluate_opportunity_confirmation(
        selected,
        baseline,
        incumbent,
        targets,
        component="hitter",
        unit="pa",
    )

    assert result.confirmed is True
    assert all(result.gates.values())
    assert result.metrics.height == 3
    assert "opportunity_mse" in result.metrics.columns
    assert "mse_no_worse_than_incumbent" in result.gates
    assert "mae_no_worse_than_incumbent" not in result.gates


def test_fixed_confirmation_rule_fails_worse_selected_model() -> None:
    targets = pl.DataFrame(
        {"player_id": [1, 2, 3, 4], "observed_mlb_pa": [0, 100, 200, 0]}
    )
    selected = _predictions([0.4, 0.5, 0.5, 0.4], [200, 100, 100, 200])
    baseline = _predictions([0.05, 0.9, 0.9, 0.05], [100, 110, 220, 100])
    incumbent = baseline.drop("model_nb_alpha")

    result = evaluate_opportunity_confirmation(
        selected,
        baseline,
        incumbent,
        targets,
        component="hitter",
        unit="pa",
    )

    assert result.confirmed is False
    assert not all(result.gates.values())
