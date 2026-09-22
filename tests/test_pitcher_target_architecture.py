import numpy as np
import polars as pl

from universal_baseball.hitter_target_architecture import Fold
from universal_baseball.pitcher_target_architecture import (
    run_pitcher_architecture_fold,
)


def test_pitcher_architecture_outputs_all_three_targets() -> None:
    rows = []
    for origin in (2021, 2022, 2023):
        for player_id in range(20):
            active = int(player_id % 3 == 0)
            rows.append(
                {
                    "origin_year": origin,
                    "target_season": origin + 1,
                    "player_id": player_id,
                    "lag0__highest_level": "MLB" if active else "AAA",
                    "lag0__strikeout_rate": 0.20 + player_id / 1_000,
                    "target_mlb_bf": 100.0 * active,
                    "target_mlb_active": active,
                    "target_conditional_component_war_per_800": (
                        2.0 if active else None
                    ),
                    "target_component_war": 0.25 * active,
                }
            )
    panel = pl.DataFrame(rows)

    predictions, metrics = run_pitcher_architecture_fold(
        panel,
        Fold(test_origin=2023, train_origins=(2021, 2022)),
        "ridge",
    )

    assert predictions.height == 20
    assert set(("prediction_direct", "prediction_two_part", "prediction_three_part")) <= set(
        predictions.columns
    )
    assert np.isfinite(predictions["prediction_three_part"].to_numpy()).all()
    assert set(metrics) == {
        "direct",
        "two_part",
        "three_part",
        "active_probability",
    }
