from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl


sys.path.insert(0, str(Path("scripts").resolve()))

from audit_age_to_peak_talent import _player_score  # noqa: E402
from materialize_current_peak_talent import _rank_prospects  # noqa: E402


def test_player_score_does_not_weight_a_player_by_future_workload() -> None:
    predictions = np.asarray([[0.5, 0.5], [0.5, 0.5]])
    rows = [
        {"target_a": 75.0, "target_b": 25.0},
        {"target_a": 25.0, "target_b": 75.0},
    ]
    scaled_rows = [rows[0], {"target_a": 2500.0, "target_b": 7500.0}]

    original = _player_score(predictions, rows, ("a", "b"))
    scaled = _player_score(predictions, scaled_rows, ("a", "b"))

    assert scaled["log_loss"] == original["log_loss"]
    assert scaled["brier"] == original["brier"]


def test_prospect_rank_excludes_mlb_unknown_age_and_age_over_25() -> None:
    frame = pl.DataFrame({
        "player_id": [1, 2, 3, 4],
        "ranking_status": ["ranked"] * 4,
        "as_of_level_group": ["AA", "MLB", "AAA", "AA"],
        "age_years": [20.0, 20.0, None, 26.0],
        "peak_runs_rate": [1.0, 4.0, 3.0, 2.0],
        "effective_evidence": [200.0] * 4,
    })

    result = _rank_prospects(frame)

    assert result.filter(pl.col("prospect_peak_rate_rank").is_not_null()).get_column(
        "player_id"
    ).to_list() == [1]
