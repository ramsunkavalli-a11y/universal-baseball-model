from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_historical_mlb_source_allows_bridge_era_without_model_authority() -> None:
    text = (
        ROOT / "scripts" / "materialize_current_talent_historical_mlb_game_evidence.py"
    ).read_text(encoding="utf-8")
    assert "if season < 2019" in text
    assert '"candidate_fit": False' in text
    assert '"candidate_scored": False' in text
    assert '"model_use_authorized": False' in text
    assert '"protected_2026_opened": False' in text


def test_manual_historical_mlb_workflow_exposes_2020_choice() -> None:
    text = (
        ROOT / ".github" / "workflows" / "current-talent-historical-mlb-season.yml"
    ).read_text(encoding="utf-8")
    assert '          - "2019"' in text
    assert '          - "2020"' in text
    assert "workflow_dispatch:" in text
