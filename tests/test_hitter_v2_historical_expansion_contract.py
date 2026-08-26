from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_historical_expansion_authorization_is_source_only() -> None:
    payload = json.loads(
        (ROOT / "docs" / "hitter-v2-historical-expansion-authorization.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["parent_commit"] == "91661ee1154b2bfabd2a144ae6fbcd7977bebf39"
    assert "candidate fitting or scoring" in payload["not_authorized"]
    assert "bulk historical materialization" in payload["not_authorized"]
    assert payload["protected_target_policy"]["protected_season"] == 2026
    assert payload["protected_target_policy"]["outcome_payload_access"] == "forbidden"


def test_historical_expansion_contract_preserves_2020_distinction() -> None:
    text = (
        ROOT / "docs" / "hitter-v2-historical-expansion-source-contract.md"
    ).read_text(encoding="utf-8")
    assert "no affiliated MiLB season occurred" in text
    assert "MLB played a shortened 2020 regular season" in text
    assert "missing 2020 MiLB season must" in text
    assert "not zero talent" in text
    assert "exhibition- and postseason-only filename periods" in text


def test_historical_expansion_result_is_compatible_but_not_model_authority() -> None:
    payload = json.loads(
        (
            ROOT
            / "docs"
            / "hitter-v2-historical-expansion-audit-result.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["representative_audit"]["sample_pair_count"] == 9
    assert payload["representative_audit"]["compatible_sample_pair_count"] == 9
    assert payload["representative_audit"]["same_game_league_authority_missing_game_count"] == 0
    assert payload["candidate_fit"] is False
    assert payload["candidate_scored"] is False
    assert payload["protected_2026_outcome_payload_accessed"] is False
    assert payload["decision"]["model_use"] == "not authorized"


def test_workflow_status_distinguishes_completed_source_from_model_use() -> None:
    payload = json.loads(
        (ROOT / "docs" / "hitter-v2-workflow-status.json").read_text(
            encoding="utf-8"
        )
    )
    expansion = payload["historical_source_expansion"]
    assert expansion["representative_milb_compatibility_passed"] is True
    assert expansion["candidate_fit"] is False
    assert expansion["full_2019_milb_materialization_complete"] is True
    assert expansion["mlb_2020_source_certification_complete"] is True
    assert expansion["historical_model_use_authorized"] is False
    assert payload["authorization"]["2026_confirmation_access_authorized"] is False
