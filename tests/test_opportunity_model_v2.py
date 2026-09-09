from __future__ import annotations

import polars as pl

from universal_baseball.opportunity_model_v2 import (
    build_universal_hitter_opportunity_fold,
    select_universal_opportunity_form,
)
from universal_baseball.playing_time_model import PT_FORM_U, PT_FORM_U0, PT_FORM_UA


def test_fold_keeps_zero_outcomes_and_splits_current_mlb_milb_pa() -> None:
    snapshot = pl.DataFrame(
        {
            "snapshot_year": [2024, 2024],
            "player_id": [1, 2],
            "age_years": [25.0, None],
            "as_of_level_group": ["MLB", "INACTIVE"],
        }
    )
    current = pl.DataFrame(
        {
            "stat_group": ["hitting", "hitting"],
            "player_id": [1, 1],
            "sport_id": [1, 11],
            "plate_appearances": [100, 50],
        }
    )
    future = pl.DataFrame(
        {
            "stat_group": ["hitting"],
            "player_id": [1],
            "sport_id": [1],
            "plate_appearances": [200],
        }
    )
    membership = pl.DataFrame(
        {"season": [2024], "player_id": [1], "on_40man": [True]}
    )

    fold = build_universal_hitter_opportunity_fold(
        snapshot, current, future, membership, snapshot_year=2024
    )

    assert fold.predictors.row(0, named=True)["current_season_mlb_pa"] == 100
    assert fold.predictors.row(0, named=True)["current_season_milb_pa"] == 50
    assert fold.predictors.row(1, named=True)["on_40man"] is False
    assert fold.targets.get_column("next_year_mlb_pa").to_list() == [200, 0]


def test_selection_requires_three_fold_wins_and_all_pooled_gates() -> None:
    fold_rows = []
    for year in (2022, 2023, 2024, 2025):
        fold_rows.extend(
            [
                {"form": PT_FORM_U0, "target_year": year, "mean_full_negative_log_likelihood": 1.0},
                {"form": PT_FORM_UA, "target_year": year, "mean_full_negative_log_likelihood": 0.99 if year != 2025 else 1.01},
                {"form": PT_FORM_U, "target_year": year, "mean_full_negative_log_likelihood": 0.98},
            ]
        )
    pooled = pl.DataFrame(
        [
            {"form": PT_FORM_U0, "mean_full_negative_log_likelihood": 1.0, "participation_log_loss": 0.3, "unconditional_mlb_pa_mae": 40.0},
            {"form": PT_FORM_UA, "mean_full_negative_log_likelihood": 0.995, "participation_log_loss": 0.29, "unconditional_mlb_pa_mae": 40.2},
            {"form": PT_FORM_U, "mean_full_negative_log_likelihood": 0.98, "participation_log_loss": 0.28, "unconditional_mlb_pa_mae": 39.0},
        ]
    )

    decision = select_universal_opportunity_form(pl.DataFrame(fold_rows), pooled)

    assert decision["selected_form"] == PT_FORM_U
    assert decision["protected_2026_outcomes_used"] is False
