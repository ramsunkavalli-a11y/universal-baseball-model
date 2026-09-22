from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_gradient_materialization import CONTACT_OUTCOMES
from universal_baseball.pitcher_contact_neutralization import (
    OUTCOME_VALUES,
    aggregate_pitcher_contact_value,
    attach_pitcher_contact_value_lags,
)


def test_aggregate_pitcher_contact_value_uses_actual_minus_expected() -> None:
    events = pl.DataFrame(
        {
            "season": [2024, 2024],
            "player_id": [10, 10],
            "level": ["aaa", "aaa"],
            "canonical_outcome": ["1B", "OTHER_OUT"],
        }
    )
    probability = np.zeros((2, len(CONTACT_OUTCOMES)), dtype=np.float32)
    out_index = CONTACT_OUTCOMES.index("OTHER_OUT")
    probability[:, out_index] = 1.0

    result = aggregate_pitcher_contact_value(events, probability, prior_contacts=2.0)

    expected_sum = OUTCOME_VALUES["1B"] - OUTCOME_VALUES["OTHER_OUT"]
    assert result["contact_events"].item() == 2
    assert result["contact_value_residual_sum"].item() == pytest.approx(expected_sum)
    assert result["contact_value_residual_rate"].item() == pytest.approx(
        expected_sum / 4.0
    )


def test_attach_pitcher_contact_value_lags_keeps_missing_evidence_neutral() -> None:
    panel = pl.DataFrame(
        {
            "origin_year": [2024, 2024],
            "target_season": [2025, 2025],
            "player_id": [1, 2],
        }
    )
    annual = pl.DataFrame(
        {
            "season": [2024],
            "player_id": [1],
            "contact_events": [100],
            "contact_value_residual_rate": [-0.02],
        }
    )

    result = attach_pitcher_contact_value_lags(
        panel, annual, prefix="contact", lags=(0,)
    )

    assert result.filter(pl.col("player_id") == 1)["contact_lag0__available"].item() == 1
    assert result.filter(pl.col("player_id") == 2)["contact_lag0__available"].item() == 0
    assert result.filter(pl.col("player_id") == 2)[
        "contact_lag0__contact_value_residual_rate"
    ].item() is None
