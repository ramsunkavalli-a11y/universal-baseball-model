from __future__ import annotations

import numpy as np

from scripts.score_prospect_six_year_hitter_blend_confirmation import (
    blended_expected_war,
)


def test_blend_keeps_arrival_separate_from_conditional_quality() -> None:
    result = blended_expected_war(
        np.asarray([0.0, 0.5, 1.0]),
        np.asarray([10.0, 10.0, 10.0]),
        2.0,
    )

    np.testing.assert_allclose(result, [0.0, 2.6, 5.2])
