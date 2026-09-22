from __future__ import annotations

import polars as pl
import pytest

from universal_baseball.runner_value_bridge import (
    build_runner_bridge_candidates,
    select_from_prior_targets,
)


def test_runner_bridge_uses_milb_as_fallback_without_overwriting_missing() -> None:
    base = pl.DataFrame(
        {
            "target_season": [2024, 2024, 2024],
            "player_id": [1, 2, 3],
            "prediction_candidate_expected_pa": [600.0, 600.0, 600.0],
            "prediction_advancement_war": [0.10, 0.00, 0.20],
            "baserunning_evidence_tier": [
                "steal_and_advancement",
                "steal_only",
                "steal_only",
            ],
        }
    )
    milb = pl.DataFrame(
        {"target_season": [2024, 2024], "player_id": [1, 2], "projected_effect": [0.02, 0.04]}
    )
    result = build_runner_bridge_candidates(
        base,
        milb,
        advancement_opportunities_per_pa=0.2,
        runs_per_win=10.0,
    )
    rows = {row["player_id"]: row for row in result.to_dicts()}
    assert rows[1]["prediction_advancement_fallback_100"] == pytest.approx(0.10)
    assert rows[2]["prediction_advancement_fallback_100"] == pytest.approx(0.48)
    assert rows[3]["prediction_advancement_fallback_100"] == pytest.approx(0.20)


def test_runner_bridge_selection_never_uses_current_target() -> None:
    frame = pl.DataFrame(
        {
            "target_season": [2022, 2023],
            "later_advancement_war": [1.0, -1.0],
            "baseline": [0.9, -1.0],
            "challenger": [0.0, -1.0],
        }
    )
    selected, rows, _ = select_from_prior_targets(
        frame,
        target_season=2023,
        candidates=("baseline", "challenger"),
    )
    assert selected == "baseline"
    assert rows == 1
