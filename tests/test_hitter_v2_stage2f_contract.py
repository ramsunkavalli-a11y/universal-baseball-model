from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/hitter-v2-stage2f-development-contract.json"


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_stage2f_is_frozen_but_every_execution_gate_is_closed() -> None:
    contract = _contract()
    assert contract["status"] == "frozen_before_candidate_implementation_fit_or_score"
    authorization = contract["authorization"]
    assert authorization["contract_frozen"] is True
    assert authorization["target_free_implementation_authorized"] is False
    assert authorization["candidate_fit_authorized"] is False
    assert authorization["candidate_scoring_authorized"] is False
    assert authorization["protected_2026_access_authorized"] is False
    assert authorization["full_WAR_authorized"] is False


def test_H0_is_distinct_and_H1_cannot_rescue_it() -> None:
    contract = _contract()
    ladder = contract["candidate_ladder"]
    assert ladder[0]["model_id"] == "H0_NEUTRAL_HIERARCHICAL_OUTCOMES"
    assert ladder[1]["authorized_only_if_H0_passes"] is True
    assert ladder[1]["cannot_rescue_failed_H0"] is True
    assert contract["H0_model"]["opponent_context_increment"] is False
    assert contract["failure_policy"]["H1_after_H0_failure"] is False


def test_target_and_contact_fallback_boundaries_are_explicit() -> None:
    contract = _contract()
    target = contract["target_construct"]
    assert target["target_level_as_predictor"] is False
    assert (
        target["target_membership_playing_time_park_or_environment_as_predictor"]
        is False
    )
    contact = contract["H1_contact_increment"]
    assert contact["authorized_now"] is False
    assert contact["missing_shape"] == "exact_H0_prediction"
    assert contact["identical_overlap_comparison"] is True
    assert (
        contact["all_ten_percentages_as_unrestricted_multinomial_adjustment"] is False
    )
