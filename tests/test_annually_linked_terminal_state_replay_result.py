import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/annually-linked-terminal-state-replay-result.json"


def test_annually_linked_terminal_state_candidate_is_not_promoted() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["forecast_origin"] == 2021
    assert result["target_years"] == [2022, 2023, 2024, 2025]
    assert result["current_2026_used"] is False
    assert result["production_changed"] is False
    assert result["candidate_passed"] is False
    assert result["decision"] == "reject_terminal_state_candidate"
    assert result["hitter"]["candidate_minus_baseline_brier"]["ci_low"] > 0
    for metric in ("log_loss", "brier"):
        assert result["pitcher"][f"candidate_minus_baseline_{metric}"]["ci_high"] < 0
