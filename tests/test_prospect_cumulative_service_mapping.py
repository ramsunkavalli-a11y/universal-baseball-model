from __future__ import annotations

import polars as pl

from scripts.audit_prospect_cumulative_service_mapping import (
    apply_service_predictions,
)


def test_zero_workload_never_invents_service_state() -> None:
    training = pl.DataFrame(
        {
            "player_type": ["hitter", "hitter", "hitter", "hitter"],
            "first_mlb_season": [True, True, False, False],
            "workload": [0.0, 600.0, 0.0, 600.0],
            "service_days": [20, 172, 50, 172],
        }
    )
    paths = pl.DataFrame(
        {
            "player_id": [1, 1],
            "player_type": ["hitter", "hitter"],
            "first_mlb_season": [True, False],
            "workload": [0.0, 300.0],
            "raw_workload": [0.0, 300.0],
        }
    )

    result = apply_service_predictions(paths, training)

    assert result.item(0, "mapped_service_days") == 0.0
    assert result.item(0, "active_season_shortcut_days") == 0.0
    assert result.item(1, "mapped_service_days") > 0.0
    assert result.item(1, "active_season_shortcut_days") == 172.0
