from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from universal_baseball.hitter_v2_outcomes import HITTER_TALENT_OUTCOMES
from universal_baseball.hitter_v2_s0 import (
    blend_outcome_predictions,
    select_c0_weight,
)


def _predictions(player_ids: list[int], first_probability: float) -> pl.DataFrame:
    remainder = (1.0 - first_probability) / (len(HITTER_TALENT_OUTCOMES) - 1)
    return pl.DataFrame(
        [
            {
                "player_id": player_id,
                **{
                    f"p_{outcome}": (
                        first_probability if index == 0 else remainder
                    )
                    for index, outcome in enumerate(HITTER_TALENT_OUTCOMES)
                },
            }
            for player_id in player_ids
        ]
    )


def test_blend_is_convex_normalized_and_uses_identical_cohort() -> None:
    c0 = _predictions([2, 1], 0.20)
    marcel = _predictions([1, 2], 0.10)
    result = blend_outcome_predictions(c0, marcel, c0_weight=0.75)
    assert result["player_id"].to_list() == [1, 2]
    assert result["p_UBB"].to_list() == pytest.approx([0.175, 0.175])
    assert result.select(
        pl.sum_horizontal(*[f"p_{outcome}" for outcome in HITTER_TALENT_OUTCOMES])
    ).to_series().to_list() == pytest.approx([1.0, 1.0])
    with pytest.raises(ValueError, match="identical"):
        blend_outcome_predictions(c0, _predictions([1], 0.10), c0_weight=0.75)


def test_selection_tie_prefers_larger_C0_weight() -> None:
    scores = pl.DataFrame(
        {
            "c0_weight": [0.5, 0.75, 1.0],
            "mean_player_pa_terminal_log_loss": [0.4, 0.3, 0.300000005],
        }
    )
    selected = select_c0_weight(scores)
    assert selected["c0_weight"] == 1.0


def test_fit_runner_has_no_disclosed_or_protected_loader() -> None:
    source = Path("scripts/fit_hitter_v2_S0.py").read_text(encoding="utf-8")
    assert "target_players" not in source
    assert "2026" not in source
