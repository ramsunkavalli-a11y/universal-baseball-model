import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/prospect-post-arrival-destination-result.json"


def test_destination_rule_was_selected_in_time_order() -> None:
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    assert result["current_2026_used"] is False
    assert result["shortened_2020_outcomes_excluded"] is True
    assert [fold["outcome_year"] for fold in result["folds"]] == [2023, 2024, 2025]
    assert [fold["training_players"] for fold in result["folds"]] == sorted(
        fold["training_players"] for fold in result["folds"]
    )
    assert result["decision"] in {
        "use_player_type_destination_split",
        "retain_pooled_destination_probability",
    }
    assert result["production_changed"] is False
