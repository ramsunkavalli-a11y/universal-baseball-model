from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_peak_talent_ranking import _ranking_score  # noqa: E402


def test_ranking_score_rewards_correct_top_order() -> None:
    actual = np.asarray([1.0, 2.0, 3.0, 4.0])
    correct = _ranking_score(actual, actual)
    reversed_score = _ranking_score(actual[::-1], actual)
    assert correct["spearman"] == 1.0
    assert correct["top_quartile_precision"] == 1.0
    assert reversed_score["spearman"] == -1.0
    assert reversed_score["top_quartile_precision"] == 0.0
