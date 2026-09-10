import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_hitter_demographic_candidate_is_rejected_on_confirmation() -> None:
    result = json.loads(
        (ROOT / "docs/hitter-age-level-batting-side-result.json").read_text(
            encoding="utf-8"
        )
    )
    confirmation = result["confirmation_2025"]
    assert result["development_2024"]["selected_family"] == "age_side_interaction"
    assert confirmation["candidate_minus_incumbent_log_loss"] > 0
    assert confirmation["candidate_minus_incumbent_brier"] > 0
    assert result["decision"]["promoted"] is False
    assert result["boundaries"]["current_2026_outcomes_used"] is False
    assert result["boundaries"]["current_values_changed"] is False
