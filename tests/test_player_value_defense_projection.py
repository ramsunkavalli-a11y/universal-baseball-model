from __future__ import annotations

from universal_baseball.player_value_defense_projection import (
    predict_catcher_c2_skill,
    predict_framing_skill,
    predict_general_range_skill,
)


def _general_parameters() -> dict[str, object]:
    moments = [
        {"feature": feature, "position": "SS", "level_group": "MLB", "mean": 1.0, "sd": 2.0}
        for feature in (
            "fielding_pct",
            "range_factor_per_9",
            "errors_per_9",
            "throwing_errors_per_9",
        )
    ]
    return {
        "normalization": {"cell": moments, "position": [], "global": []},
        "tracked_mlb": {"coefficients": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]},
        "universal": {"coefficients": [1.0, 2.0, 3.0, 4.0, 5.0]},
    }


def _profile(**updates: object) -> dict[str, object]:
    result: dict[str, object] = {
        "position": "SS",
        "fielding_outs": 500,
        "chances": 200,
        "current_level_group": "MLB",
        "fielding_pct": 3.0,
        "range_factor_per_9": 3.0,
        "errors_per_9": 3.0,
        "throwing_errors_per_9": 3.0,
    }
    result.update(updates)
    return result


def test_general_range_uses_frozen_t1_u1_b0_hierarchy() -> None:
    parameters = _general_parameters()
    assert predict_general_range_skill(_profile(), tracked_z=2.0, parameters=parameters) == (
        27.0,
        "T1",
    )
    assert predict_general_range_skill(_profile(), tracked_z=None, parameters=parameters) == (
        15.0,
        "U1",
    )
    assert predict_general_range_skill(
        _profile(fielding_outs=299), tracked_z=2.0, parameters=parameters
    ) == (0.0, "B0")


def test_repaired_catcher_throwing_weights_by_steal_attempts() -> None:
    parameters = {
        "feature": "caught_stealing_pct",
        "normalization": {"mean": 0.25, "sd": 0.05},
        "prior_season_recency_weight": 0.5,
        "coefficients": [0.1, 0.5],
    }
    current = {
        "fielding_outs": 900,
        "steal_attempts": 10,
        "caught_stealing_pct": 0.30,
    }
    prior = {
        "fielding_outs": 300,
        "steal_attempts": 20,
        "caught_stealing_pct": 0.20,
    }
    # Equal effective steal-attempt exposure makes the feature z-score zero.
    assert predict_catcher_c2_skill(
        current, prior, parameters=parameters, component="throwing"
    ) == (0.1, "C2")


def test_framing_requires_eligible_mlb_tracking() -> None:
    parameters = {"coefficients": [-0.25, 0.75]}
    current = {"fielding_outs": 600, "current_level_group": "MLB"}
    assert predict_framing_skill(current, tracked_z=2.0, parameters=parameters) == (
        1.25,
        "F1",
    )
    assert predict_framing_skill(current, tracked_z=None, parameters=parameters) == (
        0.0,
        "F0",
    )
