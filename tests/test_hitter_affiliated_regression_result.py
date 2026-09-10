import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_hitter_regression_challenger_fails_uncertainty_gate() -> None:
    result = json.loads(
        (ROOT / "docs/hitter-affiliated-regression-audit-result.json").read_text(
            encoding="utf-8"
        )
    )
    assert result["selection"]["selected_regression_pa"] == 400
    confirmation = result["confirmation_2025"]
    assert confirmation["selected_minus_incumbent_log_loss"] < 0
    assert confirmation["selected_minus_incumbent_brier"] < 0
    assert confirmation["player_bootstrap"]["component_log_loss"]["upper_95"] > 0
    assert confirmation["player_bootstrap"]["component_brier"]["upper_95"] > 0
    assert result["decision"] == {"promoted": False, "regression_pa": 1200}
    assert result["boundaries"]["current_2026_outcomes_used"] is False
    assert result["boundaries"]["current_values_changed"] is False
