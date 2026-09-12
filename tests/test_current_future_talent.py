from __future__ import annotations

import sys
from pathlib import Path

import numpy as np


sys.path.insert(0, str(Path("scripts").resolve()))

from materialize_current_future_talent import _hitter_runs, _pitcher_runs  # noqa: E402


def test_unchanged_hitter_components_preserve_present_run_rate() -> None:
    present = np.asarray([[0.08, 0.01, 0.15, 0.05, 0.005, 0.04, 0.665]])
    present_runs = np.asarray([12.5])

    result = _hitter_runs(present.copy(), present, present_runs)

    np.testing.assert_allclose(result, present_runs)


def test_unchanged_pitcher_components_preserve_present_run_rate() -> None:
    present = np.asarray([[0.26, 0.07, 0.01, 0.025, 0.635]])
    present_runs = np.asarray([8.0])

    result = _pitcher_runs(present.copy(), present, present_runs)

    np.testing.assert_allclose(result, present_runs)
