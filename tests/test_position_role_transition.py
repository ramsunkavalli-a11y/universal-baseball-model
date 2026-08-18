from __future__ import annotations

import numpy as np
import pytest

from universal_baseball.position_role_profile import BATTING_ROLE_POSITIONS
from universal_baseball.position_role_transition import (
    fit_primary_destination_means,
    primary_position,
    summed_squared_error,
    total_variation_distance,
    transition_smoothed_prediction,
)


def _one_hot(position: str) -> np.ndarray:
    vector = np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
    vector[BATTING_ROLE_POSITIONS.index(position)] = 1.0
    return vector


def test_transition_smoother_blends_by_primary_share() -> None:
    current = np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
    current[BATTING_ROLE_POSITIONS.index("SS")] = 0.75
    current[BATTING_ROLE_POSITIONS.index("2B")] = 0.25
    destination = np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
    destination[BATTING_ROLE_POSITIONS.index("SS")] = 0.50
    destination[BATTING_ROLE_POSITIONS.index("2B")] = 0.50

    predicted = transition_smoothed_prediction(
        current,
        primary_share=0.75,
        destination_mean=destination,
    )

    assert predicted[BATTING_ROLE_POSITIONS.index("SS")] == pytest.approx(0.6875)
    assert predicted[BATTING_ROLE_POSITIONS.index("2B")] == pytest.approx(0.3125)
    assert predicted.sum() == pytest.approx(1.0)


def test_fit_destination_means_requires_every_frozen_position() -> None:
    samples = {position: [_one_hot(position)] for position in BATTING_ROLE_POSITIONS}
    samples["LF"] = [_one_hot("LF"), _one_hot("RF")]

    means, counts = fit_primary_destination_means(samples)

    assert counts["LF"] == 2
    assert means["LF"][BATTING_ROLE_POSITIONS.index("LF")] == pytest.approx(0.5)
    assert means["LF"][BATTING_ROLE_POSITIONS.index("RF")] == pytest.approx(0.5)

    incomplete = dict(samples)
    del incomplete["DH"]
    with pytest.raises(ValueError, match="no destination profiles for DH"):
        fit_primary_destination_means(incomplete)


def test_role_vector_scores_and_primary_position() -> None:
    observed = _one_hot("CF")
    predicted = np.zeros(len(BATTING_ROLE_POSITIONS), dtype=float)
    predicted[BATTING_ROLE_POSITIONS.index("CF")] = 0.8
    predicted[BATTING_ROLE_POSITIONS.index("LF")] = 0.2

    assert total_variation_distance(predicted, observed) == pytest.approx(0.2)
    assert summed_squared_error(predicted, observed) == pytest.approx(0.08)
    assert primary_position(predicted) == "CF"
