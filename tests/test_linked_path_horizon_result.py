from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _report(player_type: str) -> dict[str, object]:
    path = ROOT / f"docs/dependent-career-linked-{player_type}-replay-result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_pitcher_linked_path_tradeoff_persists_across_horizons() -> None:
    report = _report("pitcher")
    rows = report["horizon_sensitivity"]
    assert [row["horizon_years"] for row in rows] == [1, 2, 3, 4]
    assert all(
        row["arrival_only_candidate"]["mae"] > row["incumbent"]["mae"]
        for row in rows
    )
    assert report["model_effect"] == "none"


def test_hitter_linked_path_tradeoff_persists_across_horizons() -> None:
    report = _report("hitter")
    rows = report["horizon_sensitivity"]
    assert [row["horizon_years"] for row in rows] == [1, 2, 3, 4]
    assert all(
        row["arrival_only_candidate"]["rmse"] > row["incumbent"]["rmse"]
        for row in rows
    )
    assert report["boundaries"]["production_values_changed"] is False
