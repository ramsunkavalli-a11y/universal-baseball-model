from __future__ import annotations

import polars as pl

from universal_baseball.model_law_audit import audit_private_preview_laws
from universal_baseball.prospect_value import display_fv, model_fv_from_expected_war


def test_private_preview_laws_detect_clean_minimal_build() -> None:
    seasons = list(range(2027, 2033))
    hitter = pl.DataFrame(
        {
            "player_id": [1] * 6, "season": seasons,
            "mlb_active_probability": [0.5] * 6,
            "conditional_mlb_pa": [400.0] * 6, "expected_mlb_pa": [200.0] * 6,
            "conditional_war_per_600_pa": [3.0] * 6, "expected_war": [1.0] * 6,
            "predicted_ubb_rate": [.1] * 6, "predicted_hbp_rate": [.01] * 6,
            "predicted_single_rate": [.14] * 6, "predicted_double_rate": [.04] * 6,
            "predicted_triple_rate": [.01] * 6, "predicted_hr_rate": [.04] * 6,
            "predicted_other_rate": [.66] * 6,
        }
    )
    pitcher = pl.DataFrame(
        {
            "player_id": [2] * 6, "season": seasons,
            "mlb_active_probability": [.5] * 6,
            "conditional_mlb_bf": [400.0] * 6, "expected_mlb_bf": [200.0] * 6,
            "conditional_war_per_800_bf": [4.0] * 6, "expected_war": [1.0] * 6,
            "predicted_other_rate": [.65] * 6, "predicted_so_rate": [.22] * 6,
            "predicted_ubb_rate": [.08] * 6, "predicted_hbp_rate": [.01] * 6,
            "predicted_hr_rate": [.04] * 6,
            "starter_probability_if_active": [.5] * 6,
            "swingman_probability_if_active": [.2] * 6,
            "reliever_probability_if_active": [.3] * 6,
        }
    )
    war = 2.0
    granular = model_fv_from_expected_war(war, "hitter")
    nested = pl.DataFrame(
        {
            "player_id": [1], "hitter_path_rows": [6], "pitcher_path_rows": [0],
            "model_player_type": ["hitter"], "ordered_arrival_probability": [.5],
            "ordered_meaningful_probability": [.3], "ordered_established_probability": [.1],
            "fringe_probability": [.2], "meaningful_only_probability": [.2],
            "established_probability": [.1], "three_tier_expected_six_year_war": [war],
            "three_tier_model_fv_granular": [granular],
            "three_tier_model_fv_display": [display_fv(granular)],
        }
    )
    values = pl.DataFrame(
        {
            "player_id": [1], "expected_remaining_war_lower": [1.0],
            "expected_remaining_war": [2.0], "expected_remaining_war_upper": [3.0],
            "transferable_value_lower_dollars": [-1.0],
            "transferable_value_dollars": [2.0],
            "transferable_value_upper_dollars": [4.0],
        }
    )
    result = audit_private_preview_laws(hitter, pitcher, nested, values)
    assert result["failed"] == 0


def test_private_preview_laws_catch_probability_and_interval_breaks() -> None:
    # Start with the clean fixture and corrupt two independent laws.
    seasons = list(range(2027, 2033))
    hitter = pl.DataFrame({
        "player_id": [1] * 6, "season": seasons, "mlb_active_probability": [1.2] * 6,
        "conditional_mlb_pa": [100.0] * 6, "expected_mlb_pa": [120.0] * 6,
        "conditional_war_per_600_pa": [0.0] * 6, "expected_war": [0.0] * 6,
        "predicted_ubb_rate": [.1] * 6, "predicted_hbp_rate": [.01] * 6,
        "predicted_single_rate": [.14] * 6, "predicted_double_rate": [.04] * 6,
        "predicted_triple_rate": [.01] * 6, "predicted_hr_rate": [.04] * 6,
        "predicted_other_rate": [.66] * 6,
    })
    pitcher = pl.DataFrame({
        "player_id": [2] * 6, "season": seasons, "mlb_active_probability": [.5] * 6,
        "conditional_mlb_bf": [400.0] * 6, "expected_mlb_bf": [200.0] * 6,
        "conditional_war_per_800_bf": [4.0] * 6, "expected_war": [1.0] * 6,
        "predicted_other_rate": [.65] * 6, "predicted_so_rate": [.22] * 6,
        "predicted_ubb_rate": [.08] * 6, "predicted_hbp_rate": [.01] * 6,
        "predicted_hr_rate": [.04] * 6, "starter_probability_if_active": [.5] * 6,
        "swingman_probability_if_active": [.2] * 6, "reliever_probability_if_active": [.3] * 6,
    })
    granular = model_fv_from_expected_war(1.0, "hitter")
    nested = pl.DataFrame({
        "player_id": [1], "hitter_path_rows": [6], "pitcher_path_rows": [0],
        "model_player_type": ["hitter"], "ordered_arrival_probability": [.4],
        "ordered_meaningful_probability": [.5], "ordered_established_probability": [.1],
        "fringe_probability": [-.1], "meaningful_only_probability": [.4],
        "established_probability": [.1], "three_tier_expected_six_year_war": [1.0],
        "three_tier_model_fv_granular": [granular],
        "three_tier_model_fv_display": [display_fv(granular)],
    })
    values = pl.DataFrame({
        "player_id": [1], "expected_remaining_war_lower": [3.0],
        "expected_remaining_war": [2.0], "expected_remaining_war_upper": [1.0],
        "transferable_value_lower_dollars": [0.0], "transferable_value_dollars": [1.0],
        "transferable_value_upper_dollars": [2.0],
    })
    result = audit_private_preview_laws(hitter, pitcher, nested, values)
    failed = {check["name"] for check in result["checks"] if check["status"] == "fail"}
    assert "hitter_active_probability_bounds" in failed
    assert "nested_probability_order_and_partition" in failed
    assert "current_value_interval_order" in failed
