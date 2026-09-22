from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from universal_baseball.hitter_target_architecture import Fold
from universal_baseball.pitcher_workload_model import run_pitcher_workload_fold


def _panel() -> pl.DataFrame:
    rows = []
    for origin in range(2010, 2021):
        for player in range(30):
            recent_bf = float((player % 6) * 90)
            active = int(player % 5 == 0 or recent_bf >= 180)
            target_bf = float(active * (70 + recent_bf * 0.7 + player % 4))
            rows.append(
                {
                    "origin_year": origin,
                    "target_season": origin + 1,
                    "player_id": origin * 100 + player,
                    "lag0__batters_faced": recent_bf,
                    "lag0__highest_level": "MLB" if recent_bf else "AAA",
                    "target_mlb_bf": target_bf,
                    "target_mlb_active": active,
                    "target_conditional_component_war_per_800": 0.5,
                    "target_component_war": target_bf / 800.0 * 0.5,
                }
            )
    return pl.DataFrame(rows)


def test_pitcher_workload_fold_is_zero_inclusive_and_bounded() -> None:
    panel = _panel()
    predictions, metrics = run_pitcher_workload_fold(
        panel,
        Fold(train_origins=tuple(range(2010, 2020)), test_origin=2020),
        "ridge",
    )
    assert predictions.height == 30
    assert predictions["predicted_expected_bf"].is_finite().all()
    assert (predictions["active_probability"] >= 0.0).all()
    assert (predictions["active_probability"] <= 1.0).all()
    assert (predictions["predicted_conditional_bf"] >= 0.0).all()
    assert (predictions["predicted_conditional_bf"] <= 1_500.0).all()
    np.testing.assert_allclose(
        predictions["predicted_expected_bf"].to_numpy(),
        predictions["active_probability"].to_numpy()
        * predictions["predicted_conditional_bf"].to_numpy(),
    )
    assert metrics["zero_inclusive_bf"]["rmse"] >= 0.0


def test_pitcher_workload_model_rejects_target_leakage() -> None:
    panel = _panel().with_columns(pl.col("target_mlb_bf").alias("target_leak"))
    with pytest.raises(ValueError, match="future outcome"):
        run_pitcher_workload_fold(
            panel,
            Fold(train_origins=tuple(range(2010, 2020)), test_origin=2020),
            "ridge",
        )
