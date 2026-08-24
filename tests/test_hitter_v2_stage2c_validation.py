import polars as pl

from universal_baseball.hitter_v2_stage2c_validation import (
    hr_increment_gate,
    pooled_rate_gate,
    score_hr_conditional,
)


def _prediction(player_id: int, hr: float) -> dict[str, float | int]:
    non_hr = 1.0 - hr
    return {
        "player_id": player_id,
        "p_K": 0.0,
        "p_UBB": 0.0,
        "p_HBP": 0.0,
        "p_HR": hr,
        "p_3B": 0.0,
        "p_2B": 0.0,
        "p_1B": non_hr,
        "p_ROE": 0.0,
        "p_FC_REACH": 0.0,
        "p_SF": 0.0,
        "p_MULTI_OUT": 0.0,
        "p_OTHER_OUT": 0.0,
    }


def _target() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {"player_id": 1, "HR": 1, "1B": 9},
            {"player_id": 2, "HR": 9, "1B": 1},
        ]
    ).with_columns(
        *[
            pl.lit(0).alias(outcome)
            for outcome in ("K", "UBB", "HBP", "3B", "2B", "ROE", "FC_REACH", "SF", "MULTI_OUT", "OTHER_OUT")
        ]
    )


def test_hr_conditional_score_rewards_better_probabilities() -> None:
    target = _target()
    good = score_hr_conditional(
        pl.DataFrame([_prediction(1, 0.1), _prediction(2, 0.9)]),
        target,
        weighting="pa",
    )
    bad = score_hr_conditional(
        pl.DataFrame([_prediction(1, 0.5), _prediction(2, 0.5)]),
        target,
        weighting="pa",
    )
    assert good["hr_conditional_log_loss"] < bad["hr_conditional_log_loss"]
    assert good["hr_conditional_brier"] < bad["hr_conditional_brier"]


def test_hr_increment_gate_is_strict() -> None:
    base = {"hr_conditional_log_loss": 0.5}
    assert hr_increment_gate({"hr_conditional_log_loss": 0.49}, base)["pass"] is True
    assert hr_increment_gate({"hr_conditional_log_loss": 0.5}, base)["pass"] is False


def test_pooled_rate_gate_requires_both_rate_metrics() -> None:
    baseline = {"woba_rmse": 0.04, "runs_per_600_rmse": 20.0}
    candidate = {"woba_rmse": 0.039, "runs_per_600_rmse": 20.1}
    assert pooled_rate_gate(candidate, baseline, baseline)["pass"] is False
