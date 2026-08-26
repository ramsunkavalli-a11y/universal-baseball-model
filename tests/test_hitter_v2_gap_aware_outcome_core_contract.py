import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_gap_aware_contract_keeps_history_and_later_increments_separate() -> None:
    contract = json.loads(
        (ROOT / "docs/hitter-v2-gap-aware-outcome-core-contract.json").read_text()
    )
    assert contract["candidate"]["model_id"] == "G0_GAP_AWARE_HISTORICAL_C0"
    assert contract["candidate"]["new_predictors"] == []
    assert contract["historical_source_policy"]["2020_milb"].startswith(
        "missing_observation_gap"
    )
    assert contract["candidate"]["hyperparameter_search"] is False
    assert contract["protected_2026_access_authorized"] is False
    assert [row["model_id"] for row in contract["later_increment_ladder"]] == [
        "G1_PRIOR_OPPONENT_QUALITY_RESIDUAL",
        "G2_CONTACT_PROCESS_RESIDUAL",
        "G3_LAGGED_LINEUP_BELIEF_PRIOR",
        "G4_PHYSICAL_SIMILARITY_PRIOR",
    ]


def test_gap_aware_authorization_does_not_open_later_gates() -> None:
    authorization = json.loads(
        (ROOT / "docs/hitter-v2-gap-aware-outcome-core-authorization.json").read_text()
    )
    assert authorization["candidate_fit_authorized"] is True
    assert authorization["protected_2026_opened"] is False
    assert "automatic_G1_or_later_increment_fit" in authorization["not_authorized"]
