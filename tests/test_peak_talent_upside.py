from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import polars as pl


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_peak_talent_upside import _probability, _score  # noqa: E402


def test_upside_probability_increases_with_point_mean() -> None:
    library = pl.DataFrame({
        "origin_age_band": ["20_to_21"] * 4,
        "evidence_band": ["200_to_499"] * 4,
        "residual": [-2.0, -1.0, 1.0, 2.0],
    })
    low = {"predicted_runs": -2.0, "origin_age_band": "20_to_21", "evidence_band": "200_to_499"}
    high = {"predicted_runs": 2.0, "origin_age_band": "20_to_21", "evidence_band": "200_to_499"}
    assert _probability(library, high, 0.0, "global") > _probability(
        library, low, 0.0, "global"
    )


def test_proper_score_rewards_correct_probabilities() -> None:
    outcome = np.asarray([0.0, 1.0])
    good = _score(np.asarray([0.1, 0.9]), outcome)
    bad = _score(np.asarray([0.9, 0.1]), outcome)
    assert good["brier"] < bad["brier"]
    assert good["log_loss"] < bad["log_loss"]
