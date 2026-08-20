from __future__ import annotations

import pytest

from universal_baseball.player_value_advancement_projection import (
    PlayerSeasonAdvancementSummary,
)

from scripts.recertify_player_value_v1_advancement_history import (
    canonical_model_input_sha256,
    relative_score_drift,
)


def test_canonical_hash_is_order_independent_and_value_sensitive() -> None:
    rows = [
        PlayerSeasonAdvancementSummary(2, 2023, -0.25, 10.0),
        PlayerSeasonAdvancementSummary(1, 2022, 0.5, 20.0),
    ]
    assert canonical_model_input_sha256(rows) == canonical_model_input_sha256(reversed(rows))
    changed = [
        PlayerSeasonAdvancementSummary(2, 2023, -0.20, 10.0),
        rows[1],
    ]
    assert canonical_model_input_sha256(rows) != canonical_model_input_sha256(changed)


def test_relative_score_drift_uses_frozen_magnitude() -> None:
    assert relative_score_drift(0.10005, 0.1) == pytest.approx(0.0005)
