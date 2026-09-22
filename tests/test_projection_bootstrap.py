from __future__ import annotations

import numpy as np
import pytest

from universal_baseball.projection_bootstrap import paired_player_cluster_bootstrap


def test_paired_bootstrap_identifies_uniformly_better_candidate() -> None:
    actual = np.asarray([[0.8, 0.2], [0.2, 0.8], [0.7, 0.3], [0.3, 0.7]])
    baseline = np.full((4, 2), 0.5)
    candidate = 0.75 * actual + 0.25 * baseline
    result = paired_player_cluster_bootstrap(
        player_ids=np.asarray([1, 1, 2, 2]),
        actual=actual,
        baseline=baseline,
        candidate=candidate,
        weights=np.ones(4),
        repetitions=200,
        seed=7,
    )
    for metric in result.values():
        assert metric["upper_95"] < 0
        assert metric["probability_candidate_better"] == 1.0


def test_paired_bootstrap_validates_shapes() -> None:
    with pytest.raises(ValueError, match="same shape"):
        paired_player_cluster_bootstrap(
            player_ids=np.asarray([1]),
            actual=np.asarray([[0.5, 0.5]]),
            baseline=np.asarray([[0.5]]),
            candidate=np.asarray([[0.5, 0.5]]),
            weights=np.ones(1),
            repetitions=100,
        )
