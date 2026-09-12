from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl


sys.path.insert(0, str(Path("scripts").resolve()))

from audit_age_to_peak_talent import _player_score  # noqa: E402
from materialize_current_peak_talent import (  # noqa: E402
    _rank_prospects,
    _run_calibration,
)
from materialize_current_future_talent import _hitter_runs, _pitcher_runs  # noqa: E402


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


def test_prospect_rank_excludes_mlb_unknown_age_and_age_over_23() -> None:
    frame = pl.DataFrame({
        "player_id": [1, 2, 3, 4],
        "ranking_status": ["ranked"] * 4,
        "as_of_level_group": ["AA", "MLB", "AAA", "AA"],
        "age_years": [20.0, 20.0, None, 24.0],
        "peak_runs_rate": [1.0, 4.0, 3.0, 2.0],
        "effective_evidence": [200.0] * 4,
    })

    result = _rank_prospects(frame)

    assert result.filter(pl.col("prospect_peak_rate_rank").is_not_null()).get_column(
        "player_id"
    ).to_list() == [1]


def test_run_calibration_uses_age_band_only_inside_supported_model() -> None:
    adjustment = _run_calibration(
        np.asarray([19.9, 20.0, 21.9, 22.0, 24.0]),
        np.asarray([True, True, True, True, False]),
        {"under_20": 5.0, "20_to_21": 3.0, "22_to_23": 1.0},
    )

    assert adjustment.tolist() == [5.0, 3.0, 3.0, 1.0, 0.0]


def test_hitter_run_score_rewards_hits_at_expense_of_outs() -> None:
    present = np.asarray([[0.20, 0.08, 0.01, 0.14, 0.04, 0.005, 0.03, 0.495]])
    more_homers = present.copy()
    more_homers[0, 6] += 0.01
    more_homers[0, 7] -= 0.01

    assert _hitter_runs(more_homers, present, np.asarray([0.0]))[0] > 0.0


def test_pitcher_run_score_rewards_strikeouts_and_penalizes_walks() -> None:
    present = np.asarray([[0.22, 0.08, 0.01, 0.03, 0.66]])
    more_strikeouts = present.copy()
    more_strikeouts[0, 0] += 0.01
    more_strikeouts[0, 4] -= 0.01
    more_walks = present.copy()
    more_walks[0, 1] += 0.01
    more_walks[0, 4] -= 0.01

    assert _pitcher_runs(more_strikeouts, present, np.asarray([0.0]))[0] > 0.0
    assert _pitcher_runs(more_walks, present, np.asarray([0.0]))[0] < 0.0
